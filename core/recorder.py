import time
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any
import win32api
import win32con
import win32gui
from utils.log_utils import logger
from utils.config_utils import get_config

@dataclass
class RecordStep:
    """录制步骤数据结构"""
    type: str  # mouse_move/mouse_click/key_press/ocr/screenshot_check
    timestamp: float
    x: int = 0
    y: int = 0
    button: str = ""  # left/right/middle
    key: str = ""     # 按键名称
    params: Dict[str, Any] = None  # OCR/截图校验的额外参数

class Recorder:
    def __init__(self):
        self.config = get_config()
        self.is_recording = False
        self.record_steps: List[RecordStep] = []
        self.start_time = 0.0
        self.script_save_path = Path(self.config["basic"]["script_save_path"])
        self.script_save_path.mkdir(exist_ok=True)
    
    def start(self):
        """开始录制"""
        if self.is_recording:
            logger.warning("已在录制中")
            return
        
        self.is_recording = True
        self.start_time = time.time()
        self.record_steps.clear()
        logger.info("开始录制（按F11停止）")
    
    def stop(self) -> str:
        """停止录制并保存脚本"""
        if not self.is_recording:
            logger.warning("未在录制中")
            return ""
        
        self.is_recording = False
        script_filename = f"script_{int(time.time())}_{len(self.record_steps)}ops.json"
        script_path = self.script_save_path / script_filename
        
        # 保存录制步骤
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(
                [asdict(step) for step in self.record_steps],
                f,
                ensure_ascii=False,
                indent=2
            )
        
        logger.info(f"录制停止，脚本已保存: {script_path}")
        return str(script_path)
    
    def record_mouse_move(self, x: int, y: int):
        """录制鼠标移动"""
        if not self.is_recording or not self.config["recorder"]["record_mouse_move"]:
            return
        
        step = RecordStep(
            type="mouse_move",
            timestamp=time.time() - self.start_time,
            x=x,
            y=y
        )
        self.record_steps.append(step)
    
    def record_mouse_click(self, x: int, y: int, button: str):
        """录制鼠标点击"""
        if not self.is_recording:
            return
        
        step = RecordStep(
            type="mouse_click",
            timestamp=time.time() - self.start_time,
            x=x,
            y=y,
            button=button
        )
        self.record_steps.append(step)
    
    def record_key_press(self, key: str):
        """录制按键"""
        if not self.is_recording:
            return
        
        step = RecordStep(
            type="key_press",
            timestamp=time.time() - self.start_time,
            key=key
        )
        self.record_steps.append(step)
    
    def insert_ocr_step(self, x1: int, y1: int, x2: int, y2: int):
        """插入OCR识别步骤"""
        if not self.is_recording:
            logger.warning("未在录制中，无法插入OCR步骤")
            return
        
        step = RecordStep(
            type="ocr",
            timestamp=time.time() - self.start_time,
            params={
                "roi": [x1, y1, x2, y2],  # 识别区域
                "confidence_threshold": self.config["ocr"]["confidence_threshold"]
            }
        )
        self.record_steps.append(step)
        logger.info(f"已插入OCR识别步骤，区域: ({x1},{y1})-({x2},{y2})")
    
    def insert_screenshot_check_step(self, x1: int, y1: int, x2: int, y2: int):
        """插入截图校验步骤"""
        if not self.is_recording:
            logger.warning("未在录制中，无法插入截图校验步骤")
            return
        
        # 保存基准截图
        screenshot_path = Path(self.config["basic"]["screenshot_save_path"])
        screenshot_path.mkdir(exist_ok=True)
        img_filename = f"check_{int(time.time())}.png"
        img_path = screenshot_path / img_filename
        
        # 截取指定区域并保存
        self._capture_roi(x1, y1, x2, y2, img_path)
        
        step = RecordStep(
            type="screenshot_check",
            timestamp=time.time() - self.start_time,
            params={
                "roi": [x1, y1, x2, y2],
                "reference_img": str(img_path),
                "similarity_threshold": self.config["screenshot"]["similarity_threshold"],
                "timeout": self.config["screenshot"]["timeout"],
                "check_interval": self.config["screenshot"]["check_interval"]
            }
        )
        self.record_steps.append(step)
        logger.info(f"已插入截图校验步骤，基准截图: {img_path}")
    
    @staticmethod
    def _capture_roi(x1: int, y1: int, x2: int, y2: int, save_path: Path):
        """截取指定区域并保存"""
        from PIL import ImageGrab
        try:
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            img.save(save_path)
        except Exception as e:
            logger.error(f"截取区域失败: {e}")
            raise