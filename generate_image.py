import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALEXYA_API_KEY")
BASE_URL = "https://alexya.ai/api/v1"
OUTPUT_DIR = Path("outputs")


def generate_image(prompt: str) -> Path:
    if not API_KEY:
        raise ValueError("ALEXYA_API_KEY manquante dans .env")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": prompt,
    }

    print(f"Génération en cours pour : {prompt!r}")
    response = requests.post(f"{BASE_URL}/image/generate", headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()

    # Adapter selon la réponse réelle de l'API
    image_url = data.get("url") or data.get("image_url") or data["data"][0]["url"]

    OUTPUT_DIR.mkdir(exist_ok=True)
    slug = prompt[:40].replace(" ", "_").replace("/", "-")
    output_path = OUTPUT_DIR / f"{slug}.png"

    image_data = requests.get(image_url).content
    output_path.write_bytes(image_data)

    print(f"Image sauvegardée : {output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python generate_image.py \"votre prompt ici\"")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])
    generate_image(prompt)
