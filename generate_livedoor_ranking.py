import datetime
import argparse
import os
from dmm_client import DMMClient
from livedoor_autopost.livedoor_client import LivedoorClient

# 24時間分のローテーション設定 (サービス, フロア, キーワード, 表示用カテゴリ/タイトル)
# FC2の SCHEDULE_24H を継承
SCHEDULE_24H = [
    {"service": "doujin", "floor": None, "keyword": "同人CG", "category": "同人CG・ゲーム"},  # 0時
    {"service": "digital", "floor": "videoa", "keyword": "NTR", "category": "NTR"},  # 1時
    {"service": "doujin", "floor": None, "keyword": "同人動画", "category": "同人動画"},  # 2時
    {"service": "digital", "floor": "videoa", "keyword": "痴漢", "category": "痴漢"},  # 3時
    {"service": "doujin", "floor": None, "keyword": "同人コミック", "category": "同人コミック"},  # 4時 (※同人作品)
    {"service": "digital", "floor": "videoa", "keyword": "M字開脚", "category": "M字開脚"},  # 5時
    {"service": "digital", "floor": "videoa", "keyword": "巨乳", "category": "巨乳"},  # 6時
    {"service": "mono", "floor": "goods", "keyword": "オナホール", "category": "アダルトグッズ"},  # 7時
    {"service": "digital", "floor": "videoa", "keyword": "人妻", "category": "人妻・熟女"},  # 8時
    {"service": "digital", "floor": "videoa", "keyword": "マイクロビキニ", "category": "マイクロビキニ"},  # 9時 (電子書籍から変更)
    {"service": "digital", "floor": "videoa", "keyword": "素人", "category": "素人ビデオ"},  # 10時
    {"service": "mono", "floor": "goods", "keyword": "コスプレ", "category": "コスプレグッズ"},  # 11時
    {"service": "digital", "floor": "videoa", "keyword": "企画", "category": "企画ビデオ"},  # 12時
    {"service": "digital", "floor": "anime", "keyword": "エロアニメ", "category": "アダルトアニメ"},  # 13時
    {"service": "digital", "floor": "videoa", "keyword": "制服", "category": "制服・コスプレ"},  # 14時
    {"service": "pcgame", "floor": "digital_pcgame", "keyword": None, "category": "美少女PCゲーム"},  # 15時
    {"service": "digital", "floor": "videoa", "keyword": "お姉さん", "category": "お姉さん"},  # 16時
    {"service": "mono", "floor": "goods", "keyword": "ローター", "category": "小型グッズ(ローター)"},  # 17時
    {"service": "digital", "floor": "videoa", "keyword": "単体", "category": "単体女優人気"},  # 18時
    {"service": "doujin", "floor": None, "keyword": "ASMR", "category": "同人ボイス・ASMR"},  # 19時
    {"service": "digital", "floor": "videoa", "keyword": "ギャル", "category": "ギャル"},  # 20時
    {"service": "digital", "floor": "videoa", "keyword": "美脚", "category": "美脚・タイツ"},  # 21時 (電子書籍から変更)
    {"service": "digital", "floor": "videoa", "keyword": "中出し", "category": "中出し"},  # 22時
    {"service": "digital", "floor": "videoa", "keyword": "VR", "category": "VRアダルト動画"},  # 23時
]

NG_WORDS = [
    "洗脳", "レイプ", "強姦", "盗撮", "リベンジポルノ", "乱暴", "鬼畜", "無理やり", "無理矢理", 
    "監禁", "奴隷", "調教", "強制", "辱め", "陵辱",
    "ロリ", "ペド", "幼女", "稚児", "児童", "JS", "JC", "JK", "女子校生", "女子高生", "女子中学生", "女子小学生",
    "女学生", "女子生徒", "教え子", "女子大生", "学生", "学園", "校内", "体育倉庫", "授乳",
    "援交", "援助交際", "パパ活", "売春", "買春", "近親相姦", "義母", "実母", "姉妹", "継母", "兄妹"
]

def sanitize_text(text):
    if not text:
        return ""
    for word in NG_WORDS:
        text = text.replace(word, "〇〇")
    return text

def generate_html_article(items, category_name):
    """
    DMMのアイテムリストからライブドアブログ用HTMLを生成する
    """
    today_str = datetime.datetime.now().strftime("%Y年%m月%d日")
    
    html = f'<div class="ranking-header">\n'
    html += f'  <p>【{today_str}更新】最新の【{category_name}】売れ筋ランキングをお届けします！</p>\n'
    html += f'</div>\n'
    html += "<hr>\n"
    
    for rank, item in enumerate(items, 1):
        raw_title = item.get("title", "タイトル不明")
        title = sanitize_text(raw_title)
        affiliate_url = item.get("affiliateURL", "#")
        image_url = item.get("imageURL", {}).get("large", "")
        
        # 紹介文の取得 (introduction, description, またはジャンル情報)
        introduction = item.get("introduction", "")
        if not introduction and "iteminfo" in item:
            genres = item["iteminfo"].get("genre", [])
            if genres:
                genre_names = [g.get("name") for g in genres if g.get("name")]
                introduction = "ジャンル: " + ", ".join(genre_names)
        
        introduction = sanitize_text(introduction)
        
        # アイテム情報の組み立て
        html += f'<div class="ranking-item" style="margin-bottom: 40px; border: 1px solid #eee; padding: 15px; border-radius: 8px;">\n'
        html += f'  <h3 style="color: #d32f2f;">第{rank}位： {title}</h3>\n'
        
        if image_url:
            html += f'  <div class="item-image" style="text-align: center; margin: 20px 0;">\n'
            html += f'    <a href="{affiliate_url}" target="_blank" rel="noopener">\n'
            html += f'      <img src="{image_url}" alt="{title}" style="max-width: 100%; height: auto; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">\n'
            html += f'    </a>\n'
            html += f'  </div>\n'
        
        if introduction:
            html += f'  <div class="item-description" style="background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 15px; line-height: 1.6;">\n'
            html += f'    {introduction}\n'
            html += f'  </div>\n'
        
        html += f'  <div class="item-link" style="text-align: center;">\n'
        html += f'    <a href="{affiliate_url}" target="_blank" rel="noopener" style="display: inline-block; background: #ff9800; color: #fff; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">▶ FANZAで詳細を見る</a>\n'
        html += f'  </div>\n'
        html += f'</div>\n'
        
    html += "<p style='font-size: 0.8em; color: #777;'>※ランキング情報は記事作成時点のものです。最新の情報はリンク先でご確認ください。</p>\n"
    return html

def main():
    parser = argparse.ArgumentParser(description="Livedoor Blog FANZAランキング自動投稿スクリプト")
    parser.add_argument("--keyword", type=str, default=None, help="手動検索キーワード")
    parser.add_argument("--service", type=str, default="digital", help="手動指定時のサービス")
    parser.add_argument("--floor", type=str, default="videoa", help="手動指定時のフロア")
    parser.add_argument("--category", type=str, default=None, help="手動時のカテゴリ名")
    parser.add_argument("--hits", type=int, default=10, help="取得件数")
    parser.add_argument("--draft", action="store_true", help="下書きとして保存")
    args = parser.parse_args()

    try:
        # スケジュールの決定
        if not args.keyword and not args.category:
            jst = datetime.timezone(datetime.timedelta(hours=9))
            now_jst = datetime.datetime.now(jst)
            current_hour = now_jst.hour
            conf = SCHEDULE_24H[current_hour % 24]
            current_keyword = conf["keyword"]
            current_service = conf["service"]
            current_floor = conf["floor"]
            target_category = conf["category"]
            print(f"JST {current_hour}時: スケジュール実行 - 「{target_category}」")
        else:
            current_keyword = args.keyword
            current_service = args.service
            current_floor = args.floor
            target_category = args.category if args.category else (current_keyword if current_keyword else "FANZAランキング")
            print(f"手動実行 - 「{target_category}」")

        # DMMから売れ筋情報を取得
        dmm = DMMClient()
        top_items = dmm.get_top_fanza_works(service=current_service, floor=current_floor, hits=args.hits, keyword=current_keyword)
        
        if not top_items and current_keyword:
            print("結果0件のため、キーワードなしで再試行...")
            top_items = dmm.get_top_fanza_works(service=current_service, floor=current_floor, hits=args.hits, keyword=None)

        if not top_items:
            print("アイテムを取得できませんでした。")
            return
            
        print(f"{len(top_items)}件のアイテムを取得しました。")
        
        # HTMLの生成
        article_html = generate_html_article(top_items, target_category)
        
        # ライブドアブログに投稿
        livedoor = LivedoorClient()
        today_str = datetime.datetime.now().strftime("%Y/%m/%d")
        title = f"【{today_str}】FANZA売れ筋！【{target_category}】ランキング TOP{args.hits}"
        
        is_publish = not args.draft
        print(f"ライブドアブログへ投稿中... [公開: {is_publish}]")
        livedoor.post_article(title, article_html, categories=[target_category], publish=is_publish)
        
    except Exception as e:
        print(f"予期せぬエラー: {e}")

if __name__ == "__main__":
    main()
