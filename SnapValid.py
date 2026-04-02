import os
import sys
import time
import json
import threading
from datetime import datetime

# ====================== DPI崩溃解决 ======================
os.environ["QT_QPA_PLATFORM"] = "windows"
os.environ["QT_FONT_DPI"] = "96"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"

try:
    from screeninfo import get_monitors
except:
    def get_monitors():
        from dataclasses import dataclass
        @dataclass
        class Monitor: x: int; y: int; width: int; height: int; is_primary: bool
        return [Monitor(0,0,1920,1080,True)]

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import pyautogui
import keyboard
from pynput import mouse, keyboard as pk_keyboard
from pynput.keyboard import Key, KeyCode
import pygetwindow as gw

from img_utils import capture_screen, compare_img_similarity, recognize_code
from selector import get_area

# ====================== 配置初始化 ======================
if not os.path.exists("config.json"):
    default_cfg = {
        "软件名称": "SnapValid", "版本号": "v2.6.0",
        "相似度阈值(0-1)": 0.9, "回放循环次数": 1,
        "录制时截图保存路径": "./screenshots/record/",
        "回放对比截图保存路径": "./screenshots/play/",
        "验证码原始图片保存路径": "./screenshots/ocr/",
        "验证码识别结果保存文件": "./ocr_result.txt",
        "录制脚本存储路径": "./scripts/",
        "操作日志文件": "./operation_log.txt"
    }
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(default_cfg, f, indent=2, ensure_ascii=False)

with open("config.json", "r", encoding="utf-8") as f:
    CFG = json.load(f)

THRESHOLD = CFG["相似度阈值(0-1)"]
PLAY_COUNT = CFG["回放循环次数"]
DIR_REC  = CFG["录制时截图保存路径"]
DIR_PLAY = CFG["回放对比截图保存路径"]
DIR_OCR  = CFG["验证码原始图片保存路径"]
TXT_OCR  = CFG["验证码识别结果保存文件"]
DIR_SCRIPT = CFG["录制脚本存储路径"]
LOG_FILE = CFG["操作日志文件"]

for d in [DIR_REC, DIR_PLAY, DIR_OCR, DIR_SCRIPT]:
    os.makedirs(d, exist_ok=True)

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.08

# ====================== 多屏支持 ======================
def check_display_mode():
    monitors = get_monitors()
    return True, f"✅ 多屏扩展模式（{len(monitors)}屏）"

# ====================== 主窗口 ======================
class SnapValid(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        self.resize(500, 400)
        self.setWindowTitle(f"SnapValid {CFG['版本号']} | 完美稳定版")

        self.is_recording = False
        self.is_playing  = False
        self.script = []
        self.rec_start = 0
        self.stop_event = threading.Event()
        self.m_listen = None
        self.k_listen = None
        self.input_buf = ""
        self.rec_area_idx = 1
        
        # 验证码录制相关
        self.ocr_recording = False
        self.ocr_area = None
        self.ocr_input_pos = None
        self.ocr_input_text = ""
        self.ocr_script_index = -1

        self.init_ui()
        self.bind_hotkeys()
        self.log("✅ 程序启动成功（完美稳定版）")
        self.log("📌 修复：重复输入自动清空 | 输入法乱码 | 验证码完美替换")

    def log(self, msg):
        try:
            t = datetime.now().strftime("%H:%M:%S")
            line = f"[{t}] {msg}"
            self.log_box.append(line)
            self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except: pass

    def init_ui(self):
        c = QWidget()
        self.setCentralWidget(c)
        lay = QVBoxLayout(c)
        lay.setContentsMargins(8,8,8,8)
        lay.setSpacing(6)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("✅ 就绪 | 重复输入/乱码/验证码 全修复")
        self.status_bar.addWidget(self.status_label)

        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(5)
        self.btn_rec  = QPushButton("F9 录制")
        self.btn_play = QPushButton("F5 回放")
        self.btn_stop = QPushButton("F8 停止")
        self.btn_load = QPushButton("加载脚本")
        for btn in [self.btn_rec,self.btn_play,self.btn_stop,self.btn_load]:
            btn.setMinimumHeight(30)
        self.btn_rec.clicked.connect(self.start_rec)
        self.btn_play.clicked.connect(self.start_play)
        self.btn_stop.clicked.connect(self.stop_all)
        self.btn_load.clicked.connect(self.load_script_dialog)
        btn_lay.addWidget(self.btn_rec)
        btn_lay.addWidget(self.btn_play)
        btn_lay.addWidget(self.btn_stop)
        btn_lay.addWidget(self.btn_load)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("Consolas",9))
        lay.addLayout(btn_lay)
        lay.addWidget(self.log_box)

    # ====================== 热键 ======================
    def bind_hotkeys(self):
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey("F9", self.start_rec)
            keyboard.add_hotkey("F5", self.start_play)
            keyboard.add_hotkey("F8", self.stop_all)
            keyboard.add_hotkey("ctrl+alt+s", self.insert_compare)
            keyboard.add_hotkey("ctrl+alt+d", self.start_ocr_recording)
        except Exception as e:
            self.log(f"❌ 热键绑定失败：{e}")

    # ====================== 录制核心 ======================
    def start_rec(self):
        ok, tip = check_display_mode()
        self.log(tip)
        if self.is_recording or self.is_playing:
            self.log("❌ 正在录制/回放")
            return

        self.is_recording = True
        self.script = []
        self.rec_start = time.time()
        self.input_buf = ""
        self.rec_area_idx = 1
        self.ocr_recording = False
        self.ocr_area = None
        self.ocr_input_pos = None
        self.ocr_input_text = ""
        
        self.log("📹 开始录制")
        self.status_label.setText("🔴 录制中")

        try:
            self.m_listen = mouse.Listener(on_click=self.on_click, daemon=True)
            self.k_listen = pk_keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release, daemon=True)
            self.m_listen.start()
            self.k_listen.start()
            self.log("✅ 键鼠监听已启动")
        except Exception as e:
            self.log(f"❌ 监听启动失败：{e}")
            self.is_recording = False

    def on_click(self, x, y, btn, pressed):
        if not self.is_recording or not pressed or btn != mouse.Button.left:
            return
        
        if self.ocr_recording and self.ocr_area is not None and self.ocr_input_pos is None:
            self.ocr_input_pos = (x, y)
            self.log(f"📍 已记录验证码输入框：({x},{y})")
            self.log("⌨️ 输入验证码，按↓结束")
            return
        
        self.flush_input()
        self.log(f"🖱️ 记录点击：({x},{y})")
        self.script.append({
            "t": round(time.time()-self.rec_start,2),
            "act":"click", "x":x,"y":y,"btn":"left"
        })

    def on_key_press(self, key):
        if not self.is_recording:
            return
        
        if self.ocr_recording:
            if key == Key.down:
                self.finish_ocr_recording()
                return
            try:
                if key.char is not None:
                    self.ocr_input_text += key.char
                    self.log(f"📝 验证码：{self.ocr_input_text}")
                return
            except AttributeError:
                pass
            if key == Key.backspace and len(self.ocr_input_text) > 0:
                self.ocr_input_text = self.ocr_input_text[:-1]
                self.log(f"📝 验证码：{self.ocr_input_text}")
            return

        try:
            if key.char:
                self.input_buf += key.char
        except:
            pass

    def on_key_release(self, key):
        if not self.is_recording or self.ocr_recording:
            return
        if key in (Key.enter, Key.space, Key.tab):
            self.flush_input()
            k_map = {Key.enter:"enter", Key.space:"space", Key.tab:"tab"}
            self.log(f"⌨️ 记录按键：{k_map[key]}")
            self.script.append({
                "t": round(time.time()-self.rec_start,2),
                "act":"key", "key":k_map[key]
            })

    def flush_input(self):
        if self.input_buf.strip() and not self.ocr_recording:
            self.log(f"⌨️ 记录输入：【{self.input_buf}】")
            self.script.append({
                "t": round(time.time()-self.rec_start,2),
                "act":"input", "text":self.input_buf
            })
            self.input_buf = ""

    # ====================== 验证码录制 ======================
    def start_ocr_recording(self):
        if not self.is_recording:
            self.log("❌ 请先开始录制")
            return
        self.ocr_recording = True
        self.log("🔍 框选验证码图片，空格确认")
        area = get_area()
        if not area:
            self.ocr_recording = False
            self.log("❌ 已取消")
            return
        self.ocr_area = area
        self.log(f"✅ 验证码区域已保存")
        self.log("📍 点击验证码输入框")

    def finish_ocr_recording(self):
        if not self.ocr_recording or not self.ocr_area or not self.ocr_input_pos or not self.ocr_input_text:
            self.log("❌ 信息不完整，取消")
            self.ocr_recording = False
            return
        self.script.append({
            "t": round(time.time()-self.rec_start,2),
            "act": "ocr_replace",
            "ocr_area": self.ocr_area,
            "input_pos": self.ocr_input_pos,
            "recorded_text": self.ocr_input_text
        })
        self.log(f"✅ 验证码录制完成：【{self.ocr_input_text}】")
        self.ocr_recording = False
        self.ocr_area = None
        self.ocr_input_pos = None
        self.ocr_input_text = ""

    # ====================== 对比区域 ======================
    def insert_compare(self):
        if not self.is_recording or self.ocr_recording:
            self.log("❌ 无法操作")
            return
        self.flush_input()
        self.log("📷 框选对比区域，空格确认")
        area = get_area()
        if not area:
            self.log("❌ 已取消")
            return
        x1,y1,x2,y2 = area
        fp = os.path.join(DIR_REC, f"cmp_{self.rec_area_idx}.png")
        capture_screen(x1,y1,x2,y2,fp)
        self.script.append({
            "t": round(time.time()-self.rec_start,2),
            "act":"compare", "x1":x1,"y1":y1,"x2":x2,"y2":y2,
            "src":fp, "no":self.rec_area_idx
        })
        self.log(f"✅ 插入对比区域 {self.rec_area_idx}")
        self.rec_area_idx +=1

    # ====================== 【核心修复】回放：输入前清空+切英文 ======================
    def safe_type(self, text):
        """安全输入：切换英文 + 全选清空 + 一次性输入（杜绝乱码+重复）"""
        # 1. 切换到英文输入法（Win+空格）
        pyautogui.hotkey('win', 'space')
        time.sleep(0.1)
        # 2. 全选清空原有内容（解决浏览器自动填充重复）
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        # 3. 一次性完整输入（不分段）
        pyautogui.typewrite(text, interval=0.02)

    def start_play(self):
        ok, tip = check_display_mode()
        self.log(tip)
        if not ok or self.is_playing or not self.script:
            self.log("❌ 无脚本或正在回放")
            return
        self.is_playing = True
        self.stop_event.clear()
        self.ocr_script_index = -1
        self.log("▶️ 开始回放（安全输入+验证码替换）")
        self.status_label.setText("🟢 回放中")
        threading.Thread(target=self.play_thread, daemon=True).start()

    def play_thread(self):
        try:
            for cnt in range(1, PLAY_COUNT+1):
                if self.stop_event.is_set(): break
                self.log(f"==== 第 {cnt} 次回放 ====")
                last_t = 0
                time.sleep(0.5)
                for idx, act in enumerate(self.script):
                    if self.stop_event.is_set(): break
                    wait_time = max(0.0, act["t"] - last_t)
                    time.sleep(wait_time)
                    last_t = act["t"]

                    try:
                        if act["act"] == "click":
                            pyautogui.moveTo(act["x"], act["y"], 0.1)
                            pyautogui.click()
                            self.log(f"🖱️ 回放点击 ({act['x']},{act['y']})")

                        elif act["act"] == "input":
                            if self.ocr_script_index == idx:
                                self.log(f"🔄 跳过录制验证码：【{act['text']}】")
                                continue
                            # 🔥 修复：安全输入（清空+英文+一次性输入）
                            self.safe_type(act["text"])
                            self.log(f"⌨️ 安全输入：【{act['text']}】")

                        elif act["act"] == "key":
                            pyautogui.press(act["key"])
                            self.log(f"⌨️ 回放按键 {act['key']}")

                        elif act["act"] == "compare":
                            time.sleep(0.7)
                            n = act["no"]
                            nowp = os.path.join(DIR_PLAY, f"play_{n}_{cnt}.png")
                            capture_screen(act["x1"], act["y1"], act["x2"], act["y2"], nowp)
                            sim = compare_img_similarity(act["src"], nowp)
                            res = "OK" if sim >= THRESHOLD else "FAIL"
                            self.log(f"📷 对比{n}：{res} {sim:.2f}")

                        elif act["act"] == "ocr_replace":
                            self.log("🔍 识别验证码...")
                            ox1, oy1, ox2, oy2 = act["ocr_area"]
                            ocr_path = os.path.join(DIR_OCR, f"ocr_{int(time.time())}.png")
                            capture_screen(ox1, oy1, ox2, oy2, ocr_path)
                            code = recognize_code(ocr_path) or ""
                            self.log(f"✅ 识别结果：【{code}】")
                            # 安全填入验证码
                            ix, iy = act["input_pos"]
                            pyautogui.moveTo(ix, iy, 0.2)
                            pyautogui.click()
                            time.sleep(0.2)
                            self.safe_type(code)
                            self.log(f"✅ 已填入：【{code}】")
                            # 标记跳过旧验证码
                            for i in range(idx+1, len(self.script)):
                                if self.script[i]["act"] == "input" and self.script[i]["text"] == act["recorded_text"]:
                                    self.ocr_script_index = i
                                    break

                    except Exception as e:
                        self.log(f"⚠️  执行异常：{e}")
            self.log("✅ 回放完成 ✅")
        except Exception as e:
            self.log(f"❌ 回放异常：{e}")
        self.is_playing = False
        self.status_label.setText("✅ 就绪")

    # ====================== 停止 ======================
    def stop_all(self):
        if self.ocr_recording:
            self.finish_ocr_recording()
        if self.is_recording:
            self.flush_input()
            if len(self.script) > 0:
                name = f"script_{int(time.time())}_{len(self.script)}ops.json"
                with open(os.path.join(DIR_SCRIPT, name), "w", encoding="utf-8") as f:
                    json.dump(self.script, f, indent=2)
                self.log(f"💾 脚本已保存：{name}")
        self.is_recording = False
        self.is_playing = False
        self.stop_event.set()
        try:
            if self.m_listen: self.m_listen.stop()
            if self.k_listen: self.k_listen.stop()
        except: pass
        self.log("⏹️ 已停止")

    def load_script_dialog(self):
        p, _ = QFileDialog.getOpenFileName(self, "加载脚本", DIR_SCRIPT, "JSON (*.json)")
        if p and os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                self.script = json.load(f)
            ocr_cnt = sum(1 for a in self.script if a["act"] == "ocr_replace")
            self.log(f"📂 已加载：{os.path.basename(p)}")
            self.log(f"📌 包含 {ocr_cnt} 个验证码替换")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SnapValid()
    win.show()
    sys.exit(app.exec())
