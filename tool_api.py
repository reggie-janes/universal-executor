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

Example:

    from tool_api import input, output, export

    tool_name = "Adder"

    a: input(int, "first")  = 0
    b: input(int, "second") = 0
    s: output("sum")

    @export("add")
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


@dataclass(frozen=True)
class Output:
    description: str


def input(kind: Any, description: str) -> Input:  # noqa: A001 — DSL name
    return Input(kind, description)


def output(description: str) -> Output:
    return Output(description)


def export(description: str):
    def decorator(fn):
        fn.__tool_description__ = description
        return fn
    return decorator


__all__ = ["input", "output", "export", "Input", "Output", "Enum"]
