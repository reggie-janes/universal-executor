"""Hi-DPI / 4K display support.

Detects the OS DPI scale factor once at startup and exposes ``_s(x)`` so the
UI layer can route every pixel-denominated literal through it. Without this,
non-DPI-aware processes get bitmap-stretched by the OS on hi-res displays
(visible as blurry text), and even after opting into DPI awareness the
hardcoded 96-DPI layout would render at a fraction of its intended size.

Usage from ``main()`` — must run before ``dpg.create_context``:

    dpi.enable_awareness()           # Windows-only opt-in
    dpi.init(saved.get("ui_scale"))  # populates SCALE
    from ui import ...               # only now — ui/state.py reads _s at import

The ``ui_scale`` settings.json key overrides auto-detect.
"""
from __future__ import annotations

import sys


SCALE: float = 1.0


def enable_awareness() -> None:
    """Mark the process per-monitor DPI aware. Windows-only; no-op elsewhere.

    On Linux there's no equivalent process flag — apps render to whatever
    pixel grid the compositor hands them. macOS handles Retina natively
    via GLFW. Idempotent; safe to call multiple times.
    """
    if not sys.platform.startswith("win"):
        return
    import ctypes

    # SetProcessDpiAwarenessContext takes a HANDLE-sized value; without an
    # explicit c_void_p, ctypes encodes -4 as a 32-bit c_int and the API
    # receives 0x00000000FFFFFFFC on x64 — it silently returns FALSE without
    # raising, so we have to inspect the return value to know it failed and
    # fall through. Same return-check applies to the other two: BOOL/HRESULT
    # failures don't raise either.
    candidates = (
        # PMv2 (Win 10 1703+): correct DPI on every monitor, handles drag.
        # BOOL: returns non-zero on success.
        lambda: bool(ctypes.windll.user32.SetProcessDpiAwarenessContext(
            ctypes.c_void_p(-4))),
        # PerMonitor (Win 8.1+): correct at startup, no live re-DPI on drag.
        # HRESULT: returns 0 (S_OK) on success.
        lambda: ctypes.windll.shcore.SetProcessDpiAwareness(2) == 0,
        # System (Vista+): single DPI for the lifetime of the process.
        # BOOL: returns non-zero on success.
        lambda: bool(ctypes.windll.user32.SetProcessDPIAware()),
    )
    for fn in candidates:
        try:
            if fn():
                return
        except (OSError, AttributeError):
            continue


def _detect_scale_windows() -> float:
    import ctypes

    try:
        dpi = ctypes.windll.user32.GetDpiForSystem()
    except (OSError, AttributeError):
        try:
            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32
            hdc = user32.GetDC(0)
            dpi = gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            user32.ReleaseDC(0, hdc)
        except (OSError, AttributeError):
            return 1.0
    return dpi / 96.0


def _detect_scale_linux() -> float:
    import os
    import subprocess

    # GDK_SCALE: GNOME's primary hidpi knob; many Wayland compositors set it
    # for GTK clients automatically.
    raw = os.environ.get("GDK_SCALE")
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    # QT_SCALE_FACTOR: KDE/Qt; can be fractional.
    raw = os.environ.get("QT_SCALE_FACTOR")
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    # X11 fallback: xrdb's Xft.dpi resource. xrdb may be missing on minimal
    # systems (containers, headless), hence the wide except.
    try:
        out = subprocess.run(
            ["xrdb", "-query"], capture_output=True, text=True, timeout=1
        ).stdout
        for line in out.splitlines():
            if line.startswith("Xft.dpi:"):
                return float(line.split(":", 1)[1].strip()) / 96.0
    except (FileNotFoundError, subprocess.SubprocessError, ValueError):
        pass
    return 1.0


def detect_scale() -> float:
    """OS DPI scale factor (1.0 == 96 DPI). Clamped to [1.0, 4.0]; 1.0 fallback."""
    try:
        if sys.platform.startswith("win"):
            scale = _detect_scale_windows()
        elif sys.platform.startswith("linux"):
            scale = _detect_scale_linux()
        else:
            scale = 1.0  # darwin: GLFW handles Retina natively
    except Exception:
        scale = 1.0
    return max(1.0, min(4.0, scale))


def init(override: float | None) -> float:
    """Set module-level SCALE from override (settings.json) or auto-detect.

    Must run before any ``ui.*`` module imports — those modules call ``_s``
    at import time to scale their constants.
    """
    global SCALE
    if isinstance(override, (int, float)) and override > 0:
        SCALE = float(override)
    else:
        SCALE = detect_scale()
    return SCALE


def _s(x: int | float) -> int:
    """Scale a logical-pixel literal to a physical-pixel int."""
    return int(round(x * SCALE))
