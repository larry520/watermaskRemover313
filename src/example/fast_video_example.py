"""
快速视频去水印示例 - 使用固定 Mask
适用于水印位置固定的视频（大幅提升处理速度）
"""
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.watermark_remover import WatermarkRemover
from src.fast_video_processor import FastVideoProcessor


def example_1_auto_detect_first_frame():
    """
    示例1: 从第一帧自动检测水印 ⭐ 推荐
    
    优势:
    - 自动化，无需手动指定
    - 速度快，只检测一次
    - 适合90%以上的场景
    """
    print("=== 示例1: 自动检测第一帧 ===\n")
    
    # 初始化
    remover = WatermarkRemover()
    processor = FastVideoProcessor(remover)
    
    # 处理视频
    result = processor.process_video_with_fixed_mask(
        input_path="input_video.mp4",
        output_path="output_video.mp4",
        detect_from_first_frame=True,  # 从第一帧检测
        quality='high',
        keep_audio=True
    )
    
    print(f"✓ 处理完成!")
    print(f"  总帧数: {result['total_frames']}")
    print(f"  Mask 保存: {result['mask_path']}")
    print()


def example_2_manual_box():
    """
    示例2: 手动指定水印区域
    
    优势:
    - 完全控制
    - 速度最快（无需 OCR）
    - 适合已知水印位置
    """
    print("=== 示例2: 手动指定区域 ===\n")
    
    remover = WatermarkRemover()
    processor = FastVideoProcessor(remover)
    
    # 手动指定水印位置 (x1, y1, x2, y2)
    watermark_box = (50, 10, 200, 80)
    
    result = processor.process_video_with_fixed_mask(
        input_path="input_video.mp4",
        output_path="output_video.mp4",
        manual_box=watermark_box,  # 手动区域
        quality='high',
        keep_audio=True
    )
    
    print(f"✓ 处理完成!")
    print()


def example_3_reuse_mask():
    """
    示例3: 复用已保存的 Mask
    
    优势:
    - 批量处理同类视频
    - 速度极快
    - 保证一致性
    """
    print("=== 示例3: 复用保存的 Mask ===\n")
    
    remover = WatermarkRemover()
    processor = FastVideoProcessor(remover)
    
    # 1. 加载之前保存的 mask
    print("步骤1: 加载 Mask...")
    processor.load_mask("saved_mask.png")
    
    # 2. 处理视频
    print("步骤2: 处理视频...")
    result = processor.process_video_with_fixed_mask(
        input_path="input_video.mp4",
        output_path="output_video.mp4",
        detect_from_first_frame=False  # 不检测，直接用加载的 mask
    )
    
    print(f"✓ 处理完成!")
    print()


def example_4_preview_before_process():
    """
    示例4: 预览 Mask 效果后再处理
    
    优势:
    - 确认 mask 准确性
    - 避免浪费时间
    """
    print("=== 示例4: 预览后处理 ===\n")
    
    remover = WatermarkRemover()
    processor = FastVideoProcessor(remover)
    
    # 1. 手动指定区域
    watermark_box = (50, 10, 200, 80)
    
    # 2. 生成 mask
    print("步骤1: 生成 Mask...")
    import cv2
    cap = cv2.VideoCapture("input_video.mp4")
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cap.release()
    
    mask = processor._create_mask_from_box((h, w), watermark_box)
    processor.fixed_mask = mask
    
    # 3. 预览 mask 在第一帧的效果
    print("步骤2: 预览 Mask...")
    processor.preview_mask_on_frame(
        "input_video.mp4",
        "mask_preview.png",
        frame_number=0
    )
    print("  ✓ 预览已保存: mask_preview.png")
    print("  请检查预览图，确认 mask 是否准确")
    
    # 4. 确认后处理
    input("按 Enter 继续处理，或 Ctrl+C 取消...")
    
    print("步骤3: 处理视频...")
    result = processor.process_video_with_fixed_mask(
        input_path="input_video.mp4",
        output_path="output_video.mp4",
        mask=mask
    )
    
    print(f"✓ 处理完成!")
    print()


def example_5_batch_same_mask():
    """
    示例5: 使用相同 Mask 批量处理多个视频 ⭐ 高效
    
    优势:
    - 批量处理
    - 统一水印处理
    - 适合系列视频
    """
    print("=== 示例5: 批量处理（相同 Mask）===\n")
    
    remover = WatermarkRemover()
    processor = FastVideoProcessor(remover)
    
    # 视频列表
    video_files = [
        "video1.mp4",
        "video2.mp4",
        "video3.mp4"
    ]
    
    # 方式1: 从第一个视频自动检测
    print("方式1: 自动检测...")
    results = processor.batch_process_with_same_mask(
        video_paths=video_files,
        output_dir="./output_videos"
    )
    
    # 方式2: 手动指定区域
    print("\n方式2: 手动指定...")
    results = processor.batch_process_with_same_mask(
        video_paths=video_files,
        output_dir="./output_videos",
        manual_box=(50, 10, 200, 80)
    )
    
    print(f"\n✓ 批量处理完成: {len(results)} 个视频")
    print()


def example_6_compare_speed():
    """
    示例6: 速度对比（固定 Mask vs 逐帧检测）
    """
    print("=== 示例6: 速度对比 ===\n")
    
    import time
    from src.video_processor import VideoProcessor
    
    remover = WatermarkRemover()
    
    # 方法1: 固定 Mask（快速）
    print("方法1: 固定 Mask 处理...")
    fast_processor = FastVideoProcessor(remover)
    
    start = time.time()
    fast_processor.process_video_with_fixed_mask(
        "test_video.mp4",
        "output_fast.mp4",
        detect_from_first_frame=True
    )
    fast_time = time.time() - start
    
    print(f"  耗时: {fast_time:.2f} 秒")
    
    # 方法2: 逐帧检测（慢）
    print("\n方法2: 逐帧检测处理...")
    normal_processor = VideoProcessor(remover)
    
    start = time.time()
    normal_processor.process_video(
        "test_video.mp4",
        "output_normal.mp4",
        skip_frames=1
    )
    normal_time = time.time() - start
    
    print(f"  耗时: {normal_time:.2f} 秒")
    
    # 对比
    print(f"\n速度提升: {normal_time / fast_time:.1f}x")
    print()


def example_7_workflow():
    """
    示例7: 完整工作流程
    
    步骤:
    1. 从第一帧检测生成 mask
    2. 保存 mask
    3. 预览 mask
    4. 处理视频
    5. 复用 mask 处理更多视频
    """
    print("=== 示例7: 完整工作流程 ===\n")
    
    remover = WatermarkRemover()
    processor = FastVideoProcessor(remover)
    
    # 步骤1: 处理第一个视频，生成 mask
    print("步骤1: 处理第一个视频...")
    result = processor.process_video_with_fixed_mask(
        input_path="video1.mp4",
        output_path="output1.mp4",
        detect_from_first_frame=True
    )
    print(f"  ✓ 完成，Mask 保存至: {result['mask_path']}")
    
    # 步骤2: 保存 mask 以便复用
    print("\n步骤2: 保存 Mask...")
    processor.save_mask("my_watermark_mask.png")
    print("  ✓ Mask 已保存")
    
    # 步骤3: 使用相同 mask 处理其他视频
    print("\n步骤3: 处理更多视频...")
    more_videos = ["video2.mp4", "video3.mp4"]
    
    for video in more_videos:
        result = processor.process_video_with_fixed_mask(
            input_path=video,
            output_path=f"output_{video}",
            detect_from_first_frame=False  # 复用已有 mask
        )
        print(f"  ✓ {video} 处理完成")
    
    print("\n✓ 所有视频处理完成!")
    print()


def example_8_save_and_load_mask():
    """
    示例8: 保存和加载 Mask（跨项目复用）
    """
    print("=== 示例8: Mask 保存与加载 ===\n")
    
    remover = WatermarkRemover()
    
    # === 场景1: 第一次处理，保存 mask ===
    print("场景1: 第一次处理...")
    processor1 = FastVideoProcessor(remover)
    
    result = processor1.process_video_with_fixed_mask(
        "video1.mp4",
        "output1.mp4",
        manual_box=(50, 10, 200, 80)
    )
    
    # 保存 mask
    processor1.save_mask("watermark_mask.png")
    print("  ✓ Mask 已保存: watermark_mask.png\n")
    
    # === 场景2: 下次直接加载 mask ===
    print("场景2: 直接加载 Mask...")
    processor2 = FastVideoProcessor(remover)
    
    # 加载之前保存的 mask
    processor2.load_mask("watermark_mask.png")
    
    # 立即处理
    result = processor2.process_video_with_fixed_mask(
        "video2.mp4",
        "output2.mp4",
        detect_from_first_frame=False
    )
    
    print("  ✓ 使用保存的 Mask 处理完成")
    print()


if __name__ == "__main__":
    print("快速视频去水印 - 固定 Mask 方法\n")
    print("=" * 60)
    
    # 选择要运行的示例
    
    # 推荐示例：自动检测
    # example_1_auto_detect_first_frame()
    
    # 手动指定区域
    # example_2_manual_box()
    
    # 复用 mask
    # example_3_reuse_mask()
    
    # 预览后处理
    # example_4_preview_before_process()
    
    # 批量处理
    # example_5_batch_same_mask()
    
    # 速度对比
    # example_6_compare_speed()
    
    # 完整流程
    # example_7_workflow()
    
    # 保存加载
    # example_8_save_and_load_mask()
    
    print("=" * 60)
    print("\n请取消注释要运行的示例")
