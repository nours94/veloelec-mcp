import time
import requests

API_BASE = "https://comparateur-velo.onrender.com"


class CatalogueError(Exception):
    """Levée quand le catalogue n'a pas pu répondre (429, timeout, etc.)."""
    pass


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

    raise CatalogueError(
        "Trop de requêtes vers le catalogue. Réessayez dans quelques secondes."
    )


def appeler_catalogue_cible(identifiant: str):
    """
    Appel allégé pour detail_velo / comparer_velos : on ne veut qu'un ou
    deux vélos précis, donc on passe `recherche` pour activer le filtre
    explicite côté API (1 requête SQL) au lieu de la branche "sans filtre"
    qui interroge le catalogue 7 fois (une par grande catégorie + 1
    complémentaire) pour ne garder qu'un seul vélo à la fin.
    """
    return appeler_catalogue({"recherche": identifiant, "limit": 15})