"""Editor zum Markieren, Umrahmen und Speichern von Screenshots."""
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QFont,
    QImage,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QFileDialog,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QToolBar,
)

MIN_DRAG = 3


class Canvas(QGraphicsView):
    """Zeichenfläche: das Bild als Hintergrund, Markierungen als eigene Elemente."""

    changed = Signal()

    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.tool = "rect"
        self.color = QColor("#ff3b30")
        self.width = 6

        self._annotations = []
        self._current = None
        self._active_tool = None
        self._start = QPointF()
        self._path = None

    def _make_pen(self):
        color = QColor(self.color)
        width = float(self.width)
        if self.tool == "marker":
            color.setAlpha(110)
            width = max(14.0, width * 4)
        pen = QPen(color, width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return pen

    def _arrow_path(self, start, end):
        path = QPainterPath(start)
        path.lineTo(end)
        length = QLineF(end, start).length()
        if length < 1:
            return path
        head = min(max(14.0, self.width * 4.0), length)
        for delta in (25, -25):
            side = QLineF(end, start)
            side.setLength(head)
            side.setAngle(side.angle() + delta)
            path.moveTo(end)
            path.lineTo(side.p2())
        return path

    def begin(self, pos):
        self._start = pos
        self._active_tool = self.tool
        if self.tool == "text":
            text, ok = QInputDialog.getText(self, "Text", "Text eingeben:")
            if ok and text.strip():
                self.add_text(pos, text)
            self._active_tool = None
            return

        pen = self._make_pen()
        if self.tool in ("pen", "marker"):
            self._path = QPainterPath(pos)
            item = QGraphicsPathItem(self._path)
        elif self.tool == "rect":
            item = QGraphicsRectItem(QRectF(pos, pos))
        elif self.tool == "ellipse":
            item = QGraphicsEllipseItem(QRectF(pos, pos))
        elif self.tool == "line":
            item = QGraphicsLineItem(QLineF(pos, pos))
        elif self.tool == "arrow":
            item = QGraphicsPathItem()
        else:
            return
        item.setPen(pen)
        self._scene.addItem(item)
        self._current = item

    def drag(self, pos):
        item = self._current
        if item is None:
            return
        tool = self._active_tool
        if tool in ("pen", "marker"):
            self._path.lineTo(pos)
            item.setPath(self._path)
        elif tool in ("rect", "ellipse"):
            item.setRect(QRectF(self._start, pos).normalized())
        elif tool == "line":
            item.setLine(QLineF(self._start, pos))
        elif tool == "arrow":
            item.setPath(self._arrow_path(self._start, pos))

    def end(self, pos):
        item = self._current
        if item is None:
            return
        self.drag(pos)
        self._current = None
        if (pos - self._start).manhattanLength() < MIN_DRAG:
            self._scene.removeItem(item)
            return
        self._annotations.append(item)
        self.changed.emit()

    def add_text(self, pos, text):
        item = QGraphicsTextItem(text)
        font = QFont()
        font.setPointSize(max(14, int(self.width) * 4 + 8))
        font.setBold(True)
        item.setFont(font)
        item.setDefaultTextColor(self.color)
        item.setPos(pos)
        self._scene.addItem(item)
        self._annotations.append(item)
        self.changed.emit()

    def undo(self):
        if self._annotations:
            self._scene.removeItem(self._annotations.pop())
            self.changed.emit()

    def annotation_count(self):
        return len(self._annotations)

    def render_image(self):
        rect = self._scene.sceneRect()
        image = QImage(int(rect.width()), int(rect.height()), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._scene.render(painter, QRectF(image.rect()), rect)
        painter.end()
        return image

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.begin(self.mapToScene(event.position().toPoint()))

    def mouseMoveEvent(self, event):
        if self._current is not None:
            self.drag(self.mapToScene(event.position().toPoint()))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.end(self.mapToScene(event.position().toPoint()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class EditorWindow(QMainWindow):
    TOOLS = [
        ("rect", "Rahmen"),
        ("ellipse", "Kreis"),
        ("arrow", "Pfeil"),
        ("line", "Linie"),
        ("pen", "Stift"),
        ("marker", "Textmarker"),
        ("text", "Text"),
    ]

    def __init__(self, pixmap, save_dir):
        super().__init__()
        self.setWindowTitle("Screenshot bearbeiten")
        self.save_dir = Path(save_dir)
        self.canvas = Canvas(pixmap)
        self.setCentralWidget(self.canvas)

        bar = QToolBar("Werkzeuge")
        bar.setMovable(False)
        self.addToolBar(bar)

        group = QActionGroup(self)
        for key, label in self.TOOLS:
            action = QAction(label, self, checkable=True)
            action.triggered.connect(lambda _checked, k=key: self._set_tool(k))
            group.addAction(action)
            bar.addAction(action)
            if key == self.canvas.tool:
                action.setChecked(True)

        bar.addSeparator()
        self.color_action = QAction("Farbe", self)
        self.color_action.triggered.connect(self._choose_color)
        bar.addAction(self.color_action)
        self._update_color_icon()

        bar.addWidget(QLabel(" Stärke "))
        self.width_box = QSpinBox()
        self.width_box.setRange(1, 40)
        self.width_box.setValue(self.canvas.width)
        self.width_box.valueChanged.connect(self._set_width)
        bar.addWidget(self.width_box)

        bar.addSeparator()
        self._add_action(bar, "Rückgängig", QKeySequence.StandardKey.Undo, self.canvas.undo)
        self._add_action(bar, "Kopieren", QKeySequence.StandardKey.Copy, self.copy_to_clipboard)
        self._add_action(bar, "Speichern", QKeySequence.StandardKey.Save, self.save)
        self._add_action(bar, "Speichern unter …", QKeySequence.StandardKey.SaveAs, self.save_as)

        self.resize(min(pixmap.width() + 40, 1400), min(pixmap.height() + 120, 900))

    def _add_action(self, bar, label, shortcut, slot):
        action = QAction(label, self)
        action.setShortcut(shortcut)
        action.triggered.connect(slot)
        bar.addAction(action)
        return action

    def _set_tool(self, key):
        self.canvas.tool = key

    def _set_width(self, value):
        self.canvas.width = value

    def _choose_color(self):
        color = QColorDialog.getColor(self.canvas.color, self, "Farbe wählen")
        if color.isValid():
            self.canvas.color = color
            self._update_color_icon()

    def _update_color_icon(self):
        swatch = QPixmap(16, 16)
        swatch.fill(self.canvas.color)
        from PySide6.QtGui import QIcon

        self.color_action.setIcon(QIcon(swatch))

    def copy_to_clipboard(self):
        QApplication.clipboard().setImage(self.canvas.render_image())
        self.statusBar().showMessage("In die Zwischenablage kopiert", 3000)

    def save(self):
        name = datetime.now().strftime("Screenshot %Y-%m-%d %H.%M.%S.png")
        self._write(self.save_dir / name)

    def save_as(self):
        start = str(self.save_dir / datetime.now().strftime("Screenshot %Y-%m-%d %H.%M.%S.png"))
        path, _ = QFileDialog.getSaveFileName(self, "Speichern unter", start, "PNG (*.png)")
        if path:
            self._write(Path(path))

    def _write(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        if self.canvas.render_image().save(str(path)):
            self.statusBar().showMessage(f"Gespeichert: {path}", 6000)
        else:
            QMessageBox.warning(self, "Fehler", f"Konnte nicht speichern:\n{path}")
