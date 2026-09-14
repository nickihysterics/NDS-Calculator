"""Smoke-проверка настоящего Qt WebChannel без файловых диалогов."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

from PySide6 import QtCore, QtWidgets  # noqa: E402

from app import MainWindow  # noqa: E402


def main():
    with tempfile.TemporaryDirectory() as directory:
        os.environ["PYNDS_SETTINGS_DIR"] = directory
        app = QtWidgets.QApplication([])
        window = MainWindow()
        window.show()
        completed = False

        def inspect(value):
            nonlocal completed
            if value == "ready":
                completed = True
                window.view.page().runJavaScript('document.querySelector("#loadDemo").click()')
                QtCore.QTimer.singleShot(300, verify)
            else:
                QtCore.QTimer.singleShot(100, poll)

        def poll():
            window.view.page().runJavaScript(
                'typeof loadingSettings !== "undefined" && !loadingSettings && backend ? "ready" : "wait"',
                inspect,
            )

        def verify():
            window.view.page().runJavaScript(
                'document.querySelector("#sumGross").textContent', finish
            )

        def finish(value):
            if value.replace("\u00a0", " ") != "4 209,00 ₽":
                app.exit(1)
            else:
                print("Desktop OK: Qt WebEngine + WebChannel + settings + demo totals")
                app.exit(0)

        def timeout():
            print(f"Desktop timeout; connected={completed}")
            app.exit(1)

        QtCore.QTimer.singleShot(100, poll)
        QtCore.QTimer.singleShot(20000, timeout)
        code = app.exec()
        window.view.setPage(None)
        return code


if __name__ == "__main__":
    sys.exit(main())
