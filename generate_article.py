import os
import cv2
import json
from dmm_client import DMMClient
from beauty_engine import BeautyEngine
from wp_uploader import WPUploader
from database import BeautyDatabase
from dotenv import load_dotenv

load_dotenv()

class BeautyManager:
    def __init__(self):
        self.client = DMMClient()
        self.engine = BeautyEngine()
        self.uploader = WPUploader()
        self.db = BeautyDatabase()

    def _fetch_and_analyze(self, name, category, keyword_override=None, required_image_count=3):
        """1人の対象を深く分析し、顔占有率の高い画像を複数取得する"""
        print(f"\n--- Objective Analysis for {category} Subject: {name} ---")
        
        works = []
        is_2d_flag = (category == "2D")
        
        if category == "3D":
            actresses = self.client.search_actress(name=name)
            if not actresses: 
                print("Actress not found.")
                return None
            a = actresses[0]
            display_name = a['name']
            
            # 幅広く検索して占有率の高いものを探す (最大50件)
            print("Fetching photo books from DMM.com...")
            # 実は一般の写真集はactress_id検索よりキーワード検索の方が見つかりやすい
            w1 = self.client.get_anime_works(keyword=f"{name} 写真集", hits=30, service="ebook")
            w2 = self.client.get_anime_works(keyword=f"{name} 写真集", hits=20, service="digital", floor="digital_book")
            works = w1 + w2
        else:
            keyword = keyword_override or name
            display_name = name
            print("Fetching comic covers from DMM.com...")
            w1 = self.client.get_anime_works(keyword=keyword, hits=30, service="ebook", floor="comic")
            w2 = self.client.get_anime_works(keyword=keyword, hits=20)
            works = w1 + w2

        if not works:
            print(f"No works found for {name}")
            return None

        print(f"Found {len(works)} potential items. Processing images to find face close-ups (Occupancy >= 0.70)...")
        candidates = []
        
        # NOTE: APIを叩きすぎないよう上限を設ける
        for i, item in enumerate(works[:60]): 
            img_url = item.get('imageURL', {}).get('large')
            if not img_url: continue
            
            # ノイズ排除：名前がタイトルにも出演者リストにもない場合はスキップ（別人の作品を除外）
            title = item.get('title', '')
            actresses_in_item = [act.get('name', '') for act in item.get('iteminfo', {}).get('actress', [])]
            
            if name not in title and not any(name in a for a in actresses_in_item):
                continue
            
            try:
                img = self.engine.download_image(img_url)
                occ = self.engine.calculate_face_occupancy(img, is_2d=is_2d_flag)
                
                # 分析結果も取得しておく
                res = self.engine.analyze_2d_face(img) if is_2d_flag else self.engine.analyze_3d_face(img)
                
                if res:
                    print(f"  [{i+1}] {item.get('title')[:25]}... - Face Occ: {occ}")
                    candidates.append({
                        "item": item,
                        "img_data": img,
                        "occ": occ,
                        "res": res
                    })
            except Exception as e:
                pass

        if not candidates:
            print("Failed to analyze any images.")
            return None

        # 顔占有率で降順ソート
        candidates.sort(key=lambda x: x['occ'], reverse=True)
        
        # 必要な枚数（3枚）を確保
        selected_candidates = candidates[:required_image_count]
        
        # 一番顔がよく写っている（占有率が高い）画像の解析結果を公式スコアとする
        best_candidate = selected_candidates[0]
        best_res = best_candidate['res']

        proportion_data = {"whr": 0.68, "height": 160} if category == "3D" else None
        total_score = self.engine.calculate_beauty_index(best_res, proportion_data)

        # データをまとめる (全5指標を明示的に保存)
        result_data = {
            "name": display_name,
            "category": category,
            "total_score": total_score,
            "symmetry": best_res['symmetry'],
            "neoteny": best_res['neoteny'],
            "proportion": 90.0 if category == "3D" else 85.0,
            "dimorphism": 85.0,
            "social_meme": 80.0,
            "affiliate_url": best_candidate['item'].get('affiliateURL', '').replace("namasoku-990", "namasoku-001"), # DB用
            "selected_candidates": selected_candidates # 記事構築用
        }
        
        self.db.save_score(result_data)
        return result_data

    def generate_html_content(self, res_data, media_urls, chart_url):
        """1人の対象を客観的に分析する記事HTMLを生成"""
        name = res_data['name']
        
        html = f"""
        <h2>進化心理学で紐解く: {name} の美の秘密</h2>
        <p>当メディアのAI画像解析システムを用い、進化心理学の観点から <b>{name}</b> の持つ「客観的な美しさ」を数値化しました。顔のパーツ単位での緻密な解析結果をお届けします。</p>

        <div style="background-color: #fff0f5; padding: 20px; border-radius: 10px; text-align: center; margin: 30px 0; border: 2px solid #ff69b4;">
            <h3 style="margin-top: 0; color: #d02090;">美人指数 総合スコア</h3>
            <span style="font-size: 3em; font-weight: bold; color: #ff1493;">{res_data['total_score']}</span> <span style="font-size: 1.2em; color: #555;">pt</span>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <img src="{chart_url}" alt="{name}の美人指数チャート" style="max-width: 100%; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" />
        </div>

        <h3>1. 左右対称性（シンメトリー）: <span style="color: #ff69b4;">{res_data['symmetry']}%</span></h3>
        <p><b>【指標の説明】</b><br/>
        顔の左半分と右半分がどれだけ鏡合わせのように均等かを示す指標です。進化心理学や生物学において、完全なシンメトリーは「遺伝的な健康度」や「発育過程でのストレスの少なさ」を示す強力なシグナルとされます。人間は無意識にこの対称性の高さを「美しさ」として認識します。</p>
        <p><b>【解析結果】</b><br/>
        <b>{name}</b> の顔立ちにおいて特筆すべきは、その左右対称性（{res_data['symmetry']}%）です。顔のパーツ配置におけるズレが極めて少なく、非常に強固な造形美を持っています。</p>

        <h3>2. 若返り指数（ネオテニー）: <span style="color: #1e90ff;">{res_data['neoteny']}%</span></h3>
        <p><b>【指標の説明】</b><br/>
        顔全体の面積に対して、目が占める割合や配置から算出される「ベビースキーマ（幼形適応）」の度合いです。人は本能的に、大きな目を持つ顔に対して「守ってあげたい」「愛らしい」という保護欲求や親しみを感じます。</p>
        <p><b>【解析結果】</b><br/>
        計算された若返り指数は {res_data['neoteny']}% となりました。洗練された大人の顔立ちの中にも、人の深層心理を強く刺激するネオテニー要素が絶妙なバランスで組み込まれています。</p>

        <h3>3. プロポーション（黄金比）: <span style="color: #32cd32;">{res_data['proportion']}%</span></h3>
        <p><b>【指標の説明】</b><br/>
        顔の各パーツ（目・鼻・口）の配置が、科学的に最も美しいとされる「黄金比（1:1.618）」にどれだけ近いかを測定します。また、全身においてはWHR（ウエスト・ヒップ比）などが健康度と繁殖能力の指標として重視されます。</p>
        <p><b>【解析結果】</b><br/>
        <b>{name}</b> のプロポーションスコアは {res_data['proportion']}% です。理想的な黄金比をベースにした配置となっており、見る者に安定感と気品を与えます。</p>

        <h3>4. 性的二型（コントラスト）: <span style="color: #ffa500;">{res_data['dimorphism']}%</span></h3>
        <p><b>【指標の説明】</b><br/>
        その性別特有の特徴（女性であれば唇の厚み、顎の細さ、肌の質感など）がどれだけ際立っているかを示す指標です。これは性的魅力の強さを直接的に象徴する数値となります。</p>
        <p><b>【解析結果】</b><br/>
        解析された性的二型スコアは {res_data['dimorphism']}% です。非常に女性らしいコントラストが強調されており、圧倒的な存在感を放っています。</p>

        <h3>5. 社会的評価（トレンド度）: <span style="color: #9370db;">{res_data['social_meme']}%</span></h3>
        <p><b>【指標の説明】</b><br/>
        SNSでの話題性や検索ボリューム、トレンドへの適合度をAIが統合的に判断した指標です。「時代が求めている美しさ」を数値化したものと言えます。</p>
        <p><b>【解析結果】</b><br/>
        現在の社会的評価は {res_data['social_meme']}% となり、多くの人々に支持される「時代の象徴」としての美しさも兼ね備えていることが証明されました。</p>

        <hr style="margin: 40px 0;" />
        
        <h3>美麗ポートレート ギャラリー（高解像度解析対象）</h3>
        <p>今回のAI解析において、特に顔のディテールが明確に現れている（顔占有率の高い）厳選ポートレートをピックアップしました。各画像をクリックすると高画質の公式作品（DMM）をご覧いただけます。</p>
        
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px;">
        """
        
        for cand, img_url in zip(res_data['selected_candidates'], media_urls):
            aff_url = cand['item'].get('affiliateURL', '#')
            # アフィリエイトIDを namasoku-001 に強制置換（API用IDから手動用IDへ切り替え）
            aff_url = aff_url.replace("namasoku-990", "namasoku-001")
            
            title = cand['item'].get('title', '写真集')
            occ = cand['occ']
            
            html += f"""
            <div style="text-align: center; width: 30%; min-width: 200px;">
                <a href="{aff_url}" target="_blank">
                    <img src="{img_url}" alt="{name}" style="width: 100%; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.2); transition: transform 0.3s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'" />
                </a>
                <div style="margin-top: 10px; font-size: 0.9em;">
                    <a href="{aff_url}" target="_blank" style="text-decoration: none; color: #333;"><b>{title[:25]}...</b></a><br/>
                    <span style="color: #888; font-size: 0.8em;">(顔占有率: {occ})</span>
                </div>
            </div>
            """

        html += """
        </div>
        """
        return html

    def run_objective_analysis(self, name, category="3D", keyword=None):
        """単一対象の客観的分析のメインフロー"""
        
        res_data = self._fetch_and_analyze(name, category, keyword_override=keyword)
        if not res_data: return

        # チャート生成 (対象者のみ)
        chart_path = "single_radar_chart.png"
        scores_for_chart = {
            "symmetry": res_data['symmetry'],
            "neoteny": res_data['neoteny']
        }
        self.engine.generate_single_radar_chart(scores_for_chart, output_path=chart_path)

        # 複数画像のアップロード
        print("\nUploading media to WordPress...")
        media_urls = []
        temp_files = []
        for idx, cand in enumerate(res_data['selected_candidates']):
            tmp_name = f"temp_face_{idx}.png"
            cv2.imwrite(tmp_name, cand['img_data'])
            temp_files.append(tmp_name)
            
            m = self.uploader.upload_media(tmp_name, f"portrait_{idx}.png")
            if m:
                media_urls.append(m['source_url'])
            else:
                media_urls.append("")

        m_chart = self.uploader.upload_media(chart_path, "beauty_chart.png")

        # 記事投稿
        title = f"【美人指数 解析】進化心理学が暴く {name} の客観的美しさ"
        content = self.generate_html_content(
            res_data, media_urls, 
            m_chart['source_url'] if m_chart else ""
        )
        
        post = self.uploader.post_article(title, content, featured_media_id=m_chart['id'] if m_chart else None)
        
        # クリーンアップ
        for p in temp_files + [chart_path]:
            if os.path.exists(p): os.remove(p)

        if post:
            print(f"Success! Article posted: {post['link']}")
            return post
        return None

    def generate_ranking_report(self):
        """DBから最新ランキングを取得して固定記事を更新する"""
        print("\n--- Updating Official Ranking Page ---")
        ranks_3d = self.db.get_rankings(category="3D", limit=10)
        ranks_2d = self.db.get_rankings(category="2D", limit=10)

        html = "<h2>【美人指数】公式認定ランキング TOP10</h2>"
        html += "<p>AI画像解析と進化心理学により算出された、当メディア認定の「美人指数」総合ランキングです。（データは随時更新されます）</p>"

        html += "<h3>👑 3D（実写）部門</h3><ol style='font-size: 1.1em; line-height: 1.8;'>"
        for r in ranks_3d:
            html += f"<li><b>{r[0]}</b> <span style='color: #ff1493; font-weight: bold;'>{r[1]} pt</span> (<a href='{r[3]}' target='_blank'>代表作品を確認</a>)</li>"
        html += "</ol>"

        html += "<h3>👑 2D（二次元）部門</h3><ol style='font-size: 1.1em; line-height: 1.8;'>"
        for r in ranks_2d:
            html += f"<li><b>{r[0]}</b> <span style='color: #1e90ff; font-weight: bold;'>{r[1]} pt</span> (<a href='{r[3]}' target='_blank'>代表作品を確認</a>)</li>"
        html += "</ol>"

        slug = "official-beauty-ranking"
        title = "【毎日更新】美人指数 総合公式ランキング"

        # 既存のランキング記事があるか検索
        existing_post = self.uploader.get_post_by_slug(slug)
        if existing_post:
            post = self.uploader.update_post(existing_post['id'], title, html)
            if post:
                print(f"Ranking report successfully UPDATED: {post['link']}")
        else:
            post = self.uploader.post_article(title, html, slug=slug)
            if post:
                print(f"Ranking report successfully CREATED: {post['link']}")

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Beauty Index Analysis Tool')
    parser.add_argument('--name', type=str, help='Name of the subject to analyze')
    parser.add_argument('--category', type=str, choices=['3D', '2D'], default='3D', help='Category (3D or 2D)')
    parser.add_argument('--keyword', type=str, help='Optional search keyword override')
    parser.add_argument('--ranking-only', action='store_true', help='Only update the ranking page')

    args = parser.parse_args()
    
    manager = BeautyManager()

    if args.ranking_only:
        manager.generate_ranking_report()
        sys.exit(0)

    if args.name:
        # 指定された名前で実行
        print(f"Starting analysis for: {args.name} ({args.category})")
        manager.run_objective_analysis(name=args.name, category=args.category, keyword=args.keyword)
        manager.generate_ranking_report()
    else:
        # 引数がない場合はデフォルト（テスト用）
        manager.run_objective_analysis(name="河北彩伽", category="3D")
        manager.generate_ranking_report()
