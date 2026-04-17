import yaml
from pathlib import Path
from typing import Dict, Any
from utils.log_utils import logger

_CONFIG: Dict[str, Any] = None

def get_config(config_path: str = "./config.yml") -> Dict[str, Any]:
    """加载并缓存配置文件"""
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            _CONFIG = yaml.safe_load(f)
        logger.info(f"配置文件加载成功: {config_path}")
        return _CONFIG
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"配置文件解析错误: {e}")
        raise