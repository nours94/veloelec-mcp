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


def determiner_categorie(usage):
    usage_n = normaliser(usage)

    if usage_n == "famille":
        return "cargo"

    if usage_n == "vtt":
        return "VTT"

    if usage_n in ["travail", "randonnée", "loisir"]:
        return "VTC"

    if usage_n == "ville":
        return "ville"

    return None


def calculer_recommandations(
    velos,
    budget_max,
    distance_km=None,
    relief=None,
    priorite=None,
):
    relief_n = normaliser(relief)
    priorite_n = normaliser(priorite)
    budget_avec_marge = int(budget_max * 1.10)

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
    return recommandations