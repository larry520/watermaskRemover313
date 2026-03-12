"""
批量处理示例
"""
from pathlib import Path
from src.watermark_remover import WatermarkRemover
from tqdm import tqdm
import concurrent.futures


def batch_process_sequential():
    """顺序批量处理"""
    print("=== 顺序批量处理 ===\n")
    
    input_dir = Path("./input_images")
    output_dir = Path("./output_images")
    
    # 初始化
    remover = WatermarkRemover()
    
    # 获取所有图片
    image_files = list(input_dir.glob("*.jpg"))
    print(f"找到 {len(image_files)} 个图片\n")
    
    # 处理
    for img_file in tqdm(image_files, desc="处理中"):
        output_file = output_dir / img_file.name
        try:
            remover.remove(img_file, output_file)
        except Exception as e:
            print(f"处理失败: {img_file.name}, 错误: {e}")
    
    print("\n完成!")


def batch_process_parallel():
    """并行批量处理（多线程）"""
    print("=== 并行批量处理 ===\n")
    
    input_dir = Path("./input_images")
    output_dir = Path("./output_images")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取所有图片
    image_files = list(input_dir.glob("*.jpg"))
    print(f"找到 {len(image_files)} 个图片\n")
    
    def process_one(img_file):
        """处理单个文件"""
        remover = WatermarkRemover()  # 每个线程创建自己的实例
        output_file = output_dir / img_file.name
        try:
            remover.remove(img_file, output_file)
            return True, img_file.name
        except Exception as e:
            return False, f"{img_file.name}: {e}"
    
    # 并行处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(tqdm(
            executor.map(process_one, image_files),
            total=len(image_files),
            desc="处理中"
        ))
    
    # 统计结果
    success = sum(1 for r, _ in results if r)
    print(f"\n完成! 成功: {success}/{len(image_files)}")


def batch_with_filter():
    """带过滤的批量处理"""
    print("=== 带过滤的批量处理 ===\n")
    
    input_dir = Path("./input_images")
    output_dir = Path("./output_images")
    
    remover = WatermarkRemover()
    
    # 获取所有图片
    all_files = list(input_dir.glob("*.*"))
    
    # 过滤：只处理包含水印的图片
    files_to_process = []
    
    print("检测水印中...")
    for img_file in tqdm(all_files, desc="扫描"):
        try:
            detections = remover.detect_only(img_file)
            has_watermark = any(d['is_watermark'] for d in detections)
            if has_watermark:
                files_to_process.append(img_file)
        except:
            pass
    
    print(f"\n找到 {len(files_to_process)} 个包含水印的图片\n")
    
    # 处理
    for img_file in tqdm(files_to_process, desc="去水印"):
        output_file = output_dir / img_file.name
        try:
            remover.remove(img_file, output_file)
        except Exception as e:
            print(f"处理失败: {img_file.name}")
    
    print("\n完成!")


def batch_with_comparison():
    """批量处理并生成对比图"""
    print("=== 批量处理 + 对比图 ===\n")
    
    import cv2
    import numpy as np
    from utils.image_utils import ImageUtils
    
    input_dir = Path("./input_images")
    output_dir = Path("./output_images")
    comparison_dir = Path("./comparison_images")
    comparison_dir.mkdir(parents=True, exist_ok=True)
    
    remover = WatermarkRemover()
    
    image_files = list(input_dir.glob("*.jpg"))
    
    for img_file in tqdm(image_files, desc="处理中"):
        try:
            # 处理
            output_file = output_dir / img_file.name
            remover.remove(img_file, output_file)
            
            # 生成对比图
            original = ImageUtils.load_image(img_file)
            result = ImageUtils.load_image(output_file)
            
            # 确保尺寸一致
            if original.shape != result.shape:
                result = cv2.resize(result, (original.shape[1], original.shape[0]))
            
            # 左右拼接
            comparison = np.hstack([original, result])
            
            # 添加标签
            cv2.putText(comparison, "Original", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(comparison, "Result", (original.shape[1] + 10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # 保存
            comparison_file = comparison_dir / f"comparison_{img_file.name}"
            ImageUtils.save_image(comparison, comparison_file)
            
        except Exception as e:
            print(f"处理失败: {img_file.name}, 错误: {e}")
    
    print("\n完成!")


def batch_with_statistics():
    """批量处理并统计信息"""
    print("=== 批量处理 + 统计 ===\n")
    
    import time
    from utils.image_utils import ImageUtils
    
    input_dir = Path("./input_images")
    output_dir = Path("./output_images")
    
    remover = WatermarkRemover()
    
    image_files = list(input_dir.glob("*.jpg"))
    
    # 统计数据
    stats = {
        'total': len(image_files),
        'success': 0,
        'failed': 0,
        'has_watermark': 0,
        'no_watermark': 0,
        'total_time': 0,
        'avg_time': 0
    }
    
    start_time = time.time()
    
    for img_file in tqdm(image_files, desc="处理中"):
        try:
            file_start = time.time()
            
            # 检测
            detections = remover.detect_only(img_file)
            has_watermark = any(d['is_watermark'] for d in detections)
            
            if has_watermark:
                stats['has_watermark'] += 1
                
                # 去除水印
                output_file = output_dir / img_file.name
                remover.remove(img_file, output_file)
                stats['success'] += 1
            else:
                stats['no_watermark'] += 1
                
            file_time = time.time() - file_start
            stats['total_time'] += file_time
            
        except Exception as e:
            stats['failed'] += 1
            print(f"失败: {img_file.name}")
    
    stats['avg_time'] = stats['total_time'] / stats['total']
    
    # 打印统计
    print("\n=== 统计信息 ===")
    print(f"总计: {stats['total']} 个文件")
    print(f"成功: {stats['success']} 个")
    print(f"失败: {stats['failed']} 个")
    print(f"包含水印: {stats['has_watermark']} 个")
    print(f"无水印: {stats['no_watermark']} 个")
    print(f"总耗时: {stats['total_time']:.2f} 秒")
    print(f"平均耗时: {stats['avg_time']:.2f} 秒/张")
    print()


if __name__ == "__main__":
    # 选择要运行的示例
    print("批量处理示例\n")
    
    # batch_process_sequential()
    # batch_process_parallel()
    # batch_with_filter()
    # batch_with_comparison()
    batch_with_statistics()
