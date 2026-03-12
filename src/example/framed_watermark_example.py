"""
处理带矩形框水印的示例
专门针对 "AI生成" 等带边框的水印
"""
import cv2
import numpy as np
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.watermark_remover import WatermarkRemover
from src.framed_watermark_detector import FramedWatermarkDetector
from utils.image_utils import ImageUtils


def process_framed_watermark_basic(input_path: str, output_path: str):
    """
    方法1: 基础处理 - 扩展检测区域
    
    适用场景: 大部分带框水印
    """
    print("=== 方法1: 基础扩展处理 ===\n")
    
    # 初始化
    remover = WatermarkRemover()
    frame_detector = FramedWatermarkDetector()
    
    # 读取图片
    image_bgr = ImageUtils.load_image(input_path)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    
    # 1. OCR 检测文字
    print("步骤1: 检测水印文字...")
    text_boxes = remover.detector.detect(image_rgb)
    print(f"检测到 {len(text_boxes)} 个文字区域")
    
    # 2. 增强检测 - 扩展到矩形框
    print("步骤2: 扩展检测区域包含矩形框...")
    enhanced_boxes = frame_detector.detect_frames(image_bgr, text_boxes)
    print(f"增强后区域: {enhanced_boxes}")
    
    # 3. 生成 Mask
    print("步骤3: 生成 Mask...")
    mask = remover.mask_generator.generate(image_rgb, enhanced_boxes)
    
    # 4. 图像修复
    print("步骤4: 修复图像...")
    result_rgb = remover.inpainter.inpaint(image_rgb, mask)
    result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
    
    # 5. 保存结果
    cv2.imwrite(output_path, result_bgr)
    print(f"✓ 结果已保存: {output_path}\n")
    
    # 可视化检测结果
    vis = frame_detector.visualize_detection(image_bgr, text_boxes, enhanced_boxes)
    vis_path = output_path.replace('.', '_detection.')
    cv2.imwrite(vis_path, vis)
    print(f"✓ 检测可视化已保存: {vis_path}\n")
    
    return result_bgr


def process_framed_watermark_edge_detection(input_path: str, output_path: str):
    """
    方法2: 边缘检测 - 精确定位矩形框
    
    适用场景: 矩形框边缘清晰的水印
    """
    print("=== 方法2: 边缘检测处理 ===\n")
    
    remover = WatermarkRemover()
    frame_detector = FramedWatermarkDetector()
    
    # 读取图片
    image_bgr = ImageUtils.load_image(input_path)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    
    # 1. OCR 检测
    print("步骤1: 检测水印文字...")
    text_boxes = remover.detector.detect(image_rgb)
    
    # 2. 边缘检测增强
    print("步骤2: 使用边缘检测寻找矩形框...")
    enhanced_boxes = frame_detector.detect_frames(image_bgr, text_boxes)
    
    # 3. 生成 Mask（额外扩展）
    print("步骤3: 生成扩展 Mask...")
    mask = remover.mask_generator.generate_with_expansion(
        image_rgb, 
        enhanced_boxes,
        expand_pixels=10  # 额外扩展10像素确保完全覆盖
    )
    
    # 4. 修复
    print("步骤4: 修复图像...")
    result_rgb = remover.inpainter.inpaint(image_rgb, mask)
    result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
    
    # 5. 保存
    cv2.imwrite(output_path, result_bgr)
    print(f"✓ 结果已保存: {output_path}\n")
    
    return result_bgr


def process_framed_watermark_color_based(input_path: str, output_path: str):
    """
    方法3: 颜色检测 - 基于矩形框颜色
    
    适用场景: 矩形框有特定颜色（白色、黑色等）
    """
    print("=== 方法3: 颜色检测处理 ===\n")
    
    remover = WatermarkRemover()
    frame_detector = FramedWatermarkDetector()
    
    # 读取图片
    image_bgr = ImageUtils.load_image(input_path)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    
    # 1. OCR 检测
    print("步骤1: 检测水印文字...")
    text_boxes = remover.detector.detect(image_rgb)
    
    # 2. 颜色检测
    print("步骤2: 基于颜色检测矩形框...")
    # 检测白色/浅色矩形框
    enhanced_boxes = frame_detector.detect_by_color(
        image_bgr,
        text_boxes,
        color_range=((180, 180, 180), (255, 255, 255))  # 白色范围
    )
    
    # 如果没检测到，尝试其他颜色
    if enhanced_boxes == text_boxes:
        print("未检测到白色框，尝试检测黑色框...")
        enhanced_boxes = frame_detector.detect_by_color(
            image_bgr,
            text_boxes,
            color_range=((0, 0, 0), (80, 80, 80))  # 黑色范围
        )
    
    # 3. 生成 Mask
    print("步骤3: 生成 Mask...")
    mask = remover.mask_generator.generate(image_rgb, enhanced_boxes)
    
    # 4. 修复
    print("步骤4: 修复图像...")
    result_rgb = remover.inpainter.inpaint(image_rgb, mask)
    result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
    
    # 5. 保存
    cv2.imwrite(output_path, result_bgr)
    print(f"✓ 结果已保存: {output_path}\n")
    
    return result_bgr


def process_framed_watermark_manual(input_path: str, output_path: str,
                                   manual_box: tuple = None):
    """
    方法4: 手动指定 - 完全控制
    
    适用场景: 自动检测效果不佳时
    """
    print("=== 方法4: 手动指定区域 ===\n")
    
    remover = WatermarkRemover()
    
    # 读取图片
    image_bgr = ImageUtils.load_image(input_path)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    
    if manual_box is None:
        # 如果没有手动指定，显示图片让用户选择
        print("请查看图片确定水印位置...")
        print("格式: (x1, y1, x2, y2)")
        manual_box = (100, 50, 300, 120)  # 示例坐标
        print(f"使用示例坐标: {manual_box}")
    
    # 直接使用手动指定的区域
    print(f"步骤1: 使用手动区域: {manual_box}")
    boxes = [manual_box]
    
    # 生成 Mask
    print("步骤2: 生成 Mask...")
    mask = remover.mask_generator.generate(image_rgb, boxes)
    
    # 修复
    print("步骤3: 修复图像...")
    result_rgb = remover.inpainter.inpaint(image_rgb, mask)
    result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
    
    # 保存
    cv2.imwrite(output_path, result_bgr)
    print(f"✓ 结果已保存: {output_path}\n")
    
    return result_bgr


def process_framed_watermark_combined(input_path: str, output_path: str):
    """
    方法5: 组合策略 - 自动选择最佳方法
    
    这是推荐方法，自动尝试多种检测策略
    """
    print("=== 方法5: 智能组合处理 (推荐) ===\n")
    
    remover = WatermarkRemover()
    frame_detector = FramedWatermarkDetector()
    
    # 读取图片
    image_bgr = ImageUtils.load_image(input_path)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    
    # 1. OCR 检测
    print("步骤1: 检测水印文字...")
    text_boxes = remover.detector.detect(image_rgb)
    
    if not text_boxes:
        print("未检测到水印文字")
        return image_bgr
    
    # 2. 尝试多种检测方法
    print("步骤2: 尝试多种检测策略...")
    
    # 2.1 基础扩展
    boxes_expanded = frame_detector.detect_frames(image_bgr, text_boxes)
    
    # 2.2 颜色检测
    boxes_color = frame_detector.detect_by_color(image_bgr, text_boxes)
    
    # 2.3 选择最大的区域（更可能包含完整框）
    all_boxes = boxes_expanded + boxes_color
    final_box = frame_detector._merge_boxes(all_boxes)
    print(f"最终区域: {final_box}")
    
    # 3. 生成 Mask（额外扩展确保完全覆盖）
    print("步骤3: 生成优化 Mask...")
    mask = remover.mask_generator.generate_with_expansion(
        image_rgb,
        [final_box],
        expand_pixels=15  # 额外扩展
    )
    
    # 4. 修复
    print("步骤4: 修复图像...")
    result_rgb = remover.inpainter.inpaint(image_rgb, mask)
    result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
    
    # 5. 保存
    cv2.imwrite(output_path, result_bgr)
    print(f"✓ 结果已保存: {output_path}\n")
    
    # 保存对比图
    comparison = np.hstack([image_bgr, result_bgr])
    comp_path = output_path.replace('.', '_comparison.')
    cv2.imwrite(comp_path, comparison)
    print(f"✓ 对比图已保存: {comp_path}\n")
    
    return result_bgr


def interactive_manual_selection(input_path: str, output_path: str):
    """
    交互式手动选择水印区域
    
    使用鼠标框选水印位置
    """
    print("=== 交互式手动选择 ===\n")
    print("使用说明:")
    print("1. 点击并拖动鼠标框选水印区域")
    print("2. 按 'r' 重置选择")
    print("3. 按 'Enter' 确认并处理")
    print("4. 按 'Esc' 取消\n")
    
    # 读取图片
    image = cv2.imread(input_path)
    clone = image.copy()
    
    # 存储选择的区域
    ref_point = []
    cropping = False
    
    def click_and_crop(event, x, y, flags, param):
        nonlocal ref_point, cropping
        
        if event == cv2.EVENT_LBUTTONDOWN:
            ref_point = [(x, y)]
            cropping = True
        
        elif event == cv2.EVENT_LBUTTONUP:
            ref_point.append((x, y))
            cropping = False
            
            # 绘制矩形
            cv2.rectangle(image, ref_point[0], ref_point[1], (0, 255, 0), 2)
            cv2.imshow("image", image)
    
    # 创建窗口
    cv2.namedWindow("image")
    cv2.setMouseCallback("image", click_and_crop)
    
    # 显示图片
    while True:
        cv2.imshow("image", image)
        key = cv2.waitKey(1) & 0xFF
        
        # 按 'r' 重置
        if key == ord("r"):
            image = clone.copy()
            ref_point = []
        
        # 按 Enter 确认
        elif key == 13:  # Enter
            break
        
        # 按 Esc 取消
        elif key == 27:  # Esc
            cv2.destroyAllWindows()
            print("已取消")
            return None
    
    cv2.destroyAllWindows()
    
    # 处理选中的区域
    if len(ref_point) == 2:
        x1, y1 = ref_point[0]
        x2, y2 = ref_point[1]
        
        # 确保 x1 < x2, y1 < y2
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        manual_box = (x1, y1, x2, y2)
        print(f"选中区域: {manual_box}")
        
        # 处理
        return process_framed_watermark_manual(input_path, output_path, manual_box)
    else:
        print("未选择区域")
        return None


if __name__ == "__main__":
    # 输入输出路径
    input_image = "logo.png"  # 替换为你的图片路径
    
    print("带矩形框水印处理示例\n")
    print("=" * 50)
    
    # 方法1: 基础扩展（最快）
    # process_framed_watermark_basic(input_image, "output_basic.png")
    
    # 方法2: 边缘检测（较精确）
    # process_framed_watermark_edge_detection(input_image, "output_edge.png")
    
    # 方法3: 颜色检测（适合特定颜色框）
    # process_framed_watermark_color_based(input_image, "output_color.png")
    
    # 方法4: 手动指定（最可控）
    # process_framed_watermark_manual(input_image, "output_manual.png", 
    #                                manual_box=(50, 20, 200, 80))
    
    # 方法5: 智能组合（推荐）⭐
    process_framed_watermark_combined(input_image, "output_best.png")
    
    # 交互式选择（需要图形界面）
    # interactive_manual_selection(input_image, "output_interactive.png")
    
    print("=" * 50)
    print("\n所有处理完成!")
