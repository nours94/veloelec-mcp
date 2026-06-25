from fastmcp import FastMCP
from tools.catalogue import appeler_catalogue

mcp = FastMCP("VeloElec & Co")


@mcp.tool()
def rechercher_velos(
    budget_max: int | None = None,
    taille_cm: int | None = None,
    categorie: str | None = None,
):
    """
    Recherche des vélos électriques dans le catalogue VeloElec & Co.
    """
    params = {}

    if budget_max:
        params["budget_max"] = budget_max

    if taille_cm:
        params["taille_cm"] = taille_cm

    if categorie:
        params["categorie"] = categorie

    return appeler_catalogue(params)


@mcp.tool()
def rechercher_cargos(
    budget_max: int | None = None,
    taille_cm: int | None = None,
):
    """
    Recherche les vélos cargo électriques pour transporter enfants ou charges.
    """
    params = {"categorie": "cargo"}

    if budget_max:
        params["budget_max"] = budget_max

    if taille_cm:
        params["taille_cm"] = taille_cm

    return appeler_catalogue(params)


@mcp.tool()
def rechercher_velos_travail(
    budget_max: int | None = None,
    taille_cm: int | None = None,
):
    """
    Recherche des vélos adaptés aux trajets domicile-travail.
    """
    resultats = []

    for categorie in ["VTC", "ville"]:
        params = {"categorie": categorie}

        if budget_max:
            params["budget_max"] = budget_max

        if taille_cm:
            params["taille_cm"] = taille_cm

        resultats.append({
            "categorie": categorie,
            "velos": appeler_catalogue(params)
        })

    return resultats

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port
    )