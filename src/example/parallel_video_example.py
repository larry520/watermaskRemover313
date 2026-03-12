"""
多线程视频处理示例
展示如何使用并行处理大幅提升速度
"""
import cv2
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.watermark_remover import WatermarkRemover
from src.parallel_video_processor import ParallelVideoProcessor


def example_1_basic_parallel():
    """
    示例1: 基本并行处理
    
    最简单的用法，自动检测水印并并行处理
    """
    print("=" * 70)
    print("示例1: 基本并行处理")
    print("=" * 70)
    print()
    
    # 初始化
    remover = WatermarkRemover(config_path=r"D:\projects\watermask\config.yaml")
    processor = ParallelVideoProcessor(remover)
    
    # 并行处理（自动检测）
    result = processor.process_video_parallel(
        input_path=r"D:\projects\watermask\outputs\62_raw.mp4",
        output_path="output_parallel.mp4",
        batch_size=30,          # 每批处理30帧
        quality='high',
        keep_audio=True
    )
    
    print(f"\n✓ 处理完成!")
    print(f"  总帧数: {result['total_frames']}")
    print(f"  耗时: {result['elapsed_time']:.2f} 秒")
    print(f"  速度: {result['processing_speed']:.2f} fps")
    print(f"  工作线程: {result['num_workers']}")


def example_2_manual_box():
    """
    示例2: 手动指定水印区域
    
    当已知水印位置时，跳过检测直接处理
    """
    print("=" * 70)
    print("示例2: 手动指定水印区域（最快）")
    print("=" * 70)
    print()
    
    remover = WatermarkRemover()
    processor = ParallelVideoProcessor(remover, num_workers=4)
    
    # 手动指定水印位置
    watermark_box = (50, 10, 200, 80)
    
    result = processor.process_video_parallel(
        input_path="input_video.mp4",
        output_path="output_parallel.mp4",
        manual_box=watermark_box,  # 手动指定
        batch_size=50,              # 可以用更大的批次
        quality='medium'
    )
    
    print(f"\n✓ 处理完成!")


def example_3_with_saved_mask():
    """
    示例3: 使用已保存的 Mask
    
    复用之前保存的 mask，最快速度
    """
    print("=" * 70)
    print("示例3: 使用已保存的 Mask")
    print("=" * 70)
    print()
    
    # 加载之前保存的 mask
    mask = cv2.imread("saved_mask.png", cv2.IMREAD_GRAYSCALE)
    
    remover = WatermarkRemover()
    processor = ParallelVideoProcessor(remover)
    
    result = processor.process_video_parallel(
        input_path="input_video.mp4",
        output_path="output_parallel.mp4",
        mask=mask,              # 直接提供 mask
        batch_size=50,
        quality='high'
    )
    
    print(f"\n✓ 处理完成!")


def example_4_adjust_workers():
    """
    示例4: 调整工作线程数
    
    根据CPU核心数优化性能
    """
    print("=" * 70)
    print("示例4: 调整工作线程数")
    print("=" * 70)
    print()
    
    from multiprocessing import cpu_count
    
    print(f"CPU 核心数: {cpu_count()}")
    print()
    
    remover = WatermarkRemover()
    
    # 测试不同的工作线程数
    for num_workers in [1, 2, 4, cpu_count()]:
        print(f"\n测试 {num_workers} 个工作线程...")
        
        processor = ParallelVideoProcessor(remover, num_workers=num_workers)
        
        result = processor.process_video_parallel(
            input_path="test_video.mp4",
            output_path=f"output_{num_workers}workers.mp4",
            manual_box=(50, 10, 200, 80),
            batch_size=30
        )
        
        print(f"  速度: {result['processing_speed']:.2f} fps")


def example_5_batch_size_optimization():
    """
    示例5: 优化批次大小
    
    找到最佳的批次大小
    """
    print("=" * 70)
    print("示例5: 优化批次大小")
    print("=" * 70)
    print()
    
    remover = WatermarkRemover()
    processor = ParallelVideoProcessor(remover)
    
    # 测试不同的批次大小
    for batch_size in [10, 30, 50, 100]:
        print(f"\n测试批次大小: {batch_size}")
        
        result = processor.process_video_parallel(
            input_path="test_video.mp4",
            output_path=f"output_batch{batch_size}.mp4",
            manual_box=(50, 10, 200, 80),
            batch_size=batch_size
        )
        
        print(f"  速度: {result['processing_speed']:.2f} fps")
        print(f"  批次数: {result['total_frames'] // batch_size}")


def example_6_compare_methods():
    """
    示例6: 对比不同方法的速度
    
    单线程 vs 多线程 vs 快速模式
    """
    print("=" * 70)
    print("示例6: 速度对比")
    print("=" * 70)
    print()
    
    import time
    
    remover = WatermarkRemover()
    video_path = "test_video.mp4"
    
    # 方法1: 标准单线程（VideoProcessor）
    print("方法1: 标准单线程处理...")
    from src.video_processor import VideoProcessor
    
    processor_std = VideoProcessor(remover, remover.config)
    
    start = time.time()
    processor_std.process_video(
        video_path,
        "output_standard.mp4",
        skip_frames=1
    )
    std_time = time.time() - start
    
    print(f"  耗时: {std_time:.2f} 秒")
    print()
    
    # 方法2: 快速单线程（FastVideoProcessor）
    print("方法2: 快速单线程（固定 Mask）...")
    from src.fast_video_processor import FastVideoProcessor
    
    processor_fast = FastVideoProcessor(remover)
    
    start = time.time()
    processor_fast.process_video_with_fixed_mask(
        video_path,
        "output_fast.mp4",
        manual_box=(50, 10, 200, 80)
    )
    fast_time = time.time() - start
    
    print(f"  耗时: {fast_time:.2f} 秒")
    print()
    
    # 方法3: 多线程并行
    print("方法3: 多线程并行...")
    processor_parallel = ParallelVideoProcessor(remover)
    
    start = time.time()
    processor_parallel.process_video_parallel(
        video_path,
        "output_parallel.mp4",
        manual_box=(50, 10, 200, 80),
        batch_size=30
    )
    parallel_time = time.time() - start
    
    print(f"  耗时: {parallel_time:.2f} 秒")
    print()
    
    # 对比结果
    print("=" * 70)
    print("速度对比")
    print("=" * 70)
    print(f"标准单线程:   {std_time:.2f} 秒  (基准)")
    print(f"快速单线程:   {fast_time:.2f} 秒  (提升 {std_time/fast_time:.2f}x)")
    print(f"多线程并行:   {parallel_time:.2f} 秒  (提升 {std_time/parallel_time:.2f}x)")
    print()
    print(f"多线程相比快速: 提升 {fast_time/parallel_time:.2f}x")
    print("=" * 70)


def example_7_production_workflow():
    """
    示例7: 生产环境完整流程
    
    实际项目中推荐的使用方式
    """
    print("=" * 70)
    print("示例7: 生产环境完整流程")
    print("=" * 70)
    print()
    
    # 1. 初始化
    print("步骤1: 初始化处理器...")
    remover = WatermarkRemover()
    processor = ParallelVideoProcessor(
        remover,
        num_workers=None  # 自动使用 CPU核心数-1
    )
    print("  ✓ 完成")
    print()
    
    # 2. 从第一个视频生成 mask
    print("步骤2: 从第一个视频生成 Mask...")
    first_video = "video1.mp4"
    
    # 读取第一帧
    cap = cv2.VideoCapture(first_video)
    ret, first_frame = cap.read()
    cap.release()
    
    # 检测并生成 mask
    frame_rgb = cv2.cvtColor(first_frame, cv2.COLOR_BGR2RGB)
    detections = remover.detector.detect(frame_rgb)
    
    if detections:
        boxes = [det['box'] for det in detections]
        mask = remover.mask_generator.generate_with_expansion(
            frame_rgb, boxes, expand_pixels=20
        )
        
        # 保存 mask
        cv2.imwrite("master_mask.png", mask)
        print("  ✓ Mask 已保存: master_mask.png")
    else:
        print("  ✗ 未检测到水印，使用手动区域")
        mask = None
    
    print()
    
    # 3. 批量处理所有视频
    print("步骤3: 批量处理所有视频...")
    videos = [
        "video1.mp4",
        "video2.mp4",
        "video3.mp4"
    ]
    
    for i, video in enumerate(videos, 1):
        print(f"\n处理 [{i}/{len(videos)}]: {video}")
        
        result = processor.process_video_parallel(
            input_path=video,
            output_path=f"processed_{video}",
            mask=mask,  # 使用相同的 mask
            batch_size=50,
            quality='high',
            keep_audio=True
        )
        
        print(f"  ✓ 完成，速度: {result['processing_speed']:.2f} fps")
    
    print()
    print("=" * 70)
    print("✓ 所有视频处理完成！")
    print("=" * 70)


if __name__ == "__main__":
    print("多线程视频处理示例\n")
    print("=" * 70)
    print("选择要运行的示例:")
    print("=" * 70)
    print("1. 基本并行处理")
    print("2. 手动指定水印区域")
    print("3. 使用已保存的 Mask")
    print("4. 调整工作线程数")
    print("5. 优化批次大小")
    print("6. 速度对比")
    print("7. 生产环境完整流程 ⭐ 推荐")
    print("=" * 70)
    print()
    
    # 取消注释要运行的示例
    
    example_1_basic_parallel()
    # example_2_manual_box()
    # example_3_with_saved_mask()
    # example_4_adjust_workers()
    # example_5_batch_size_optimization()
    # example_6_compare_methods()
    # example_7_production_workflow()
    
    print("请取消注释要运行的示例")
