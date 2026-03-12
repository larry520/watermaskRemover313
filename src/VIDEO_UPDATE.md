# 🎬 视频去水印功能 - 更新说明

## ✨ 新增功能

### 1. 视频水印去除

现在支持对视频文件进行逐帧去水印处理！

**核心特性**:
- 🎥 逐帧自动去水印
- 🔊 保留原视频音频
- ⚡ 跳帧加速处理
- 🎯 自适应水印检测
- 📐 片段时间范围处理
- 🎨 多种质量选项

### 2. 新增模块

#### VideoProcessor 类 (`src/video_processor.py`)

```python
from src.video_processor import VideoProcessor

processor = VideoProcessor(watermark_remover)

# 处理视频
result = processor.process_video(
    input_path="input.mp4",
    output_path="output.mp4",
    skip_frames=2,
    quality='high',
    keep_audio=True
)
```

**主要方法**:
- `process_video()` - 基本视频处理
- `process_video_adaptive()` - 自适应检测处理
- `extract_frames()` - 提取视频帧
- `get_video_info()` - 获取视频信息

### 3. 命令行支持

新增两个命令：

```bash
# 处理视频
python main.py video -i input.mp4 -o output.mp4

# 查看视频信息
python main.py video-info -i input.mp4
```

**完整选项**:
```bash
python main.py video \
  -i input.mp4 \        # 输入视频
  -o output.mp4 \       # 输出视频
  -s 10 \               # 开始时间（秒）
  -e 30 \               # 结束时间（秒）
  -k 2 \                # 跳帧数（加速）
  -q high \             # 质量 (high/medium/low)
  --no-audio \          # 不保留音频（可选）
  -a                    # 自适应检测（可选）
```

### 4. REST API 支持

新增视频处理 API 端点：

**上传视频**:
```bash
POST /upload_video
```

**获取视频信息**:
```bash
POST /video_info
```

### 5. 配置选项

在 `config/config.yaml` 新增视频配置：

```yaml
video:
  default_skip_frames: 1
  default_quality: "high"
  keep_audio: true
  adaptive_detection_interval: 30
  temp_dir: "./temp_video"
```

---

## 📖 使用示例

### 基本用法

```python
from src.watermark_remover import WatermarkRemover
from src.video_processor import VideoProcessor

# 初始化
remover = WatermarkRemover()
processor = VideoProcessor(remover)

# 处理视频
result = processor.process_video(
    input_path="input.mp4",
    output_path="output.mp4"
)

print(f"处理完成: {result['processed_frames']} 帧")
```

### 快速处理（跳帧）

```python
# 速度提升 2-3 倍
result = processor.process_video(
    input_path="input.mp4",
    output_path="output.mp4",
    skip_frames=2,      # 每 2 帧处理 1 帧
    quality='medium'    # 中等质量
)
```

### 处理片段

```python
# 只处理 10-30 秒
result = processor.process_video(
    input_path="input.mp4",
    output_path="clip.mp4",
    start_time=10.0,
    end_time=30.0
)
```

### 自适应检测

```python
# 水印位置变化的视频
result = processor.process_video_adaptive(
    input_path="input.mp4",
    output_path="output.mp4",
    detection_interval=30  # 每 30 帧检测一次
)
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install moviepy ffmpeg-python imageio imageio-ffmpeg
```

### 2. 处理第一个视频

```bash
python main.py video -i test.mp4 -o result.mp4
```

### 3. 查看结果

视频会保存为 `result.mp4`，包含去除水印后的内容和原始音频。

---

## ⚙️ 性能优化建议

### 1. 跳帧处理

**推荐设置**: `skip_frames=2`

- 速度提升约 2 倍
- 质量影响较小
- 适合大多数场景

### 2. 质量选择

| 质量 | 速度 | 文件大小 | 推荐场景 |
|------|------|----------|----------|
| high | 慢 | 大 | 短视频、重要内容 |
| medium | 中 | 中 | **推荐默认** |
| low | 快 | 小 | 预览、测试 |

### 3. GPU 加速

确保启用 GPU：

```yaml
ocr:
  gpu: true

inpaint:
  device: "cuda"
```

### 4. 分段处理

长视频可以分段处理：

```bash
# 处理前 5 分钟
python main.py video -i long.mp4 -o part1.mp4 -e 300

# 处理 5-10 分钟
python main.py video -i long.mp4 -o part2.mp4 -s 300 -e 600
```

---

## 📊 性能参考

测试环境：
- GPU: NVIDIA RTX 3080
- 视频: 1920x1080, 30fps
- 模型: LaMa

| 配置 | 处理速度 | 说明 |
|------|----------|------|
| skip_frames=1, high | ~0.5 fps | 最高质量 |
| skip_frames=2, medium | ~1 fps | **推荐配置** |
| skip_frames=3, low | ~1.5 fps | 快速预览 |

---

## 🎯 使用场景

### 场景 1: 短视频（1-3 分钟）

```bash
# 追求质量
python main.py video -i short.mp4 -o output.mp4 -k 1 -q high
```

### 场景 2: 长视频（10+ 分钟）

```bash
# 追求速度
python main.py video -i long.mp4 -o output.mp4 -k 3 -q medium
```

### 场景 3: 精彩片段

```bash
# 提取并处理
python main.py video -i full.mp4 -o highlight.mp4 -s 60 -e 120
```

### 场景 4: 动态水印

```bash
# 使用自适应检测
python main.py video -i dynamic.mp4 -o output.mp4 -a
```

---

## 📚 文档

详细文档请查看：

- **视频功能指南**: [VIDEO_GUIDE.md](VIDEO_GUIDE.md)
- **使用示例**: [examples/video_usage.py](examples/video_usage.py)
- **API 文档**: http://localhost:8000/docs

---

## 🔍 常见问题

### Q: 处理速度慢怎么办？

**A**: 
1. 增加跳帧: `skip_frames=2` 或 `3`
2. 降低质量: `quality='medium'`
3. 启用 GPU
4. 处理片段而非整个视频

### Q: 音频丢失？

**A**:
1. 安装 MoviePy: `pip install moviepy`
2. 确保 `keep_audio=True`
3. 检查原视频是否有音频

### Q: 水印没有完全去除？

**A**:
1. 使用自适应检测: `-a`
2. 减少跳帧数
3. 调整检测参数

### Q: 支持哪些视频格式？

**A**: 
支持所有 OpenCV 支持的格式，包括：
- MP4
- AVI
- MOV
- MKV
- 等

---

## 🎓 学习资源

### 示例代码

`examples/video_usage.py` 包含 12 个完整示例：

1. 基本视频处理
2. 视频片段处理
3. 跳帧处理
4. 自适应检测
5. 获取视频信息
6. 提取帧
7. 自定义配置
8. 进度回调
9. 批量处理
10. 无音频处理
11. 高质量输出
12. 生成对比视频

### API 示例

```python
# 完整的处理流程
from src.watermark_remover import WatermarkRemover
from src.video_processor import VideoProcessor

# 1. 初始化
remover = WatermarkRemover()
processor = VideoProcessor(remover)

# 2. 查看视频信息
info = processor.get_video_info("input.mp4")
print(f"时长: {info['duration']:.2f} 秒")

# 3. 处理视频
result = processor.process_video(
    input_path="input.mp4",
    output_path="output.mp4",
    skip_frames=2,
    quality='high',
    keep_audio=True
)

# 4. 查看结果
print(f"处理完成!")
print(f"处理帧数: {result['processed_frames']}")
print(f"输出路径: {result['output_path']}")
```

---

## 💡 最佳实践

1. **先测试小片段**
   ```bash
   python main.py video -i test.mp4 -o test_out.mp4 -e 10
   ```

2. **选择合适的跳帧数**
   - 质量优先: `skip_frames=1`
   - 平衡: `skip_frames=2` ⭐
   - 速度优先: `skip_frames=3`

3. **监控处理进度**
   使用进度回调或查看终端输出

4. **保存原文件**
   处理前备份原视频

5. **批量处理优化**
   ```python
   # 使用多进程或分时段处理
   for video in videos:
       processor.process_video(
           video,
           output_path,
           skip_frames=2,
           quality='medium'
       )
   ```

---

## 🎉 总结

视频去水印功能让水印去除系统更加完整和实用！

**核心优势**:
- ✅ 自动化处理，无需手动标注
- ✅ 保留音频，体验完整
- ✅ 灵活配置，适应不同场景
- ✅ 多种接口，易于集成

立即尝试：

```bash
python main.py video -i your_video.mp4 -o result.mp4
```

有问题欢迎提 Issue！
