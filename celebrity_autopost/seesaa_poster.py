import xmlrpc.client
import os
from dotenv import load_dotenv

load_dotenv()

class SeesaaCelebPoster:
    """
    芸能人ブログ用 Seesaa XML-RPC 投稿クライアント
    ブログ: https://namasoku.seesaa.net/
    """
    
    ENDPOINT = "https://blog.seesaa.jp/rpc"
    
    def __init__(self):
        self.email = os.getenv("SEESAA_CELEB_EMAIL", "garoa53@yahoo.co.jp")
        self.password = os.getenv("SEESAA_CELEB_PASSWORD", "kaimono53")
        self.client = xmlrpc.client.ServerProxy(self.ENDPOINT)
        self._blog_id = None

    def get_blog_id(self):
        """アカウントのブログIDを取得する"""
        if self._blog_id:
            return self._blog_id
        
        try:
            blogs = self.client.blogger.getUsersBlogs("", self.email, self.password)
            if blogs:
                # namasoku.seesaa.net のブログを探す
                for blog in blogs:
                    url = blog.get("url", "")
                    if "namasoku" in url:
                        self._blog_id = blog["blogid"]
                        print(f"✅ ブログ発見: {url} (ID: {self._blog_id})")
                        return self._blog_id
                
                # 見つからない場合は最初のブログを使用
                self._blog_id = blogs[0]["blogid"]
                print(f"ℹ️ 最初のブログを使用: ID={self._blog_id}")
                return self._blog_id
        
        except Exception as e:
            print(f"❌ ブログID取得エラー: {e}")
        
        return None

    def post_article(self, title, html_content, categories=None, tags=None):
        """
        記事を投稿する
        
        Args:
            title (str): 記事タイトル
            html_content (str): HTML形式の本文
            categories (list): カテゴリ名リスト
            tags (list): タグリスト
        
        Returns:
            str|None: 投稿IDまたはNone
        """
        blog_id = self.get_blog_id()
        if not blog_id:
            print("❌ ブログIDが取得できないため投稿をスキップします")
            return None
        
        post_data = {
            "title": title,
            "description": html_content,
        }
        
        if categories:
            post_data["categories"] = categories
        
        if tags:
            post_data["mt_keywords"] = ",".join(tags) if isinstance(tags, list) else tags
        
        try:
            post_id = self.client.metaWeblog.newPost(
                blog_id, self.email, self.password, post_data, True  # True = 即時公開
            )
            print(f"✅ 記事投稿成功！ Post ID: {post_id}")
            return str(post_id)
        
        except Exception as e:
            print(f"❌ 記事投稿エラー: {e}")
            return None


if __name__ == "__main__":
    poster = SeesaaCelebPoster()
    bid = poster.get_blog_id()
    print(f"Blog ID: {bid}")
