"""
水印去除主类
"""
import yaml
import numpy as np
from pathlib import Path
from typing import Union, Dict, List, Tuple, Optional
from loguru import logger

from .ocr_detector import WatermarkDetector
from .mask_generator import MaskGenerator
from .inpainter import ImageInpainter
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.image_utils import ImageUtils


class WatermarkRemover:
    """水印去除主类"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        初始化水印去除器
        
        Args:
            config_path: 配置文件路径，如果为 None 则使用默认配置
        """
        self.config = self._load_config(config_path)
        self._setup_logger()
        
        # 初始化各个模块
        logger.info("初始化水印去除系统...")
        self.detector = WatermarkDetector(self.config)
        self.mask_generator = MaskGenerator(self.config)
        self.inpainter = ImageInpainter(self.config)
        logger.info("系统初始化完成")
        
    def _load_config(self, config_path: Optional[Union[str, Path]]) -> Dict:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        if config_path is None:
            # 使用默认配置
            config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
        
        config_path = Path(config_path)
        
        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self._get_default_config()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'ocr': {
                'languages': ['ch_sim', 'en'],
                'gpu': True,
                'min_confidence': 0.5,
            },
            'mask': {
                'expand_pixels': 5,
                'enable_morphology': True,
                'dilate_iterations': 2,
            },
            'inpaint': {
                'model': 'lama',
                'device': 'cuda',
            }
        }
    
    def _setup_logger(self):
        """设置日志"""
        log_config = self.config.get('logging', {})
        level = log_config.get('level', 'INFO')
        log_format = log_config.get('format', 
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
            "<level>{message}</level>"
        )
        
        logger.remove()
        logger.add(
            sys.stderr,
            format=log_format,
            level=level,
            colorize=True
        )
    
    def remove(self, input_path: Union[str, Path], 
               output_path: Union[str, Path],
               return_mask: bool = False,
               visualize_detection: bool = False) -> Union[np.ndarray, Tuple]:
        """
        去除图片水印
        
        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            return_mask: 是否返回 mask
            visualize_detection: 是否可视化检测结果
            
        Returns:
            如果 return_mask=True，返回 (result_image, mask)
            否则返回 result_image
        """
        logger.info(f"处理图片: {input_path}")
        
        # 1. 加载图片
        image_rgb = ImageUtils.load_image_rgb(input_path)
        logger.info(f"图片尺寸: {image_rgb.shape[1]}x{image_rgb.shape[0]}")
        
        # 2. 检测水印
        watermark_boxes = self.detector.detect(image_rgb)
        
        if not watermark_boxes:
            logger.warning("未检测到水印，保存原图")
            ImageUtils.save_image(
                ImageUtils.rgb_to_bgr(image_rgb), 
                output_path
            )
            if return_mask:
                return image_rgb, np.zeros(image_rgb.shape[:2], dtype=np.uint8)
            return image_rgb
        
        # 3. 生成 mask
        mask = self.mask_generator.generate(image_rgb, watermark_boxes)
        mask_info = self.mask_generator.get_mask_info(mask)
        logger.info(f"Mask 信息: {mask_info['mask_percentage']} 的像素被标记")
        
        # 4. 修复图片
        result_rgb = self.inpainter.inpaint(image_rgb, mask)
        
        # 5. 保存结果
        ImageUtils.save_image(ImageUtils.rgb_to_bgr(result_rgb), output_path)
        logger.info(f"结果已保存: {output_path}")
        
        # 可视化检测结果（可选）
        if visualize_detection:
            vis_path = self._get_visualization_path(output_path, '_detection')
            vis_image = self.mask_generator.visualize(
                ImageUtils.rgb_to_bgr(image_rgb), 
                mask
            )
            ImageUtils.save_image(vis_image, vis_path)
            logger.info(f"检测可视化已保存: {vis_path}")
        
        if return_mask:
            return result_rgb, mask
        return result_rgb
    
    def remove_from_array(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        从 numpy 数组去除水印
        
        Args:
            image: RGB 格式的图片数组
            
        Returns:
            (修复后的图片, mask)
        """
        # 检测水印
        watermark_boxes = self.detector.detect(image)
        
        if not watermark_boxes:
            logger.warning("未检测到水印")
            return image, np.zeros(image.shape[:2], dtype=np.uint8)
        
        # 生成 mask
        mask = self.mask_generator.generate(image, watermark_boxes)
        
        # 修复图片
        result = self.inpainter.inpaint(image, mask)
        
        return result, mask
    
    def batch_remove(self, input_dir: Union[str, Path],
                    output_dir: Union[str, Path],
                    pattern: str = '*.*') -> List[str]:
        """
        批量处理图片
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            pattern: 文件匹配模式
            
        Returns:
            处理成功的文件列表
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取所有图片文件
        image_files = list(input_dir.glob(pattern))
        image_files = [f for f in image_files if f.suffix.lower() in 
                      ['.jpg', '.jpeg', '.png', '.bmp', '.webp']]
        
        total = len(image_files)
        logger.info(f"找到 {total} 个图片文件")
        
        success_files = []
        
        for i, input_path in enumerate(image_files, 1):
            try:
                logger.info(f"[{i}/{total}] 处理: {input_path.name}")
                output_path = output_dir / input_path.name
                self.remove(input_path, output_path)
                success_files.append(str(input_path))
            except Exception as e:
                logger.error(f"处理失败: {input_path.name}, 错误: {e}")
        
        logger.info(f"批量处理完成: 成功 {len(success_files)}/{total}")
        return success_files
    
    def detect_only(self, input_path: Union[str, Path]) -> List[Dict]:
        """
        仅检测水印（不修复）
        
        Args:
            input_path: 输入图片路径
            
        Returns:
            检测信息列表
        """
        image_rgb = ImageUtils.load_image_rgb(input_path)
        return self.detector.get_detection_info(image_rgb)
    
    def get_system_info(self) -> Dict:
        """
        获取系统信息
        
        Returns:
            系统信息字典
        """
        return {
            'detector': {
                'languages': self.config['ocr']['languages'],
                'gpu': self.config['ocr']['gpu'],
            },
            'inpainter': self.inpainter.get_model_info(),
            'config': self.config
        }
    
    @staticmethod
    def _get_visualization_path(output_path: Union[str, Path], 
                               suffix: str) -> Path:
        """
        生成可视化文件路径
        
        Args:
            output_path: 原输出路径
            suffix: 后缀
            
        Returns:
            可视化文件路径
        """
        output_path = Path(output_path)
        stem = output_path.stem
        ext = output_path.suffix
        return output_path.parent / f"{stem}{suffix}{ext}"
