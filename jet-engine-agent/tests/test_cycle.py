import math

import pytest

from jetagent.cycle import TurbojetInputs, analyze_turbojet, isa_atmosphere


def test_isa_sea_level_and_tropopause():
    sl = isa_atmosphere(0)
    assert math.isclose(sl.temperature_K, 288.15)
    assert math.isclose(sl.pressure_Pa, 101325.0)
    assert math.isclose(sl.speed_of_sound_m_s, 340.3, rel_tol=1e-3)
    tp = isa_atmosphere(11000)
    assert math.isclose(tp.temperature_K, 216.65, abs_tol=0.01)
    assert math.isclose(tp.pressure_Pa, 22632, rel_tol=1e-3)
    # Isotherme entre 11 et 20 km
    assert math.isclose(isa_atmosphere(15000).temperature_K, 216.65, abs_tol=0.01)


def test_isa_out_of_range():
    with pytest.raises(ValueError):
        isa_atmosphere(50000)


def test_static_sea_level_turbojet_orders_of_magnitude():
    r = analyze_turbojet(TurbojetInputs(pressure_ratio=20, turbine_inlet_temp_K=1500, mass_flow_kg_s=50))
    # Ordres de grandeur attendus pour un turboréacteur simple flux au point fixe
    assert 700 < r.specific_thrust_N_per_kg_s < 1100
    assert 0.08 < r.tsfc_kg_per_N_h < 0.13
    assert 0.018 < r.fuel_air_ratio < 0.032
    assert r.nozzle_choked is True
    assert math.isclose(r.exhaust_mach, 1.0)
    assert r.thrust_N == pytest.approx(r.specific_thrust_N_per_kg_s * 50)
    assert r.fuel_flow_kg_s == pytest.approx(r.fuel_air_ratio * 50)
    # Au point fixe, pas de rendement propulsif défini
    assert r.propulsive_efficiency == 0.0
    assert 0.3 < r.thermal_efficiency < 0.5


def test_cruise_efficiencies_are_physical():
    r = analyze_turbojet(TurbojetInputs(mach=0.85, altitude_m=11000, pressure_ratio=20, turbine_inlet_temp_K=1500))
    assert 0 < r.propulsive_efficiency < 1
    assert 0 < r.thermal_efficiency < 1
    assert math.isclose(r.overall_efficiency, r.thermal_efficiency * r.propulsive_efficiency)
    # À Mach 0,85 un simple flux a un rendement propulsif de l'ordre de 0,35-0,5
    assert 0.3 < r.propulsive_efficiency < 0.55


def test_power_balance_compressor_turbine():
    """Le travail turbine (par kg d'air) doit égaler le travail compresseur / rendement mécanique."""
    from jetagent.cycle import CP_C, CP_T
    inp = TurbojetInputs(pressure_ratio=15, turbine_inlet_temp_K=1450)
    r = analyze_turbojet(inp)
    work_c = CP_C * (r.Tt3_K - r.Tt2_K)
    work_t = (1 + r.fuel_air_ratio) * CP_T * (r.Tt4_K - r.Tt5_K) * inp.eta_mechanical
    assert math.isclose(work_c, work_t, rel_tol=1e-9)


def test_higher_opr_reduces_tsfc_at_fixed_t4():
    low = analyze_turbojet(TurbojetInputs(mach=0.8, altitude_m=10000, pressure_ratio=10, turbine_inlet_temp_K=1500))
    high = analyze_turbojet(TurbojetInputs(mach=0.8, altitude_m=10000, pressure_ratio=25, turbine_inlet_temp_K=1500))
    assert high.tsfc_kg_per_N_h < low.tsfc_kg_per_N_h


def test_higher_t4_increases_specific_thrust():
    a = analyze_turbojet(TurbojetInputs(pressure_ratio=20, turbine_inlet_temp_K=1400))
    b = analyze_turbojet(TurbojetInputs(pressure_ratio=20, turbine_inlet_temp_K=1700))
    assert b.specific_thrust_N_per_kg_s > a.specific_thrust_N_per_kg_s


def test_t4_below_t3_is_rejected():
    with pytest.raises(ValueError, match="T4"):
        analyze_turbojet(TurbojetInputs(pressure_ratio=40, turbine_inlet_temp_K=800))


def test_invalid_efficiency_is_rejected():
    with pytest.raises(ValueError):
        analyze_turbojet(TurbojetInputs(eta_compressor=1.2))


def test_material_warnings():
    r = analyze_turbojet(TurbojetInputs(pressure_ratio=50, turbine_inlet_temp_K=1900))
    joined = " ".join(r.warnings)
    assert "T4 > 1750 K" in joined
    assert "OPR > 45" in joined
