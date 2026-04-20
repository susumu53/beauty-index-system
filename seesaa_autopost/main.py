import os
import random
import datetime
from seesaa_client import SeesaaClient
from dmm_api_v3 import DMMClientV3
from beauty_analyzer import BeautyAnalyzer
from article_generator import ArticleGenerator
from scheduler import Scheduler

def main():
    seesaa = SeesaaClient()
    dmm = DMMClientV3()
    analyzer = BeautyAnalyzer()
    generator = ArticleGenerator()
    scheduler = Scheduler()

    category, post_type, sort_method = scheduler.get_current_task()
    hour = datetime.datetime.now().hour
    
    # Check if this is a "Sale" hour
    is_sale = scheduler.is_sale_hour(hour)
    if is_sale:
        category = "shopping"
        sort_method = "rank"
    
    print(f"Executing Task: Category={category}, Type={post_type}, Sort={sort_method}, SaleMode={is_sale}")

    items = []
    title = ""
    subtitle = "DMM.com公式データに基づく最新情報"
    tags = ["DMM", "アフィリエイト"]

    # 1. Fetch Data based on category and sorting
    if is_sale:
        items = dmm.get_sale_items(hits=10)
        title = "【期間限定】DMM大還元セール・注目アイテム特集"
        subtitle = "今だけお得なキャンペーン対象商品をピックアップ！"
        tags += ["セール", "お買い得", "キャンペーン"]
    elif category == "idol":
        items = dmm.get_gravure_ranking(hits=10 if post_type == "ranking" else 5)
        title = "【最新】グラビアアイドル人気ランキング" if post_type == "ranking" else "【AI分析】本日の美少女・グラビア分析"
        tags += ["グラビア", "アイドル", "美少女"]
    elif category == "tv":
        items = dmm.get_dmm_tv_programs(hits=10, sort=sort_method)
        title = "DMM TV 最新・人気番組ランキング" if sort_method == "rank" else "DMM TV 新着配信・独占番組情報"
        subtitle = "公式の人気順に基づいた番組セレクション" if sort_method == "rank" else "配信開始されたばかりの最新注目作"
        tags += ["DMMTV", "アニメ", "独占配信"]
    elif category == "books":
        items = dmm.get_books_ranking(hits=10, sort=sort_method)
        title = "DMMブックス 売れ筋ランキング" if sort_method == "rank" else "DMMブックス 本日発売の新作コミック"
        tags += ["電子書籍", "漫画", "ラノベ"]
    elif category == "games":
        items = dmm.get_games_ranking(hits=10, sort=sort_method)
        title = "PCゲーム・PCソフト 人気ランキング" if sort_method == "rank" else "新作PCゲーム・ソフト最新情報"
        tags += ["PCゲーム", "パソコンソフト"]
    elif category == "stage":
        items = dmm.get_items(service="digital", floor="stage", hits=10, sort=sort_method)
        title = "2.5次元・舞台 注目作品ランキング"
        tags += ["舞台", "2.5次元"]
    elif category == "shopping":
        items = dmm.get_shopping_ranking(hits=10)
        title = "DMM通販・ショッピング 週間ランキング"
        tags += ["通販", "お買い物"]
    elif category == "seasonal":
        kw = scheduler.get_seasonal_keyword()
        items = dmm.get_items(site="DMM.com", keyword=kw, hits=10, sort="rank")
        title = f"【季節限定】今すぐ欲しい！注目のアイテム特集"
        subtitle = f"「{kw}」関連の人気アイテムをピックアップ"
        tags += ["流行", "季節物"]

    if not items:
        print("No items found. Aborting.")
        return

    # 2. Generate Content
    if post_type == "spotlight":
        # Pick high-rated item for spotlight
        target = items[0]
        radar_url = None
        scores = None
        
        # If idol/gravure, perform beauty analysis
        if category == "idol" or "idol" in tags:
            img_url = target.get('imageURL', {}).get('large', '')
            image = analyzer.download_image(img_url)
            scores = analyzer.analyze(image)
            if scores:
                radar_path = "radar_temp.png"
                analyzer.generate_radar_chart(scores, radar_path)
                radar_url = seesaa.upload_media(radar_path)
                if os.path.exists(radar_path): os.remove(radar_path)
        
        if radar_url and scores:
            html = generator.generate_spotlight_html(target, scores, radar_url)
            title = f"【AI美人度分析】{target['title']}（スコア：{scores['total']}点）"
        else:
            # Fallback to rich ranking-style spotlight if analysis fails
            html = generator.generate_ranking_html(f"【注目】{target['title']}", [target], subtitle="こちらのアイテムの最新情報をお届けします")
            title = f"【ピックアップ】{target['title']}"
    else:
        # Ranking type
        html = generator.generate_ranking_html(title, items, subtitle=subtitle)

    # 3. Post to Seesaa
    if html:
        post_id = seesaa.post_article(title, html, tags=tags)
        if post_id:
            print(f"Successfully posted article: {post_id}")

if __name__ == "__main__":
    main()
