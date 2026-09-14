import pytest


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("PYNDS_SETTINGS_DIR", str(tmp_path / "settings"))
