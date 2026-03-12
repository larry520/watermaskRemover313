"""
视频去水印模块
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Union, Optional, Callable, Tuple
from loguru import logger
from tqdm import tqdm
import tempfile
import shutil

try:
    from moviepy import VideoFileClip, AudioFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logger.warning("MoviePy 未安装，音频处理功能不可用")


class VideoProcessor:
    """视频去水印处理器"""
    
    def __init__(self, watermark_remover, config: dict = None):
        """
        初始化视频处理器
        
        Args:
            watermark_remover: WatermarkRemover 实例
            config: 视频处理配置
        """
        self.remover = watermark_remover
        self.config = config or {}
        self.video_config = self.config.get('video', {})
        
    def process_video(self, 
                     input_path: Union[str, Path],
                     output_path: Union[str, Path],
                     start_time: Optional[float] = None,
                     end_time: Optional[float] = None,
                     skip_frames: int = 1,
                     frame_by_frame: bool = True,
                     keep_audio: bool = True,
                     progress_callback: Optional[Callable] = None) -> dict:
        """
        处理视频去水印
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            skip_frames: 跳帧处理（1=全部处理，2=每2帧处理1帧）
            quality: 输出质量 ('high', 'medium', 'low')
            keep_audio: 是否保留音频
            progress_callback: 进度回调函数 callback(current, total, message)
            
        Returns:
            处理信息字典
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {input_path}")
        
        logger.info(f"开始处理视频: {input_path}")
        
        # 打开视频
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {input_path}")
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps
        
        logger.info(f"视频信息: {width}x{height} @ {fps:.2f}fps, {total_frames} 帧, {duration:.2f}秒")
        
        # 计算处理范围
        start_frame = int(start_time * fps) if start_time else 0
        end_frame = int(end_time * fps) if end_time else total_frames
        process_frames = end_frame - start_frame
        
        # 设置起始位置
        if start_frame > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # 创建临时视频文件（无音频）
        temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_video_path = Path(temp_video.name)
        temp_video.close()
        
        # 设置编码器
        fourcc = cv2.VideoWriter.fourcc(*'mp4v')
        out = cv2.VideoWriter(
            str(temp_video_path),
            fourcc,
            fps,
            (width, height)
        )

        # 使用第一帧水印掩码去水印
        if not frame_by_frame:
            # 检测水印位置（使用第一帧）
            ret, first_frame = cap.read()
            if not ret:
                raise ValueError("无法读取视频帧")

            first_frame_rgb = cv2.cvtColor(first_frame, cv2.COLOR_BGR2RGB)
            watermark_boxes = self.remover.detector.detect(first_frame_rgb)

            if watermark_boxes:
                logger.info(f"检测到 {len(watermark_boxes)} 个水印区域")
            else:
                logger.warning("未检测到水印，将输出原视频")

            # 生成 mask（只生成一次，假设水印位置固定）
            mask = self.remover.mask_generator.generate(first_frame_rgb, watermark_boxes)
            has_watermark = np.any(mask > 0)

            # 重置到起始帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            # 处理每一帧
            frame_count = 0
            processed_count = 0

            try:
                with tqdm(total=process_frames, desc="处理视频帧") as pbar:
                    while frame_count < process_frames:
                        ret, frame = cap.read()
                        if not ret:
                            break

                        # 跳帧处理
                        if frame_count % skip_frames == 0 and has_watermark:
                            # 去水印
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            result_rgb = self.remover.inpainter.inpaint(frame_rgb, mask)
                            result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
                            out.write(result_bgr)
                            processed_count += 1
                        else:
                            # 直接写入原帧
                            out.write(frame)

                        frame_count += 1
                        pbar.update(1)

                        # 回调进度
                        if progress_callback:
                            progress_callback(frame_count, process_frames,
                                              f"处理中: {frame_count}/{process_frames}")
            finally:
                cap.release()
                out.release()

        # 帧去水印
        else:
            # 重置到起始帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            # 处理每一帧
            frame_count = 0
            processed_count = 0

            try:
                with tqdm(total=process_frames, desc="处理视频帧") as pbar:
                    while frame_count < process_frames:
                        ret, frame = cap.read()
                        if not ret:
                            break

                        if frame_count % skip_frames == 0 :
                            # 去水印
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            detections = self.remover.detector.detect(frame_rgb)
                            if not detections:
                                # 直接写入原帧
                                out.write(frame)
                            else:
                                mask = self.remover.mask_generator.generate(frame_rgb, detections)
                                result_rgb = self.remover.inpainter.inpaint(frame_rgb, mask)
                                result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
                                out.write(result_bgr)
                                processed_count += 1

                        frame_count += 1
                        pbar.update(1)

                        # 回调进度
                        if progress_callback:
                            progress_callback(frame_count, process_frames,
                                              f"处理中: {frame_count}/{process_frames}")

            finally:
                cap.release()
                out.release()
        
        logger.info(f"视频帧处理完成: {processed_count}/{frame_count} 帧已去水印")
        
        # 处理音频
        if keep_audio and MOVIEPY_AVAILABLE:
            logger.info("合并音频...")
            self._merge_audio(input_path, temp_video_path, output_path, 
                            start_time, end_time)
            temp_video_path.unlink()
        else:
            # 直接使用无音频视频
            shutil.move(str(temp_video_path), str(output_path))
            if keep_audio and not MOVIEPY_AVAILABLE:
                logger.warning("MoviePy 未安装，无法保留音频")
        
        logger.info(f"视频处理完成: {output_path}")
        
        return {
            'input_path': str(input_path),
            'output_path': str(output_path),
            'total_frames': frame_count,
            'processed_frames': processed_count,
            'watermark_detected': has_watermark,
            'duration': frame_count / fps,
            'fps': fps,
            'resolution': f"{width}x{height}"
        }
    
    def process_video_adaptive(self,
                              input_path: Union[str, Path],
                              output_path: Union[str, Path],
                              detection_interval: int = 30,
                              **kwargs) -> dict:
        """
        自适应处理视频（定期重新检测水印位置）
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            detection_interval: 重新检测间隔（帧数）
            **kwargs: 其他参数传递给 process_video
            
        Returns:
            处理信息字典
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        logger.info(f"开始自适应处理视频: {input_path}")
        
        # 打开视频
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {input_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 设置编码器
        quality = kwargs.get('quality', 'high')
        codec, bitrate = self._get_codec_settings(quality)
        fourcc = cv2.VideoWriter.fourcc(*codec)
        
        temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_video_path = Path(temp_video.name)
        temp_video.close()
        
        out = cv2.VideoWriter(
            str(temp_video_path),
            fourcc,
            fps,
            (width, height)
        )
        
        frame_count = 0
        processed_count = 0
        current_mask = None
        
        try:
            with tqdm(total=total_frames, desc="自适应处理") as pbar:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # 定期重新检测水印
                    if frame_count % detection_interval == 0:
                        logger.debug(f"重新检测水印 (帧 {frame_count})")
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        watermark_boxes = self.remover.detector.detect(frame_rgb)
                        current_mask = self.remover.mask_generator.generate(
                            frame_rgb, watermark_boxes
                        )
                    
                    # 处理帧
                    if current_mask is not None and np.any(current_mask > 0):
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        result_rgb = self.remover.inpainter.inpaint(frame_rgb, current_mask)
                        result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
                        out.write(result_bgr)
                        processed_count += 1
                    else:
                        out.write(frame)
                    
                    frame_count += 1
                    pbar.update(1)
        
        finally:
            cap.release()
            out.release()
        
        logger.info(f"自适应处理完成: {processed_count}/{frame_count} 帧已去水印")
        
        # 处理音频
        keep_audio = kwargs.get('keep_audio', True)
        if keep_audio and MOVIEPY_AVAILABLE:
            logger.info("合并音频...")
            self._merge_audio(input_path, temp_video_path, output_path)
            temp_video_path.unlink()
        else:
            shutil.move(str(temp_video_path), str(output_path))
        
        return {
            'input_path': str(input_path),
            'output_path': str(output_path),
            'total_frames': frame_count,
            'processed_frames': processed_count,
            'detection_interval': detection_interval
        }
    
    def extract_frames(self,
                      video_path: Union[str, Path],
                      output_dir: Union[str, Path],
                      interval: int = 1,
                      max_frames: Optional[int] = None) -> list:
        """
        提取视频帧
        
        Args:
            video_path: 视频路径
            output_dir: 输出目录
            interval: 提取间隔（帧）
            max_frames: 最大提取帧数
            
        Returns:
            提取的图片路径列表
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cap = cv2.VideoCapture(str(video_path))
        frame_count = 0
        extracted_count = 0
        extracted_files = []
        
        logger.info(f"开始提取视频帧: {video_path}")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % interval == 0:
                    output_file = output_dir / f"frame_{frame_count:06d}.jpg"
                    cv2.imwrite(str(output_file), frame)
                    extracted_files.append(str(output_file))
                    extracted_count += 1
                    
                    if max_frames and extracted_count >= max_frames:
                        break
                
                frame_count += 1
        
        finally:
            cap.release()
        
        logger.info(f"提取完成: {extracted_count} 帧")
        return extracted_files
    
    def _merge_audio(self,
                    original_video: Path,
                    processed_video: Path,
                    output_video: Path,
                    start_time: Optional[float] = None,
                    end_time: Optional[float] = None):
        """
        合并音频到处理后的视频
        
        Args:
            original_video: 原始视频路径
            processed_video: 处理后的视频路径（无音频）
            output_video: 输出视频路径
            start_time: 音频开始时间
            end_time: 音频结束时间
        """
        if not MOVIEPY_AVAILABLE:
            logger.warning("MoviePy 未安装，跳过音频合并")
            shutil.copy(processed_video, output_video)
            return
        
        try:
            # 加载视频和音频
            video = VideoFileClip(str(processed_video))
            original_audio = AudioFileClip(str(original_video))

            # 提取音频
            if original_audio is not None:
                audio = original_audio
                
                # # 裁剪音频
                # if start_time is not None or end_time is not None:
                #     start = start_time or 0
                #     end = end_time or audio.duration
                #     audio = audio.subclip(start, end)
                
                # 合并
                final_video = video.with_audio(audio)
                final_video.write_videofile(
                    str(output_video),
                    codec='libx264',
                    audio_codec='aac',
                    logger=None
                )
                
                # 清理
                final_video.close()
            else:
                logger.warning("原视频没有音频轨道")
                shutil.copy(processed_video, output_video)
            
            video.close()
            original_audio.close()
            
        except Exception as e:
            logger.error(f"音频合并失败: {e}")
            shutil.copy(processed_video, output_video)
    
    def _get_codec_settings(self, quality: str) -> Tuple[str, int]:
        """
        获取编码器设置
        
        Args:
            quality: 质量等级
            
        Returns:
            (codec, bitrate)
        """
        settings = {
            'high': ('mp4v', 5000),
            'medium': ('mp4v', 2500),
            'low': ('mp4v', 1000)
        }
        return settings.get(quality, settings['high'])
    
    def get_video_info(self, video_path: Union[str, Path]) -> dict:
        """
        获取视频信息
        
        Args:
            video_path: 视频路径
            
        Returns:
            视频信息字典
        """
        video_path = Path(video_path)
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        info = {
            'path': str(video_path),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'codec': int(cap.get(cv2.CAP_PROP_FOURCC)),
        }
        
        info['duration'] = info['total_frames'] / info['fps']
        info['resolution'] = f"{info['width']}x{info['height']}"
        
        cap.release()
        
        return info
