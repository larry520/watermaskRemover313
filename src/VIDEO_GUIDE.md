# 视频去水印功能文档

## 📹 功能概述

视频去水印功能通过逐帧处理视频，自动检测并去除每一帧中的水印，然后重新合成为视频文件。

### ✨ 主要特性

- ✅ **自动处理**: 逐帧自动去除水印
- ✅ **保留音频**: 支持保留原视频音频轨道
- ✅ **跳帧加速**: 可选跳帧处理提升速度
- ✅ **自适应检测**: 支持水印位置变化的视频
- ✅ **片段处理**: 可指定时间范围处理
- ✅ **质量控制**: 多种质量选项
- ✅ **进度显示**: 实时显示处理进度
- ✅ **批量处理**: 支持批量处理多个视频

---

## 🚀 快速开始

### 命令行使用

```bash
# 处理整个视频
python main.py video -i input.mp4 -o output.mp4

# 处理视频片段
python main.py video -i input.mp4 -o output.mp4 -s 10 -e 30

# 跳帧加速
python main.py video -i input.mp4 -o output.mp4 -k 2 -q medium

# 自适应检测
python main.py video -i input.mp4 -o output.mp4 -a

# 查看视频信息
python main.py video-info -i input.mp4
```

### Python API 使用

```python
from src.watermark_remover import WatermarkRemover
from src.video_processor import VideoProcessor

# 初始化
remover = WatermarkRemover()
processor = VideoProcessor(remover)

# 基本处理
result = processor.process_video(
    input_path="input.mp4",
    output_path="output.mp4"
)

# 高级选项
result = processor.process_video(
    input_path="input.mp4",
    output_path="output.mp4",
    start_time=10.0,      # 开始时间（秒）
    end_time=30.0,        # 结束时间（秒）
    skip_frames=2,        # 跳帧数
    quality='high',       # 质量
    keep_audio=True       # 保留音频
)
```

---

## 📖 详细用法

### 1. 基本视频处理

```python
from src.watermark_remover import WatermarkRemover
from src.video_processor import VideoProcessor

remover = WatermarkRemover()
processor = VideoProcessor(remover)

result = processor.process_video(
    input_path="input_video.mp4",
    output_path="output_video.mp4",
    keep_audio=True
)

print(f"处理完成: {result['processed_frames']} 帧")
```

### 2. 处理视频片段

```python
# 只处理 10-30 秒的片段
result = processor.process_video(
    input_path="input.mp4",
    output_path="output_clip.mp4",
    start_time=10.0,  # 从第 10 秒开始
    end_time=30.0,    # 到第 30 秒结束
    keep_audio=True
)
```

### 3. 跳帧加速处理

```python
# 每 2 帧处理 1 帧（速度提升约 2 倍）
result = processor.process_video(
    input_path="input.mp4",
    output_path="output_fast.mp4",
    skip_frames=2,      # 跳帧数
    quality='medium'    # 降低质量进一步提速
)
```

**跳帧说明**:
- `skip_frames=1`: 处理所有帧（最慢，质量最好）
- `skip_frames=2`: 每 2 帧处理 1 帧（速度提升 2 倍）
- `skip_frames=3`: 每 3 帧处理 1 帧（速度提升 3 倍）

### 4. 自适应检测

适用于水印位置会变化的视频：

```python
# 每 30 帧重新检测一次水印位置
result = processor.process_video_adaptive(
    input_path="input.mp4",
    output_path="output_adaptive.mp4",
    detection_interval=30,  # 检测间隔（帧数）
    quality='high'
)
```

### 5. 质量控制

```python
# 高质量输出（速度慢，文件大）
result = processor.process_video(
    input_path="input.mp4",
    output_path="output_hq.mp4",
    skip_frames=1,
    quality='high'
)

# 中等质量（推荐）
result = processor.process_video(
    input_path="input.mp4",
    output_path="output_mq.mp4",
    skip_frames=2,
    quality='medium'
)

# 低质量（速度快，文件小）
result = processor.process_video(
    input_path="input.mp4",
    output_path="output_lq.mp4",
    skip_frames=3,
    quality='low'
)
```

### 6. 不保留音频

```python
result = processor.process_video(
    input_path="input.mp4",
    output_path="output_no_audio.mp4",
    keep_audio=False  # 不保留音频
)
```

### 7. 进度回调

```python
def progress_callback(current, total, message):
    percentage = (current / total) * 100
    print(f"\r{message} - {percentage:.1f}%", end='')

result = processor.process_video(
    input_path="input.mp4",
    output_path="output.mp4",
    progress_callback=progress_callback
)
```

### 8. 获取视频信息

```python
info = processor.get_video_info("input.mp4")

print(f"分辨率: {info['resolution']}")
print(f"帧率: {info['fps']:.2f} fps")
print(f"时长: {info['duration']:.2f} 秒")
print(f"总帧数: {info['total_frames']}")
```

### 9. 提取视频帧

```python
# 提取关键帧到目录
frames = processor.extract_frames(
    video_path="input.mp4",
    output_dir="./frames",
    interval=30,      # 每 30 帧提取一张
    max_frames=100    # 最多提取 100 张
)

print(f"提取了 {len(frames)} 帧")
```

### 10. 批量处理视频

```python
from pathlib import Path
from tqdm import tqdm

input_dir = Path("./input_videos")
output_dir = Path("./output_videos")
output_dir.mkdir(exist_ok=True)

video_files = list(input_dir.glob("*.mp4"))

for video_file in tqdm(video_files):
    output_file = output_dir / video_file.name
    try:
        processor.process_video(
            video_file,
            output_file,
            skip_frames=2,
            quality='medium'
        )
    except Exception as e:
        print(f"处理失败: {video_file.name}")
```

---

## 🔧 命令行选项

### video 命令

```bash
python main.py video [OPTIONS]

选项:
  -i, --input PATH          输入视频路径 [必需]
  -o, --output PATH         输出视频路径 [必需]
  -c, --config PATH         配置文件路径
  -s, --start FLOAT         开始时间（秒）
  -e, --end FLOAT           结束时间（秒）
  -k, --skip-frames INT     跳帧数（默认: 1）
  -q, --quality [high|medium|low]  输出质量（默认: high）
  --no-audio                不保留音频
  -a, --adaptive            使用自适应检测
```

### video-info 命令

```bash
python main.py video-info -i input.mp4
```

---

## 🎯 使用场景

### 场景 1: 短视频处理

```bash
# 1-2 分钟的短视频，追求质量
python main.py video -i short.mp4 -o output.mp4 -k 1 -q high
```

### 场景 2: 长视频处理

```bash
# 10+ 分钟的长视频，追求速度
python main.py video -i long.mp4 -o output.mp4 -k 3 -q medium
```

### 场景 3: 片段处理

```bash
# 只处理精彩片段
python main.py video -i full.mp4 -o highlight.mp4 -s 60 -e 120
```

### 场景 4: 水印位置变化

```bash
# 使用自适应检测
python main.py video -i dynamic.mp4 -o output.mp4 -a
```

---

## ⚙️ 配置说明

在 `config/config.yaml` 中配置视频处理参数：

```yaml
video:
  # 默认跳帧数
  default_skip_frames: 1
  
  # 默认输出质量
  default_quality: "high"
  
  # 是否保留音频
  keep_audio: true
  
  # 自适应检测间隔
  adaptive_detection_interval: 30
  
  # 临时文件目录
  temp_dir: "./temp_video"
```

---

## 📊 性能优化

### 1. 跳帧处理

**效果**: 速度提升 2-3 倍，质量轻微下降

```python
result = processor.process_video(
    input_path="input.mp4",
    output_path="output.mp4",
    skip_frames=2  # 速度提升 2 倍
)
```

### 2. 降低质量

**效果**: 文件更小，编码更快

```python
result = processor.process_video(
    input_path="input.mp4",
    output_path="output.mp4",
    quality='medium'  # 或 'low'
)
```

### 3. 组合优化

**推荐配置**（速度与质量平衡）:

```python
result = processor.process_video(
    input_path="input.mp4",
    output_path="output.mp4",
    skip_frames=2,      # 跳帧
    quality='medium'    # 中等质量
)
```

### 4. GPU 加速

确保在配置中启用 GPU：

```yaml
ocr:
  gpu: true

inpaint:
  device: "cuda"  # 或 "mps" (Mac)
```

---

## 🔍 故障排除

### 问题 1: 处理速度慢

**解决方案**:
1. 增加跳帧数: `skip_frames=2` 或 `3`
2. 降低质量: `quality='medium'` 或 `'low'`
3. 启用 GPU 加速
4. 处理视频片段而非整个视频

### 问题 2: 内存不足

**解决方案**:
1. 降低视频分辨率
2. 增加跳帧数
3. 分段处理长视频

### 问题 3: 音频丢失

**解决方案**:
1. 确保安装了 MoviePy: `pip install moviepy`
2. 检查 `keep_audio=True`
3. 查看日志确认音频处理状态

### 问题 4: 水印残留

**解决方案**:
1. 使用自适应检测: `-a` 或 `adaptive=True`
2. 降低跳帧数以处理更多帧
3. 调整配置文件中的检测参数

---

## 📝 最佳实践

1. **测试小片段**: 先处理 5-10 秒测试效果
2. **选择合适跳帧**: 平衡速度和质量
3. **保存原文件**: 处理前备份原视频
4. **监控进度**: 使用进度回调了解处理状态
5. **GPU 加速**: 优先使用 GPU 处理

---

## 🎓 技术细节

### 处理流程

```
1. 读取视频 → OpenCV VideoCapture
2. 检测水印 → 使用第一帧检测（或自适应检测）
3. 生成 Mask → 一次性生成或定期更新
4. 逐帧处理 → 应用 Inpainting
5. 合成视频 → OpenCV VideoWriter
6. 合并音频 → MoviePy（可选）
```

### 音频处理

- 使用 MoviePy 提取和合并音频
- 支持裁剪音频到指定时间范围
- 如果 MoviePy 不可用，将输出无音频视频

### 编码器

- 使用 MP4V 编码器
- 支持多种质量级别
- 可配置比特率

---

## 🌐 API 接口

### 上传视频

```bash
curl -X POST "http://localhost:8000/upload_video" \
  -F "file=@input.mp4" \
  -F "skip_frames=2" \
  -F "quality=high" \
  -F "keep_audio=true"
```

### 查询状态

```bash
curl "http://localhost:8000/status/{task_id}"
```

### 下载结果

```bash
curl "http://localhost:8000/download/{task_id}" -o result.mp4
```

### 获取视频信息

```bash
curl -X POST "http://localhost:8000/video_info" \
  -F "file=@input.mp4"
```

---

## 📚 示例代码

完整示例请参考 `examples/video_usage.py`，包含 12 个实用示例。

---

## ⚠️ 注意事项

1. **处理时间**: 视频处理比图片慢得多，长视频可能需要数小时
2. **存储空间**: 确保有足够空间存储临时文件和输出文件
3. **版权合规**: 仅处理有权处理的视频
4. **音频限制**: 某些音频格式可能不支持

---

## 💡 提示

- 先用小视频测试参数
- 长视频建议夜间处理
- 使用 GPU 可大幅提速
- 批量处理时监控资源使用

有问题请查看完整文档或提交 Issue！
