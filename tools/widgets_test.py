import math
from decimal import ROUND_HALF_EVEN

import pytest

from ui.widgets import _parse_si_number


@pytest.mark.parametrize("text, expected", [
    ("", 0.0),
    ("0", 0.0),
    ("42", 42.0),
    ("-3.5", -3.5),
    ("1.5e3", 1500.0),
])
def test_plain_numbers(text, expected):
    assert float(_parse_si_number(text)) == expected


@pytest.mark.parametrize("text, expected", [
    ("1n", 1e-9),
    ("1u", 1e-6),
    ("1µ", 1e-6),
    ("1μ", 1e-6),
    ("5m", 5e-3),
    ("2k", 2e3),
    ("2K", 2e3),
    ("1.5M", 1.5e6),
    ("3G", 3e9),
    ("2.5T", 2.5e12),
])
def test_supported_si_suffixes(text, expected):
    assert math.isclose(float(_parse_si_number(text)), expected, rel_tol=1e-12)


@pytest.mark.parametrize("text", ["1y", "1z", "1a", "1f", "1p", "1P", "1E", "1Z", "1Y"])
def test_dropped_si_suffixes_are_rejected(text):
    with pytest.raises(ValueError):
        _parse_si_number(text)


@pytest.mark.parametrize("comma, dot", [
    ("1,5", "1.5"),
    ("-2,75", "-2.75"),
    ("1,5k", "1.5k"),
    ("0,001", "0.001"),
])
def test_comma_is_equivalent_to_dot(comma, dot):
    assert _parse_si_number(comma) == _parse_si_number(dot)


def test_thousand_separators_are_not_supported():
    with pytest.raises(ValueError):
        _parse_si_number("1,000,000")


@pytest.mark.parametrize("text, expected", [
    ("1e5", 100_000),
    ("1e20", 10**20),
    ("1.234e20", 123_400_000_000_000_000_000),
    ("1e309", 10**309),
    ("5G", 5_000_000_000),
    ("2.5T", 2_500_000_000_000),
    ("1.5", 2),
    ("2.5", 2),
    ("-1.5", -2),
])
def test_lossless_int_conversion(text, expected):
    d = _parse_si_number(text)
    assert int(d.to_integral_value(rounding=ROUND_HALF_EVEN)) == expected
