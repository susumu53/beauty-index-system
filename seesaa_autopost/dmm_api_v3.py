import os
import requests
from dotenv import load_dotenv

load_dotenv()

class DMMClientV3:
    def __init__(self):
        self.api_id = os.getenv("DMM_API_ID")
        self.affiliate_id = os.getenv("DMM_AFFILIATE_ID_SEESAA") or os.getenv("DMM_AFFILIATE_ID")
        self.base_url = "https://api.dmm.com/affiliate/v3/ItemList"

    def get_items(self, site="DMM.com", service=None, floor=None, hits=10, sort="rank", keyword=None, campaign=False):
        params = {
            "api_id": self.api_id,
            "affiliate_id": self.affiliate_id,
            "site": site,
            "hits": hits,
            "sort": sort,
            "output": "json"
        }
        if service: params["service"] = service
        if floor: params["floor"] = floor
        if keyword: params["keyword"] = keyword
        # Note: API doesn't have a direct 'campaign' filter, we use keywords or parse response

        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            if "result" in data and "items" in data["result"]:
                return data["result"]["items"]
        except Exception as e:
            print(f"DMM API Error: {e}")
        return []

    def get_dmm_tv_programs(self, hits=10, sort="rank"):
        """DMM TVの注目番組情報を取得し、画像がない場合は他フロアから補完する"""
        items = self.get_items(service="dmmtv", floor="dmmtv_video", hits=hits, sort=sort)
        
        refined_items = []
        for item in items:
            # DMM TV floor often lacks images. Try to find matched item in 'digital' or 'mono'
            if not item.get('imageURL'):
                search_res = self.get_items(site="DMM.com", keyword=item['title'], hits=1)
                if search_res and search_res[0].get('imageURL'):
                    item['imageURL'] = search_res[0]['imageURL']
                    # Use a more stable affiliate URL if possible
                    item['affiliateURL'] = search_res[0]['affiliateURL']
            
            # Additional metadata for justification
            item['ranking_reason'] = "公式人気ランキング上位" if sort == "rank" else "最新注目作品"
            refined_items.append(item)
            
        return refined_items

    def get_sale_items(self, category_keyword="DVD", hits=10):
        """キャンペーン・セール中の商材を取得"""
        return self.get_items(site="DMM.com", keyword=f"{category_keyword} セール", hits=hits, sort="rank")

    def get_books_ranking(self, hits=10, sort="rank"):
        return self.get_items(service="ebook", floor="comic", hits=hits, sort=sort)

    def get_games_ranking(self, hits=10, sort="rank"):
        return self.get_items(service="pcsoft", floor="digital_pcgame", hits=hits, sort=sort)

    def get_gravure_ranking(self, hits=10):
        """グラビアアイドル（美人度分析用）を検索"""
        # Using digital service and idol floor
        return self.get_items(service="digital", floor="idol", hits=hits, sort="rank")

    def get_shopping_ranking(self, floor="dvd", hits=10):
        """通販カテゴリのランキング"""
        return self.get_items(service="mono", floor=floor, hits=hits, sort="rank")

    def get_seasonal_items(self, keyword, hits=5):
        """季節モノのキーワード検索"""
        return self.get_items(service="mono", keyword=keyword, hits=hits, sort="rank")

if __name__ == "__main__":
    client = DMMClientV3()
    items = client.get_dmm_tv_programs(hits=1)
    if items:
        print(f"TV Program: {items[0]['title']}")
