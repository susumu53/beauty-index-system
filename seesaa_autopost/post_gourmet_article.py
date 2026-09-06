import sys
import argparse

# WindowsコンソールのUnicodeEncodeError防止
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from gourmet_article_generator import GourmetArticleGenerator
from gourmet_seesaa_client import GourmetSeesaaClient

def main():
    parser = argparse.ArgumentParser(description="料理・グルメブログ (syoshinsya2525.seesaa.net) 記事投稿スクリプト")
    parser.add_argument(
        "--type",
        choices=["buzz", "manga", "anime", "knowhow", "auto"],
        default="auto",
        help="投稿する記事タイプ (buzz: バズレシピ, manga: グルメ漫画, anime: 料理アニメ/番組, knowhow: ノウハウ, auto: 自動選択)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="投稿を行わず、生成した記事内容のみを出力して確認する"
    )
    args = parser.parse_args()

    print("==================================================")
    print(" 🍳 料理・グルメブログ 自動投稿システム")
    print(f" ターゲット: https://syoshinsya2525.seesaa.net/")
    print(f" 選択タイプ: {args.type} (Dry-Run: {args.dry_run})")
    print("==================================================")

    generator = GourmetArticleGenerator()
    
    if args.type == "buzz":
        article = generator.generate_buzz_recipe_article()
    elif args.type == "manga":
        article = generator.generate_manga_article()
    elif args.type == "anime":
        article = generator.generate_anime_tv_article()
    elif args.type == "knowhow":
        article = generator.generate_knowhow_article()
    else:
        article = generator.generate_random_article()

    print(f"\n【生成タイトル】\n{article['title']}")
    print(f"\n【カテゴリー】: {article['categories']}")
    print(f"【タグ】: {article['tags']}")

    if args.dry_run:
        print("\n--- [DRY-RUN] 本文プレビュー (先頭500文字) ---")
        print(article['content'][:500])
        print("\n--- [DRY-RUN 完了: 投稿は行われませんでした] ---")
        return

    # 投稿処理
    print("\nSeesaaブログへ投稿処理中...")
    client = GourmetSeesaaClient()
    post_id = client.post_article(
        title=article['title'],
        content=article['content'],
        categories=article['categories'],
        tags=article['tags']
    )

    if post_id:
        print(f"\n🎉 投稿成功！ 記事ID: {post_id}")
        print(f"ブログURL: https://syoshinsya2525.seesaa.net/")
        
        # 投稿ログの記録
        try:
            import datetime
            log_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("autopost.log", "a", encoding="utf-8") as f:
                f.write(f"[{log_time}] [SUCCESS] ID:{post_id} | Cat:{article['categories']} | {article['title']}\n")
        except Exception as le:
            print(f"Log write failed: {le}")
    else:
        print("\n❌ 投稿に失敗しました。認証情報またはネットワークを確認してください。")
        try:
            import datetime
            log_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("autopost.log", "a", encoding="utf-8") as f:
                f.write(f"[{log_time}] [FAILED] {article.get('title', 'Unknown')}\n")
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
