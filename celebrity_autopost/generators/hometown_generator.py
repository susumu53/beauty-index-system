"""
hometown_generator.py
【独自記事③】都道府県別・芸能人出身地まとめ
47都道府県を日付ベースでローテーションして、Wikipedia検索で出身芸能人を紹介する。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
from datetime import datetime
from wiki_fetcher import _fetch_wiki_summary
from dmm_fetcher import DMMCelebFetcher

WIKI_SEARCH_URL = "https://ja.wikipedia.org/w/api.php"
WIKI_HEADERS = {"User-Agent": "celebrity-autopost-bot/1.0"}

PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]

CELEB_OCCUPATIONS_JP = ["俳優", "女優", "歌手", "タレント", "アイドル", "声優", "お笑い", "モデル", "漫才"]


def get_today_prefecture():
    """今日の日付から都道府県を決定（47日ローテ）"""
    day_of_year = datetime.now().timetuple().tm_yday
    return PREFECTURES[(day_of_year - 1) % len(PREFECTURES)]


def search_celebrities_by_prefecture(prefecture, max_results=5):
    """Wikipedia 検索APIで出身地の芸能人を検索"""
    celebrities = []

    for occ in ["俳優", "女優", "歌手", "タレント", "アイドル"]:
        if len(celebrities) >= max_results:
            break

        params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{prefecture}出身 {occ}",
            "srlimit": 5,
            "format": "json",
            "utf8": 1,
        }

        try:
            r = requests.get(WIKI_SEARCH_URL, params=params, headers=WIKI_HEADERS, timeout=10)
            results = r.json().get("query", {}).get("search", [])

            for res in results:
                title = res.get("title", "")
                snippet = res.get("snippet", "")

                # 既に追加済みなら除外
                if any(c["name"] == title for c in celebrities):
                    continue

                # 芸能人らしいか確認（職業ワードが含まれる）
                is_celeb = any(occ_kw in snippet for occ_kw in CELEB_OCCUPATIONS_JP)
                if not is_celeb:
                    continue

                # プロフィールを取得
                profile = _fetch_wiki_summary(title, WIKI_HEADERS)
                if not profile:
                    continue

                # 出身地が本当にその都道府県か確認
                if prefecture not in profile.get("full_extract", "")[:500]:
                    continue

                celebrities.append({
                    "name": title,
                    "occupation": profile.get("occupation", occ),
                    "birth_date": profile.get("birth_date", ""),
                    "summary": profile.get("summary", ""),
                    "thumbnail_url": profile.get("thumbnail_url", ""),
                    "wiki_url": profile.get("wiki_url", ""),
                })

                if len(celebrities) >= max_results:
                    break

        except Exception as e:
            print("[hometown] 検索エラー: " + str(e))

    return celebrities


def run():
    """出身地別まとめ記事を生成"""
    prefecture = get_today_prefecture()
    today_str = datetime.now().strftime("%Y年%m月%d日")

    print("[hometown] 本日の都道府県: " + prefecture)
    celebs = search_celebrities_by_prefecture(prefecture, max_results=5)

    if not celebs:
        print("[hometown] 芸能人が見つかりませんでした")
        return None

    print("[hometown] 見つかった人数: " + str(len(celebs)))

    # DMM商品取得
    dmm = DMMCelebFetcher()
    for celeb in celebs:
        items = dmm.search_celebrity_products(celeb["name"], max_items=1)
        celeb["dmm_product"] = items[0] if items else None

    html = _build_html(celebs, prefecture, today_str)
    title = f"【{prefecture}出身の芸能人まとめ】俳優・歌手・タレント一覧【{today_str}】"
    tags = [prefecture, "出身", "芸能人まとめ", "プロフィール"] + [c["name"] for c in celebs[:3]]

    return {"title": title, "html": html, "tags": tags[:10], "celebrity_name": celebs[0]["name"]}


def _pref_emoji(pref):
    """都道府県に対応する絵文字を返す（簡略版）"""
    if "北海道" in pref: return "🏔"
    if "東京" in pref: return "🏙"
    if "大阪" in pref: return "🎡"
    if "京都" in pref: return "⛩"
    if "沖縄" in pref: return "🌺"
    return "🗾"


def _build_html(celebs, prefecture, today_str):
    styles = """
<style>
.ht-wrap{font-family:'Hiragino Kaku Gothic ProN','メイリオ',sans-serif;max-width:820px;margin:0 auto;color:#333;}
.ht-header{background:linear-gradient(135deg,#1a6b3a,#56ab2f);padding:24px;border-radius:12px;margin-bottom:20px;color:#fff;text-align:center;}
.ht-header h1{margin:0;font-size:1.4em;}
.ht-header .sub{font-size:.85em;opacity:.9;margin-top:4px;}
.ht-card{background:#fff;border:1px solid #eee;border-radius:12px;padding:20px;margin-bottom:14px;box-shadow:0 2px 8px rgba(0,0,0,.05);display:flex;gap:14px;}
.ht-photo{width:80px;height:80px;border-radius:50%;object-fit:cover;border:3px solid #56ab2f;flex-shrink:0;}
.ht-photo-ph{width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,#1a6b3a,#56ab2f);display:flex;align-items:center;justify-content:center;font-size:1.8em;flex-shrink:0;}
.ht-info{flex:1;}
.ht-name{font-size:1.15em;font-weight:700;margin-bottom:3px;}
.ht-occ{display:inline-block;background:#e8f5e9;color:#1a6b3a;border-radius:16px;padding:2px 10px;font-size:.8em;font-weight:600;margin-bottom:6px;}
.ht-summary{font-size:.88em;color:#555;line-height:1.7;}
.ht-wiki{font-size:.8em;color:#1a6b3a;text-decoration:none;}
.ht-product{display:flex;gap:10px;margin-top:10px;background:#f1f8f1;border-radius:8px;padding:10px;align-items:center;}
.ht-product img{width:55px;height:75px;object-fit:cover;border-radius:4px;}
.ht-product .prod-btn{display:inline-block;background:linear-gradient(135deg,#1a6b3a,#56ab2f);color:#fff;border-radius:4px;padding:4px 10px;text-decoration:none;font-size:.78em;}
.footer-note{text-align:center;font-size:.78em;color:#bbb;margin-top:20px;padding-top:12px;border-top:1px solid #eee;}
</style>
"""
    emoji = _pref_emoji(prefecture)

    cards_html = ""
    for celeb in celebs:
        photo_html = f'<img src="{celeb["thumbnail_url"]}" alt="{celeb["name"]}" class="ht-photo">' if celeb.get("thumbnail_url") else f'<div class="ht-photo-ph">{emoji}</div>'

        wiki_link = f'<a href="{celeb["wiki_url"]}" target="_blank" rel="noopener" class="ht-wiki">Wikipediaで見る →</a>' if celeb.get("wiki_url") else ""

        birth_txt = f"（{celeb['birth_date']}生まれ）" if celeb.get("birth_date") else ""

        prod = celeb.get("dmm_product")
        prod_html = ""
        if prod:
            img = f'<img src="{prod["image_url"]}" alt="">' if prod.get("image_url") else ""
            prod_html = f"""
<div class="ht-product">
  {img}
  <div style="flex:1;font-size:.82em;">
    <div style="font-weight:600;margin-bottom:4px;">{prod['title'][:40]}{'…' if len(prod['title'])>40 else ''}</div>
    <div style="color:#e94560;font-weight:700;">{prod.get('price','')}</div>
    <a href="{prod['affiliate_url']}" class="prod-btn" target="_blank" rel="noopener">DMMで見る</a>
  </div>
</div>"""

        cards_html += f"""
<div class="ht-card">
  {photo_html}
  <div class="ht-info">
    <div class="ht-name">{celeb['name']}</div>
    <div class="ht-occ">{celeb.get('occupation','芸能人')}{birth_txt}</div>
    <div class="ht-summary">{celeb.get('summary','')[:200]}</div>
    {wiki_link}
    {prod_html}
  </div>
</div>"""

    return f"""
<div class="ht-wrap">
{styles}
<div class="ht-header">
  <h1>{emoji} {prefecture}出身の芸能人まとめ</h1>
  <div class="sub">📅 {today_str}｜Wikipediaデータより自動集計</div>
</div>
<p><strong>{prefecture}</strong>出身の俳優・歌手・タレントをご紹介します！</p>
{cards_html}
<div class="footer-note">情報元: Wikipedia（CC BY-SA 3.0）・DMM.com｜{today_str}集計</div>
</div>
"""
