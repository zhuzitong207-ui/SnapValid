# img_utils.py
import os
import pyautogui
from PIL import Image
import imagehash

_ocr = None

def _get_ocr():
    global _ocr
    if _ocr is None:
        try:
            import ddddocr
            _ocr = ddddocr.DdddOcr(det=False, ocr=True)
        except ImportError:
            print("[SnapValid] 警告: ddddocr 未安装，验证码识别功能不可用")
            _ocr = False
    return _ocr if _ocr is not False else None

def capture_screen(x1, y1, x2, y2, save_path):
    try:
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        if width < 5 or height < 5:
            print("[SnapValid] 截图区域太小，忽略")
            return False
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        img = pyautogui.screenshot(region=(left, top, width, height))
        img.save(save_path)
        return True
    except Exception as e:
        print(f"[SnapValid] 截图错误: {e}")
        return False

def compare_img_similarity(p1, p2):
    try:
        img1 = Image.open(p1).resize((128, 128)).convert('L')
        img2 = Image.open(p2).resize((128, 128)).convert('L')
        hash1 = imagehash.phash(img1)
        hash2 = imagehash.phash(img2)
        hamming_dist = abs(hash1 - hash2)
        similarity = 1.0 - (hamming_dist / 64.0)
        return round(similarity, 4)
    except Exception as e:
        print(f"[SnapValid] 图片比对错误: {e}")
        return 0.0

def recognize_code(image_path):
    ocr = _get_ocr()
    if ocr is None:
        return "OCR_ERROR"
    try:
        with open(image_path, 'rb') as f:
            result = ocr.classification(f.read())
        return result
    except Exception as e:
        print(f"[SnapValid] OCR识别错误: {e}")
        return "OCR_ERROR"