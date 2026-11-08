"""Dimensionnement géométrique du micro-turboréacteur (sans construction CAO)."""
import math

import pytest

from jetagent.cad.microturbojet import size_engine


def test_sizing_350N_matches_rc_turbine_class():
    d = size_engine(350.0)
    assert 0.55 < d.mass_flow_kg_s < 0.75
    assert 120 < d.casing_diameter < 160          # classe JetCat P300/P400 : 130-150 mm
    assert 300 < d.overall_length < 400
    assert 60 < d.nozzle_exit_diameter < 75
    assert d.turbine_tip_diameter < d.compressor_tip_diameter < d.casing_diameter
    assert d.turbine_hub_diameter < d.turbine_tip_diameter
    assert 0.13 < d.tsfc_kg_per_N_h < 0.16


def test_sizing_scales_with_sqrt_of_thrust():
    a, b = size_engine(100.0), size_engine(400.0)
    assert b.mass_flow_kg_s == pytest.approx(4 * a.mass_flow_kg_s, rel=1e-6)
    assert b.casing_diameter == pytest.approx(2 * a.casing_diameter, rel=1e-6)
    assert b.nozzle_exit_diameter == pytest.approx(2 * a.nozzle_exit_diameter, rel=1e-6)


def test_exit_area_consistent_with_exit_diameters():
    d = size_engine(350.0)
    a9 = math.pi / 4 * (d.nozzle_exit_diameter**2 - d.nozzle_cone_exit_diameter**2) / 100  # cm²
    assert a9 == pytest.approx(d.exit_area_cm2, rel=1e-6)


def test_invalid_thrust():
    with pytest.raises(ValueError):
        size_engine(0)
