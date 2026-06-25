import requests

API_BASE = "https://comparateur-velo.onrender.com"


def appeler_catalogue(params: dict):
    response = requests.get(
        f"{API_BASE}/api/ia/catalogue",
        params=params,
        timeout=60
    )
    response.raise_for_status()
    return response.json()