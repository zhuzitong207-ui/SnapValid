import tkinter as tk
from tkinter import ttk
import threading
from core.engine import SnapValidEngine

class SnapValidGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SnapValid - 自动化工具")
        self.root.geometry("520x400")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)  # 始终置顶

        self.engine = SnapValidEngine()

        tk.Label(root, text="SnapValid 自动化操作工具", font=("微软雅黑", 16)).pack(pady=10)
        self.status_label = tk.Label(root, text="✅ 工具已启动", fg="green", font=("微软雅黑", 12))
        self.status_label.pack(pady=5)

        frame = tk.Frame(root)
        frame.pack(pady=10)

        ttk.Button(frame, text="F6 开始录制", command=self.start_record, width=15).grid(row=0, column=0, padx=10, pady=8)
        ttk.Button(frame, text="F7 开始回放", command=self.start_play, width=15).grid(row=0, column=1, padx=10, pady=8)
        ttk.Button(frame, text="F8 停止", command=self.stop, width=15).grid(row=0, column=2, padx=10, pady=8)

        ttk.Button(frame, text="OCR 识别", command=self.ocr, width=15).grid(row=1, column=0, padx=10, pady=8)
        ttk.Button(frame, text="截图对比", command=self.snapshot, width=15).grid(row=1, column=1, padx=10, pady=8)
        ttk.Button(frame, text="退出程序", command=root.quit, width=15).grid(row=1, column=2, padx=10, pady=8)

        tk.Label(root, text="F6=录制 | F7=回放 | F8=8停止 | Ctrl+Alt+I=OCR | Ctrl+Alt+S=截图对比").pack()

        threading.Thread(target=self.engine.start, daemon=True).start()

    def start_record(self):
        self.engine.recorder.start_record()
        self.status_label.config(text="⏺ 正在录制...", fg="red")

    def start_play(self):
        self.engine.recorder.start_play()
        self.status_label.config(text="▶ 正在回放...", fg="blue")

    def stop(self):
        self.engine.recorder.stop()
        self.status_label.config(text="⏹ 已停止", fg="green")

    def ocr(self):
        self.engine.recorder.do_ocr()

    def snapshot(self):
        self.engine.recorder.do_compare()

if __name__ == "__main__":
    root = tk.Tk()
    SnapValidGUI(root)
    root.mainloop()