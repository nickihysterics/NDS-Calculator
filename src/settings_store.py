"""Чтение и запись настроек спецификации."""

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path


def _settings_write_path():
    """Настройки пользователя хранятся отдельно от исходников и сборки."""
    override = os.environ.get("PYNDS_SETTINGS_DIR")
    if override:
        directory = Path(override).expanduser()
    elif sys.platform == "win32":
        directory = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "PyNDS"
    elif sys.platform == "darwin":
        directory = Path.home() / "Library" / "Application Support" / "PyNDS"
    else:
        directory = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "pynds"
    return directory / "spec_settings.json"


def _settings_read_path():
    user_path = _settings_write_path()
    if user_path.exists():
        return user_path
    return Path(__file__).resolve().parent / "spec_settings.json"


def default_settings():
    """Формирует настройки спецификации по умолчанию."""
    today = datetime.now().strftime("%d.%m.%Y")
    return {
        "vatRate": "22",
        "appendix_no": "2",
        "supply_contract_line": "к Договору поставки № ____ от __.__.____г.",
        "spec_line": f"Спецификация № ____ от {today} г.",
        "contract_line": "к Договору № ____ от __.__.____ г.",
        "spec_date": today,
        "detail_rows": [
            ["Срок поставки:", ""],
            ["Реквизиты грузополучателя:", ""],
            ["Реквизиты поставщика:", ""],
            ["Транспорт поставки", ""],
            ["Величина транспортных расходов", ""],
            ["Базис поставки", ""],
            ["Станция (пункт) отправления", ""],
            ["Станция (пункт) назначения", ""],
            ["Способ оплаты", ""],
            ["Условия оплаты", ""],
            ["Условия гарантии", ""],
            ["Дополнительные условия", ""],
            ["Срок действия настоящей Спецификации:", ""],
        ],
        "buyer_position": "Директор Филиала",
        "seller_position": "Директор",
        "buyer_org": "ООО «________________»",
        "seller_org": "ООО «________________»",
        "buyer_sign": "__________________",
        "seller_sign": "__________________",
    }


def load_settings():
    """Загружает настройки из файла и объединяет с дефолтными."""
    settings = default_settings()
    settings_path = _settings_read_path()
    if settings_path.exists():
        try:
            raw_text = settings_path.read_text(encoding="utf-8")
            file_settings = json.loads(raw_text)
        except (OSError, UnicodeError, json.JSONDecodeError):
            file_settings = {}
        if isinstance(file_settings, dict):
            settings.update(file_settings)
    return sanitize_settings(settings)


def sanitize_settings(data):
    """Оставляет только известные поля и исправляет повреждённые структуры."""
    from decimal import Decimal

    from calculations import number

    result = default_settings()
    for key, default in result.items():
        if key != "detail_rows" and isinstance(data.get(key), str):
            result[key] = data[key]
    details = data.get("detail_rows")
    if isinstance(details, list):
        result["detail_rows"] = [
            [str(row[0]), str(row[1]) if len(row) > 1 else ""]
            for row in details
            if isinstance(row, (list, tuple)) and row
        ]
    try:
        result["vatRate"] = str(number(result["vatRate"], "Ставка НДС", Decimal(100), Decimal(22)))
    except ValueError:
        result["vatRate"] = "22"
    return result


def save_settings(data):
    """Сохраняет настройки в JSON файл."""
    settings_path = _settings_write_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    data = sanitize_settings(data)
    # Запись в той же директории и атомарная замена защищают от обрыва записи.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=settings_path.parent,
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(settings_path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def load_spec_context(settings_override=None):
    """Возвращает итоговый контекст для спецификации с подстановками."""
    context = load_settings()
    if isinstance(settings_override, dict):
        context.update(settings_override)

    context = sanitize_settings(context)
    detail_rows = context.get("detail_rows")
    if isinstance(detail_rows, list):
        context["detail_rows"] = [
            (str(item[0]), str(item[1]))
            for item in detail_rows
            if isinstance(item, (list, tuple)) and len(item) >= 2
        ]

    spec_date = context.get("spec_date") or datetime.now().strftime("%d.%m.%Y")
    spec_line = context.get("spec_line") or (f"Спецификация № ____ от {spec_date} г.")
    if "__DATE__" in spec_line:
        spec_line = spec_line.replace("__DATE__", spec_date)
    context["spec_line"] = spec_line
    context["spec_date"] = spec_date

    return context
