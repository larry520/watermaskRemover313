# 带矩形框水印处理指南

## 问题类型

像 "AI生成" 这种带矩形边框的水印，包含两部分：
1. **文字内容** - "AI生成"
2. **矩形边框** - 文字周围的半透明框

## 🎯 处理方法

### 方法1: 快速处理（推荐）⭐

**适用场景**: 简单的带框水印，水印位置固定

```python
import cv2
import numpy as np

# 1. 读取图片
image = cv2.imread("input.png")
h, w = image.shape[:2]

# 2. 创建 mask
mask = np.zeros((h, w), dtype=np.uint8)

# 3. 根据水印位置绘制矩形区域
# 需要根据实际图片调整坐标
x1, y1, x2, y2 = 50, 5, 190, 40  # 水印区域坐标
cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)

# 4. 扩展 mask（包含边框）
kernel = np.ones((7, 7), np.uint8)
mask = cv2.dilate(mask, kernel, iterations=2)

# 5. 边缘模糊
mask = cv2.GaussianBlur(mask, (5, 5), 0)

# 6. 修复
result = cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_NS)

# 7. 保存
cv2.imwrite("output.png", result)
```

**关键参数**:
- `x1, y1, x2, y2`: 水印边界框坐标（需要根据图片调整）
- `kernel=(7, 7)`: 膨胀核大小，越大覆盖范围越广
- `iterations=2`: 膨胀次数，确保完全覆盖边框
- `inpaintRadius=3`: 修复半径，越大修复范围越广

---

### 方法2: 自动检测处理

**适用场景**: 水印位置不固定，需要自动检测

```python
from src.watermark_remover import WatermarkRemover
import cv2

# 初始化
remover = WatermarkRemover()

# 读取图片
image_bgr = cv2.imread("input.png")
image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

# 1. OCR 检测文字位置
text_boxes = remover.detector.detect(image_rgb)

# 2. 扩展区域以包含矩形框
expanded_boxes = []
for x1, y1, x2, y2 in text_boxes:
    # 向四周扩展 25 像素
    x1 -= 25
    y1 -= 25
    x2 += 25
    y2 += 25
    expanded_boxes.append((x1, y1, x2, y2))

# 3. 生成 mask（额外扩展 10 像素）
mask = remover.mask_generator.generate_with_expansion(
    image_rgb,
    expanded_boxes,
    expand_pixels=10
)

# 4. 修复
result_rgb = remover.inpainter.inpaint(image_rgb, mask)
result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)

# 5. 保存
cv2.imwrite("output.png", result_bgr)
```

---

### 方法3: 增强检测（精确处理）

**适用场景**: 复杂水印，需要精确检测矩形框边界

使用我创建的 `FramedWatermarkDetector`:

```python
from src.watermark_remover import WatermarkRemover
from src.framed_watermark_detector import FramedWatermarkDetector
import cv2

# 初始化
remover = WatermarkRemover()
frame_detector = FramedWatermarkDetector()

# 读取图片
image_bgr = cv2.imread("input.png")
image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

# 1. 检测文字
text_boxes = remover.detector.detect(image_rgb)

# 2. 检测矩形框（自动扩展）
enhanced_boxes = frame_detector.detect_frames(image_bgr, text_boxes)

# 3. 生成 mask
mask = remover.mask_generator.generate_with_expansion(
    image_rgb,
    enhanced_boxes,
    expand_pixels=15
)

# 4. 修复
result_rgb = remover.inpainter.inpaint(image_rgb, mask)
result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)

# 5. 保存
cv2.imwrite("output.png", result_bgr)
```

---

### 方法4: 手动指定（完全控制）

**适用场景**: 自动检测效果不理想

```bash
# 命令行
python examples/framed_watermark_example.py

# 在代码中指定坐标
process_framed_watermark_manual(
    "input.png",
    "output.png",
    manual_box=(50, 5, 190, 40)  # (x1, y1, x2, y2)
)
```

---

## 🔧 参数调优指南

### 1. 确定水印位置

**查看图片坐标**:
```python
import cv2

image = cv2.imread("input.png")
print(f"图片尺寸: {image.shape[1]}x{image.shape[0]}")  # 宽x高

# 可以用图像查看工具（如 Photoshop、GIMP）确定坐标
```

### 2. 调整扩展范围

**扩展不够（边框残留）**:
```python
# 增加扩展像素
expand_pixels = 20  # 原来是 10，增加到 20

# 或增加膨胀迭代
iterations = 3  # 原来是 2，增加到 3
```

**扩展过多（修复区域过大）**:
```python
# 减少扩展
expand_pixels = 5
iterations = 1
```

### 3. 调整修复参数

**修复质量不佳**:
```python
# OpenCV 方法
result = cv2.inpaint(image, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
# 增加半径: 3 -> 5
# 改用 TELEA 算法

# IOPaint 方法（更好效果）
# 确保使用 LaMa 或 MAT 模型
remover.config['inpaint']['model'] = 'lama'
```

---

## 💡 最佳实践

### 1. 先测试小图

```python
# 调整参数时，先用小图测试
test_image = image[:100, :200]  # 裁剪测试区域
```

### 2. 可视化 Mask

```python
# 查看 mask 覆盖范围
mask_vis = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
overlay = cv2.addWeighted(image, 0.7, mask_vis, 0.3, 0)
cv2.imwrite("mask_check.png", overlay)
```

### 3. 分步处理

```python
# 1. 先检测
text_boxes = remover.detector.detect(image_rgb)
print(f"检测到: {text_boxes}")

# 2. 再扩展
expanded = expand_boxes(text_boxes, padding=25)
print(f"扩展后: {expanded}")

# 3. 最后修复
result = process(image, expanded)
```

---

## 📊 实际案例

### 案例: "AI生成" 水印

**图片信息**:
- 尺寸: 164x65 像素
- 水印位置: 左上角
- 水印内容: "AI生成" + 矩形框

**处理参数**:
```python
# 水印区域
x1, y1, x2, y2 = 50, 5, 190, 40

# 膨胀参数
kernel_size = (7, 7)
iterations = 2

# 模糊参数
blur_kernel = (5, 5)

# 修复半径
inpaint_radius = 3
```

**处理效果**: ✅ 水印完全去除，背景自然

---

## ⚠️ 常见问题

### Q1: 水印没有完全去除？

**解决方案**:
1. 增加扩展范围: `expand_pixels = 30`
2. 增加膨胀次数: `iterations = 3`
3. 手动指定更大的区域

### Q2: 修复后有明显痕迹？

**解决方案**:
1. 使用 IOPaint 代替 OpenCV: `model='lama'`
2. 增加修复半径: `inpaintRadius=5`
3. 尝试不同的修复模型: `lama`, `mat`, `ldm`

### Q3: 如何处理多个水印？

**解决方案**:
```python
# 检测所有水印
all_boxes = remover.detector.detect(image_rgb)

# 分别扩展
expanded_boxes = [expand_box(box, 25) for box in all_boxes]

# 一次性修复
mask = remover.mask_generator.generate(image_rgb, expanded_boxes)
result = remover.inpainter.inpaint(image_rgb, mask)
```

### Q4: 矩形框颜色特殊怎么办？

**解决方案**:
```python
# 使用颜色检测
frame_detector = FramedWatermarkDetector()
boxes = frame_detector.detect_by_color(
    image,
    text_boxes,
    color_range=((200, 200, 200), (255, 255, 255))  # 白色
)
```

---

## 🚀 快速命令

```bash
# 1. 使用示例脚本（推荐）
cd examples
python framed_watermark_example.py

# 2. 使用命令行工具
python main.py remove -i input.png -o output.png

# 3. 自定义处理
python -c "
import cv2
import numpy as np

image = cv2.imread('input.png')
mask = np.zeros(image.shape[:2], dtype=np.uint8)
cv2.rectangle(mask, (50, 5), (190, 40), 255, -1)
mask = cv2.dilate(mask, np.ones((7,7), np.uint8), iterations=2)
result = cv2.inpaint(image, mask, 3, cv2.INPAINT_NS)
cv2.imwrite('output.png', result)
"
```

---

## 📚 相关文档

- **示例代码**: `examples/framed_watermark_example.py`
- **增强检测器**: `src/framed_watermark_detector.py`
- **主文档**: `README.md`

---

## 💯 总结

对于 "AI生成" 这种**带矩形框的水印**:

1. ⭐ **推荐**: 方法1（快速处理）- 简单高效
2. 🔄 **备选**: 方法2（自动检测）- 适合批量
3. 🎯 **精确**: 方法3（增强检测）- 复杂水印
4. ✋ **兜底**: 方法4（手动指定）- 完全控制

**关键点**:
- 扩展检测区域以包含矩形框
- 适当膨胀和模糊 mask 边缘
- 选择合适的修复算法

立即尝试：
```bash
python examples/framed_watermark_example.py
```
