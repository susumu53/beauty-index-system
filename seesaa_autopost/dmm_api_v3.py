import os
import requests
import re
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

class DMMClientV3:
    def __init__(self):
        self.api_id = os.getenv("DMM_API_ID")
        self.affiliate_id = os.getenv("DMM_AFFILIATE_ID_SEESAA") or os.getenv("DMM_AFFILIATE_ID")
        self.base_url = "https://api.dmm.com/affiliate/v3/ItemList"

    def _clean_title(self, title):
        """タイトルから検索の邪魔になるノイズ（シーズン情報、括弧など）を除去"""
        title = re.sub(r'[\(（].*?[\)）]', '', title) # 括弧内削除
        title = re.sub(r'[「」『』【】]', ' ', title) # 括弧記号をスペースに
        title = re.sub(r'第.*?期|シーズン\s*\d+|Season\s*\d+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+', ' ', title).strip()
        return title

    def _get_youtube_video_id(self, query):
        """YouTubeを検索して公式PV等の動画IDを取得"""
        try:
            search_query = f"{query} 公式 PV 予告"
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            r = requests.get(url, headers=headers, timeout=10)
            
            # Look for videoId
            match = re.search(r'\"videoRenderer\":\{\"videoId\":\"(.*?)\"', r.text)
            if match: return match.group(1)
            
            match = re.search(r'watch\?v=([a-zA-Z0-9_-]{11})', r.text)
            if match: return match.group(1)
        except Exception as e:
            print(f"YouTube search failed for {query}: {e}")
        return None

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
        """DMM TVの注目番組情報を取得し、画像がない場合はYouTube動画または他フロアから補完する"""
        items = self.get_items(service="dmmtv", floor="dmmtv_video", hits=hits, sort=sort)
        
        refined_items = []
        for item in items:
            cleaned_title = self._clean_title(item['title'])
            
            # 1. Try DMM Floor Search Fallback if image is missing
            if not item.get('imageURL'):
                search_res = self.get_items(site="DMM.com", keyword=cleaned_title, hits=1)
                if search_res and search_res[0].get('imageURL'):
                    item['imageURL'] = search_res[0]['imageURL']
                    item['affiliateURL'] = search_res[0]['affiliateURL']
            
            # 2. Try YouTube Video Fallback if image is still missing or as an enhancement
            if not item.get('imageURL'):
                video_id = self._get_youtube_video_id(cleaned_title)
                if video_id:
                    item['youtube_video_id'] = video_id
            
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
