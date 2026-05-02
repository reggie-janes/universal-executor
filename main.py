from pathlib import Path

import dearpygui.dearpygui as dpg

import settings
from ui import layout, scanner, theme

ROOT = Path(__file__).parent
TOOLS_DIR = ROOT / "tools"
ASSETS_DIR = ROOT / "assets"


def _rescan():
    return scanner.discover_tools(TOOLS_DIR)


def _save_window_pos() -> None:
    x, y = dpg.get_viewport_pos()
    settings.update(window_x=int(x), window_y=int(y))


def main() -> None:
    saved = settings.load()
    dpg.create_context()
    viewport_kwargs: dict = dict(
        title="Universal Executor",
        width=1280,
        height=800,
        small_icon=str(ASSETS_DIR / "app.ico"),
        large_icon=str(ASSETS_DIR / "app.ico"),
    )
    if isinstance(saved.get("window_x"), int) and isinstance(saved.get("window_y"), int):
        viewport_kwargs["x_pos"] = saved["window_x"]
        viewport_kwargs["y_pos"] = saved["window_y"]
    dpg.create_viewport(**viewport_kwargs)
    theme.apply(ASSETS_DIR, mode=saved.get("theme"))
    layout.build_window(_rescan(), rescan=_rescan)
    dpg.setup_dearpygui()
    dpg.set_exit_callback(_save_window_pos)
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
