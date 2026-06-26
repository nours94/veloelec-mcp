import os
from fastmcp import FastMCP
from tools.catalogue import appeler_catalogue

mcp = FastMCP("VeloElec & Co")


def normaliser(texte):
    return (texte or "").strip().lower()


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
    Recommande les 3 meilleurs vélos selon le profil utilisateur.
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

    budget_avec_marge = int(budget_max * 1.1)

    params = {
        "budget_max": budget_avec_marge
    }

    if taille_cm:
        params["taille_cm"] = taille_cm

    if categorie:
        params["categorie"] = categorie

    data = appeler_catalogue(params)
    velos = data.get("velos", [])

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
            raisons.append("Reste dans la marge maximale de 10 % du budget.")
        else:
            limites.append("Dépasse le budget autorisé.")
            continue

        if relief_n in ["vallonné", "très vallonné", "chemins", "sentiers"]:
            if couple >= 70:
                score += 25
                raisons.append("Couple moteur élevé adapté au relief.")
            elif couple >= 50:
                score += 15
                raisons.append("Couple moteur correct.")
            else:
                limites.append("Couple moteur limité pour relief difficile.")

        if distance_km and distance_km > 40:
            if any(x in batterie for x in ["700", "720", "730"]):
                score += 25
                raisons.append("Batterie importante pour longues distances.")
            elif any(x in batterie for x in ["500", "614"]):
                score += 15
                raisons.append("Batterie correcte pour trajets réguliers.")
            else:
                limites.append("Batterie potentiellement limitée pour longues distances.")

        if priorite_n == "prix":
            bonus_prix = max(0, 20 - int(prix / 300))
            score += bonus_prix
            raisons.append("Bon positionnement prix.")

        if priorite_n == "puissance" and couple >= 70:
            score += 20
            raisons.append("Très bon couple moteur.")

        if poids < 25:
            score += 10
            raisons.append("Poids contenu.")

        velo_resultat = {
            **velo,
            "score": score,
            "raisons": raisons,
            "limites": limites,
        }

        recommandations.append(velo_resultat)

    recommandations.sort(key=lambda v: v["score"], reverse=True)

    return {
        "usage": usage,
        "categorie_utilisee": categorie,
        "budget_initial": budget_max,
        "budget_max_avec_marge": budget_avec_marge,
        "nombre_resultats": len(recommandations),
        "recommandations": recommandations[:3],
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port
    )