"""Author-facing API for tool modules.

A tool author writes a normal Python module that imports `input`, `output`,
and `export` from this module. Public input/output variables are declared as
type-annotated module-level names; exported callables are marked with
`@export("description")`. Anything else (underscore-prefixed names, helpers)
is treated as private.

Outputs are always strings (default ``""``). The exported function assigns
a string to each output — including soft-error messages like
``"undefined, can't divide by 0"``. The error popup is reserved for
uncaught exceptions (programmer mistakes).

Each of ``input``, ``output``, and ``export`` accepts an optional ``tooltip``
string. When non-empty, the UI shows it as a hover tooltip on the
corresponding label/widget/button.

Example:

    from core.tool_api import input, output, export

    tool_name = "Adder"

    a: input(int, "first",  tooltip="left operand")  = 0
    b: input(int, "second", tooltip="right operand") = 0
    s: output("sum")

    @export("add", tooltip="compute a + b")
    def add():
        global s
        s = str(a + b)
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any


@dataclass(frozen=True)
class Input:
    kind: Any
    description: str
    tooltip: str = ""


@dataclass(frozen=True)
class Output:
    description: str
    tooltip: str = ""


def input(kind: Any, description: str, tooltip: str = "") -> Input:  # noqa: A001 — DSL name
    return Input(kind, description, tooltip)


def output(description: str, tooltip: str = "") -> Output:
    return Output(description, tooltip)


def export(description: str, tooltip: str = ""):
    def decorator(fn):
        fn.__tool_description__ = description
        fn.__tool_tooltip__ = tooltip
        return fn
    return decorator


__all__ = ["input", "output", "export", "Input", "Output", "Enum"]
