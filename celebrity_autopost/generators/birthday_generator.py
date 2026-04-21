"""
birthday_generator.py
【独自記事②】今日が誕生日の芸能人まとめ
Wikipedia の on-this-day API から当日誕生日の著名人を取得し、芸能人をフィルタして紹介する。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
import re
from datetime import datetime
from wiki_fetcher import get_wiki_profile
from dmm_fetcher import DMMCelebFetcher

WIKI_HEADERS = {"User-Agent": "celebrity-autopost-bot/1.0"}

CELEB_OCCUPATIONS = [
    "俳優", "女優", "歌手", "タレント", "アイドル", "モデル", "声優",
    "お笑い芸人", "映画監督", "脚本家", "ミュージシャン", "アーティスト",
    "司会者", "グラビア", "漫才師", "コメディアン",
]


def _is_celebrity(text):
    """テキストに芸能人職業ワードが含まれるか判定"""
    for occ in CELEB_OCCUPATIONS:
        if occ in text:
            return True
    return False


def get_today_birthdays(month, day, max_celebs=5):
    """Wikipedia の on-this-day API から誕生日著名人を取得"""
    url = f"https://ja.wikipedia.org/api/rest_v1/feed/onthisday/births/{month:02d}/{day:02d}"
    try:
        r = requests.get(url, headers=WIKI_HEADERS, timeout=10)
        if r.status_code != 200:
            print("[birthday] Wikipedia on-this-day API エラー: " + str(r.status_code))
            return []

        data = r.json()
        births = data.get("births", [])
        print("[birthday] 誕生日著名人候補: " + str(len(births)) + "人")

        celebs = []
        for item in births:
            text = item.get("text", "") + " " + item.get("pages", [{}])[0].get("extract", "") if item.get("pages") else item.get("text", "")

            if not _is_celebrity(text):
                continue

            pages = item.get("pages", [])
            if not pages:
                continue

            page = pages[0]
            name = page.get("titles", {}).get("normalized", "")
            extract = page.get("extract", "")
            thumbnail = page.get("thumbnail", {})
            thumbnail_url = thumbnail.get("source", "") if thumbnail else ""
            wiki_url = page.get("content_urls", {}).get("desktop", {}).get("page", "")
            year = item.get("year", "")

            if not name:
                continue

            celebs.append({
                "name": name,
                "birth_year": year,
                "extract": extract[:300] + "..." if len(extract) > 300 else extract,
                "thumbnail_url": thumbnail_url,
                "wiki_url": wiki_url,
            })

            if len(celebs) >= max_celebs:
                break

        return celebs

    except Exception as e:
        print("[birthday] エラー: " + str(e))
        return []


def run():
    """誕生日記事を生成"""
    now = datetime.now()
    month = now.month
    day = now.day
    today_str = now.strftime("%Y年%m月%d日")

    print(f"[birthday] {month}月{day}日の誕生日芸能人を検索中...")
    celebs = get_today_birthdays(month, day, max_celebs=5)

    if not celebs:
        print("[birthday] 誕生日芸能人が見つかりませんでした")
        return None

    print("[birthday] 見つかった人数: " + str(len(celebs)))

    # DMM商品取得
    dmm = DMMCelebFetcher()
    for celeb in celebs:
        items = dmm.search_celebrity_products(celeb["name"], max_items=1)
        celeb["dmm_product"] = items[0] if items else None

    html = _build_html(celebs, month, day, today_str)
    title = f"【{month}月{day}日】今日が誕生日の芸能人まとめ｜{today_str}"
    tags = ["誕生日", "芸能人", f"{month}月{day}日", "誕生日まとめ"] + [c["name"] for c in celebs[:3]]

    return {"title": title, "html": html, "tags": tags[:10], "celebrity_name": celebs[0]["name"]}


def _build_html(celebs, month, day, today_str):
    styles = """
<style>
.bday-wrap{font-family:'Hiragino Kaku Gothic ProN','メイリオ',sans-serif;max-width:820px;margin:0 auto;color:#333;}
.bday-header{background:linear-gradient(135deg,#7b2ff7,#f107a3);padding:24px;border-radius:12px;margin-bottom:20px;color:#fff;text-align:center;}
.bday-header h1{margin:0;font-size:1.5em;}
.bday-header .sub{font-size:.85em;opacity:.9;margin-top:4px;}
.bday-card{background:#fff;border:1px solid #eee;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.06);display:flex;gap:16px;}
.bday-photo{width:90px;height:90px;border-radius:50%;object-fit:cover;border:3px solid #f107a3;flex-shrink:0;}
.bday-photo-ph{width:90px;height:90px;border-radius:50%;background:linear-gradient(135deg,#7b2ff7,#f107a3);display:flex;align-items:center;justify-content:center;font-size:2em;flex-shrink:0;}
.bday-info{flex:1;}
.bday-name{font-size:1.2em;font-weight:700;margin-bottom:4px;}
.bday-age{display:inline-block;background:#fce4f5;color:#c0055e;border-radius:20px;padding:2px 10px;font-size:.85em;font-weight:600;margin-bottom:6px;}
.bday-text{font-size:.88em;color:#555;line-height:1.7;}
.bday-wiki{font-size:.8em;color:#7b2ff7;text-decoration:none;}
.bday-wiki:hover{text-decoration:underline;}
.bday-product{display:flex;gap:10px;margin-top:10px;background:#faf5ff;border-radius:8px;padding:10px;align-items:center;}
.bday-product img{width:55px;height:75px;object-fit:cover;border-radius:4px;}
.bday-product .prod-info{flex:1;font-size:.82em;}
.bday-product .prod-btn{display:inline-block;background:linear-gradient(135deg,#7b2ff7,#f107a3);color:#fff;border-radius:4px;padding:4px 10px;text-decoration:none;font-size:.78em;}
.footer-note{text-align:center;font-size:.78em;color:#bbb;margin-top:20px;padding-top:12px;border-top:1px solid #eee;}
</style>
"""

    cards_html = ""
    current_year = datetime.now().year

    for celeb in celebs:
        photo_html = ""
        if celeb.get("thumbnail_url"):
            photo_html = f'<img src="{celeb["thumbnail_url"]}" alt="{celeb["name"]}" class="bday-photo">'
        else:
            photo_html = '<div class="bday-photo-ph">🎂</div>'

        age_html = ""
        if celeb.get("birth_year"):
            try:
                age = current_year - int(celeb["birth_year"])
                age_html = f'<div class="bday-age">🎂 {celeb["birth_year"]}年生まれ・今年{age}歳</div>'
            except Exception:
                pass

        wiki_link = ""
        if celeb.get("wiki_url"):
            wiki_link = f'<a href="{celeb["wiki_url"]}" target="_blank" rel="noopener" class="bday-wiki">Wikipediaで詳しく見る →</a>'

        prod = celeb.get("dmm_product")
        prod_html = ""
        if prod:
            img = f'<img src="{prod["image_url"]}" alt="">' if prod.get("image_url") else ""
            prod_html = f"""
<div class="bday-product">
  {img}
  <div class="prod-info">
    <div class="prod-title" style="font-weight:600;margin-bottom:4px;">{prod["title"][:40]}{'…' if len(prod["title"])>40 else ''}</div>
    <div style="color:#e94560;font-weight:700;">{prod.get('price','')}</div>
    <a href="{prod['affiliate_url']}" class="prod-btn" target="_blank" rel="noopener">DMMで見る</a>
  </div>
</div>"""

        cards_html += f"""
<div class="bday-card">
  {photo_html}
  <div class="bday-info">
    <div class="bday-name">🎉 {celeb["name"]}</div>
    {age_html}
    <div class="bday-text">{celeb.get("extract","")}</div>
    {wiki_link}
    {prod_html}
  </div>
</div>"""

    return f"""
<div class="bday-wrap">
{styles}
<div class="bday-header">
  <h1>🎂 {month}月{day}日が誕生日の芸能人まとめ</h1>
  <div class="sub">📅 {today_str}｜Wikipedia誕生日データより</div>
</div>
<p>本日 <strong>{month}月{day}日</strong> が誕生日の芸能人・著名人をご紹介します！</p>
{cards_html}
<div class="footer-note">情報元: Wikipedia（CC BY-SA 3.0）・DMM.com｜{today_str}集計</div>
</div>
"""
