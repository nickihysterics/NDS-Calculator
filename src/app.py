"""Локальное приложение Qt WebEngine; запуск: python src/app.py."""

import json
import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView

from backend import ExportBackend
from constants import APP_TITLE
from settings_store import save_settings


class MainWindow(QtWidgets.QMainWindow):
    """Окно с локальным HTML и мостом к файловым операциям Python."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1320, 900)
        self.setMinimumSize(900, 640)
        icon = Path(__file__).resolve().parent / "ui" / "icon.svg"
        self.setWindowIcon(QtGui.QIcon(str(icon)))
        self._close_approved = False
        self._checking_close = False
        self.view = QWebEngineView(self)
        self.view.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)
        self.setCentralWidget(self.view)
        self.channel = QWebChannel(self.view)
        self.backend = ExportBackend(self)
        self.channel.registerObject("backend", self.backend)
        self.view.page().setWebChannel(self.channel)
        ui_path = Path(__file__).resolve().parent / "ui" / "index.html"
        if not ui_path.is_file():
            raise FileNotFoundError(f"Не найден интерфейс: {ui_path}")
        self.view.load(QtCore.QUrl.fromLocalFile(str(ui_path)))

    def closeEvent(self, event):
        """Предупреждает о таблице в памяти и завершает автосохранение настроек."""
        if self._close_approved:
            event.accept()
            return
        event.ignore()
        if self._checking_close:
            return
        self._checking_close = True
        self.view.page().runJavaScript(
            'typeof getPayload === "function" && !loadingSettings ? JSON.stringify(getPayload()) : ""',
            self._confirm_close,
        )

    def _confirm_close(self, payload):
        self._checking_close = False
        data = json.loads(payload) if payload else {}
        if data.get("rows"):
            answer = QtWidgets.QMessageBox.question(
                self,
                "Закрыть PyNDS?",
                "Таблица хранится в памяти. Сохраните её в Excel, если она нужна. Закрыть окно?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if answer != QtWidgets.QMessageBox.Yes:
                return
        if data.get("settings"):
            try:
                save_settings(data["settings"])
            except OSError as exc:
                QtWidgets.QMessageBox.warning(self, "Настройки не сохранены", str(exc))
                return
        self._close_approved = True
        self.close()


def main():
    """Запускает приложение из исходников или из комплекта сборки."""
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("PyNDS")
    app.setOrganizationName("PyNDS")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
