# 水印去除系统

基于 **EasyOCR** 和 **IOPaint** 的智能水印去除工具，支持图片和视频。

## 🌟 特性

- ✅ **智能检测**: 使用 EasyOCR 自动识别水印位置
- ✅ **高质量修复**: 集成 IOPaint 多种修复模型（LaMa、MAT等）
- ✅ **图片处理**: 单张、批量处理图片
- ✅ **视频处理**: 逐帧去除视频水印，保留音频
- ✅ **灵活配置**: YAML 配置文件，可自定义检测和修复参数
- ✅ **多种接口**: 命令行、Python API、REST API
- ✅ **可视化**: 支持检测结果可视化
- ✅ **GPU 加速**: 支持 CUDA 和 MPS

## 📦 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd watermark-remover
```

### 2. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 下载模型（可选）

EasyOCR 和 IOPaint 会在首次运行时自动下载模型。

## 🚀 快速开始

### 方式 1: Web 浏览器界面 ⭐ 最简单

```bash
# 启动 Web 服务
python start_web.py

# 打开浏览器访问
http://localhost:8000
```

**Web 界面功能**:
- 🎨 美观的用户界面
- 📷 图片去水印
- 🎬 视频去水印
- ⚡ 快速视频处理
- 📦 批量处理
- 📊 实时进度显示
- 👆 拖拽上传文件

### 方式 2: 命令行

```bash
# 图片去水印
python main.py remove -i input.jpg -o output.jpg

# 批量处理图片
python main.py batch -i ./input_folder -o ./output_folder

# 视频去水印（标准方法）
python main.py video -i input.mp4 -o output.mp4

# 快速视频去水印（固定 Mask）⭐ 推荐
python main.py fast-video -i input.mp4 -o output.mp4

# 视频片段处理
python main.py video -i input.mp4 -o output.mp4 -s 10 -e 30

# 仅检测水印
python main.py detect -i input.jpg

# 查看视频信息
python main.py video-info -i input.mp4

# 查看系统信息
python main.py info
```

### 方式 3: Python 代码

**图片处理:**

```python
from src.watermark_remover import WatermarkRemover

# 初始化
remover = WatermarkRemover()

# 去除水印
remover.remove("input.jpg", "output.jpg")

# 批量处理
remover.batch_remove("./input_folder", "./output_folder")
```

**视频处理:**

```python
from src.watermark_remover import WatermarkRemover
from src.video_processor import VideoProcessor

# 初始化
remover = WatermarkRemover()
processor = VideoProcessor(remover)

# 处理视频
result = processor.process_video(
    input_path="input.mp4",
    output_path="output.mp4",
    skip_frames=2,      # 跳帧加速
    quality='high',     # 输出质量
    keep_audio=True     # 保留音频
)
```

### 方式 3: API 服务

```bash
# 启动服务
uvicorn api.app:app --reload

# 或使用启动脚本
python start_web.py
```

访问：
- **Web 界面**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **交互式文档**: http://localhost:8000/redoc

## 📖 使用示例

### 图片处理

#### 示例 1: 基本使用

```python
from src.watermark_remover import WatermarkRemover

remover = WatermarkRemover()
remover.remove("input.jpg", "output.jpg")
```

#### 示例 2: 带可视化

```python
remover = WatermarkRemover()
remover.remove(
    "input.jpg", 
    "output.jpg",
    visualize_detection=True  # 保存检测结果
)
```

#### 示例 3: 自定义配置

```python
# 修改 config/config.yaml
remover = WatermarkRemover(config_path="config/config.yaml")
remover.remove("input.jpg", "output.jpg")
```

#### 示例 4: 仅检测

```python
detections = remover.detect_only("input.jpg")
for det in detections:
    print(f"文字: {det['text']}, 置信度: {det['confidence']}")
```

#### 示例 5: 从数组处理

```python
import cv2
from utils.image_utils import ImageUtils

# 读取图片
image = ImageUtils.load_image_rgb("input.jpg")

# 处理
result, mask = remover.remove_from_array(image)

# 保存
ImageUtils.save_image(ImageUtils.rgb_to_bgr(result), "output.jpg")
```

### 视频处理

#### 示例 6: 基本视频处理

```python
from src.watermark_remover import WatermarkRemover
from src.video_processor import VideoProcessor

remover = WatermarkRemover()
processor = VideoProcessor(remover)

result = processor.process_video(
    input_path="input.mp4",
    output_path="output.mp4"
)
```

#### 示例 6.5: 快速视频处理（固定 Mask）⭐ 推荐

```python
from src.watermark_remover import WatermarkRemover
from src.fast_video_processor import FastVideoProcessor

remover = WatermarkRemover()
processor = FastVideoProcessor(remover)

# 方法1: 自动检测（从第一帧）
result = processor.process_video_with_fixed_mask(
    input_path="input.mp4",
    output_path="output.mp4",
    detect_from_first_frame=True  # 只检测一次
)

# 方法2: 手动指定（最快）
result = processor.process_video_with_fixed_mask(
    input_path="input.mp4",
    output_path="output.mp4",
    manual_box=(50, 10, 200, 80)  # 水印位置
)

# 速度提升 10-50 倍！
```

#### 示例 6.6: 多线程并行处理 🚀 最快

```python
from src.watermark_remover import WatermarkRemover
from src.parallel_video_processor import ParallelVideoProcessor

remover = WatermarkRemover()
processor = ParallelVideoProcessor(
    remover,
    num_workers=7  # 工作线程数
)

# 并行处理（速度提升 20-50 倍！）
result = processor.process_video_parallel(
    input_path="input.mp4",
    output_path="output.mp4",
    manual_box=(50, 10, 200, 80),
    batch_size=30  # 每批处理30帧
)

print(f"处理速度: {result['processing_speed']:.2f} fps")
# 典型结果: 40-50 fps（vs 单线程 1-2 fps）
```

#### 示例 7: 视频片段处理

```python
# 只处理 10-30 秒的片段
result = processor.process_video(
    input_path="input.mp4",
    output_path="clip.mp4",
    start_time=10.0,  # 开始时间
    end_time=30.0     # 结束时间
)
```

#### 示例 8: 跳帧加速

```python
# 每 2 帧处理 1 帧，速度提升 2 倍
result = processor.process_video(
    input_path="input.mp4",
    output_path="output.mp4",
    skip_frames=2,
    quality='medium'
)
```

#### 示例 9: 自适应检测

```python
# 适用于水印位置会变化的视频
result = processor.process_video_adaptive(
    input_path="input.mp4",
    output_path="output.mp4",
    detection_interval=30  # 每 30 帧重新检测
)
```

#### 示例 10: 获取视频信息

```python
info = processor.get_video_info("input.mp4")
print(f"分辨率: {info['resolution']}")
print(f"时长: {info['duration']:.2f} 秒")
```

**更多示例**: 参见 `examples/` 目录

## ⚙️ 配置说明

配置文件位于 `config/config.yaml`：

```yaml
# OCR 配置
ocr:
  languages: ['ch_sim', 'en']  # 支持的语言
  gpu: true                     # 是否使用 GPU
  min_confidence: 0.5           # 最小置信度

# Mask 生成配置
mask:
  expand_pixels: 5              # 边缘扩展像素
  enable_morphology: true       # 启用形态学处理
  dilate_iterations: 2          # 膨胀迭代次数

# 图像修复配置
inpaint:
  model: "lama"                 # 修复模型
  device: "cuda"                # 设备
  hd_strategy: "Resize"         # HD 策略
```

### 支持的修复模型

- **lama**: 快速、精准（推荐）
- **mat**: 适合大面积修复
- **ldm**: 基于扩散模型
- **fcf**: 快速卷积填充
- **manga**: 专门用于漫画
- **cv2**: OpenCV 修复（后备方案）

## 📊 API 接口

### 图片处理

**上传并处理**

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@input.jpg"
```

**仅检测**

```bash
curl -X POST "http://localhost:8000/detect" \
  -F "file=@input.jpg"
```

### 视频处理

**上传视频**

```bash
curl -X POST "http://localhost:8000/upload_video" \
  -F "file=@input.mp4" \
  -F "skip_frames=2" \
  -F "quality=high" \
  -F "keep_audio=true"
```

**获取视频信息**

```bash
curl -X POST "http://localhost:8000/video_info" \
  -F "file=@input.mp4"
```

### 通用接口

**查询任务状态**

```bash
curl "http://localhost:8000/status/{task_id}"
```

**下载结果**

```bash
curl "http://localhost:8000/download/{task_id}" \
  -o result.mp4
```

## 🎯 高级功能

### 批量处理脚本

参见 `examples/batch_process.py`：

- 顺序处理
- 并行处理
- 带过滤的处理
- 生成对比图
- 统计信息

### 自定义水印检测

修改 `config/config.yaml` 中的检测策略：

```yaml
detection:
  position_filter:
    enabled: true
    areas: ['corners', 'edges']  # 检测区域
  
  text_filter:
    enabled: true
    min_text_length: 1
    max_text_length: 50
```

## 🔧 系统要求

- **Python**: 3.8+
- **内存**: 建议 8GB+
- **GPU**: 可选，NVIDIA CUDA 或 Apple MPS
- **系统**: Windows, macOS, Linux

## 📝 项目结构

```
watermark-remover/
├── config/              # 配置文件
├── src/                 # 核心代码
│   ├── ocr_detector.py
│   ├── mask_generator.py
│   ├── inpainter.py
│   └── watermark_remover.py
├── api/                 # API 服务
├── utils/               # 工具类
├── examples/            # 使用示例
├── main.py             # 命令行入口
└── requirements.txt    # 依赖
```

## 🐛 故障排除

### 问题 1: CUDA out of memory

**解决**: 降低图片分辨率或在配置中设置较小的 `hd_strategy_resize_limit`

### 问题 2: EasyOCR 模型下载失败

**解决**: 手动下载模型到 `~/.EasyOCR/model/`

### 问题 3: IOPaint 未检测到 GPU

**解决**: 检查 PyTorch CUDA 安装：

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系

如有问题，请提交 Issue。

## 🙏 致谢

- [EasyOCR](https://github.com/JaidedAI/EasyOCR) - OCR 文字检测
- [IOPaint](https://github.com/Sanster/IOPaint) - AI 图像修复
- [OpenCV](https://opencv.org/) - 图像和视频处理
- [MoviePy](https://github.com/Zulko/moviepy) - 视频编辑

---

## 📚 相关文档

- **完整文档**: [README.md](README.md)
- **快速开始**: [QUICKSTART.md](QUICKSTART.md)
- **Web 界面**: [WEB_GUIDE.md](WEB_GUIDE.md) ⭐ 新增
- **视频功能**: [VIDEO_GUIDE.md](VIDEO_GUIDE.md)
- **快速视频**: [FAST_VIDEO_GUIDE.md](FAST_VIDEO_GUIDE.md)
- **带框水印**: [FRAMED_WATERMARK_GUIDE.md](FRAMED_WATERMARK_GUIDE.md)
- **架构文档**: [ARCHITECTURE_README.md](ARCHITECTURE_README.md)
- **项目总结**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
