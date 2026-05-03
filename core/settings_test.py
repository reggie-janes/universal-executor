from pathlib import Path

import pytest

from core import settings


@pytest.fixture
def tmp_settings(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "SETTINGS_PATH", path)
    return path


def test_load_missing_file_returns_empty(tmp_settings):
    assert not tmp_settings.exists()
    assert settings.load() == {}


def test_load_malformed_json_returns_empty(tmp_settings):
    tmp_settings.write_text("{not valid json")
    assert settings.load() == {}


def test_load_non_dict_returns_empty(tmp_settings):
    tmp_settings.write_text("[1, 2, 3]")
    assert settings.load() == {}


def test_save_then_load_roundtrips(tmp_settings):
    payload = {"theme": "dark", "window_x": 100, "selected_tool": "calc"}
    settings.save(payload)
    assert settings.load() == payload


def test_update_merges_into_existing(tmp_settings):
    settings.save({"theme": "light", "window_x": 100})
    result = settings.update(theme="dark", window_y=200)
    assert result == {"theme": "dark", "window_x": 100, "window_y": 200}
    assert settings.load() == result


def test_update_on_missing_file_creates_it(tmp_settings):
    assert not tmp_settings.exists()
    result = settings.update(theme="dark")
    assert result == {"theme": "dark"}
    assert tmp_settings.exists()


def test_update_on_malformed_file_overwrites(tmp_settings):
    tmp_settings.write_text("garbage")
    result = settings.update(theme="dark")
    assert result == {"theme": "dark"}
    assert settings.load() == {"theme": "dark"}
