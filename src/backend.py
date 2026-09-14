"""Backend PySide6 для обмена данными с UI и экспорта."""

import json

from PySide6 import QtCore, QtWidgets

from calculations import normalize_rows
from excel_io import read_excel, write_excel
from settings_store import load_settings, save_settings
from word_export import write_word


class ExportBackend(QtCore.QObject):
    """Слой обмена между UI (WebChannel) и логикой экспорта."""

    importDataReady = QtCore.Signal(str)
    settingsReady = QtCore.Signal(str)
    settingsSaved = QtCore.Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent

    @QtCore.Slot(str)
    def exportExcel(self, payload):
        """Экспортирует данные в Excel."""
        data = self._load_payload(payload)
        if data is None:
            return
        try:
            vat_rate, rows = normalize_rows(data)
        except ValueError as exc:
            self._show_message("Проверьте данные", str(exc), error=True)
            return
        if not rows:
            self._show_message("Экспорт", "Нет данных для экспорта.")
            return
        path = self._choose_path("Сохранить Excel", "specification.xlsx", "Excel (*.xlsx)", ".xlsx")
        if not path:
            return
        try:
            write_excel(path, vat_rate, rows)
        except ModuleNotFoundError:
            self._show_message(
                "Экспорт",
                "Не найден модуль openpyxl. Установите: pip install openpyxl",
                error=True,
            )
            return
        except Exception as exc:
            self._show_message("Экспорт", f"Ошибка при сохранении Excel: {exc}", error=True)
            return
        self._show_message("Экспорт", f"Excel файл сохранен:\n{path}")

    @QtCore.Slot(str)
    def exportWord(self, payload):
        """Экспортирует данные в Word."""
        data = self._load_payload(payload)
        if data is None:
            return
        try:
            vat_rate, rows = normalize_rows(data)
        except ValueError as exc:
            self._show_message("Проверьте данные", str(exc), error=True)
            return
        settings = data.get("settings") if isinstance(data, dict) else None
        if not rows:
            self._show_message("Экспорт", "Нет данных для экспорта.")
            return
        path = self._choose_path("Сохранить Word", "specification.docx", "Word (*.docx)", ".docx")
        if not path:
            return
        try:
            write_word(path, vat_rate, rows, settings)
        except ModuleNotFoundError:
            message = "Не найден модуль python-docx. Установите: pip install python-docx"
            self._show_message("Экспорт", message, error=True)
            return
        except Exception as exc:
            self._show_message("Экспорт", f"Ошибка при сохранении Word: {exc}", error=True)
            return
        self._show_message("Экспорт", f"Word файл сохранен:\n{path}")

    @QtCore.Slot()
    def requestSettings(self):
        """Возвращает настройки UI при старте."""
        settings = load_settings()
        payload = json.dumps(settings, ensure_ascii=False)
        self.settingsReady.emit(payload)

    @QtCore.Slot(str)
    def saveSettings(self, payload):
        """Сохраняет настройки из UI."""
        data = self._load_payload(payload)
        if data is None:
            self.settingsSaved.emit(False, "Некорректные данные настроек.")
            return
        if not isinstance(data, dict):
            self.settingsSaved.emit(False, "Некорректный формат настроек.")
            return
        try:
            save_settings(data)
        except Exception as exc:
            self.settingsSaved.emit(False, f"Ошибка сохранения: {exc}")
            return
        self.settingsSaved.emit(True, "Настройки сохранены.")

    @QtCore.Slot()
    def importExcel(self):
        """Импортирует Excel и отправляет строки в UI."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.parent_widget,
            "Импорт Excel",
            "",
            "Excel (*.xlsx *.xlsm *.xltx *.xltm)",
        )
        if not path:
            return
        try:
            raw_rows = read_excel(path)
            _, normalized = normalize_rows(
                {"vatRate": load_settings()["vatRate"], "rows": raw_rows}
            )
            rows = [{key: str(value) for key, value in row.items()} for row in normalized]
        except ModuleNotFoundError:
            self._show_message(
                "Импорт",
                "Не найден модуль openpyxl. Установите: pip install openpyxl",
                error=True,
            )
            return
        except Exception as exc:
            self._show_message(
                "Импорт",
                f"Ошибка при импорте Excel: {exc}",
                error=True,
            )
            return
        if not rows:
            self._show_message("Импорт", "В файле нет данных для импорта.")
            return

        payload = json.dumps({"rows": rows}, ensure_ascii=False)
        self.importDataReady.emit(payload)

    def _load_payload(self, payload):
        """Пытается прочитать JSON payload от UI."""
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            self._show_message(
                "Экспорт",
                "Не удалось прочитать данные.",
                error=True,
            )
            return None
        if not isinstance(data, dict):
            self._show_message(
                "Экспорт",
                "Некорректный формат данных.",
                error=True,
            )
            return None
        return data

    def _choose_path(self, title, suggested_name, filter_text, extension):
        """Запрашивает путь сохранения через стандартный диалог."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.parent_widget, title, suggested_name, filter_text
        )
        if not path:
            return None
        if not path.lower().endswith(extension):
            path += extension
        return path

    def _show_message(self, title, text, error=False):
        """Показывает информационное или ошибочное окно."""
        if error:
            QtWidgets.QMessageBox.critical(self.parent_widget, title, text)
        else:
            QtWidgets.QMessageBox.information(self.parent_widget, title, text)
