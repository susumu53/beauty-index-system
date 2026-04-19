import requests

url = "https://al.dmm.com/?lurl=https%3A%2F%2Fbook.dmm.com%2Fproduct%2F4259463%2Fb600dsgk34394%2F&af_id=namasoku-990&ch=api"
r = requests.get(url, allow_redirects=False)
print("Status:", r.status_code)
if r.status_code in (301, 302):
    print("Location:", r.headers.get('Location'))
else:
    print("Content snippet:", r.text[:200])

url2 = "https://al.fanza.co.jp/?lurl=https%3A%2F%2Fvideo.dmm.co.jp%2Fav%2Fcontent%2F%3Fid%3Dsivr00380&af_id=namasoku-990&ch=api"
r2 = requests.get(url2, allow_redirects=False)
print("Status 2:", r2.status_code)
if r2.status_code in (301, 302):
    print("Location 2:", r2.headers.get('Location'))
else:
    print("Content snippet 2:", r2.text[:200])
