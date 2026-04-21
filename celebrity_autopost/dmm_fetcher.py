import os
import re
import requests
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

DMM_API_BASE = "https://api.dmm.com/affiliate/v3/ItemList"

# 一般コンテンツのみのフロア定義（アダルト完全除外）
SAFE_SEARCH_CONFIGS = [
    {"site": "DMM.com", "service": "mono", "floor": "dvd"},          # DVD/Blu-ray 通販
    {"site": "DMM.com", "service": "mono", "floor": "book"},         # 書籍・写真集
    {"site": "DMM.com", "service": "digital", "floor": "photo"},     # デジタル写真集
    {"site": "DMM.com", "service": "dmmtv", "floor": "dmmtv_video"}, # DMM TV
]

class DMMCelebFetcher:
    def __init__(self):
        self.api_id = os.getenv("DMM_API_ID")
        self.affiliate_id = os.getenv("DMM_AFFILIATE_ID_CELEB") or os.getenv("DMM_AFFILIATE_ID_SEESAA") or os.getenv("DMM_AFFILIATE_ID")
        
        if not self.api_id:
            raise ValueError("DMM_API_ID が設定されていません")

    def _call_api(self, params):
        """DMM API を呼び出す共通メソッド"""
        base_params = {
            "api_id": self.api_id,
            "affiliate_id": self.affiliate_id,
            "hits": 5,
            "sort": "rank",
            "output": "json",
        }
        base_params.update(params)
        
        try:
            r = requests.get(DMM_API_BASE, params=base_params, timeout=10)
            data = r.json()
            if "result" in data and "items" in data["result"]:
                return data["result"]["items"]
        except Exception as e:
            print(f"  DMM API エラー: {e}")
        return []

    def _is_adult_content(self, item):
        """アダルトコンテンツか判定（念のため二重チェック）"""
        title = item.get("title", "").lower()
        url = item.get("affiliateURL", "").lower()
        
        adult_keywords = ["fanza", "av女優", "エロ", "成人", "18禁", "R18", "sexually"]
        for kw in adult_keywords:
            if kw.lower() in title or kw.lower() in url:
                return True
        
        # FANZA ドメインが含まれていたらアダルトとみなす
        if "dmm.co.jp" in url and "fanza" in url:
            return True
        
        return False

    def search_celebrity_products(self, celebrity_name, max_items=5):
        """
        芸能人名でDMM一般コンテンツを検索する。
        複数フロアを試して商品を収集する。
        """
        results = []
        seen_ids = set()
        
        print(f"🔍 DMM検索: {celebrity_name}")
        
        for config in SAFE_SEARCH_CONFIGS:
            if len(results) >= max_items:
                break
            
            params = {
                "keyword": celebrity_name,
                "hits": 5,
            }
            params.update(config)
            
            items = self._call_api(params)
            
            for item in items:
                content_id = item.get("content_id", "")
                
                # 重複・アダルトをスキップ
                if content_id in seen_ids:
                    continue
                if self._is_adult_content(item):
                    continue
                
                seen_ids.add(content_id)
                results.append(self._format_item(item))
                
                if len(results) >= max_items:
                    break
            
            if items:
                print(f"  ✅ {config['floor']}: {len(items)}件取得")
        
        if not results:
            print(f"  ⚠️ '{celebrity_name}' の一般商品が見つかりませんでした")
        
        return results

    def _format_item(self, item):
        """商品データを整形する"""
        images = item.get("imageURL", {})
        prices = item.get("prices", {})
        
        # 価格取得
        price = ""
        if prices:
            price_val = prices.get("price", prices.get("list", ""))
            if price_val:
                price = f"¥{price_val}"
        
        # サムネイル優先順位: large > small > なし
        image_url = images.get("large", images.get("small", ""))
        
        return {
            "title": item.get("title", ""),
            "affiliate_url": item.get("affiliateURL", ""),
            "image_url": image_url,
            "price": price,
            "review_average": item.get("review", {}).get("average", ""),
            "review_count": item.get("review", {}).get("count", ""),
            "maker": item.get("iteminfo", {}).get("maker", [{}])[0].get("name", "") if item.get("iteminfo", {}).get("maker") else "",
            "date": item.get("date", ""),
        }

    def get_youtube_fallback(self, celebrity_name):
        """DMM商品がない場合のYouTube動画IDフォールバック"""
        try:
            query = f"{celebrity_name} 公式 インタビュー"
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            r = requests.get(url, headers=headers, timeout=10)
            
            match = re.search(r'"videoRenderer"\:\{"videoId"\:"(.*?)"', r.text)
            if match:
                return match.group(1)
            match = re.search(r'watch\?v=([a-zA-Z0-9_-]{11})', r.text)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"⚠️ YouTube検索エラー: {e}")
        return None


if __name__ == "__main__":
    fetcher = DMMCelebFetcher()
    products = fetcher.search_celebrity_products("石原さとみ")
    for p in products:
        print(f"  [{p['price']}] {p['title']}")
