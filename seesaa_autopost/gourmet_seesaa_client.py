import xmlrpc.client
import os
import mimetypes
from dotenv import load_dotenv

load_dotenv()

class GourmetSeesaaClient:
    """料理・グルメブログ (syoshinsya2525.seesaa.net / BlogID: 4681940) 専用投稿クライアント"""
    def __init__(self, email=None, password=None, target_blog_id="4681940"):
        self.endpoint = "https://blog.seesaa.jp/rpc"
        self.email = email or os.getenv("SEESAA_EMAIL")
        self.password = password or os.getenv("SEESAA_PASSWORD")
        self.client = xmlrpc.client.ServerProxy(self.endpoint)
        self.target_blog_id = target_blog_id
        self._blog_id = None

    def get_blog_id(self):
        """syoshinsya2525.seesaa.net (ID: 4681940) を特定して返す"""
        if self._blog_id:
            return self._blog_id
        
        try:
            blogs = self.client.blogger.getUsersBlogs("", self.email, self.password)
            if blogs:
                for blog in blogs:
                    if str(blog.get("blogid")) == str(self.target_blog_id) or "syoshinsya2525" in blog.get("url", ""):
                        self._blog_id = blog['blogid']
                        print(f"Targeting Gourmet Blog: {blog['url']} (ID: {self._blog_id})")
                        return self._blog_id
                
                self._blog_id = self.target_blog_id
                return self._blog_id
        except Exception as e:
            print(f"Failed to get Blog ID: {e}")
            self._blog_id = self.target_blog_id
        return self._blog_id

    def upload_media(self, file_path):
        """画像をアップロードしてURLを返す"""
        blog_id = self.get_blog_id()
        if not blog_id:
            return None

        filename = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "image/jpeg"

        with open(file_path, "rb") as f:
            bits = xmlrpc.client.Binary(f.read())

        media_data = {
            "name": filename,
            "type": mime_type,
            "bits": bits,
            "overwrite": True
        }

        try:
            result = self.client.metaWeblog.newMediaObject(blog_id, self.email, self.password, media_data)
            return result.get("url")
        except Exception as e:
            print(f"Failed to upload media: {e}")
            return None

    # SeesaaブログのカテゴリーIDマッピング
    CATEGORY_MAP = {
        "バズレシピ": "28215583",
        "グルメ漫画": "28215584",
        "料理番組・アニメ": "28215585",
        "名店の味・再現": "28215586",
        "名店の味": "28215586",
        "料理ノウハウ": "28215587",
        "厳選お取り寄せ": "28215588",
    }

    def post_article(self, title, content, categories=None, tags=None):
        """記事を投稿し、カテゴリーIDを確実に紐付ける"""
        blog_id = self.get_blog_id()
        if not blog_id:
            print("Blog ID not found.")
            return None

        post_data = {
            "title": title,
            "description": content,
        }
        
        if categories:
            post_data["categories"] = categories if isinstance(categories, list) else [categories]
        if tags:
            post_data["mt_keywords"] = ",".join(tags) if isinstance(tags, list) else tags

        try:
            post_id = self.client.metaWeblog.newPost(blog_id, self.email, self.password, post_data, True)
            print(f"Successfully posted article: {post_id}")
            
            # カテゴリIDの紐付け (MovableType API)
            if categories:
                cat_names = categories if isinstance(categories, list) else [categories]
                cat_list = []
                for idx, cname in enumerate(cat_names):
                    cid = self.CATEGORY_MAP.get(cname)
                    if cid:
                        cat_list.append({'categoryId': cid, 'isPrimary': (idx == 0)})
                
                if cat_list:
                    try:
                        self.client.mt.setPostCategories(post_id, self.email, self.password, cat_list)
                        print(f"Assigned category IDs: {[c['categoryId'] for c in cat_list]}")
                    except Exception as ce:
                        print(f"Warning: Failed to assign category IDs: {ce}")

            return post_id
        except Exception as e:
            print(f"Failed to post article: {e}")
            return None

if __name__ == "__main__":
    client = GourmetSeesaaClient()
    bid = client.get_blog_id()
    print(f"Gourmet Blog ID verified: {bid}")
