# SnapValid 图片工具核心模块
# 功能：屏幕截图、图片相似度对比、OCR验证码识别
# 适配：Windows/Linux/Mac
import pyautogui
from PIL import Image
import imagehash
import os

def capture_screen(x1, y1, x2, y2, save_path):
    try:
        left = min(x1, x2)
        top = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        if w < 5 or h < 5:
            return False
        img = pyautogui.screenshot(region=(left, top, w, h))
        img.save(save_path)
        return True
    except Exception as e:
        print("SnapValid 截图错误:", e)
        return False

def compare_img_similarity(p1, p2):
    try:
        i1 = Image.open(p1).resize((128, 128))
        i2 = Image.open(p2).resize((128, 128))
        h1 = imagehash.phash(i1)
        h2 = imagehash.phash(i2)
        return round(1 - (abs(h1 - h2) / 64), 2)
    except:
        return 0.0

def recognize_code(path):
    try:
        import ddddocr
        ocr = ddddocr.DdddOcr(det=False, ocr=True)
        with open(path, 'rb') as f:
            return ocr.classification(f.read())
    except Exception as e:
        print("SnapValid OCR识别错误:", e)
        return "OCR_ERROR"
