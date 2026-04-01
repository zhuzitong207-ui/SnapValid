# SnapValid 屏幕区域选择工具
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import Qt, QPoint, QRect

class ScreenSelector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_selecting = False
        self.result = None

    def paintEvent(self, event):
        painter = QPainter(self)
        color = QColor(0, 0, 0, 100)
        painter.fillRect(self.rect(), color)
        if not self.start_point.isNull() and not self.end_point.isNull():
            select_rect = QRect(self.start_point, self.end_point)
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(select_rect, Qt.transparent)
            pen = QPen(QColor(0, 255, 0), 2)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(pen)
            painter.drawRect(select_rect)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.result = (self.start_point.x(), self.start_point.y(),
                         self.end_point.x(), self.end_point.y())
            self.close()
        elif event.key() == Qt.Key_Escape:
            self.result = None
            self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.is_selecting = True

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.end_point = event.pos()
            self.is_selecting = False
            self.update()

    def select(self):
        self.exec()
        return self.result
