import time
import keyboard
from utils.logger import info
from utils.config import get_config
from core.recorder import Recorder

class SnapValidEngine:
    def __init__(self):
        self.recorder = Recorder()
        self.config = get_config()
        self.running = True

    def start(self):
        self._bind_hotkeys()
        info("快捷键监听已启动")
        print("\n✅ SnapValid 已启动（完整版）")
        print("F6=录制  | F7=回放 | F8=强制停止")
        print("Ctrl+Alt+I=OCR | Ctrl+Alt+S=截图对比")
        while self.running:
            time.sleep(1)

    def _bind_hotkeys(self):
        hk = self.config["hotkey"]
        keyboard.add_hotkey(hk["record"], self.recorder.start_record)
        keyboard.add_hotkey(hk["play"], self.recorder.start_play)
        
        # 🔥 F8 强制停止（全局绑定，永远生效）
        keyboard.add_hotkey(hk["stop"], self.recorder.stop)
        
        keyboard.add_hotkey(hk["ocr"], self.recorder.do_ocr)
        keyboard.add_hotkey(hk["snapshot"], self.recorder.do_compare)