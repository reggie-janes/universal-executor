"""Input/output widget construction, sections, and value push/pull."""
from __future__ import annotations

import dearpygui.dearpygui as dpg

from . import layout
from .scanner import ToolSpec, VarSpec, is_choices_kind, is_enum_kind


_SI_SUFFIXES = {
    "y": 1e-24, "z": 1e-21, "a": 1e-18, "f": 1e-15,
    "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "μ": 1e-6,
    "m": 1e-3,
    "k": 1e3, "K": 1e3,
    "M": 1e6, "G": 1e9, "T": 1e12,
    "P": 1e15, "E": 1e18, "Z": 1e21, "Y": 1e24,
}


def _parse_si_number(text: str) -> float:
    """Parse ``text`` as a number, optionally with a single SI suffix.

    Examples: "10k" -> 10000, "2.5M" -> 2_500_000, "5m" -> 0.005.
    Note that ``m`` is milli and ``M`` is mega — case matters.
    """
    text = text.strip()
    if not text:
        return 0.0
    last = text[-1]
    if last in _SI_SUFFIXES and len(text) > 1:
        return float(text[:-1].strip()) * _SI_SUFFIXES[last]
    return float(text)


def _make_input_widget(var: VarSpec, module) -> int | str:
    current = getattr(module, var.name, None)
    kind = var.kind
    if kind is int:
        return dpg.add_input_text(default_value=str(int(current or 0)),
                                  width=layout.NUMBER_FIELD_WIDTH)
    if kind is float:
        return dpg.add_input_text(default_value=format(float(current or 0.0), ".6g"),
                                  width=layout.NUMBER_FIELD_WIDTH)
    if kind is bool:
        return dpg.add_checkbox(default_value=bool(current))
    if is_enum_kind(kind):
        items = [m.name for m in kind]
        default = current.name if current is not None and current.__class__ is kind else (items[0] if items else "")
        return dpg.add_combo(items=items, default_value=default, width=layout.COMBO_FIELD_WIDTH)
    if is_choices_kind(kind):
        items = [str(c) for c in kind]
        default = str(current) if current is not None else (items[0] if items else "")
        return dpg.add_combo(items=items, default_value=default, width=layout.COMBO_FIELD_WIDTH)
    return dpg.add_input_text(default_value=str(current), readonly=True,
                              width=layout.TEXT_FIELD_WIDTH)


def _make_output_widget(var: VarSpec, module) -> int | str:
    current = getattr(module, var.name, "")
    return dpg.add_input_text(default_value=str(current), readonly=True,
                              width=layout.TEXT_FIELD_WIDTH)


def build_inputs_section(tool: ToolSpec) -> None:
    dpg.add_text("Inputs")
    if not tool.inputs:
        dpg.add_text("(no inputs)", color=layout.DIM_COLOR)
        return
    with dpg.table(header_row=False, resizable=False,
                   policy=dpg.mvTable_SizingFixedFit,
                   borders_innerH=False, borders_innerV=False):
        dpg.add_table_column(width_fixed=True, init_width_or_weight=layout.LABEL_COLUMN_WIDTH)
        dpg.add_table_column()
        for var in tool.inputs:
            with dpg.table_row():
                dpg.add_text(var.description)
                tag = _make_input_widget(var, tool.module)
                layout._state["input_tags"][var.name] = tag


def build_outputs_section(tool: ToolSpec) -> None:
    dpg.add_text("Outputs")
    if not tool.outputs:
        dpg.add_text("(no outputs)", color=layout.DIM_COLOR)
        return
    with dpg.table(header_row=False, resizable=False,
                   policy=dpg.mvTable_SizingFixedFit,
                   borders_innerH=False, borders_innerV=False):
        dpg.add_table_column(width_fixed=True, init_width_or_weight=layout.LABEL_COLUMN_WIDTH)
        dpg.add_table_column()
        for var in tool.outputs:
            with dpg.table_row():
                dpg.add_text(var.description)
                tag = _make_output_widget(var, tool.module)
                layout._state["output_tags"][var.name] = tag


def push_inputs(tool: ToolSpec) -> None:
    for var in tool.inputs:
        tag = layout._state["input_tags"][var.name]
        raw = dpg.get_value(tag)
        kind = var.kind
        if kind is int:
            value = int(round(_parse_si_number(raw)))
        elif kind is float:
            value = _parse_si_number(raw)
        elif is_enum_kind(kind):
            value = kind[raw] if raw in kind.__members__ else getattr(tool.module, var.name)
        elif is_choices_kind(kind):
            value = next((c for c in kind if str(c) == raw), raw)
        else:
            value = raw
        setattr(tool.module, var.name, value)


def pull_outputs(tool: ToolSpec) -> None:
    for var in tool.outputs:
        tag = layout._state["output_tags"][var.name]
        value = getattr(tool.module, var.name)
        dpg.set_value(tag, str(value))
