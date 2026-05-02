"""Run an exported tool function and surface any uncaught error in a modal."""
from __future__ import annotations

import traceback

import dearpygui.dearpygui as dpg

from core.scanner import FuncSpec

from . import layout, widgets


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
    if dpg.does_item_exist(layout.OUTPUTS_LAST_ACTION):
        dpg.set_value(layout.OUTPUTS_LAST_ACTION, f"[{fn.description}]")
    dpg.set_value(layout.STATUS, f"Running {fn.name}()...")
    try:
        widgets.push_inputs(tool)
        fn.callable()
        widgets.pull_outputs(tool)
        dpg.set_value(layout.STATUS, f"Last run: {fn.name}() OK")
    except Exception:
        tb = traceback.format_exc()
        dpg.set_value(layout.STATUS, f"Last run: {fn.name}() FAILED")
        _show_error_modal(f"Error in {fn.name}()", tb)


def _show_error_modal(title: str, body: str) -> None:
    with dpg.window(label=title, modal=True, show=True,
                    width=720, height=420, pos=(80, 80)) as win:
        dpg.add_text(body, wrap=680)
        dpg.add_separator()
        dpg.add_button(label="Close", callback=lambda *_a, **_kw: dpg.delete_item(win))
