from pathlib import Path

import dearpygui.dearpygui as dpg

import settings
from ui import layout, scanner, theme

ROOT = Path(__file__).parent
TOOLS_DIR = ROOT / "tools"
ASSETS_DIR = ROOT / "assets"


def _rescan():
    return scanner.discover_tools(TOOLS_DIR)


def main() -> None:
    dpg.create_context()
    dpg.create_viewport(
        title="Universal Executor",
        width=1280,
        height=800,
        small_icon=str(ASSETS_DIR / "app.ico"),
        large_icon=str(ASSETS_DIR / "app.ico"),
    )
    theme.apply(ASSETS_DIR, mode=settings.load().get("theme"))
    layout.build_window(_rescan(), rescan=_rescan)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
