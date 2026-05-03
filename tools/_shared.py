"""Shared helpers for tools in this folder."""
import math


def sqrt(x: float) -> str:
    if x < 0:
        return "undefined, can't sqrt a negative number"
    return str(math.sqrt(x))
