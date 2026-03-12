"""
IOPaint 图像修复模块
"""
import numpy as np
from typing import Dict, Optional
from loguru import logger

try:
    from iopaint.model_manager import ModelManager
    from iopaint.schema import InpaintRequest, HDStrategy
    IOPAINT_AVAILABLE = True
except ImportError:
    IOPAINT_AVAILABLE = False
    logger.warning("IOPaint 未安装，将使用 OpenCV 修复作为后备方案")

import cv2


class ImageInpainter:
    """图像修复器"""
    
    def __init__(self, config: Dict):
        """
        初始化修复器
        
        Args:
            config: 配置字典
        """
        self.config = config.get('inpaint', {})
        self.model = None
        self.use_iopaint = IOPAINT_AVAILABLE
        
        if self.use_iopaint:
            self._init_iopaint()
        else:
            logger.info("使用 OpenCV inpaint 作为修复方法")
    
    def _init_iopaint(self):
        """初始化 IOPaint 模型"""
        model_name = self.config.get('model', 'lama')
        device = self.config.get('device', 'cuda')
        
        try:
            logger.info(f"加载 IOPaint 模型: {model_name}, 设备: {device}")
            self.model = ModelManager(
                name=model_name,
                device=device
            )
            logger.info("IOPaint 模型加载成功")
        except Exception as e:
            logger.error(f"IOPaint 模型加载失败: {e}")
            logger.info("降级使用 OpenCV inpaint")
            self.use_iopaint = False
    
    def inpaint(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        修复图片
        
        Args:
            image: 原图 (RGB 格式)
            mask: mask (0-255，白色为待修复区域)
            
        Returns:
            修复后的图片 (RGB 格式)
        """
        logger.info("开始图像修复...")
        
        if self.use_iopaint and self.model is not None:
            result = self._inpaint_with_iopaint(image, mask)
        else:
            result = self._inpaint_with_opencv(image, mask)
        
        logger.info("图像修复完成")
        return result
    
    def _inpaint_with_iopaint(self, image: np.ndarray, 
                             mask: np.ndarray) -> np.ndarray:
        """
        使用 IOPaint 修复
        
        Args:
            image: 原图
            mask: mask
            
        Returns:
            修复后的图片
        """
        try:
            # 准备配置
            config = self._get_iopaint_config()
            
            # 确保 mask 是二值化的
            mask_binary = (mask > 127).astype(np.uint8) * 255
            
            # 执行修复
            logger.debug("执行 IOPaint 修复...")
            result = self.model(image, mask_binary, config)
            result = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            return result
            
        except Exception as e:
            logger.error(f"IOPaint 修复失败: {e}")
            logger.info("降级使用 OpenCV inpaint")
            return self._inpaint_with_opencv(image, mask)
    
    def _inpaint_with_opencv(self, image: np.ndarray, 
                            mask: np.ndarray) -> np.ndarray:
        """
        使用 OpenCV 修复（后备方案）
        
        Args:
            image: 原图 (RGB 格式)
            mask: mask
            
        Returns:
            修复后的图片 (RGB 格式)
        """
        logger.debug("使用 OpenCV inpaint...")
        
        # OpenCV 需要 BGR 格式
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # 确保 mask 是单通道
        if len(mask.shape) == 3:
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        
        # 使用 Navier-Stokes 方法修复
        result_bgr = cv2.inpaint(
            image_bgr, 
            mask, 
            inpaintRadius=3, 
            flags=cv2.INPAINT_NS
        )
        
        # 转回 RGB
        result = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
        
        return result
    
    def _get_iopaint_config(self) -> 'Config':
        """
        获取 IOPaint 配置
        
        Returns:
            Config 对象
        """
        if not IOPAINT_AVAILABLE:
            return None
        
        # HD 策略映射
        hd_strategy_map = {
            'Original': HDStrategy.ORIGINAL,
            'Resize': HDStrategy.RESIZE,
            'Crop': HDStrategy.CROP
        }
        
        hd_strategy_str = self.config.get('hd_strategy', 'Resize')
        hd_strategy = hd_strategy_map.get(hd_strategy_str, HDStrategy.RESIZE)
        
        config = InpaintRequest(
            hd_strategy=hd_strategy,
            hd_strategy_resize_limit=self.config.get('hd_strategy_resize_limit', 2048),
            hd_strategy_crop_margin=self.config.get('hd_strategy_crop_margin', 128),
            hd_strategy_crop_trigger_size=self.config.get('hd_strategy_crop_trigger_size', 2048),
        )
        
        return config
    
    def batch_inpaint(self, images: list, masks: list) -> list:
        """
        批量修复图片
        
        Args:
            images: 图片列表
            masks: mask 列表
            
        Returns:
            修复后的图片列表
        """
        results = []
        total = len(images)
        
        for i, (image, mask) in enumerate(zip(images, masks)):
            logger.info(f"修复进度: {i+1}/{total}")
            result = self.inpaint(image, mask)
            results.append(result)
        
        return results
    
    def get_model_info(self) -> Dict:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            'using_iopaint': self.use_iopaint,
            'model_name': self.config.get('model', 'opencv'),
            'device': self.config.get('device', 'cpu'),
            'hd_strategy': self.config.get('hd_strategy', 'N/A')
        }
