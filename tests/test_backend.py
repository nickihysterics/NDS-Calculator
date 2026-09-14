import json

import pytest

import backend as bridge
from backend import ExportBackend


@pytest.fixture
def backend(monkeypatch):
    instance = ExportBackend()
    messages = []
    monkeypatch.setattr(
        instance, "_show_message", lambda *args, **kwargs: messages.append((args, kwargs))
    )
    instance.messages = messages
    return instance


@pytest.mark.parametrize("method", ["exportExcel", "exportWord"])
def test_invalid_export_stops_before_file_dialog(backend, monkeypatch, method):
    def unexpected(*args):
        pytest.fail("Некорректные данные не должны открывать файловый диалог")

    monkeypatch.setattr(backend, "_choose_path", unexpected)
    getattr(backend, method)(json.dumps({"rows": [{"name": "Товар", "gross": "NaN"}]}))
    assert backend.messages[-1][1]["error"]


@pytest.mark.parametrize("method,suffix", [("exportExcel", ".xlsx"), ("exportWord", ".docx")])
def test_backend_exports_and_reports_success(backend, monkeypatch, tmp_path, method, suffix):
    path = tmp_path / f"example{suffix}"
    monkeypatch.setattr(backend, "_choose_path", lambda *args: str(path))
    getattr(backend, method)(json.dumps({"rows": [{"name": "Товар", "gross": "122", "qty": "2"}]}))
    assert path.is_file()
    assert "сохранен" in backend.messages[-1][0][1]


def test_import_emits_normalized_rows(backend, monkeypatch, tmp_path):
    path = tmp_path / "example.xlsx"
    monkeypatch.setattr(backend, "_choose_path", lambda *args: str(path))
    backend.exportExcel(json.dumps({"rows": [{"name": "Товар", "gross": "122", "qty": "2"}]}))
    monkeypatch.setattr(
        bridge.QtWidgets.QFileDialog, "getOpenFileName", lambda *args: (str(path), "")
    )
    payloads = []
    backend.importDataReady.connect(payloads.append)
    backend.importExcel()
    rows = json.loads(payloads[0])["rows"]
    assert len(rows) == 1
    assert rows[0]["sum_gross"] == "244.00"
    assert rows[0]["qty"] == "2.000"


def test_invalid_json_and_settings_signal(backend):
    assert backend._load_payload("not json") is None
    assert backend._load_payload("[]") is None
    signals = []
    backend.settingsSaved.connect(lambda ok, message: signals.append(ok))
    backend.saveSettings('{"vatRate": "10"}')
    backend.saveSettings("[]")
    assert signals == [True, False]
