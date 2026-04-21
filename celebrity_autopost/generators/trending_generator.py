"""
trending_generator.py
既存の「トレンド芸能人 + ニュース + Wikipedia + DMM」記事生成ロジック
（元 main.py から分離）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from news_fetcher import get_trending_celebrity, get_celebrity_news, mark_as_posted
from wiki_fetcher import get_wiki_profile
from dmm_fetcher import DMMCelebFetcher
from article_builder import build_article_html, build_article_title


def run():
    """トレンド芸能人記事を生成して返す。dict: {title, html, tags, celebrity_name}"""
    print("[trending] トレンド芸能人を選定中...")
    celebrity_name = get_trending_celebrity()
    if not celebrity_name:
        print("[trending] 芸能人が取得できませんでした")
        return None

    print("[trending] 対象: " + celebrity_name)

    wiki_profile = get_wiki_profile(celebrity_name)
    news_list = get_celebrity_news(celebrity_name, max_articles=3)
    print("[trending] ニュース: " + str(len(news_list)) + "件")

    youtube_video_id = None
    dmm_products = []
    try:
        dmm = DMMCelebFetcher()
        dmm_products = dmm.search_celebrity_products(celebrity_name, max_items=5)
        if not dmm_products:
            youtube_video_id = dmm.get_youtube_fallback(celebrity_name)
    except Exception as e:
        print("[trending] DMM error: " + str(e))

    title = build_article_title(celebrity_name, news_list)
    html = build_article_html(
        celebrity_name=celebrity_name,
        wiki_profile=wiki_profile,
        news_list=news_list,
        dmm_products=dmm_products,
        youtube_video_id=youtube_video_id,
    )

    tags = [celebrity_name, "芸能人", "最新情報", "プロフィール", "エンタメ"]
    if wiki_profile and wiki_profile.get("occupation"):
        for occ in wiki_profile["occupation"].split("・"):
            tags.append(occ.strip())

    mark_as_posted(celebrity_name)
    return {"title": title, "html": html, "tags": tags[:10], "celebrity_name": celebrity_name}
