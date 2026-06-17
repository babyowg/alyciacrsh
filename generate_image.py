import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALEXYA_API_KEY")
BASE_URL = "https://alexya.ai/api/v1"
OUTPUT_DIR = Path("outputs")


def create_image_job(prompt: str, aspect_ratio: str = "9:16") -> dict:
    if not API_KEY:
        raise ValueError("ALEXYA_API_KEY manquante dans .env")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": prompt,
        "mode": "high_quality",
        "aspect_ratio": aspect_ratio,
    }

    print(f"Création du job pour : {prompt!r} (aspect_ratio={aspect_ratio})")
    response = requests.post(f"{BASE_URL}/image/generate", headers=headers, json=payload)

    print(f"Statut HTTP : {response.status_code}")
    data = response.json()
    print("Réponse JSON complète :")
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python generate_image.py \"votre prompt\" [aspect_ratio]")
        print("Aspect ratios disponibles : 1:1  16:9  9:16  4:3  3:4  5:4  4:5")
        sys.exit(1)

    prompt = sys.argv[1]
    aspect_ratio = sys.argv[2] if len(sys.argv) > 2 else "9:16"
    create_image_job(prompt, aspect_ratio)
