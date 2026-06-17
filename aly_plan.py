import os
import sys
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OUTPUT_BASE = Path("outputs/content_packs")

PROMPT_SUFFIX = (
    "Clean final photo export. No camera app interface. No iPhone UI. No shutter button. "
    "No screen overlay. No recording indicators. No app icons. No status bar. "
    "No notifications. No screenshot appearance. Professional final image only."
)

SCENE_TEMPLATES = [
    {
        "scene_number": 1,
        "type": "talking-head",
        "duration_seconds": 5,
        "role": "hook",
        "description_template": "Aly face caméra, expression choquée ou intriguée, accroche immédiate sur le sujet : {topic}",
        "voiceover_template": "[ HOOK — question choc ou révélation ] ex: « {topic} — et personne ne t'en parle. »",
        "image_prompt_template": "Aly talking directly to camera with shocked expression, RØDE microphone visible, cozy bedroom warm light, wide neckline feminine top, curly deep red hair, black glasses, freckles, ultra realistic, amateur iPhone photo quality, 9:16",
    },
    {
        "scene_number": 2,
        "type": "talking-head",
        "duration_seconds": 7,
        "role": "setup",
        "description_template": "Aly introduit le contexte, pose la situation liée à : {topic}",
        "voiceover_template": "[ SETUP — contexte ] ex: « Laisse-moi t'expliquer ce qui m'est arrivé / ce que j'ai observé... »",
        "image_prompt_template": "Aly talking to camera with engaged expression, RØDE microphone, cozy bedroom natural daylight, curly deep red hair, green eyes, black glasses, ultra realistic, 9:16",
    },
    {
        "scene_number": 3,
        "type": "b-roll",
        "duration_seconds": 6,
        "role": "development",
        "description_template": "B-roll illustrant la situation ou l'émotion associée à : {topic}",
        "voiceover_template": "[ VOIX OFF — narration ] ex: « Au début, tout semblait normal... »",
        "image_prompt_template": "close-up hands holding smartphone with chat conversation visible, cozy bedroom background warm bokeh, natural light, ultra realistic, amateur iPhone quality, 9:16",
    },
    {
        "scene_number": 4,
        "type": "reaction",
        "duration_seconds": 5,
        "role": "development",
        "description_template": "Gros plan réaction d'Aly face à une révélation ou situation liée à : {topic}",
        "voiceover_template": "[ RÉACTION ] ex: « Et là... j'ai compris. »",
        "image_prompt_template": "Aly close-up face reaction shot, surprised or emotional expression, green eyes wide, curly deep red hair, black glasses, soft warm light, ultra realistic, amateur iPhone quality, 9:16",
    },
    {
        "scene_number": 5,
        "type": "talking-head",
        "duration_seconds": 7,
        "role": "development",
        "description_template": "Aly développe le premier point clé sur : {topic}",
        "voiceover_template": "[ POINT 1 ] ex: « La première chose à savoir, c'est que... »",
        "image_prompt_template": "Aly talking to camera gesturing with hand, RØDE microphone, cozy bedroom warm light, wide neckline top, curly deep red hair, black glasses, ultra realistic, 9:16",
    },
    {
        "scene_number": 6,
        "type": "b-roll",
        "duration_seconds": 6,
        "role": "development",
        "description_template": "B-roll illustrant le deuxième aspect de : {topic}",
        "voiceover_template": "[ POINT 2 — voix off ] ex: « Et ce que la plupart des gens ignorent... »",
        "image_prompt_template": "couple sitting together at cafe table, warm golden hour light, candid intimate moment, bokeh background, ultra realistic, amateur iPhone photo, 9:16",
    },
    {
        "scene_number": 7,
        "type": "talking-head",
        "duration_seconds": 7,
        "role": "development",
        "description_template": "Aly approfondit avec une anecdote personnelle ou un exemple concret sur : {topic}",
        "voiceover_template": "[ ANECDOTE / EXEMPLE ] ex: « Une amie m'a dit quelque chose qui a tout changé... »",
        "image_prompt_template": "Aly talking to camera with warm smile, RØDE microphone, cozy bedroom with Pokémon plushies visible, warm light, wide neckline top, curly deep red hair, black glasses, ultra realistic, 9:16",
    },
    {
        "scene_number": 8,
        "type": "reaction",
        "duration_seconds": 5,
        "role": "development",
        "description_template": "Réaction émotionnelle d'Aly — twist ou révélation sur : {topic}",
        "voiceover_template": "[ TWIST ] ex: « Et la vérité que personne ne dit... c'est ça. »",
        "image_prompt_template": "Aly close-up face with knowing smile, slightly raised eyebrow, green eyes, curly deep red hair, black glasses, soft natural light, ultra realistic, amateur iPhone quality, 9:16",
    },
    {
        "scene_number": 9,
        "type": "talking-head",
        "duration_seconds": 7,
        "role": "conseil",
        "description_template": "Aly donne le conseil clé ou la leçon retenue sur : {topic}",
        "voiceover_template": "[ CONSEIL / LEÇON ] ex: « Ce que j'ai retenu de tout ça, c'est simple : ... »",
        "image_prompt_template": "Aly talking to camera with serious thoughtful expression, RØDE microphone, cozy bedroom warm light, wide neckline top, curly deep red hair, black glasses, ultra realistic, 9:16",
    },
    {
        "scene_number": 10,
        "type": "talking-head",
        "duration_seconds": 6,
        "role": "cta",
        "description_template": "Aly conclut avec un appel à l'action — question à la communauté sur : {topic}",
        "voiceover_template": "[ CTA ] ex: « Et toi, t'as déjà vécu ça ? Dis-moi en commentaire 👇 »",
        "image_prompt_template": "Aly talking to camera with open inviting smile, pointing finger toward camera, RØDE microphone, cozy bedroom, curly deep red hair, black glasses, ultra realistic, 9:16",
    },
]


def build_scenes(topic):
    scenes = []
    for t in SCENE_TEMPLATES:
        scene = {
            "scene_number": t["scene_number"],
            "type": t["type"],
            "duration_seconds": t["duration_seconds"],
            "role": t["role"],
            "description": t["description_template"].format(topic=topic),
            "voiceover": t["voiceover_template"].format(topic=topic),
            "image_prompt": t["image_prompt_template"] + " " + PROMPT_SUFFIX,
        }
        scenes.append(scene)
    return scenes


def generate_plan(topic):
    scenes = build_scenes(topic)
    total_duration = sum(s["duration_seconds"] for s in scenes)
    plan = {
        "title": "[ TITRE À COMPLÉTER ] — " + topic,
        "topic": topic,
        "duration_seconds": total_duration,
        "scenes": scenes,
    }
    return plan


def save_pack(topic, plan):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = topic[:30].replace(" ", "_").replace("/", "-")
    pack_dir = OUTPUT_BASE / (timestamp + "_" + slug)
    pack_dir.mkdir(parents=True, exist_ok=True)

    scenes_path = pack_dir / "scenes.json"
    scenes_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    plan_md = _build_plan_md(plan)
    plan_path = pack_dir / "plan.md"
    plan_path.write_text(plan_md, encoding="utf-8")

    return pack_dir


def _build_plan_md(plan):
    lines = [
        "# " + plan.get("title", "Plan vidéo"),
        "",
        "**Sujet :** " + plan.get("topic", ""),
        "**Durée cible :** " + str(plan.get("duration_seconds", "?")) + "s",
        "",
        "> Édite les lignes **Voix** et le **Titre** avant de générer les images.",
        "",
        "---",
        "",
    ]

    for scene in plan.get("scenes", []):
        n = scene.get("scene_number", "?")
        stype = scene.get("type", "")
        dur = scene.get("duration_seconds", "?")
        role = scene.get("role", "").upper()
        desc = scene.get("description", "")
        vo = scene.get("voiceover", "")
        prompt = scene.get("image_prompt", "")

        lines.append("## Scène " + str(n) + " — " + stype + " · " + role + " (" + str(dur) + "s)")
        lines.append("")
        lines.append("**Description :** " + desc)
        lines.append("")
        lines.append("**Voix :** " + vo)
        lines.append("")
        lines.append("**Prompt image :** `" + prompt + "`")
        lines.append("")

    return "\n".join(lines)


def print_plan_summary(plan, pack_dir):
    print("\n" + "=" * 60)
    print("PLAN GÉNÉRÉ : " + plan.get("title", ""))
    print("=" * 60)
    print("Sujet     : " + plan.get("topic", ""))
    print("Durée     : " + str(plan.get("duration_seconds", "?")) + "s")
    print("Scènes    : " + str(len(plan.get("scenes", []))))
    print("\nDossier   : " + str(pack_dir))
    print("\nScènes :")

    for s in plan.get("scenes", []):
        role = s.get("role", "").upper()
        print("  [" + str(s["scene_number"]).zfill(2) + "] " + s["type"].ljust(12) + " " + str(s["duration_seconds"]) + "s · " + role)

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
    print("Plan sauvegardé dans : " + str(pack_dir) + "/plan.md")
    print("Scènes JSON dans     : " + str(pack_dir) + "/scenes.json")
