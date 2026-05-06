from unittest.mock import patch

import pytest

from core import dpi


@pytest.fixture(autouse=True)
def reset_scale():
    """Each test gets a clean SCALE=1.0; restore on the way out."""
    original = dpi.SCALE
    dpi.SCALE = 1.0
    yield
    dpi.SCALE = original


def test_s_rounds_to_int():
    dpi.SCALE = 1.5
    assert dpi._s(10) == 15
    assert dpi._s(20) == 30
    assert dpi._s(13) == 20  # 19.5 — banker's round, away from .5


def test_s_returns_int_type():
    dpi.SCALE = 2.0
    result = dpi._s(13)
    assert isinstance(result, int)
    assert result == 26


def test_s_identity_at_scale_1():
    dpi.SCALE = 1.0
    for v in (0, 1, 7, 18, 100, 1280):
        assert dpi._s(v) == v


def test_init_uses_override_when_positive():
    dpi.init(2.5)
    assert dpi.SCALE == 2.5


def test_init_ignores_zero_override():
    with patch.object(dpi, "detect_scale", return_value=1.7):
        dpi.init(0)
        assert dpi.SCALE == 1.7


def test_init_ignores_none_override():
    with patch.object(dpi, "detect_scale", return_value=2.0):
        dpi.init(None)
        assert dpi.SCALE == 2.0


def test_init_ignores_non_numeric_override():
    with patch.object(dpi, "detect_scale", return_value=1.5):
        dpi.init("2.0")  # string, not float
        assert dpi.SCALE == 1.5


def test_detect_scale_clamps_low():
    with patch.object(dpi.sys, "platform", "linux"), \
         patch.object(dpi, "_detect_scale_linux", return_value=0.5):
        assert dpi.detect_scale() == 1.0


def test_detect_scale_clamps_high():
    with patch.object(dpi.sys, "platform", "linux"), \
         patch.object(dpi, "_detect_scale_linux", return_value=10.0):
        assert dpi.detect_scale() == 4.0


def test_detect_scale_falls_back_on_exception():
    with patch.object(dpi.sys, "platform", "linux"), \
         patch.object(dpi, "_detect_scale_linux", side_effect=RuntimeError):
        assert dpi.detect_scale() == 1.0


def test_detect_scale_macos_returns_one():
    with patch.object(dpi.sys, "platform", "darwin"):
        assert dpi.detect_scale() == 1.0


def test_linux_gdk_scale_takes_precedence(monkeypatch):
    monkeypatch.setenv("GDK_SCALE", "2")
    monkeypatch.setenv("QT_SCALE_FACTOR", "1.5")
    assert dpi._detect_scale_linux() == 2.0


def test_linux_qt_scale_used_when_gdk_absent(monkeypatch):
    monkeypatch.delenv("GDK_SCALE", raising=False)
    monkeypatch.setenv("QT_SCALE_FACTOR", "1.75")
    assert dpi._detect_scale_linux() == 1.75


def test_linux_invalid_gdk_falls_through(monkeypatch):
    monkeypatch.setenv("GDK_SCALE", "not_a_number")
    monkeypatch.setenv("QT_SCALE_FACTOR", "1.5")
    assert dpi._detect_scale_linux() == 1.5


def test_linux_xrdb_fallback(monkeypatch):
    monkeypatch.delenv("GDK_SCALE", raising=False)
    monkeypatch.delenv("QT_SCALE_FACTOR", raising=False)

    class FakeResult:
        stdout = "Xft.antialias:\t1\nXft.dpi:\t192\nXft.hinting:\t1\n"

    import subprocess as _sp
    with patch.object(_sp, "run", return_value=FakeResult()):
        assert dpi._detect_scale_linux() == pytest.approx(2.0)


def test_linux_xrdb_missing_returns_one(monkeypatch):
    monkeypatch.delenv("GDK_SCALE", raising=False)
    monkeypatch.delenv("QT_SCALE_FACTOR", raising=False)
    import subprocess as _sp
    with patch.object(_sp, "run", side_effect=FileNotFoundError):
        assert dpi._detect_scale_linux() == 1.0


def test_enable_awareness_noop_off_windows():
    with patch.object(dpi.sys, "platform", "linux"):
        # Should not raise — there's no ctypes path executed on linux.
        dpi.enable_awareness()
