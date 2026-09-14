"""Рендерит собственную SVG-иконку в ICO для Windows-сборки (нужен Pillow)."""

from io import BytesIO
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

root = Path(__file__).resolve().parents[1]
canvas = QImage(256, 256, QImage.Format_ARGB32)
canvas.fill(0)
painter = QPainter(canvas)
QSvgRenderer(str(root / "src/ui/icon.svg")).render(painter)
painter.end()
data = QByteArray()
buffer = QBuffer(data)
buffer.open(QIODevice.WriteOnly)
canvas.save(buffer, "PNG")
Image.open(BytesIO(bytes(data))).save(
    root / "assets/app.ico", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)]
)
