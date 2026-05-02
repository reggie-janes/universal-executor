"""Modern web-like theme + Roboto font loading for DearPyGui.

Two palettes (dark / light) are built into separate DPG themes at startup;
``set_mode`` swaps which one is bound globally.
"""
from pathlib import Path
from typing import Callable

import dearpygui.dearpygui as dpg


BASE_FONT_SIZE = 18

# Tailwind-ish dark palette (zinc + blue).
DARK = {
    "ACCENT":     (59, 130, 246, 255),    # blue-500
    "ACCENT_DIM": (37, 99, 235, 255),     # blue-600
    "BG":         (24, 24, 27, 255),      # zinc-900
    "PANEL":      (39, 39, 42, 255),      # zinc-800
    "PANEL_HI":   (63, 63, 70, 255),      # zinc-700
    "TEXT":       (244, 244, 245, 255),   # zinc-100
    "TEXT_DIM":   (161, 161, 170, 255),   # zinc-400
    "BORDER":     (63, 63, 70, 255),
    "FRAME_HI":   (82, 82, 91, 255),
    "FRAME_AC":   (113, 113, 122, 255),
    "TITLE":      (39, 39, 42, 255),
    "BUTTON":     (59, 130, 246, 255),    # blue-500
    "BUTTON_HI":  (37, 99, 235, 255),     # blue-600
}

# Mirror palette in light values.
LIGHT = {
    "ACCENT":     (59, 130, 246, 255),    # blue-500
    "ACCENT_DIM": (37, 99, 235, 255),     # blue-600
    "BG":         (250, 250, 250, 255),   # zinc-50
    "PANEL":      (244, 244, 245, 255),   # zinc-100
    "PANEL_HI":   (228, 228, 231, 255),   # zinc-200
    "TEXT":       (24, 24, 27, 255),      # zinc-900
    "TEXT_DIM":   (113, 113, 122, 255),   # zinc-500
    "BORDER":     (212, 212, 216, 255),   # zinc-300
    "FRAME_HI":   (212, 212, 216, 255),
    "FRAME_AC":   (161, 161, 170, 255),
    "TITLE":      (228, 228, 231, 255),
    "BUTTON":     (212, 212, 216, 255),   # zinc-300
    "BUTTON_HI":  (161, 161, 170, 255),   # zinc-400
}


_state: dict = {
    "mode": "dark",
    "themes": {},   # mode -> theme tag
    "listeners": [],
}


def apply(assets_dir: Path, mode: str | None = None) -> None:
    _load_fonts(assets_dir)
    _state["themes"]["dark"] = _build_theme(DARK)
    _state["themes"]["light"] = _build_theme(LIGHT)
    if mode in _state["themes"]:
        _state["mode"] = mode
    _bind_current()


def set_mode(mode: str) -> None:
    if mode not in _state["themes"] or mode == _state["mode"]:
        return
    _state["mode"] = mode
    _bind_current()
    palette = current_palette()
    for cb in list(_state["listeners"]):
        cb(palette)


def toggle_mode() -> str:
    set_mode("light" if _state["mode"] == "dark" else "dark")
    return _state["mode"]


def current_mode() -> str:
    return _state["mode"]


def current_palette() -> dict:
    return LIGHT if _state["mode"] == "light" else DARK


def on_change(cb: Callable[[dict], None]) -> None:
    _state["listeners"].append(cb)


def _bind_current() -> None:
    dpg.bind_theme(_state["themes"][_state["mode"]])


def _load_fonts(assets_dir: Path) -> None:
    font_path = assets_dir / "Roboto-VariableFont_wdth,wght.ttf"
    if not font_path.exists():
        return
    with dpg.font_registry():
        default_font = dpg.add_font(str(font_path), BASE_FONT_SIZE)
    dpg.bind_font(default_font)


def _build_theme(p: dict) -> int:
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, p["BG"])
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, p["PANEL"])
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, p["PANEL"])
            dpg.add_theme_color(dpg.mvThemeCol_Border, p["BORDER"])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, p["PANEL_HI"])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, p["FRAME_HI"])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, p["FRAME_AC"])
            dpg.add_theme_color(dpg.mvThemeCol_Text, p["TEXT"])
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, p["TEXT_DIM"])
            dpg.add_theme_color(dpg.mvThemeCol_InputTextCursor, p["TEXT"])
            dpg.add_theme_color(dpg.mvThemeCol_Button, p["BUTTON"])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, p["BUTTON_HI"])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, p["BUTTON_HI"])
            dpg.add_theme_color(dpg.mvThemeCol_Header, p["ACCENT_DIM"])
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, p["ACCENT"])
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, p["ACCENT"])
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, p["TITLE"])
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, p["ACCENT_DIM"])
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, p["BG"])
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, p["PANEL_HI"])
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, p["ACCENT"])
            dpg.add_theme_color(dpg.mvThemeCol_Separator, p["BORDER"])
            dpg.add_theme_color(dpg.mvThemeCol_Tab, p["PANEL"])
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, p["ACCENT"])
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, p["ACCENT_DIM"])

            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 8)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 16, 16)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 14)
    return theme
