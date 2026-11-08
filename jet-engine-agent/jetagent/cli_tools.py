"""Accès en ligne de commande aux outils déterministes, SANS modèle ni clé API.

Permet d'utiliser les calculs depuis un terminal, un script, ou depuis Claude
Code (via la skill `jet-engine-agent`) où le modèle de langage est déjà fourni
par l'application : seul le calcul est délégué à ce programme.

Exemples :
    python -m jetagent.cli_tools cycle --mach 0.9 --altitude 11000 --opr 13 --t4 1650
    python -m jetagent.cli_tools cycle --opr 8 --t4 1600 --mach 2 --altitude 15000 \\
        --rechauffe 2000 --tuyere convergent_divergent --debit 70
    python -m jetagent.cli_tools isa 11000
    python -m jetagent.cli_tools doc "afterburner turbojet TSFC"
    python -m jetagent.cli_tools convert 10000 lbf kN
    python -m jetagent.cli_tools schemas        # définitions JSON des outils
"""

from __future__ import annotations

import argparse
import json
import sys

from .tools import (
    ALL_TOOLS,
    analyser_cycle_turboreacteur,
    atmosphere_standard,
    convertir_unites,
    rechercher_documentation,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m jetagent.cli_tools",
                                     description="Outils moteurs à réaction (sans API).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("cycle", help="analyse de cycle turboréacteur")
    c.add_argument("--mach", type=float, default=0.0)
    c.add_argument("--altitude", type=float, default=0.0, help="m")
    c.add_argument("--opr", type=float, default=20.0, help="taux de compression global")
    c.add_argument("--t4", type=float, default=1500.0, help="température entrée turbine, K")
    c.add_argument("--eta-c", type=float, default=0.88)
    c.add_argument("--eta-t", type=float, default=0.90)
    c.add_argument("--eta-inlet", type=float, default=0.97)
    c.add_argument("--perte-chambre", type=float, default=0.04)
    c.add_argument("--debit", type=float, default=None, help="débit d'air, kg/s")
    c.add_argument("--rechauffe", type=float, default=None, help="Tt7 post-combustion, K")
    c.add_argument("--tuyere", choices=["convergent", "convergent_divergent"], default="convergent")

    i = sub.add_parser("isa", help="atmosphère standard")
    i.add_argument("altitude", type=float, help="m")

    d = sub.add_parser("doc", help="recherche documentaire")
    d.add_argument("requete")
    d.add_argument("-n", type=int, default=3)

    v = sub.add_parser("convert", help="conversion d'unités")
    v.add_argument("valeur", type=float)
    v.add_argument("de")
    v.add_argument("vers")

    sub.add_parser("schemas", help="définitions JSON des outils exposés au modèle")

    a = parser.parse_args(argv)
    if a.cmd == "cycle":
        out = analyser_cycle_turboreacteur.call({
            "mach": a.mach, "altitude_m": a.altitude, "taux_compression": a.opr,
            "temperature_entree_turbine_K": a.t4, "rendement_compresseur": a.eta_c,
            "rendement_turbine": a.eta_t, "recouvrement_entree": a.eta_inlet,
            "perte_pression_chambre": a.perte_chambre, "debit_air_kg_s": a.debit,
            "temperature_rechauffe_K": a.rechauffe, "type_tuyere": a.tuyere,
        })
    elif a.cmd == "isa":
        out = atmosphere_standard.call({"altitude_m": a.altitude})
    elif a.cmd == "doc":
        out = rechercher_documentation.call({"requete": a.requete, "nombre_resultats": a.n})
    elif a.cmd == "convert":
        out = convertir_unites.call({"valeur": a.valeur, "de": a.de, "vers": a.vers})
    else:
        out = json.dumps([t.to_dict() for t in ALL_TOOLS], ensure_ascii=False, indent=1)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
