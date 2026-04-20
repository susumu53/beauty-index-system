import datetime
import argparse
from dmm_client import DMMClient
from fc2_autopost.fc2_client import FC2Client

# 24時間分のローテーション設定 (サービス, フロア, キーワード, 表示用カテゴリ/タイトル)
SCHEDULE_24H = [
    # 深夜帯 (マニアック・同人重視)
    {"service": "doujin", "floor": None, "keyword": "同人CG", "category": "同人CG・ゲーム"},  # 0時
    {"service": "digital", "floor": "videoa", "keyword": "NTR", "category": "NTR"},  # 1時
    {"service": "doujin", "floor": None, "keyword": "同人動画", "category": "同人動画"},  # 2時
    {"service": "digital", "floor": "videoa", "keyword": "痴漢", "category": "痴漢"},  # 3時
    {"service": "doujin", "floor": None, "keyword": "同人コミック", "category": "同人コミック"},  # 4時
    {"service": "digital", "floor": "videoa", "keyword": "M字開脚", "category": "M字開脚"},  # 5時

    # 朝〜昼帯 (グッズ・コミック・王道ビデオ)
    {"service": "digital", "floor": "videoa", "keyword": "巨乳", "category": "巨乳"},  # 6時
    {"service": "mono", "floor": "goods", "keyword": "オナホール", "category": "アダルトグッズ"},  # 7時
    {"service": "digital", "floor": "videoa", "keyword": "人妻", "category": "人妻・熟女"},  # 8時
    {"service": "ebook", "floor": "comic", "keyword": "アダルトコミック", "category": "アダルトコミック"},  # 9時
    {"service": "digital", "floor": "videoa", "keyword": "素人", "category": "素人ビデオ"},  # 10時
    {"service": "mono", "floor": "goods", "keyword": "コスプレ", "category": "コスプレグッズ"},  # 11時

    # 昼下がり〜夕方 (少し刺激的・アニメ・PCゲーム)
    {"service": "digital", "floor": "videoa", "keyword": "企画", "category": "企画ビデオ"},  # 12時
    {"service": "digital", "floor": "anime", "keyword": "エロアニメ", "category": "アダルトアニメ"},  # 13時
    {"service": "digital", "floor": "videoa", "keyword": "制服", "category": "制服・コスプレ"},  # 14時 (学生を回避)
    {"service": "digital", "floor": "pcgame", "keyword": "アダルトPCゲーム", "category": "美少女PCゲーム"},  # 15時
    {"service": "digital", "floor": "videoa", "keyword": "お姉さん", "category": "お姉さん"},  # 16時
    {"service": "mono", "floor": "goods", "keyword": "ローター", "category": "小型グッズ(ローター)"},  # 17時

    # 夜〜ゴールデン帯 (単体・ボイス・写真集・最新技術)
    {"service": "digital", "floor": "videoa", "keyword": "単体", "category": "単体女優人気"},  # 18時
    {"service": "doujin", "floor": None, "keyword": "ASMR", "category": "同人ボイス・ASMR"},  # 19時
    {"service": "digital", "floor": "videoa", "keyword": "ギャル", "category": "ギャル"},  # 20時
    {"service": "ebook", "floor": "photo", "keyword": "写真集", "category": "アダルト写真集"},  # 21時
    {"service": "digital", "floor": "videoa", "keyword": "中出し", "category": "中出し"},  # 22時
    {"service": "digital", "floor": "videoa", "keyword": "VR", "category": "VRアダルト動画"},  # 23時
]

# FC2ブログの規約違反(NGワード)対策リスト
NG_WORDS = [
    # 犯罪・強制・過激系
    "洗脳", "レイプ", "強姦", "盗撮", "リベンジポルノ", "乱暴", "鬼畜", "無理やり", "無理矢理", 
    "監禁", "奴隷", "調教", "強制", "辱め", "陵辱",
    
    # 年齢・身分系 (FC2は特に厳しい)
    "ロリ", "ペド", "幼女", "稚児", "児童", "JS", "JC", "JK", "女子校生", "女子高生", "女子中学生", "女子小学生",
    "女学生", "女子生徒", "教え子", "女子大生", "学生", "学園", "校内", "体育倉庫", "授乳",
    
    # 社会的・近親系
    "援交", "援助交際", "パパ活", "売春", "買春", "近親相姦", "義母", "実母", "姉妹", "継母", "兄妹"
]

def sanitize_text(text):
    """タイトル等に含まれるNGワードを伏せ字(〇〇)に変換する"""
    if not text:
        return ""
    for word in NG_WORDS:
        text = text.replace(word, "〇〇")
    return text

def generate_html_article(items, category_name):
    """
    DMMのアイテムリストからシンプルなランキング用HTMLを生成する
    """
    today_str = datetime.datetime.now().strftime("%Y年%m月%d日")
    
    html = f"<p>これは{today_str}時点での【{category_name}】売れ筋トップ{len(items)}のランキングです。</p>\n"
    html += "<hr>\n"
    
    for rank, item in enumerate(items, 1):
        raw_title = item.get("title", "タイトル不明")
        title = sanitize_text(raw_title)
        affiliate_url = item.get("affiliateURL", "#")
        image_url = item.get("imageURL", {}).get("large", "")
        
        # アイテム情報の組み立て
        html += f"<h3>第{rank}位： {title}</h3>\n"
        if image_url:
            html += f'<div style="text-align: center;"><a href="{affiliate_url}" target="_blank" rel="noopener"><img src="{image_url}" alt="{title}" style="max-width: 100%; height: auto;"></a></div>\n'
        
        html += f'<p style="text-align: center; margin-top: 10px;"><a href="{affiliate_url}" target="_blank" rel="noopener"><strong>▶ この商品の詳細を見る（FANZA）</strong></a></p>\n'
        html += "<hr>\n"
        
    html += "<p>※ランキング情報は記事取得時のものです。</p>\n"
    return html

def main():
    parser = argparse.ArgumentParser(description="FANZAランキング自動投稿スクリプト")
    parser.add_argument("--keyword", type=str, default=None, help="手動検索キーワード")
    parser.add_argument("--service", type=str, default="digital", help="手動指定時のサービス")
    parser.add_argument("--floor", type=str, default="videoa", help="手動指定時のフロア")
    parser.add_argument("--category", type=str, default=None, help="手動時のFC2カテゴリ")
    parser.add_argument("--hits", type=int, default=10, help="取得件数 (デフォルト10)")
    parser.add_argument("--draft", action="store_true", help="公開せず下書き状態で保存する")
    args = parser.parse_args()

    try:
        # スケジュールの決定
        if not args.keyword and not args.category:
            current_hour = datetime.datetime.now().hour
            conf = SCHEDULE_24H[current_hour % 24]
            current_keyword = conf["keyword"]
            current_service = conf["service"]
            current_floor = conf["floor"]
            target_category = conf["category"]
            print(f"自動実行モード: {current_hour}時のスケジュールにより「{target_category}」を選択しました。")
        else:
            current_keyword = args.keyword
            current_service = args.service
            current_floor = args.floor
            target_category = args.category if args.category else (current_keyword if current_keyword else "FANZAランキング")
            print(f"手動実行モード: 「{target_category}」を選択しました。")

        # DMMから売れ筋情報を取得
        dmm = DMMClient()
        print(f"DMMから対象ランキングを取得中... (サービス: {current_service}, フロア: {current_floor}, キーワード: {current_keyword})")
        top_items = dmm.get_top_fanza_works(service=current_service, floor=current_floor, hits=args.hits, keyword=current_keyword)
        
        if not top_items:
            print("エラー: DMMからアイテムを取得できませんでした。")
            return
            
        print(f"{len(top_items)}件のアイテムを取得しました。")
        
        # HTMLの生成
        article_html = generate_html_article(top_items, target_category)
        
        # FC2ブログに投稿
        fc2 = FC2Client()
        today_str = datetime.datetime.now().strftime("%Y/%m/%d")
        title = f"【{today_str}】FANZA 今売れてる！【{target_category}】ランキング トップ{args.hits}！"
        
        is_publish = not args.draft
        print(f"FC2ブログへ投稿を開始します... [公開設定: {is_publish}, カテゴリ: {target_category}]")
        post_id = fc2.post_article(title, article_html, categories=[target_category], publish=is_publish)
        
        if post_id:
            print(f"自動投稿処理が正常に完了しました！（記事ID: {post_id}）")
            
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
