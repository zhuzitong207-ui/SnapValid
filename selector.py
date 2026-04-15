# selector.py
import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QColor, QGuiApplication

class Selector(QDialog):
    """全屏区域选择器，返回用户框选的矩形坐标"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowFullScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)

        self.origin = QPoint()
        self.rect = QRect()
        self.drawing = False

        # 提示标签
        self.label = QLabel("请按住鼠标左键拖拽选择区域，松开后确认", self)
        self.label.setStyleSheet("color: white; background: rgba(0,0,0,150); padding: 8px; border-radius: 4px;")
        self.label.adjustSize()
        self.label.move(20, 20)

        # 确认按钮（右下角）
        self.confirm_btn = QPushButton("确认使用此区域", self)
        self.confirm_btn.clicked.connect(self.accept)
        self.confirm_btn.setStyleSheet("background: #4CAF50; color: white; padding: 8px 16px; border-radius: 4px;")
        self.confirm_btn.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        # 半透明黑色遮罩
        painter.fillRect(self.rect(), QColor(0, 0, 0, 180))
        if not self.rect.isNull():
            # 清除选中区域内的遮罩
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(self.rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            # 绘制红色边框
            pen = QPen(QColor(255, 0, 0), 2)
            painter.setPen(pen)
            painter.drawRect(self.rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.origin = event.pos()
            self.rect = QRect(self.origin, self.origin)

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.rect = QRect(self.origin, event.pos()).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.update()
            if self.rect.width() > 5 and self.rect.height() > 5:
                self.confirm_btn.show()
                self.confirm_btn.move(self.width() - self.confirm_btn.width() - 20,
                                      self.height() - self.confirm_btn.height() - 20)
            else:
                self.rect = QRect()

    def get_selected_region(self):
        """返回 (x1, y1, x2, y2) 屏幕绝对坐标"""
        if self.rect.isNull():
            return (0, 0, 0, 0)
        return (self.rect.x(), self.rect.y(),
                self.rect.x() + self.rect.width(),
                self.rect.y() + self.rect.height())

# 独立测试入口
if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    sel = Selector()
    if sel.exec() == QDialog.Accepted:
        x1, y1, x2, y2 = sel.get_selected_region()
        print(f"Selected region: ({x1},{y1}) -> ({x2},{y2})")
    sys.exit()