class ArticleGenerator:
    def __init__(self):
        pass

    def _generate_stars(self, average):
        if not average: return ""
        avg = float(average)
        full_stars = int(avg)
        half_star = 1 if avg - full_stars >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        return "★" * full_stars + "☆" * half_star + "☆" * (empty_stars - half_star if empty_stars > 0 else 0)

    def generate_ranking_html(self, title, items, subtitle="DMM.com公式データに基づく人気ランキング"):
        """ランキング形式の記事HTMLを生成（YouTube埋め込み対応版）"""
        html = f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; max-width: 800px; margin: 0 auto; background: #fafafa; padding: 10px;">
            <div style="text-align: center; margin-bottom: 30px; padding: 20px; background: #fff; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h2 style="color: #d32f2f; margin: 0 0 10px; font-size: 26px;">{title}</h2>
                <p style="color: #666; font-size: 14px; margin: 0;">{subtitle}</p>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; padding-bottom: 20px;">
        """
        
        for i, item in enumerate(items, 1):
            img_url = item.get('imageURL', {}).get('large', 'https://p.dmm.com/p/general/base/noimage_large.png')
            aff_url = item.get('affiliateURL', '')
            item_title = item.get('title', '')
            price = item.get('prices', {}).get('price', 'N/A')
            review = item.get('review', {})
            avg_score = review.get('average', '0.0')
            count = review.get('count', 0)
            reason = item.get('ranking_reason', '高評価・売れ筋アイテム')
            youtube_id = item.get('youtube_video_id')
            
            stars = self._generate_stars(avg_score)
            
            # Use YouTube iframe if image is missing but video is available
            media_html = ""
            if not item.get('imageURL') and youtube_id:
                media_html = f"""
                <div style="position: relative; width: 100%; padding-top: 56.25%; background: #000;">
                    <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" 
                        src="https://www.youtube.com/embed/{youtube_id}" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
                    </iframe>
                </div>
                """
            else:
                media_html = f"""
                <a href="{aff_url}" target="_blank" style="display: block; overflow: hidden;">
                    <img src="{img_url}" alt="{item_title}" style="width: 100%; height: 250px; object-fit: cover; transition: transform 0.3s;">
                </a>
                """
            
            html += f"""
            <div style="border: 1px solid #eee; border-radius: 12px; overflow: hidden; background: #fff; box-shadow: 0 10px 20px rgba(0,0,0,0.05); position: relative; display: flex; flex-direction: column;">
                <div style="position: absolute; top: 0; left: 0; background: linear-gradient(135deg, #d32f2f, #ff5252); color: #fff; padding: 8px 15px; border-bottom-right-radius: 12px; font-weight: bold; z-index: 10; font-size: 18px;">第{i}位</div>
                
                {media_html}
                
                <div style="padding: 20px; flex-grow: 1;">
                    <span style="display: inline-block; background: #fff9c4; color: #f57f17; font-size: 11px; padding: 2px 8px; border-radius: 10px; margin-bottom: 10px; font-weight: bold;">{reason}</span>
                    <h3 style="font-size: 17px; margin: 0 0 12px; line-height: 1.4; color: #111; height: 2.8em; overflow: hidden;">{item_title}</h3>
                    
                    <div style="margin-bottom: 15px;">
                        <span style="color: #ffb400; font-size: 18px;">{stars}</span>
                        <span style="color: #666; font-size: 13px; margin-left: 5px;">({avg_score} / {count}件)</span>
                    </div>
                    
                    <p style="color: #d32f2f; font-size: 18px; font-weight: bold; margin-bottom: 20px;">{price}円〜</p>
                    
                    <a href="{aff_url}" target="_blank" style="display: block; text-align: center; background: #d32f2f; color: #fff; padding: 12px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 0 #b71c1c;">詳細ページで確認する</a>
                </div>
            </div>
            """
            
        html += """
            </div>
            <div style="text-align: center; color: #888; font-size: 12px; padding: 30px 0; background: #eee; border-radius: 10px; margin-top: 20px;">
                <p>※価格や在庫状況は変動するため、必ずリンク先の公式サイトにてご確認ください。</p>
            </div>
        </div>
        """
        return html

    def generate_spotlight_html(self, item, scores, radar_url):
        """個別アイテム（美人度分析付き）の記事HTMLを生成（フッター文言削除版）"""
        title = item.get('title', '')
        img_url = item.get('imageURL', {}).get('large', 'https://p.dmm.com/p/general/base/noimage_large.png')
        aff_url = item.get('affiliateURL', '')
        price = item.get('prices', {}).get('price', 'N/A')
        review = item.get('review', {})
        avg_score = review.get('average', '0.0')
        count = review.get('count', 0)
        youtube_id = item.get('youtube_video_id')
        
        stars = self._generate_stars(avg_score)
        
        # Parse description
        desc = item.get('iteminfo', {}).get('maker', [{}])[0].get('name', '')
        if 'campaign' in item:
            desc += f" <br>【期間限定キャンペーン】{item['campaign'][0].get('title', '')}"

        # Use YouTube if image is missing
        media_html = ""
        if not item.get('imageURL') and youtube_id:
            media_html = f"""
            <div style="position: relative; width: 100%; padding-top: 56.25%; background: #000; border-radius: 15px; overflow: hidden; margin-bottom: 40px;">
                <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" 
                    src="https://www.youtube.com/embed/{youtube_id}" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
                </iframe>
            </div>
            """
        else:
            media_html = f"""
            <div style="text-align: center; margin-bottom: 40px;">
                <img src="{img_url}" alt="{title}" style="max-width: 90%; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">
            </div>
            """

        html = f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; max-width: 800px; margin: 0 auto; line-height: 1.6; background: #fff;">
            <div style="background: linear-gradient(to bottom, #fff0f5, #ffffff); padding: 40px 20px; text-align: center; border-bottom: 1px solid #ffd1dc;">
                <span style="background: #ff1493; color: #fff; padding: 4px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; letter-spacing: 1px;">AI BEAUTY ANALYSIS</span>
                <h1 style="color: #ff1493; font-size: 28px; margin: 15px 0;">{title}</h1>
                <div style="margin-top: 10px; color: #666;">
                    <span style="color: #ffb400;">{stars}</span> ユーザー評価: {avg_score} ({count}件のレビュー)
                </div>
            </div>
            
            <div style="padding: 30px 20px;">
                {media_html}

                <div style="background: #ffffff; padding: 25px; border-radius: 20px; margin-bottom: 40px; border: 2px solid #fff0f5; box-shadow: 0 5px 15px rgba(255,20,147,0.05);">
                    <h2 style="color: #ff1493; font-size: 20px; text-align: center; margin-bottom: 25px; display: flex; align-items: center; justify-content: center;">
                        <span style="margin-right: 10px;">📊</span> AIによる美人度分析レポート
                    </h2>
                    <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 20px;">
                        <div style="flex: 1; min-width: 280px; text-align: center;">
                            <img src="{radar_url}" alt="Beauty Radar" style="width: 100%; max-width: 320px; height: auto;">
                        </div>
                        <div style="flex: 1; min-width: 280px; background: #fffafb; padding: 25px; border-radius: 15px;">
                            <div style="text-align: center; margin-bottom: 20px;">
                                <div style="font-size: 14px; color: #999; margin-bottom: 5px;">Beauty Index Score</div>
                                <div style="font-size: 60px; font-weight: bold; color: #ff1493; line-height: 1;">{scores['total']}<span style="font-size: 18px; margin-left: 5px;">pts</span></div>
                            </div>
                            <table style="width: 100%; font-size: 15px; border-collapse: collapse;">
                                <tr style="border-bottom: 1px dashed #ffd1dc;">
                                    <td style="padding: 10px 0; color: #666;">✨ 左右対称性</td>
                                    <td style="padding: 10px 0; text-align: right; font-weight: bold; color: #ff1493;">{scores['symmetry']}</td>
                                </tr>
                                <tr style="border-bottom: 1px dashed #ffd1dc;">
                                    <td style="padding: 10px 0; color: #666;">👶 黄金比指数</td>
                                    <td style="padding: 10px 0; text-align: right; font-weight: bold; color: #ff1493;">{scores['neoteny']}</td>
                                </tr>
                                <tr style="border-bottom: 1px dashed #ffd1dc;">
                                    <td style="padding: 10px 0; color: #666;">📏 プロポーション</td>
                                    <td style="padding: 10px 0; text-align: right; font-weight: bold; color: #ff1493;">{int(scores['proportion'])}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0; color: #666;">💕 性的魅力度</td>
                                    <td style="padding: 10px 0; text-align: right; font-weight: bold; color: #ff1493;">{int(scores['dimorphism'])}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </div>

                <div style="background: #fdfdfd; padding: 25px; border-radius: 15px; border-left: 5px solid #ff1493;">
                    <h3 style="margin-top: 0; font-size: 18px; color: #333;">アイテム詳細</h3>
                    <p style="color: #555; line-height: 1.8;">{desc}</p>
                    <div style="margin-top: 25px; font-size: 20px; font-weight: bold; color: #ff1493;">価格：{price}円〜</div>
                </div>

                <div style="text-align: center; margin: 50px 0 20px;">
                    <a href="{aff_url}" target="_blank" style="display: inline-block; background: linear-gradient(to right, #ff1493, #ff4081); color: #fff; padding: 18px 50px; text-decoration: none; border-radius: 40px; font-weight: bold; font-size: 20px; box-shadow: 0 10px 20px rgba(255,20,147,0.3); transition: 0.3s;">
                        公式サイトで今すぐチェック ＞
                    </a>
                </div>
            </div>
            
            <div style="background: #333; color: #fff; text-align: center; padding: 20px; font-size: 12px;">
                © AI Beauty Index System / DMM Affiliate<br>
                Powered by MediaPipe & OpenCV Analysis
            </div>
        </div>
        """
        return html
