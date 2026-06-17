import os
import sys
import json
import hashlib
import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OUTPUT_BASE = Path("outputs")

PROMPT_SUFFIX = (
    "Clean final photo export. No camera app interface. No iPhone UI. No shutter button. "
    "No screen overlay. No recording indicators. No app icons. No status bar. "
    "No notifications. No screenshot appearance. Professional final image only."
)

# ---------------------------------------------------------------------------
# Appearance presets — one is chosen per content pack and held constant
# across every scene so all images feel like the same recording session.
# Keys map directly to prompt fragments injected into every image prompt.
# ---------------------------------------------------------------------------
APPEARANCE_PRESETS = [
    {
        "id": "preset_A",
        "outfit": "oversized cream ribbed knit sweater with wide neckline",
        "hairstyle": "loose curly deep red hair down over shoulders",
        "makeup": "natural minimal makeup, light lip gloss, subtle mascara",
        "glasses": "large glossy black rectangular frames",
        "microphone": "RØDE NT-USB Mini on boom arm, slightly left of frame",
    },
    {
        "id": "preset_B",
        "outfit": "fitted black scoop-neck long sleeve top",
        "hairstyle": "curly deep red hair half-up half-down with loose strands framing face",
        "makeup": "soft matte skin, nude lip, defined brows",
        "glasses": "large glossy black rectangular frames",
        "microphone": "RØDE NT-USB Mini on boom arm, slightly left of frame",
    },
    {
        "id": "preset_C",
        "outfit": "sage green wrap-style blouse with wide neckline",
        "hairstyle": "curly deep red hair pulled loosely to one side",
        "makeup": "dewy skin, soft rose lip, light blush",
        "glasses": "large glossy black rectangular frames",
        "microphone": "RØDE NT-USB Mini on boom arm, slightly left of frame",
    },
    {
        "id": "preset_D",
        "outfit": "white linen button-down shirt open at neckline",
        "hairstyle": "curly deep red hair down, natural volume, no accessories",
        "makeup": "fresh bare-skin look, tinted moisturizer, clear lip",
        "glasses": "large glossy black rectangular frames",
        "microphone": "RØDE NT-USB Mini on boom arm, slightly left of frame",
    },
]


def pick_appearance(topic):
    """Pick a preset deterministically from the topic so re-runs are stable."""
    index = int(hashlib.md5(topic.encode()).hexdigest(), 16) % len(APPEARANCE_PRESETS)
    return APPEARANCE_PRESETS[index]


def appearance_fragment(appearance):
    """Return the prompt fragment that describes Aly's locked appearance."""
    return (
        "{outfit}, {hairstyle}, {makeup}, {glasses}, {microphone}".format(**appearance)
    )


# ---------------------------------------------------------------------------
# Scene templates
# Appearance details are NOT hardcoded here — they are injected at
# build_scenes() time from the chosen preset so every prompt is consistent.
# ---------------------------------------------------------------------------
SCENE_TEMPLATES = [
    {
        "scene_number": 1,
        "type": "talking-head",
        "duration_seconds": 5,
        "role": "hook",
        "description_template": "Aly face caméra, expression choquée ou intriguée, accroche immédiate sur le sujet : {topic}",
        "voiceover_template": "[ HOOK — question choc ou révélation ] ex: « {topic} — et personne ne t'en parle. »",
        "image_prompt_base": "Aly talking directly to camera with shocked wide-eyed expression, cozy bedroom warm light, freckles, green eyes, ultra realistic, amateur iPhone photo quality, 9:16",
    },
    {
        "scene_number": 2,
        "type": "talking-head",
        "duration_seconds": 7,
        "role": "setup",
        "description_template": "Aly introduit le contexte, pose la situation liée à : {topic}",
        "voiceover_template": "[ SETUP — contexte ] ex: « Laisse-moi t'expliquer ce qui m'est arrivé / ce que j'ai observé... »",
        "image_prompt_base": "Aly talking to camera with serious focused expression, cozy bedroom natural daylight, green eyes, ultra realistic, 9:16",
    },
    {
        "scene_number": 3,
        "type": "b-roll",
        "duration_seconds": 6,
        "role": "development",
        "description_template": "B-roll illustrant la situation ou l'émotion associée à : {topic}",
        "voiceover_template": "[ VOIX OFF — narration ] ex: « Au début, tout semblait normal... »",
        "image_prompt_base": "close-up hands holding smartphone with chat conversation visible, cozy bedroom background warm bokeh, natural light, ultra realistic, amateur iPhone quality, 9:16",
    },
    {
        "scene_number": 4,
        "type": "reaction",
        "duration_seconds": 5,
        "role": "development",
        "description_template": "Gros plan réaction d'Aly face à une révélation ou situation liée à : {topic}",
        "voiceover_template": "[ RÉACTION ] ex: « Et là... j'ai compris. »",
        "image_prompt_base": "Aly close-up face reaction shot, concerned or disappointed expression, green eyes slightly narrowed, freckles, soft warm light, ultra realistic, amateur iPhone quality, 9:16",
    },
    {
        "scene_number": 5,
        "type": "talking-head",
        "duration_seconds": 7,
        "role": "development",
        "description_template": "Aly développe le premier point clé sur : {topic}",
        "voiceover_template": "[ POINT 1 ] ex: « La première chose à savoir, c'est que... »",
        "image_prompt_base": "Aly talking to camera with neutral confident expression, gesturing with hand, cozy bedroom warm light, green eyes, ultra realistic, 9:16",
    },
    {
        "scene_number": 6,
        "type": "b-roll",
        "duration_seconds": 6,
        "role": "development",
        "description_template": "B-roll illustrant le deuxième aspect de : {topic}",
        "voiceover_template": "[ POINT 2 — voix off ] ex: « Et ce que la plupart des gens ignorent... »",
        "image_prompt_base": "couple sitting together at cafe table, warm golden hour light, candid intimate moment, bokeh background, ultra realistic, amateur iPhone photo, 9:16",
    },
    {
        "scene_number": 7,
        "type": "talking-head",
        "duration_seconds": 7,
        "role": "development",
        "description_template": "Aly approfondit avec une anecdote personnelle ou un exemple concret sur : {topic}",
        "voiceover_template": "[ ANECDOTE / EXEMPLE ] ex: « Une amie m'a dit quelque chose qui a tout changé... »",
        "image_prompt_base": "Aly talking to camera with thoughtful reflective expression, cozy bedroom with Pokémon plushies visible, warm light, green eyes, ultra realistic, 9:16",
    },
    {
        "scene_number": 8,
        "type": "reaction",
        "duration_seconds": 5,
        "role": "development",
        "description_template": "Réaction émotionnelle d'Aly — twist ou révélation sur : {topic}",
        "voiceover_template": "[ TWIST ] ex: « Et la vérité que personne ne dit... c'est ça. »",
        "image_prompt_base": "Aly close-up face with skeptical expression, slightly raised eyebrow, lips pressed together, green eyes, freckles, soft natural light, ultra realistic, amateur iPhone quality, 9:16",
    },
    {
        "scene_number": 9,
        "type": "talking-head",
        "duration_seconds": 7,
        "role": "conseil",
        "description_template": "Aly donne le conseil clé ou la leçon retenue sur : {topic}",
        "voiceover_template": "[ CONSEIL / LEÇON ] ex: « Ce que j'ai retenu de tout ça, c'est simple : ... »",
        "image_prompt_base": "Aly talking to camera with serious thoughtful expression, cozy bedroom warm light, green eyes, ultra realistic, 9:16",
    },
    {
        "scene_number": 10,
        "type": "talking-head",
        "duration_seconds": 6,
        "role": "cta",
        "description_template": "Aly conclut avec un appel à l'action — question à la communauté sur : {topic}",
        "voiceover_template": "[ CTA ] ex: « Et toi, t'as déjà vécu ça ? Dis-moi en commentaire 👇 »",
        "image_prompt_base": "Aly talking to camera with confident direct expression, pointing finger toward camera, cozy bedroom, green eyes, ultra realistic, 9:16",
    },
]

# B-roll scenes have no Aly face — appearance fragment is omitted for those.
BROLL_SCENES = {3, 6}


def build_scenes(topic, appearance):
    frag = appearance_fragment(appearance)
    scenes = []
    for t in SCENE_TEMPLATES:
        n = t["scene_number"]
        base = t["image_prompt_base"]

        if n in BROLL_SCENES:
            # B-roll: environment only, no Aly appearance details needed.
            full_prompt = base + " " + PROMPT_SUFFIX
        else:
            # Insert appearance fragment right after the base description.
            full_prompt = base + ", " + frag + " " + PROMPT_SUFFIX

        scene = {
            "scene_number": n,
            "type": t["type"],
            "duration_seconds": t["duration_seconds"],
            "role": t["role"],
            "description": t["description_template"].format(topic=topic),
            "voiceover": t["voiceover_template"].format(topic=topic),
            "image_prompt": full_prompt,
        }
        scenes.append(scene)
    return scenes


def generate_plan(topic):
    appearance = pick_appearance(topic)
    scenes = build_scenes(topic, appearance)
    total_duration = sum(s["duration_seconds"] for s in scenes)
    plan = {
        "title": "[ TITRE À COMPLÉTER ] — " + topic,
        "topic": topic,
        "duration_seconds": total_duration,
        "appearance": appearance,
        "scenes": scenes,
    }
    return plan


def save_pack(topic, plan):
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    slug = topic[:40].replace(" ", "_").replace("/", "-")
    pack_dir = OUTPUT_BASE / (timestamp + "_" + slug)
    pack_dir.mkdir(parents=True, exist_ok=True)

    scenes_path = pack_dir / "scenes.json"
    scenes_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    plan_md = _build_plan_md(plan)
    plan_path = pack_dir / "plan.md"
    plan_path.write_text(plan_md, encoding="utf-8")

    return pack_dir


def _build_plan_md(plan):
    appearance = plan.get("appearance", {})
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
        "## Apparence — session complète",
        "",
        "> Ces détails sont identiques dans toutes les scènes.",
        "",
        "| Élément | Choix pour cette vidéo |",
        "|---------|------------------------|",
        "| Tenue | " + appearance.get("outfit", "") + " |",
        "| Coiffure | " + appearance.get("hairstyle", "") + " |",
        "| Maquillage | " + appearance.get("makeup", "") + " |",
        "| Lunettes | " + appearance.get("glasses", "") + " |",
        "| Micro | " + appearance.get("microphone", "") + " |",
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
    appearance = plan.get("appearance", {})
    print("\n" + "=" * 60)
    print("PLAN GÉNÉRÉ : " + plan.get("title", ""))
    print("=" * 60)
    print("Sujet     : " + plan.get("topic", ""))
    print("Durée     : " + str(plan.get("duration_seconds", "?")) + "s")
    print("Scènes    : " + str(len(plan.get("scenes", []))))
    print("\nApparence (session complète) :")
    print("  Preset    : " + appearance.get("id", ""))
    print("  Tenue     : " + appearance.get("outfit", ""))
    print("  Coiffure  : " + appearance.get("hairstyle", ""))
    print("  Maquillage: " + appearance.get("makeup", ""))
    print("  Lunettes  : " + appearance.get("glasses", ""))
    print("  Micro     : " + appearance.get("microphone", ""))
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
