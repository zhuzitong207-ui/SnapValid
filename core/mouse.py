import pyautogui

def move(x, y, duration=0.1):
    pyautogui.moveTo(x, y, duration=duration)

def click(x, y):
    pyautogui.click(x, y)