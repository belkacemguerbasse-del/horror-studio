"""Modèle 3D paramétrique d'un micro-turboréacteur (micro turbojet) pour aéromodélisme.

Le modèle est dimensionné à partir de la poussée visée au point fixe : le cycle
thermodynamique (jetagent.cycle) fournit la poussée spécifique, donc le débit
d'air, la vitesse et la température d'éjection, donc la section de sortie de
tuyère. Les autres cotes suivent des ratios typiques des micro-turbines de
100 à 600 N (rouet centrifuge, turbine axiale mono-étage, chambre annulaire).

Il s'agit d'un modèle d'implantation (layout) : enveloppes, positions, sections
et nombre d'aubes sont réalistes ; les profils d'aubes sont des plaques
simplifiées, PAS des profils aérodynamiques dessinés. Il sert à visualiser,
intégrer dans une cellule, imprimer une maquette, ou servir de squelette à une
conception détaillée (ligne moyenne, CFD, calcul rotor).

Usage :
    python -m jetagent.cad --poussee 350 --out sorties/micro350
    python -m jetagent.cad --poussee 350 --out sorties/micro350 --sans-visionneuse
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path

from ..cycle import GAMMA_T, R_AIR, TurbojetInputs, analyze_turbojet

# Hypothèses composants d'une micro-turbine RC (voir réponse de dimensionnement)
RC_MICROTURBINE = dict(
    pressure_ratio=3.5,
    turbine_inlet_temp_K=1150.0,
    eta_compressor=0.76,
    eta_turbine=0.82,
    eta_inlet=0.98,
    combustor_pressure_loss=0.06,
)
INLET_AXIAL_VELOCITY = 100.0  # m/s à l'entrée du rouet
RHO_SL = 1.225


@dataclass
class EngineDimensions:
    """Cotes principales en millimètres, et grandeurs de cycle associées."""
    thrust_N: float
    mass_flow_kg_s: float
    fuel_flow_kg_s: float
    tsfc_kg_per_N_h: float
    exhaust_velocity_m_s: float
    exhaust_temp_K: float
    exit_area_cm2: float
    inlet_diameter: float
    compressor_tip_diameter: float
    casing_diameter: float
    turbine_tip_diameter: float
    turbine_hub_diameter: float
    nozzle_exit_diameter: float
    nozzle_cone_exit_diameter: float
    overall_length: float
    shaft_diameter: float
    compressor_blades: int
    diffuser_vanes: int
    ngv_count: int
    turbine_blades: int
    vaporizer_tubes: int

    def to_dict(self) -> dict:
        return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in asdict(self).items()}


def size_engine(thrust_N: float) -> EngineDimensions:
    """Dimensionnement : du cycle aux cotes principales (mm)."""
    if thrust_N <= 0:
        raise ValueError("la poussée doit être strictement positive")
    cyc = analyze_turbojet(TurbojetInputs(mach=0.0, altitude_m=0.0, **RC_MICROTURBINE))
    mdot = thrust_N / cyc.specific_thrust_N_per_kg_s
    a_in = mdot / (RHO_SL * INLET_AXIAL_VELOCITY)
    d_in = math.sqrt(4 * a_in / math.pi) * 1000

    # Section de sortie tuyère (détente complète si non amorcée, sinon section au col)
    f = cyc.total_fuel_air_ratio
    rho9 = (cyc.P0_Pa if not cyc.nozzle_choked else cyc.Pt7_Pa / ((GAMMA_T + 1) / 2) ** (GAMMA_T / (GAMMA_T - 1))) \
        / (R_AIR * cyc.exhaust_temp_K)
    a9 = mdot * (1 + f) / (rho9 * cyc.exhaust_velocity_m_s)  # m²
    cone_ratio = 0.30  # rayon du cône central / rayon de sortie
    r_exit = math.sqrt(a9 / (math.pi * (1 - cone_ratio**2))) * 1000

    d_c = 1.25 * d_in
    d_case = 1.35 * d_c
    d_t = 0.85 * d_c
    length = 3.3 * d_c

    return EngineDimensions(
        thrust_N=thrust_N,
        mass_flow_kg_s=mdot,
        fuel_flow_kg_s=f * mdot,
        tsfc_kg_per_N_h=cyc.tsfc_kg_per_N_h,
        exhaust_velocity_m_s=cyc.exhaust_velocity_m_s,
        exhaust_temp_K=cyc.exhaust_temp_K,
        exit_area_cm2=a9 * 1e4,
        inlet_diameter=d_in,
        compressor_tip_diameter=d_c,
        casing_diameter=d_case,
        turbine_tip_diameter=d_t,
        turbine_hub_diameter=0.62 * d_t,
        nozzle_exit_diameter=2 * r_exit,
        nozzle_cone_exit_diameter=2 * r_exit * cone_ratio,
        overall_length=length,
        shaft_diameter=0.16 * d_c,
        compressor_blades=11,
        diffuser_vanes=17,
        ngv_count=13,
        turbine_blades=19,
        vaporizer_tubes=6,
    )


# ---------------------------------------------------------------------------
# Construction CadQuery
# ---------------------------------------------------------------------------

def _hub_profile(x1: float, lc: float, r0: float, rc: float, n: int = 14) -> list[tuple[float, float]]:
    """Moyeu du rouet : quart d'ellipse de (x1, r0) à (x1+lc, rc), tangente radiale en sortie."""
    pts = []
    for i in range(n + 1):
        u = i / n
        pts.append((x1 + u * lc, r0 + (rc - r0) * (1 - math.sqrt(max(0.0, 1 - u * u)))))
    return pts


def _shroud_profile(x1: float, lc: float, r_in: float, rc: float, n: int = 14) -> list[tuple[float, float]]:
    """Carter du rouet (shroud) : de (x1, r_in) à (x1+0.85 lc, rc)."""
    ls = 0.85 * lc
    pts = []
    for i in range(n + 1):
        u = i / n
        pts.append((x1 + u * ls, r_in + (rc - r_in) * (1 - math.sqrt(max(0.0, 1 - u * u)))))
    return pts


def _dedupe(points: list[tuple[float, float]], eps: float = 1e-6) -> list[tuple[float, float]]:
    """Supprime les points consécutifs identiques (arêtes de longueur nulle refusées par OCC)."""
    out: list[tuple[float, float]] = []
    for pt in points:
        if not out or abs(pt[0] - out[-1][0]) > eps or abs(pt[1] - out[-1][1]) > eps:
            out.append(pt)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) <= eps and abs(out[0][1] - out[-1][1]) <= eps:
        out.pop()
    return out


def build_engine(dims: EngineDimensions):
    """Construit les pièces ; retourne {nom: (Workplane, couleur_rgb)} dans l'ordre d'assemblage."""
    import cadquery as cq

    D = dims
    Rc = D.compressor_tip_diameter / 2
    Rcase = D.casing_diameter / 2
    Rt = D.turbine_tip_diameter / 2
    Rth = D.turbine_hub_diameter / 2
    Rin = D.inlet_diameter / 2
    Dc = D.compressor_tip_diameter
    wall = max(1.5, 0.012 * Dc)
    r_shaft = D.shaft_diameter / 2
    r_tun = r_shaft + 0.07 * Dc  # tunnel d'arbre (logement roulements)
    r0 = 0.28 * Rin              # rayon du nez de moyeu

    # Positions axiales (mm)
    x_nose = -0.25 * Dc
    x1 = 0.0                      # entrée du rouet
    Lb = 0.30 * Dc                # longueur du cornet d'entrée (en amont de x1)
    Lc = 0.45 * Dc                # longueur axiale du rouet
    x_back = x1 + Lc              # face arrière du rouet
    x_cc0 = x_back + 0.12 * Dc    # dôme de chambre
    Lcc = 1.30 * Dc
    x_cc1 = x_cc0 + Lcc           # sortie chambre / entrée distributeur
    Lngv = 0.12 * Dc
    x_t0 = x_cc1 + Lngv + 0.02 * Dc  # bord d'attaque turbine
    Lt = 0.10 * Dc
    x_t1 = x_t0 + Lt
    x_n0 = x_t1 + 0.06 * Dc       # début tuyère
    Ln = 0.60 * Dc
    x_n1 = x_n0 + Ln              # sortie
    Re = D.nozzle_exit_diameter / 2
    Rcone = D.nozzle_cone_exit_diameter / 2

    parts: dict[str, tuple] = {}

    # 1. Cornet d'entrée (bellmouth) : révolution d'un quart de tore épais
    bell = []
    nb = 10
    for i in range(nb + 1):
        a = math.pi / 2 * i / nb
        bell.append((x1 - Lb * math.cos(a) * 0.9, Rin + Lb * 0.9 * (1 - math.sin(a))))
    shroud = _shroud_profile(x1, Lc, Rin, Rc)
    outer = [(x, r + wall) for (x, r) in shroud]
    prof = _dedupe(bell + shroud + outer[::-1] + [(bell[0][0], bell[0][1] + wall)])
    front_cover = cq.Workplane("XY").polyline(prof).close().revolve(360, (0, 0, 0), (1, 0, 0))
    # plaque avant reliant le shroud au carter
    xs = shroud[-1][0]
    plate = (cq.Workplane("YZ").circle(Rcase).circle(Rc + wall).extrude(2.0).translate((xs - 2.0, 0, 0)))
    parts["carter_avant"] = (front_cover.union(plate), (0.75, 0.75, 0.78))

    # 2. Nez de démarreur (cône central d'entrée)
    nose = (cq.Workplane("XY").polyline([(x_nose, 0), (x1, 0), (x1, r0), (x_nose + 0.08 * Dc, r0 * 0.55)])
            .close().revolve(360, (0, 0, 0), (1, 0, 0)))
    parts["nez_demarreur"] = (nose, (0.25, 0.25, 0.28))

    # 3. Rouet centrifuge : moyeu + aubes
    hub_pts = _hub_profile(x1, Lc, r0, Rc)
    hub_prof = _dedupe([(x1, 0.0)] + hub_pts + [(x_back, 0.0)])
    hub = cq.Workplane("XY").polyline(hub_prof).close().revolve(360, (0, 0, 0), (1, 0, 0))
    # aube : bord d'attaque de (x1, r0) à (x1, Rin), extrados le long du shroud, sortie radiale en Rc
    blade_prof = _dedupe(hub_pts + [(x_back - 0.02 * Dc, Rc - 0.3)] + shroud[::-1])
    tb = max(1.2, 0.012 * Dc)
    blade = cq.Workplane("XY").polyline(blade_prof).close().extrude(tb / 2, both=True)
    wheel = hub
    for i in range(D.compressor_blades):
        wheel = wheel.union(blade.rotate((0, 0, 0), (1, 0, 0), 360.0 * i / D.compressor_blades))
    parts["rouet_compresseur"] = (wheel, (0.85, 0.85, 0.88))

    # 4. Diffuseur radial : anneau à canaux
    diff = (cq.Workplane("YZ").circle(Rcase - wall - 0.5).circle(Rc + 1.0).extrude(0.15 * Dc)
            .translate((xs, 0, 0)))
    slot = (cq.Workplane("XY").box(0.15 * Dc + 1, (Rcase - Rc), 0.08 * Dc)
            .translate((xs + 0.075 * Dc, (Rc + Rcase) / 2, 0)))
    for i in range(D.diffuser_vanes):
        diff = diff.cut(slot.rotate((0, 0, 0), (1, 0, 0), 360.0 * i / D.diffuser_vanes + 8))
    parts["diffuseur"] = (diff, (0.55, 0.58, 0.62))

    # 5. Carter principal : tube du diffuseur jusqu'à la turbine
    casing = (cq.Workplane("YZ").circle(Rcase).circle(Rcase - wall).extrude(x_n0 - xs).translate((xs, 0, 0)))
    parts["carter"] = (casing, (0.70, 0.70, 0.74))

    # 6. Tunnel d'arbre et arbre
    tunnel = (cq.Workplane("YZ").circle(r_tun).circle(r_tun - wall).extrude(x_t0 - 2 - x_back)
              .translate((x_back, 0, 0)))
    bearing = cq.Workplane("YZ").circle(r_tun - wall + 0.1).circle(r_shaft - 0.1).extrude(0.06 * Dc)
    tunnel = tunnel.union(bearing.translate((x_back + 0.02 * Dc, 0, 0))).union(
        bearing.translate((x_t0 - 2 - 0.08 * Dc, 0, 0)))
    parts["tunnel_arbre_roulements"] = (tunnel, (0.45, 0.45, 0.50))
    shaft = (cq.Workplane("YZ").circle(r_shaft).extrude(x_t1 + 0.05 * Dc - (x1 + 0.3 * Lc))
             .translate((x1 + 0.3 * Lc, 0, 0)))
    parts["arbre"] = (shaft, (0.35, 0.35, 0.38))

    # 7. Chambre de combustion annulaire : viroles interne / externe, dôme, vaporisateurs
    Ro = Rcase - wall - 0.06 * Dc
    Ri = r_tun + 0.07 * Dc
    tl = 0.8
    outer_liner = cq.Workplane("YZ").circle(Ro).circle(Ro - tl).extrude(Lcc).translate((x_cc0, 0, 0))
    inner_liner = cq.Workplane("YZ").circle(Ri + tl).circle(Ri).extrude(Lcc).translate((x_cc0, 0, 0))
    dome = cq.Workplane("YZ").circle(Ro).circle(Ri).extrude(tl).translate((x_cc0, 0, 0))

    def radial_cutter(x: float, r_center: float, radius: float, depth: float = 3.0):
        c = cq.Workplane("YZ").circle(radius).extrude(2 * depth).translate((-depth, 0, 0))
        c = c.rotate((0, 0, 0), (0, 0, 1), 90)  # axe X -> axe Y (radial)
        return c.translate((x, r_center, 0))

    rows_outer = [(x_cc0 + 0.30 * Lcc, 0.028 * Dc, 12), (x_cc0 + 0.58 * Lcc, 0.030 * Dc, 12),
                  (x_cc0 + 0.84 * Lcc, 0.045 * Dc, 8)]
    for x, rh, n in rows_outer:
        for i in range(n):
            outer_liner = outer_liner.cut(radial_cutter(x, Ro - tl / 2, rh)
                                          .rotate((0, 0, 0), (1, 0, 0), 360.0 * i / n))
    rows_inner = [(x_cc0 + 0.35 * Lcc, 0.022 * Dc, 10), (x_cc0 + 0.70 * Lcc, 0.025 * Dc, 10)]
    for x, rh, n in rows_inner:
        for i in range(n):
            inner_liner = inner_liner.cut(radial_cutter(x, Ri + tl / 2, rh)
                                          .rotate((0, 0, 0), (1, 0, 0), 360.0 * i / n + 18))
    combustor = outer_liner.union(inner_liner).union(dome)
    # tubes vaporisateurs : traversent le dôme, débouchent vers l'arrière dans la zone primaire
    rv = 0.028 * Dc
    r_mid = (Ro + Ri) / 2
    tube = (cq.Workplane("YZ").circle(rv).circle(rv - 0.5).extrude(0.42 * Lcc)
            .translate((x_cc0 - 0.12 * Lcc, r_mid, 0)))
    for i in range(D.vaporizer_tubes):
        combustor = combustor.union(tube.rotate((0, 0, 0), (1, 0, 0), 360.0 * i / D.vaporizer_tubes))
    parts["chambre_combustion"] = (combustor, (0.80, 0.55, 0.30))

    # 8. Distributeur de turbine (NGV)
    ngv_ring_o = cq.Workplane("YZ").circle(Rt + wall).circle(Rt).extrude(Lngv).translate((x_cc1, 0, 0))
    ngv_ring_i = cq.Workplane("YZ").circle(Rth).circle(Rth - wall).extrude(Lngv).translate((x_cc1, 0, 0))
    ngv = ngv_ring_o.union(ngv_ring_i)
    vane = (cq.Workplane("XY").box(Lngv * 0.95, Rt - Rth + 0.4, 1.2)
            .rotate((0, 0, 0), (0, 1, 0), 55)
            .translate((x_cc1 + Lngv / 2, (Rt + Rth) / 2, 0)))
    for i in range(D.ngv_count):
        ngv = ngv.union(vane.rotate((0, 0, 0), (1, 0, 0), 360.0 * i / D.ngv_count))
    parts["distributeur_turbine"] = (ngv, (0.60, 0.50, 0.45))

    # 9. Roue de turbine : disque + aubes
    disk_prof = [(x_t0, 0), (x_t0, Rth), (x_t1, Rth), (x_t1, Rth * 0.6), (x_t1 + 0.05 * Dc, r_shaft + 2),
                 (x_t1 + 0.05 * Dc, 0)]
    disk = cq.Workplane("XY").polyline(disk_prof).close().revolve(360, (0, 0, 0), (1, 0, 0))
    tblade = (cq.Workplane("XY").box(Lt * 0.9, Rt - Rth - 0.6, 1.2)
              .rotate((0, 0, 0), (0, 1, 0), -35)
              .translate((x_t0 + Lt / 2, (Rt + Rth) / 2 - 0.3, 0)))
    turbine = disk
    for i in range(D.turbine_blades):
        turbine = turbine.union(tblade.rotate((0, 0, 0), (1, 0, 0), 360.0 * i / D.turbine_blades))
    parts["roue_turbine"] = (turbine, (0.78, 0.70, 0.55))

    # 10. Tuyère : cône externe convergent + cône central
    noz_prof = [(x_n0, Rcase - wall), (x_n1, Re), (x_n1, Re + 1.2), (x_n0, Rcase)]
    nozzle = cq.Workplane("XY").polyline(noz_prof).close().revolve(360, (0, 0, 0), (1, 0, 0))
    parts["tuyere"] = (nozzle, (0.62, 0.62, 0.66))
    cone_prof = [(x_t1 + 0.05 * Dc, 0), (x_t1 + 0.05 * Dc, Rth * 0.85), (x_n1, Rcone), (x_n1, 0)]
    cone = cq.Workplane("XY").polyline(cone_prof).close().revolve(360, (0, 0, 0), (1, 0, 0))
    parts["cone_central_tuyere"] = (cone, (0.50, 0.50, 0.54))

    return parts


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

def export_all(dims: EngineDimensions, out_dir: Path, viewer: bool = True) -> dict[str, str]:
    import cadquery as cq
    from cadquery import exporters

    out_dir.mkdir(parents=True, exist_ok=True)
    parts = build_engine(dims)
    tag = f"micro_turbojet_{dims.thrust_N:.0f}N"
    written: dict[str, str] = {}

    # STEP d'assemblage (pièces nommées et colorées)
    assy = cq.Assembly(name=tag)
    for name, (wp, rgb) in parts.items():
        assy.add(wp, name=name, color=cq.Color(*rgb))
    step_path = out_dir / f"{tag}.step"
    assy.save(str(step_path))
    written["step"] = str(step_path)

    # STL complet et par pièce
    shapes = [wp.val() for wp, _ in parts.values()]
    compound = cq.Compound.makeCompound(shapes)
    stl_path = out_dir / f"{tag}.stl"
    exporters.export(cq.Workplane().add(compound), str(stl_path), tolerance=0.05, angularTolerance=0.15)
    written["stl"] = str(stl_path)
    parts_dir = out_dir / "pieces"
    parts_dir.mkdir(exist_ok=True)
    for name, (wp, _) in parts.items():
        exporters.export(wp, str(parts_dir / f"{name}.stl"), tolerance=0.05, angularTolerance=0.15)
    written["pieces_stl"] = str(parts_dir)

    # Vues au trait (lignes cachées retirées) : moteur à l'horizontale, isométrie 3/4 avant
    half = cq.Workplane("XY").box(4000, 4000, 4000).translate((0, 0, 2000))
    cut_shapes = [wp.cut(half).val() for wp, _ in parts.values()]
    svg_opt = {"projectionDir": (-0.55, 0.45, 0.70), "width": 1400, "height": 700,
               "showHidden": False, "strokeWidth": 0.35, "marginLeft": 30, "marginTop": 30}
    svg_section = out_dir / f"{tag}_coupe.svg"
    exporters.export(cq.Workplane().add(cq.Compound.makeCompound(cut_shapes)), str(svg_section), opt=svg_opt)
    written["coupe_svg"] = str(svg_section)
    svg_ext = out_dir / f"{tag}_exterieur.svg"
    exporters.export(cq.Workplane().add(compound), str(svg_ext), opt=svg_opt)
    written["exterieur_svg"] = str(svg_ext)

    # Cotes et cycle
    dims_path = out_dir / f"{tag}_cotes.json"
    dims_path.write_text(json.dumps(dims.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
    written["cotes_json"] = str(dims_path)

    # Visionneuse 3D interactive autonome
    if viewer:
        from .viewer import export_viewer
        html_path = export_viewer(parts, cut_shapes, dims, out_dir / f"{tag}_visionneuse.html",
                                  title=f"Micro-turboréacteur {dims.thrust_N:.0f} N")
        written["visionneuse_html"] = str(html_path)
    return written


def main(argv: list[str] | None = None) -> int:
    import argparse
    import time

    p = argparse.ArgumentParser(prog="python -m jetagent.cad",
                                description="Modèle 3D paramétrique d'un micro-turboréacteur.")
    p.add_argument("--poussee", type=float, default=350.0, help="poussée au point fixe, N")
    p.add_argument("--out", default="sorties/micro_turbojet", help="dossier de sortie")
    p.add_argument("--sans-visionneuse", action="store_true", help="ne pas générer la page HTML 3D")
    p.add_argument("--cotes-seules", action="store_true", help="afficher les cotes sans construire la CAO")
    a = p.parse_args(argv)

    dims = size_engine(a.poussee)
    if a.cotes_seules:
        print(json.dumps(dims.to_dict(), ensure_ascii=False, indent=1))
        return 0
    t0 = time.time()
    written = export_all(dims, Path(a.out), viewer=not a.sans_visionneuse)
    print(json.dumps({"cotes": dims.to_dict(), "fichiers": written,
                      "duree_s": round(time.time() - t0, 1)}, ensure_ascii=False, indent=1))
    return 0
