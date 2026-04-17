import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCREENSHOT_DIR = os.path.join(ROOT, "screenshots")
LOG_DIR = os.path.join(ROOT, "logs")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)