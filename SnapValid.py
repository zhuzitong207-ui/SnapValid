# SnapValid.py
# 主程序：录制/回放自动化脚本，支持截图比对、OCR验证码识别
# 依赖：PySide6, pyautogui, keyboard, pynput, pillow, imagehash, ddddocr

import sys
import os
import json
import time
import threading
from datetime import datetime

# ---------- 路径与配置初始化（必须在其他导入之前）----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")

os.makedirs(SCRIPTS_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# 加载配置文件
def load_config():
    if not os.path.exists(CONFIG_PATH):
        default = {
            "similarity_threshold": 0.85,
            "action_pause": 0.08,
            "replay_speed": 1.0,
            "ocr_language": "eng"
        }
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=4)
        return default
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()

# 设置全局 pyautogui 参数
import pyautogui
pyautogui.PAUSE = config.get("action_pause", 0.08)
pyautogui.FAILSAFE = True

# ---------- DPI 感知（Windows）----------
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# ---------- 导入第三方库 ----------
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QListWidget, QTextEdit,
                               QLabel, QFileDialog, QMessageBox, QInputDialog)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QAction, QKeySequence

import keyboard
from pynput import mouse, keyboard as pynput_keyboard

# 导入自定义图像工具
import img_utils
from selector import Selector

# ---------- 动作类型常量 ----------
ACTION_CLICK = "click"
ACTION_MOVE = "move"
ACTION_KEYDOWN = "keydown"
ACTION_KEYUP = "keyup"
ACTION_WAIT = "wait"
ACTION_SCREENSHOT = "screenshot"
ACTION_OCR = "ocr"

# ---------- 录制线程 ----------
class RecorderThread(QThread):
    status_signal = Signal(str)
    finished_signal = Signal(list)

    def __init__(self):
        super().__init__()
        self.recording = False
        self.actions = []
        self.last_time = None
        self.mouse_listener = None
        self.keyboard_listener = None

    def run(self):
        self.recording = True
        self.actions = []
        self.last_time = time.time()
        self.status_signal.emit("录制中... 按 F9 停止")

        # 启动监听器
        self.mouse_listener = mouse.Listener(on_click=self.on_click, on_move=self.on_move)
        self.keyboard_listener = pynput_keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.mouse_listener.start()
        self.keyboard_listener.start()

        # 等待停止信号
        while self.recording:
            self.msleep(100)

        # 停止监听器
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

        self.finished_signal.emit(self.actions)

    def stop(self):
        self.recording = False

    def record_action(self, action_type, **kwargs):
        now = time.time()
        delay = round(now - self.last_time, 3)
        self.last_time = now
        action = {"type": action_type, "delay": delay}
        action.update(kwargs)
        self.actions.append(action)

    def on_click(self, x, y, button, pressed):
        if not self.recording:
            return
        if pressed:
            self.record_action(ACTION_CLICK, x=x, y=y, button=str(button))

    def on_move(self, x, y):
        if not self.recording:
            return
        # 移动事件太多，仅当移动距离较大时记录（可选简化）
        if self.actions and self.actions[-1].get("type") == ACTION_MOVE:
            # 合并连续的移动
            self.actions[-1]["x"] = x
            self.actions[-1]["y"] = y
        else:
            self.record_action(ACTION_MOVE, x=x, y=y)

    def on_key_press(self, key):
        if not self.recording:
            return
        try:
            k = key.char
        except AttributeError:
            k = str(key)
        self.record_action(ACTION_KEYDOWN, key=k)

    def on_key_release(self, key):
        if not self.recording:
            return
        try:
            k = key.char
        except AttributeError:
            k = str(key)
        self.record_action(ACTION_KEYUP, key=k)

# ---------- 回放线程 ----------
class ReplayThread(QThread):
    status_signal = Signal(str)
    finished_signal = Signal(bool)

    def __init__(self, actions, script_name):
        super().__init__()
        self.actions = actions
        self.script_name = script_name
        self.stop_flag = False

    def run(self):
        self.status_signal.emit(f"回放脚本: {self.script_name}")
        speed = config.get("replay_speed", 1.0)
        for action in self.actions:
            if self.stop_flag:
                break
            delay = action.get("delay", 0) / speed
            if delay > 0:
                time.sleep(delay)

            action_type = action["type"]
            try:
                if action_type == ACTION_CLICK:
                    x, y = action["x"], action["y"]
                    pyautogui.click(x, y)
                elif action_type == ACTION_MOVE:
                    x, y = action["x"], action["y"]
                    pyautogui.moveTo(x, y)
                elif action_type == ACTION_KEYDOWN:
                    key = action["key"]
                    pyautogui.keyDown(key)
                elif action_type == ACTION_KEYUP:
                    key = action["key"]
                    pyautogui.keyUp(key)
                elif action_type == ACTION_WAIT:
                    time.sleep(action.get("seconds", 0))
                elif action_type == ACTION_SCREENSHOT:
                    # 截图比对动作
                    x1, y1, x2, y2 = action["region"]
                    expected_img = action["expected_img"]
                    temp_img = os.path.join(SCREENSHOTS_DIR, f"temp_{int(time.time())}.png")
                    ok = img_utils.capture_screen(x1, y1, x2, y2, temp_img)
                    if not ok:
                        self.status_signal.emit("截图失败，比对跳过")
                        continue
                    sim = img_utils.compare_img_similarity(expected_img, temp_img)
                    threshold = config.get("similarity_threshold", 0.85)
                    if sim >= threshold:
                        self.status_signal.emit(f"截图比对通过 (相似度 {sim:.2f})")
                    else:
                        self.status_signal.emit(f"截图比对失败 (相似度 {sim:.2f} < {threshold})")
                        # 可选择停止回放
                        # self.stop_flag = True
                elif action_type == ACTION_OCR:
                    x1, y1, x2, y2 = action["region"]
                    target_input = action.get("input_target", None)  # 未来扩展
                    temp_img = os.path.join(SCREENSHOTS_DIR, f"ocr_{int(time.time())}.png")
                    ok = img_utils.capture_screen(x1, y1, x2, y2, temp_img)
                    if ok:
                        code = img_utils.recognize_code(temp_img)
                        self.status_signal.emit(f"OCR识别结果: {code}")
                        # 自动输入识别结果（可选）
                        if code and code != "OCR_ERROR":
                            pyautogui.write(code)
                    else:
                        self.status_signal.emit("OCR截图失败")
            except Exception as e:
                self.status_signal.emit(f"执行动作失败: {e}")
                self.stop_flag = True

        if self.stop_flag:
            self.status_signal.emit("回放已停止")
        else:
            self.status_signal.emit("回放完成")
        self.finished_signal.emit(not self.stop_flag)

    def stop(self):
        self.stop_flag = True

# ---------- 主窗口 ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapValid - 自动化录制回放工具")
        self.setGeometry(100, 100, 800, 600)

        # 控件
        self.script_list = QListWidget()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)

        self.record_btn = QPushButton("开始录制 (F6)")
        self.stop_record_btn = QPushButton("停止录制 (F9)")
        self.stop_record_btn.setEnabled(False)
        self.replay_btn = QPushButton("回放选中脚本")
        self.delete_btn = QPushButton("删除脚本")
        self.add_screenshot_action_btn = QPushButton("插入截图比对动作")
        self.add_ocr_action_btn = QPushButton("插入OCR识别动作")

        # 布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("脚本列表"))
        left_panel.addWidget(self.script_list)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.replay_btn)
        btn_layout.addWidget(self.delete_btn)
        left_panel.addLayout(btn_layout)
        left_panel.addWidget(self.add_screenshot_action_btn)
        left_panel.addWidget(self.add_ocr_action_btn)

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("日志输出"))
        right_panel.addWidget(self.log_text)
        record_layout = QHBoxLayout()
        record_layout.addWidget(self.record_btn)
        record_layout.addWidget(self.stop_record_btn)
        right_panel.addLayout(record_layout)

        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)

        # 信号连接
        self.record_btn.clicked.connect(self.start_recording)
        self.stop_record_btn.clicked.connect(self.stop_recording)
        self.replay_btn.clicked.connect(self.start_replay)
        self.delete_btn.clicked.connect(self.delete_script)
        self.add_screenshot_action_btn.clicked.connect(self.insert_screenshot_action)
        self.add_ocr_action_btn.clicked.connect(self.insert_ocr_action)

        # 全局热键
        keyboard.add_hotkey('f6', self.start_recording)
        keyboard.add_hotkey('f9', self.stop_recording)

        # 线程
        self.recorder = None
        self.replayer = None

        # 当前编辑的脚本（用于插入动作）
        self.current_script_path = None
        self.current_actions = []

        self.refresh_script_list()

    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {msg}")

    def refresh_script_list(self):
        self.script_list.clear()
        if not os.path.exists(SCRIPTS_DIR):
            return
        for f in os.listdir(SCRIPTS_DIR):
            if f.endswith(".json"):
                self.script_list.addItem(f)

    def start_recording(self):
        if self.recorder and self.recorder.isRunning():
            self.log("录制已在运行中")
            return
        # 询问脚本名称
        name, ok = QInputDialog.getText(self, "新建脚本", "请输入脚本名称（不含扩展名）:")
        if not ok or not name.strip():
            return
        self.current_script_path = os.path.join(SCRIPTS_DIR, name.strip() + ".json")
        self.recorder = RecorderThread()
        self.recorder.status_signal.connect(self.log)
        self.recorder.finished_signal.connect(self.on_recording_finished)
        self.recorder.start()
        self.record_btn.setEnabled(False)
        self.stop_record_btn.setEnabled(True)
        self.log(f"开始录制脚本: {name}")

    def stop_recording(self):
        if self.recorder and self.recorder.isRunning():
            self.recorder.stop()
            self.log("正在停止录制...")
        else:
            self.log("没有正在进行的录制")

    def on_recording_finished(self, actions):
        self.record_btn.setEnabled(True)
        self.stop_record_btn.setEnabled(False)
        if not actions:
            self.log("录制动作列表为空，未保存脚本")
            return
        # 保存为 JSON
        script_data = {
            "name": os.path.basename(self.current_script_path),
            "created": datetime.now().isoformat(),
            "actions": actions
        }
        with open(self.current_script_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
        self.log(f"脚本已保存: {self.current_script_path}，共 {len(actions)} 个动作")
        self.refresh_script_list()

    def start_replay(self):
        if self.replayer and self.replayer.isRunning():
            self.log("回放已在运行中")
            return
        selected = self.script_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择一个脚本")
            return
        script_name = selected.text()
        script_path = os.path.join(SCRIPTS_DIR, script_name)
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            actions = script_data.get("actions", [])
            if not actions:
                self.log("脚本中没有动作")
                return
            self.replayer = ReplayThread(actions, script_name)
            self.replayer.status_signal.connect(self.log)
            self.replayer.finished_signal.connect(self.on_replay_finished)
            self.replayer.start()
            self.replay_btn.setEnabled(False)
            self.log(f"开始回放: {script_name}")
        except Exception as e:
            self.log(f"加载脚本失败: {e}")

    def on_replay_finished(self, success):
        self.replay_btn.setEnabled(True)
        self.log("回放线程结束" + (" (成功)" if success else " (失败)"))

    def delete_script(self):
        selected = self.script_list.currentItem()
        if not selected:
            return
        script_name = selected.text()
        reply = QMessageBox.question(self, "确认删除", f"确定删除脚本 {script_name} 吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            path = os.path.join(SCRIPTS_DIR, script_name)
            os.remove(path)
            self.log(f"已删除脚本: {script_name}")
            self.refresh_script_list()

    def insert_screenshot_action(self):
        """交互式插入截图比对动作到当前脚本（需先选中脚本）"""
        selected = self.script_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选中一个脚本，再插入动作")
            return
        script_path = os.path.join(SCRIPTS_DIR, selected.text())
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
        except:
            self.log("读取脚本失败")
            return

        # 打开区域选择器
        selector = Selector()
        if selector.exec() != Selector.DialogCode.Accepted:
            return
        x1, y1, x2, y2 = selector.get_selected_region()
        # 截图保存为预期图片
        expected_img = os.path.join(SCREENSHOTS_DIR, f"expected_{int(time.time())}.png")
        ok = img_utils.capture_screen(x1, y1, x2, y2, expected_img)
        if not ok:
            self.log("截图失败，无法插入比对动作")
            return

        # 插入动作到 actions 列表末尾（可调整位置）
        new_action = {
            "type": ACTION_SCREENSHOT,
            "delay": 0.5,
            "region": [x1, y1, x2, y2],
            "expected_img": expected_img
        }
        script_data["actions"].append(new_action)
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
        self.log(f"已插入截图比对动作，预期图片保存为: {expected_img}")

    def insert_ocr_action(self):
        selected = self.script_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选中一个脚本，再插入动作")
            return
        script_path = os.path.join(SCRIPTS_DIR, selected.text())
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
        except:
            self.log("读取脚本失败")
            return

        selector = Selector()
        if selector.exec() != Selector.DialogCode.Accepted:
            return
        x1, y1, x2, y2 = selector.get_selected_region()
        new_action = {
            "type": ACTION_OCR,
            "delay": 0.5,
            "region": [x1, y1, x2, y2]
        }
        script_data["actions"].append(new_action)
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
        self.log(f"已插入OCR识别动作，区域: ({x1},{y1})-({x2},{y2})")

# ---------- 程序入口 ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())