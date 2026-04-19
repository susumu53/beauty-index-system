import os
from dmm_client import DMMClient
from dotenv import load_dotenv

load_dotenv()

client = DMMClient()
print(f"API ID length: {len(client.api_id) if client.api_id else 0}")
print(f"Affiliate ID length: {len(client.affiliate_id) if client.affiliate_id else 0}")
print(f"Affiliate ID shape: {client.affiliate_id[:3] + '...' if client.affiliate_id else 'None'}")
print(f"Full Affiliate ID config: {client.affiliate_id}")

# Fetch a sample
works = client.get_actress_works(1044864, hits=1, site="DMM.com", service="ebook", keyword="写真集")
if works:
    print(f"Sample URL: {works[0].get('affiliateURL')}")
