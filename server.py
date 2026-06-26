import os
from pathlib import Path

from fastmcp import FastMCP
from tools.catalogue import appeler_catalogue

mcp = FastMCP("VeloElec & Co")


def normaliser(texte):
    return (texte or "").strip().lower()


def extraire_velos(data):
    if isinstance(data, dict):
        if isinstance(data.get("velos"), list):
            return data["velos"]
        if isinstance(data.get("resultats"), list):
            return data["resultats"]
        if isinstance(data.get("data"), list):
            return data["data"]

    if isinstance(data, list):
        return data

    return []


@mcp.resource("ui://velo-widget.html")
def velo_widget():
    """
    Interface HTML utilisée par l'App ChatGPT pour afficher les recommandations.
    """
    chemin = Path(__file__).parent / "public" / "velo-widget.html"
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
    """
    Recommande automatiquement les 3 meilleurs vélos selon le profil utilisateur.
    """

    usage_n = normaliser(usage)
    relief_n = normaliser(relief)
    priorite_n = normaliser(priorite)

    categorie = None

    if usage_n == "famille":
        categorie = "cargo"
    elif usage_n == "vtt":
        categorie = "VTT"
    elif usage_n in ["travail", "randonnée", "loisir"]:
        categorie = "VTC"
    elif usage_n == "ville":
        categorie = "ville"

    budget_avec_marge = int(budget_max * 1.10)

    params = {"budget_max": budget_avec_marge}

    if taille_cm:
        params["taille_cm"] = taille_cm

    if categorie:
        params["categorie"] = categorie

    data = appeler_catalogue(params)
    velos = extraire_velos(data)

    recommandations = []

    for velo in velos:
        score = 0
        raisons = []
        limites = []

        prix = velo.get("prix") or 0
        couple = velo.get("couple_moteur") or 0
        poids = velo.get("poids") or 99
        batterie = str(velo.get("batterie") or "")

        if prix <= budget_max:
            score += 30
            raisons.append("Respecte le budget.")
        elif prix <= budget_avec_marge:
            score += 20
            raisons.append("Dans la marge de 10 %.")
        else:
            continue

        if relief_n in ["vallonné", "très vallonné", "chemins", "sentiers"]:
            if couple >= 70:
                score += 25
                raisons.append("Très bon couple moteur.")
            elif couple >= 50:
                score += 15
                raisons.append("Couple moteur correct.")
            else:
                limites.append("Couple un peu limité.")

        if distance_km and distance_km > 40:
            if any(x in batterie for x in ["700", "720", "725", "730"]):
                score += 25
                raisons.append("Grande batterie.")
            elif any(x in batterie for x in ["614", "625", "630", "500"]):
                score += 15
                raisons.append("Bonne autonomie.")
            else:
                limites.append("Autonomie moyenne.")

        if priorite_n == "prix":
            score += max(0, 20 - int(prix / 300))
            raisons.append("Bon positionnement prix.")
        elif priorite_n == "puissance" and couple >= 70:
            score += 20
            raisons.append("Bonne puissance moteur.")
        elif priorite_n == "confort":
            score += 10
            raisons.append("Profil adapté au confort.")
        elif priorite_n == "autonomie":
            score += 10
            raisons.append("Profil adapté à l'autonomie.")
        elif priorite_n == "polyvalence":
            score += 10
            raisons.append("Profil polyvalent.")

        if poids < 25:
            score += 10
            raisons.append("Poids contenu.")

        recommandations.append({
            **velo,
            "score": score,
            "raisons": raisons,
            "limites": limites,
        })

    recommandations.sort(key=lambda v: v["score"], reverse=True)

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
    """
    Recherche simple dans le catalogue.
    """

    params = {}

    if budget_max:
        params["budget_max"] = budget_max

    if taille_cm:
        params["taille_cm"] = taille_cm

    if categorie:
        params["categorie"] = categorie

    return appeler_catalogue(params)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
    )