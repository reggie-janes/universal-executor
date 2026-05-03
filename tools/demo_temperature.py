from core.tool_api import input, output, export, LabeledEnum

tool_name = "Temperature converter"


class Unit(LabeledEnum):
    CELSIUS    = "C"
    FAHRENHEIT = "F"
    KELVIN     = "K"

Unit.CELSIUS    ("°C")
Unit.FAHRENHEIT ("Fahrenheit")
#Unit.KELVIN     ("Kelvin")  # default

KELVIN_OFFSET = 273.15

value:    input(float, "value")        = 0.0
from_u:   input(Unit,  "from unit")    = Unit.FAHRENHEIT
to_u:     input(Unit,  "to unit")      = Unit.CELSIUS
round_it: input(bool,  "round result") = False

result: output("result")


def _to_kelvin(v: float, u: Unit) -> float:
    if u is Unit.CELSIUS:
        return v + KELVIN_OFFSET
    if u is Unit.FAHRENHEIT:
        return (v - 32.0) * 5.0 / 9.0 + KELVIN_OFFSET
    return v


def _from_kelvin(k: float, u: Unit) -> float:
    if u is Unit.CELSIUS:
        return k - KELVIN_OFFSET
    if u is Unit.FAHRENHEIT:
        return (k - KELVIN_OFFSET) * 9.0 / 5.0 + 32.0
    return k


@export("Convert")
def convert():
    global result
    k = _to_kelvin(value, from_u)
    r = _from_kelvin(k, to_u)
    result = str(round(r) if round_it else r)
