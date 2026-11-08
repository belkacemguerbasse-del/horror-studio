"""Outils exposés au modèle (fonctions déterministes appelées par l'agent)."""

from __future__ import annotations

import json

from anthropic import beta_tool

from .cycle import TurbojetInputs, analyze_turbojet, isa_atmosphere
from .knowledge import KnowledgeBase

_kb = KnowledgeBase()


@beta_tool
def analyser_cycle_turboreacteur(
    mach: float = 0.0,
    altitude_m: float = 0.0,
    taux_compression: float = 20.0,
    temperature_entree_turbine_K: float = 1500.0,
    rendement_compresseur: float = 0.88,
    rendement_turbine: float = 0.90,
    recouvrement_entree: float = 0.97,
    perte_pression_chambre: float = 0.04,
    debit_air_kg_s: float | None = None,
) -> str:
    """Analyse de cycle paramétrique d'un turboréacteur simple flux à tuyère convergente.

    Calcule les températures et pressions totales à chaque station (2, 3, 4, 5),
    la richesse, la vitesse d'éjection, la poussée spécifique, la consommation
    spécifique (TSFC) et les rendements thermique, propulsif et global, pour un
    point de vol donné (atmosphère ISA). Utiliser cet outil pour TOUT calcul de
    performance plutôt que d'estimer les chiffres de tête.

    Args:
        mach: Nombre de Mach de vol (0 = point fixe).
        altitude_m: Altitude en mètres (0 à 32 000).
        taux_compression: Taux de compression global OPR (Pt3/Pt2), > 1.
        temperature_entree_turbine_K: Température totale entrée turbine T4 (TIT), en kelvins.
        rendement_compresseur: Rendement isentropique du compresseur (0,80-0,92).
        rendement_turbine: Rendement isentropique de la turbine (0,85-0,93).
        recouvrement_entree: Recouvrement de pression totale de l'entrée d'air (0,90-0,99).
        perte_pression_chambre: Perte relative de pression dans la chambre (0,03-0,06).
        debit_air_kg_s: Débit d'air en kg/s ; si fourni, la poussée et le débit carburant absolus sont calculés.
    """
    try:
        res = analyze_turbojet(TurbojetInputs(
            mach=mach,
            altitude_m=altitude_m,
            pressure_ratio=taux_compression,
            turbine_inlet_temp_K=temperature_entree_turbine_K,
            eta_compressor=rendement_compresseur,
            eta_turbine=rendement_turbine,
            eta_inlet=recouvrement_entree,
            combustor_pressure_loss=perte_pression_chambre,
            mass_flow_kg_s=debit_air_kg_s,
        ))
    except ValueError as exc:
        return json.dumps({"erreur": str(exc)}, ensure_ascii=False)
    return json.dumps(_round(res.to_dict()), ensure_ascii=False, indent=1)


@beta_tool
def atmosphere_standard(altitude_m: float) -> str:
    """Conditions ISA (température, pression, densité, vitesse du son) à une altitude.

    Args:
        altitude_m: Altitude géopotentielle en mètres (-1 000 à 32 000).
    """
    try:
        atm = isa_atmosphere(altitude_m)
    except ValueError as exc:
        return json.dumps({"erreur": str(exc)}, ensure_ascii=False)
    return json.dumps(_round(atm.__dict__), ensure_ascii=False)


@beta_tool
def rechercher_documentation(requete: str, nombre_resultats: int = 3) -> str:
    """Recherche dans la base documentaire interne sur les moteurs à réaction.

    Couvre : principes du cycle de Brayton, composants (entrée, compresseur,
    chambre, turbine, tuyère, réchauffe), matériaux et limites thermiques,
    certification (CS-E, Part 33, OACI), normes SAE, méthodes de conception,
    carburants. Citer la source retournée dans la réponse.

    Args:
        requete: Mots-clés ou question en français.
        nombre_resultats: Nombre de sections à retourner (1 à 6).
    """
    hits = _kb.search(requete, top_k=max(1, min(6, nombre_resultats)))
    if not hits:
        return json.dumps({"resultats": [], "documents_disponibles": _kb.list_documents()},
                          ensure_ascii=False)
    return json.dumps({
        "resultats": [
            {"source": s.source, "section": s.title, "score": round(score, 2), "contenu": s.preview()}
            for score, s in hits
        ]
    }, ensure_ascii=False, indent=1)


@beta_tool
def convertir_unites(valeur: float, de: str, vers: str) -> str:
    """Conversion d'unités courantes en propulsion.

    Unités supportées : poussée (N, kN, lbf, kgf), TSFC (kg/N/h, lb/lbf/h, g/kN/s),
    température (K, C, F), pression (Pa, kPa, bar, psi, atm), vitesse (m/s, km/h, kt, ft/s),
    longueur (m, ft, in), masse (kg, lb), débit (kg/s, lb/s).

    Args:
        valeur: Valeur numérique à convertir.
        de: Unité d'origine (ex. "lbf").
        vers: Unité cible (ex. "kN").
    """
    try:
        return json.dumps({"valeur": round(_convert(valeur, de, vers), 6), "unite": vers},
                          ensure_ascii=False)
    except ValueError as exc:
        return json.dumps({"erreur": str(exc)}, ensure_ascii=False)


# ---------------------------------------------------------------------------

_TO_SI: dict[str, tuple[str, float]] = {
    # poussée / force -> N
    "n": ("force", 1.0), "kn": ("force", 1e3), "lbf": ("force", 4.4482216), "kgf": ("force", 9.80665),
    # TSFC -> kg/N/h
    "kg/n/h": ("tsfc", 1.0), "lb/lbf/h": ("tsfc", 0.101972), "g/kn/s": ("tsfc", 3.6e-3),
    # pression -> Pa
    "pa": ("pressure", 1.0), "kpa": ("pressure", 1e3), "bar": ("pressure", 1e5),
    "psi": ("pressure", 6894.757), "atm": ("pressure", 101325.0),
    # vitesse -> m/s
    "m/s": ("speed", 1.0), "km/h": ("speed", 1 / 3.6), "kt": ("speed", 0.514444), "ft/s": ("speed", 0.3048),
    # longueur -> m
    "m": ("length", 1.0), "ft": ("length", 0.3048), "in": ("length", 0.0254),
    # masse -> kg
    "kg": ("mass", 1.0), "lb": ("mass", 0.45359237),
    # débit -> kg/s
    "kg/s": ("flow", 1.0), "lb/s": ("flow", 0.45359237),
}


def _convert(value: float, src: str, dst: str) -> float:
    s, d = src.strip().lower(), dst.strip().lower()
    temps = {"k", "c", "f", "°c", "°f"}
    if s in temps or d in temps:
        return _convert_temp(value, s.replace("°", ""), d.replace("°", ""))
    if s not in _TO_SI or d not in _TO_SI:
        raise ValueError(f"unité inconnue : {src!r} ou {dst!r}")
    (dim_s, k_s), (dim_d, k_d) = _TO_SI[s], _TO_SI[d]
    if dim_s != dim_d:
        raise ValueError(f"dimensions incompatibles : {src} ({dim_s}) vers {dst} ({dim_d})")
    return value * k_s / k_d


def _convert_temp(value: float, s: str, d: str) -> float:
    if s not in {"k", "c", "f"} or d not in {"k", "c", "f"}:
        raise ValueError("conversion de température : unités K, C ou F uniquement")
    kelvin = {"k": value, "c": value + 273.15, "f": (value - 32) * 5 / 9 + 273.15}[s]
    return {"k": kelvin, "c": kelvin - 273.15, "f": (kelvin - 273.15) * 9 / 5 + 32}[d]


def _round(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, float):
            out[k] = round(v, 6 if abs(v) < 1 else 3)
        else:
            out[k] = v
    return out


ALL_TOOLS = [analyser_cycle_turboreacteur, atmosphere_standard, rechercher_documentation, convertir_unites]
