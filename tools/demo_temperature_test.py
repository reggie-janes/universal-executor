import pytest

import tools.demo_temperature as t
from tools.demo_temperature import Unit


def _set(value, from_u, to_u, round_it=False):
    t.value = value
    t.from_u = from_u
    t.to_u = to_u
    t.round_it = round_it


def test_identity_celsius():
    _set(25.0, Unit.CELSIUS, Unit.CELSIUS)
    t.convert()
    assert float(t.result) == pytest.approx(25.0)


def test_celsius_to_fahrenheit():
    _set(100.0, Unit.CELSIUS, Unit.FAHRENHEIT)
    t.convert()
    assert float(t.result) == pytest.approx(212.0)


def test_fahrenheit_to_celsius():
    _set(32.0, Unit.FAHRENHEIT, Unit.CELSIUS)
    t.convert()
    assert float(t.result) == pytest.approx(0.0)


def test_celsius_to_kelvin():
    _set(0.0, Unit.CELSIUS, Unit.KELVIN)
    t.convert()
    assert float(t.result) == pytest.approx(273.15)


def test_kelvin_to_celsius():
    _set(0.0, Unit.KELVIN, Unit.CELSIUS)
    t.convert()
    assert float(t.result) == pytest.approx(-273.15)


def test_fahrenheit_to_kelvin():
    _set(32.0, Unit.FAHRENHEIT, Unit.KELVIN)
    t.convert()
    assert float(t.result) == pytest.approx(273.15)


def test_kelvin_to_fahrenheit():
    _set(273.15, Unit.KELVIN, Unit.FAHRENHEIT)
    t.convert()
    assert float(t.result) == pytest.approx(32.0)


def test_round_flag():
    _set(100.0, Unit.CELSIUS, Unit.FAHRENHEIT, round_it=True)
    t.convert()
    assert t.result == "212"


def test_round_flag_off_keeps_float():
    _set(37.0, Unit.CELSIUS, Unit.FAHRENHEIT, round_it=False)
    t.convert()
    assert "." in t.result
    assert float(t.result) == pytest.approx(98.6)
