"""
EasyOCR 水印检测模块
"""
import easyocr
import numpy as np
from typing import List, Tuple, Dict, Optional
from loguru import logger


class WatermarkDetector:
    """使用 EasyOCR 检测水印位置"""
    
    def __init__(self, config: Dict):
        """
        初始化检测器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.ocr_config = config.get('ocr', {})
        self.detection_config = config.get('detection', {})
        
        # 初始化 EasyOCR
        languages = self.ocr_config.get('languages', ['ch_sim', 'en'])
        gpu = self.ocr_config.get('gpu', True)
        
        logger.info(f"初始化 EasyOCR，语言: {languages}, GPU: {gpu}")
        self.reader = easyocr.Reader(languages, gpu=gpu, verbose=False, model_storage_directory='model/easyocr',
                                     download_enabled=False,)
        
        # 水印关键词
        self.watermark_keywords = self.ocr_config.get('watermark_keywords', [])
        
    def detect(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        检测图片中的水印位置
        
        Args:
            image: RGB 格式的图片数组
            
        Returns:
            水印区域列表 [(x1, y1, x2, y2), ...]
        """
        logger.info("开始检测水印...")
        
        # OCR 识别
        results = self._run_ocr(image)
        
        if not results:
            logger.warning("未检测到任何文字")
            return []
        
        logger.info(f"检测到 {len(results)} 个文字区域")
        
        # 过滤水印
        watermark_boxes = self._filter_watermarks(results, image.shape[:2])
        
        logger.info(f"识别到 {len(watermark_boxes)} 个水印区域")
        
        return watermark_boxes
    
    def _run_ocr(self, image: np.ndarray) -> List:
        """
        运行 OCR 识别
        
        Args:
            image: 图片数组
            
        Returns:
            OCR 结果列表
        """
        text_threshold = self.ocr_config.get('text_threshold', 0.7)
        link_threshold = self.ocr_config.get('link_threshold', 0.4)
        
        try:
            results = self.reader.readtext(
                image,
                text_threshold=text_threshold,
                link_threshold=link_threshold
            )
            return results
        except Exception as e:
            logger.error(f"OCR 识别失败: {e}")
            return []
    
    def _filter_watermarks(self, results: List, 
                          image_shape: Tuple[int, int]) -> List[Tuple[int, int, int, int]]:
        """
        过滤出水印区域
        
        Args:
            results: OCR 结果
            image_shape: 图片形状 (height, width)
            
        Returns:
            水印边界框列表
        """
        watermark_boxes = []
        min_confidence = self.ocr_config.get('min_confidence', 0.5)
        
        for bbox, text, confidence in results:
            # 置信度过滤
            if confidence < min_confidence:
                continue

            # 位置过滤
            box = self._bbox_to_box(bbox)
            if not self._is_watermark_position(box, image_shape):
                continue

            # 文字特征过滤
            if not self._is_watermark_text(text):
                continue

            # 特定水印扩展掩码区域
            if text.replace(" ", "").lower() == 'ai生成' or text.replace(" ", "").lower() == 'al生成':
                x1, y1, x2, y2 = box
                rectangle_x_buffer = self.ocr_config.get('rectangle_x_buffer', 30)
                rectangle_y_buffer = self.ocr_config.get('rectangle_y_buffer', 20)
                x1 = max(0, x1 - rectangle_x_buffer)
                y1 = max(0, y1 - rectangle_y_buffer)
                x2 = min(image_shape[1], x2 + rectangle_x_buffer)
                y2 = min(image_shape[0], y2 + rectangle_y_buffer)
                box = (x1, y1, x2, y2)

            elif '即' in text or '梦' in text:
                x1, y1, x2, y2 = box
                jimeng_x_buffer = self.ocr_config.get('jimeng_x_buffer', 50)
                jimeng_y_buffer = self.ocr_config.get('jimeng_y_buffer', 20)
                x1 = max(0, x1 - jimeng_x_buffer)
                y1 = max(0, y1 - jimeng_y_buffer)
                box = (x1, y1, x2, y2)

            
            logger.debug(f"检测到水印: '{text}' (置信度: {confidence:.2f})")
            watermark_boxes.append(box)
        
        return watermark_boxes
    
    def _is_watermark_text(self, text: str) -> bool:
        """
        判断文字是否为水印特征
        
        Args:
            text: 识别的文字
            
        Returns:
            是否为水印
        """
        text_filter = self.detection_config.get('text_filter', {})
        
        if not text_filter.get('enabled', True):
            return True
        
        # 长度过滤
        min_len = text_filter.get('min_text_length', 1)
        max_len = text_filter.get('max_text_length', 50)
        if not (min_len <= len(text) <= max_len):
            return False
        
        # 关键词匹配
        text_lower = text.lower()
        for keyword in self.watermark_keywords:
            if keyword.lower() in text_lower:
                return True
        
        # 如果没有配置关键词，默认认为是水印
        if not self.watermark_keywords:
            return True
        
        return False
    
    def _is_watermark_position(self, box: Tuple[int, int, int, int], 
                               image_shape: Tuple[int, int]) -> bool:
        """
        判断位置是否为水印典型位置
        
        Args:
            box: 边界框 (x1, y1, x2, y2)
            image_shape: 图片形状 (height, width)
            
        Returns:
            是否在水印典型位置
        """
        position_filter = self.detection_config.get('position_filter', {})
        
        if not position_filter.get('enabled', True):
            return True
        
        areas = position_filter.get('areas', ['corners', 'edges'])
        if 'all' in areas:
            return True
        
        h, w = image_shape
        x1, y1, x2, y2 = box
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        corner_ratio = position_filter.get('corner_ratio', 0.3)
        edge_ratio = position_filter.get('edge_ratio', 0.2)
        customize_y = position_filter.get('customize_y', 0.78)
        customize_ratio = position_filter.get('customize_ratio', 0.2)

        
        # 检查是否在角落
        if 'corners' in areas:
            corner_w = int(w * corner_ratio)
            corner_h = int(h * corner_ratio)
            
            if ((center_x < corner_w or center_x > w - corner_w) and
                (center_y < corner_h or center_y > h - corner_h)):
                return True
        
        # 检查是否在边缘
        if 'edges' in areas:
            edge_w = int(w * edge_ratio)
            edge_h = int(h * edge_ratio)
            
            if (center_x < edge_w or center_x > w - edge_w or
                center_y < edge_h or center_y > h - edge_h):
                return True
        
        # 检查是否在中心
        if 'center' in areas:
            center_w = int(w * 0.3)
            center_h = int(h * 0.3)
            
            if (w // 2 - center_w < center_x < w // 2 + center_w and
                h // 2 - center_h < center_y < h // 2 + center_h):
                return True

        # 检查自定义区域
        if 'customize' in areas:
            center_w = int(w * customize_ratio)
            center_h = int(h *customize_ratio)
            ref_x = w // 2
            ref_y = int(h*customize_y)

            if (ref_x - center_w < center_x < ref_x + center_w and
                    ref_y - center_h < center_y < ref_y + center_h):
                return True


        return False
    
    @staticmethod
    def _bbox_to_box(bbox: List) -> Tuple[int, int, int, int]:
        """
        将 OCR 的 bbox 转换为标准格式
        
        Args:
            bbox: OCR 返回的边界框 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            
        Returns:
            (x1, y1, x2, y2) 格式的边界框
        """
        points = np.array(bbox)
        x1 = int(points[:, 0].min())
        y1 = int(points[:, 1].min())
        x2 = int(points[:, 0].max())
        y2 = int(points[:, 1].max())
        return (x1, y1, x2, y2)
    
    def get_detection_info(self, image: np.ndarray) -> List[Dict]:
        """
        获取详细的检测信息（用于调试）
        
        Args:
            image: 图片数组
            
        Returns:
            检测信息列表
        """
        results = self._run_ocr(image)
        info_list = []
        
        for bbox, text, confidence in results:
            box = self._bbox_to_box(bbox)
            is_watermark = self._is_watermark_text(text) and \
                          self._is_watermark_position(box, image.shape[:2])
            
            info_list.append({
                'text': text,
                'confidence': confidence,
                'box': box,
                'is_watermark': is_watermark
            })
        
        return info_list
