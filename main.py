from dmm_client import DMMClient
from beauty_engine import BeautyEngine
import json

def main():
    client = DMMClient()
    engine = BeautyEngine()

    print("--- 3D Analysis (Mikami Yua) ---")
    actresses = client.search_actress(name="三上悠亜")
    if actresses:
        a = actresses[0]
        print(f"Target: {a['name']}")
        
        # プロポーション数値化
        proportion = None
        try:
            b = int(a.get('bust', 0))
            w = int(a.get('waist', 0))
            h = int(a.get('hip', 0))
            height = int(a.get('height', 0))
            if w > 0 and h > 0:
                whr = w / h
                proportion = {"whr": whr, "height": height}
                print(f"Proportion: B{b} W{w} H{h} (WHR: {round(whr, 3)})")
        except:
            pass

        # 作品画像解析
        works = client.get_actress_works(a['id'], hits=5)
        face_scores = None
        for work in works:
            img_url = work.get('imageURL', {}).get('large')
            if img_url:
                print(f"Analyzing Image: {img_url}")
                img = engine.download_image(img_url)
                face_scores = engine.analyze_3d_face(img)
                if face_scores:
                    print(f"Face Analysis Success: {face_scores}")
                    break
        
        if face_scores:
            bi = engine.calculate_beauty_index(face_scores, proportion)
            print(f"==> Beauty Index (3D): {bi}\n")

    print("--- 2D Analysis (Frieren) ---")
    # 「葬送のフリーレン」で検索
    anime_works = client.get_anime_works(keyword="葬送のフリーレン", hits=1)
    if anime_works:
        item = anime_works[0]
        print(f"Target: {item['title']}")
        img_url = item.get('imageURL', {}).get('large')
        if img_url:
            print(f"Analyzing Image: {img_url}")
            img = engine.download_image(img_url)
            face_scores = engine.analyze_2d_face(img)
            if face_scores:
                print(f"Face Analysis Success: {face_scores}")
                bi = engine.calculate_beauty_index(face_scores)
                print(f"==> Beauty Index (2D): {bi}\n")
            else:
                print("Face not detected in the anime cover.")

if __name__ == "__main__":
    main()
