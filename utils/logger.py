import logging
import os
from utils.path import LOG_DIR

log_file = os.path.join(LOG_DIR, "run.log")

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)

def info(msg):
    print(f"✅ {msg}")
    logging.info(msg)

def error(msg):
    print(f"❌ {msg}")
    logging.error(msg)