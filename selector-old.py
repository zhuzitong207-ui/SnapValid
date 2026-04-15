import sys
from PySide6.QtWidgets import QApplication, QWidget, QRubberBand
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QGuiApplication, QPen, QColor, QPainter

class ScreenSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")
        
        self.origin = None
        self.rubber = QRubberBand(QRubberBand.Rectangle, self)
        self.selected_rect = None

        screen = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen)

    def paintEvent(self, event):
        painter = QPainter(self)
        color = QColor(0, 0, 0, 100)
        painter.fillRect(self.rect(), color)

        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.globalPos()
            self.rubber.setGeometry(QRect(self.origin, QPoint()))
            self.rubber.show()

    def mouseMoveEvent(self, event):
        if self.origin:
            self.rubber.setGeometry(QRect(self.origin, event.globalPos()).normalized())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected_rect = self.rubber.geometry()
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.selected_rect = self.rubber.geometry()
            self.close()
        if event.key() == Qt.Key_Escape:
            self.selected_rect = None
            self.close()

def get_area():
    app = QApplication.instance()
    selector = ScreenSelector()
    selector.show()
    app.exec()
    rect = selector.selected_rect
    if rect:
        return (rect.left(), rect.top(), rect.right(), rect.bottom())
    return None
