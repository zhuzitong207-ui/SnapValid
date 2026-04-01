# SnapValid.py
# 键盘鼠标自动化 | OCR验证码识别 | 截图相似度校验
# 项目地址：https://github.com/taojy123/SnapValid.git (重命名版)
import sys
import json
import time
import os
import threading
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QTextEdit, QLabel,
                               QSpinBox, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from pynput import mouse, keyboard
import pyautogui
import datetime
import ctypes
import ctypes.wintypes
from screeninfo import get_monitors
import pygetwindow as gw
from UIFunc import Ui_MainWindow
from img_utils import ocr_recognize, image_compare, save_screenshot
from selector import ScreenSelector

# 全局热键状态
is_recording = False
is_replaying = False
record_list = []
start_time = 0
last_operation_time = 0
config = {}

# 日志信号类
class LogSignal(QObject):
    log_signal = Signal(str)

log_signal = LogSignal()

# 主窗口类
class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("SnapValid - 自动化截图校验工具")
        self.config = config
        self.script_path = ""
        self.replay_count = 1
        
        # 初始化日志
        log_signal.log_signal.connect(self.append_log)
        self.append_log("SnapValid 启动成功")
        self.append_log("快捷键：F9录制 | F10回放 | F11停止 | Ctrl+Alt+I OCR | Ctrl+Alt+S 截图对比")
        
        # 按钮绑定
        self.ui.btn_record.clicked.connect(self.start_record)
        self.ui.btn_replay.clicked.connect(self.start_replay)
        self.ui.btn_stop.clicked.connect(self.stop_all)
        self.ui.btn_load.clicked.connect(self.load_script)
        self.ui.spin_replay.valueChanged.connect(self.update_replay_count)
        
        # 初始化全局监听
        self.init_hotkey()

    def append_log(self, text):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_text = f"[{now}] {text}"
        self.ui.text_log.append(log_text)
        with open(self.config["log_path"], "a", encoding="utf-8") as f:
            f.write(log_text + "\n")

    def update_replay_count(self, value):
        self.replay_count = value

    def init_hotkey(self):
        def on_press(key):
            try:
                if key == keyboard.Key.f9:
                    self.start_record()
                elif key == keyboard.Key.f10:
                    self.start_replay()
                elif key == keyboard.Key.f11:
                    self.stop_all()
            except:
                pass

        self.hotkey_listener = keyboard.Listener(on_press=on_press)
        self.hotkey_listener.start()

    def check_display_mode(self):
        monitors = get_monitors()
        if len(monitors) > 1:
            self.append_log("警告：检测到多屏幕，请按 Win+P 切换为复制模式，避免坐标偏移")
            return False
        return True

    def max_browser(self):
        try:
            browsers = ["Chrome", "Edge", "Firefox", "浏览器"]
            for browser in browsers:
                try:
                    win = gw.getWindowsWithTitle(browser)[0]
                    win.maximize()
                    time.sleep(0.5)
                    break
                except:
                    continue
        except:
            pass

    def start_record(self):
        global is_recording, record_list, start_time, last_operation_time
        if is_replaying:
            self.append_log("请先停止回放")
            return
        if not self.check_display_mode():
            return
        is_recording = True
        record_list = []
        start_time = time.time()
        last_operation_time = start_time
        self.append_log("SnapValid 开始录制")
        
        # 启动鼠标监听
        self.mouse_listener = mouse.Listener(
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll)
        self.mouse_listener.start()
        
        # 启动键盘监听
        self.key_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release)
        self.key_listener.start()

    def on_mouse_click(self, x, y, button, pressed):
        if not is_recording:
            return
        if pressed:
            delay = time.time() - last_operation_time
            last_operation_time = time.time()
            record_list.append({
                "type": "click",
                "x": x, "y": y,
                "button": str(button),
                "delay": round(delay, 3)
            })
            self.append_log(f"录制点击：({x},{y})")

    def on_mouse_scroll(self, x, y, dx, dy):
        if not is_recording:
            return
        delay = time.time() - last_operation_time
        last_operation_time = time.time()
        record_list.append({
            "type": "scroll",
            "x": x, "y": y,
            "dy": dy,
            "delay": round(delay, 3)
        })

    def on_key_press(self, key):
        if not is_recording:
            return
        # 快捷键插入OCR
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            if keyboard.Key.alt_l and keyboard.KeyCode(char='i'):
                self.insert_ocr()
                return
        # 快捷键插入截图对比
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            if keyboard.Key.alt_l and keyboard.KeyCode(char='s'):
                self.insert_compare()
                return

    def on_key_release(self, key):
        if not is_recording:
            return
        try:
            delay = time.time() - last_operation_time
            last_operation_time = time.time()
            key_str = key.char if hasattr(key, 'char') else str(key)
            record_list.append({
                "type": "key",
                "key": key_str,
                "delay": round(delay, 3)
            })
        except:
            pass

    def insert_ocr(self):
        self.append_log("请框选验证码区域，按空格确认")
        selector = ScreenSelector()
        rect = selector.select()
        if rect:
            x1, y1, x2, y2 = rect
            img_path = save_screenshot(x1, y1, x2, y2, "ocr")
            delay = time.time() - last_operation_time
            last_operation_time = time.time()
            record_list.append({
                "type": "ocr",
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "img_path": img_path,
                "delay": round(delay, 3)
            })
            self.append_log(f"录制OCR：({x1},{y1},{x2},{y2})")

    def insert_compare(self):
        self.append_log("请框选校验区域，按空格确认")
        selector = ScreenSelector()
        rect = selector.select()
        if rect:
            x1, y1, x2, y2 = rect
            img_path = save_screenshot(x1, y1, x2, y2, "compare")
            delay = time.time() - last_operation_time
            last_operation_time = time.time()
            record_list.append({
                "type": "compare",
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "img_path": img_path,
                "delay": round(delay, 3)
            })
            self.append_log(f"录制截图校验：({x1},{y1},{x2},{y2})")

    def start_replay(self):
        global is_replaying
        if is_recording:
            self.append_log("请先停止录制")
            return
        if not record_list and not self.script_path:
            self.append_log("请先录制或加载脚本")
            return
        is_replaying = True
        self.check_display_mode()
        self.max_browser()
        self.append_log(f"SnapValid 开始回放，次数：{self.replay_count}")
        
        def replay():
            for i in range(self.replay_count):
                if not is_replaying:
                    break
                self.append_log(f"第 {i+1} 次回放")
                for op in record_list:
                    if not is_replaying:
                        break
                    time.sleep(op["delay"])
                    if op["type"] == "click":
                        pyautogui.click(op["x"], op["y"])
                        self.append_log(f"回放点击：({op['x']},{op['y']})")
                    elif op["type"] == "key":
                        pyautogui.press(op["key"])
                    elif op["type"] == "scroll":
                        pyautogui.scroll(op["dy"], op["x"], op["y"])
                    elif op["type"] == "ocr":
                        res = ocr_recognize(op["img_path"])
                        self.append_log(f"OCR识别结果：{res}")
                        with open(config["ocr_result_path"], "a", encoding="utf-8") as f:
                            f.write(f"{datetime.datetime.now()} OCR: {res}\n")
                    elif op["type"] == "compare":
                        score = image_compare(op["img_path"], op["x1"], op["y1"], op["x2"], op["y2"])
                        res = "PASS" if score >= config["similarity_threshold"] else "FAIL"
                        self.append_log(f"截图对比相似度：{score} 结果：{res}")
                        with open(config["compare_result_path"], "a", encoding="utf-8") as f:
                            f.write(f"{datetime.datetime.now()} SIM: {score} {res}\n")
                self.append_log(f"第 {i+1} 次回放完成")
            is_replaying = False
            self.append_log("SnapValid 回放全部完成")
        
        threading.Thread(target=replay, daemon=True).start()

    def stop_all(self):
        global is_recording, is_replaying
        is_recording = False
        is_replaying = False
        self.append_log("SnapValid 已停止")
        # 保存录制脚本
        if record_list:
            if not os.path.exists(config["script_save_path"]):
                os.makedirs(config["script_save_path"])
            save_path = os.path.join(config["script_save_path"], 
                                   f"script_{int(time.time())}.json")
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(record_list, f, ensure_ascii=False, indent=2)
            self.append_log(f"脚本已保存：{save_path}")

    def load_script(self):
        path, _ = QFileDialog.getOpenFileName(self, "加载脚本", "", "JSON (*.json)")
        if path:
            self.script_path = path
            global record_list
            with open(path, "r", encoding="utf-8") as f:
                record_list = json.load(f)
            self.append_log(f"加载脚本成功：{path}")

    def closeEvent(self, event):
        self.stop_all()
        event.accept()

def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "similarity_threshold": 0.9,
            "replay_times": 1,
            "log_path": "./operation_log.txt",
            "ocr_result_path": "./ocr_result.txt",
            "compare_result_path": "./compare_result.txt",
            "script_save_path": "./scripts/",
            "screenshot_temp_path": "./temp/"
        }

if __name__ == "__main__":
    config = load_config()
    app = QApplication(sys.argv)
    window = MainWindow(config)
    window.show()
    sys.exit(app.exec())
