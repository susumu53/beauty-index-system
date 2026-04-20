import sys
import os
import cv2
import mediapipe as mp
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
import japanize_matplotlib

# Parent directory import for potentially reusing existing logic or just re-implementing
# For a clean topology, we re-implement or wrap carefully.

class BeautyAnalyzer:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )

    def download_image(self, url):
        try:
            response = requests.get(url, timeout=10)
            img = Image.open(BytesIO(response.content))
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"Image download failed: {e}")
            return None

    def analyze(self, image):
        if image is None: return None
        results = self.face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if not results.multi_face_landmarks:
            return None

        landmarks = results.multi_face_landmarks[0].landmark
        h, w, _ = image.shape

        # Symmetry calculation
        left_eye = np.array([landmarks[33].x, landmarks[33].y])
        right_eye = np.array([landmarks[263].x, landmarks[263].y])
        y_diff = abs(left_eye[1] - right_eye[1])
        symmetry_score = max(0, min(100, 100 - (y_diff * 1000)))

        # Neoteny (Face/Eye ratio)
        eye_indices = [33, 160, 158, 133, 153, 144]
        eye_points = np.array([[landmarks[i].x * w, landmarks[i].y * h] for i in eye_indices], dtype=np.int32)
        eye_area = cv2.contourArea(eye_points)
        
        x_coords = [l.x * w for l in landmarks]
        y_coords = [l.y * h for l in landmarks]
        face_area = (max(x_coords) - min(x_coords)) * (max(y_coords) - min(y_coords))
        
        neoteny_score = min(100, (eye_area / face_area) * 8000)

        # Total Beauty Index (Simplified for automation)
        total_score = (symmetry_score * 0.4) + (neoteny_score * 0.3) + (85 * 0.3) # 85 is base for other factors
        
        return {
            "symmetry": round(symmetry_score, 2),
            "neoteny": round(neoteny_score, 2),
            "total": round(total_score, 2),
            "proportion": 80 + np.random.uniform(-5, 5), # Placeholder for derived data
            "dimorphism": 85 + np.random.uniform(-5, 5),
            "social": 75 + np.random.uniform(-5, 10)
        }

    def generate_radar_chart(self, scores, output_path="beauty_radar.png"):
        labels = ["左右対称性", "若さ指数", "プロポーション", "性的二型", "社会的評価"]
        num_vars = len(labels)
        
        stats = [
            scores['symmetry'],
            scores['neoteny'],
            scores['proportion'],
            scores['dimorphism'],
            scores['social']
        ]
        
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        stats += stats[:1]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
        ax.fill(angles, stats, color='#ff1493', alpha=0.3)
        ax.plot(angles, stats, color='#ff1493', linewidth=2)
        
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_thetagrids(np.degrees(angles[:-1]), labels)
        ax.set_ylim(0, 100)
        
        plt.title(f"Beauty Index Analysis Score: {scores['total']}", size=15, color='#ff1493', y=1.1)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path

if __name__ == "__main__":
    analyzer = BeautyAnalyzer()
    # Test with a placeholder or local file if needed
    print("Analyzer Initialized.")
