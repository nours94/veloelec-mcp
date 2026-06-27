from tools.recommandation import extraire_velos


def comparer(data, identifiant_1: str, identifiant_2: str):
    velos = extraire_velos(data)

    def trouver(identifiant):
        identifiant_n = (identifiant or "").strip().lower()
        for velo in velos:
            for champ in ["id", "nom", "modele"]:
                valeur = velo.get(champ)
                if valeur and identifiant_n in str(valeur).lower():
                    return velo
        return None

    velo_1 = trouver(identifiant_1)
    velo_2 = trouver(identifiant_2)

    return velo_1, velo_2