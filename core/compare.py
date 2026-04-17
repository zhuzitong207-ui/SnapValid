import cv2
import numpy as np

def image_similarity(path1, path2):
    i1 = cv2.imread(path1, 0)
    i2 = cv2.imread(path2, 0)
    if i1 is None or i2 is None:
        return 0.0
    i1 = cv2.resize(i1, (200, 200))
    i2 = cv2.resize(i2, (200, 200))
    res = cv2.matchTemplate(i1, i2, cv2.TM_CCOEFF_NORMED)
    score = float(res[0][0])
    return max(score, 0.0)