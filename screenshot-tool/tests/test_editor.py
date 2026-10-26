"""Test des Editors ohne Bildschirm: QT_QPA_PLATFORM=offscreen python -m unittest"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import QApplication

from editor import Canvas, EditorWindow

app = QApplication.instance() or QApplication([])


def white_pixmap(width=200, height=120):
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("white"))
    return pixmap


def draw(canvas, tool, start, end):
    canvas.tool = tool
    canvas.begin(QPointF(*start))
    canvas.drag(QPointF(*end))
    canvas.end(QPointF(*end))


class CanvasTest(unittest.TestCase):
    def test_rect_draws_frame_and_undo_removes_it(self):
        canvas = Canvas(white_pixmap())
        canvas.color = QColor("#ff0000")
        draw(canvas, "rect", (20, 20), (100, 80))
        self.assertEqual(canvas.annotation_count(), 1)

        image = canvas.render_image()
        self.assertEqual(image.size().width(), 200)
        self.assertEqual(image.pixelColor(20, 50), QColor("#ff0000"))
        self.assertEqual(image.pixelColor(60, 50), QColor("white"))

        canvas.undo()
        self.assertEqual(canvas.annotation_count(), 0)
        self.assertEqual(canvas.render_image().pixelColor(20, 50), QColor("white"))

    def test_all_shape_tools_add_an_annotation(self):
        canvas = Canvas(white_pixmap())
        for tool in ("rect", "ellipse", "arrow", "line", "pen", "marker"):
            draw(canvas, tool, (10, 10), (90, 70))
        self.assertEqual(canvas.annotation_count(), 6)

    def test_click_without_drag_adds_nothing(self):
        canvas = Canvas(white_pixmap())
        draw(canvas, "rect", (30, 30), (31, 31))
        self.assertEqual(canvas.annotation_count(), 0)

    def test_marker_is_translucent(self):
        canvas = Canvas(white_pixmap())
        canvas.color = QColor("#ff0000")
        draw(canvas, "marker", (10, 60), (190, 60))
        pixel = canvas.render_image().pixelColor(100, 60)
        self.assertEqual(pixel.red(), 255)
        self.assertGreater(pixel.green(), 60)

    def test_text_is_added(self):
        canvas = Canvas(white_pixmap(300, 100))
        canvas.add_text(QPointF(10, 10), "Hallo")
        self.assertEqual(canvas.annotation_count(), 1)
        image = canvas.render_image()
        non_white = any(
            image.pixelColor(x, y) != QColor("white")
            for x in range(10, 120)
            for y in range(10, 50)
        )
        self.assertTrue(non_white)


class SaveTest(unittest.TestCase):
    def test_save_writes_png_with_annotation(self):
        with tempfile.TemporaryDirectory() as folder:
            window = EditorWindow(white_pixmap(), folder)
            window.canvas.color = QColor("#0000ff")
            draw(window.canvas, "ellipse", (20, 20), (180, 100))
            window.save()
            files = list(Path(folder).glob("Screenshot *.png"))
            self.assertEqual(len(files), 1)
            image = QImage(str(files[0]))
            self.assertEqual((image.width(), image.height()), (200, 120))
            self.assertTrue(
                any(
                    image.pixelColor(x, 60) == QColor("#0000ff")
                    for x in range(15, 30)
                )
            )


if __name__ == "__main__":
    unittest.main()
