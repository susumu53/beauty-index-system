import feedparser
import requests
import re
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup

# Google News RSS エンドポイント
GNEWS_ENTAME_URL = "https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFp1ZEdvU0JXcGhMVkpQUWlnQVAB?hl=ja&gl=JP&ceid=JP:ja"
GNEWS_SEARCH_URL = "https://news.google.com/rss/search?q={name}+芸能&hl=ja&gl=JP&ceid=JP:ja"

POSTED_LOG_PATH = os.path.join(os.path.dirname(__file__), "posted_log.json")

# 芸能人名を抽出するための除外ワード
EXCLUDE_WORDS = [
    "政府", "首相", "大臣", "官房", "議員", "知事", "市長", "区長", "選手",
    "監督", "コーチ", "アナウンサー", "記者", "社長", "会長", "代表",
]

# 芸能人の可能性が高いパターン
CELEB_PATTERNS = [
    r"([^\s]{2,6}[さ|君|くん|ちゃん])\s*[がはもを]",
    r"([^\s]{2,6})\s*(?:さん|主演|出演|共演|熱愛|結婚|離婚|妊娠|復帰|引退|デビュー|批判|炎上|謝罪)",
    r"俳優の([^\s]{2,6})",
    r"女優の([^\s]{2,6})",
    r"歌手の([^\s]{2,6})",
    r"タレントの([^\s]{2,6})",
    r"アイドルの([^\s]{2,6})",
    r"モデルの([^\s]{2,6})",
]

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

def extract_celebrity_names(text):
    """テキストから芸能人名を抽出する"""
    found = []
    for pattern in CELEB_PATTERNS:
        matches = re.findall(pattern, text)
        for m in matches:
            name = m.strip()
            # 除外ワードチェック
            if any(ex in name for ex in EXCLUDE_WORDS):
                continue
            # 長すぎる・短すぎる名前を除外
            if len(name) < 2 or len(name) > 10:
                continue
            # ひらがな・カタカナ・漢字のみの名前を優先
            if re.match(r'^[\u3040-\u30ff\u4e00-\u9fff\u3000-\u303f]+$', name):
                if name not in found:
                    found.append(name)
    return found

def get_trending_celebrity():
    """Google News エンタメRSSからトレンド芸能人名を1人取得する（未投稿優先）"""
    log = load_posted_log()
    posted_list = log.get("posted", [])
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        feed = feedparser.parse(GNEWS_ENTAME_URL)
        
        candidate_scores = {}  # name -> count
        
        for entry in feed.entries[:30]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            combined = title + " " + summary
            
            names = extract_celebrity_names(combined)
            for name in names:
                candidate_scores[name] = candidate_scores.get(name, 0) + 1
        
        # スコア高い順にソートして未投稿の人を選ぶ
        sorted_names = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
        
        for name, score in sorted_names:
            if name not in posted_list:
                print(f"✅ トレンド芸能人を選定: {name}（スコア: {score}）")
                return name
        
        # 全員投稿済みならログをリセットして再選択
        if sorted_names:
            print("⚠️ 全候補が投稿済み → ログをリセットして再試行")
            log["posted"] = []
            save_posted_log(log)
            return sorted_names[0][0]
            
    except Exception as e:
        print(f"❌ トレンド取得エラー: {e}")
    
    return None

def get_celebrity_news(celebrity_name, max_articles=3):
    """
    特定の芸能人の最新ニュースを取得する。
    著作権対策: 本文は先頭200文字のみ引用形式で返す。
    """
    url = GNEWS_SEARCH_URL.format(name=requests.utils.quote(celebrity_name))
    
    news_list = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        feed = feedparser.parse(url)
        count = 0
        
        for entry in feed.entries:
            if count >= max_articles:
                break
            
            title = entry.get("title", "").split(" - ")[0]  # 媒体名を除去
            link = entry.get("link", "")
            published = entry.get("published", "")
            source = entry.get("source", {}).get("title", "")
            
            # 記事本文を取得（失敗してもタイトルのみで続行）
            excerpt = ""
            try:
                r = requests.get(link, headers=headers, timeout=8)
                soup = BeautifulSoup(r.text, "html.parser")
                
                # 不要なタグを削除
                for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
                    tag.decompose()
                
                # 本文らしいテキストを取得（p タグから）
                paragraphs = soup.find_all("p")
                body_text = " ".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])
                
                if body_text:
                    excerpt = body_text[:200] + "…"
            except Exception:
                pass  # 本文取得失敗は無視
            
            news_list.append({
                "title": title,
                "link": link,
                "published": published,
                "source": source,
                "excerpt": excerpt,
            })
            count += 1
            
    except Exception as e:
        print(f"❌ ニュース取得エラー ({celebrity_name}): {e}")
    
    return news_list

def mark_as_posted(celebrity_name):
    """芸能人を投稿済みとして記録する"""
    log = load_posted_log()
    if celebrity_name not in log["posted"]:
        log["posted"].append(celebrity_name)
        # 最大100件保持（古いものを削除）
        if len(log["posted"]) > 100:
            log["posted"] = log["posted"][-100:]
    save_posted_log(log)

if __name__ == "__main__":
    name = get_trending_celebrity()
    print(f"芸能人: {name}")
    if name:
        news = get_celebrity_news(name)
        for n in news:
            print(f"  - {n['title']} ({n['source']})")
