import json

from settings_store import _settings_write_path, load_settings, load_spec_context, save_settings


def test_settings_are_outside_source_and_roundtrip(tmp_path):
    save_settings({"vatRate": "10", "buyer_org": "Учебная организация"})
    assert _settings_write_path().is_relative_to(tmp_path)
    assert load_settings()["buyer_org"] == "Учебная организация"
    assert load_settings()["vatRate"] == "10"
    assert not list(_settings_write_path().parent.glob("*.tmp"))


def test_corrupt_file_falls_back_to_defaults():
    path = _settings_write_path()
    path.parent.mkdir(parents=True)
    path.write_text("{broken", encoding="utf-8")
    assert load_settings()["vatRate"] == "22"


def test_malformed_details_and_unknown_keys_are_sanitized():
    save_settings(
        {
            "vatRate": "NaN",
            "detail_rows": [["Срок"], None, ["Оплата", "Перевод", "extra"]],
            "secret": "drop",
        }
    )
    saved = json.loads(_settings_write_path().read_text(encoding="utf-8"))
    assert "secret" not in saved
    assert saved["vatRate"] == "22"
    context = load_spec_context()
    assert context["detail_rows"] == [("Срок", ""), ("Оплата", "Перевод")]
