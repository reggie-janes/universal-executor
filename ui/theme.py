"""Modern web-like theme + Roboto font loading for DearPyGui."""
from pathlib import Path

import dearpygui.dearpygui as dpg


BASE_FONT_SIZE = 18

# Tailwind-ish dark palette
ACCENT     = (59, 130, 246, 255)    # blue-500
ACCENT_DIM = (37, 99, 235, 255)     # blue-600
BG         = (24, 24, 27, 255)      # zinc-900
PANEL      = (39, 39, 42, 255)      # zinc-800
PANEL_HI   = (63, 63, 70, 255)      # zinc-700
TEXT       = (244, 244, 245, 255)   # zinc-100
TEXT_DIM   = (161, 161, 170, 255)   # zinc-400
BORDER     = (63, 63, 70, 255)


def apply(assets_dir: Path) -> None:
    _load_fonts(assets_dir)
    _bind_theme()


def _load_fonts(assets_dir: Path) -> None:
    font_path = assets_dir / "Roboto-VariableFont_wdth,wght.ttf"
    if not font_path.exists():
        return
    with dpg.font_registry():
        with dpg.font(str(font_path), BASE_FONT_SIZE) as default_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
    dpg.bind_font(default_font)


def _bind_theme() -> None:
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, BG)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_Border, BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, PANEL_HI)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (82, 82, 91, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (113, 113, 122, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Text, TEXT)
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, TEXT_DIM)
            dpg.add_theme_color(dpg.mvThemeCol_Button, ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, ACCENT_DIM)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, ACCENT_DIM)
            dpg.add_theme_color(dpg.mvThemeCol_Header, ACCENT_DIM)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, ACCENT_DIM)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, BG)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, PANEL_HI)
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_Separator, BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_Tab, PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, ACCENT_DIM)

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
    dpg.bind_theme(theme)
