import sys
from pathlib import Path

import dearpygui.dearpygui as dpg

from core import scanner, settings
from ui import layout, theme

ASSETS_DIR = Path(__file__).parent / "assets"


def _save_window_pos() -> None:
    x, y = dpg.get_viewport_pos()
    settings.update(window_x=int(x), window_y=int(y))


# Holds references that must outlive _lock_window_chrome_win32 so the WndProc
# callback isn't garbage-collected while Windows is still calling into it.
_WIN32_WNDPROC_STATE: dict = {}


def _lock_window_chrome_win32(title: str) -> None:
    # Block user-driven maximize and border resize while leaving DPG's own
    # programmatic resize (used by the auto-fit handler) untouched. Style-bit
    # stripping (WS_MAXIMIZEBOX / WS_THICKFRAME) would also work, but in
    # practice it desyncs DPG's cached viewport size and breaks set_viewport_*.
    # Instead we subclass the WndProc and swallow the relevant input messages.
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
    WM_NCHITTEST = 0x0084
    WM_NCLBUTTONDBLCLK = 0x00A3
    WM_SYSCOMMAND = 0x0112
    SC_MAXIMIZE = 0xF030
    HTCAPTION = 2
    HTMAXBUTTON = 9
    HT_RESIZE = {10, 11, 12, 13, 14, 15, 16, 17}  # HTLEFT..HTBOTTOMRIGHT
    HTBORDER = 18
    GW_OWNER = 4

    def wndproc_impl(hwnd, msg, wparam, lparam):
        old = _WIN32_WNDPROC_STATE.get("old", 0)
        if msg == WM_SYSCOMMAND and (wparam & 0xFFF0) == SC_MAXIMIZE:
            return 0
        if msg == WM_NCLBUTTONDBLCLK and wparam == HTCAPTION:
            return 0
        if msg == WM_NCHITTEST:
            result = user32.CallWindowProcW(old, hwnd, msg, wparam, lparam)
            if result == HTMAXBUTTON or result in HT_RESIZE:
                return HTBORDER
            return result
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
        # Visually grey out the maximize button. WS_MAXIMIZEBOX-only strip
        # (without WS_THICKFRAME) leaves DPG's resize plumbing intact, but
        # SWP_FRAMECHANGED is required to make the caption buttons actually
        # repaint in their new disabled state. We defer this past the initial
        # paint — applied immediately, the title-bar repaint doesn't take.
        hwnd = find_hwnd()
        if not hwnd:
            return
        style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        user32.SetWindowLongW(hwnd, GWL_STYLE, style & ~WS_MAXIMIZEBOX)
        user32.SetWindowPos(
            hwnd, None, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
        )

    # WndProc subclass: synchronous (we deliberately avoid set_frame_callback
    # here because layout._select_tool schedules the initial auto-fit on
    # frame N+2 and DPG's per-frame slot would overwrite it).
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
    layout.build_window(scanner.rescan(), rescan=scanner.rescan)
    dpg.setup_dearpygui()
    dpg.set_exit_callback(_save_window_pos)
    dpg.show_viewport()
    _lock_window_chrome_win32("Universal Executor")
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
