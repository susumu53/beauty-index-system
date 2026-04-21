import os
import sys
import importlib
from datetime import datetime

# Ensure project root is in sys.path for imports
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Mapping of UTC hour -> generator module name
HOUR_TO_GENERATOR = {
    0: "buzz_ranking_generator",   # 9:00 JST
    4: "birthday_generator",       # 13:00 JST
    8: "hometown_generator",       # 17:00 JST
    12: "costar_generator",        # 21:00 JST
    16: "sentiment_generator",     # 1:00 JST (next day)
    20: "trending_generator",      # 5:00 JST (next day)
}

def load_generator(module_name: str):
    """動的にジェネレータモジュールをインポートし、run 関数を取得"""
    try:
        mod = importlib.import_module(f"generators.{module_name}")
        return getattr(mod, "run")
    except Exception as e:
        print(f"[main] ジェネレータ {module_name} のロードに失敗: {e}")
        return None


def main():
    utc_hour = datetime.utcnow().hour
    generator_name = HOUR_TO_GENERATOR.get(utc_hour)
    if not generator_name:
        print(f"[main] 現在のUTC時刻 {utc_hour} は投稿対象外です。終了します。")
        return

    print(f"[main] 現在UTC {utc_hour} 時、ジェネレータ '{generator_name}' を実行します。")
    generator_func = load_generator(generator_name)
    if not generator_func:
        print("[main] ジェネレータ関数が取得できませんでした。終了します。")
        return

    result = generator_func()
    if not result:
        print("[main] ジェネレータが有効な記事を生成しませんでした。終了します。")
        return

    # Seesaa 投稿
    from seesaa_poster import SeesaaCelebPoster
    poster = SeesaaCelebPoster()
    post_id = poster.post_article(title=result["title"], html=result["html"], tags=result.get("tags", []))
    if post_id:
        print(f"[main] 記事投稿成功！ ID: {post_id}")
    else:
        print("[main] 記事投稿に失敗しました。")

if __name__ == "__main__":
    # Windows 環境での文字化け対策（UTF-8 強制）
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf_8"):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
