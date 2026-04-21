import feedparser
import requests
import re
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup

# Google News RSS エンドポイント（動作確認済み）
GNEWS_ENTAME_URL = "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=ja&gl=JP&ceid=JP:ja"
GNEWS_SEARCH_URL = "https://news.google.com/rss/search?q={name}&hl=ja&gl=JP&ceid=JP:ja"

POSTED_LOG_PATH = os.path.join(os.path.dirname(__file__), "posted_log.json")

# ── 著名芸能人リスト（RSS から名前が抽出できない場合の補助フィルタ） ──
# ニュースタイトルに登場したらカウントアップ
KNOWN_CELEB_PATTERNS = [
    # 名前の後ろに来るキーワード（「名前 + が/は + 動詞」）
    r'([^\s「」『』【】\(（\)）、。]{2,8})\s*(?:が|は|も)(?:新|今|昨|先)',
    # 名前の前に来るキーワード
    r'(?:俳優|女優|歌手|タレント|アイドル|モデル|芸人|声優|アナ)(?:の)?([^\s「」、。\(（]{2,8})',
    # "〜、背中に" "〜、離婚" などの無助詞パターン
    r'^([一-龥ぁ-ん]{1,4}[一-龥ぁ-ん０-９A-Za-z]{1,6})(?:[、，]|\s)',
    # "浜野謙太と後藤真希が" → 2人の名前
    r'([一-龥ぁ-んァ-ン]{2,5})\s*(?:と|×|＆|&)\s*([一-龥ぁ-んァ-ン]{2,5})\s*(?:が|は|の|で)',
]

# 漢字・ひらがなのみで構成された 2〜6 文字の名前（最も信頼度高い）
STRICT_NAME_RE = re.compile(r'^[一-龥ぁ-んァ-ン]{2,6}$')

# 除外するパターン（名前ではないもの）
NOISE_WORDS = {
    "視聴率", "低迷", "共演者", "スポーツ", "ライブ", "ニュース", "エンタメ", "アニメ",
    "映画", "舞台", "ドラマ", "動画", "記事", "情報", "テレビ", "週刊", "公演",
    "キャスト", "キャラ", "ランキング", "オーラ", "シーン", "ステージ", "コンサート",
    "野球", "サッカー", "政府", "首相", "大臣", "議員", "知事", "市長",
    "花火", "タトゥー", "マンション", "コーラス",
}


def load_posted_log():
    """投稿済みログを読み込む"""
    if os.path.exists(POSTED_LOG_PATH):
        with open(POSTED_LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"posted": [], "last_updated": ""}


def save_posted_log(log_data):
    """投稿済みログを保存する"""
    log_data["last_updated"] = datetime.now().isoformat()
    with open(POSTED_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


def _strip_media_suffix(title):
    """' - 読売新聞' などの媒体名サフィックスを削除"""
    return re.sub(r'\s*[-－]\s*[^\s]{2,20}$', '', title).strip()


def _is_valid_celeb_name(name):
    """人名として有効な文字列かチェック"""
    name = name.strip()
    if not name:
        return False
    if len(name) < 2 or len(name) > 8:
        return False
    # ノイズワードに含まれる
    if name in NOISE_WORDS:
        return False
    for noise in NOISE_WORDS:
        if noise in name:
            return False
    # 数字・英字・記号が混じっている
    if re.search(r'[0-9０-９a-zA-Z\!\?\.\,\s\(\)（）「」【】]', name):
        return False
    # 2〜6文字の漢字・かな・カナ
    if not re.match(r'^[一-龥ぁ-んァ-ン]{2,8}$', name):
        return False
    return True


def extract_names_from_title(title):
    """
    ニュースタイトルから芸能人名を抽出する。
    実際のGoogle Newsタイトルに最適化。
    """
    found = []
    clean_title = _strip_media_suffix(title)

    # ① 冒頭の人名（最も信頼度高い）
    # 例: "明石家さんま　離婚後に..." → "明石家さんま"
    m = re.match(r'^([一-龥ぁ-んァ-ン]{2,8})(?:\s|　|、|が|は|も|と|の)', clean_title)
    if m:
        name = m.group(1).strip()
        if _is_valid_celeb_name(name):
            found.append(name)

    # ② "AとBが" パターン
    # 例: "浜野謙太と後藤真希がドラマ..."
    for m in re.finditer(r'([一-龥ぁ-んァ-ン]{2,6})\s*(?:と|×|＆|&)\s*([一-龥ぁ-んァ-ン]{2,6})\s*(?:が|は|の|で|も)', clean_title):
        for name in [m.group(1), m.group(2)]:
            name = name.strip()
            if _is_valid_celeb_name(name) and name not in found:
                found.append(name)

    # ③ 職業キーワードの後の名前
    # 例: "女優の石原さとみが..."
    for m in re.finditer(r'(?:俳優|女優|歌手|タレント|アイドル|モデル|芸人|声優)(?:の|・)?([一-龥ぁ-んァ-ン]{2,8})', clean_title):
        name = m.group(1).strip()
        if _is_valid_celeb_name(name) and name not in found:
            found.append(name)

    # ④ 「名前、〜」パターン（読点区切り）
    # 例: "三吉彩花、背中に入れた花のタトゥー..."
    m = re.match(r'^([一-龥ぁ-んァ-ン]{2,8})[、,，]', clean_title)
    if m:
        name = m.group(1).strip()
        if _is_valid_celeb_name(name) and name not in found:
            found.append(name)

    # ⑤ タイトル全体から "名前 + キーワード" パターン
    for m in re.finditer(r'([一-龥ぁ-んァ-ン]{2,8})\s*(?:主演|出演|共演|熱愛|結婚|離婚|妊娠|復帰|引退|デビュー|炎上|謝罪|コメント|の単独)', clean_title):
        name = m.group(1).strip()
        if _is_valid_celeb_name(name) and name not in found:
            found.append(name)

    return found


def get_trending_celebrity():
    """
    Google News エンタメRSSからトレンド芸能人名を1人取得する（未投稿優先）
    """
    log = load_posted_log()
    posted_list = log.get("posted", [])

    try:
        feed = feedparser.parse(GNEWS_ENTAME_URL)
        print("  RSSエントリ数: " + str(len(feed.entries)))

        candidate_scores = {}

        for entry in feed.entries[:60]:
            title = entry.get("title", "")
            names = extract_names_from_title(title)
            for name in names:
                candidate_scores[name] = candidate_scores.get(name, 0) + 1

        print("  名前候補数: " + str(len(candidate_scores)) + "人")

        if candidate_scores:
            top5 = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)[:5]
            print("  上位候補: " + str([(n, s) for n, s in top5]))

        sorted_names = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)

        for name, score in sorted_names:
            if name not in posted_list:
                print("  選定: " + name + " (スコア: " + str(score) + ")")
                return name

        # 全員投稿済みならリセット
        if sorted_names:
            print("  [WARN] 全候補投稿済み -> ログをリセット")
            log["posted"] = []
            save_posted_log(log)
            return sorted_names[0][0]

    except Exception as e:
        print("  [ERROR] トレンド取得エラー: " + str(e))

    return None


def get_celebrity_news(celebrity_name, max_articles=3):
    """
    特定の芸能人の最新ニュースを取得する。
    著作権対策: 本文は先頭200文字のみ引用形式で返す。
    """
    url = GNEWS_SEARCH_URL.format(name=requests.utils.quote(celebrity_name))
    news_list = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        feed = feedparser.parse(url)
        count = 0

        for entry in feed.entries:
            if count >= max_articles:
                break

            raw_title = entry.get("title", "")
            title = _strip_media_suffix(raw_title) or raw_title
            link = entry.get("link", "")
            published = entry.get("published", "")
            source_obj = entry.get("source", {})
            source = source_obj.get("title", "") if isinstance(source_obj, dict) else ""

            # 本文取得（失敗してもOK）
            excerpt = ""
            try:
                r = requests.get(link, headers=headers, timeout=8)
                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
                    tag.decompose()
                paragraphs = soup.find_all("p")
                body_text = " ".join([
                    p.get_text(strip=True)
                    for p in paragraphs
                    if len(p.get_text(strip=True)) > 30
                ])
                if body_text:
                    excerpt = body_text[:200] + "..."
            except Exception:
                pass

            news_list.append({
                "title": title,
                "link": link,
                "published": published,
                "source": source,
                "excerpt": excerpt,
            })
            count += 1

    except Exception as e:
        print("  [ERROR] ニュース取得エラー (" + celebrity_name + "): " + str(e))

    return news_list


def mark_as_posted(celebrity_name):
    """芸能人を投稿済みとして記録する"""
    log = load_posted_log()
    if celebrity_name not in log["posted"]:
        log["posted"].append(celebrity_name)
        if len(log["posted"]) > 100:
            log["posted"] = log["posted"][-100:]
    save_posted_log(log)


if __name__ == "__main__":
    import sys, io
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf_8'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    name = get_trending_celebrity()
    print("選定芸能人: " + str(name))
    if name:
        news = get_celebrity_news(name, max_articles=3)
        print("ニュース件数: " + str(len(news)))
        for n in news:
            print("  - " + n['title'])
