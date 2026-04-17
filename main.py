import sys
import threading
import win32api
import win32con
import win32gui
from pathlib import Path
from utils.log_utils import logger
from utils.config_utils import get_config
from core.recorder import Recorder
from core.player import Player

# 全局实例
recorder = Recorder()
player = Player()
last_script_path = ""

def register_hotkeys():
    """注册全局快捷键"""
    config = get_config()
    
    # 注册快捷键的回调函数
    def hotkey_start_recording():
        recorder.start()
    
    def hotkey_stop():
        global last_script_path
        if recorder.is_recording:
            last_script_path = recorder.stop()
        if player.is_playing:
            player.stop()
    
    def hotkey_play():
        if last_script_path:
            threading.Thread(target=player.play, args=(last_script_path,), daemon=True).start()
        else:
            logger.warning("无可用脚本，先录制脚本")
    
    def hotkey_insert_ocr():
        if recorder.is_recording:
            # 示例：获取鼠标选中区域（实际需实现区域选择逻辑）
            x1, y1 = win32api.GetCursorPos()
            x2, y2 = x1 + 200, y1 + 100  # 临时默认区域，需替换为用户选择
            recorder.insert_ocr_step(x1, y1, x2, y2)
    
    def hotkey_insert_screenshot_check():
        if recorder.is_recording:
            x1, y1 = win32api.GetCursorPos()
            x2, y2 = x1 + 200, y1 + 100  # 临时默认区域，需替换为用户选择
            recorder.insert_screenshot_check_step(x1, y1, x2, y2)
    
    # 注册快捷键（简化示例，实际需用RegisterHotKey）
    logger.info("注册快捷键...")
    logger.info(f"F9 - 开始录制")
    logger.info(f"F10 - 开始回放")
    logger.info(f"F11 - 停止")
    logger.info(f"Ctrl+Alt+I - 插入OCR步骤")
    logger.info(f"Ctrl+Alt+S - 插入截图校验步骤")
    
    # 实际快捷键注册逻辑（需循环监听）
    def hotkey_listener():
        while True:
            if win32api.GetAsyncKeyState(win32con.VK_F9) & 0x8000:
                hotkey_start_recording()
                time.sleep(0.5)  # 防抖
            elif win32api.GetAsyncKeyState(win32con.VK_F10) & 0x8000:
                hotkey_play()
                time.sleep(0.5)
            elif win32api.GetAsyncKeyState(win32con.VK_F11) & 0x8000:
                hotkey_stop()
                time.sleep(0.5)
            elif (win32api.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000 and
                  win32api.GetAsyncKeyState(win32con.VK_MENU) & 0x8000 and
                  win32api.GetAsyncKeyState(ord('I')) & 0x8000):
                hotkey_insert_ocr()
                time.sleep(0.5)
            elif (win32api.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000 and
                  win32api.GetAsyncKeyState(win32con.VK_MENU) & 0x8000 and
                  win32api.GetAsyncKeyState(ord('S')) & 0x8000):
                hotkey_insert_screenshot_check()
                time.sleep(0.5)
            time.sleep(0.01)
    
    # 启动快捷键监听线程
    threading.Thread(target=hotkey_listener, daemon=True).start()

def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("SnapValid 启动成功")
    logger.info("轻量强大的键盘鼠标自动化 + OCR验证码识别 + 截图相似度校验工具")
    logger.info("=" * 50)
    
    # 初始化
    try:
        get_config()  # 加载配置
        register_hotkeys()  # 注册快捷键
        
        # 鼠标移动录制线程
        def mouse_move_listener():
            last_x, last_y = win32api.GetCursorPos()
            while True:
                if recorder.is_recording:
                    x, y = win32api.GetCursorPos()
                    if x != last_x or y != last_y:
                        recorder.record_mouse_move(x, y)
                        last_x, last_y = x, y
                time.sleep(recorder.config["recorder"]["record_interval"])
        
        threading.Thread(target=mouse_move_listener, daemon=True).start()
        
        # 保持程序运行
        logger.info("程序已就绪，按F9开始录制")
        while True:
            time.sleep(1)
    except Exception as e:
        logger.error(f"程序初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import time  # 补充导入
    main()