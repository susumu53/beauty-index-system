import os
from dmm_client import DMMClient
from dotenv import load_dotenv
import requests

load_dotenv()

client = DMMClient()
actress_name = "河北彩伽"

def search(site, service, floor=None, keyword=None):
    params = {
        "api_id": client.api_id,
        "affiliate_id": client.affiliate_id,
        "site": site,
        "service": service,
        "hits": 10,
        "output": "json"
    }
    if floor: params["floor"] = floor
    if keyword: params["keyword"] = keyword
    
    response = requests.get(f"{client.base_url}/ItemList", params=params)
    return response.json()

print(f"--- Searching for {actress_name} ---")

# Try FANZA digital with keyword
res1 = search("FANZA", "digital", keyword=f"{actress_name} 写真集")
if "result" in res1 and "items" in res1["result"]:
    print("\nFANZA Digital (keyword search):")
    for i in res1["result"]["items"]:
        print(f"- {i['title']} (Floor: {i.get('floor_name')})")

# Try DMM.com ebook with keyword
res2 = search("DMM.com", "ebook", keyword=f"{actress_name} 写真集")
if "result" in res2 and "items" in res2["result"]:
    print("\nDMM.com Ebook (keyword search):")
    for i in res2["result"]["items"]:
        print(f"- {i['title']} (Floor: {i.get('floor_name')})")

# Try FANZA mono with keyword
res3 = search("FANZA", "mono", keyword=f"{actress_name} 写真集")
if "result" in res3 and "items" in res3["result"]:
    print("\nFANZA Mono (keyword search):")
    for i in res3["result"]["items"]:
        print(f"- {i['title']} (Category: {i.get('floor_name')})")
