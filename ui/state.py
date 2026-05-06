"""Shared UI state, tag/dimension constants, and tiny DPG helpers.

Lives outside ``layout.py`` so ``layout``/``widgets``/``runner`` can all import
from one place without importing each other in a cycle.
"""
from __future__ import annotations

from typing import Any

import dearpygui.dearpygui as dpg

from core.dpi import _s

from . import theme


MAIN_WINDOW = "uex_main"
TOOL_COMBO = "uex_tool_combo"
TOP_BAR = "uex_top_bar"
TOP_SEPARATOR = "uex_top_separator"
DYNAMIC_AREA = "uex_dynamic_area"
OUTPUTS_LAST_ACTION = "uex_outputs_last_action"
TOP_SPACER = "uex_top_spacer"
THEME_TOGGLE = "uex_theme_toggle"

THEME_ICON_SIZE = _s(28)
DIM_COLOR = (113, 113, 122, 255)  # zinc-500: legible on both palettes

LABEL_COLUMN_WIDTH = _s(120)
NUMBER_FIELD_WIDTH = _s(140)
COMBO_FIELD_WIDTH = _s(200)
TEXT_FIELD_WIDTH = _s(260)
# Outputs are multiline so long text scrolls; height kept just above one
# line of Roboto 18 + frame padding so short results still look compact.
OUTPUT_FIELD_HEIGHT = _s(38)

TOOLTIP_DELAY = 0.8


_state: dict[str, Any] = {
    "tools": [],
    "current": None,
    "input_tags": {},
    "output_tags": {},
    "rescan": None,
    "last_func": None,
    "last_status": None,
    # Per-tool snapshot taken on tool switch so unsubmitted input edits and the
    # last-action label survive when the user returns to a tool. Keyed by
    # tool.name -> {"inputs": {var_name: raw_widget_value},
    #               "last_func_name": str | None, "last_status": str | None}.
    "tool_states": {},
}


def bind_bold(item: int | str) -> None:
    font = theme.bold_font()
    if font is not None:
        dpg.bind_item_font(item, font)


def add_tooltip(parent_tag: int | str, text: str) -> None:
    if not text:
        return
    with dpg.tooltip(parent=parent_tag, delay=TOOLTIP_DELAY):
        dpg.add_text(text)
