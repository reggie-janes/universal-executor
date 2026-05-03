"""Run an exported tool function and surface any uncaught error in a modal."""
from __future__ import annotations

import traceback

import dearpygui.dearpygui as dpg

from core.scanner import TOOLS_DIR, FuncSpec, LoadError

from . import layout, theme, widgets


_BODY_WIDTH_PX = 700
_BODY_LINE_HEIGHT = 22         # font 18 + line spacing
_BODY_MAX_HEIGHT = 400         # past this the input scrolls instead of growing


_modal_chrome_theme: int | str | None = None
_modal_input_themes: dict[str, int | str] = {}


def _ensure_modal_input_theme() -> int | str:
    """Per-palette theme that lightens the traceback input's FrameBg so it
    stands out a touch from the modal background. Cached per mode."""
    mode = theme.current_mode()
    cached = _modal_input_themes.get(mode)
    if cached is not None and dpg.does_item_exist(cached):
        return cached
    palette = theme.LIGHT if mode == "light" else theme.DARK
    base = palette["PANEL_HI"]
    delta = 5
    lighter = (
        min(255, base[0] + delta),
        min(255, base[1] + delta),
        min(255, base[2] + delta),
        base[3],
    )
    with dpg.theme() as t:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, lighter)
    _modal_input_themes[mode] = t
    return t


def _ensure_modal_chrome_theme() -> int | str:
    """Theme that shrinks the modal title-bar (so the close-X hover bubble
    fills its height) and tightens WindowPadding so the body widget hugs
    the popup edges. Scoped to mvWindowAppItem so child widgets keep the
    normal padding.
    """
    global _modal_chrome_theme
    if _modal_chrome_theme is None or not dpg.does_item_exist(_modal_chrome_theme):
        with dpg.theme() as t:
            with dpg.theme_component(dpg.mvWindowAppItem):
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 1)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 4, 4)
        _modal_chrome_theme = t
    return _modal_chrome_theme


def make_run_cb(fn: FuncSpec):
    """Build a DPG callback that ignores all args and invokes ``fn``.

    DPG passes (sender, app_data, user_data) positionally based on the
    callback's arity, so closures are safer than lambda default-arg tricks.
    """
    def _cb(*_args, **_kwargs):
        _run(fn)
    return _cb


def _run(fn: FuncSpec) -> None:
    tool = layout._state["current"]
    if tool is None:
        return
    layout._state["last_func"] = fn
    tb: str | None = None
    try:
        widgets.push_inputs(tool)
        fn.callable()
        widgets.pull_outputs(tool)
        status = "OK"
    except Exception:
        tb = traceback.format_exc()
        status = "ERROR"
    layout._state["last_status"] = status
    if dpg.does_item_exist(layout.OUTPUTS_LAST_ACTION):
        dpg.set_value(layout.OUTPUTS_LAST_ACTION, f"[{fn.description}, {status}]")
    if tb is not None:
        _show_error_modal(f"Error in {fn.name}()", tb)


def _estimate_body_height(body: str) -> int:
    visual_lines = max(1, body.count("\n") + 1)
    return min(visual_lines * _BODY_LINE_HEIGHT + 16, _BODY_MAX_HEIGHT)


def show_load_errors_modal(errors: list[LoadError]) -> None:
    """Surface scanner load failures via the same modal the runner uses for
    uncaught exceptions. Combines all failures into one modal so a broken
    helper doesn't open N stacked popups."""
    if not errors:
        return
    base = TOOLS_DIR.parent
    parts = []
    for e in errors:
        try:
            label = str(e.path.relative_to(base))
        except ValueError:
            label = str(e.path)
        parts.append(f"{label}:\n{e.traceback.rstrip()}")
    body = "\n\n".join(parts)
    n = len(errors)
    title = f"Failed to load {n} tool{'s' if n != 1 else ''}"
    _show_error_modal(title, body)


def _show_error_modal(title: str, body: str) -> None:
    body_height = _estimate_body_height(body)
    with dpg.window(label=title, modal=True, show=True,
                    autosize=True, pos=(80, 80)) as win:
        dpg.bind_item_theme(win, _ensure_modal_chrome_theme())
        dpg.configure_item(win, on_close=lambda *_a, **_kw: dpg.delete_item(win))
        body_input = dpg.add_input_text(default_value=body, multiline=True, readonly=True,
                                        width=_BODY_WIDTH_PX, height=body_height)
        dpg.bind_item_theme(body_input, _ensure_modal_input_theme())
