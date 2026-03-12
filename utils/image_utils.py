"""
图像处理工具类
"""
import cv2
import numpy as np
from PIL import Image
from typing import Union, Tuple
from pathlib import Path
import re

class ImageUtils:
    """图像处理工具类"""
    
    @staticmethod
    def load_image(image_path: Union[str, Path]) -> np.ndarray:
        """
        加载图片
        
        Args:
            image_path: 图片路径
            
        Returns:
            BGR 格式的 numpy 数组
        """
        image_path = str(image_path)
        if re.search(r'[\u4e00-\u9fa5]', image_path):
            data = np.fromfile(image_path, dtype=np.uint8)
            image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        else:
            image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"无法加载图片: {image_path}")
        return image
    
    @staticmethod
    def load_image_rgb(image_path: Union[str, Path]) -> np.ndarray:
        """
        加载图片（RGB 格式）
        
        Args:
            image_path: 图片路径
            
        Returns:
            RGB 格式的 numpy 数组
        """
        image = ImageUtils.load_image(image_path)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    @staticmethod
    def save_image(image: np.ndarray, output_path: Union[str, Path], 
                   quality: int = 95) -> None:
        """
        保存图片
        
        Args:
            image: 图片数组
            output_path: 输出路径
            quality: JPEG 质量 (1-100)
        """
        output_path = str(output_path)
        
        # 确保输出目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 根据文件扩展名选择保存参数
        ext = Path(output_path).suffix.lower()
        if re.search(r'[\u4e00-\u9fa5]', output_path):
            res, data = cv2.imencode(ext, image)
            data.tofile(output_path)
        else:
            if ext in ['.jpg', '.jpeg']:
                cv2.imwrite(output_path, image,
                            [cv2.IMWRITE_JPEG_QUALITY, quality])
            elif ext == '.png':
                cv2.imwrite(output_path, image,
                            [cv2.IMWRITE_PNG_COMPRESSION, 9 - quality // 11])
            else:
                cv2.imwrite(output_path, image)
    
    @staticmethod
    def resize_image(image: np.ndarray, max_size: int = 2048) -> Tuple[np.ndarray, float]:
        """
        调整图片大小（保持宽高比）
        
        Args:
            image: 输入图片
            max_size: 最大边长
            
        Returns:
            调整后的图片和缩放比例
        """
        h, w = image.shape[:2]
        
        if max(h, w) <= max_size:
            return image, 1.0
        
        # 计算缩放比例
        scale = max_size / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return resized, scale
    
    @staticmethod
    def bgr_to_rgb(image: np.ndarray) -> np.ndarray:
        """BGR 转 RGB"""
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    @staticmethod
    def rgb_to_bgr(image: np.ndarray) -> np.ndarray:
        """RGB 转 BGR"""
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    @staticmethod
    def create_blank_mask(image: np.ndarray) -> np.ndarray:
        """
        创建空白 mask
        
        Args:
            image: 参考图片
            
        Returns:
            空白 mask (黑色背景)
        """
        return np.zeros(image.shape[:2], dtype=np.uint8)
    
    @staticmethod
    def expand_mask(mask: np.ndarray, pixels: int = 5, 
                    iterations: int = 1) -> np.ndarray:
        """
        扩展 mask 区域
        
        Args:
            mask: 输入 mask
            pixels: 扩展像素数
            iterations: 迭代次数
            
        Returns:
            扩展后的 mask
        """
        kernel = np.ones((pixels, pixels), np.uint8)
        expanded = cv2.dilate(mask, kernel, iterations=iterations)
        return expanded
    
    @staticmethod
    def blur_mask(mask: np.ndarray, kernel_size: int = 5, 
                  sigma: float = 0) -> np.ndarray:
        """
        模糊 mask 边缘
        
        Args:
            mask: 输入 mask
            kernel_size: 核大小（必须是奇数）
            sigma: 标准差
            
        Returns:
            模糊后的 mask
        """
        if kernel_size % 2 == 0:
            kernel_size += 1
        blurred = cv2.GaussianBlur(mask, (kernel_size, kernel_size), sigma)
        return blurred
    
    @staticmethod
    def visualize_mask(image: np.ndarray, mask: np.ndarray, 
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
        # 创建红色遮罩
        overlay = image.copy()
        overlay[mask > 0] = [0, 0, 255]  # BGR: 红色
        
        # 混合
        result = cv2.addWeighted(image, 1 - alpha, overlay, alpha, 0)
        return result
    
    @staticmethod
    def get_image_size(image: np.ndarray) -> Tuple[int, int]:
        """
        获取图片尺寸
        
        Returns:
            (width, height)
        """
        h, w = image.shape[:2]
        return w, h
    
    @staticmethod
    def is_in_region(point: Tuple[int, int], region: str, 
                     image_size: Tuple[int, int], ratio: float = 0.3) -> bool:
        """
        判断点是否在指定区域
        
        Args:
            point: (x, y) 坐标
            region: 区域类型 ('top_left', 'top_right', 'bottom_left', 'bottom_right', 'edge')
            image_size: 图片尺寸 (width, height)
            ratio: 区域占比
            
        Returns:
            是否在区域内
        """
        x, y = point
        w, h = image_size
        
        threshold_w = int(w * ratio)
        threshold_h = int(h * ratio)
        
        if region == 'top_left':
            return x < threshold_w and y < threshold_h
        elif region == 'top_right':
            return x > w - threshold_w and y < threshold_h
        elif region == 'bottom_left':
            return x < threshold_w and y > h - threshold_h
        elif region == 'bottom_right':
            return x > w - threshold_w and y > h - threshold_h
        elif region == 'edge':
            return (x < threshold_w or x > w - threshold_w or 
                   y < threshold_h or y > h - threshold_h)
        return False
