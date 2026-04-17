import time
import pyautogui
import keyboard
import threading
import win32api
from utils.logger import info, error
from utils.path import SCREENSHOT_DIR
from core.selector import select_region
from core.ocr import OCR
from core.compare import image_similarity

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

class Recorder:
    def __init__(self):
        self.actions = []
        self.recording = False
        self.playing = False
        self.stop_event = threading.Event()
        self.ocr = OCR()
        self.last_time = time.time()
        self.full_input = ""

        self.click_times = []
        self.DOUBLE_CLICK_MAX = 0.5

    def stop(self):
        self.recording = False
        self.playing = False
        self.stop_event.set()
        info("✅ 已全局强制停止")
        time.sleep(0.3)

    def start_record(self):
        if self.recording:
            return
        self.stop_event.clear()
        self.actions.clear()
        self.full_input = ""
        self.recording = True
        self.click_times = []
        self.last_time = time.time()
        info("【录制】开始（支持单击/双击）")
        threading.Thread(target=self._record_loop, daemon=True).start()

    def flush_input(self):
        if self.full_input.strip():
            info(f"【录制】输入: [{self.full_input}]")
        self.full_input = ""

    def _record_loop(self):
        last_pos = None
        left_pressed = False

        while not self.stop_event.is_set() and self.recording:
            time.sleep(0.02)
            x, y = pyautogui.position()
            now = time.time()

            state = win32api.GetKeyState(0x01)
            if state < 0:
                if not left_pressed:
                    left_pressed = True
                    self.click_times.append(now)
                    if len(self.click_times) >= 2:
                        t1 = self.click_times[-2]
                        t2 = self.click_times[-1]
                        if t2 - t1 < self.DOUBLE_CLICK_MAX:
                            self.flush_input()
                            dt = max(round(now - self.last_time, 3), 0.1)
                            self.last_time = now
                            self.actions.append(("double_click", x, y, dt))
                            info(f"【录制】双击: ({x},{y})")
                            self.click_times.clear()
            else:
                left_pressed = False

            if len(self.click_times) == 1 and now - self.click_times[0] > self.DOUBLE_CLICK_MAX:
                self.flush_input()
                dt = max(round(now - self.last_time, 3), 0.1)
                self.last_time = now
                self.actions.append(("click", x, y, dt))
                info(f"【录制】单击: ({x},{y})")
                self.click_times.clear()

            if last_pos != (x, y) and now - self.last_time >= 0.1:
                dt = max(round(now - self.last_time, 3), 0.1)
                self.actions.append(("move", x, y, dt))
                self.last_time = now
                last_pos = (x, y)

            keys = keyboard.read_events()
            for e in keys:
                if e.event_type == "down":
                    k = e.name
                    if k in ["shift", "ctrl", "alt", "esc", "tab"] or k.startswith("f"):
                        continue
                    if k == "enter":
                        self.flush_input()
                        dt = max(round(time.time() - self.last_time, 3), 0.1)
                        self.last_time = time.time()
                        self.actions.append(("key", "enter", dt))
                        info("【录制】按键: [回车]")
                    elif k == "backspace":
                        self.full_input = self.full_input[:-1]
                    elif k == "space":
                        self.full_input += " "
                    elif len(k) == 1:
                        self.full_input += k

        self.flush_input()
        self.recording = False
        info("【录制】已停止")

    def start_play(self):
        if self.playing:
            return
        self.stop_event.clear()
        self.playing = True
        threading.Thread(target=self._play_loop, daemon=True).start()

    def _play_loop(self):
        if not self.actions:
            info("【回放】无记录")
            self.playing = False
            return

        info("【回放】开始（F8随时停止）")
        for act in self.actions:
            if self.stop_event.is_set() or not self.playing:
                info("【回放】已强制停止！")
                self.playing = False
                return

            typ = act[0]
            dt = act[-1]
            time.sleep(dt)

            try:
                if typ == "move":
                    pyautogui.moveTo(act[1], act[2], duration=0.05)
                elif typ == "click":
                    x, y = act[1], act[2]
                    pyautogui.moveTo(x, y, duration=0.1)
                    pyautogui.click()
                    info(f"【回放】单击 ({x},{y})")
                elif typ == "double_click":
                    x, y = act[1], act[2]
                    pyautogui.moveTo(x, y, duration=0.15)
                    time.sleep(0.1)
                    pyautogui.doubleClick(interval=0.1)
                    info(f"【回放】双击 ({x},{y}) → 打开浏览器")
                elif typ == "key":
                    pyautogui.press(act[1])
                    info(f"【回放】按键 [{act[1]}]")
            except Exception:
                continue

        info("【回放】执行完成 ✅")
        self.playing = False

    # ==========================
    # 🔥 OCR 和 截图对比 修复
    # ==========================
    def do_ocr(self):
        try:
            info("【OCR】请框选验证码区域")
            time.sleep(0.2)
            x1, y1, x2, y2 = select_region()
            w, h = x2-x1, y2-y1
            if w <= 0 or h <= 0:
                error("【OCR】无效区域")
                return
            p = f"{SCREENSHOT_DIR}/ocr.png"
            pyautogui.screenshot(p, region=(x1,y1,w,h))
            res = self.ocr.recognize(p)
            info(f"【OCR】识别结果: {res}")
            pyautogui.typewrite(str(res).strip())
            info("【OCR】已自动输入")
        except Exception as e:
            error(f"【OCR】失败: {str(e)}")

    def do_compare(self):
        try:
            info("【截图】请框选校验区域")
            time.sleep(0.2)
            x1, y1, x2, y2 = select_region()
            w, h = x2-x1, y2-y1
            if w <= 0 or h <= 0:
                error("【截图】无效区域")
                return
            base = f"{SCREENSHOT_DIR}/base.png"
            curr = f"{SCREENSHOT_DIR}/curr.png"
            import os
            if self.recording:
                pyautogui.screenshot(base, region=(x1,y1,w,h))
                info("【截图】基准图已保存")
                return
            if os.path.exists(base):
                pyautogui.screenshot(curr, region=(x1,y1,w,h))
                sim = image_similarity(base, curr)
                info(f"【截图】相似度: {max(sim,0):.2%}")
            else:
                pyautogui.screenshot(base, region=(x1,y1,w,h))
                info("【截图】基准图已保存")
        except Exception as e:
            error(f"【截图】失败: {str(e)}")