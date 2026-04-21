"""
costar_generator.py
【独自記事④】共演者・関係性ネットワーク分析
特定のトレンド芸能人を起点に、ニュースタイトルから共演者や関係者を抽出し「つながり」を紹介する。
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import feedparser
import requests
import urllib.parse
from datetime import datetime

from news_fetcher import get_trending_celebrity, extract_names_from_title, _strip_media_suffix
from wiki_fetcher import get_wiki_profile
from dmm_fetcher import DMMCelebFetcher

GNEWS_SEARCH_URL = "https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP:ja"

def get_costars(celebrity_name, max_costars=3):
    """ニュース検索から、一緒によくニュースになる芸能人（共演者・関係者）を抽出"""
    # 「名前 共演」または単純に「名前」で検索して、他の名前を探す
    query = f'"{celebrity_name}"'
    url = GNEWS_SEARCH_URL.format(query=urllib.parse.quote(query))
    
    costar_counts = {}
    
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:50]:
            title = _strip_media_suffix(entry.get("title", ""))
            
            # 対象者本人の名前が含まれていない記事はスキップ
            if celebrity_name not in title:
                continue
                
            names = extract_names_from_title(title)
            
            for name in names:
                if name != celebrity_name:
                    costar_counts[name] = costar_counts.get(name, 0) + 1
                    
        # 出現回数順にソート
        sorted_costars = sorted(costar_counts.items(), key=lambda x: x[1], reverse=True)
        return [name for name, count in sorted_costars][:max_costars]
        
    except Exception as e:
        print(f"[costar] ニュース検索エラー: {e}")
        return []

def run():
    """共演ネットワーク記事を生成"""
    print("[costar] ターゲット芸能人を選定中...")
    main_celeb = get_trending_celebrity()
    
    if not main_celeb:
        print("[costar] ターゲットが取得できませんでした")
        return None
        
    print(f"[costar] ターゲット: {main_celeb}")
    
    # 共演者リストを取得
    costar_names = get_costars(main_celeb, max_costars=3)
    
    if not costar_names:
        print("[costar] 共演者が見つかりませんでした")
        return None
        
    print(f"[costar] 共演者: {costar_names}")
    
    today_str = datetime.now().strftime("%Y年%m月%d日")
    
    # メイン芸能人のプロフ
    main_profile = get_wiki_profile(main_celeb)
    
    # 共演者たちのデータ収集
    dmm = DMMCelebFetcher()
    costars_data = []
    
    for name in costar_names:
        profile = get_wiki_profile(name)
        dmm_items = dmm.search_celebrity_products(name, max_items=1)
        product = dmm_items[0] if dmm_items else None
        
        costars_data.append({
            "name": name,
            "profile": profile,
            "product": product
        })
        
    html = _build_html(main_celeb, main_profile, costars_data, today_str)
    title = f"【相関図】{main_celeb}と最近よく話題になる共演者・関係者まとめ【{today_str}】"
    tags = [main_celeb, "共演", "相関図", "エンタメ"] + costar_names
    
    return {"title": title, "html": html, "tags": tags[:10], "celebrity_name": main_celeb}

def _build_html(main_celeb, main_profile, costars_data, today_str):
    styles = """
<style>
.net-wrap { font-family: 'Hiragino Kaku Gothic ProN', 'メイリオ', sans-serif; max-width: 820px; margin: 0 auto; color: #333; line-height: 1.6; }
.net-header { background: linear-gradient(135deg, #005c97, #363795); padding: 24px; border-radius: 12px; margin-bottom: 24px; color: #fff; text-align: center; }
.net-header h1 { margin: 0; font-size: 1.4em; }
.net-header .sub { font-size: 0.85em; opacity: 0.9; margin-top: 6px; }
.main-target { text-align: center; margin-bottom: 30px; }
.main-photo { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 4px solid #363795; margin-bottom: 10px; }
.main-photo-ph { width: 100px; height: 100px; border-radius: 50%; background: #363795; display: inline-flex; align-items: center; justify-content: center; font-size: 2.5em; color: white; margin-bottom: 10px; }
.main-name { font-size: 1.4em; font-weight: 700; color: #005c97; }
.relationship-line { text-align: center; font-size: 2em; color: #999; margin: -10px 0 20px; }
.costar-card { background: #fff; border: 1px solid #ddd; border-radius: 12px; padding: 20px; margin-bottom: 16px; display: flex; gap: 16px; align-items: flex-start; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
.costar-photo { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.costar-photo-ph { width: 80px; height: 80px; border-radius: 50%; background: #eee; display: flex; align-items: center; justify-content: center; font-size: 2em; flex-shrink: 0; }
.costar-info { flex: 1; }
.costar-name { font-size: 1.2em; font-weight: 700; margin-bottom: 5px; color: #222; }
.costar-desc { font-size: 0.85em; color: #555; margin-bottom: 10px; }
.prod-box { background: #f8f9fa; border-radius: 8px; padding: 10px; display: flex; gap: 10px; align-items: center; }
.prod-box img { width: 50px; height: 70px; object-fit: cover; border-radius: 4px; }
.prod-detail { flex: 1; font-size: 0.8em; }
.prod-btn { display: inline-block; background: #005c97; color: #fff; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 0.9em; margin-top: 4px; }
.footer-note { text-align: center; font-size: 0.78em; color: #bbb; margin-top: 30px; padding-top: 15px; border-top: 1px solid #eee; }
</style>
"""

    main_img = f'<img src="{main_profile["thumbnail_url"]}" alt="{main_celeb}" class="main-photo">' if main_profile and main_profile.get("thumbnail_url") else f'<div class="main-photo-ph">👤</div>'
    main_desc = main_profile.get("summary", "")[:100] + "..." if main_profile else ""

    cards_html = ""
    for data in costars_data:
        name = data["name"]
        prof = data["profile"]
        prod = data["product"]
        
        img = f'<img src="{prof["thumbnail_url"]}" alt="{name}" class="costar-photo">' if prof and prof.get("thumbnail_url") else '<div class="costar-photo-ph">👤</div>'
        desc = prof.get("summary", "")[:150] + "..." if prof else f"{name}の最新情報が注目されています。"
        
        prod_html = ""
        if prod:
            p_img = f'<img src="{prod["image_url"]}" alt="">' if prod.get("image_url") else ""
            prod_html = f"""
            <div class="prod-box">
                {p_img}
                <div class="prod-detail">
                    <div style="font-weight:600; margin-bottom:4px;">{prod["title"][:40]}</div>
                    <a href="{prod['affiliate_url']}" class="prod-btn" target="_blank" rel="noopener">関連作品を見る</a>
                </div>
            </div>
            """
            
        cards_html += f"""
        <div class="costar-card">
            {img}
            <div class="costar-info">
                <div class="costar-name">🤝 {name}</div>
                <div class="costar-desc">{desc}</div>
                {prod_html}
            </div>
        </div>
        """

    return f"""
<div class="net-wrap">
    {styles}
    <div class="net-header">
        <h1>🔗 芸能界 人物相関図・関係性まとめ</h1>
        <div class="sub">📅 {today_str} 更新 ｜ 最新ニュースに基づく自動抽出</div>
    </div>
    
    <div class="main-target">
        <p>本日注目されているのはこの人！</p>
        {main_img}
        <div class="main-name">{main_celeb}</div>
        <p style="font-size:0.85em; color:#666; max-width:500px; margin: 10px auto;">{main_desc}</p>
    </div>
    
    <div class="relationship-line">⬇️ 話題の共演者・関係者 ⬇️</div>
    
    {cards_html}
    
    <div class="footer-note">情報元: Google News共起分析・Wikipedia・DMM.com</div>
</div>
"""
