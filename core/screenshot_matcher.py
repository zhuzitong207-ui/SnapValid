import time
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import bool
from utils.log_utils import logger
from utils.config_utils import get_config

class ScreenshotMatcher:
    def __init__(self):
        self.config = get_config()
    
    def match(
        self,
        roi: list,
        reference_img: str,
        similarity_threshold: float = None,
        timeout: float = None,
        check_interval: float = None
    ) -> bool:
        """
        截图相似度校验
        :param roi: [x1, y1, x2, y2] 校验区域
        :param reference_img: 基准截图路径
        :param similarity_threshold: 相似度阈值
        :param timeout: 超时时间
        :param check_interval: 校验间隔
        :return: 是否匹配成功
        """
        # 参数初始化
        similarity_threshold = similarity_threshold or self.config["screenshot"]["similarity_threshold"]
        timeout = timeout or self.config["screenshot"]["timeout"]
        check_interval = check_interval or self.config["screenshot"]["check_interval"]
        
        # 加载基准截图
        reference_path = Path(reference_img)
        if not reference_path.exists():
            logger.error(f"基准截图不存在: {reference_path}")
            raise FileNotFoundError(f"基准截图不存在: {reference_path}")
        
        ref_img = cv2.imread(str(reference_path), cv2.IMREAD_GRAYSCALE)
        if ref_img is None:
            logger.error(f"基准截图加载失败: {reference_path}")
            raise ValueError(f"基准截图加载失败: {reference_path}")
        
        # 循环校验直到超时
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # 截取当前区域
                x1, y1, x2, y2 = roi
                current_img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                current_img_cv = cv2.cvtColor(np.array(current_img), cv2.COLOR_RGB2GRAY)
                
                # 调整尺寸匹配基准截图
                current_img_cv = cv2.resize(current_img_cv, (ref_img.shape[1], ref_img.shape[0]))
                
                # 计算相似度（模板匹配）
                result = cv2.matchTemplate(current_img_cv, ref_img, cv2.TM_CCOEFF_NORMED)
                similarity = np.max(result)
                
                logger.debug(f"截图相似度校验: {similarity:.4f} (阈值: {similarity_threshold})")
                
                if similarity >= similarity_threshold:
                    logger.info(f"截图校验通过，相似度: {similarity:.4f}")
                    return True
                
                time.sleep(check_interval)
            except Exception as e:
                logger.warning(f"截图校验失败，重试: {e}")
                time.sleep(check_interval)
        
        logger.error(f"截图校验超时({timeout}s)，未达到相似度阈值")
        return False

# 补充ImageGrab导入
try:
    from PIL import ImageGrab
except ImportError:
    logger.warning("PIL.ImageGrab不可用（非Windows系统）")