"""Run an exported tool function and surface any uncaught error in a modal."""
from __future__ import annotations

import textwrap
import traceback

import dearpygui.dearpygui as dpg

from core.scanner import FuncSpec

from . import layout, widgets


_BODY_WRAP_PX = 680
_BODY_WRAP_CHARS = 78          # rough char count that fits in _BODY_WRAP_PX at font 18
_BODY_LINE_HEIGHT = 22         # font 18 + line spacing
_BODY_MAX_HEIGHT = 400         # past this the child_window scrolls instead of growing


_modal_chrome_theme: int | str | None = None


def _ensure_modal_chrome_theme() -> int | str:
    """Theme that shrinks the modal title-bar so the close (X) hover bubble
    fills its height. Scoped to mvWindowAppItem so child widgets keep the
    normal FramePadding.
    """
    global _modal_chrome_theme
    if _modal_chrome_theme is None or not dpg.does_item_exist(_modal_chrome_theme):
        with dpg.theme() as t:
            with dpg.theme_component(dpg.mvWindowAppItem):
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 1)
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
    visual_lines = 0
    for line in body.splitlines() or [""]:
        visual_lines += max(1, len(textwrap.wrap(line, width=_BODY_WRAP_CHARS)) or 1)
    return min(max(1, visual_lines) * _BODY_LINE_HEIGHT + 16, _BODY_MAX_HEIGHT)


def _show_error_modal(title: str, body: str) -> None:
    body_height = _estimate_body_height(body)
    with dpg.window(label=title, modal=True, show=True,
                    autosize=True, pos=(80, 80)) as win:
        dpg.bind_item_theme(win, _ensure_modal_chrome_theme())
        with dpg.child_window(width=_BODY_WRAP_PX + 20, height=body_height, border=False):
            dpg.add_text(body, wrap=_BODY_WRAP_PX)
        dpg.add_separator()
        dpg.add_button(label="Close", callback=lambda *_a, **_kw: dpg.delete_item(win))
