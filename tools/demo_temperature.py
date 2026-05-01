from enum import Enum

from tool_api import input, output, export

tool_name = "Temperature converter"


class Unit(Enum):
    CELSIUS = "C"
    FAHRENHEIT = "F"
    KELVIN = "K"


value:    input(float, "value")        = 0.0
from_u:   input(Unit,  "from unit")    = Unit.CELSIUS
to_u:     input(Unit,  "to unit")      = Unit.FAHRENHEIT
round_it: input(bool,  "round result") = False

result: output("result")


def _to_kelvin(v: float, u: Unit) -> float:
    if u is Unit.CELSIUS:
        return v + 273.15
    if u is Unit.FAHRENHEIT:
        return (v - 32.0) * 5.0 / 9.0 + 273.15
    return v


def _from_kelvin(k: float, u: Unit) -> float:
    if u is Unit.CELSIUS:
        return k - 273.15
    if u is Unit.FAHRENHEIT:
        return (k - 273.15) * 9.0 / 5.0 + 32.0
    return k


@export("convert")
def convert():
    global result
    k = _to_kelvin(value, from_u)
    r = _from_kelvin(k, to_u)
    result = str(round(r) if round_it else r)
