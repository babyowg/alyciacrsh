import os
import sys
import json
import time
import mimetypes
import requests
from pathlib import Path
from typing import List
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALEXYA_API_KEY")
BASE_URL = "https://alexya.ai/api/v1"
ALY_REFS_DIR = Path("references/aly")
ALY_IMAGE = ALY_REFS_DIR / "mok-up Aly.png"

POLL_INTERVAL = 5
POLL_TIMEOUT = 600

PROMPT_SUFFIX = (
    "Clean final photo export. No camera app interface. No iPhone UI. No shutter button. "
    "No screen overlay. No recording indicators. No app icons. No status bar. "
    "No notifications. No screenshot appearance. Professional final image only."
)

NEGATIVE_PROMPT = (
    "camera app UI, iPhone camera interface, shutter button, screen overlay, phone screenshot, "
    "app interface, icons, status bar, notification bar, recording overlay, text, watermark, "
    "logo, low quality, blurry, cartoon, anime, CGI, 3D render"
)


def api_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def upload_reference(image_path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type:
        mime_type = "image/png"

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

    with open(image_path, "rb") as f:
        put_resp = requests.put(
            presign_data["upload_url"],
            data=f,
            headers={"Content-Type": mime_type},
        )

    if put_resp.status_code not in (200, 204):
        raise RuntimeError(f"Échec upload ({put_resp.status_code}) : {put_resp.text}")

    return presign_data["public_url"]


def is_aly_prompt(prompt: str) -> bool:
    return any(k in prompt.lower() for k in ["aly", "alycia", "alicia"])


def create_image_job(prompt: str) -> dict:
    if not API_KEY:
        raise ValueError("ALEXYA_API_KEY manquante dans .env")

    full_prompt = prompt if prompt.endswith(PROMPT_SUFFIX) else prompt + " " + PROMPT_SUFFIX
    full_prompt = full_prompt + " Negative prompt: " + NEGATIVE_PROMPT

    payload = {
        "prompt": full_prompt,
        "mode": "high_quality",
        "aspect_ratio": "9:16",
    }

    if is_aly_prompt(prompt) and ALY_IMAGE.exists():
        public_url = upload_reference(ALY_IMAGE)
        payload["image_urls"] = [public_url]

    resp = requests.post(f"{BASE_URL}/image/generate", headers=api_headers(), json=payload)

    if resp.status_code != 202:
        raise RuntimeError(f"Erreur API ({resp.status_code}) : {resp.text}")

    return resp.json()


def poll_job(poll_url: str) -> str:
    deadline = time.time() + POLL_TIMEOUT

    while time.time() < deadline:
        resp = requests.get(poll_url, headers=api_headers())
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        print(f"    Statut : {status}")

        if status == "completed":
            output_url = data.get("output_url")
            if not output_url:
                raise RuntimeError(f"output_url absent : {data}")
            return output_url

        if status == "failed":
            raise RuntimeError(f"Job échoué : {data}")

        time.sleep(POLL_INTERVAL)

    raise TimeoutError(f"Timeout après {POLL_TIMEOUT // 60} minutes.")


def download_image(output_url: str, output_path: Path) -> None:
    img_data = requests.get(output_url).content
    output_path.write_bytes(img_data)


def scene_filename(scene: dict) -> str:
    n = scene["scene_number"]
    role = scene.get("role", scene.get("type", "scene")).lower().replace(" ", "_")
    return f"scene_{n:02d}_{role}.png"


def generate_scene_image(scene: dict, pack_dir: Path) -> Path:
    n = scene["scene_number"]
    prompt = scene.get("image_prompt", "")
    output_path = pack_dir / scene_filename(scene)

    print(f"\n  Scène {n:02d} — {scene.get('type', '')} : {prompt[:60]}...")

    if output_path.exists():
        print(f"    Déjà générée, ignorée : {output_path.name}")
        return output_path

    job = create_image_job(prompt)
    poll_url = job.get("poll_url")
    if not poll_url:
        raise RuntimeError(f"poll_url absent : {job}")

    output_url = poll_job(poll_url)
    download_image(output_url, output_path)
    print(f"    Sauvegardée : {output_path.name}")
    return output_path


def generate_all(pack_dir: Path) -> List[Path]:
    if not API_KEY:
        raise ValueError("ALEXYA_API_KEY manquante dans .env")

    scenes_path = pack_dir / "scenes.json"
    if not scenes_path.exists():
        raise FileNotFoundError(f"scenes.json introuvable dans : {pack_dir}")

    data = json.loads(scenes_path.read_text(encoding="utf-8"))
    scenes = data.get("scenes", [])

    if not scenes:
        raise ValueError("Aucune scène trouvée dans scenes.json")

    print(f"Génération de {len(scenes)} image(s) pour : {pack_dir.name}")

    generated = []
    for scene in scenes:
        path = generate_scene_image(scene, pack_dir)
        generated.append(path)

    return generated


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python3 aly_generate_images.py <pack_dir>")
        print()
        print("Exemple :")
        print("  python3 aly_generate_images.py outputs/content_packs/20240617_143022_Les_red_flags")
        sys.exit(1)

    pack_dir = Path(sys.argv[1])
    if not pack_dir.exists():
        print(f"Erreur : dossier introuvable : {pack_dir}")
        sys.exit(1)

    paths = generate_all(pack_dir)
    print(f"\n{len(paths)} image(s) générée(s) dans {pack_dir}")
