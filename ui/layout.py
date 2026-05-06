"""Build/rebuild the main DearPyGui layout for the selected tool."""
from __future__ import annotations

import math
from typing import Any, Callable

import dearpygui.dearpygui as dpg

from core import scanner, settings
from core.dpi import _s
from core.scanner import ToolSpec

from . import theme
from .state import (
    DIM_COLOR,
    DYNAMIC_AREA,
    LABEL_COLUMN_WIDTH,
    MAIN_WINDOW,
    OUTPUTS_LAST_ACTION,
    TEXT_FIELD_WIDTH,
    THEME_ICON_SIZE,
    THEME_TOGGLE,
    TOOL_COMBO,
    TOP_BAR,
    TOP_SEPARATOR,
    TOP_SPACER,
    _state,
    add_tooltip,
    bind_bold,
)
from .widgets import build_inputs_section, build_outputs_section
from .runner import make_run_cb, show_load_errors_modal


def build_window(tools: list[ToolSpec], rescan: Callable[[], list[ToolSpec]]) -> None:
    _state["tools"] = tools
    _state["rescan"] = rescan

    saved_name = settings.load().get("selected_tool")
    initial = next((t for t in tools if t.name == saved_name), None) \
        or (tools[0] if tools else None)

    with dpg.window(tag=MAIN_WINDOW, label="Universal Executor",
                    no_title_bar=True, no_move=True, no_resize=True, no_collapse=True,
                    no_scrollbar=True):
        with dpg.group(horizontal=True, tag=TOP_BAR):
            dpg.add_text("Tool")
            dpg.add_combo(
                items=[t.name for t in tools],
                default_value=initial.name if initial else "",
                tag=TOOL_COMBO,
                callback=_on_tool_changed,
                width=_s(360),
            )
            dpg.add_button(label="Reload", callback=_on_reload)
            # Spacer width is recomputed in _fit_viewport_to_content so the
            # toggle stays glued to the right edge of the content area.
            dpg.add_spacer(width=_s(24), tag=TOP_SPACER)
            _build_theme_toggle()
        dpg.add_separator(tag=TOP_SEPARATOR)
        dpg.add_group(tag=DYNAMIC_AREA)

    dpg.set_primary_window(MAIN_WINDOW, True)
    _bind_no_scrollbar_theme(MAIN_WINDOW)
    _ensure_wheel_handler()
    _ensure_resize_handler()
    _ensure_key_handler()
    if initial is not None:
        _select_tool(initial)


def _build_theme_toggle() -> None:
    """Drawlist showing a sun (light mode) or moon (dark mode); click toggles."""
    dpg.add_drawlist(width=THEME_ICON_SIZE, height=THEME_ICON_SIZE, tag=THEME_TOGGLE)
    if not _state.get("theme_toggle_handler"):
        with dpg.item_handler_registry() as reg:
            dpg.add_item_clicked_handler(callback=_on_theme_toggle)
        _state["theme_toggle_handler"] = reg
    dpg.bind_item_handler_registry(THEME_TOGGLE, _state["theme_toggle_handler"])
    _redraw_theme_icon()


def _on_theme_toggle(*_args, **_kwargs):
    mode = theme.toggle_mode()
    _redraw_theme_icon()
    settings.update(theme=mode)


def _redraw_theme_icon() -> None:
    if not dpg.does_item_exist(THEME_TOGGLE):
        return
    dpg.delete_item(THEME_TOGGLE, children_only=True)
    palette = theme.current_palette()
    if theme.current_mode() == "dark":
        _draw_moon(THEME_TOGGLE, palette["TEXT"], palette["BG"])
    else:
        _draw_sun(THEME_TOGGLE, palette["TEXT"])


def _draw_sun(parent: str, fg: tuple) -> None:
    cx = cy = THEME_ICON_SIZE / 2
    r = THEME_ICON_SIZE * 0.20
    dpg.draw_circle((cx, cy), r, color=fg, fill=fg, parent=parent)
    inner = r + 3
    outer = THEME_ICON_SIZE / 2 - 1
    for i in range(8):
        a = i * math.pi / 4
        x1, y1 = cx + math.cos(a) * inner, cy + math.sin(a) * inner
        x2, y2 = cx + math.cos(a) * outer, cy + math.sin(a) * outer
        dpg.draw_line((x1, y1), (x2, y2), color=fg, thickness=2, parent=parent)


def _draw_moon(parent: str, fg: tuple, bg: tuple) -> None:
    """Crescent: a filled disk masked by a second disk in the window-bg color.

    The drawlist itself is transparent, so painting the mask in ``bg`` (the
    palette's WindowBg) blends seamlessly with the surrounding top bar.
    """
    cx = cy = THEME_ICON_SIZE / 2
    r = THEME_ICON_SIZE * 0.40
    dpg.draw_circle((cx, cy), r, color=fg, fill=fg, parent=parent)
    dpg.draw_circle((cx + r * 0.55, cy - r * 0.20), r * 0.92,
                    color=bg, fill=bg, parent=parent)


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


def _ensure_key_handler() -> None:
    """Re-run the last action when Enter is pressed in a focused input."""
    if _state.get("key_handler"):
        return
    with dpg.handler_registry():
        dpg.add_key_press_handler(key=dpg.mvKey_Return, callback=_on_enter)
        dpg.add_key_press_handler(key=dpg.mvKey_NumPadEnter, callback=_on_enter)
    _state["key_handler"] = True


def _on_enter(*_args, **_kwargs):
    tool = _state.get("current")
    if tool is None or not tool.funcs:
        return
    input_tags = _state.get("input_tags", {})
    if not any(dpg.is_item_focused(t) for t in input_tags.values()):
        return
    last = _state.get("last_func")
    fn = last if last in tool.funcs else tool.funcs[0]
    from . import runner
    runner._run(fn)


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
    _save_current_tool_state()
    new_tools = _state["rescan"]()
    _state["tools"] = new_tools
    new_names = {t.name for t in new_tools}
    _state["tool_states"] = {
        k: v for k, v in _state["tool_states"].items() if k in new_names
    }
    dpg.configure_item(TOOL_COMBO, items=[t.name for t in new_tools])
    show_load_errors_modal(scanner.last_load_errors())

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
    _state["last_func"] = None
    _state["last_status"] = None


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

    # Stretch (or shrink) the top-bar spacer so the theme toggle hugs the
    # right edge of whichever section ends up wider — the top bar or the
    # dynamic area below it. Converges in 1-2 resize cycles.
    if dpg.does_item_exist(TOP_SPACER):
        delta = int(round(dyn_size[0] - top_size[0]))
        if delta != 0:
            current = int(dpg.get_item_configuration(TOP_SPACER).get("width", _s(24)))
            new_spacer = max(0, current + delta)
            if new_spacer != current:
                dpg.configure_item(TOP_SPACER, width=new_spacer)


def _save_current_tool_state() -> None:
    """Snapshot the currently selected tool's widget values and last action.

    Stored raw (the strings/bools/enum-names DPG widgets return), so restoration
    is just ``dpg.set_value`` regardless of the input kind. Called before any
    tool switch or reload so unsubmitted edits aren't dropped on the floor.
    """
    current = _state.get("current")
    if current is None:
        return
    inputs: dict[str, Any] = {}
    for name, tag in _state.get("input_tags", {}).items():
        if dpg.does_item_exist(tag):
            inputs[name] = dpg.get_value(tag)
    last = _state.get("last_func")
    _state["tool_states"][current.name] = {
        "inputs": inputs,
        "last_func_name": last.name if last else None,
        "last_status": _state.get("last_status"),
    }


def _restore_tool_state(tool: ToolSpec) -> None:
    saved = _state["tool_states"].get(tool.name)
    if not saved:
        return
    for name, value in saved.get("inputs", {}).items():
        tag = _state["input_tags"].get(name)
        if tag is not None and dpg.does_item_exist(tag):
            dpg.set_value(tag, value)
    last_name = saved.get("last_func_name")
    if last_name:
        match = next((f for f in tool.funcs if f.name == last_name), None)
        if match is not None:
            _state["last_func"] = match
            status = saved.get("last_status")
            _state["last_status"] = status
            if dpg.does_item_exist(OUTPUTS_LAST_ACTION):
                label = (f"[{match.description}, {status}]"
                         if status else f"[{match.description}]")
                dpg.set_value(OUTPUTS_LAST_ACTION, label)


def _select_tool(tool: ToolSpec):
    _save_current_tool_state()
    _state["current"] = tool
    settings.update(selected_tool=tool.name)
    _clear_dynamic()
    parent = DYNAMIC_AREA

    # Actions
    actions_label = dpg.add_text("Actions", parent=parent)
    bind_bold(actions_label)
    if not tool.funcs:
        dpg.add_text("(no exported functions)", color=DIM_COLOR, parent=parent)
    else:
        with dpg.group(horizontal=True, parent=parent):
            for fn in tool.funcs:
                btn = dpg.add_button(label=fn.description, callback=make_run_cb(fn))
                add_tooltip(btn, fn.tooltip)

    # Inputs (left) and Outputs (right) side-by-side. The section width adds
    # room for table cell padding (~4px each side, two cells) on top of the
    # label+field columns; without the buffer, the rightmost widget's rounded
    # corners get clipped by the group bound and render as a vertical line.
    section_width = LABEL_COLUMN_WIDTH + TEXT_FIELD_WIDTH + _s(16)
    with dpg.group(horizontal=True, parent=parent):
        with dpg.group(width=section_width):
            build_inputs_section(tool)
        dpg.add_spacer(width=_s(24))
        with dpg.group(width=section_width):
            build_outputs_section(tool)

    _restore_tool_state(tool)

    # Resize handler may fire before the new layout has settled — re-measure
    # a couple of frames later to catch the final size.
    dpg.set_frame_callback(dpg.get_frame_count() + 2, _fit_viewport_to_content)
