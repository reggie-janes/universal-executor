"""Build/rebuild the main DearPyGui layout for the selected tool."""
from __future__ import annotations

import traceback
from typing import Any, Callable

import dearpygui.dearpygui as dpg

from .scanner import FuncSpec, ToolSpec, VarSpec, is_choices_kind, is_enum_kind


MAIN_WINDOW = "uex_main"
TOOL_COMBO = "uex_tool_combo"
TOP_BAR = "uex_top_bar"
TOP_SEPARATOR = "uex_top_separator"
DYNAMIC_AREA = "uex_dynamic_area"
STATUS = "uex_status"

LABEL_COLUMN_WIDTH = 120
NUMBER_FIELD_WIDTH = 140
COMBO_FIELD_WIDTH = 200
TEXT_FIELD_WIDTH = 260


_state: dict[str, Any] = {
    "tools": [],
    "current": None,
    "input_tags": {},
    "output_tags": {},
    "rescan": None,
}


def build_window(tools: list[ToolSpec], rescan: Callable[[], list[ToolSpec]]) -> None:
    _state["tools"] = tools
    _state["rescan"] = rescan

    with dpg.window(tag=MAIN_WINDOW, label="Universal Executor",
                    no_title_bar=True, no_move=True, no_resize=True, no_collapse=True,
                    no_scrollbar=True):
        with dpg.group(horizontal=True, tag=TOP_BAR):
            dpg.add_text("Tool")
            dpg.add_combo(
                items=[t.name for t in tools],
                default_value=tools[0].name if tools else "",
                tag=TOOL_COMBO,
                callback=_on_tool_changed,
                width=360,
            )
            dpg.add_button(label="Reload", callback=_on_reload)
        dpg.add_separator(tag=TOP_SEPARATOR)
        dpg.add_group(tag=DYNAMIC_AREA)

    dpg.set_primary_window(MAIN_WINDOW, True)
    _bind_no_scrollbar_theme(MAIN_WINDOW)
    _ensure_wheel_handler()
    _ensure_resize_handler()
    if tools:
        _select_tool(tools[0])


def _bind_no_scrollbar_theme(item: str) -> None:
    """Force scrollbar size to 0 for ``item``.

    The ``no_scrollbar=True`` window flag does not reliably suppress the
    transient scrollbar that appears for a frame or two when the new tool's
    content is taller than the previous viewport (before the resize callback
    fires and grows the viewport). Setting ``ScrollbarSize`` to 0 on this
    window only makes the bar zero pixels wide — invisible — without
    affecting other windows like the error modal.
    """
    with dpg.theme() as no_sb:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 0)
    dpg.bind_item_theme(item, no_sb)


def _ensure_wheel_handler() -> None:
    if _state.get("wheel_handler"):
        return
    with dpg.handler_registry():
        dpg.add_mouse_wheel_handler(callback=_on_wheel)
    _state["wheel_handler"] = True


def _ensure_resize_handler() -> None:
    if _state.get("resize_handler"):
        return
    with dpg.item_handler_registry() as reg:
        dpg.add_item_resize_handler(callback=_fit_viewport_to_content)
    dpg.bind_item_handler_registry(DYNAMIC_AREA, reg)
    _state["resize_handler"] = True


def _on_wheel(sender, app_data):
    """Cycle the tool combo when the wheel turns over (or while focused on) it.

    DPG mouse-wheel ``app_data`` is +1 for wheel-forward (scroll up),
    -1 for wheel-backward (scroll down). Scroll up = previous, scroll
    down = next, with wrap-around at the ends.
    """
    delta = int(app_data) if app_data else 0
    if delta == 0:
        return
    if not (dpg.is_item_hovered(TOOL_COMBO) or dpg.is_item_focused(TOOL_COMBO)):
        return
    tools = _state["tools"]
    if not tools:
        return
    current = _state["current"]
    idx = 0
    if current is not None:
        for i, t in enumerate(tools):
            if t.name == current.name:
                idx = i
                break
    new_idx = (idx - delta) % len(tools)
    new_tool = tools[new_idx]
    dpg.set_value(TOOL_COMBO, new_tool.name)
    _select_tool(new_tool)


def _on_tool_changed(sender, app_data):
    selected = next((t for t in _state["tools"] if t.name == app_data), None)
    if selected is not None:
        _select_tool(selected)


def _on_reload():
    new_tools = _state["rescan"]()
    _state["tools"] = new_tools
    dpg.configure_item(TOOL_COMBO, items=[t.name for t in new_tools])

    if not new_tools:
        dpg.set_value(TOOL_COMBO, "")
        _clear_dynamic()
        _state["current"] = None
        return

    current_name = _state["current"].name if _state["current"] else None
    keep = next((t for t in new_tools if t.name == current_name), None) or new_tools[0]
    dpg.set_value(TOOL_COMBO, keep.name)
    _select_tool(keep)


def _clear_dynamic():
    dpg.delete_item(DYNAMIC_AREA, children_only=True)
    _state["input_tags"].clear()
    _state["output_tags"].clear()


def _fit_viewport_to_content(*_args, **_kwargs):
    """Resize the OS viewport to hug the natural size of the window contents.

    Uses screen-relative rect_min/rect_max of the topmost (TOP_BAR) and
    bottommost (DYNAMIC_AREA) children of MAIN_WINDOW, then mirrors the top
    inset onto the bottom so the window has symmetric ImGui padding.
    """
    top_min = dpg.get_item_rect_min(TOP_BAR)
    dyn_max = dpg.get_item_rect_max(DYNAMIC_AREA)
    top_size = dpg.get_item_rect_size(TOP_BAR)
    dyn_size = dpg.get_item_rect_size(DYNAMIC_AREA)
    if not top_size or not dyn_size:
        return

    pad_top = top_min[1]  # screen-y of first child = window padding above it
    pad_left = top_min[0]
    content_h = dyn_max[1] - top_min[1]
    content_w = max(top_size[0], dyn_size[0])

    chrome_w = dpg.get_viewport_width() - dpg.get_viewport_client_width()
    chrome_h = dpg.get_viewport_height() - dpg.get_viewport_client_height()

    new_w = content_w + 2 * pad_left + chrome_w
    new_h = content_h + 2 * pad_top + chrome_h

    if abs(new_w - dpg.get_viewport_width()) > 1:
        dpg.set_viewport_width(new_w)
    if abs(new_h - dpg.get_viewport_height()) > 1:
        dpg.set_viewport_height(new_h)


def _select_tool(tool: ToolSpec):
    _state["current"] = tool
    _clear_dynamic()
    parent = DYNAMIC_AREA

    # Actions
    dpg.add_text("Actions", parent=parent)
    if not tool.funcs:
        dpg.add_text("(no exported functions)", color=(161, 161, 170, 255), parent=parent)
    else:
        with dpg.group(horizontal=True, parent=parent):
            for fn in tool.funcs:
                dpg.add_button(label=fn.description, callback=_make_run_cb(fn))

    # Inputs (left) and Outputs (right) side-by-side.
    section_width = LABEL_COLUMN_WIDTH + TEXT_FIELD_WIDTH
    with dpg.group(horizontal=True, parent=parent):
        with dpg.group(width=section_width):
            _build_inputs_section(tool)
        dpg.add_spacer(width=24)
        with dpg.group(width=section_width):
            _build_outputs_section(tool)

    dpg.add_separator(parent=parent)
    dpg.add_text("Ready.", tag=STATUS, parent=parent, color=(161, 161, 170, 255))

    # Resize handler may fire before the new layout has settled — re-measure
    # a couple of frames later to catch the final size.
    dpg.set_frame_callback(dpg.get_frame_count() + 2, _fit_viewport_to_content)


def _build_inputs_section(tool: ToolSpec) -> None:
    dpg.add_text("Inputs")
    if not tool.inputs:
        dpg.add_text("(no inputs)", color=(161, 161, 170, 255))
        return
    with dpg.table(header_row=False, resizable=False,
                   policy=dpg.mvTable_SizingFixedFit,
                   borders_innerH=False, borders_innerV=False):
        dpg.add_table_column(width_fixed=True, init_width_or_weight=LABEL_COLUMN_WIDTH)
        dpg.add_table_column()
        for var in tool.inputs:
            with dpg.table_row():
                dpg.add_text(var.description)
                tag = _make_input_widget(var, tool.module)
                _state["input_tags"][var.name] = tag


def _build_outputs_section(tool: ToolSpec) -> None:
    dpg.add_text("Outputs")
    if not tool.outputs:
        dpg.add_text("(no outputs)", color=(161, 161, 170, 255))
        return
    with dpg.table(header_row=False, resizable=False,
                   policy=dpg.mvTable_SizingFixedFit,
                   borders_innerH=False, borders_innerV=False):
        dpg.add_table_column(width_fixed=True, init_width_or_weight=LABEL_COLUMN_WIDTH)
        dpg.add_table_column()
        for var in tool.outputs:
            with dpg.table_row():
                dpg.add_text(var.description)
                tag = _make_output_widget(var, tool.module)
                _state["output_tags"][var.name] = tag


def _make_input_widget(var: VarSpec, module) -> int | str:
    current = getattr(module, var.name, None)
    kind = var.kind
    if kind is int:
        return dpg.add_input_int(default_value=int(current or 0), width=NUMBER_FIELD_WIDTH)
    if kind is float:
        return dpg.add_input_float(default_value=float(current or 0.0),
                                   format="%.6g", width=NUMBER_FIELD_WIDTH)
    if kind is bool:
        return dpg.add_checkbox(default_value=bool(current))
    if is_enum_kind(kind):
        items = [m.name for m in kind]
        default = current.name if current is not None and current.__class__ is kind else (items[0] if items else "")
        return dpg.add_combo(items=items, default_value=default, width=COMBO_FIELD_WIDTH)
    if is_choices_kind(kind):
        items = [str(c) for c in kind]
        default = str(current) if current is not None else (items[0] if items else "")
        return dpg.add_combo(items=items, default_value=default, width=COMBO_FIELD_WIDTH)
    return dpg.add_input_text(default_value=str(current), readonly=True, width=TEXT_FIELD_WIDTH)


def _make_output_widget(var: VarSpec, module) -> int | str:
    current = getattr(module, var.name, "")
    return dpg.add_input_text(default_value=str(current), readonly=True, width=TEXT_FIELD_WIDTH)


def _push_inputs(tool: ToolSpec) -> None:
    for var in tool.inputs:
        tag = _state["input_tags"][var.name]
        raw = dpg.get_value(tag)
        kind = var.kind
        if is_enum_kind(kind):
            value = kind[raw] if raw in kind.__members__ else getattr(tool.module, var.name)
        elif is_choices_kind(kind):
            value = next((c for c in kind if str(c) == raw), raw)
        else:
            value = raw
        setattr(tool.module, var.name, value)


def _pull_outputs(tool: ToolSpec) -> None:
    for var in tool.outputs:
        tag = _state["output_tags"][var.name]
        value = getattr(tool.module, var.name)
        dpg.set_value(tag, str(value))


def _make_run_cb(fn: FuncSpec):
    """Build a DPG callback that ignores all args and invokes ``fn``.

    DPG passes (sender, app_data, user_data) positionally based on the
    callback's arity, so closures are safer than lambda default-arg tricks.
    """
    def _cb(*_args, **_kwargs):
        _run(fn)
    return _cb


def _run(fn: FuncSpec) -> None:
    tool = _state["current"]
    if tool is None:
        return
    dpg.set_value(STATUS, f"Running {fn.name}()...")
    try:
        _push_inputs(tool)
        fn.callable()
        _pull_outputs(tool)
        dpg.set_value(STATUS, f"Last run: {fn.name}() OK")
    except Exception:
        tb = traceback.format_exc()
        dpg.set_value(STATUS, f"Last run: {fn.name}() FAILED")
        _show_error_modal(f"Error in {fn.name}()", tb)


def _show_error_modal(title: str, body: str) -> None:
    with dpg.window(label=title, modal=True, show=True,
                    width=720, height=420, pos=(80, 80)) as win:
        dpg.add_text(body, wrap=680)
        dpg.add_separator()
        dpg.add_button(label="Close", callback=lambda *_a, **_kw: dpg.delete_item(win))
