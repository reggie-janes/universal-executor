import sys
from pathlib import Path

import dearpygui.dearpygui as dpg

from core import dpi, scanner, settings

ASSETS_DIR = Path(__file__).parent / "assets"
_REQUIRED_ASSETS = ("app.ico", "Roboto-Regular.ttf", "Roboto-Bold.ttf")


def _missing_assets() -> list[Path]:
    return [ASSETS_DIR / name for name in _REQUIRED_ASSETS
            if not (ASSETS_DIR / name).exists()]


def _save_window_pos() -> None:
    x, y = dpg.get_viewport_pos()
    settings.update(window_x=int(x), window_y=int(y))


# Holds references that must outlive _disable_maximize_win32 so the WndProc
# callback isn't garbage-collected while Windows is still calling into it.
_WIN32_WNDPROC_STATE: dict = {}


def _disable_maximize_win32(title: str) -> None:
    # GLFW's resizable=False (passed to create_viewport) already strips
    # WS_THICKFRAME — border drag-resize is gone on every platform. But the
    # DPG-bundled GLFW build doesn't strip WS_MAXIMIZEBOX, so the maximize
    # button still works and double-clicking the title bar still maximizes.
    # Fix that here on Windows: strip the style bit (visual disable) and
    # subclass WndProc to swallow the maximize messages that DefWindowProc
    # still produces. WS_MAXIMIZEBOX-only strip is safe — it leaves DPG's
    # resize plumbing intact, unlike a WS_THICKFRAME strip which desyncs
    # DPG's cached viewport size.
    if not sys.platform.startswith("win"):
        return
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    LRESULT = ctypes.c_ssize_t
    WNDPROC = ctypes.WINFUNCTYPE(
        LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
    )

    user32.FindWindowW.restype = wintypes.HWND
    user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    user32.GetWindowLongW.restype = wintypes.LONG
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.SetWindowLongW.restype = wintypes.LONG
    user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.UINT,
    ]
    user32.CallWindowProcW.restype = LRESULT
    user32.CallWindowProcW.argtypes = [
        ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
    ]
    user32.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetWindow.restype = wintypes.HWND

    GWL_STYLE = -16
    GWLP_WNDPROC = -4
    WS_MAXIMIZEBOX = 0x00010000
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_NOZORDER = 0x0004
    SWP_FRAMECHANGED = 0x0020
    WM_NCLBUTTONDBLCLK = 0x00A3
    WM_SYSCOMMAND = 0x0112
    SC_MAXIMIZE = 0xF030
    HTCAPTION = 2
    GW_OWNER = 4

    def wndproc_impl(hwnd, msg, wparam, lparam):
        old = _WIN32_WNDPROC_STATE.get("old", 0)
        if msg == WM_SYSCOMMAND and (wparam & 0xFFF0) == SC_MAXIMIZE:
            return 0
        if msg == WM_NCLBUTTONDBLCLK and wparam == HTCAPTION:
            return 0
        return user32.CallWindowProcW(old, hwnd, msg, wparam, lparam)

    def find_hwnd():
        hwnd = user32.FindWindowW(None, title)
        if hwnd:
            return hwnd
        pid = kernel32.GetCurrentProcessId()
        found = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def cb(hwnd, _lparam):
            owner_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner_pid))
            if (owner_pid.value == pid
                    and user32.IsWindowVisible(hwnd)
                    and not user32.GetWindow(hwnd, GW_OWNER)):
                found.append(hwnd)
                return False
            return True

        user32.EnumWindows(cb, 0)
        return found[0] if found else None

    def install_wndproc():
        if "proc" in _WIN32_WNDPROC_STATE:
            return True
        hwnd = find_hwnd()
        if not hwnd:
            return False
        proc = WNDPROC(wndproc_impl)
        old = user32.GetWindowLongPtrW(hwnd, GWLP_WNDPROC)
        _WIN32_WNDPROC_STATE["old"] = old
        _WIN32_WNDPROC_STATE["proc"] = proc  # keep alive
        user32.SetWindowLongPtrW(
            hwnd, GWLP_WNDPROC,
            ctypes.cast(proc, ctypes.c_void_p).value,
        )
        return True

    def grey_out_maximize_button():
        # SWP_FRAMECHANGED forces the caption buttons to actually repaint in
        # their new disabled state. Deferred past the initial paint —
        # applied immediately, the title-bar repaint doesn't take.
        hwnd = find_hwnd()
        if not hwnd:
            return
        style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        user32.SetWindowLongW(hwnd, GWL_STYLE, style & ~WS_MAXIMIZEBOX)
        user32.SetWindowPos(
            hwnd, None, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
        )

    if not install_wndproc():
        def retry_wndproc():
            install_wndproc()
        for f in (50, 100, 200):
            dpg.set_frame_callback(f, retry_wndproc)
    # Style strip / repaint: pick a frame past the initial frame-2 auto-fit
    # so we don't overwrite it.
    dpg.set_frame_callback(10, grey_out_maximize_button)


def main() -> None:
    saved = settings.load()
    # DPI awareness must precede create_context so GLFW sees a DPI-aware
    # process at window creation; init must precede the ui imports below
    # because ui/state.py reads dpi._s at module import time.
    dpi.enable_awareness()
    dpi.init(saved.get("ui_scale"))
    from ui import layout, runner, theme  # deferred — see above
    missing = _missing_assets()
    dpg.create_context()
    # resizable=False blocks user drag-resize and the maximize button on every
    # platform GLFW supports. Programmatic set_viewport_width/height (used by
    # the auto-fit handler) keeps working — the hint only gates user input.
    viewport_kwargs: dict = dict(
        title="Universal Executor",
        width=dpi._s(1280),
        height=dpi._s(800),
        resizable=False,
    )
    icon = ASSETS_DIR / "app.ico"
    if icon.exists():
        viewport_kwargs["small_icon"] = str(icon)
        viewport_kwargs["large_icon"] = str(icon)
    if isinstance(saved.get("window_x"), int) and isinstance(saved.get("window_y"), int):
        viewport_kwargs["x_pos"] = saved["window_x"]
        viewport_kwargs["y_pos"] = saved["window_y"]
    dpg.create_viewport(**viewport_kwargs)
    theme.apply(ASSETS_DIR, mode=saved.get("theme"))
    layout.build_window(scanner.rescan(), rescan=scanner.rescan)
    if missing:
        runner.show_missing_assets_modal(missing)
    runner.show_load_errors_modal(scanner.last_load_errors())
    dpg.setup_dearpygui()
    dpg.set_exit_callback(_save_window_pos)
    dpg.show_viewport()
    _disable_maximize_win32("Universal Executor")
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
