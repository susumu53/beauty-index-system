import os
import random
import datetime
import urllib.parse
import requests
import re
from dmm_api_v3 import DMMClientV3

class GourmetArticleGenerator:
    """料理・グルメブログ (syoshinsya2525.seesaa.net) 専用 記事生成エンジン"""

    def __init__(self):
        self.dmm = DMMClientV3()

    def _get_youtube_video_id(self, query):
        """YouTube動画IDを検索して取得"""
        try:
            search_query = f"{query} レシピ 作り方 公式"
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            r = requests.get(url, headers=headers, timeout=10)
            m1 = re.search(r'\"videoRenderer\":\{\"videoId\":\"(.*?)\"', r.text)
            if m1:
                return m1.group(1)
            m2 = re.search(r'watch\?v=([a-zA-Z0-9_-]{11})', r.text)
            if m2:
                return m2.group(1)
        except Exception as e:
            print(f"YouTube search failed for {query}: {e}")
        return None

    def generate_buzz_recipe_article(self):
        """1. YouTubeバズレシピ特集記事を生成"""
        recipes_database = [
            {
                "dish": "至高の生姜焼き",
                "creator": "料理研究家リュウジ",
                "yt_query": "リュウジ 至高の生姜焼き",
                "features": "タレにすりおろし玉ねぎとリンゴを加えることで、肉が格段に柔らかくなり、名店以上の深いコクとタレ絡みを実現した伝説のレシピ。",
                "materials": ["豚肩ロースまたは豚バラ肉 250g", "玉ねぎ 1/2個", "生姜（すりおろし） 大さじ1", "醤油・酒・みりん 各大さじ2", "砂糖 小さじ1"],
                "tips": ["豚肉は焼く直前に常温に戻し、強火でサッと焼き固めて肉汁を逃さない", "タレに玉ねぎのすりおろしを加えることで酵素の力で肉が柔らかくなる", "仕上げに追い生姜を少し加えると香りが劇的にアップ"]
            },
            {
                "dish": "極上ペペロンチーノ",
                "creator": "パスタ専門シェフ直伝",
                "yt_query": "ペペロンチーノ 乳化 コツ プロ",
                "features": "具材はニンニクと唐辛子だけなのに、レストランの味を完全再現。徹底的な『乳化』の技術で、とろりとした極上ソースに仕上げる決定版。",
                "materials": ["スパゲッティ（1.6〜1.8mm） 100g", "ニンニク 2片", "赤唐辛子 1本", "エクストラバージンオリーブオイル 大さじ3", "茹で汁 60ml", "塩 適量"],
                "tips": ["ニンニクは弱火でじっくり熱し、オイルに香りを限界まで移す", "パスタの茹で汁の塩分濃度はしっかり1%をキープする", "火を止めてから茹で汁とオイルを素早く激しくフライパンを振って白濁させる（乳化）"]
            },
            {
                "dish": "至高の炒飯（チャーハン）",
                "creator": "町中華再現レシピ",
                "yt_query": "リュウジ 至高の炒飯",
                "features": "家庭の火力でもパラパラ＆しっとりを両立！ラードとネギ油、そして秘密の隠し味で中華料理屋のパラパラチャーハンを完全再現。",
                "materials": ["温かいご飯 200g", "卵 2個", "長ネギ 1/2本", "チャーシュー（または豚バラ） 50g", "ラード（またはサラダ油） 大さじ1.5", "中華スープの素・塩コショウ・醤油 少々"],
                "tips": ["ご飯は炊きたてを少し冷まして余分な水分を飛ばしておく", "卵を入れたらすぐにご飯を投入し、卵をコーティングするように混ぜ合わせる", "鍋肌から醤油を焦がし入れ、香ばしい香りを全体にまとわせる"]
            },
            {
                "dish": "フライパンで作る極上ハンバーグ",
                "creator": "洋食名店シェフ再現",
                "yt_query": "ハンバーグ 肉汁 肉の焼き方 コツ",
                "features": "切った瞬間に溢れ出す肉汁！氷と飴色玉ねぎ、そして蒸し焼きの温度管理で、専門店クオリティのふっくらジューシーなハンバーグに仕上げます。",
                "materials": ["牛豚合い挽き肉 300g", "玉ねぎ 1個", "パン粉 大さじ4", "牛乳 大さじ3", "卵 1個", "塩・ナツメグ・黒胡椒 適量"],
                "tips": ["ひき肉は直前まで冷蔵庫で冷やし、手の熱が伝わらないよう素早くこねる", "両手でキャッチボールをしてしっかり空気を抜く", "焼き目をつけたら弱火にして蓋をし、じっくり蒸し焼きにする"]
            }
        ]

        recipe = random.choice(recipes_database)
        video_id = self._get_youtube_video_id(recipe["yt_query"])

        title = f"【話題のバズレシピ】自宅でプロの味！「{recipe['dish']}」の作り方＆極上に仕上げる3つの黄金ルール"
        categories = ["バズレシピ"]
        tags = ["バズレシピ", "YouTube", recipe["dish"], "簡単料理", "プロの裏技", "時短レシピ"]

        materials_li = "".join([f"<li style='margin-bottom: 6px;'>{m}</li>" for m in recipe["materials"]])
        tips_li = "".join([f"<li style='margin-bottom: 10px;'><strong>【ポイント{i+1}】</strong> {tip}</li>" for i, tip in enumerate(recipe["tips"])])

        video_embed_html = ""
        if video_id:
            video_embed_html = f"""
            <div style="position: relative; width: 100%; padding-top: 56.25%; background: #1a1a1a; border-radius: 8px; overflow: hidden; margin: 25px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.15);">
                <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;"
                    src="https://www.youtube.com/embed/{video_id}"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
                </iframe>
            </div>
            """

        content = f"""
<div style="font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', sans-serif; line-height: 1.85; color: #2d2926; max-width: 720px; margin: 0 auto; padding: 10px;">

    <!-- PR表記 -->
    <div style="font-size: 11px; color: #78716c; text-align: right; margin-bottom: 10px;">
        【PR】本記事にはアフィリエイト広告が含まれる場合があります
    </div>

    <!-- 記事トップ概要ボックス -->
    <div style="background: #fdfbf7; border: 1px solid #e7dfd5; border-left: 5px solid #c59b6d; border-radius: 6px; padding: 18px 20px; margin-bottom: 25px;">
        <span style="display: inline-block; background: #c59b6d; color: #ffffff; font-size: 12px; font-weight: bold; padding: 3px 10px; border-radius: 4px; margin-bottom: 8px;">バズレシピ注目特集</span>
        <h2 style="font-size: 20px; color: #242220; margin: 0 0 10px 0; line-height: 1.4;">
            今ネットで大絶賛！「{recipe['dish']}」を究極に美味しく作るテクニック
        </h2>
        <p style="font-size: 14.5px; margin: 0; color: #44403c;">
            {recipe['features']}
        </p>
    </div>

    <!-- YouTube動画埋め込み -->
    {video_embed_html}

    <!-- 材料リスト -->
    <div style="background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin: 25px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
        <h3 style="font-size: 17px; color: #242220; margin: 0 0 15px 0; border-bottom: 2px solid #c59b6d; padding-bottom: 8px;">
            📝 用意する材料（目安）
        </h3>
        <ul style="margin: 0; padding-left: 22px; font-size: 14.5px; color: #374151;">
            {materials_li}
        </ul>
    </div>

    <!-- プロ直伝のコツ -->
    <div style="background: #fffdfa; border: 1px solid #f3ebe1; border-radius: 8px; padding: 20px; margin: 25px 0;">
        <h3 style="font-size: 17px; color: #92400e; margin: 0 0 15px 0;">
            🔥 ここが違う！失敗しないプロ直伝の3大ポイント
        </h3>
        <ol style="margin: 0; padding-left: 22px; font-size: 14.5px; color: #4b5563;">
            {tips_li}
        </ol>
    </div>

    <!-- DMMブックス/レシピ本訴求 -->
    <div style="background: linear-gradient(135deg, #242220, #36322d); border-radius: 8px; padding: 22px; margin: 30px 0; color: #ffffff; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
        <span style="background: #c59b6d; color: #fff; font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 3px; display: inline-block; margin-bottom: 8px;">料理をもっと極めるなら</span>
        <h3 style="color: #f5efe6; font-size: 18px; margin: 0 0 10px 0;">人気料理研究家のレシピ本＆名作グルメ漫画をチェック！</h3>
        <p style="font-size: 13.5px; color: #d6d3d1; margin: 0 0 18px 0;">DMMブックスなら初回限定クーポンや無料試し読み作品が多数揃っています。</p>
        <a href="https://al.dmm.com/?lurl=https%3A%2F%2Fbook.dmm.com%2F&af_id=namasoku-991&ch=api" target="_blank" rel="nofollow" style="display: inline-block; background: linear-gradient(135deg, #e0b484, #c59b6d); color: #242220; font-weight: bold; font-size: 15px; padding: 12px 28px; border-radius: 25px; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
            📖 DMMブックスでレシピ本・グルメ本を探す
        </a>
    </div>

</div>
"""
        return {"title": title, "content": content, "categories": categories, "tags": tags}

    def _is_safe_gourmet_title(self, title):
        """成人向け・センシティブなタイトルを除外するフィルタ"""
        ng_words = ["淫", "エロ", "調教", "巨乳", "愛人", "オトナ", "痴漢", "抱か", "孕", "初体験", "フェラ", "生ハメ", "セフレ"]
        for ng in ng_words:
            if ng in title:
                return False
        return True

    def generate_manga_article(self):
        """2. グルメ漫画特集記事を生成（DMMブックスAPI連携）"""
        # 人気・名作グルメ漫画のシードリスト
        seed_mangas = [
            "ダンジョン飯",
            "きのう何食べた？",
            "異世界居酒屋「のぶ」",
            "孤独のグルメ",
            "ワカコ酒",
            "ラーメン大好き小泉さん",
            "舞妓さんちのまかないさん",
            "信長のシェフ",
            "異世界食堂",
            "山と食欲と私",
            "甘々と稲妻",
            "侠飯"
        ]
        target_seed = random.choice(seed_mangas)
        
        # まずシード漫画で検索
        raw_items = self.dmm.get_items(service="ebook", floor="comic", keyword=target_seed, hits=5, sort="rank")
        items = [it for it in raw_items if self._is_safe_gourmet_title(it.get("title", ""))]

        # ヒットしない場合は一般的な「グルメ漫画」「料理」で安全検索
        if not items:
            raw_items = self.dmm.get_items(service="ebook", floor="comic", keyword="料理 グルメ", hits=10, sort="rank")
            items = [it for it in raw_items if self._is_safe_gourmet_title(it.get("title", ""))]

        if not items:
            # フォールバック
            items = [{"title": target_seed, "affiliateURL": "https://book.dmm.com/", "imageURL": {"large": "https://p.dmm.com/p/general/base/noimage_large.png"}}]

        main_item = items[0]
        main_title = main_item.get("title", target_seed)
        clean_title = re.sub(r'[\(（【].*?[\)）】]', '', main_title).strip()

        title = f"【至高のグルメ漫画】読むとお腹が空く！食欲と料理欲をそそる傑作『{clean_title}』ほかおすすめ特集"
        categories = ["グルメ漫画"]
        tags = ["グルメ漫画", "DMMブックス", "料理", "おすすめ漫画", clean_title, "飯テロ"]

        items_html = ""
        for i, it in enumerate(items[:3], 1):
            it_title = it.get("title", "")
            it_aff = it.get("affiliateURL", "https://book.dmm.com/")
            it_img = it.get("imageURL", {}).get("large", "https://p.dmm.com/p/general/base/noimage_large.png")
            it_price = it.get("prices", {}).get("price", "")
            price_txt = f"{it_price}円（税込）" if it_price else "セール・ポイント還元中"

            items_html += f"""
            <div style="display: flex; flex-wrap: wrap; background: #ffffff; border: 1px solid #e7e5e4; border-radius: 8px; margin-bottom: 20px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
                <div style="flex: 0 0 160px; max-width: 160px; background: #f5f5f4; text-align: center; padding: 10px; box-sizing: border-box;">
                    <a href="{it_aff}" target="_blank" rel="nofollow">
                        <img src="{it_img}" alt="{it_title}" style="max-width: 100%; height: auto; border-radius: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.15);">
                    </a>
                </div>
                <div style="flex: 1; min-width: 240px; padding: 16px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <span style="display: inline-block; background: #c59b6d; color: #fff; font-size: 11px; font-weight: bold; padding: 2px 8px; border-radius: 3px; margin-bottom: 6px;">注目作 {i}</span>
                        <h4 style="font-size: 16px; color: #242220; margin: 0 0 8px 0; line-height: 1.4;">
                            <a href="{it_aff}" target="_blank" rel="nofollow" style="color: #242220; text-decoration: none;">{it_title}</a>
                        </h4>
                        <p style="font-size: 13px; color: #78716c; margin: 0 0 10px 0;">電子書籍価格：<strong style="color: #b91c1c;">{price_txt}</strong></p>
                    </div>
                    <div style="text-align: right; margin-top: 10px;">
                        <a href="{it_aff}" target="_blank" rel="nofollow" style="display: inline-block; background: #c59b6d; color: #ffffff; font-size: 13px; font-weight: bold; padding: 8px 18px; border-radius: 4px; text-decoration: none;">
                            📖 DMMブックスで試し読みする
                        </a>
                    </div>
                </div>
            </div>
            """

        content = f"""
<div style="font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', sans-serif; line-height: 1.85; color: #2d2926; max-width: 720px; margin: 0 auto; padding: 10px;">

    <!-- PR表記 -->
    <div style="font-size: 11px; color: #78716c; text-align: right; margin-bottom: 10px;">
        【PR】本記事にはアフィリエイト広告（DMMブックス）が含まれます
    </div>

    <!-- 記事トップ概要ボックス -->
    <div style="background: #fdfbf7; border: 1px solid #e7dfd5; border-left: 5px solid #c59b6d; border-radius: 6px; padding: 18px 20px; margin-bottom: 25px;">
        <span style="display: inline-block; background: #c59b6d; color: #ffffff; font-size: 12px; font-weight: bold; padding: 3px 10px; border-radius: 4px; margin-bottom: 8px;">今週の厳選グルメコミック</span>
        <h2 style="font-size: 20px; color: #242220; margin: 0 0 10px 0; line-height: 1.4;">
            読んだら今夜の献立が決まる！飯テロ＆感動の極上グルメ漫画特集
        </h2>
        <p style="font-size: 14.5px; margin: 0; color: #44403c;">
            美味しい料理描写と、そこに込められた人間ドラマが魅力のグルメ漫画。作中に出てくる再現レシピに挑戦したくなる話題の注目作品をピックアップしました！
        </p>
    </div>

    <!-- コミック一覧 -->
    <div style="margin: 25px 0;">
        <h3 style="font-size: 18px; color: #242220; margin: 0 0 15px 0; border-bottom: 2px solid #c59b6d; padding-bottom: 8px;">
            📚 今すぐ読みたい！おすすめグルメ作品
        </h3>
        {items_html}
    </div>

    <!-- 公式訴求バナー風枠 -->
    <div style="background: #242220; border-radius: 8px; padding: 22px; margin: 30px 0; color: #ffffff; text-align: center;">
        <h3 style="color: #e0b484; font-size: 18px; margin: 0 0 10px 0;">電子書籍ならDMMブックスが超お得！</h3>
        <p style="font-size: 13.5px; color: #d6d3d1; margin: 0 0 18px 0;">お得な割引クーポンやポイント還元で、人気コミックを一気読みできます。</p>
        <a href="https://al.dmm.com/?lurl=https%3A%2F%2Fbook.dmm.com%2F&af_id=namasoku-991&ch=api" target="_blank" rel="nofollow" style="display: inline-block; background: linear-gradient(135deg, #e0b484, #c59b6d); color: #242220; font-weight: bold; font-size: 15px; padding: 12px 28px; border-radius: 25px; text-decoration: none;">
            🔍 DMMブックスで最新グルメ漫画を探す
        </a>
    </div>

</div>
"""
        return {"title": title, "content": content, "categories": categories, "tags": tags}

    def generate_anime_tv_article(self):
        """3. グルメアニメ・料理番組特集記事を生成（DMM TV API連携 ＋ PV動画埋め込み）"""
        seed_animes = [
            "ダンジョン飯",
            "異世界居酒屋「のぶ」",
            "とんでもスキルで異世界放浪メシ",
            "ラーメン赤猫",
            "異世界食堂",
            "ゆるキャン△",
            "衛宮さんちの今日のごはん",
            "食戟のソーマ"
        ]
        target_seed = random.choice(seed_animes)

        raw_items = self.dmm.get_items(service="dmmtv", floor="dmmtv_video", keyword=target_seed, hits=3, sort="rank")
        items = [it for it in raw_items if self._is_safe_gourmet_title(it.get("title", ""))]

        if not items:
            raw_items = self.dmm.get_items(service="dmmtv", floor="dmmtv_video", keyword="料理 グルメ", hits=5, sort="rank")
            items = [it for it in raw_items if self._is_safe_gourmet_title(it.get("title", ""))]

        if not items:
            items = [{"title": target_seed, "affiliateURL": "https://tv.dmm.com/vod/"}]

        main_item = items[0]
        main_title = main_item.get("title", target_seed)
        clean_title = re.sub(r'[\(（【].*?[\)）】]', '', main_title).strip()

        video_id = self._get_youtube_video_id(f"{clean_title} 公式 PV 予告")
        aff_url = main_item.get("affiliateURL", "https://tv.dmm.com/vod/")

        title = f"【DMM TVで観る飯テロ】見たら絶対お腹が空く！極上グルメアニメ・料理作品『{clean_title}』の見どころ解説"
        categories = ["料理番組・アニメ"]
        tags = ["料理番組・アニメ", "DMMTV", "飯テロ", "アニメ", clean_title, "無料体験"]

        video_embed_html = ""
        if video_id:
            video_embed_html = f"""
            <div style="position: relative; width: 100%; padding-top: 56.25%; background: #1a1a1a; border-radius: 8px; overflow: hidden; margin: 25px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.15);">
                <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;"
                    src="https://www.youtube.com/embed/{video_id}"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
                </iframe>
            </div>
            """

        content = f"""
<div style="font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', sans-serif; line-height: 1.85; color: #2d2926; max-width: 720px; margin: 0 auto; padding: 10px;">

    <!-- PR表記 -->
    <div style="font-size: 11px; color: #78716c; text-align: right; margin-bottom: 10px;">
        【PR】本記事にはアフィリエイト広告（DMM TV）が含まれます
    </div>

    <!-- 記事トップ概要ボックス -->
    <div style="background: #fdfbf7; border: 1px solid #e7dfd5; border-left: 5px solid #0284c7; border-radius: 6px; padding: 18px 20px; margin-bottom: 25px;">
        <span style="display: inline-block; background: #0284c7; color: #ffffff; font-size: 12px; font-weight: bold; padding: 3px 10px; border-radius: 4px; margin-bottom: 8px;">DMM TV 注目作品</span>
        <h2 style="font-size: 20px; color: #242220; margin: 0 0 10px 0; line-height: 1.4;">
            深夜の飯テロ注意報！『{clean_title}』の魅力と見どころ
        </h2>
        <p style="font-size: 14.5px; margin: 0; color: #44403c;">
            映像・音・シズル感のすべてが食欲を刺激する大人気作。DMM TVならスマホ・テレビ・PCで高画質見放題で楽しめます！
        </p>
    </div>

    <!-- PV動画 -->
    {video_embed_html}

    <!-- 作品の魅力 -->
    <div style="background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin: 25px 0;">
        <h3 style="font-size: 17px; color: #242220; margin: 0 0 12px 0; border-bottom: 2px solid #0284c7; padding-bottom: 8px;">
            🎬 本作がグルメファンの心を掴んで離さない理由
        </h3>
        <ul style="margin: 0; padding-left: 20px; font-size: 14.5px; color: #374151;">
            <li style="margin-bottom: 8px;">調理シーンのリアルな音響（ジュージューと焼ける音、包丁のリズム）</li>
            <li style="margin-bottom: 8px;">登場人物たちが一口食べた瞬間の至福の表情描写</li>
            <li style="margin-bottom: 8px;">明日真似して作りたくなるこだわりの調理工程・レシピ解説</li>
        </ul>
    </div>

    <!-- DMM TV 30日間無料体験 訴求枠 -->
    <div style="background: linear-gradient(135deg, #0f172a, #1e293b); border-radius: 8px; padding: 24px; margin: 30px 0; color: #ffffff; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.25);">
        <span style="background: #0284c7; color: #fff; font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 3px; display: inline-block; margin-bottom: 8px;">月額550円（税込）でアニメ・エンタメ見放題</span>
        <h3 style="color: #38bdf8; font-size: 19px; margin: 0 0 10px 0;">DMM TVなら初回【30日間無料体験】実施中！</h3>
        <p style="font-size: 13.5px; color: #cbd5e1; margin: 0 0 20px 0;">グルメアニメはもちろん、2.5次元舞台やバラエティまで圧倒的作品数が楽しめる！まずは無料でお試し。</p>
        <a href="{aff_url}" target="_blank" rel="nofollow" style="display: inline-block; background: linear-gradient(135deg, #38bdf8, #0284c7); color: #ffffff; font-weight: bold; font-size: 16px; padding: 14px 32px; border-radius: 25px; text-decoration: none; box-shadow: 0 4px 12px rgba(2,132,199,0.4);">
            ▶ DMM TVで『{clean_title}』を無料体験で観る
        </a>
    </div>

</div>
"""
        return {"title": title, "content": content, "categories": categories, "tags": tags}

    def generate_knowhow_article(self):
        """4. 料理ノウハウ・裏技・名店の味再現記事を生成"""
        knowhow_db = [
            {
                "topic": "名店の味を自宅で！黄金比率の万能タレ＆下味レシピ5選",
                "tag": "料理ノウハウ",
                "summary": "照り焼き、生姜焼き、煮物、唐揚げ…プロの料理人が現場で使う『黄金比率』を覚えれば、レシピ本を見なくても味付けが決まります！",
                "contents": [
                    ("照り焼きの黄金比", "醤油：酒：みりん：砂糖 ＝ 2：2：2：1。どんな肉や魚もテリテリ＆上品な甘辛さに。"),
                    ("極上煮物の黄金比", "出汁：醤油：みりん：酒 ＝ 8：1：1：1。具材の風味を活かす料亭風の味わい。"),
                    ("冷めてもサクサク唐揚げの下味", "醤油：酒 ＝ 1：1 にニンニク・生姜をプラス。隠し味にマヨネーズ小さじ1を揉み込むと肉汁が閉じ込められます。")
                ]
            },
            {
                "topic": "肉が劇的に柔らかくなる！プロが実践する下処理の裏技",
                "tag": "名店の味",
                "summary": "特売の安いお肉でも、高級店のような柔らかさになる科学的な下処理のコツを徹底解説します。",
                "contents": [
                    ("筋切りと繊維の断ち方", "肉の繊維方向を見極めて垂直に包丁を入れるだけで、噛み切りやすさが段違いに。"),
                    ("重曹水またはブライン液（塩水）漬け", "水100mlに対し塩5g・砂糖5gを溶かしたブライン液に30分漬けるだけで、水分を抱え込んでジューシーに。"),
                    ("舞茸やすりおろし玉ねぎの酵素利用", "タンパク質分解酵素（プロテアーゼ）の働きで、赤身肉でも驚くほどトロトロ食感に。")
                ]
            }
        ]

        item = random.choice(knowhow_db)
        title = f"【プロ直伝】{item['topic']}"
        categories = [item["tag"]]
        tags = [item["tag"], "料理の裏技", "プロのコツ", "時短テクニック", "黄金比率"]

        sections_html = ""
        for name, desc in item["contents"]:
            sections_html += f"""
            <div style="background: #ffffff; border-left: 4px solid #c59b6d; border-radius: 4px; padding: 15px 18px; margin-bottom: 15px; box-shadow: 0 1px 4px rgba(0,0,0,0.03);">
                <h4 style="font-size: 16px; color: #242220; margin: 0 0 6px 0;">◆ {name}</h4>
                <p style="font-size: 14px; color: #4b5563; margin: 0;">{desc}</p>
            </div>
            """

        content = f"""
<div style="font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', sans-serif; line-height: 1.85; color: #2d2926; max-width: 720px; margin: 0 auto; padding: 10px;">

    <!-- PR表記 -->
    <div style="font-size: 11px; color: #78716c; text-align: right; margin-bottom: 10px;">
        【PR】本記事にはアフィリエイト広告が含まれます
    </div>

    <!-- 概要ボックス -->
    <div style="background: #fdfbf7; border: 1px solid #e7dfd5; border-left: 5px solid #c59b6d; border-radius: 6px; padding: 18px 20px; margin-bottom: 25px;">
        <span style="display: inline-block; background: #c59b6d; color: #ffffff; font-size: 12px; font-weight: bold; padding: 3px 10px; border-radius: 4px; margin-bottom: 8px;">料理の上達ノウハウ</span>
        <h2 style="font-size: 20px; color: #242220; margin: 0 0 10px 0; line-height: 1.4;">
            毎日の料理が劇的においしくなるプロの知恵
        </h2>
        <p style="font-size: 14.5px; margin: 0; color: #44403c;">
            {item['summary']}
        </p>
    </div>

    <!-- ノウハウ詳細 -->
    <div style="margin: 25px 0;">
        {sections_html}
    </div>

    <!-- 実用書DMMブックス訴求 -->
    <div style="background: #242220; border-radius: 8px; padding: 22px; margin: 30px 0; color: #ffffff; text-align: center;">
        <h3 style="color: #e0b484; font-size: 18px; margin: 0 0 10px 0;">プロの技術をもっと知りたい方へ</h3>
        <p style="font-size: 13.5px; color: #d6d3d1; margin: 0 0 18px 0;">DMMブックスでは料理の基本書や名シェフの実用ノウハウ本が電子書籍ですぐ読めます。</p>
        <a href="https://al.dmm.com/?lurl=https%3A%2F%2Fbook.dmm.com%2F&af_id=namasoku-991&ch=api" target="_blank" rel="nofollow" style="display: inline-block; background: linear-gradient(135deg, #e0b484, #c59b6d); color: #242220; font-weight: bold; font-size: 15px; padding: 12px 28px; border-radius: 25px; text-decoration: none;">
            📖 DMMブックスで料理実用書をチェック
        </a>
    </div>

</div>
"""
        return {"title": title, "content": content, "categories": categories, "tags": tags}

    def generate_random_article(self):
        """ランダムまたは曜日別で最適な記事を生成"""
        generators = [
            self.generate_buzz_recipe_article,
            self.generate_manga_article,
            self.generate_anime_tv_article,
            self.generate_knowhow_article
        ]
        chosen = random.choice(generators)
        return chosen()
