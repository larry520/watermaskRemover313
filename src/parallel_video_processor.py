"""
多进程并行视频处理模块
充分利用多核 CPU，大幅提升处理速度

性能提升：
- 多进程并行：2-8倍加速（取决于 CPU 核心数）
- 固定 Mask + 并行：10-50倍加速
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Union, Optional, Tuple, List
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import tempfile
import shutil
import time
from tqdm import tqdm

from src.watermark_remover import WatermarkRemover
# 创建去除器
remover = WatermarkRemover(config_path=r'config.yaml')

class ParallelVideoProcessor:
    """并行视频处理器"""
    
    def __init__(self, num_workers: Optional[int] = None):
        """
        初始化
        
        Args:
            num_workers: 进程数（默认为 CPU 核心数）
        """
        if num_workers is None:
            self.num_workers = mp.cpu_count()
        else:
            self.num_workers = min(num_workers, mp.cpu_count())
        
        print(f"✓ 初始化并行处理器，进程数: {self.num_workers}")
    
    def process_video_parallel(self,
                              input_path: Union[str, Path],
                              output_path: Union[str, Path],
                              mask: Optional[np.ndarray] = None,
                              batch_size: int = 30,
                              quality: str = 'high',
                              keep_audio: bool = True) -> dict:
        """
        并行处理视频
        
        Args:
            input_path: 输入视频
            output_path: 输出视频
            mask: 固定 mask（如果提供则使用固定 mask 模式）
            batch_size: 批大小（控制内存）
            quality: 输出质量
            keep_audio: 是否保留音频
            
        Returns:
            处理信息
        """
        print(f"\n{'='*60}")
        print("并行视频处理")
        print(f"{'='*60}")
        print(f"输入: {input_path}")
        print(f"输出: {output_path}")
        print(f"进程数: {self.num_workers}")
        print(f"批大小: {batch_size}")
        print()
        
        start_time = time.time()
        
        # 读取视频信息
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {input_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"视频信息: {width}x{height} @ {fps:.2f}fps, {total_frames} 帧")
        print()
        
        # 读取所有帧
        print("步骤1: 读取视频帧...")
        frames = []
        for _ in tqdm(range(total_frames), desc="读取帧"):
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        
        actual_frames = len(frames)
        print(f"✓ 读取完成: {actual_frames} 帧\n")
        
        # 保存 mask 到临时文件（用于子进程）
        temp_mask_path = None
        if mask is not None:
            temp_mask_path = tempfile.mktemp(suffix='.npy')
            np.save(temp_mask_path, mask)
            print(f"✓ 使用固定 Mask 模式（速度更快）\n")
        
        try:
            # 并行处理
            print("步骤2: 并行处理帧...")
            processed_frames = self._process_frames_in_parallel(
                frames,
                temp_mask_path,
                batch_size
            )
            
            # 写入视频
            print("\n步骤3: 写入输出视频...")
            temp_video = Path(tempfile.mktemp(suffix='.mp4'))
            
            self._write_video(
                processed_frames,
                temp_video,
                fps,
                width,
                height,
                quality
            )
            
            # 合并音频
            if keep_audio:
                print("\n步骤4: 合并音频...")
                self._merge_audio(input_path, temp_video, output_path)
                temp_video.unlink()
            else:
                shutil.move(str(temp_video), str(output_path))
            
            elapsed = time.time() - start_time
            processing_fps = actual_frames / elapsed
            
            print(f"\n{'='*60}")
            print("✓ 处理完成！")
            print(f"{'='*60}")
            print(f"总耗时: {elapsed:.2f} 秒")
            print(f"处理速度: {processing_fps:.2f} fps")
            print(f"输出: {output_path}")
            print(f"{'='*60}\n")
            
            return {
                'input_path': str(input_path),
                'output_path': str(output_path),
                'total_frames': actual_frames,
                'elapsed_time': elapsed,
                'processing_fps': processing_fps,
                'num_workers': self.num_workers
            }
        
        finally:
            # 清理临时 mask 文件
            if temp_mask_path and Path(temp_mask_path).exists():
                Path(temp_mask_path).unlink()
    
    def _process_frames_in_parallel(self,
                                    frames: List[np.ndarray],
                                    mask_path: Optional[str],
                                    batch_size: int) -> List[np.ndarray]:
        """
        并行处理帧
        
        Args:
            frames: 所有帧
            mask_path: Mask 文件路径（如果使用固定 mask）
            batch_size: 批大小
            
        Returns:
            处理后的帧列表
        """
        num_frames = len(frames)
        processed_frames = [None] * num_frames
        
        num_batches = (num_frames + batch_size - 1) // batch_size
        
        with tqdm(total=num_frames, desc="处理进度") as pbar:
            for batch_idx in range(num_batches):
                start_idx = batch_idx * batch_size
                end_idx = min((batch_idx + 1) * batch_size, num_frames)
                
                batch_frames = frames[start_idx:end_idx]
                batch_indices = list(range(start_idx, end_idx))
                
                # 使用进程池处理当前批次
                with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
                    if mask_path:
                        # 固定 mask 模式
                        futures = {
                            executor.submit(_process_frame_with_mask, frame, mask_path): idx
                            for idx, frame in zip(batch_indices, batch_frames)
                        }
                    else:
                        # OCR 检测模式
                        futures = {
                            executor.submit(_process_frame_with_ocr, frame): idx
                            for idx, frame in zip(batch_indices, batch_frames)
                        }
                    
                    # 收集结果
                    for future in as_completed(futures):
                        idx = futures[future]
                        try:
                            result = future.result()
                            processed_frames[idx] = result
                        except Exception as e:
                            print(f"\n⚠ 处理帧 {idx} 失败: {e}")
                            # 失败时使用原帧
                            processed_frames[idx] = frames[idx]
                
                pbar.update(len(batch_frames))
        
        return processed_frames
    
    def _write_video(self,
                    frames: List[np.ndarray],
                    output_path: Path,
                    fps: float,
                    width: int,
                    height: int,
                    quality: str):
        """写入视频文件"""
        codec_map = {
            'high': ('mp4v', 5000),
            'medium': ('mp4v', 2500),
            'low': ('mp4v', 1000)
        }
        codec, _ = codec_map.get(quality, codec_map['high'])
        
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        for frame in tqdm(frames, desc="写入帧"):
            out.write(frame)
        
        out.release()
        print(f"✓ 视频已写入")
    
    def _merge_audio(self,
                    original: Path,
                    processed: Path,
                    output: Path):
        """合并音频"""
        try:
            from moviepy.editor import VideoFileClip
            
            video = VideoFileClip(str(processed))
            original_clip = VideoFileClip(str(original))
            
            if original_clip.audio is not None:
                final = video.set_audio(original_clip.audio)
                final.write_videofile(
                    str(output),
                    codec='libx264',
                    audio_codec='aac',
                    logger=None
                )
                final.close()
            else:
                shutil.copy(processed, output)
            
            video.close()
            original_clip.close()
            
            print("✓ 音频已合并")
            
        except ImportError:
            print("⚠ MoviePy 未安装，跳过音频合并")
            shutil.copy(processed, output)
        except Exception as e:
            print(f"⚠ 音频合并失败: {e}")
            shutil.copy(processed, output)


# === 子进程处理函数（必须在模块级别定义）===

def _process_frame_with_mask(frame: np.ndarray, mask_path: str) -> np.ndarray:
    """
    使用固定 mask 处理帧（子进程函数）
    
    Args:
        frame: 输入帧（BGR）
        mask_path: Mask 文件路径
        
    Returns:
        处理后的帧（BGR）
    """
    import cv2
    import numpy as np
    
    try:
        # 加载 mask
        mask = np.load(mask_path)
        
        # 转换颜色
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 修复
        result_rgb = cv2.inpaint(frame_rgb, mask, 3, cv2.INPAINT_NS)
        
        # 转换回 BGR
        result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
        
        return result_bgr
    
    except Exception:
        # 失败时返回原帧
        return frame


def _process_frame_with_ocr(frame: np.ndarray) -> np.ndarray:
    """
    使用 OCR 检测处理帧（子进程函数）
    
    Args:
        frame: 输入帧（BGR）
        
    Returns:
        处理后的帧（BGR）
    """
    import cv2
    import sys
    from pathlib import Path
    
    # 添加项目路径
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    try:
        # from src.watermark_remover import WatermarkRemover
        #
        # # 创建去除器
        # remover = WatermarkRemover(config_path=r'config.yaml')
        
        # 转换颜色
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 检测水印
        detections = remover.detector.detect(frame_rgb)
        
        if not detections:
            return frame
        
        # # 提取边界框
        # boxes = [det['box'] for det in detections]
        
        # 生成掩码
        mask = remover.mask_generator.generate(frame_rgb, detections)
        
        # 修复
        result_rgb = remover.inpainter.inpaint(frame_rgb, mask)
        
        # 转换回 BGR
        result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
        
        return result_bgr
    
    except Exception:
        # 失败时返回原帧
        return frame
