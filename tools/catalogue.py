import time
import requests

API_BASE = "https://comparateur-velo.onrender.com"


def appeler_catalogue(params: dict):
    for tentative in range(3):
        response = requests.get(
            f"{API_BASE}/api/ia/catalogue",
            params=params,
            timeout=60
        )

        if response.status_code == 429:
            time.sleep(5 * (tentative + 1))
            continue

        response.raise_for_status()
        return response.json()

    return {
        "site": "VéloÉlec & Co",
        "erreur": "Trop de requêtes vers le catalogue. Réessayez dans quelques secondes.",
        "velos": []
    }