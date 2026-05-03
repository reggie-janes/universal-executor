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
import inspect
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
        _check_no_required_params(fn)
        fn.__tool_description__ = description
        fn.__tool_tooltip__ = tooltip
        return fn
    return decorator


_BAD_PARAM_KINDS = (
    inspect.Parameter.POSITIONAL_ONLY,
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
    inspect.Parameter.KEYWORD_ONLY,
)


def _check_no_required_params(fn: Any) -> None:
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return
    required = [
        p.name for p in sig.parameters.values()
        if p.kind in _BAD_PARAM_KINDS and p.default is inspect.Parameter.empty
    ]
    if not required:
        return
    name = getattr(fn, "__name__", repr(fn))
    raise TypeError(
        f"@export def {name}({', '.join(required)}): exported tool functions "
        f"must take no arguments. Read {', '.join(required)} as module "
        f'globals — declare them with `{required[0]}: input(int, "...") = 0`.'
    )


class LabeledEnum(Enum):
    """Enum whose members carry a human-friendly display label.

    Call a member with a string to register its label; the call returns the
    member itself, so it composes with default-value syntax::

        class Unit(LabeledEnum):
            CELSIUS = "C"

        to_u: input(Unit, "to unit") = Unit.CELSIUS("Celsius degrees")

    Members without a registered label fall back to ``self.name``.
    """

    def __call__(self, label: str) -> "LabeledEnum":
        cls = type(self)
        if "_labels" not in cls.__dict__:
            cls._labels = {}
        cls._labels[self] = label
        return self

    @property
    def label(self) -> str:
        return type(self).__dict__.get("_labels", {}).get(self, self.name)


__all__ = ["input", "output", "export", "Input", "Output", "Enum", "LabeledEnum"]
