import cv2
import numpy as np
import pytesseract
from PIL import Image
from typing import Optional
from utils.log_utils import logger
from utils.config_utils import get_config

class OCREngine:
    def __init__(self):
        self.config = get_config()
        pytesseract.pytesseract.tesseract_cmd = self.config["ocr"]["tesseract_path"]
        self.lang = self.config["ocr"]["lang"]
        self.confidence_threshold = self.config["ocr"]["confidence_threshold"]
    
    def recognize(self, roi: list, confidence_threshold: float = None) -> Optional[str]:
        """
        OCR识别指定区域
        :param roi: [x1, y1, x2, y2] 识别区域
        :param confidence_threshold: 置信度阈值
        :return: 识别结果
        """
        confidence_threshold = confidence_threshold or self.confidence_threshold
        
        # 截取区域
        try:
            x1, y1, x2, y2 = roi
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # 预处理（降噪、二值化）
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # OCR识别
            result = pytesseract.image_to_data(thresh, lang=self.lang, output_type=pytesseract.Output.DICT)
            texts = []
            confidences = []
            
            for i, conf in enumerate(result["conf"]):
                if int(conf) > confidence_threshold * 100:
                    texts.append(result["text"][i])
                    confidences.append(int(conf))
            
            if not texts:
                logger.warning("OCR识别无有效结果")
                return None
            
            final_text = "".join(texts).strip()
            avg_conf = sum(confidences) / len(confidences)
            logger.info(f"OCR识别完成: {final_text} (平均置信度: {avg_conf:.1f}%)")
            return final_text
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            raise

# 补充ImageGrab导入（解决跨平台问题）
try:
    from PIL import ImageGrab
except ImportError:
    logger.warning("PIL.ImageGrab不可用（非Windows系统）")