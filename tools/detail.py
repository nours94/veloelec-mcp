from tools.recommandation import extraire_velos


def trouver_velo(data, identifiant: str):
    velos = extraire_velos(data)
    identifiant_n = (identifiant or "").strip().lower()

    for velo in velos:
        candidats = [
            velo.get("id"),
            velo.get("nom"),
            velo.get("modele"),
        ]

        for candidat in candidats:
            if candidat and identifiant_n in str(candidat).lower():
                return velo

    return None