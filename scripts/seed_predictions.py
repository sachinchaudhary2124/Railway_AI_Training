import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "admin"
PASSWORD = "password"
BASE_DIR = Path(__file__).resolve().parent.parent

def seed():
    # 1. Login
    print(f"Connecting to {BASE_URL}/login...")
    try:
        login_res = requests.post(f"{BASE_URL}/login", json={
            "username": USERNAME,
            "password": PASSWORD
        })
        login_res.raise_for_status()
        token = login_res.json()["access_token"]
        print("Logged in successfully. Token acquired.")
    except Exception as e:
        print(f"Failed to log in: {e}")
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Images to seed
    image_paths = [
        BASE_DIR / "dataset/splits/test/broken_rail/broken_rail_001.jpg",
        BASE_DIR / "dataset/splits/test/normal/normal_007.jpg"
    ]

    for img_path in image_paths:
        if not img_path.exists():
            print(f"Image not found: {img_path}")
            continue
        
        print(f"Uploading and predicting {img_path.name}...")
        try:
            with open(img_path, "rb") as f:
                files = {
                    "file": (img_path.name, f, "image/jpeg")
                }
                res = requests.post(f"{BASE_URL}/predict", headers=headers, files=files)
                res.raise_for_status()
                data = res.json()
                print(f"Successfully predicted {img_path.name}. Result: {data['predicted_class']} (confidence: {data['confidence']*100:.2f}%)")
        except Exception as e:
            print(f"Prediction failed for {img_path.name}: {e}")

if __name__ == "__main__":
    seed()
