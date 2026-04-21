#!/usr/bin/env python3
"""
芸能人自動ブログ投稿システム
ブログ: https://namasoku.seesaa.net/
スケジュール: 1日4回（0時・6時・12時・18時 JST）

処理フロー:
1. Google News RSS からトレンド芸能人を自動選定
2. Wikipedia からプロフィール・経歴を取得
3. Google News から最新ニュース（3件）を取得
4. DMM API から関連作品・商品（一般のみ）を取得
5. テンプレートベースで HTML 記事を組み立て
6. Seesaa Blog に XML-RPC で投稿
"""

import sys
import os
import traceback
from datetime import datetime

# 同フォルダのモジュールをインポート
sys.path.insert(0, os.path.dirname(__file__))

from news_fetcher import get_trending_celebrity, get_celebrity_news, mark_as_posted
from wiki_fetcher import get_wiki_profile
from dmm_fetcher import DMMCelebFetcher
from article_builder import build_article_html, build_article_title
from seesaa_poster import SeesaaCelebPoster


def main():
    print("=" * 60)
    print(f"🎬 芸能人自動投稿システム 開始")
    print(f"   実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # ── Step 1: トレンド芸能人を取得 ──
    print("\n📡 Step 1: トレンド芸能人を取得中...")
    celebrity_name = get_trending_celebrity()
    
    if not celebrity_name:
        print("❌ トレンド芸能人が取得できませんでした。処理を終了します。")
        sys.exit(1)
    
    print(f"   ▶ 対象芸能人: {celebrity_name}")
    
    # ── Step 2: Wikipedia プロフィール取得 ──
    print(f"\n📖 Step 2: Wikipedia プロフィール取得中... ({celebrity_name})")
    wiki_profile = get_wiki_profile(celebrity_name)
    
    if wiki_profile:
        print(f"   ▶ 職業: {wiki_profile.get('occupation', '不明')}")
        print(f"   ▶ 生年月日: {wiki_profile.get('birth_date', '不明')}")
    else:
        print(f"   ⚠️ Wikipedia情報が見つかりませんでした（記事は続行します）")
    
    # ── Step 3: 最新ニュース取得 ──
    print(f"\n📰 Step 3: 最新ニュース取得中... ({celebrity_name})")
    news_list = get_celebrity_news(celebrity_name, max_articles=3)
    print(f"   ▶ 取得件数: {len(news_list)}件")
    for news in news_list:
        print(f"   - {news['title'][:60]}")
    
    # ── Step 4: DMM 商品取得 ──
    print(f"\n🛒 Step 4: DMM 商品取得中... ({celebrity_name})")
    youtube_video_id = None
    
    try:
        dmm = DMMCelebFetcher()
        dmm_products = dmm.search_celebrity_products(celebrity_name, max_items=5)
        print(f"   ▶ 取得件数: {len(dmm_products)}件")
        
        if not dmm_products:
            print("   ⚠️ DMM商品なし → YouTubeフォールバックを試みます")
            youtube_video_id = dmm.get_youtube_fallback(celebrity_name)
            if youtube_video_id:
                print(f"   ▶ YouTube動画ID: {youtube_video_id}")
    
    except Exception as e:
        print(f"   ❌ DMM取得エラー: {e}")
        dmm_products = []
    
    # ── Step 5: HTML 記事生成 ──
    print(f"\n📝 Step 5: HTML記事を生成中...")
    
    title = build_article_title(celebrity_name, news_list)
    html_content = build_article_html(
        celebrity_name=celebrity_name,
        wiki_profile=wiki_profile,
        news_list=news_list,
        dmm_products=dmm_products,
        youtube_video_id=youtube_video_id,
    )
    
    print(f"   ▶ タイトル: {title}")
    print(f"   ▶ HTML長さ: {len(html_content)}文字")
    
    # ── Step 6: Seesaa Blog に投稿 ──
    print(f"\n🚀 Step 6: Seesaa Blog に投稿中...")
    
    tags = [celebrity_name, "芸能人", "最新情報", "プロフィール", "エンタメ"]
    if wiki_profile and wiki_profile.get("occupation"):
        # 職業タグを追加（例: 「女優」「歌手」）
        for occ in wiki_profile["occupation"].split("・"):
            tags.append(occ.strip())
    
    categories = ["芸能人", "エンタメニュース"]
    
    poster = SeesaaCelebPoster()
    post_id = poster.post_article(
        title=title,
        html_content=html_content,
        categories=categories,
        tags=tags[:10],  # Seesaaのタグ上限を考慮
    )
    
    if post_id:
        # Step 7: 投稿済みログを更新
        mark_as_posted(celebrity_name)
        print(f"\n✅ 完了！ 記事タイトル: {title}")
        print(f"   投稿ID: {post_id}")
        print(f"   ブログ: https://namasoku.seesaa.net/")
    else:
        print(f"\n❌ 投稿に失敗しました")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 処理完了")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n💥 予期しないエラーが発生しました:")
        traceback.print_exc()
        sys.exit(1)
