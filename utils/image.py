import cv2

def preprocess(path):
    img = cv2.imread(path, 0)
    img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return img