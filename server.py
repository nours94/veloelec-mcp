import os
from pathlib import Path

from fastmcp import FastMCP
from tools.catalogue import appeler_catalogue, appeler_catalogue_cible, CatalogueError
from tools.comparaison import comparer
from tools.detail import trouver_velo
from tools.recommandation import (
    determiner_categorie,
    extraire_velos,
    calculer_recommandations,
)

mcp = FastMCP("VeloElec & Co")


READ_ONLY_TOOL = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}


def ui_meta(resource_uri: str):
    return {
        "ui.resourceUri": resource_uri,
        "openai/outputTemplate": resource_uri,
    }


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


@mcp.tool(annotations=READ_ONLY_TOOL)
def recommander_velos(
    budget_max: int,
    usage: str,
    distance_km: int | None = None,
    relief: str | None = None,
    priorite: str | None = None,
    taille_cm: int | None = None,
):
    """
    Utiliser cet outil dès qu'un utilisateur demande une recommandation de vélo électrique.
    Retourne uniquement des vélos issus du catalogue VeloElec & Co.
    Ne modifie aucune donnée.
    """
    categorie = determiner_categorie(usage)
    budget_avec_marge = int(budget_max * 1.10)

    params = {"budget_max": budget_avec_marge}

    if taille_cm:
        params["taille_cm"] = taille_cm

    if categorie:
        params["categorie"] = categorie

    try:
        data = appeler_catalogue(params)
    except CatalogueError as e:
        return {
            "erreur": str(e),
            "usage": usage,
            "categorie_utilisee": categorie,
            "budget_initial": budget_max,
            "nombre_resultats": 0,
            "recommandations": [],
            "_meta": ui_meta("ui://velo-widget.html"),
        }

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
        "_meta": ui_meta("ui://velo-widget.html"),
    }


@mcp.tool(annotations=READ_ONLY_TOOL)
def rechercher_velos(
    budget_max: int | None = None,
    taille_cm: int | None = None,
    categorie: str | None = None,
):
    """
    Utiliser cet outil pour rechercher des vélos dans le catalogue VeloElec & Co.
    Retourne uniquement des vélos du catalogue.
    Ne modifie aucune donnée.
    """
    params = {}

    if budget_max:
        params["budget_max"] = budget_max

    if taille_cm:
        params["taille_cm"] = taille_cm

    if categorie:
        params["categorie"] = categorie

    try:
        return appeler_catalogue(params)
    except CatalogueError as e:
        return {
            "erreur": str(e),
            "velos": [],
        }


@mcp.tool(annotations=READ_ONLY_TOOL)
def detail_velo(identifiant: str):
    """
    Utiliser cet outil pour afficher la fiche détaillée d'un vélo du catalogue VeloElec & Co.
    Recherche par id, nom ou modèle.
    Ne modifie aucune donnée.
    """
    try:
        data = appeler_catalogue_cible(identifiant)
    except CatalogueError as e:
        return {
            "trouve": False,
            "erreur": str(e),
            "velo": None,
            "_meta": ui_meta("ui://detail-widget.html"),
        }

    velo = trouver_velo(data, identifiant)

    if not velo:
        # Repli : l'identifiant ne correspond peut-être à aucun mot-clé
        # indexé côté SQL (ex. un id technique "velo-042"), on retente
        # alors sur le catalogue complet avant de conclure à une absence.
        try:
            data_complet = appeler_catalogue({})
        except CatalogueError as e:
            return {
                "trouve": False,
                "erreur": str(e),
                "velo": None,
                "_meta": ui_meta("ui://detail-widget.html"),
            }
        velo = trouver_velo(data_complet, identifiant)

    if not velo:
        return {
            "trouve": False,
            "message": "Aucun vélo trouvé pour cet identifiant.",
            "velo": None,
            "_meta": ui_meta("ui://detail-widget.html"),
        }

    return {
        "trouve": True,
        "velo": velo,
        "_meta": ui_meta("ui://detail-widget.html"),
    }


@mcp.tool(annotations=READ_ONLY_TOOL)
def comparer_velos(identifiant_1: str, identifiant_2: str):
    """
    Utiliser cet outil pour comparer deux vélos du catalogue VeloElec & Co.
    Recherche les deux vélos par id, nom ou modèle.
    Ne modifie aucune donnée.
    """
    try:
        data_1 = appeler_catalogue_cible(identifiant_1)
        data_2 = appeler_catalogue_cible(identifiant_2)
    except CatalogueError as e:
        return {
            "erreur": str(e),
            "velo_1": None,
            "velo_2": None,
            "trouve_1": False,
            "trouve_2": False,
            "_meta": ui_meta("ui://compare-widget.html"),
        }

    velos_fusionnes = extraire_velos(data_1) + extraire_velos(data_2)
    velo_1, velo_2 = comparer({"velos": velos_fusionnes}, identifiant_1, identifiant_2)

    if velo_1 is None or velo_2 is None:
        # Repli : un des deux identifiants n'a peut-être pas matché de
        # mot-clé indexé côté SQL (ex. id technique), on retente sur le
        # catalogue complet avant de conclure à une absence.
        try:
            data_complet = appeler_catalogue({})
        except CatalogueError as e:
            return {
                "erreur": str(e),
                "velo_1": velo_1,
                "velo_2": velo_2,
                "trouve_1": velo_1 is not None,
                "trouve_2": velo_2 is not None,
                "_meta": ui_meta("ui://compare-widget.html"),
            }
        velo_1, velo_2 = comparer(data_complet, identifiant_1, identifiant_2)

    return {
        "velo_1": velo_1,
        "velo_2": velo_2,
        "trouve_1": velo_1 is not None,
        "trouve_2": velo_2 is not None,
        "_meta": ui_meta("ui://compare-widget.html"),
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
    )