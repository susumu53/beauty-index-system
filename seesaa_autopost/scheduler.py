import datetime

class Scheduler:
    def __init__(self):
        # 24時間のスケジュール定義 (hour: (category, type, sort))
        # sort: 'rank', 'date' (New), 'review'
        self.schedule = {
            0:  ("tv", "ranking", "rank"),         # 人気ランキング
            1:  ("idol", "spotlight", "rank"),     # 美人度分析
            2:  ("books", "ranking", "rank"),      # 人気ランキング
            3:  ("games", "ranking", "date"),      # ★新着ゲーム
            4:  ("stage", "spotlight", "rank"),    # 注目舞台
            5:  ("shopping", "ranking", "rank"),   # 人気ランキング
            6:  ("seasonal", "ranking", "rank"),   # 季節モノ
            7:  ("tv", "ranking", "rank"),         # 人気ランキング
            8:  ("idol", "spotlight", "rank"),     # 美人度分析
            9:  ("books", "spotlight", "rank"),    # 注目作品
            10: ("games", "spotlight", "date"),    # ★新着ゲーム
            11: ("shopping", "spotlight", "rank"), # 注目通販
            12: ("seasonal", "spotlight", "rank"), # 季節注目
            13: ("tv", "spotlight", "rank"),       # 特集
            14: ("idol", "ranking", "rank"),       # 人気アイドル
            15: ("books", "ranking", "date"),      # ★新着コミック
            16: ("games", "ranking", "rank"),      # 人気ゲーム
            17: ("shopping", "ranking", "rank"),   # 人気通販
            18: ("stage", "ranking", "rank"),      # 舞台ランキング
            19: ("tv", "ranking", "date"),         # ★最新番組
            20: ("idol", "spotlight", "rank"),     # 美人度分析
            21: ("books", "spotlight", "date"),    # ★最新コミック
            22: ("games", "spotlight", "rank"),    # 注目ソフト
            23: ("seasonal", "ranking", "rank"),   # 季節まとめ
        }

    def get_current_task(self):
        hour = datetime.datetime.now().hour
        return self.schedule.get(hour, ("tv", "ranking", "rank"))

    def is_sale_hour(self, hour):
        # 特定の時間帯（例: 3, 10, 15, 21）はセール情報を優先するなど
        return hour in [3, 11, 17]

    def get_seasonal_keyword(self):
        month = datetime.datetime.now().month
        keywords = {
            1: "福袋 初売り 暖房",
            2: "バレンタイン チョコ 節分",
            3: "ホワイトデー 卒業 新生活",
            4: "お花見 入学 キャンプ",
            5: "母の日 ゴールデンウィーク",
            6: "父の日 梅雨 雨具",
            7: "お中元 夏休み 海水浴 水着",
            8: "夏祭り 花火 キャンプ",
            9: "敬老の日 お月見 秋の味覚",
            10: "ハロウィン 仮装 秋キャンプ",
            11: "ボジョレーヌーボー 紅葉 暖房",
            12: "クリスマス プレゼント お歳暮",
        }
        return keywords.get(month, "ギフト 人気")
