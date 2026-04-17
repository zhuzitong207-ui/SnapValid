import time
import json
from pathlib import Path
from typing import List, Dict, Any
import win32api
import win32con
import win32gui
from utils.log_utils import logger
from utils.config_utils import get_config
from core.ocr_engine import OCREngine
from core.screenshot_matcher import ScreenshotMatcher

class Player:
    def __init__(self):
        self.config = get_config()
        self.is_playing = False
        self.play_speed = self.config["player"]["play_speed"]
        self.retry_times = self.config["player"]["retry_times"]
        self.retry_interval = self.config["player"]["retry_interval"]
        self.ocr_engine = OCREngine()
        self.screenshot_matcher = ScreenshotMatcher()
    
    def play(self, script_path: str) -> bool:
        """回放指定脚本"""
        if self.is_playing:
            logger.warning("已在回放中")
            return False
        
        script_path = Path(script_path)
        if not script_path.exists():
            logger.error(f"脚本文件不存在: {script_path}")
            return False
        
        # 加载脚本
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                steps = json.load(f)
        except Exception as e:
            logger.error(f"加载脚本失败: {e}")
            return False
        
        self.is_playing = True
        logger.info(f"开始回放脚本: {script_path} (速度倍率: {self.play_speed})")
        start_time = time.time()
        
        try:
            for step in steps:
                if not self.is_playing:
                    break
                
                # 按时间戳等待
                time.sleep(max(0, step["timestamp"] / self.play_speed - (time.time() - start_time)))
                
                # 执行步骤
                self._execute_step(step)
            
            logger.info("脚本回放完成")
            return True
        except Exception as e:
            logger.error(f"回放失败: {e}")
            return False
        finally:
            self.is_playing = False
    
    def stop(self):
        """停止回放"""
        if self.is_playing:
            self.is_playing = False
            logger.info("回放已停止")
    
    def _execute_step(self, step: Dict[str, Any]):
        """执行单个步骤"""
        step_type = step["type"]
        logger.debug(f"执行步骤: {step_type} - {step}")
        
        # 重试装饰器
        def retry(func):
            def wrapper(*args, **kwargs):
                for i in range(self.retry_times):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if i == self.retry_times - 1:
                            raise
                        logger.warning(f"步骤执行失败，重试({i+1}/{self.retry_times}): {e}")
                        time.sleep(self.retry_interval)
                return None
            return wrapper
        
        # 执行不同类型的步骤
        if step_type == "mouse_move":
            retry(self._move_mouse)(step["x"], step["y"])
        elif step_type == "mouse_click":
            retry(self._click_mouse)(step["x"], step["y"], step["button"])
        elif step_type == "key_press":
            retry(self._press_key)(step["key"])
        elif step_type == "ocr":
            text = retry(self.ocr_engine.recognize)(**step["params"])
            retry(self._type_text)(text)
        elif step_type == "screenshot_check":
            retry(self.screenshot_matcher.match)(**step["params"])
        else:
            logger.warning(f"未知步骤类型: {step_type}")
    
    @staticmethod
    def _move_mouse(x: int, y: int):
        """移动鼠标"""
        win32api.SetCursorPos((x, y))
    
    @staticmethod
    def _click_mouse(x: int, y: int, button: str):
        """点击鼠标"""
        win32api.SetCursorPos((x, y))
        if button == "left":
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        elif button == "right":
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x, y, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x, y, 0, 0)
        elif button == "middle":
            win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, x, y, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, x, y, 0, 0)
    
    @staticmethod
    def _press_key(key: str):
        """按下按键"""
        # 此处需扩展按键映射，示例仅为框架
        key_code = win32api.VkKeyScan(key)
        win32api.keybd_event(key_code, 0, 0, 0)
        win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)
    
    @staticmethod
    def _type_text(text: str):
        """输入文本"""
        for char in text:
            win32api.keybd_event(win32api.VkKeyScan(char), 0, 0, 0)
            win32api.keybd_event(win32api.VkKeyScan(char), 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.05)