from datetime import datetime


def build_article_html(celebrity_name, wiki_profile, news_list, dmm_products, youtube_video_id=None):
    """
    芸能人記事の HTML を組み立てる（AI不使用、テンプレートベース）
    
    Args:
        celebrity_name (str): 芸能人名
        wiki_profile (dict|None): Wikipedia プロフィールデータ
        news_list (list): 最新ニュースリスト
        dmm_products (list): DMM商品リスト
        youtube_video_id (str|None): YouTube動画ID（フォールバック）
    
    Returns:
        str: HTML文字列
    """
    
    today = datetime.now().strftime("%Y年%m月%d日")
    
    # ── CSS（インライン埋め込みでSeesaa互換） ──
    styles = """
<style>
  .celeb-article { font-family: 'Hiragino Kaku Gothic ProN', 'メイリオ', sans-serif; line-height: 1.8; color: #333; max-width: 800px; margin: 0 auto; }
  .celeb-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: #fff; padding: 28px 24px; border-radius: 12px; margin-bottom: 24px; display: flex; gap: 20px; align-items: center; }
  .celeb-header-photo { width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 3px solid #e94560; flex-shrink: 0; }
  .celeb-header-photo-placeholder { width: 120px; height: 120px; border-radius: 50%; background: #e94560; display: flex; align-items: center; justify-content: center; font-size: 48px; flex-shrink: 0; }
  .celeb-header-info h1 { font-size: 1.6em; margin: 0 0 6px; font-weight: 700; }
  .celeb-header-info .meta { font-size: 0.85em; color: #adb5bd; }
  .celeb-header-info .tags span { display: inline-block; background: rgba(233,69,96,0.3); border: 1px solid #e94560; color: #fff; border-radius: 20px; padding: 2px 10px; font-size: 0.75em; margin: 4px 4px 0 0; }
  .section { background: #fff; border: 1px solid #e8e8e8; border-radius: 10px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
  .section-title { font-size: 1.15em; font-weight: 700; color: #0f3460; border-left: 4px solid #e94560; padding-left: 12px; margin: 0 0 16px; }
  .news-item { border-bottom: 1px dashed #ddd; padding: 12px 0; }
  .news-item:last-child { border-bottom: none; }
  .news-item h3 { font-size: 1em; margin: 0 0 6px; }
  .news-item h3 a { color: #0f3460; text-decoration: none; }
  .news-item h3 a:hover { text-decoration: underline; color: #e94560; }
  .news-excerpt { background: #f8f9fa; border-left: 3px solid #ccc; padding: 8px 12px; font-size: 0.88em; color: #555; margin: 6px 0; border-radius: 0 4px 4px 0; }
  .news-source { font-size: 0.8em; color: #999; }
  .wiki-text { font-size: 0.95em; color: #444; white-space: pre-line; }
  .profile-table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
  .profile-table tr th { background: #f0f4f8; color: #0f3460; padding: 8px 12px; text-align: left; width: 30%; border: 1px solid #ddd; font-weight: 600; }
  .profile-table tr td { padding: 8px 12px; border: 1px solid #ddd; background: #fff; }
  .profile-wiki-link { display: inline-block; margin-top: 10px; font-size: 0.85em; color: #0f3460; text-decoration: none; }
  .profile-wiki-link:hover { text-decoration: underline; }
  .dmm-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 14px; }
  .dmm-card { border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; text-align: center; transition: transform 0.2s, box-shadow 0.2s; }
  .dmm-card:hover { transform: translateY(-3px); box-shadow: 0 6px 16px rgba(0,0,0,0.12); }
  .dmm-card img { width: 100%; aspect-ratio: 2/3; object-fit: cover; display: block; }
  .dmm-card .card-body { padding: 8px; }
  .dmm-card .card-title { font-size: 0.78em; color: #333; margin: 0 0 4px; line-height: 1.4; -webkit-line-clamp: 3; display: -webkit-box; -webkit-box-orient: vertical; overflow: hidden; }
  .dmm-card .card-price { font-size: 0.82em; color: #e94560; font-weight: 700; margin-bottom: 6px; }
  .dmm-card .card-btn { display: block; background: linear-gradient(135deg, #e94560, #c0392b); color: #fff; text-decoration: none; font-size: 0.75em; padding: 5px 8px; border-radius: 4px; font-weight: 600; }
  .dmm-card .card-btn:hover { opacity: 0.88; }
  .youtube-wrapper { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 8px; }
  .youtube-wrapper iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }
  .no-products { text-align: center; color: #999; font-size: 0.9em; padding: 16px; }
  .footer-note { text-align: center; font-size: 0.78em; color: #bbb; margin-top: 24px; padding-top: 12px; border-top: 1px solid #eee; }
  @media (max-width: 600px) { .celeb-header { flex-direction: column; text-align: center; } .dmm-grid { grid-template-columns: repeat(2, 1fr); } }
</style>
"""

    # ── ヘッダーセクション ──
    occupation = (wiki_profile or {}).get("occupation", "芸能人")
    thumbnail_url = (wiki_profile or {}).get("thumbnail_url", "")
    birth_date = (wiki_profile or {}).get("birth_date", "")
    
    if thumbnail_url:
        photo_html = f'<img src="{thumbnail_url}" alt="{celebrity_name}" class="celeb-header-photo" />'
    else:
        photo_html = f'<div class="celeb-header-photo-placeholder">🎤</div>'
    
    tags_html = "".join([f"<span>{t}</span>" for t in [occupation, "芸能人", "最新情報"] if t])
    
    header_html = f"""
<div class="celeb-header">
  {photo_html}
  <div class="celeb-header-info">
    <h1>{celebrity_name}の最新情報まとめ【{today}】</h1>
    <div class="meta">📅 {today} 更新</div>
    <div class="tags">{tags_html}</div>
  </div>
</div>
"""

    # ── ① 最新ニュースセクション ──
    news_html = ""
    if news_list:
        items_html = ""
        for news in news_list:
            excerpt_html = ""
            if news.get("excerpt"):
                excerpt_html = f'<blockquote class="news-excerpt">{news["excerpt"]}</blockquote>'
            
            source_html = ""
            if news.get("source") or news.get("published"):
                source_html = f'<div class="news-source">📰 {news.get("source", "")} {news.get("published", "")}</div>'
            
            items_html += f"""
<div class="news-item">
  <h3><a href="{news['link']}" target="_blank" rel="noopener noreferrer">{news['title']}</a></h3>
  {excerpt_html}
  {source_html}
</div>
"""
        
        news_html = f"""
<div class="section">
  <div class="section-title">📰 最新ニュース</div>
  {items_html}
</div>
"""
    
    # ── ② プロフィール・経歴セクション ──
    profile_html = ""
    if wiki_profile:
        rows = ""
        if wiki_profile.get("birth_date"):
            rows += f'<tr><th>生年月日</th><td>{wiki_profile["birth_date"]}</td></tr>'
        if wiki_profile.get("occupation"):
            rows += f'<tr><th>職業</th><td>{wiki_profile["occupation"]}</td></tr>'
        
        table_html = f'<table class="profile-table">{rows}</table>' if rows else ""
        
        wiki_link = ""
        if wiki_profile.get("wiki_url"):
            wiki_link = f'<a href="{wiki_profile["wiki_url"]}" target="_blank" rel="noopener noreferrer" class="profile-wiki-link">📖 Wikipediaで詳しく見る</a>'
        
        profile_html = f"""
<div class="section">
  <div class="section-title">👤 プロフィール・経歴</div>
  {table_html}
  <div class="wiki-text" style="margin-top:12px;">{wiki_profile.get("summary", "")}</div>
  {wiki_link}
</div>
"""

    # ── ③ DMM 商品セクション ──
    dmm_html = ""
    if dmm_products:
        cards_html = ""
        for product in dmm_products:
            img_html = ""
            if product.get("image_url"):
                img_html = f'<img src="{product["image_url"]}" alt="{product["title"]}" loading="lazy" />'
            else:
                img_html = '<div style="height:210px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;color:#999">📷</div>'
            
            review_html = ""
            if product.get("review_average"):
                stars = "⭐" * round(float(product["review_average"]) / 2) if product["review_average"] else ""
                review_html = f'<div style="font-size:0.75em;color:#f39c12;">{stars} {product["review_average"]}</div>'
            
            cards_html += f"""
<div class="dmm-card">
  {img_html}
  <div class="card-body">
    <div class="card-title">{product['title']}</div>
    {review_html}
    <div class="card-price">{product.get('price', '')}</div>
    <a href="{product['affiliate_url']}" class="card-btn" target="_blank" rel="noopener noreferrer">DMMで見る</a>
  </div>
</div>
"""
        
        dmm_html = f"""
<div class="section">
  <div class="section-title">🛒 関連作品・グッズ（DMM）</div>
  <div class="dmm-grid">{cards_html}</div>
  <p style="font-size:0.78em;color:#999;margin-top:10px;">※ 本記事のリンクはアフィリエイトリンクを含みます。</p>
</div>
"""
    elif youtube_video_id:
        # YouTube フォールバック
        dmm_html = f"""
<div class="section">
  <div class="section-title">🎬 関連動画</div>
  <div class="youtube-wrapper">
    <iframe src="https://www.youtube.com/embed/{youtube_video_id}" 
            title="{celebrity_name} 動画" allowfullscreen></iframe>
  </div>
</div>
"""
    else:
        dmm_html = f"""
<div class="section">
  <div class="section-title">🛒 関連作品・グッズ（DMM）</div>
  <div class="no-products">現在、関連商品の情報を取得中です。</div>
</div>
"""

    # ── フッター ──
    footer_html = f"""
<div class="footer-note">
  この記事の情報は {today} 時点のものです。最新情報は各公式サイトをご確認ください。<br>
  情報元: Google News・Wikipedia（CC BY-SA 3.0）・DMM.com
</div>
"""

    # ── 全体を組み立て ──
    full_html = f"""
<div class="celeb-article">
{styles}
{header_html}
{news_html}
{profile_html}
{dmm_html}
{footer_html}
</div>
"""
    return full_html


def build_article_title(celebrity_name, news_list):
    """SEO を意識した記事タイトルを生成する"""
    today = datetime.now().strftime("%Y年%m月%d日")
    
    # ニュースがあればそのキーワードをタイトルに活用
    if news_list:
        first_news_title = news_list[0].get("title", "")
        # 「〜が〜した」のような動詞パターンを抽出
        import re
        action_match = re.search(r'(熱愛|結婚|離婚|妊娠|復帰|引退|出演|主演|共演|活動|炎上|謝罪|コメント)', first_news_title)
        if action_match:
            action = action_match.group(1)
            return f"【{today}】{celebrity_name}が{action}！最新情報まとめ"
    
    return f"【{today}】{celebrity_name}の最新情報・プロフィール・作品まとめ"


if __name__ == "__main__":
    # テスト用
    sample_news = [
        {"title": "石原さとみが新CMに出演", "link": "https://example.com", "source": "テスト", "published": "2026-04-21", "excerpt": "テスト本文..."},
    ]
    sample_wiki = {
        "occupation": "女優・タレント",
        "birth_date": "1986年12月24日",
        "summary": "石原さとみは日本の女優・タレントです。東京都出身。...",
        "thumbnail_url": "",
        "wiki_url": "https://ja.wikipedia.org/wiki/石原さとみ",
    }
    sample_products = [
        {"title": "石原さとみ 写真集", "affiliate_url": "https://dmm.com", "image_url": "", "price": "¥2,000", "review_average": "4.5"},
    ]
    html = build_article_html("石原さとみ", sample_wiki, sample_news, sample_products)
    print(html[:500])
