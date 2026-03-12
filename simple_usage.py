"""
简单使用示例
"""
from src.watermark_remover import WatermarkRemover


def example_1_basic_usage():
    """示例1: 基本使用"""
    print("=== 示例1: 基本使用 ===\n")
    
    # 初始化
    remover = WatermarkRemover(config_path='config.yaml')
    
    # 去除水印
    remover.remove(
        input_path="input.jpg",
        output_path="output.jpg"
    )
    
    print("完成!\n")


def example_2_with_visualization():
    """示例2: 带可视化"""
    print("=== 示例2: 带可视化 ===\n")
    
    remover = WatermarkRemover()
    
    # 去除水印并保存检测可视化
    remover.remove(
        input_path="input.jpg",
        output_path="output.jpg",
        visualize_detection=True  # 会额外保存 output_detection.jpg
    )
    
    print("完成!\n")


def example_3_custom_config():
    """示例3: 自定义配置"""
    print("=== 示例3: 自定义配置 ===\n")
    
    # 使用自定义配置文件
    remover = WatermarkRemover(config_path="my_config.yaml")
    
    remover.remove(
        input_path="input.jpg",
        output_path="output.jpg"
    )
    
    print("完成!\n")


def example_4_detect_only():
    """示例4: 仅检测水印"""
    print("=== 示例4: 仅检测水印 ===\n")
    
    remover = WatermarkRemover()
    
    # 仅检测，不修复
    detections = remover.detect_only("input.jpg")
    
    print(f"检测到 {len(detections)} 个文字区域:\n")
    for i, det in enumerate(detections, 1):
        print(f"{i}. '{det['text']}' (置信度: {det['confidence']:.2f})")
        print(f"   位置: {det['box']}")
        print(f"   是否为水印: {det['is_watermark']}\n")


def example_5_from_array():
    """示例5: 从 numpy 数组处理"""
    print("=== 示例5: 从 numpy 数组处理 ===\n")
    
    import cv2
    from utils.image_utils import ImageUtils
    
    remover = WatermarkRemover()
    
    # 读取图片为 numpy 数组
    image = ImageUtils.load_image_rgb("input.jpg")
    
    # 处理
    result, mask = remover.remove_from_array(image)
    
    # 保存
    ImageUtils.save_image(ImageUtils.rgb_to_bgr(result), "output.jpg")
    
    print("完成!\n")


def example_6_get_system_info():
    """示例6: 获取系统信息"""
    print("=== 示例6: 获取系统信息 ===\n")
    
    remover = WatermarkRemover()
    info = remover.get_system_info()
    
    print("OCR 语言:", info['detector']['languages'])
    print("GPU 加速:", info['detector']['gpu'])
    print("修复模型:", info['inpainter']['model_name'])
    print("设备:", info['inpainter']['device'])
    print()


def example_7_batch_processing():
    """示例7: 批量处理"""
    print("=== 示例7: 批量处理 ===\n")
    
    remover = WatermarkRemover()
    
    # 批量处理整个文件夹
    success_files = remover.batch_remove(
        input_dir="./input_folder",
        output_dir="./output_folder",
        pattern="*.jpg"  # 只处理 jpg 文件
    )
    
    print(f"成功处理 {len(success_files)} 个文件\n")


if __name__ == "__main__":
    # 运行示例
    print("水印去除工具 - 使用示例\n")
    
    # 选择要运行的示例
    example_1_basic_usage()
    # example_2_with_visualization()
    # example_3_custom_config()
    # example_4_detect_only()
    # example_5_from_array()
    # example_6_get_system_info()
    # example_7_batch_processing()
