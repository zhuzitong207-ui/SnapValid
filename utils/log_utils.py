import sys
from pathlib import Path
from loguru import logger
from utils.config_utils import get_config

def init_logger():
    """初始化日志系统"""
    config = get_config()
    log_dir = Path(config["basic"]["log_path"])
    log_dir.mkdir(exist_ok=True)
    
    # 移除默认日志处理器
    logger.remove()
    
    # 控制台日志格式
    console_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    logger.add(
        sys.stdout,
        format=console_format,
        level=config["basic"]["log_level"],
        enqueue=True
    )
    
    # 文件日志格式（结构化）
    file_format = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    logger.add(
        log_dir / "run_{time:YYYYMMDD}.log",
        format=file_format,
        level=config["basic"]["log_level"],
        rotation="00:00",  # 每日轮转
        retention="7 days",  # 保留7天
        enqueue=True,
        encoding="utf-8"
    )
    
    return logger

# 全局日志实例
logger = init_logger()