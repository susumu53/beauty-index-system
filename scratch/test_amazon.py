import os
from amazon_paapi import AmazonApi

# キーは環境変数から取得
ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
ASSOCIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "blogseesaa090-22")
COUNTRY = "JP"

try:
    print("Initializating Amazon PA-API client...")
    amazon = AmazonApi(ACCESS_KEY, SECRET_KEY, ASSOCIATE_TAG, COUNTRY)
    
    print("Searching for items...")
    search_result = amazon.search_items(keywords="広瀬すず 写真集", search_index="Books")
    
    print(f"Found {len(search_result.items)} items.")
    for item in search_result.items:
        print(f"Title: {item.item_info.title.display_value}")
        if item.images and item.images.primary and item.images.primary.large:
            print(f"Image: {item.images.primary.large.url}")
        print(f"URL: {item.detail_page_url}")
        print("-" * 20)
        
except Exception as e:
    print(f"Error occurred: {type(e).__name__}")
    print(e)
