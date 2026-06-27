import os
from pathlib import Path

from fastmcp import FastMCP
from tools.catalogue import appeler_catalogue
from tools.comparaison import comparer
from tools.detail import trouver_velo
from tools.recommandation import (
    determiner_categorie,
    extraire_velos,
    calculer_recommandations,
)

mcp = FastMCP("VeloElec & Co")


@mcp.resource("ui://home.html")
def home_widget():
    chemin = Path(__file__).parent / "public" / "home.html"
    return chemin.read_text(encoding="utf-8")


@mcp.resource("ui://velo-widget.html")
def velo_widget():
    chemin = Path(__file__).parent / "public" / "velo-widget.html"
    return chemin.read_text(encoding="utf-8")


@mcp.resource("ui://detail-widget.html")
def detail_widget():
    chemin = Path(__file__).parent / "public" / "detail-widget.html"
    return chemin.read_text(encoding="utf-8")


@mcp.resource("ui://compare-widget.html")
def compare_widget():
    chemin = Path(__file__).parent / "public" / "compare-widget.html"
    return chemin.read_text(encoding="utf-8")


@mcp.tool()
def recommander_velos(
    budget_max: int,
    usage: str,
    distance_km: int | None = None,
    relief: str | None = None,
    priorite: str | None = None,
    taille_cm: int | None = None,
):
    categorie = determiner_categorie(usage)
    budget_avec_marge = int(budget_max * 1.10)

    params = {"budget_max": budget_avec_marge}

    if taille_cm:
        params["taille_cm"] = taille_cm

    if categorie:
        params["categorie"] = categorie

    data = appeler_catalogue(params)
    velos = extraire_velos(data)

    recommandations = calculer_recommandations(
        velos=velos,
        budget_max=budget_max,
        distance_km=distance_km,
        relief=relief,
        priorite=priorite,
    )

    return {
        "usage": usage,
        "categorie_utilisee": categorie,
        "budget_initial": budget_max,
        "budget_max_avec_marge": budget_avec_marge,
        "nombre_resultats": len(recommandations),
        "recommandations": recommandations[:3],
        "_meta": {
            "openai/outputTemplate": "ui://velo-widget.html"
        }
    }


@mcp.tool()
def rechercher_velos(
    budget_max: int | None = None,
    taille_cm: int | None = None,
    categorie: str | None = None,
):
    params = {}

    if budget_max:
        params["budget_max"] = budget_max

    if taille_cm:
        params["taille_cm"] = taille_cm

    if categorie:
        params["categorie"] = categorie

    return appeler_catalogue(params)


@mcp.tool()
def detail_velo(identifiant: str):
    data = appeler_catalogue({})
    velo = trouver_velo(data, identifiant)

    if not velo:
        return {
            "trouve": False,
            "message": "Aucun vélo trouvé pour cet identifiant.",
            "velo": None,
        }

    return {
        "trouve": True,
        "velo": velo,
        "_meta": {
            "openai/outputTemplate": "ui://detail-widget.html"
        }
    }


@mcp.tool()
def comparer_velos(identifiant_1: str, identifiant_2: str):
    data = appeler_catalogue({})
    velo_1, velo_2 = comparer(data, identifiant_1, identifiant_2)

    return {
        "velo_1": velo_1,
        "velo_2": velo_2,
        "trouve_1": velo_1 is not None,
        "trouve_2": velo_2 is not None,
        "_meta": {
            "openai/outputTemplate": "ui://compare-widget.html"
        }
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
    )