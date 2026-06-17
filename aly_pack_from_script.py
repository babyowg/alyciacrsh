"""
aly_pack_from_script.py

Usage:
    python3 aly_pack_from_script.py script.txt [topic]
    python3 aly_pack_from_script.py script.txt "Le jeu de l'indifférence"

Or import and call:
    from aly_pack_from_script import generate_pack_from_script
    pack_dir = generate_pack_from_script(script_text, topic="Mon sujet")

Script format expected (one block per scene):
    SCÈNE 1
    Texte : "..."
    Émotion : ...
    Plan : ...
"""

import os
import re
import sys
import json
import random
import datetime
from pathlib import Path
from typing import Optional, List, Tuple

# Always resolve imports relative to this file so the script works when
# called from any working directory (e.g. from a Claude Code slash command).
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from dotenv import load_dotenv

load_dotenv(_HERE / ".env")

# Reuse appearance + prompt logic from aly_plan
from aly_plan import (
    generate_appearance,
    appearance_fragment,
    PROMPT_SUFFIX,
    BROLL_SCENES,
)

# Reuse image generation from aly_generate_images
from aly_generate_images import generate_all

OUTPUT_BASE = _HERE / "outputs"

# Scene roles by position (1-indexed)
SCENE_ROLES = {
    1: "hook",
    2: "setup",
    3: "development",
    4: "development",
    5: "development",
    6: "development",
    7: "development",
    8: "development",
    9: "conseil",
    10: "cta",
}

# Default durations by scene number
SCENE_DURATIONS = {
    1: 5, 2: 6, 3: 6, 4: 5, 5: 6,
    6: 6, 7: 6, 8: 5, 9: 7, 10: 6,
}

# Scene types by role
SCENE_TYPES = {
    "hook": "talking-head",
    "setup": "talking-head",
    "development": "talking-head",
    "conseil": "talking-head",
    "cta": "talking-head",
}

# Emotion keyword → English expression fragment
EMOTION_MAP = {
    "provocation calme": "calm provocative expression",
    "presque dure": "near-harsh direct expression",
    "constat": "matter-of-fact neutral expression",
    "ironie amère": "bitter ironic expression",
    "ironie": "ironic expression",
    "lassitude": "weary resigned expression",
    "vulnérabilité naissante": "emerging vulnerable expression",
    "vulnérabilité": "vulnerable expression",
    "tension douce": "soft tense expression",
    "tension": "tense expression",
    "tristesse retenue": "restrained sad expression",
    "tristesse": "sad expression",
    "émotion pleine": "full emotional expression",
    "émotion": "emotional expression",
    "bascule": "liberated open expression",
    "libération": "liberated confident expression",
    "douceur": "gentle warm expression",
    "invitation": "soft inviting expression",
    "neutre": "neutral expression",
    "confident": "confident expression",
    "sérieux": "serious expression",
    "réflexif": "thoughtful reflective expression",
    "déçue": "disappointed expression",
    "déception": "disappointed expression",
    "sceptique": "skeptical expression",
    "surprise": "surprised expression",
    "sourire triste": "bittersweet slight smile",
    "sourire": "warm smile",
}

# Camera/plan keyword → English framing fragment
PLAN_MAP = {
    "face caméra": "facing directly to camera",
    "légère plongée": "slight high-angle shot",
    "regard fixe": "intense fixed gaze",
    "regard gauche": "eyes glancing to the left",
    "regard droite": "eyes glancing to the right",
    "regard dans le vide": "eyes gazing into the distance unfocused",
    "regard baissé": "gaze lowered",
    "léger recul": "slight backward lean",
    "rapprochement léger": "slight lean toward camera",
    "rapprochement": "leaning toward camera",
    "profil": "three-quarter profile",
    "gros plan visage": "close-up face shot",
    "gros plan": "close-up shot",
    "lumière plus chaude": "warmer golden light",
    "voix plus basse": "intimate close framing",
    "léger sourire triste": "with bittersweet slight smile",
}


def _translate_emotion(raw: str) -> str:
    raw_lower = raw.lower().strip()
    for key, val in EMOTION_MAP.items():
        if key in raw_lower:
            return val
    # Fallback: use raw text as-is (Alexya handles mixed language)
    return raw.strip()


def _translate_plan(raw: str) -> str:
    raw_lower = raw.lower().strip()
    fragments = []
    for key, val in PLAN_MAP.items():
        if key in raw_lower:
            fragments.append(val)
    if fragments:
        return ", ".join(fragments)
    return raw.strip()


def _build_image_prompt(n: int, emotion_raw: str, plan_raw: str, appearance_frag: str) -> str:
    if n in BROLL_SCENES:
        base = "cozy bedroom background warm bokeh, natural light, ultra realistic, amateur iPhone quality, 9:16"
        return base + " " + PROMPT_SUFFIX

    emotion_en = _translate_emotion(emotion_raw)
    plan_en = _translate_plan(plan_raw)

    is_reaction = any(k in emotion_raw.lower() for k in ["gros plan", "émotion pleine", "tristesse", "retenue"])
    is_closeup = "gros plan" in plan_raw.lower()

    if is_closeup or is_reaction:
        base = f"Aly close-up face with {emotion_en}, {plan_en}, freckles, green eyes, soft warm light, ultra realistic, amateur iPhone photo quality, 9:16"
    else:
        base = f"Aly talking to camera with {emotion_en}, {plan_en}, cozy bedroom warm light, green eyes, freckles, ultra realistic, amateur iPhone photo quality, 9:16"

    return base + ", " + appearance_frag + " " + PROMPT_SUFFIX


def infer_topic_from_script(script_text: str) -> str:
    """
    Extract a topic/title from the script text.
    Tries these in order:
      1. A line starting with "Titre :" or "Sujet :"
      2. The first non-empty quoted text (first Texte field)
      3. The first non-empty line before SCÈNE 1
    Falls back to a timestamp slug if nothing is found.
    """
    # 1. Explicit title line
    m = re.search(r"(?:Titre|Sujet)\s*:\s*(.+)", script_text, re.IGNORECASE)
    if m:
        return m.group(1).strip().strip('"').strip()

    # 2. First Texte field — use up to 50 chars as slug
    m = re.search(r"Texte\s*:\s*[\"«]?\s*(.+?)[\".»]", script_text, re.IGNORECASE)
    if m:
        raw = m.group(1).strip()
        return raw[:50].rstrip(".,…")

    # 3. First non-empty line before any SCÈNE marker
    for line in script_text.splitlines():
        line = line.strip()
        if line and not re.match(r"SC[ÈE]NE\s+\d+", line, re.IGNORECASE):
            return line[:50]

    return "pack_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def parse_script(script_text: str) -> List[dict]:
    """
    Parse a script in the Aly format into a list of raw scene dicts.
    Handles both SCÈNE and SCENE, with or without quotes around Texte.
    """
    # Split on scene headers: SCÈNE N or SCENE N
    blocks = re.split(r"\bSC[ÈE]NE\s+(\d+)\b", script_text, flags=re.IGNORECASE)

    # blocks = [pre, num, content, num, content, ...]
    scenes_raw = []
    i = 1
    while i < len(blocks) - 1:
        num = int(blocks[i])
        content = blocks[i + 1]

        texte = _extract_field(content, r"Texte\s*:\s*")
        emotion = _extract_field(content, r"[ÉE]motion\s*:\s*")
        plan = _extract_field(content, r"Plan\s*:\s*")

        # Strip surrounding quotes from texte
        texte = texte.strip().strip('"').strip("«").strip("»").strip('"').strip('"')

        scenes_raw.append({
            "num": num,
            "texte": texte,
            "emotion": emotion,
            "plan": plan,
        })
        i += 2

    if not scenes_raw:
        raise ValueError(
            "Aucune scène trouvée dans le script. "
            "Format attendu : SCÈNE N / Texte : ... / Émotion : ... / Plan : ..."
        )

    return scenes_raw


def _extract_field(text: str, pattern: str) -> str:
    match = re.search(pattern + r"(.+?)(?=\n[A-ZÉÈÊ]|\Z)", text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip().splitlines()[0].strip()
    return ""


def build_plan(script_text: str, topic: Optional[str] = None) -> dict:
    scenes_raw = parse_script(script_text)
    appearance = generate_appearance()
    frag = appearance_fragment(appearance)

    if not topic:
        topic = "Contenu Aly"

    scenes = []
    for s in scenes_raw:
        n = s["num"]
        role = SCENE_ROLES.get(n, "development")
        stype = SCENE_TYPES.get(role, "talking-head")
        dur = SCENE_DURATIONS.get(n, 6)
        image_prompt = _build_image_prompt(n, s["emotion"], s["plan"], frag)

        scenes.append({
            "scene_number": n,
            "type": stype,
            "duration_seconds": dur,
            "role": role,
            "description": f"{s['plan']} — {s['emotion']}",
            "voiceover": s["texte"],
            "image_prompt": image_prompt,
        })

    total = sum(sc["duration_seconds"] for sc in scenes)

    return {
        "title": topic,
        "topic": topic,
        "duration_seconds": total,
        "appearance": appearance,
        "scenes": scenes,
    }


def _write_plan_md(plan: dict, pack_dir: Path) -> None:
    a = plan["appearance"]
    lines = [
        "# " + plan["title"],
        "",
        "**Sujet :** " + plan["topic"],
        "**Durée cible :** " + str(plan["duration_seconds"]) + "s",
        "",
        "---",
        "",
        "## Apparence — session complète",
        "",
        "| Élément | Choix pour cette vidéo |",
        "|---------|------------------------|",
        "| Tenue      | " + a["outfit"] + " |",
        "| Coiffure   | " + a["hairstyle"] + " |",
        "| Maquillage | " + a["makeup"] + " |",
        "| Lunettes   | " + a["glasses"] + " |",
        "| Micro      | " + a["microphone"] + " |",
        "",
        "---",
        "",
    ]
    for sc in plan["scenes"]:
        lines += [
            "## Scène " + str(sc["scene_number"]) + " — " + sc["type"] + " · " + sc["role"].upper() + " (" + str(sc["duration_seconds"]) + "s)",
            "",
            "**Description :** " + sc["description"],
            "",
            "**Voix :** " + sc["voiceover"],
            "",
            "**Prompt image :** `" + sc["image_prompt"] + "`",
            "",
        ]
    (pack_dir / "plan.md").write_text("\n".join(lines), encoding="utf-8")


def generate_pack_from_script(
    script_text: str,
    topic: Optional[str] = None,
    generate_images: bool = True,
) -> Path:
    """
    Parse script_text, write all pack files to disk, then generate images.
    Returns the pack directory path.
    """
    plan = build_plan(script_text, topic=topic)

    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    slug = (topic or "pack")[:40].replace(" ", "_").replace("/", "-")
    pack_dir = OUTPUT_BASE / (timestamp + "_" + slug)
    pack_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write scenes.json
    (pack_dir / "scenes.json").write_text(
        json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # 2. Write plan.md
    _write_plan_md(plan, pack_dir)

    # 3. Write script.txt (original, unmodified)
    (pack_dir / "script.txt").write_text(script_text.strip(), encoding="utf-8")

    print("\n" + "=" * 60)
    print("PACK CRÉÉ : " + plan["title"])
    print("=" * 60)
    print("Dossier   : " + str(pack_dir))
    print("Fichiers  : scenes.json, plan.md, script.txt")
    print("\nApparence (session complète) :")
    for k, v in plan["appearance"].items():
        print("  " + k.ljust(12) + ": " + v)
    print("\nScènes :")
    for sc in plan["scenes"]:
        print("  [" + str(sc["scene_number"]).zfill(2) + "] " + sc["type"].ljust(12) + " " + str(sc["duration_seconds"]) + "s · " + sc["role"].upper())

    if not generate_images:
        print("\nGénération d'images ignorée (generate_images=False).")
        return pack_dir

    print("\n" + "-" * 60)
    print("Lancement de la génération d'images...")
    print("-" * 60)

    failed: List[Tuple[int, str]] = []
    generated: List[Path] = []

    scenes = plan["scenes"]
    for sc in scenes:
        from aly_generate_images import generate_scene_image
        try:
            path = generate_scene_image(sc, pack_dir)
            generated.append(path)
        except Exception as e:
            failed.append((sc["scene_number"], str(e)))
            print(f"    ERREUR scène {sc['scene_number']:02d} : {e}")

    print("\n" + "=" * 60)
    print("RÉSULTAT FINAL")
    print("=" * 60)
    print("Dossier         : " + str(pack_dir))
    print("Images générées : " + str(len(generated)) + " / " + str(len(scenes)))

    if generated:
        print("\nFichiers créés :")
        for p in sorted(generated):
            print("  " + p.name)

    if failed:
        print("\nÉchecs (" + str(len(failed)) + ") :")
        for num, err in failed:
            print("  Scène " + str(num).zfill(2) + " : " + err)

    print()
    return pack_dir


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage : python3 aly_pack_from_script.py <script.txt> [topic] [--no-images] [--infer-topic]")
        print()
        print("Arguments :")
        print("  script.txt     Fichier texte contenant le script en format Aly")
        print("  topic          Titre / sujet de la vidéo (optionnel)")
        print("  --no-images    Créer le pack sans lancer la génération d'images")
        print("  --infer-topic  Déduire automatiquement le titre depuis le script")
        print()
        print("Exemples :")
        print('  python3 aly_pack_from_script.py mon_script.txt "Le jeu de l\'indifférence"')
        print('  python3 aly_pack_from_script.py /tmp/aly_script_input.txt --infer-topic')
        sys.exit(0 if len(sys.argv) > 1 else 1)

    script_file = Path(sys.argv[1])
    if not script_file.exists():
        print("Erreur : fichier introuvable : " + str(script_file))
        sys.exit(1)

    topic = None
    generate_images = True
    infer_topic = False

    for arg in sys.argv[2:]:
        if arg == "--no-images":
            generate_images = False
        elif arg == "--infer-topic":
            infer_topic = True
        elif not arg.startswith("--"):
            topic = arg

    script_text = script_file.read_text(encoding="utf-8")

    if infer_topic and not topic:
        topic = infer_topic_from_script(script_text)
        print("Titre inféré : " + topic)

    generate_pack_from_script(script_text, topic=topic, generate_images=generate_images)
