import requests
import re

WIKI_API_URL = "https://ja.wikipedia.org/api/rest_v1/page/summary/{name}"
WIKI_SEARCH_URL = "https://ja.wikipedia.org/w/api.php"

def get_wiki_profile(celebrity_name):
    """
    Wikipedia から芸能人のプロフィールと経歴を取得する。
    返却: dict { summary, thumbnail_url, wiki_url, birth_date, occupation }
    """
    headers = {"User-Agent": "celebrity-autopost-bot/1.0 (garoa53@yahoo.co.jp)"}
    
    # まず直接ページ名でアクセス
    result = _fetch_wiki_summary(celebrity_name, headers)
    
    # 見つからない場合は検索APIで候補を探す
    if not result:
        result = _search_wiki(celebrity_name, headers)
    
    return result

def _fetch_wiki_summary(name, headers):
    """Wikipedia REST API でサマリーを取得"""
    try:
        url = WIKI_API_URL.format(name=requests.utils.quote(name))
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code != 200:
            return None
        
        data = r.json()
        
        # 曖昧さ回避ページはスキップ
        if data.get("type") == "disambiguation":
            return None
        
        extract = data.get("extract", "")
        if not extract or len(extract) < 50:
            return None
        
        # 生年月日を抽出
        birth_date = _extract_birth_date(extract)
        
        # 職業を抽出
        occupation = _extract_occupation(extract)
        
        # 本文を適切な長さに整理（最大600文字）
        summary_text = _clean_extract(extract, max_chars=600)
        
        # サムネイル (Wikipedia 顔写真)
        thumbnail = data.get("thumbnail", {})
        thumbnail_url = thumbnail.get("source", "") if thumbnail else ""
        
        wiki_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
        
        print(f"✅ Wikipedia 取得成功: {name}")
        return {
            "name": name,
            "summary": summary_text,
            "full_extract": extract,
            "thumbnail_url": thumbnail_url,
            "wiki_url": wiki_url,
            "birth_date": birth_date,
            "occupation": occupation,
        }
    
    except Exception as e:
        print(f"❌ Wikipedia 取得エラー ({name}): {e}")
        return None

def _search_wiki(name, headers):
    """Wikipedia 検索APIで芸能人ページを探す"""
    try:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{name} 芸能人 俳優 女優 歌手",
            "srlimit": 3,
            "format": "json",
            "utf8": 1,
        }
        r = requests.get(WIKI_SEARCH_URL, params=params, headers=headers, timeout=10)
        data = r.json()
        
        results = data.get("query", {}).get("search", [])
        if not results:
            return None
        
        # 最初の検索結果でサマリー取得を試みる
        page_title = results[0]["title"]
        return _fetch_wiki_summary(page_title, headers)
    
    except Exception as e:
        print(f"❌ Wikipedia 検索エラー ({name}): {e}")
        return None

def _extract_birth_date(text):
    """テキストから生年月日を抽出"""
    patterns = [
        r'(\d{4})年(\d{1,2})月(\d{1,2})日生まれ',
        r'(\d{4})年(\d{1,2})月(\d{1,2})日、',
        r'生年月日.*?(\d{4})年(\d{1,2})月(\d{1,2})日',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return f"{m.group(1)}年{m.group(2)}月{m.group(3)}日"
    return ""

def _extract_occupation(text):
    """テキストから職業を抽出"""
    occupations = [
        "俳優", "女優", "歌手", "アイドル", "タレント", "モデル", "声優",
        "お笑い芸人", "コメディアン", "ミュージシャン", "アーティスト",
        "司会者", "リポーター", "グラビアアイドル", "YouTuber",
    ]
    found = []
    for occ in occupations:
        if occ in text[:200]:  # 冒頭200文字から職業を探す
            found.append(occ)
    return "・".join(found[:3]) if found else "芸能人"

def _clean_extract(text, max_chars=600):
    """Wikipedia本文テキストを整理する"""
    # 注釈記号を除去
    text = re.sub(r'\[注.*?\]', '', text)
    text = re.sub(r'\[出典.*?\]', '', text)
    text = re.sub(r'\[\d+\]', '', text)
    
    # 余分な空白を整理
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    if len(text) > max_chars:
        # 文の途中で切れないようにする
        truncated = text[:max_chars]
        last_period = max(truncated.rfind('。'), truncated.rfind('．'))
        if last_period > max_chars * 0.7:
            truncated = truncated[:last_period + 1]
        text = truncated + "…"
    
    return text

if __name__ == "__main__":
    profile = get_wiki_profile("石原さとみ")
    if profile:
        print(f"職業: {profile['occupation']}")
        print(f"生年月日: {profile['birth_date']}")
        print(f"概要: {profile['summary'][:100]}...")
        print(f"写真URL: {profile['thumbnail_url']}")
