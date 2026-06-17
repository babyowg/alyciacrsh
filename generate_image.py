import os
import sys
import json
import time
import mimetypes
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALEXYA_API_KEY")
BASE_URL = "https://alexya.ai/api/v1"
OUTPUT_DIR = Path("outputs")
ALY_REFS_DIR = Path("references/aly")
ALY_IMAGE = ALY_REFS_DIR / "mok-up Aly.png"

POLL_INTERVAL = 5
POLL_TIMEOUT = 600


def api_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def upload_reference(image_path: Path) -> str:
    """Upload une image locale et retourne son public_url."""
    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type:
        mime_type = "image/png"

    print(f"Upload de la référence : {image_path.name} ({mime_type})")

    # 1. Obtenir l'URL pré-signée
    presign_resp = requests.post(
        f"{BASE_URL}/uploads/presign",
        headers=api_headers(),
        json={
            "kind": "image_input",
            "content_type": mime_type,
            "file_name": image_path.name,
        },
    )
    presign_resp.raise_for_status()
    presign_data = presign_resp.json()

    upload_url = presign_data["upload_url"]
    public_url = presign_data["public_url"]

    # 2. PUT du fichier binaire vers l'URL pré-signée
    with open(image_path, "rb") as f:
        put_resp = requests.put(
            upload_url,
            data=f,
            headers={"Content-Type": mime_type},
        )

    if put_resp.status_code not in (200, 204):
        raise RuntimeError(f"Échec de l'upload ({put_resp.status_code}) : {put_resp.text}")

    print(f"Référence uploadée avec succès.")
    return public_url


def is_aly_prompt(prompt: str) -> bool:
    keywords = ["aly", "alycia", "alicia"]
    return any(k in prompt.lower() for k in keywords)


def create_image_job(prompt: str, aspect_ratio: str = "9:16") -> dict:
    if not API_KEY:
        raise ValueError("ALEXYA_API_KEY manquante dans .env")

    payload = {
        "prompt": prompt,
        "mode": "high_quality",
        "aspect_ratio": aspect_ratio,
    }

    if is_aly_prompt(prompt):
        if ALY_IMAGE.exists():
            public_url = upload_reference(ALY_IMAGE)
            payload["image_urls"] = [public_url]
        else:
            print(f"Avertissement : {ALY_IMAGE} introuvable, génération sans référence.")

    print(f"Création du job : {prompt!r} (aspect_ratio={aspect_ratio})")
    resp = requests.post(f"{BASE_URL}/image/generate", headers=api_headers(), json=payload)

    if resp.status_code != 202:
        raise RuntimeError(f"Erreur API ({resp.status_code}) : {resp.text}")

    data = resp.json()
    print(f"Job créé. Réponse :")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return data


def poll_job(poll_url: str) -> str:
    """Polle poll_url jusqu'à completion. Retourne output_url."""
    print(f"Polling toutes les {POLL_INTERVAL}s (max {POLL_TIMEOUT // 60} min)...")
    deadline = time.time() + POLL_TIMEOUT

    while time.time() < deadline:
        resp = requests.get(poll_url, headers=api_headers())
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        print(f"  Statut : {status}")

        if status == "completed":
            output_url = data.get("output_url")
            if not output_url:
                raise RuntimeError(f"Job terminé mais output_url absent : {data}")
            return output_url

        if status == "failed":
            raise RuntimeError(f"Job échoué : {data}")

        time.sleep(POLL_INTERVAL)

    raise TimeoutError(f"Timeout : job non terminé après {POLL_TIMEOUT // 60} minutes.")


def download_image(output_url: str, prompt: str) -> Path:
    """Télécharge l'image et la sauvegarde dans outputs/."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    slug = prompt[:40].replace(" ", "_").replace("/", "-")
    output_path = OUTPUT_DIR / f"{slug}.png"

    print(f"Téléchargement de l'image...")
    img_data = requests.get(output_url).content
    output_path.write_bytes(img_data)
    return output_path


def generate(prompt: str, aspect_ratio: str = "9:16") -> None:
    job = create_image_job(prompt, aspect_ratio)

    poll_url = job.get("poll_url")
    if not poll_url:
        raise RuntimeError(f"poll_url absent dans la réponse : {job}")

    output_url = poll_job(poll_url)
    output_path = download_image(output_url, prompt)
    print(f"\nImage sauvegardée : {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python generate_image.py \"votre prompt\" [aspect_ratio]")
        print("Aspect ratios : 1:1  16:9  9:16  4:3  3:4  5:4  4:5")
        sys.exit(1)

    prompt = sys.argv[1]
    aspect_ratio = sys.argv[2] if len(sys.argv) > 2 else "9:16"
    generate(prompt, aspect_ratio)
