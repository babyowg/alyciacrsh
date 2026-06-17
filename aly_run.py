import sys
from pathlib import Path

import aly_plan
import aly_generate_images


def run(topic: str) -> None:
    plan = aly_plan.generate_plan(topic)
    pack_dir = aly_plan.save_pack(topic, plan)
    aly_plan.print_plan_summary(plan, pack_dir)

    answer = input("Générer les images pour ce plan ? [o/N] ").strip().lower()
    if answer not in ("o", "oui", "y", "yes"):
        print("Génération annulée. Le plan est sauvegardé.")
        print(f"  {pack_dir}/plan.md")
        print(f"  {pack_dir}/scenes.json")
        return

    paths = aly_generate_images.generate_all(pack_dir)
    print(f"\n{len(paths)} image(s) générée(s) dans : {pack_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python3 aly_run.py \"sujet de la vidéo\"")
        print()
        print("Exemple :")
        print('  python3 aly_run.py "Les red flags à repérer dès le premier rendez-vous"')
        sys.exit(1)

    run(sys.argv[1])
