"""
视频去水印使用示例
"""
from src.watermark_remover import WatermarkRemover
from src.video_processor import VideoProcessor
from pathlib import Path


def example_1_basic_video():
    """示例1: 基本视频处理"""
    print("=== 示例1: 基本视频处理 ===\n")
    
    # 初始化
    remover = WatermarkRemover(config_path='config.yaml')
    processor = VideoProcessor(remover)
    
    # 处理视频
    result = processor.process_video(
        input_path=r"D:\projects\watermask\video\raw.mp4",
        output_path="output_video.mp4",
        keep_audio=True
    )
    
    print(f"处理完成!")
    print(f"处理帧数: {result['processed_frames']}/{result['total_frames']}")


def example_2_video_clip():
    """示例2: 处理视频片段"""
    print("=== 示例2: 处理视频片段 ===\n")
    
    remover = WatermarkRemover()
    processor = VideoProcessor(remover)
    
    # 只处理 10-30 秒的片段
    result = processor.process_video(
        input_path="input_video.mp4",
        output_path="output_clip.mp4",
        start_time=10.0,  # 从第 10 秒开始
        end_time=30.0,    # 到第 30 秒结束
        keep_audio=True
    )
    
    print(f"片段处理完成!")
    print()


def example_3_skip_frames():
    """示例3: 跳帧处理（提速）"""
    print("=== 示例3: 跳帧处理 ===\n")
    
    remover = WatermarkRemover()
    processor = VideoProcessor(remover)
    
    # 每 2 帧处理 1 帧（速度提升 2 倍）
    result = processor.process_video(
        input_path="input_video.mp4",
        output_path="output_fast.mp4",
        skip_frames=2,  # 跳帧处理
        quality='medium'  # 降低质量以进一步提速
    )
    
    print(f"快速处理完成!")
    print()


def example_4_adaptive_detection():
    """示例4: 自适应检测（水印位置变化的视频）"""
    print("=== 示例4: 自适应检测 ===\n")
    
    remover = WatermarkRemover()
    processor = VideoProcessor(remover)
    
    # 每 30 帧重新检测一次水印位置
    result = processor.process_video_adaptive(
        input_path="input_video.mp4",
        output_path="output_adaptive.mp4",
        detection_interval=30,  # 每 30 帧检测一次
        quality='high'
    )
    
    print(f"自适应处理完成!")
    print()


def example_5_get_video_info():
    """示例5: 获取视频信息"""
    print("=== 示例5: 获取视频信息 ===\n")
    
    remover = WatermarkRemover()
    processor = VideoProcessor(remover)
    
    # 获取视频信息
    info = processor.get_video_info("input_video.mp4")
    
    print(f"视频信息:")
    print(f"  分辨率: {info['resolution']}")
    print(f"  帧率: {info['fps']:.2f} fps")
    print(f"  总帧数: {info['total_frames']}")
    print(f"  时长: {info['duration']:.2f} 秒")
    print()


def example_6_extract_frames():
    """示例6: 提取视频帧"""
    print("=== 示例6: 提取视频帧 ===\n")
    
    remover = WatermarkRemover()
    processor = VideoProcessor(remover)
    
    # 提取帧到目录
    frames = processor.extract_frames(
        video_path="input_video.mp4",
        output_dir="./extracted_frames",
        interval=30,  # 每 30 帧提取一张
        max_frames=10  # 最多提取 10 张
    )
    
    print(f"提取了 {len(frames)} 帧")
    print()


def example_7_custom_config():
    """示例7: 自定义配置"""
    print("=== 示例7: 自定义配置 ===\n")
    
    # 使用自定义配置
    remover = WatermarkRemover(config_path="config/config.yaml")
    processor = VideoProcessor(remover, remover.config)
    
    result = processor.process_video(
        input_path="input_video.mp4",
        output_path="output_custom.mp4"
    )
    
    print(f"处理完成!")
    print()


def example_8_progress_callback():
    """示例8: 带进度回调"""
    print("=== 示例8: 带进度回调 ===\n")
    
    def progress_handler(current, total, message):
        """进度回调函数"""
        percentage = (current / total) * 100
        print(f"\r{message} - {percentage:.1f}%", end='', flush=True)
    
    remover = WatermarkRemover()
    processor = VideoProcessor(remover)
    
    result = processor.process_video(
        input_path="input_video.mp4",
        output_path="output_progress.mp4",
        progress_callback=progress_handler
    )
    
    print("\n处理完成!")
    print()


def example_9_batch_videos():
    """示例9: 批量处理视频"""
    print("=== 示例9: 批量处理视频 ===\n")
    
    from pathlib import Path
    from tqdm import tqdm
    
    remover = WatermarkRemover()
    processor = VideoProcessor(remover)
    
    # 获取所有视频文件
    input_dir = Path("./input_videos")
    output_dir = Path("./output_videos")
    output_dir.mkdir(exist_ok=True)
    
    video_files = list(input_dir.glob("*.mp4"))
    
    print(f"找到 {len(video_files)} 个视频")
    
    # 批量处理
    for video_file in tqdm(video_files, desc="处理视频"):
        output_file = output_dir / video_file.name
        try:
            processor.process_video(
                video_file,
                output_file,
                skip_frames=2,  # 加速处理
                quality='medium'
            )
        except Exception as e:
            print(f"处理失败: {video_file.name}, 错误: {e}")
    
    print("\n批量处理完成!")
    print()


def example_10_no_audio():
    """示例10: 不保留音频"""
    print("=== 示例10: 不保留音频 ===\n")
    
    remover = WatermarkRemover()
    processor = VideoProcessor(remover)
    
    # 处理视频，不保留音频
    result = processor.process_video(
        input_path="input_video.mp4",
        output_path="output_no_audio.mp4",
        keep_audio=False  # 不保留音频
    )
    
    print(f"处理完成（无音频）!")
    print()


def example_11_high_quality():
    """示例11: 高质量输出"""
    print("=== 示例11: 高质量输出 ===\n")
    
    remover = WatermarkRemover()
    processor = VideoProcessor(remover)
    
    # 高质量处理（不跳帧，高质量编码）
    result = processor.process_video(
        input_path="input_video.mp4",
        output_path="output_hq.mp4",
        skip_frames=1,  # 处理所有帧
        quality='high'  # 高质量
    )
    
    print(f"高质量处理完成!")
    print()


def example_12_comparison():
    """示例12: 生成对比视频"""
    print("=== 示例12: 生成对比视频 ===\n")
    
    import cv2
    import numpy as np
    from tqdm import tqdm
    
    # 读取原视频和处理后的视频
    cap1 = cv2.VideoCapture("input_video.mp4")
    cap2 = cv2.VideoCapture("output_video.mp4")
    
    # 获取视频信息
    fps = cap1.get(cv2.CAP_PROP_FPS)
    width = int(cap1.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap1.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap1.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # 创建输出视频（左右对比）
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(
        "comparison_video.mp4",
        fourcc,
        fps,
        (width * 2, height)
    )
    
    # 生成对比视频
    for _ in tqdm(range(total_frames), desc="生成对比"):
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()
        
        if not ret1 or not ret2:
            break
        
        # 添加标签
        cv2.putText(frame1, "Original", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame2, "Processed", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 左右拼接
        comparison = np.hstack([frame1, frame2])
        out.write(comparison)
    
    cap1.release()
    cap2.release()
    out.release()
    
    print("对比视频生成完成!")
    print()


if __name__ == "__main__":
    print("视频去水印使用示例\n")
    
    # 选择要运行的示例
    example_1_basic_video()
    # example_2_video_clip()
    # example_3_skip_frames()
    # example_4_adaptive_detection()
    # example_5_get_video_info()
    # example_6_extract_frames()
    # example_7_custom_config()
    # example_8_progress_callback()
    # example_9_batch_videos()
    # example_10_no_audio()
    # example_11_high_quality()
    # example_12_comparison()
    
    print("请取消注释要运行的示例")
