import os
import sys
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv
import anthropic

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OUTPUT_BASE = Path("outputs/content_packs")
STYLE_GUIDE = Path("aly_style_guide.md")


def load_style_guide() -> str:
    if STYLE_GUIDE.exists():
        return STYLE_GUIDE.read_text(encoding="utf-8")
    return ""


def generate_plan(topic: str) -> dict:
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY manquante dans .env")

    style_guide = load_style_guide()

    system_prompt = f"""Tu es le directeur créatif d'Aly, une influenceuse IA francophone spécialisée dans la niche couple & relations amoureuses.

Voici le guide de style d'Aly :

{style_guide}

Ton rôle : à partir d'un sujet donné, générer un plan vidéo complet de 9 à 10 scènes pour une vidéo TikTok/Reels de 60 à 70 secondes.

Réponds UNIQUEMENT avec un objet JSON valide (pas de markdown, pas de texte autour), avec cette structure exacte :

{{
  "title": "Titre accrocheur de la vidéo (en français)",
  "topic": "sujet fourni",
  "duration_seconds": 65,
  "scenes": [
    {{
      "scene_number": 1,
      "type": "talking-head|b-roll|reaction",
      "duration_seconds": 6,
      "description": "Description détaillée de ce qui se passe dans la scène",
      "voiceover": "Ce qu'Aly dit exactement (en français)",
      "image_prompt": "Prompt en anglais pour générer l'image AlexyaAI, inclure 'Aly' si Aly est visible"
    }}
  ]
}}"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    print(f"Génération du plan pour : {topic!r}")
    print("Appel Claude claude-opus-4-8...")

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": f"Crée un plan vidéo complet pour le sujet suivant : {topic}",
            }
        ],
    )

    raw = message.content[-1].text.strip()

    try:
        plan = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Réponse Claude invalide (pas du JSON) : {e}\n\nRéponse brute :\n{raw}")

    return plan


def save_pack(topic: str, plan: dict) -> Path:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = topic[:30].replace(" ", "_").replace("/", "-")
    pack_dir = OUTPUT_BASE / f"{timestamp}_{slug}"
    pack_dir.mkdir(parents=True, exist_ok=True)

    scenes_path = pack_dir / "scenes.json"
    scenes_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    plan_md = _build_plan_md(plan)
    plan_path = pack_dir / "plan.md"
    plan_path.write_text(plan_md, encoding="utf-8")

    return pack_dir


def _build_plan_md(plan: dict) -> str:
    lines = [
        f"# {plan.get('title', 'Plan vidéo')}",
        f"\n**Sujet :** {plan.get('topic', '')}",
        f"**Durée cible :** {plan.get('duration_seconds', '?')}s",
        f"\n---\n",
    ]

    for scene in plan.get("scenes", []):
        n = scene.get("scene_number", "?")
        stype = scene.get("type", "")
        dur = scene.get("duration_seconds", "?")
        desc = scene.get("description", "")
        vo = scene.get("voiceover", "")
        prompt = scene.get("image_prompt", "")

        lines.append(f"## Scène {n} — {stype} ({dur}s)")
        lines.append(f"\n**Description :** {desc}")
        lines.append(f"\n**Voix :** _{vo}_")
        lines.append(f"\n**Prompt image :** `{prompt}`")
        lines.append("")

    return "\n".join(lines)


def print_plan_summary(plan: dict, pack_dir: Path) -> None:
    print(f"\n{'='*60}")
    print(f"PLAN GÉNÉRÉ : {plan.get('title')}")
    print(f"{'='*60}")
    print(f"Sujet     : {plan.get('topic')}")
    print(f"Durée     : {plan.get('duration_seconds')}s")
    print(f"Scènes    : {len(plan.get('scenes', []))}")
    print(f"\nDossier   : {pack_dir}")
    print(f"\nScènes :")

    for s in plan.get("scenes", []):
        print(f"  [{s['scene_number']:02d}] {s['type']:12s} {s['duration_seconds']}s — {s['description'][:60]}...")

    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python3 aly_plan.py \"sujet de la vidéo\"")
        print()
        print("Exemple :")
        print('  python3 aly_plan.py "Les red flags à repérer dès le premier rendez-vous"')
        sys.exit(1)

    topic = sys.argv[1]
    plan = generate_plan(topic)
    pack_dir = save_pack(topic, plan)
    print_plan_summary(plan, pack_dir)
    print(f"Plan sauvegardé dans : {pack_dir}/plan.md")
    print(f"Scènes JSON dans     : {pack_dir}/scenes.json")
