"""
buzz_ranking_generator.py
【独自記事①】芸能界バズりスコアランキング
Google News の件数・キーワードから「今日の芸能人注目度スコア」を算出してTOP5を紹介する。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import re
import feedparser
from datetime import datetime
from news_fetcher import extract_names_from_title, _strip_media_suffix
from dmm_fetcher import DMMCelebFetcher

GNEWS_ENTAME_URL = "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=ja&gl=JP&ceid=JP:ja"
GNEWS_SEARCH_URL = "https://news.google.com/rss/search?q={name}&hl=ja&gl=JP&ceid=JP:ja"

# ニュース内のキーワードスコア（スコアを加算するキーワード）
HOT_KEYWORDS = {
    "熱愛": 25, "交際": 20, "結婚": 20, "離婚": 20,
    "炎上": 25, "謝罪": 20, "批判": 15, "問題": 10,
    "主演": 15, "出演決定": 15, "受賞": 15, "デビュー": 15,
    "引退": 20, "復帰": 18, "妊娠": 22, "破局": 18,
}


def _calc_buzz_score(name, titles):
    """芸能人名とニュースタイトルリストからバズりスコアを算出"""
    score = 0
    sources = set()

    for title, source in titles:
        if name in title:
            score += 10  # 1記事につき10点
            for kw, pts in HOT_KEYWORDS.items():
                if kw in title:
                    score += pts
            if source:
                sources.add(source)

    # 複数ソースに登場するとボーナス
    score += (len(sources) - 1) * 8

    return score, list(sources)


def _score_bar(score):
    """スコアを炎マークのビジュアルバーに変換"""
    flames = min(5, max(1, score // 20))
    return "🔥" * flames + "　" + str(score) + "pt"


def _medal(rank):
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    return medals.get(rank, f"{rank}位")


def run():
    """バズりスコアランキング記事を生成"""
    today = datetime.now().strftime("%Y年%m月%d日")
    print("[buzz] エンタメニュース取得中...")

    feed = feedparser.parse(GNEWS_ENTAME_URL)
    all_titles = []
    candidate_scores_raw = {}

    for entry in feed.entries[:80]:
        raw = entry.get("title", "")
        src = entry.get("source", {})
        source = src.get("title", "") if isinstance(src, dict) else ""
        clean = _strip_media_suffix(raw)
        all_titles.append((clean, source))

        names = extract_names_from_title(clean)
        for name in names:
            candidate_scores_raw[name] = candidate_scores_raw.get(name, 0) + 1

    print("[buzz] 候補数: " + str(len(candidate_scores_raw)))

    # スコア算出
    ranked = []
    for name in candidate_scores_raw:
        score, sources = _calc_buzz_score(name, all_titles)
        if score > 0:
            ranked.append((name, score, sources))

    ranked.sort(key=lambda x: x[1], reverse=True)
    top5 = ranked[:5]

    if not top5:
        print("[buzz] ランキングデータが不十分")
        return None

    print("[buzz] TOP5: " + str([n for n, s, _ in top5]))

    # DMM商品取得（TOP5の各人）
    dmm = DMMCelebFetcher()
    products_map = {}
    for name, _, _ in top5:
        items = dmm.search_celebrity_products(name, max_items=1)
        if items:
            products_map[name] = items[0]

    # HTML生成
    html = _build_html(top5, products_map, today)
    title = f"【{today}】芸能界バズりスコアランキングTOP5｜今日最も注目の芸能人は？"
    tags = ["バズりランキング", "芸能界", "注目", "エンタメ", "ランキング"]
    for name, _, _ in top5[:3]:
        tags.append(name)

    return {"title": title, "html": html, "tags": tags[:10], "celebrity_name": top5[0][0]}


def _build_html(top5, products_map, today):
    styles = """
<style>
.buzz-wrap{font-family:'Hiragino Kaku Gothic ProN','メイリオ',sans-serif;max-width:820px;margin:0 auto;color:#333;}
.buzz-header{background:linear-gradient(135deg,#ff6b35,#f7c59f);padding:24px;border-radius:12px;margin-bottom:20px;color:#fff;text-align:center;}
.buzz-header h1{margin:0;font-size:1.4em;}
.buzz-header .sub{font-size:.85em;opacity:.9;margin-top:6px;}
.score-badge{display:inline-block;background:#fff;color:#ff6b35;border-radius:20px;padding:3px 12px;font-weight:700;font-size:.9em;margin-left:8px;}
.rank-card{background:#fff;border:1px solid #eee;border-radius:10px;padding:20px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.06);display:flex;gap:16px;align-items:flex-start;}
.rank-num{font-size:2em;min-width:50px;text-align:center;}
.rank-info{flex:1;}
.rank-name{font-size:1.2em;font-weight:700;color:#222;margin-bottom:4px;}
.rank-score{font-size:1em;color:#ff6b35;font-weight:700;margin-bottom:6px;}
.rank-sources{font-size:.8em;color:#888;}
.rank-product{display:flex;gap:10px;margin-top:10px;background:#fafafa;border-radius:8px;padding:10px;align-items:center;}
.rank-product img{width:60px;height:80px;object-fit:cover;border-radius:4px;}
.rank-product .prod-info{flex:1;font-size:.82em;}
.rank-product .prod-title{color:#333;margin-bottom:4px;font-weight:600;}
.rank-product .prod-btn{display:inline-block;background:#ff6b35;color:#fff;border-radius:4px;padding:4px 10px;text-decoration:none;font-size:.78em;}
.rank-product .prod-btn:hover{opacity:.85;}
.method-box{background:#fff8f0;border:1px solid #ffd4b5;border-radius:8px;padding:16px;margin-top:20px;font-size:.85em;color:#666;}
.method-box h3{color:#ff6b35;font-size:1em;margin:0 0 8px;}
.footer-note{text-align:center;font-size:.78em;color:#bbb;margin-top:20px;padding-top:12px;border-top:1px solid #eee;}
</style>
"""

    cards_html = ""
    for i, (name, score, sources) in enumerate(top5):
        rank = i + 1
        prod = products_map.get(name)
        prod_html = ""
        if prod:
            img = f'<img src="{prod["image_url"]}" alt="{prod["title"]}">' if prod.get("image_url") else ""
            prod_html = f"""
<div class="rank-product">
  {img}
  <div class="prod-info">
    <div class="prod-title">{prod["title"][:40]}{'…' if len(prod["title"])>40 else ''}</div>
    <div style="color:#e94560;font-weight:700;font-size:.85em;">{prod.get('price','')}</div>
    <a href="{prod['affiliate_url']}" class="prod-btn" target="_blank" rel="noopener">DMMで見る</a>
  </div>
</div>"""

        src_txt = "・".join(sources[:3]) if sources else ""

        cards_html += f"""
<div class="rank-card">
  <div class="rank-num">{_medal(rank)}</div>
  <div class="rank-info">
    <div class="rank-name">{name}<span class="score-badge">{score}pt</span></div>
    <div class="rank-score">{_score_bar(score)}</div>
    {'<div class="rank-sources">報道媒体: ' + src_txt + '</div>' if src_txt else ''}
    {prod_html}
  </div>
</div>"""

    method_html = """
<div class="method-box">
  <h3>スコア算出方法</h3>
  <p>本ランキングは当サイト独自のバズりスコアを使用しています。<br>
  📊 1記事あたり +10pt｜熱愛・炎上など注目キーワード +15〜25pt｜複数媒体掲載 +8pt/媒体<br>
  集計対象: Google News エンタメセクション・本日更新分</p>
</div>"""

    return f"""
<div class="buzz-wrap">
{styles}
<div class="buzz-header">
  <h1>🔥 芸能界バズりスコアランキング TOP5</h1>
  <div class="sub">📅 {today} 更新｜当サイト独自スコアで算出</div>
</div>
{cards_html}
{method_html}
<div class="footer-note">情報元: Google News（{today}集計）｜商品情報: DMM.com</div>
</div>
"""
