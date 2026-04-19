import requests
import os
from dotenv import load_dotenv

load_dotenv()

wp_url = os.getenv("WP_URL")
wp_user = os.getenv("WP_USERNAME")
wp_pass = os.getenv("WP_APP_PASSWORD")

auth = (wp_user, wp_pass)
name_to_delete = "河北彩伽"
years = [2026, 2025, 2024] # Check multiple years just in case

# 1. Delete from ranking data
for year in years:
    delete_url = f"{wp_url}wp-json/beauty-index/v1/delete-entry"
    payload = {"name": name_to_delete, "year": year}
    try:
        resp = requests.post(delete_url, json=payload, auth=auth)
        if resp.status_code == 200:
            print(f"Ranking delete request sent for {name_to_delete} ({year}): {resp.json()}")
        else:
            print(f"Failed to delete {name_to_delete} from {year} ranking: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Error calling delete API: {e}")

# 2. Check and delete post if it exists
search_url = f"{wp_url}wp-json/wp/v2/posts?search={name_to_delete}"
try:
    resp = requests.get(search_url, auth=auth)
    posts = resp.json()
    if posts and isinstance(posts, list):
        for post in posts:
            post_id = post['id']
            post_title = post['title']['rendered']
            print(f"Found related post: {post_title} (ID: {post_id}). Deleting...")
            del_resp = requests.delete(f"{wp_url}wp-json/wp/v2/posts/{post_id}", auth=auth)
            if del_resp.status_code in [200, 201]:
                print(f"Post {post_id} deleted successfully.")
            else:
                print(f"Failed to delete post {post_id}: {del_resp.status_code}")
    else:
        print("No related posts found.")
except Exception as e:
    print(f"Error searching/deleting posts: {e}")
