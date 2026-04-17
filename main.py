import sys
import os
import tkinter as tk
from tkinter import ttk
import threading
from pathlib import Path

# 添加项目根目录到Python路径（解决模块导入问题）
sys.path.append(str(Path(__file__).parent))

# 导入优化后的工具模块和核心引擎
from utils import load_config, init_logger, get_logger, ensure_dir
from utils.path import get_output_path
from core.engine import SnapValidEngine

class SnapValidGUI:
    def __init__(self, root):
        # 初始化基础配置
        self.config = load_config("config.yml")
        self.logger = get_logger()
        
        # 主窗口配置
        self.root = root
        self.root.title(f"{self.config['app']['name']} - 自动化工具")
        self.root.geometry("520x400")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)  # 窗口始终置顶

        # 初始化自动化引擎
        self.engine = SnapValidEngine(self.config)

        # 构建UI界面
        self._build_ui()

        # 启动引擎后台线程
        threading.Thread(target=self.engine.start, daemon=True).start()
        self.logger.info("✅ SnapValid GUI 初始化完成，引擎已启动")

    def _build_ui(self):
        """构建GUI界面（模块化拆分，提升可读性）"""
        # 标题区域
        title_label = tk.Label(
            self.root, 
            text=f"{self.config['app']['name']} 自动化操作工具", 
            font=("微软雅黑", 16)
        )
        title_label.pack(pady=10)

        # 状态提示区域
        self.status_label = tk.Label(
            self.root, 
            text="✅ 工具已启动", 
            fg="green", 
            font=("微软雅黑", 12)
        )
        self.status_label.pack(pady=5)

        # 功能按钮区域
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        # 第一行按钮（录制/回放/停止）
        ttk.Button(
            btn_frame, 
            text=f"{self.config['hotkeys']['record_start']} 开始录制", 
            command=self.start_record, 
            width=15
        ).grid(row=0, column=0, padx=10, pady=8)
        
        ttk.Button(
            btn_frame, 
            text=f"{self.config['hotkeys']['play_start']} 开始回放", 
            command=self.start_play, 
            width=15
        ).grid(row=0, column=1, padx=10, pady=8)
        
        ttk.Button(
            btn_frame, 
            text=f"{self.config['hotkeys']['stop']} 停止", 
            command=self.stop, 
            width=15
        ).grid(row=0, column=2, padx=10, pady=8)

        # 第二行按钮（OCR/截图对比/退出）
        ttk.Button(
            btn_frame, 
            text=f"{self.config['hotkeys']['insert_ocr']} OCR 识别", 
            command=self.ocr, 
            width=15
        ).grid(row=1, column=0, padx=10, pady=8)
        
        ttk.Button(
            btn_frame, 
            text=f"{self.config['hotkeys']['insert_compare']} 截图对比", 
            command=self.snapshot, 
            width=15
        ).grid(row=1, column=1, padx=10, pady=8)
        
        ttk.Button(
            btn_frame, 
            text="退出程序", 
            command=self.quit_app, 
            width=15
        ).grid(row=1, column=2, padx=10, pady=8)

        # 快捷键提示区域
        hotkey_tips = (
            f"{self.config['hotkeys']['record_start']}=录制 | "
            f"{self.config['hotkeys']['play_start']}=回放 | "
            f"{self.config['hotkeys']['stop']}=停止 | "
            f"{self.config['hotkeys']['insert_ocr']}=OCR | "
            f"{self.config['hotkeys']['insert_compare']}=截图对比"
        )
        tips_label = tk.Label(self.root, text=hotkey_tips)
        tips_label.pack()

    def start_record(self):
        """开始录制操作"""
        try:
            self.engine.recorder.start_record()
            self.status_label.config(text="⏺ 正在录制...", fg="red")
            self.logger.info("开始录制操作")
        except Exception as e:
            self.status_label.config(text=f"❌ 录制启动失败: {str(e)}", fg="red")
            self.logger.error(f"录制启动失败: {e}", exc_info=True)

    def start_play(self):
        """开始回放操作"""
        try:
            self.engine.recorder.start_play()
            self.status_label.config(text="▶ 正在回放...", fg="blue")
            self.logger.info("开始回放操作")
        except Exception as e:
            self.status_label.config(text=f"❌ 回放启动失败: {str(e)}", fg="red")
            self.logger.error(f"回放启动失败: {e}", exc_info=True)

    def stop(self):
        """停止录制/回放"""
        try:
            self.engine.recorder.stop()
            self.status_label.config(text="⏹ 已停止", fg="green")
            self.logger.info("停止录制/回放操作")
        except Exception as e:
            self.status_label.config(text=f"❌ 停止操作失败: {str(e)}", fg="red")
            self.logger.error(f"停止操作失败: {e}", exc_info=True)

    def ocr(self):
        """执行OCR识别操作"""
        try:
            self.engine.recorder.do_ocr()
            self.status_label.config(text="🔍 执行OCR识别...", fg="purple")
            self.logger.info("执行OCR识别操作")
        except Exception as e:
            self.status_label.config(text=f"❌ OCR识别失败: {str(e)}", fg="red")
            self.logger.error(f"OCR识别失败: {e}", exc_info=True)

    def snapshot(self):
        """执行截图对比操作"""
        try:
            self.engine.recorder.do_compare()
            self.status_label.config(text="🖼️ 执行截图对比...", fg="orange")
            self.logger.info("执行截图对比操作")
        except Exception as e:
            self.status_label.config(text=f"❌ 截图对比失败: {str(e)}", fg="red")
            self.logger.error(f"截图对比失败: {e}", exc_info=True)

    def quit_app(self):
        """安全退出程序"""
        try:
            self.engine.stop()  # 停止引擎
            self.logger.info("📤 程序正常退出")
        except Exception as e:
            self.logger.error(f"退出时异常: {e}", exc_info=True)
        finally:
            self.root.quit()

def init_app():
    """应用初始化（配置、日志、目录）"""
    # 1. 加载配置文件
    config = load_config("config.yml")
    
    # 2. 初始化日志系统
    init_logger(
        log_level=config["app"]["log_level"],
        log_file=os.path.join("logs", "run.log")
    )
    logger = get_logger()
    
    # 3. 创建必要的输出目录
    ensure_dir(get_output_path("scripts"))
    ensure_dir(get_output_path("screenshots/ocr"))
    ensure_dir(get_output_path("screenshots/play"))
    ensure_dir(get_output_path("screenshots/record"))
    
    logger.info(f"🚀 {config['app']['name']} 基础初始化完成")
    return config, logger

if __name__ == "__main__":
    # 全局应用初始化
    try:
        init_app()
    except Exception as e:
        print(f"应用初始化失败: {e}")
        sys.exit(1)
    
    # 启动GUI主程序
    root = tk.Tk()
    app = SnapValidGUI(root)
    root.mainloop()