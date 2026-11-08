"""Post-combustion, tuyère convergente-divergente, recherche bilingue, CLI hors ligne."""
import json
import subprocess
import sys

import pytest

from jetagent.agent import is_in_scope
from jetagent.cycle import TurbojetInputs, analyze_turbojet
from jetagent.knowledge import KnowledgeBase, expand_query
from jetagent.tools import analyser_cycle_turboreacteur

BASE = dict(mach=0.9, altitude_m=11000, pressure_ratio=13, turbine_inlet_temp_K=1650)


def test_afterburner_increases_thrust_and_tsfc():
    dry = analyze_turbojet(TurbojetInputs(**BASE))
    wet = analyze_turbojet(TurbojetInputs(**BASE, afterburner_temp_K=2000))
    assert wet.afterburner_on and not dry.afterburner_on
    assert wet.specific_thrust_N_per_kg_s > 1.2 * dry.specific_thrust_N_per_kg_s
    assert wet.tsfc_kg_per_N_h > dry.tsfc_kg_per_N_h
    assert wet.afterburner_fuel_air_ratio > 0
    assert wet.total_fuel_air_ratio == pytest.approx(wet.fuel_air_ratio + wet.afterburner_fuel_air_ratio)
    assert wet.Tt7_K == 2000 and dry.Tt7_K == dry.Tt5_K
    assert wet.Pt7_Pa < wet.Pt5_Pa  # perte de pression du canal de réchauffe


def test_afterburner_below_t5_is_rejected():
    with pytest.raises(ValueError, match="réchauffe"):
        analyze_turbojet(TurbojetInputs(**BASE, afterburner_temp_K=1000))


def test_afterburner_above_stoichiometric_is_rejected():
    with pytest.raises(ValueError):
        analyze_turbojet(TurbojetInputs(**BASE, afterburner_temp_K=2400))


def test_cd_nozzle_beats_convergent_at_high_npr():
    conv = analyze_turbojet(TurbojetInputs(**BASE, afterburner_temp_K=2000))
    cd = analyze_turbojet(TurbojetInputs(**BASE, afterburner_temp_K=2000, nozzle_type="convergent_divergent"))
    assert conv.nozzle_pressure_ratio > 4
    assert cd.specific_thrust_N_per_kg_s > conv.specific_thrust_N_per_kg_s
    assert cd.tsfc_kg_per_N_h < conv.tsfc_kg_per_N_h
    assert cd.exhaust_mach > 1.5 and conv.exhaust_mach == pytest.approx(1.0)
    assert any("convergente-divergente" in w for w in conv.warnings)
    assert cd.nozzle_type == "convergent_divergent"


def test_cd_nozzle_matches_convergent_when_unchoked():
    """Sous le NPR critique, les deux tuyères détendent jusqu'à P0 : mêmes résultats."""
    low = dict(mach=0.0, altitude_m=0, pressure_ratio=3.0, turbine_inlet_temp_K=1100)
    a = analyze_turbojet(TurbojetInputs(**low))
    b = analyze_turbojet(TurbojetInputs(**low, nozzle_type="convergent_divergent"))
    assert not a.nozzle_choked and not b.nozzle_choked
    assert a.specific_thrust_N_per_kg_s == pytest.approx(b.specific_thrust_N_per_kg_s)


def test_invalid_nozzle_type():
    with pytest.raises(ValueError, match="nozzle_type"):
        analyze_turbojet(TurbojetInputs(**BASE, nozzle_type="plug"))


def test_defaults_unchanged_without_afterburner():
    r = analyze_turbojet(TurbojetInputs(pressure_ratio=20, turbine_inlet_temp_K=1500, mass_flow_kg_s=50))
    assert r.afterburner_fuel_air_ratio == 0.0
    assert r.total_fuel_air_ratio == r.fuel_air_ratio
    assert r.fuel_flow_kg_s == pytest.approx(r.fuel_air_ratio * 50)


def test_tool_exposes_afterburner_and_nozzle():
    schema = analyser_cycle_turboreacteur.to_dict()["input_schema"]["properties"]
    assert "temperature_rechauffe_K" in schema and "type_tuyere" in schema
    out = json.loads(analyser_cycle_turboreacteur.call({
        "mach": 2.0, "altitude_m": 15000, "taux_compression": 8.0, "temperature_entree_turbine_K": 1600.0,
        "temperature_rechauffe_K": 2000.0, "type_tuyere": "convergent_divergent",
    }))
    assert out["afterburner_on"] is True and out["nozzle_type"] == "convergent_divergent"


def test_bilingual_query_expansion_and_search():
    assert "turboreacteur" in expand_query(["turbojet"])
    kb = KnowledgeBase()
    hits = kb.search("turbojet engine afterburner thrust", top_k=2)
    assert hits and hits[0][1].source == "05_turbojet_engine.md"
    hits = kb.search("J79 Olympus 593 Concorde", top_k=1)
    assert hits[0][1].source == "05_turbojet_engine.md"
    hits = kb.search("thrust specific fuel consumption", top_k=3)
    assert any("glossaire" in s.source for _, s in hits)


def test_scope_accepts_english_questions():
    assert is_in_scope("What OPR should a turbojet engine use at Mach 2?")
    assert is_in_scope("Explain afterburner reheat on the J79")


def test_offline_cli_cycle_and_doc():
    r = subprocess.run([sys.executable, "-m", "jetagent.cli_tools", "cycle", "--mach", "0.8",
                        "--altitude", "10000", "--opr", "12", "--t4", "1500", "--rechauffe", "1900"],
                       capture_output=True, text=True, check=True)
    out = json.loads(r.stdout)
    assert out["afterburner_on"] is True
    r = subprocess.run([sys.executable, "-m", "jetagent.cli_tools", "doc", "turbojet history Whittle", "-n", "1"],
                       capture_output=True, text=True, check=True)
    assert json.loads(r.stdout)["resultats"][0]["source"] == "05_turbojet_engine.md"
    r = subprocess.run([sys.executable, "-m", "jetagent.cli_tools", "convert", "10000", "lbf", "kN"],
                       capture_output=True, text=True, check=True)
    assert abs(json.loads(r.stdout)["valeur"] - 44.482216) < 1e-6
