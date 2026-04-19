import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

url = "https://al.dmm.com/?lurl=https%3A%2F%2Fbook.dmm.com%2Fproduct%2F4259463%2Fb600dsgk34394%2F&af_id=namasoku-990&ch=api"
r = requests.get(url, headers=headers, allow_redirects=False)
print("Status 1:", r.status_code)
if r.status_code in (301, 302):
    print("Location 1:", r.headers.get('Location'))

url2 = "https://al.fanza.co.jp/?lurl=https%3A%2F%2Fvideo.dmm.co.jp%2Fav%2Fcontent%2F%3Fid%3Dsivr00380&af_id=namasoku-990&ch=api"
r2 = requests.get(url2, headers=headers, allow_redirects=False)
print("Status 2:", r2.status_code)
if r2.status_code in (301, 302):
    print("Location 2:", r2.headers.get('Location'))

