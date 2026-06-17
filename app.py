import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALEXYA_API_KEY")
BASE_URL = "https://alexya.ai/api/v1"


def get_credits():
    if not API_KEY:
        raise ValueError("ALEXYA_API_KEY manquante dans le fichier .env")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.get(f"{BASE_URL}/account/credits", headers=headers)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    try:
        data = get_credits()
        print("Connexion réussie. Crédits disponibles :")
        print(data)
    except ValueError as e:
        print(f"Erreur de configuration : {e}")
    except requests.HTTPError as e:
        print(f"Erreur API ({e.response.status_code}) : {e.response.text}")
    except requests.ConnectionError:
        print("Impossible de joindre l'API AlexyaAI. Vérifiez votre connexion.")
