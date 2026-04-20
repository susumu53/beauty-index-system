import datetime
import argparse
import os
from dmm_client import DMMClient
from livedoor_autopost.livedoor_client import LivedoorClient

# 24時間分のローテーション設定 (サービス, フロア, キーワード, 表示用カテゴリ/タイトル)
# FC2の SCHEDULE_24H を継承
SCHEDULE_24H = [
    {"service": "digital", "floor": "videoa", "keyword": "競泳水着", "category": "競泳水着・スク水"},  # 0時 (同人から変更)
    {"service": "digital", "floor": "videoa", "keyword": "NTR", "category": "NTR"},  # 1時
    {"service": "digital", "floor": "videoa", "keyword": "タイツ", "category": "パンスト・タイツ"},  # 2時 (同人から変更)
    {"service": "digital", "floor": "videoa", "keyword": "痴漢", "category": "痴漢"},  # 3時
    {"service": "digital", "floor": "videoa", "keyword": "野外", "category": "野外・露出"},  # 4時 (同人から変更)
    {"service": "digital", "floor": "videoa", "keyword": "M字開脚", "category": "M字開脚"},  # 5時
    {"service": "digital", "floor": "videoa", "keyword": "巨乳", "category": "巨乳"},  # 6時
    {"service": "mono", "floor": "goods", "keyword": "オナホール", "category": "アダルトグッズ"},  # 7時
    {"service": "digital", "floor": "videoa", "keyword": "人妻", "category": "人妻・熟女"},  # 8時
    {"service": "digital", "floor": "videoa", "keyword": "マイクロビキニ", "category": "マイクロビキニ"},  # 9時
    {"service": "digital", "floor": "videoa", "keyword": "素人", "category": "素人ビデオ"},  # 10時
    {"service": "mono", "floor": "goods", "keyword": "コスプレ", "category": "コスプレグッズ"},  # 11時
    {"service": "digital", "floor": "videoa", "keyword": "企画", "category": "企画ビデオ"},  # 12時
    {"service": "digital", "floor": "anime", "keyword": "エロアニメ", "category": "アダルトアニメ"},  # 13時
    {"service": "digital", "floor": "videoa", "keyword": "制服", "category": "制服・コスプレ"},  # 14時
    {"service": "pcgame", "floor": "digital_pcgame", "keyword": None, "category": "美少女PCゲーム"},  # 15時
    {"service": "digital", "floor": "videoa", "keyword": "お姉さん", "category": "お姉さん"},  # 16時
    {"service": "mono", "floor": "goods", "keyword": "ローター", "category": "小型グッズ(ローター)"},  # 17時
    {"service": "digital", "floor": "videoa", "keyword": "単体", "category": "単体女優人気"},  # 18時
    {"service": "digital", "floor": "videoa", "keyword": "OL", "category": "OL・制服"},  # 19時 (同人から変更)
    {"service": "digital", "floor": "videoa", "keyword": "ギャル", "category": "ギャル"},  # 20時
    {"service": "digital", "floor": "videoa", "keyword": "美脚", "category": "美脚・タイツ"},  # 21時
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
    
    # CSSスタイル定義（ライブドアブログの記事内に埋め込む）
    style = """
    <style>
    .ranking-container { font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif; color: #333; max-width: 800px; margin: 0 auto; line-height: 1.6; }
    .ranking-header { background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); color: white; padding: 30px; text-align: center; border-radius: 15px; margin-bottom: 40px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .ranking-header h1 { margin: 0; font-size: 24px; font-weight: bold; }
    .ranking-item { background: #fff; border-radius: 15px; padding: 25px; margin-bottom: 50px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: 1px solid #f0f0f0; transition: transform 0.3s ease; }
    .ranking-item:hover { transform: translateY(-5px); }
    .rank-badge { display: inline-block; background: #e91e63; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 14px; margin-bottom: 15px; }
    .item-title { font-size: 20px; font-weight: bold; margin-bottom: 20px; color: #1a1a1a; border-left: 5px solid #2575fc; padding-left: 15px; }
    .main-image { text-align: center; margin-bottom: 25px; }
    .main-image img { max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); border: 3px solid #f8f9fa; }
    .product-info-table { width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 14px; }
    .product-info-table th { background: #f8f9fa; text-align: left; padding: 10px; border-bottom: 1px solid #eee; width: 100px; color: #666; }
    .product-info-table td { padding: 10px; border-bottom: 1px solid #eee; color: #333; }
    .sample-images { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 10px; margin-top: 20px; }
    .sample-images img { width: 100%; height: auto; border-radius: 5px; cursor: pointer; transition: opacity 0.3s; border: 1px solid #eee; }
    .sample-images img:hover { opacity: 0.8; }
    .ranking-footer { text-align: center; margin-top: 50px; padding: 20px; border-top: 1px solid #eee; color: #888; font-size: 12px; }
    </style>
    """
    
    html = f'{style}\n<div class="ranking-container">\n'
    html += f'  <div class="ranking-header">\n'
    html += f'    <h1>【{today_str}更新】{category_name}ランキング TOP10</h1>\n'
    html += f'  </div>\n'
    
    for rank, item in enumerate(items, 1):
        raw_title = item.get("title", "タイトル不明")
        title = sanitize_text(raw_title)
        affiliate_url = item.get("affiliateURL", "#")
        image_url = item.get("imageURL", {}).get("large", "")
        
        # アイテム情報の抽出
        item_info = item.get("iteminfo", {})
        actresses = ", ".join([a.get("name") for a in item_info.get("actress", []) if a.get("name")])
        maker = ", ".join([m.get("name") for m in item_info.get("maker", []) if m.get("name")])
        label = ", ".join([l.get("name") for l in item_info.get("label", []) if l.get("name")])
        date = item.get("date", "不明")
        
        # サンプル画像の抽出 (最大5枚)
        samples = item.get("sampleImageURL", {}).get("sample_l", {}).get("image", [])
        sample_html = ""
        if samples:
            sample_html = '<div class="sample-images">\n'
            for s_img in samples[:5]:
                sample_html += f'    <a href="{affiliate_url}" target="_blank" rel="noopener"><img src="{s_img}" alt="サンプル"></a>\n'
            sample_html += '  </div>\n'
        
        # カードの組み立て
        html += f'  <div class="ranking-item">\n'
        html += f'    <div class="rank-badge">第{rank}位</div>\n'
        html += f'    <div class="item-title"><a href="{affiliate_url}" target="_blank" rel="noopener" style="text-decoration: none; color: inherit;">{title}</a></div>\n'
        
        if image_url:
            html += f'    <div class="main-image">\n'
            html += f'      <a href="{affiliate_url}" target="_blank" rel="noopener">\n'
            html += f'        <img src="{image_url}" alt="{title}">\n'
            html += f'      </a>\n'
            html += f'    </div>\n'
        
        html += f'    <table class="product-info-table">\n'
        if actresses: html += f'      <tr><th>出演者</th><td>{sanitize_text(actresses)}</td></tr>\n'
        if maker: html += f'      <tr><th>メーカー</th><td>{sanitize_text(maker)}</td></tr>\n'
        if label: html += f'      <tr><th>レーベル</th><td>{sanitize_text(label)}</td></tr>\n'
        if date: html += f'      <tr><th>配信開始</th><td>{date}</td></tr>\n'
        html += f'    </table>\n'
        
        if sample_html:
            html += f'    <div style="font-size: 13px; font-weight: bold; color: #666; margin-top: 20px;">▼ サンプル画像パネル</div>\n'
            html += f'    {sample_html}\n'
            
        html += f'  </div>\n'
        
    html += '  <div class="ranking-footer">\n'
    html += f'    <p>※ランキング情報は記事作成時点（{today_str}）のものです。最新の情報はリンク先（FANZA様サイト）にてご確認ください。</p>\n'
    html += '  </div>\n'
    html += '</div>\n'
    return html

def main():
    parser = argparse.ArgumentParser(description="Livedoor Blog FANZAランキング自動投稿スクリプト")
    parser.add_argument("--keyword", type=str, default=None, help="手動検索キーワード")
    parser.add_argument("--service", type=str, default="digital", help="手動指定時のサービス")
    parser.add_argument("--floor", type=str, default="videoa", help="手動指定時のフロア")
    parser.add_argument("--category", type=str, default=None, help="手動時のカテゴリ名")
    parser.add_argument("--hits", type=int, default=10, help="取得件数")
    # --draft を削除（常に公開）
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
        
        # 常に公開
        is_publish = True
        print(f"ライブドアブログへ投稿中... [常に公開設定]")
        livedoor.post_article(title, article_html, categories=[target_category], publish=is_publish)
        
    except Exception as e:
        print(f"予期せぬエラー: {e}")

if __name__ == "__main__":
    main()
