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
SCENES_REF_DIR = Path("references/scenes")

# Preferred master reference; falls back to first image found in ALY_REFS_DIR.
ALY_MASTER = ALY_REFS_DIR / "aly_master.png"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

SCENE_REF_SUFFIX = (
    "Recreate the scene reference image while preserving exactly the same environment, "
    "camera angle, framing, lighting, outfit style, pose, perspective, depth of field and atmosphere. "
    "Replace only the person with Aly from the Aly character reference. "
    "Aly must be perfectly integrated into the scene with realistic shadows, matching light direction, "
    "matching color temperature, realistic skin texture and the same natural photo quality. "
    "Clean final photo export only. No camera app interface, no iPhone UI, no screenshot elements."
)

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


def resolve_aly_reference() -> Path | None:
    """Return the Aly identity reference image, or None if not found."""
    if ALY_MASTER.exists():
        return ALY_MASTER
    candidates = sorted(
        p for p in ALY_REFS_DIR.iterdir()
        if p.suffix.lower() in IMAGE_EXTENSIONS
    )
    return candidates[0] if candidates else None


def is_aly_prompt(prompt: str) -> bool:
    keywords = ["aly", "alycia", "alicia"]
    return any(k in prompt.lower() for k in keywords)


def create_image_job(prompt: str, aspect_ratio: str = "9:16", scene_reference: Path | None = None) -> dict:
    if not API_KEY:
        raise ValueError("ALEXYA_API_KEY manquante dans .env")

    image_urls = []

    if scene_reference is not None:
        # Scene-reference mode: upload scene photo + Aly identity reference.
        if not scene_reference.exists():
            raise FileNotFoundError(f"Scene reference introuvable : {scene_reference}")
        print(f"Mode scène-référence : {scene_reference.name}")
        image_urls.append(upload_reference(scene_reference))

        aly_ref = resolve_aly_reference()
        if aly_ref:
            image_urls.append(upload_reference(aly_ref))
        else:
            print(f"Avertissement : aucune référence Aly trouvée dans {ALY_REFS_DIR}")

        # Append the scene-recreation instruction to the prompt.
        if SCENE_REF_SUFFIX not in prompt:
            prompt = prompt.rstrip(". ") + ". " + SCENE_REF_SUFFIX

    elif is_aly_prompt(prompt):
        # Standard Aly prompt: inject identity reference only.
        aly_ref = resolve_aly_reference()
        if aly_ref:
            image_urls.append(upload_reference(aly_ref))
        else:
            print(f"Avertissement : aucune référence Aly trouvée dans {ALY_REFS_DIR}")

    payload = {
        "prompt": prompt,
        "mode": "high_quality",
        "aspect_ratio": aspect_ratio,
    }
    if image_urls:
        payload["image_urls"] = image_urls

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


def generate(prompt: str, aspect_ratio: str = "9:16", scene_reference: Path | None = None) -> None:
    job = create_image_job(prompt, aspect_ratio, scene_reference=scene_reference)

    poll_url = job.get("poll_url")
    if not poll_url:
        raise RuntimeError(f"poll_url absent dans la réponse : {job}")

    output_url = poll_job(poll_url)
    output_path = download_image(output_url, prompt)
    print(f"\nImage sauvegardée : {output_path}")


def _print_usage():
    print("Usage :")
    print("  python3 generate_image.py \"votre prompt\" [aspect_ratio]")
    print("  python3 generate_image.py --scene-reference <image> \"votre prompt\" [aspect_ratio]")
    print()
    print("Aspect ratios : 1:1  16:9  9:16  4:3  3:4  5:4  4:5  (défaut : 9:16)")
    print()
    print("Exemples :")
    print("  python3 generate_image.py \"Aly sourit face caméra dans sa chambre\" 9:16")
    print("  python3 generate_image.py --scene-reference references/scenes/my_scene.jpg \"Recreate this photo with Aly\"")
    print()
    print("Mode --scene-reference :")
    print("  Upload automatiquement la photo de scène + la référence Aly.")
    print("  Préserve : décor, angle, cadrage, lumière, tenue, pose, profondeur de champ.")
    print("  Remplace uniquement la personne par Aly.")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        _print_usage()
        sys.exit(0 if args else 1)

    scene_ref = None
    if args[0] == "--scene-reference":
        if len(args) < 3:
            print("Erreur : --scene-reference attend un chemin d'image puis un prompt.")
            print()
            _print_usage()
            sys.exit(1)
        scene_ref = Path(args[1])
        SCENES_REF_DIR.mkdir(parents=True, exist_ok=True)
        args = args[2:]

    prompt = args[0]
    aspect_ratio = args[1] if len(args) > 1 else "9:16"
    generate(prompt, aspect_ratio, scene_reference=scene_ref)
