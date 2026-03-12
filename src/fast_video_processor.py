"""
快速视频去水印模块 - 使用固定 Mask
适用于水印位置固定的视频（90%以上的场景）
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Union, Optional, Tuple
from loguru import logger
from tqdm import tqdm
import tempfile
import shutil

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logger.warning("MoviePy 未安装，音频功能不可用")


class FastVideoProcessor:
    """快速视频处理器 - 使用固定 Mask"""
    
    def __init__(self, watermark_remover):
        """
        初始化快速处理器
        
        Args:
            watermark_remover: WatermarkRemover 实例
        """
        self.remover = watermark_remover
        self.fixed_mask = None
        
    def process_video_with_fixed_mask(self,
                                     input_path: Union[str, Path],
                                     output_path: Union[str, Path],
                                     mask: Optional[np.ndarray] = None,
                                     detect_from_first_frame: bool = True,
                                     manual_box: Optional[Tuple[int, int, int, int]] = None,
                                     quality: str = 'high',
                                     keep_audio: bool = True) -> dict:
        """
        使用固定 Mask 快速处理视频
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            mask: 预先提供的 mask（如果提供则直接使用）
            detect_from_first_frame: 是否从第一帧检测生成 mask
            manual_box: 手动指定水印区域 (x1, y1, x2, y2)
            quality: 输出质量
            keep_audio: 是否保留音频
            
        Returns:
            处理信息字典
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        logger.info(f"快速处理视频: {input_path}")
        
        # 打开视频
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {input_path}")
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(f"视频: {width}x{height} @ {fps:.2f}fps, {total_frames} 帧")
        
        # 1. 获取或生成 Mask
        if mask is not None:
            logger.info("使用提供的 mask")
            self.fixed_mask = mask
        elif manual_box is not None:
            logger.info(f"使用手动区域生成 mask: {manual_box}")
            self.fixed_mask = self._create_mask_from_box(
                (height, width), manual_box
            )
        elif detect_from_first_frame:
            logger.info("从第一帧检测生成 mask...")
            ret, first_frame = cap.read()
            if not ret:
                raise ValueError("无法读取第一帧")
            self.fixed_mask = self._detect_mask_from_frame(first_frame)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 重置
        else:
            raise ValueError("必须提供 mask、manual_box 或启用 detect_from_first_frame")
        
        # 保存 mask 用于检查
        mask_path = output_path.parent / f"{output_path.stem}_mask.png"
        cv2.imwrite(str(mask_path), self.fixed_mask)
        logger.info(f"Mask 已保存: {mask_path}")
        
        # 2. 创建临时视频文件
        temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_video_path = Path(temp_video.name)
        temp_video.close()
        
        # 设置编码器
        codec, bitrate = self._get_codec_settings(quality)
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(
            str(temp_video_path),
            fourcc,
            fps,
            (width, height)
        )
        
        # 3. 逐帧处理（使用固定 mask）
        logger.info("开始处理视频帧...")
        frame_count = 0
        
        try:
            with tqdm(total=total_frames, desc="处理进度") as pbar:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # 使用固定 mask 修复
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    result_rgb = self.remover.inpainter.inpaint(
                        frame_rgb, self.fixed_mask
                    )
                    result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
                    
                    out.write(result_bgr)
                    frame_count += 1
                    pbar.update(1)
        
        finally:
            cap.release()
            out.release()
        
        logger.info(f"处理完成: {frame_count} 帧")
        
        # 4. 合并音频
        if keep_audio and MOVIEPY_AVAILABLE:
            logger.info("合并音频...")
            self._merge_audio(input_path, temp_video_path, output_path)
            temp_video_path.unlink()
        else:
            shutil.move(str(temp_video_path), str(output_path))
        
        logger.info(f"视频已保存: {output_path}")
        
        return {
            'input_path': str(input_path),
            'output_path': str(output_path),
            'total_frames': frame_count,
            'fps': fps,
            'resolution': f"{width}x{height}",
            'mask_path': str(mask_path)
        }
    
    def _detect_mask_from_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        从单帧检测生成 mask
        
        Args:
            frame: 输入帧（BGR 格式）
            
        Returns:
            生成的 mask
        """
        # 转换为 RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 检测水印
        watermark_boxes = self.remover.detector.detect(frame_rgb)
        
        if not watermark_boxes:
            logger.warning("未检测到水印，返回空 mask")
            return np.zeros(frame.shape[:2], dtype=np.uint8)
        
        logger.info(f"检测到 {len(watermark_boxes)} 个水印区域")
        
        # 生成 mask（额外扩展）
        mask = self.remover.mask_generator.generate_with_expansion(
            frame_rgb,
            watermark_boxes,
            expand_pixels=20  # 额外扩展确保覆盖完全
        )
        
        return mask
    
    def _create_mask_from_box(self, 
                             image_shape: Tuple[int, int],
                             box: Tuple[int, int, int, int]) -> np.ndarray:
        """
        从边界框创建 mask
        
        Args:
            image_shape: 图像尺寸 (height, width)
            box: 边界框 (x1, y1, x2, y2)
            
        Returns:
            生成的 mask
        """
        h, w = image_shape
        mask = np.zeros((h, w), dtype=np.uint8)
        
        x1, y1, x2, y2 = box
        cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
        
        # 膨胀和模糊
        kernel = np.ones((7, 7), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        return mask
    
    def save_mask(self, output_path: Union[str, Path]):
        """
        保存当前 mask
        
        Args:
            output_path: 输出路径
        """
        if self.fixed_mask is None:
            logger.warning("没有可用的 mask")
            return
        
        cv2.imwrite(str(output_path), self.fixed_mask)
        logger.info(f"Mask 已保存: {output_path}")
    
    def load_mask(self, mask_path: Union[str, Path]):
        """
        加载预先生成的 mask
        
        Args:
            mask_path: mask 文件路径
        """
        mask_path = Path(mask_path)
        if not mask_path.exists():
            raise FileNotFoundError(f"Mask 文件不存在: {mask_path}")
        
        self.fixed_mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        logger.info(f"Mask 已加载: {mask_path}")
    
    def preview_mask_on_frame(self, 
                             video_path: Union[str, Path],
                             output_path: Union[str, Path],
                             frame_number: int = 0) -> np.ndarray:
        """
        在指定帧上预览 mask 效果
        
        Args:
            video_path: 视频路径
            output_path: 输出图片路径
            frame_number: 帧号
            
        Returns:
            预览图片
        """
        if self.fixed_mask is None:
            raise ValueError("没有可用的 mask，请先生成或加载")
        
        # 读取指定帧
        cap = cv2.VideoCapture(str(video_path))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise ValueError(f"无法读取帧 {frame_number}")
        
        # 叠加 mask
        mask_vis = cv2.cvtColor(self.fixed_mask, cv2.COLOR_GRAY2BGR)
        preview = cv2.addWeighted(frame, 0.7, mask_vis, 0.3, 0)
        
        # 保存
        cv2.imwrite(str(output_path), preview)
        logger.info(f"预览已保存: {output_path}")
        
        return preview
    
    def _merge_audio(self,
                    original_video: Path,
                    processed_video: Path,
                    output_video: Path):
        """合并音频"""
        if not MOVIEPY_AVAILABLE:
            logger.warning("MoviePy 未安装，跳过音频合并")
            shutil.copy(processed_video, output_video)
            return
        
        try:
            video = VideoFileClip(str(processed_video))
            original = VideoFileClip(str(original_video))
            
            if original.audio is not None:
                final_video = video.set_audio(original.audio)
                final_video.write_videofile(
                    str(output_video),
                    codec='libx264',
                    audio_codec='aac',
                    logger=None
                )
                final_video.close()
            else:
                shutil.copy(processed_video, output_video)
            
            video.close()
            original.close()
            
        except Exception as e:
            logger.error(f"音频合并失败: {e}")
            shutil.copy(processed_video, output_video)
    
    def _get_codec_settings(self, quality: str) -> Tuple[str, int]:
        """获取编码器设置"""
        settings = {
            'high': ('mp4v', 5000),
            'medium': ('mp4v', 2500),
            'low': ('mp4v', 1000)
        }
        return settings.get(quality, settings['high'])
    
    def batch_process_with_same_mask(self,
                                    video_paths: list,
                                    output_dir: Union[str, Path],
                                    mask: Optional[np.ndarray] = None,
                                    manual_box: Optional[Tuple] = None) -> list:
        """
        使用相同 mask 批量处理多个视频
        
        Args:
            video_paths: 视频路径列表
            output_dir: 输出目录
            mask: 固定 mask（可选）
            manual_box: 手动区域（可选）
            
        Returns:
            处理结果列表
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 如果没有提供 mask，从第一个视频生成
        if mask is None and self.fixed_mask is None:
            if manual_box is None:
                logger.info("从第一个视频生成 mask...")
                cap = cv2.VideoCapture(str(video_paths[0]))
                ret, first_frame = cap.read()
                cap.release()
                
                if ret:
                    self.fixed_mask = self._detect_mask_from_frame(first_frame)
                else:
                    raise ValueError("无法从第一个视频生成 mask")
            else:
                # 从手动区域生成
                cap = cv2.VideoCapture(str(video_paths[0]))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                cap.release()
                
                self.fixed_mask = self._create_mask_from_box((h, w), manual_box)
        elif mask is not None:
            self.fixed_mask = mask
        
        # 批量处理
        results = []
        for i, video_path in enumerate(video_paths, 1):
            logger.info(f"处理 [{i}/{len(video_paths)}]: {video_path}")
            
            video_path = Path(video_path)
            output_path = output_dir / video_path.name
            
            try:
                result = self.process_video_with_fixed_mask(
                    video_path,
                    output_path,
                    mask=self.fixed_mask,
                    detect_from_first_frame=False  # 使用已有 mask
                )
                results.append(result)
            except Exception as e:
                logger.error(f"处理失败: {video_path.name}, 错误: {e}")
        
        logger.info(f"批量处理完成: {len(results)}/{len(video_paths)}")
        return results
