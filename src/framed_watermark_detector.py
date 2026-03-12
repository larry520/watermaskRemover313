"""
带边框水印的增强检测模块
专门处理带矩形框的水印（如 AI生成、版权声明等）
"""
import cv2
import numpy as np
from typing import List, Tuple, Optional
from loguru import logger


class FramedWatermarkDetector:
    """检测带矩形框的水印"""
    
    def __init__(self, config: dict = None):
        """
        初始化增强检测器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
    def detect_frames(self, image: np.ndarray, 
                     text_boxes: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """
        检测水印周围的矩形框并扩展检测区域
        
        Args:
            image: 输入图片（BGR 格式）
            text_boxes: OCR 检测到的文字边界框列表
            
        Returns:
            扩展后的边界框列表（包含矩形框）
        """
        if not text_boxes:
            return []
        
        logger.info(f"检测到 {len(text_boxes)} 个文字区域，开始检测矩形框")
        
        enhanced_boxes = []
        
        for box in text_boxes:
            # 方法1: 扩展文字区域
            expanded_box = self._expand_for_frame(box, image.shape[:2])
            
            # 方法2: 检测边缘
            frame_box = self._detect_frame_by_edge(image, box)
            
            # 选择更大的区域
            if frame_box is not None:
                final_box = self._merge_boxes([expanded_box, frame_box])
            else:
                final_box = expanded_box
            
            enhanced_boxes.append(final_box)
            logger.debug(f"原始框: {box}, 增强框: {final_box}")
        
        return enhanced_boxes
    
    def _expand_for_frame(self, box: Tuple[int, int, int, int], 
                         image_shape: Tuple[int, int],
                         padding: int = 20) -> Tuple[int, int, int, int]:
        """
        扩展边界框以包含可能的矩形框
        
        Args:
            box: 原始边界框 (x1, y1, x2, y2)
            image_shape: 图片尺寸 (height, width)
            padding: 扩展像素数
            
        Returns:
            扩展后的边界框
        """
        x1, y1, x2, y2 = box
        h, w = image_shape
        
        # 向四周扩展
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        
        return (x1, y1, x2, y2)
    
    def _detect_frame_by_edge(self, image: np.ndarray,
                             text_box: Tuple[int, int, int, int],
                             search_margin: int = 50) -> Optional[Tuple[int, int, int, int]]:
        """
        通过边缘检测寻找矩形框
        
        Args:
            image: 输入图片
            text_box: 文字边界框
            search_margin: 搜索边距
            
        Returns:
            检测到的矩形框边界，如果未检测到返回 None
        """
        x1, y1, x2, y2 = text_box
        h, w = image.shape[:2]
        
        # 扩展搜索区域
        search_x1 = max(0, x1 - search_margin)
        search_y1 = max(0, y1 - search_margin)
        search_x2 = min(w, x2 + search_margin)
        search_y2 = min(h, y2 + search_margin)
        
        # 提取搜索区域
        roi = image[search_y1:search_y2, search_x1:search_x2]
        
        # 转灰度
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi
        
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # 寻找最可能的矩形框
        for contour in sorted(contours, key=cv2.contourArea, reverse=True):
            # 近似为多边形
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # 如果是四边形
            if len(approx) == 4:
                x, y, w_rect, h_rect = cv2.boundingRect(contour)
                
                # 转换回原图坐标
                frame_x1 = search_x1 + x
                frame_y1 = search_y1 + y
                frame_x2 = frame_x1 + w_rect
                frame_y2 = frame_y1 + h_rect
                
                # 检查是否包含文字框
                if (frame_x1 <= x1 and frame_y1 <= y1 and 
                    frame_x2 >= x2 and frame_y2 >= y2):
                    return (frame_x1, frame_y1, frame_x2, frame_y2)
        
        return None
    
    def _merge_boxes(self, boxes: List[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
        """
        合并多个边界框为一个
        
        Args:
            boxes: 边界框列表
            
        Returns:
            合并后的边界框
        """
        x1 = min(box[0] for box in boxes)
        y1 = min(box[1] for box in boxes)
        x2 = max(box[2] for box in boxes)
        y2 = max(box[3] for box in boxes)
        
        return (x1, y1, x2, y2)
    
    def detect_by_color(self, image: np.ndarray,
                       text_boxes: List[Tuple[int, int, int, int]],
                       color_range: Tuple[Tuple[int, int, int], Tuple[int, int, int]] = None
                       ) -> List[Tuple[int, int, int, int]]:
        """
        通过颜色检测水印区域（适用于特定颜色的矩形框）
        
        Args:
            image: 输入图片
            text_boxes: 文字边界框
            color_range: 颜色范围 ((B_min, G_min, R_min), (B_max, G_max, R_max))
            
        Returns:
            检测到的边界框
        """
        if color_range is None:
            # 默认检测白色/浅色矩形框
            color_range = ((200, 200, 200), (255, 255, 255))
        
        lower, upper = color_range
        
        # 颜色掩码
        mask = cv2.inRange(image, np.array(lower), np.array(upper))
        
        # 形态学操作
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        enhanced_boxes = []
        
        for text_box in text_boxes:
            x1, y1, x2, y2 = text_box
            text_center = ((x1 + x2) // 2, (y1 + y2) // 2)
            
            # 寻找包含文字中心的轮廓
            best_box = text_box
            max_area = 0
            
            for contour in contours:
                if cv2.contourArea(contour) > max_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    if (x <= text_center[0] <= x + w and 
                        y <= text_center[1] <= y + h):
                        best_box = (x, y, x + w, y + h)
                        max_area = cv2.contourArea(contour)
            
            enhanced_boxes.append(best_box)
        
        return enhanced_boxes
    
    def visualize_detection(self, image: np.ndarray,
                          original_boxes: List[Tuple[int, int, int, int]],
                          enhanced_boxes: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """
        可视化检测结果
        
        Args:
            image: 原图
            original_boxes: 原始文字框
            enhanced_boxes: 增强后的框
            
        Returns:
            可视化图片
        """
        vis = image.copy()
        
        # 绘制原始文字框（绿色）
        for box in original_boxes:
            x1, y1, x2, y2 = box
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(vis, "Text", (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # 绘制增强框（红色）
        for box in enhanced_boxes:
            x1, y1, x2, y2 = box
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(vis, "Enhanced", (x1, y1 + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        return vis
