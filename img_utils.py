# SnapValid 图片工具模块 | 截图 OCR 相似度对比
import cv2
import numpy as np
import ddddocr
import os
import time
from PIL import Image
import imagehash
import pyautogui

# 初始化OCR
ocr = ddddocr.DdddOcr()

def save_screenshot(x1, y1, x2, y2, prefix):
    """保存截图到临时目录"""
    temp_path = "./temp/"
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)
    img = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
    filename = f"{prefix}_{int(time.time())}.png"
    path = os.path.join(temp_path, filename)
    img.save(path)
    return path

def ocr_recognize(img_path):
    """OCR识别"""
    try:
        with open(img_path, "rb") as f:
            img_bytes = f.read()
        return ocr.classification(img_bytes)
    except Exception as e:
        return f"识别失败：{str(e)}"

def image_compare(original_path, x1, y1, x2, y2):
    """图片相似度对比 0-1"""
    try:
        # 截取当前画面
        current_img = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
        current_img = current_img.resize((128, 128))
        # 加载基准图
        original_img = Image.open(original_path).resize((128, 128))
        # 哈希对比
        hash0 = imagehash.average_hash(original_img)
        hash1 = imagehash.average_hash(current_img)
        similarity = 1 - (hash0 - hash1) / len(hash0.hash) ** 2
        return round(similarity, 4)
    except Exception as e:
        return 0.0
