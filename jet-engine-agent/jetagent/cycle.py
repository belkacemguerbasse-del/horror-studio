"""Analyse de cycle thermodynamique pour turboréacteurs (modèle paramétrique).

Hypothèses du modèle (gaz parfait, propriétés constantes par section) :
- Air froid (entrée + compresseur) : gamma_c = 1.4, cp_c = 1004.5 J/(kg.K)
- Gaz chauds (chambre + turbine + tuyère) : gamma_t = 1.33, cp_t = 1156 J/(kg.K)
- Pouvoir calorifique inférieur du kérosène Jet A-1 : 43.0 MJ/kg
- Rendements isentropiques et pertes de pression paramétrables.

Ce module est volontairement indépendant du modèle de langage : il s'agit
d'un calcul déterministe et vérifiable, exposé ensuite comme outil à l'agent.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict

R_AIR = 287.05  # J/(kg.K)
GAMMA_C = 1.4
CP_C = 1004.5
GAMMA_T = 1.33
CP_T = 1156.0
LHV_JET_A1 = 43.0e6  # J/kg
G0 = 9.80665


# ---------------------------------------------------------------------------
# Atmosphère standard (ISA) jusqu'à 32 km
# ---------------------------------------------------------------------------

@dataclass
class Atmosphere:
    altitude_m: float
    temperature_K: float
    pressure_Pa: float
    density_kg_m3: float
    speed_of_sound_m_s: float


def isa_atmosphere(altitude_m: float) -> Atmosphere:
    """Atmosphère standard internationale, de 0 à 32 000 m."""
    if altitude_m < -1000 or altitude_m > 32000:
        raise ValueError("altitude hors du domaine supporté (-1 000 m à 32 000 m)")

    t0, p0 = 288.15, 101325.0
    if altitude_m <= 11000:
        lapse = -0.0065
        t = t0 + lapse * altitude_m
        p = p0 * (t / t0) ** (-G0 / (lapse * R_AIR))
    elif altitude_m <= 20000:
        t11 = t0 - 0.0065 * 11000
        p11 = p0 * (t11 / t0) ** (-G0 / (-0.0065 * R_AIR))
        t = t11
        p = p11 * math.exp(-G0 * (altitude_m - 11000) / (R_AIR * t11))
    else:
        t11 = t0 - 0.0065 * 11000
        p11 = p0 * (t11 / t0) ** (-G0 / (-0.0065 * R_AIR))
        p20 = p11 * math.exp(-G0 * 9000 / (R_AIR * t11))
        lapse = 0.001
        t = t11 + lapse * (altitude_m - 20000)
        p = p20 * (t / t11) ** (-G0 / (lapse * R_AIR))

    rho = p / (R_AIR * t)
    a = math.sqrt(GAMMA_C * R_AIR * t)
    return Atmosphere(altitude_m, t, p, rho, a)


# ---------------------------------------------------------------------------
# Cycle turboréacteur simple flux
# ---------------------------------------------------------------------------

@dataclass
class TurbojetInputs:
    mach: float = 0.0
    altitude_m: float = 0.0
    pressure_ratio: float = 20.0          # taux de compression global (OPR)
    turbine_inlet_temp_K: float = 1500.0  # T4, température entrée turbine (TIT)
    eta_inlet: float = 0.97               # recouvrement de pression totale (Pt2/Pt0)
    eta_compressor: float = 0.88          # rendement isentropique
    eta_combustor: float = 0.99           # rendement de combustion
    combustor_pressure_loss: float = 0.04 # perte relative de pression dans la chambre
    eta_turbine: float = 0.90             # rendement isentropique
    eta_mechanical: float = 0.99          # rendement de transmission compresseur-turbine
    eta_nozzle: float = 0.98              # coefficient de vitesse de la tuyère
    mass_flow_kg_s: float | None = None   # débit d'air ; si None, résultats par kg/s
    # Post-combustion (réchauffe) : None = éteinte ; sinon température totale visée (Tt7)
    afterburner_temp_K: float | None = None
    eta_afterburner: float = 0.95         # rendement de combustion du canal de réchauffe
    afterburner_pressure_loss: float = 0.05  # perte relative de pression (allumée)
    # "convergent" (amorcée au-delà du NPR critique) ou "convergent_divergent"
    # (détente complète jusqu'à P0, géométrie variable supposée adaptée)
    nozzle_type: str = "convergent"


@dataclass
class TurbojetResults:
    # Conditions de vol
    T0_K: float
    P0_Pa: float
    V0_m_s: float
    # Stations (totales)
    Tt2_K: float
    Pt2_Pa: float
    Tt3_K: float
    Pt3_Pa: float
    Tt4_K: float
    Pt4_Pa: float
    Tt5_K: float
    Pt5_Pa: float
    Tt7_K: float
    Pt7_Pa: float
    # Combustion
    fuel_air_ratio: float               # chambre principale
    afterburner_fuel_air_ratio: float   # réchauffe (0 si éteinte)
    total_fuel_air_ratio: float
    afterburner_on: bool
    # Tuyère
    nozzle_type: str
    nozzle_pressure_ratio: float
    nozzle_choked: bool
    exhaust_velocity_m_s: float
    exhaust_temp_K: float
    exhaust_mach: float
    # Performances
    specific_thrust_N_per_kg_s: float
    tsfc_kg_per_N_h: float
    thermal_efficiency: float
    propulsive_efficiency: float
    overall_efficiency: float
    # Si débit fourni
    thrust_N: float | None
    fuel_flow_kg_s: float | None
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_turbojet(inp: TurbojetInputs) -> TurbojetResults:
    """Analyse paramétrique d'un turboréacteur simple flux, tuyère convergente.

    Méthode : analyse de cycle « réel » au sens de Mattingly (Elements of
    Propulsion), avec rendements composants et propriétés distinctes
    air froid / gaz chauds. Post-combustion optionnelle (station 5 -> 7).
    Tuyère convergente : si le rapport de pression disponible dépasse le
    rapport critique, la tuyère est amorcée (Mach 1 en sortie) et la poussée
    de pression est ajoutée. Tuyère convergente-divergente : détente complète
    jusqu'à la pression ambiante (section de sortie supposée adaptée).
    """
    warnings: list[str] = []
    _validate(inp, warnings)

    atm = isa_atmosphere(inp.altitude_m)
    T0, P0, a0 = atm.temperature_K, atm.pressure_Pa, atm.speed_of_sound_m_s
    V0 = inp.mach * a0

    # Station 0 -> 2 : entrée d'air (compression dynamique + pertes)
    tau_r = 1 + (GAMMA_C - 1) / 2 * inp.mach**2
    pi_r = tau_r ** (GAMMA_C / (GAMMA_C - 1))
    Tt2 = T0 * tau_r
    Pt2 = P0 * pi_r * inp.eta_inlet

    # Station 2 -> 3 : compresseur
    tau_c_ideal = inp.pressure_ratio ** ((GAMMA_C - 1) / GAMMA_C)
    tau_c = 1 + (tau_c_ideal - 1) / inp.eta_compressor
    Tt3 = Tt2 * tau_c
    Pt3 = Pt2 * inp.pressure_ratio

    # Station 3 -> 4 : chambre de combustion
    Tt4 = inp.turbine_inlet_temp_K
    if Tt4 <= Tt3:
        raise ValueError(
            f"T4 ({Tt4:.0f} K) doit être supérieure à la température de sortie "
            f"compresseur T3 ({Tt3:.0f} K) : augmentez T4 ou réduisez le taux de compression."
        )
    f = (CP_T * Tt4 - CP_C * Tt3) / (inp.eta_combustor * LHV_JET_A1 - CP_T * Tt4)
    Pt4 = Pt3 * (1 - inp.combustor_pressure_loss)

    # Station 4 -> 5 : turbine (équilibre de puissance avec le compresseur)
    work_c = CP_C * (Tt3 - Tt2)  # J/kg d'air
    delta_Tt_turbine = work_c / (inp.eta_mechanical * (1 + f) * CP_T)
    Tt5 = Tt4 - delta_Tt_turbine
    tau_t = Tt5 / Tt4
    tau_t_ideal = 1 - (1 - tau_t) / inp.eta_turbine
    if tau_t_ideal <= 0:
        raise ValueError("la turbine ne peut pas fournir la puissance demandée par le compresseur")
    pi_t = tau_t_ideal ** (GAMMA_T / (GAMMA_T - 1))
    Pt5 = Pt4 * pi_t

    # Station 5 -> 7 : post-combustion (réchauffe) éventuelle
    if inp.afterburner_temp_K is not None:
        Tt7 = inp.afterburner_temp_K
        if Tt7 <= Tt5:
            raise ValueError(
                f"la température de réchauffe ({Tt7:.0f} K) doit dépasser la température "
                f"de sortie turbine T5 ({Tt5:.0f} K)."
            )
        f_ab = (1 + f) * CP_T * (Tt7 - Tt5) / (inp.eta_afterburner * LHV_JET_A1 - CP_T * Tt7)
        Pt7 = Pt5 * (1 - inp.afterburner_pressure_loss)
        afterburner_on = True
    else:
        Tt7, Pt7, f_ab, afterburner_on = Tt5, Pt5, 0.0, False
    f_total = f + f_ab

    # Station 7 -> 9 : tuyère
    npr = Pt7 / P0
    critical_pr = ((GAMMA_T + 1) / 2) ** (GAMMA_T / (GAMMA_T - 1))
    if npr < 1.0:
        raise ValueError(
            "pression totale en entrée de tuyère inférieure à la pression ambiante : "
            "le cycle ne produit pas de poussée (T4 trop basse ou rendements trop faibles)."
        )

    if inp.nozzle_type == "convergent_divergent":
        # Détente complète : P9 = P0, section de sortie adaptée (pas de poussée de pression)
        choked = npr > critical_pr
        P9 = P0
        T9 = Tt7 * (P9 / Pt7) ** ((GAMMA_T - 1) / GAMMA_T)
        V9_ideal = math.sqrt(max(2 * CP_T * (Tt7 - T9), 0.0))
        V9 = inp.eta_nozzle * V9_ideal
        M9 = V9 / math.sqrt(GAMMA_T * R_AIR * T9) if T9 > 0 else 0.0
        pressure_thrust = 0.0
    elif npr > critical_pr:
        choked = True
        M9 = 1.0
        T9 = Tt7 * 2 / (GAMMA_T + 1)
        P9 = Pt7 / critical_pr
        V9_ideal = math.sqrt(GAMMA_T * R_AIR * T9)
        V9 = inp.eta_nozzle * V9_ideal
        # Poussée de pression par unité de débit : (P9 - P0) * A9 / mdot9
        rho9 = P9 / (R_AIR * T9)
        area_per_mass = 1.0 / (rho9 * V9)
        pressure_thrust = (P9 - P0) * area_per_mass
    else:
        choked = False
        P9 = P0
        T9 = Tt7 * (P9 / Pt7) ** ((GAMMA_T - 1) / GAMMA_T)
        V9_ideal = math.sqrt(max(2 * CP_T * (Tt7 - T9), 0.0))
        V9 = inp.eta_nozzle * V9_ideal
        M9 = V9 / math.sqrt(GAMMA_T * R_AIR * T9) if T9 > 0 else 0.0
        pressure_thrust = 0.0

    # Performances
    specific_thrust = (1 + f_total) * V9 - V0 + pressure_thrust  # N par kg/s d'air
    if specific_thrust <= 0:
        raise ValueError("poussée spécifique nulle ou négative : point de fonctionnement non viable")
    tsfc = f_total / specific_thrust * 3600  # kg/(N.h)

    # Vitesse d'éjection « effective » (équivalent détente complète) : la poussée
    # de pression d'une tuyère amorcée est convertie en quantité de mouvement.
    V9_eff = V9 + pressure_thrust / (1 + f_total)
    kinetic_power = 0.5 * ((1 + f_total) * V9_eff**2 - V0**2)
    fuel_power = f_total * LHV_JET_A1
    thermal_eff = kinetic_power / fuel_power if fuel_power > 0 else 0.0
    propulsive_eff = (specific_thrust * V0) / kinetic_power if kinetic_power > 0 and V0 > 0 else 0.0
    overall_eff = thermal_eff * propulsive_eff

    thrust = fuel_flow = None
    if inp.mass_flow_kg_s is not None:
        thrust = specific_thrust * inp.mass_flow_kg_s
        fuel_flow = f_total * inp.mass_flow_kg_s

    _post_warnings(inp, Tt3, Tt5, f, f_total, npr, warnings)

    return TurbojetResults(
        T0_K=T0, P0_Pa=P0, V0_m_s=V0,
        Tt2_K=Tt2, Pt2_Pa=Pt2, Tt3_K=Tt3, Pt3_Pa=Pt3,
        Tt4_K=Tt4, Pt4_Pa=Pt4, Tt5_K=Tt5, Pt5_Pa=Pt5, Tt7_K=Tt7, Pt7_Pa=Pt7,
        fuel_air_ratio=f, afterburner_fuel_air_ratio=f_ab, total_fuel_air_ratio=f_total,
        afterburner_on=afterburner_on,
        nozzle_type=inp.nozzle_type,
        nozzle_pressure_ratio=npr, nozzle_choked=choked,
        exhaust_velocity_m_s=V9, exhaust_temp_K=T9, exhaust_mach=M9,
        specific_thrust_N_per_kg_s=specific_thrust,
        tsfc_kg_per_N_h=tsfc,
        thermal_efficiency=thermal_eff,
        propulsive_efficiency=propulsive_eff,
        overall_efficiency=overall_eff,
        thrust_N=thrust, fuel_flow_kg_s=fuel_flow,
        warnings=warnings,
    )


def _validate(inp: TurbojetInputs, warnings: list[str]) -> None:
    if inp.mach < 0:
        raise ValueError("le nombre de Mach doit être positif ou nul")
    if inp.pressure_ratio <= 1:
        raise ValueError("le taux de compression doit être supérieur à 1")
    if inp.turbine_inlet_temp_K < 600:
        raise ValueError("température entrée turbine trop basse pour un turboréacteur")
    for name in ("eta_inlet", "eta_compressor", "eta_combustor", "eta_turbine",
                 "eta_mechanical", "eta_nozzle"):
        v = getattr(inp, name)
        if not 0 < v <= 1:
            raise ValueError(f"{name} doit être dans ]0, 1]")
    if not 0 <= inp.combustor_pressure_loss < 0.5:
        raise ValueError("la perte de pression chambre doit être dans [0, 0.5[")
    if inp.mass_flow_kg_s is not None and inp.mass_flow_kg_s <= 0:
        raise ValueError("le débit d'air doit être strictement positif")
    if inp.nozzle_type not in ("convergent", "convergent_divergent"):
        raise ValueError("nozzle_type doit être 'convergent' ou 'convergent_divergent'")
    if inp.afterburner_temp_K is not None:
        if not 0 < inp.eta_afterburner <= 1:
            raise ValueError("eta_afterburner doit être dans ]0, 1]")
        if not 0 <= inp.afterburner_pressure_loss < 0.5:
            raise ValueError("la perte de pression de réchauffe doit être dans [0, 0.5[")
        if inp.afterburner_temp_K > 2300:
            raise ValueError("température de réchauffe > 2300 K : au-delà de la stoechiométrie du kérosène")
    if inp.mach > 3.5:
        warnings.append("Mach > 3.5 : un turboréacteur classique n'est plus adapté (statoréacteur recommandé).")


def _post_warnings(inp: TurbojetInputs, Tt3: float, Tt5: float, f: float, f_total: float,
                   npr: float, warnings: list[str]) -> None:
    if inp.turbine_inlet_temp_K > 1750:
        warnings.append(
            "T4 > 1750 K : nécessite aubes monocristallines refroidies + revêtement barrière thermique (TBC)."
        )
    if inp.turbine_inlet_temp_K > 2000:
        warnings.append("T4 > 2000 K : au-delà de l'état de l'art des moteurs en service (≈ 1900-2000 K).")
    if Tt3 > 950:
        warnings.append(
            f"T3 = {Tt3:.0f} K : au-delà de ~950 K, les derniers étages HP exigent des alliages de nickel "
            "(limite des alliages de titane ≈ 870-900 K)."
        )
    if f > 0.045:
        warnings.append("Richesse élevée (f > 0,045) : risque de dépassement stoechiométrique local / NOx élevés.")
    if inp.pressure_ratio > 45:
        warnings.append("OPR > 45 : nécessite une architecture multi-corps et un refroidissement HP conséquent.")
    if f_total > 0.060:
        warnings.append("Richesse totale > 0,060 : proche de la stoechiométrie (0,068), rendement de réchauffe dégradé.")
    if inp.afterburner_temp_K is not None and inp.afterburner_temp_K > 2100:
        warnings.append("Réchauffe > 2100 K : refroidissement du canal et de la tuyère par film obligatoire.")
    if inp.nozzle_type == "convergent" and npr > 4.0:
        warnings.append(
            f"NPR = {npr:.1f} avec tuyère convergente : la sous-détente coûte plusieurs % de poussée, "
            "une tuyère convergente-divergente à géométrie variable est recommandée."
        )
    if inp.nozzle_type == "convergent_divergent" and npr < 2.5:
        warnings.append("NPR < 2,5 avec tuyère C-D : gain négligeable, une tuyère convergente simple suffit.")
