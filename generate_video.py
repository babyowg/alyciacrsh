import os
import sys
import json
import time
import mimetypes
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALEXYA_VIDEO_API_KEY")
BASE_URL = "https://alexya.ai/api/v1"
OUTPUT_DIR = Path("outputs/videos")

POLL_INTERVAL = 5
POLL_TIMEOUT = 600
VALID_DURATIONS = (5, 10)


def api_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def upload_start_frame(image_path: Path) -> str:
    """Upload une image locale comme start frame et retourne son public_url."""
    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type:
        mime_type = "image/jpeg"

    print(f"Upload du start frame : {image_path.name} ({mime_type})")

    presign_resp = requests.post(
        f"{BASE_URL}/uploads/presign",
        headers=api_headers(),
        json={
            "kind": "video_start_frame",
            "content_type": mime_type,
            "file_name": image_path.name,
        },
    )
    presign_resp.raise_for_status()
    presign_data = presign_resp.json()

    upload_url = presign_data["upload_url"]
    public_url = presign_data["public_url"]

    with open(image_path, "rb") as f:
        put_resp = requests.put(
            upload_url,
            data=f,
            headers={"Content-Type": mime_type},
        )

    if put_resp.status_code not in (200, 204):
        raise RuntimeError(f"Échec de l'upload ({put_resp.status_code}) : {put_resp.text}")

    print("Start frame uploadé avec succès.")
    return public_url


def create_video_job(image_path: Path, prompt: str, duration: int) -> dict:
    if not API_KEY:
        raise ValueError("ALEXYA_VIDEO_API_KEY manquante dans .env")

    if duration not in VALID_DURATIONS:
        raise ValueError(f"Durée invalide : {duration}. Valeurs acceptées : {VALID_DURATIONS}")

    start_frame_url = upload_start_frame(image_path)

    payload = {
        "prompt": prompt,
        "mode": "best_quality",
        "duration": duration,
        "start_frame_url": start_frame_url,
    }

    print(f"Création du job vidéo : {prompt!r} ({duration}s)")
    resp = requests.post(f"{BASE_URL}/video/generate", headers=api_headers(), json=payload)

    if resp.status_code != 202:
        raise RuntimeError(f"Erreur API ({resp.status_code}) : {resp.text}")

    data = resp.json()
    print("Job créé. Réponse :")
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


def download_video(output_url: str, prompt: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = prompt[:40].replace(" ", "_").replace("/", "-")
    output_path = OUTPUT_DIR / f"{slug}.mp4"

    print("Téléchargement de la vidéo...")
    with requests.get(output_url, stream=True) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return output_path


def generate(image_path: Path, prompt: str, duration: int) -> None:
    job = create_video_job(image_path, prompt, duration)

    poll_url = job.get("poll_url")
    if not poll_url:
        raise RuntimeError(f"poll_url absent dans la réponse : {job}")

    output_url = poll_job(poll_url)
    output_path = download_video(output_url, prompt)
    print(f"\nVidéo sauvegardée : {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage : python3 generate_video.py <image> \"prompt\" [duration]")
        print("  image    : chemin vers l'image de départ (.jpg, .png, .webp)")
        print("  duration : 5 ou 10 secondes (défaut : 5)")
        print()
        print("Exemple :")
        print('  python3 generate_video.py image.jpg "Aly smiles softly and looks at the camera" 5')
        sys.exit(1)

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"Erreur : fichier introuvable : {image_path}")
        sys.exit(1)

    prompt = sys.argv[2]
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    generate(image_path, prompt, duration)
