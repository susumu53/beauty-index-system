import xmlrpc.client
import os
import base64
import mimetypes
from dotenv import load_dotenv

load_dotenv()

class SeesaaClient:
    def __init__(self, email=None, password=None):
        self.endpoint = "https://blog.seesaa.jp/rpc"
        self.email = email or os.getenv("SEESAA_EMAIL")
        self.password = password or os.getenv("SEESAA_PASSWORD")
        self.client = xmlrpc.client.ServerProxy(self.endpoint)
        self._blog_id = None

    def get_blog_id(self):
        """アカウントに関連付けられた最初のブログIDを取得する"""
        if self._blog_id:
            return self._blog_id
        
        try:
            blogs = self.client.blogger.getUsersBlogs("", self.email, self.password)
            if blogs:
                self._blog_id = blogs[0]['blogid']
                return self._blog_id
        except Exception as e:
            print(f"Failed to get Blog ID: {e}")
        return None

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

    def post_article(self, title, content, categories=None, tags=None):
        """記事を投稿する"""
        blog_id = self.get_blog_id()
        if not blog_id:
            return None

        post_data = {
            "title": title,
            "description": content,
        }
        
        if categories:
            post_data["categories"] = categories
        if tags:
            post_data["mt_keywords"] = ",".join(tags) if isinstance(tags, list) else tags

        try:
            # publish=True
            post_id = self.client.metaWeblog.newPost(blog_id, self.email, self.password, post_data, True)
            print(f"Successfully posted article: {post_id}")
            return post_id
        except Exception as e:
            print(f"Failed to post article: {e}")
            return None

if __name__ == "__main__":
    # Test (Dry run requires credentials in .env)
    client = SeesaaClient()
    bid = client.get_blog_id()
    print(f"Blog ID: {bid}")
