import requests
import os
from dotenv import load_dotenv

load_dotenv('../.env')

wp_url = os.getenv("WP_URL")
wp_user = os.getenv("WP_USERNAME")
wp_pass = os.getenv("WP_APP_PASSWORD")

endpoint = f"{wp_url.rstrip('/')}/wp-json/beauty-index/v1/update-score"

payload = {
    "name": "天海春香",
    "category": "2D",
    "score": 95.5,
    "affiliate_url": "https://al.dmm.com/dummy",
    "article_url": "http://ss660231.stars.ne.jp/2026/04/19/test-article/",
    "image_url": "https://picsum.photos/200", 
    "year": 2026
}

resp = requests.post(endpoint, json=payload, auth=(wp_user, wp_pass))
print("Status Code:", resp.status_code)
print("Response:", resp.json() if resp.text else resp.text)
