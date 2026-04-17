"""核心模块：提供自动化、OCR、校验等核心功能"""
from .engine import AutoEngine
from .recorder import ActionRecorder
from .keyboard import KeyboardController
from .mouse import MouseController
from .ocr import OCRRecognizer
from .compare import ImageComparator
from .selector import RegionSelector

__all__ = [
    "AutoEngine", "ActionRecorder",
    "KeyboardController", "MouseController",
    "OCRRecognizer", "ImageComparator",
    "RegionSelector"
]