import os
import xmlrpc.client
from dotenv import load_dotenv

load_dotenv()

class FC2Client:
    def __init__(self):
        self.username = os.getenv("FC2_USERNAME")
        self.password = os.getenv("FC2_PASSWORD")
        # デフォルトはfc2ですが、特定の場合はブログIDを指定します
        self.blog_id = os.getenv("FC2_BLOG_ID", "fc2")
        self.endpoint = "http://blog.fc2.com/xmlrpc.php"
        
        if not self.username or not self.password:
            raise ValueError("FC2_USERNAME, FC2_PASSWORD環境変数が設定されていません。")
            
        self.server = xmlrpc.client.ServerProxy(self.endpoint)

    def post_article(self, title, content, categories=None, publish=True):
        """
        FC2ブログに記事を投稿する
        
        :param title: 記事のタイトル
        :param content: HTML形式の記事本文
        :param categories: リスト形式のカテゴリ名の配列 (例: ["巨乳", "まとめ"])
        :param publish: Trueで公開、Falseで下書き
        :return: 投稿された記事ID
        """
        post_data = {
            'title': title,
            'description': content,
        }
        
        if categories:
            post_data['categories'] = categories
        
        try:
            print(f"FC2ブログへ投稿中... [{title}]")
            # metaWeblog.newPost(blogid, username, password, struct, publish)
            post_id = self.server.metaWeblog.newPost(
                self.blog_id, 
                self.username, 
                self.password, 
                post_data, 
                publish
            )
            print(f"投稿成功！ 記事ID: {post_id}")
            return post_id
        except Exception as e:
            print(f"投稿エラー: {e}")
            return None

if __name__ == "__main__":
    # テスト動作用
    try:
        client = FC2Client()
        # client.post_article("自動投稿テスト", "<p>これはXML-RPCを経由したテスト投稿です。</p>", publish=False)
        print("初期化成功。")
    except Exception as e:
        print(f"エラー: {e}")
