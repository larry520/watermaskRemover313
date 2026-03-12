"""
Mask 生成模块
"""
import cv2
import numpy as np
from typing import List, Tuple, Dict
from loguru import logger


class MaskGenerator:
    """生成水印 Mask"""
    
    def __init__(self, config: Dict):
        """
        初始化生成器
        
        Args:
            config: 配置字典
        """
        self.config = config.get('mask', {})
        
    def generate(self, image: np.ndarray, 
                boxes: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """
        生成水印 Mask
        
        Args:
            image: 原图
            boxes: 水印边界框列表 [(x1, y1, x2, y2), ...]
            
        Returns:
            Mask 数组（0-255，白色为待修复区域）
        """
        if not boxes:
            logger.warning("没有水印区域，返回空 Mask")
            return np.zeros(image.shape[:2], dtype=np.uint8)
        
        logger.info(f"生成 Mask，包含 {len(boxes)} 个区域")
        
        # 创建空白 mask
        mask = self._create_blank_mask(image)
        
        # 绘制水印区域
        mask = self._draw_boxes(mask, boxes)
        
        # 优化 mask
        mask = self._optimize_mask(mask)
        
        logger.info("Mask 生成完成")
        
        return mask
    
    def _create_blank_mask(self, image: np.ndarray) -> np.ndarray:
        """
        创建空白 mask
        
        Args:
            image: 参考图片
            
        Returns:
            空白 mask
        """
        return np.zeros(image.shape[:2], dtype=np.uint8)
    
    def _draw_boxes(self, mask: np.ndarray, 
                   boxes: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """
        在 mask 上绘制矩形区域
        
        Args:
            mask: mask 数组
            boxes: 边界框列表
            
        Returns:
            绘制后的 mask
        """
        for box in boxes:
            x1, y1, x2, y2 = box
            # 绘制白色矩形（255 表示需要修复的区域）
            cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
            logger.debug(f"绘制 Mask 区域: ({x1}, {y1}) -> ({x2}, {y2})")
        
        return mask
    
    def _optimize_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        优化 mask（扩展、模糊等）
        
        Args:
            mask: 原始 mask
            
        Returns:
            优化后的 mask
        """
        optimized_mask = mask.copy()
        
        # 边缘扩展
        if self.config.get('enable_morphology', True):
            optimized_mask = self._expand_mask(optimized_mask)
        
        # 边缘模糊
        if self.config.get('enable_blur', True):
            optimized_mask = self._blur_mask(optimized_mask)
        
        return optimized_mask
    
    def _expand_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        扩展 mask 区域（膨胀操作）
        
        Args:
            mask: 输入 mask
            
        Returns:
            扩展后的 mask
        """
        kernel_size = self.config.get('dilate_kernel_size', 5)
        iterations = self.config.get('dilate_iterations', 2)
        
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        expanded = cv2.dilate(mask, kernel, iterations=iterations)
        
        logger.debug(f"Mask 扩展: kernel={kernel_size}x{kernel_size}, iterations={iterations}")
        
        return expanded
    
    def _blur_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        模糊 mask 边缘
        
        Args:
            mask: 输入 mask
            
        Returns:
            模糊后的 mask
        """
        kernel_size = self.config.get('blur_kernel_size', 5)
        sigma = self.config.get('blur_sigma', 0)
        
        # 确保 kernel_size 是奇数
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        blurred = cv2.GaussianBlur(mask, (kernel_size, kernel_size), sigma)
        
        logger.debug(f"Mask 模糊: kernel={kernel_size}x{kernel_size}, sigma={sigma}")
        
        return blurred
    
    def generate_with_expansion(self, image: np.ndarray,
                               boxes: List[Tuple[int, int, int, int]],
                               expand_pixels: int = 0) -> np.ndarray:
        """
        生成 mask 并额外扩展指定像素
        
        Args:
            image: 原图
            boxes: 边界框列表
            expand_pixels: 额外扩展像素数
            
        Returns:
            Mask 数组
        """
        # 扩展边界框
        expanded_boxes = []
        h, w = image.shape[:2]
        
        for x1, y1, x2, y2 in boxes:
            x1 = max(0, x1 - expand_pixels)
            y1 = max(0, y1 - expand_pixels)
            x2 = min(w, x2 + expand_pixels)
            y2 = min(h, y2 + expand_pixels)
            expanded_boxes.append((x1, y1, x2, y2))
        
        return self.generate(image, expanded_boxes)
    
    def visualize(self, image: np.ndarray, mask: np.ndarray, 
                 alpha: float = 0.5) -> np.ndarray:
        """
        可视化 mask（用于调试）
        
        Args:
            image: 原图
            mask: mask
            alpha: 透明度
            
        Returns:
            叠加了 mask 的图片
        """
        # 确保图片是 BGR 格式
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
        # 创建红色遮罩
        overlay = image.copy()
        overlay[mask > 0] = [0, 0, 255]  # BGR: 红色
        
        # 混合
        result = cv2.addWeighted(image, 1 - alpha, overlay, alpha, 0)
        return result
    
    def get_mask_info(self, mask: np.ndarray) -> Dict:
        """
        获取 mask 信息
        
        Args:
            mask: mask 数组
            
        Returns:
            信息字典
        """
        total_pixels = mask.size
        mask_pixels = np.sum(mask > 0)
        mask_ratio = mask_pixels / total_pixels
        
        return {
            'total_pixels': total_pixels,
            'mask_pixels': int(mask_pixels),
            'mask_ratio': mask_ratio,
            'mask_percentage': f"{mask_ratio * 100:.2f}%"
        }
