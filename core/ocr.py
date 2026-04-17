import ddddocr
from utils.image import preprocess
from utils.logger import info

class OCR:
    def __init__(self):
        self.ocr = ddddocr.DdddOcr()
        info("OCR 加载完成")

    def recognize(self, path):
        try:
            img = preprocess(path)
            return self.ocr.classification(img).strip()
        except:
            return ""