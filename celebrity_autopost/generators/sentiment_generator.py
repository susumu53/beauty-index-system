"""
sentiment_generator.py
【独自記事⑤】ニュース感情分類（ポジティブ・ネガティブ・注目）
Google News のエンタメ記事をキーワードで分類し、バッジ付きで一覧表示。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import feedparser
import re
from datetime import datetime
from news_fetcher import _strip_media_suffix, extract_names_from_title
from dmm_fetcher import DMMCelebFetcher

GNEWS_ENTAME_URL = "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=ja&gl=JP&ceid=JP:ja"

POSITIVE_KEYS = ["結婚", "復帰", "受賞", "主演決定", "デビュー", "感謝", "祝福", "記念"]
NEGATIVE_KEYS = ["炎上", "謝罪", "離婚", "批判", "失言", "逮捕", "問題", "訴訟"]
HOT_KEYS = ["熱愛", "交際", "破局", "不倫", "スキャンダル"]

def _classify(title):
    for kw in NEGATIVE_KEYS:
        if kw in title:
            return "negative"
    for kw in POSITIVE_KEYS:
        if kw in title:
            return "positive"
    for kw in HOT_KEYS:
        if kw in title:
            return "hot"
    return "neutral"

def _badge_html(cat):
    if cat == "positive":
        return "<span style='background:#e0f8e9;color:#1a7f37;padding:2px 6px;border-radius:4px;font-size:.8em;'>👍 ポジティブ</span>"
    if cat == "negative":
        return "<span style='background:#ffe0e0;color:#c00;padding:2px 6px;border-radius:4px;font-size:.8em;'>⚠️ ネガティブ</span>"
    if cat == "hot":
        return "<span style='background:#fff4e0;color:#d97706;padding:2px 6px;border-radius:4px;font-size:.8em;'>🔥 注目</span>"
    return "<span style='background:#f0f0f0;color:#666;padding:2px 6px;border-radius:4px;font-size:.8em;'>📄 その他</span>"

def run():
    """感情分類記事を生成"""
    today = datetime.now().strftime("%Y年%m月%d日")
    print("[sentiment] エンタメニュース取得中...")
    feed = feedparser.parse(GNEWS_ENTAME_URL)
    entries = feed.entries[:80]

    categorized = {"positive": [], "negative": [], "hot": [], "neutral": []}
    for entry in entries:
        raw = entry.get("title", "")
        clean = _strip_media_suffix(raw)
        cat = _classify(clean)
        source = entry.get("source", {})
        src_name = source.get("title", "") if isinstance(source, dict) else ""
        link = entry.get("link", "")
        categorized[cat].append({"title": clean, "link": link, "source": src_name})

    # DMM商品取得（各カテゴリ上位1件）
    dmm = DMMCelebFetcher()
    dmm_products = {}
    for cat, items in categorized.items():
        if not items:
            continue
        # 先頭記事から芸能人名抽出し商品取得
        name = None
        for cand in items:
            names = extract_names_from_title(cand["title"])
            if names:
                name = names[0]
                break
        if name:
            prod = dmm.search_celebrity_products(name, max_items=1)
            if prod:
                dmm_products[cat] = prod[0]

    html = _build_html(categorized, dmm_products, today)
    title = f"【{today}】エンタメニュース感情分類まとめ｜ポジティブ・ネガティブ・注目"
    tags = ["感情分類", "エンタメニュース", "ポジティブ", "ネガティブ", "注目"]
    return {"title": title, "html": html, "tags": tags, "celebrity_name": "ニュース分類"}

def _build_html(categorized, dmm_products, today):
    styles = """
<style>
.sent-wrap{font-family:'Hiragino Kaku Gothic ProN','メイリオ',sans-serif;max-width:820px;margin:0 auto;color:#333;}
.sent-header{background:linear-gradient(135deg,#ff8c00,#ffb347);padding:24px;border-radius:12px;margin-bottom:20px;color:#fff;text-align:center;}
.sent-header h1{margin:0;font-size:1.4em;}
.sent-section{margin-bottom:24px;}
.sent-section h2{font-size:1.2em;color:#ff8c00;margin-bottom:8px;display:flex;align-items:center;gap:8px;}
.sent-list{list-style:none;padding:0;margin:0;}
.sent-list li{margin-bottom:8px;display:flex;align-items:center;gap:6px;}
.sent-list a{color:#0066cc;text-decoration:none;}
.sent-list a:hover{opacity:.8;}
.prod-card{background:#fff8e1;border:1px solid #ffd4a6;border-radius:8px;padding:12px;margin-top:12px;display:flex;gap:10px;align-items:center;}
.prod-card img{width:55px;height:75px;object-fit:cover;border-radius:4px;}
.prod-card .info{flex:1;font-size:.85em;}
.prod-card .info .title{font-weight:600;margin-bottom:4px;}
.prod-card .btn{display:inline-block;background:#ff8c00;color:#fff;padding:4px 10px;border-radius:4px;text-decoration:none;font-size:.78em;}
.footer-note{text-align:center;font-size:.78em;color:#bbb;margin-top:20px;padding-top:12px;border-top:1px solid #eee;}
</style>
"""
    sections_html = ""
    order = ["positive", "hot", "negative", "neutral"]
    cat_labels = {"positive": "ポジティブニュース", "negative": "ネガティブニュース", "hot": "注目ニュース", "neutral": "その他ニュース"}
    for cat in order:
        items = categorized.get(cat, [])
        if not items:
            continue
        sections_html += f"<div class='sent-section'><h2>{_badge_html(cat)} {cat_labels[cat]}</h2><ul class='sent-list'>"
        for it in items[:5]:
            sections_html += f"<li>{_badge_html(cat)} <a href='{it['link']}' target='_blank' rel='noopener'>{it['title']}</a>" 
            if it['source']:
                sections_html += f" <span style='color:#666;font-size:.8em;'>({it['source']})</span>"
            sections_html += "</li>"
        sections_html += "</ul>"
        # DMM product for this category
        prod = dmm_products.get(cat)
        if prod:
            img = f'<img src="{prod["image_url"]}" alt="">' if prod.get("image_url") else ""
            sections_html += f"""
<div class='prod-card'>
  {img}
  <div class='info'>
    <div class='title'>{prod['title'][:40]}{'…' if len(prod['title'])>40 else ''}</div>
    <a href='{prod['affiliate_url']}' class='btn' target='_blank' rel='noopener'>DMMで見る</a>
  </div>
</div>"""
        sections_html += "</div>"
    return f"""
<div class='sent-wrap'>
{styles}
<div class='sent-header'>
  <h1>📰 エンタメニュース感情分類まとめ</h1>
  <div class='sub'>📅 {today}｜Google News エンタメセクションから自動抽出</div>
</div>
{sections_html}
<div class='footer-note'>情報元: Google News（CC BY 4.0）｜DMM商品は自動マッチング</div>
</div>
"""
