"""
FastAPI 服务 - 完整版
提供 REST API 接口和 Web 界面
支持本地文件夹打开功能
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import Optional, List
import uuid
import shutil
from pathlib import Path
import asyncio
from datetime import datetime
import platform
import subprocess
import os

import sys
sys.path.append(str(Path(__file__).parent.parent))

# 初始化 FastAPI
app = FastAPI(
    title="水印去除 API",
    description="使用 EasyOCR + IOPaint 去除图片和视频水印",
    version="2.0.0"
)

# 添加 CORS 支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
UPLOAD_DIR = Path("./uploads")
OUTPUT_DIR = Path("./outputs")
WEB_DIR = Path("./web")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 挂载静态文件
if WEB_DIR.exists():
    app.mount("/web/static", StaticFiles(directory="web/static"), name="static")

# 任务状态存储
tasks = {}

# 延迟加载模块
remover = None

def get_remover():
    """延迟初始化水印去除器"""
    global remover
    if remover is None:
        from src.watermark_remover import WatermarkRemover
        remover = WatermarkRemover(config_path='config.yaml')
    return remover


@app.get("/", response_class=HTMLResponse)
async def root():
    """返回 Web 界面"""
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    
    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html><head><title>水印去除 API</title></head>
<body style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
    <h1>🎨 水印去除 API</h1>
    <p>✓ 服务运行中</p>
    <p>⚠ Web 界面文件未找到: {WEB_DIR}</p>
    <h2>可用端点：</h2>
    <ul>
        <li><a href="/docs">API 文档 (Swagger)</a></li>
        <li><a href="/redoc">API 文档 (ReDoc)</a></li>
        <li><a href="/health">健康检查</a></li>
    </ul>
</body></html>
    """)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "web_dir_exists": WEB_DIR.exists(),
        "output_dir": str(OUTPUT_DIR.absolute())
    }


@app.post("/upload")
async def upload_image(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """上传图片并去除水印"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只支持图片文件")
    
    task_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{task_id}_{file.filename}"
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    tasks[task_id] = {
        "type": "image",
        "status": "pending",
        "message": "图片已上传，等待处理",
        "input_path": str(input_path),
        "created_at": datetime.now().isoformat()
    }
    
    background_tasks.add_task(process_image_task, task_id, input_path)
    
    return {
        "task_id": task_id,
        "message": "图片已上传，开始处理",
        "status_url": f"/status/{task_id}"
    }


def process_image_task(task_id: str, input_path: Path):
    """后台处理图片"""
    try:
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["message"] = "正在处理图片..."
        
        output_path = OUTPUT_DIR / f"{task_id}_result.png"
        r = get_remover()
        r.remove(str(input_path), str(output_path))
        
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["message"] = "图片处理完成"
        tasks[task_id]["output_path"] = str(output_path)
        tasks[task_id]["result_url"] = f"/download/{task_id}"
        tasks[task_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["message"] = f"处理失败: {str(e)}"
        tasks[task_id]["completed_at"] = datetime.now().isoformat()


@app.post("/upload_video")
async def upload_video(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    keep_audio: bool = Form(True),
    box: Optional[str] = Form(None),
    use_fast: bool = Form(False),
    frame_by_frame: bool = Form(True)
):
    """
    上传视频并去除水印
    
    Args:
        file: 视频文件
        keep_audio: 是否保留音频
        box: 手动指定区域（快速模式）
        use_fast: 是否使用快速模式
        frame_by_frame: 是否逐帧检测水印
        
    Returns:
        任务 ID
    """
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="只支持视频文件")
    
    task_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{task_id}_{file.filename}"
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    tasks[task_id] = {
        "type": "video",
        "status": "pending",
        "message": "视频已上传，等待处理",
        "input_path": str(input_path),
        "original_filename": file.filename,
        "created_at": datetime.now().isoformat()
    }
    
    # 解析手动区域
    manual_box = None
    if box:
        try:
            coords = [int(x.strip()) for x in box.split(',')]
            if len(coords) == 4:
                manual_box = tuple(coords)
        except:
            pass
    
    # 选择处理模式（不传递quality和skip_frames参数，使用默认值）
    if frame_by_frame:
        # 逐帧检测模式（最精确，最慢）
        background_tasks.add_task(
            process_video_frame_by_frame_task,
            task_id, input_path, keep_audio
        )

    else:
        # 标准模式（自适应检测）
        background_tasks.add_task(
            process_video_task,
            task_id, input_path, keep_audio
        )
    
    return {
        "task_id": task_id,
        "message": "视频已上传，开始处理",
        "status_url": f"/status/{task_id}"
    }


def process_video_task(task_id: str, input_path: Path, keep_audio: bool):
    """后台处理视频（标准模式）"""
    try:
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["message"] = "正在处理视频（标准模式）..."
        
        output_path = OUTPUT_DIR / f"{task_id}_result.mp4"
        
        from src.video_processor import VideoProcessor
        r = get_remover()
        processor = VideoProcessor(r, r.config)
        
        result = processor.process_video(
            input_path, output_path,
            keep_audio=keep_audio,
            frame_by_frame=False
        )
        
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["message"] = "视频处理完成"
        tasks[task_id]["output_path"] = str(output_path)
        tasks[task_id]["result_url"] = f"/download/{task_id}"
        tasks[task_id]["result_info"] = result
        tasks[task_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["message"] = f"处理失败: {str(e)}"
        tasks[task_id]["completed_at"] = datetime.now().isoformat()


def process_fast_video_task(task_id: str, input_path: Path, manual_box, keep_audio: bool):
    """后台处理视频（快速模式）"""
    try:
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["message"] = "正在快速处理视频..."
        
        output_path = OUTPUT_DIR / f"{task_id}_result.mp4"
        
        from src.fast_video_processor import FastVideoProcessor
        r = get_remover()
        processor = FastVideoProcessor(r)
        
        result = processor.process_video_with_fixed_mask(
            input_path, output_path,
            manual_box=manual_box,
            detect_from_first_frame=(manual_box is None),
            quality=None,  # None表示自动匹配原视频质量
            keep_audio=keep_audio
        )
        
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["message"] = "视频处理完成（快速模式）"
        tasks[task_id]["output_path"] = str(output_path)
        tasks[task_id]["result_url"] = f"/download/{task_id}"
        tasks[task_id]["result_info"] = result
        tasks[task_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["message"] = f"处理失败: {str(e)}"
        tasks[task_id]["completed_at"] = datetime.now().isoformat()


def process_video_frame_by_frame_task(task_id: str, input_path: Path, keep_audio: bool):
    """后台处理视频（逐帧检测模式）"""
    try:
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["message"] = "正在逐帧检测并处理视频..."
        
        output_path = OUTPUT_DIR / f"{task_id}_result.mp4"
        
        from src.video_processor import VideoProcessor
        r = get_remover()
        processor = VideoProcessor(r, r.config)
        
        # 使用逐帧检测（frame_by_frame=True, skip_frames=1）
        result = processor.process_video(
            input_path, output_path,
            keep_audio=keep_audio,
            frame_by_frame=True  # 启用自适应检测（逐帧）
        )
        
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["message"] = "视频处理完成（逐帧检测）"
        tasks[task_id]["output_path"] = str(output_path)
        tasks[task_id]["result_url"] = f"/download/{task_id}"
        tasks[task_id]["result_info"] = result
        tasks[task_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["message"] = f"处理失败: {str(e)}"
        tasks[task_id]["completed_at"] = datetime.now().isoformat()


@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task_data = tasks[task_id].copy()  # 拷贝一份，避免修改原始数据

    # 递归清洗数据，确保没有不可序列化的对象
    def sanitize(obj):
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize(i) for i in obj]
        elif hasattr(obj, "__str__") and not isinstance(obj, (int, float, bool, type(None))):
            # 将 Path 对象、Numpy 浮点数等全部转为 字符串 或 原生类型
            if "numpy" in str(type(obj)):
                return obj.item()  # Numpy 转原生
            return str(obj)
        return obj

    safe_data = sanitize(task_data)

    return JSONResponse(content=jsonable_encoder(safe_data))


@app.get("/download/{task_id}")
async def download_result(task_id: str):
    """下载处理结果"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="任务未完成")
    
    if "output_path" not in task:
        raise HTTPException(status_code=404, detail="结果文件不存在")
    
    output_path = Path(task["output_path"])
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="结果文件不存在")
    
    return FileResponse(
        output_path,
        media_type="application/octet-stream",
        filename=output_path.name
    )


@app.get("/open_folder")
async def open_output_folder():
    """打开输出文件夹（本地使用）"""
    try:
        output_dir = OUTPUT_DIR.absolute()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        system = platform.system()
        
        if system == "Windows":
            os.startfile(str(output_dir))
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(output_dir)])
        else:  # Linux
            subprocess.run(["xdg-open", str(output_dir)])
        
        return {
            "success": True,
            "message": "文件夹已打开",
            "path": str(output_dir)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"打开文件夹失败: {str(e)}",
            "path": str(OUTPUT_DIR.absolute())
        }


@app.get("/open_file/{task_id}")
async def open_result_file(task_id: str):
    """打开结果文件所在文件夹并选中文件"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="任务未完成")
    
    if "output_path" not in task:
        raise HTTPException(status_code=404, detail="结果文件不存在")
    
    try:
        output_path = Path(task["output_path"]).absolute()
        
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="结果文件不存在")
        
        system = platform.system()
        
        if system == "Windows":
            # Windows - 打开文件夹并选中文件
            subprocess.run(["explorer", "/select,", str(output_path)])
        elif system == "Darwin":
            # macOS - 在 Finder 中显示文件
            subprocess.run(["open", "-R", str(output_path)])
        else:
            # Linux - 打开包含文件的文件夹
            subprocess.run(["xdg-open", str(output_path.parent)])
        
        return {
            "success": True,
            "message": "文件夹已打开",
            "path": str(output_path)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"打开失败: {str(e)}"
        }


@app.post("/detect")
async def detect_watermark(file: UploadFile = File(...)):
    """仅检测水印（不修复）"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只支持图片文件")
    
    temp_id = str(uuid.uuid4())
    temp_path = UPLOAD_DIR / f"temp_{temp_id}_{file.filename}"
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        r = get_remover()
        detections = r.detect_only(str(temp_path))
        
        return {
            "total": len(detections),
            "watermarks": detections
        }
        
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.delete("/cleanup/{task_id}")
async def cleanup_task(task_id: str):
    """清理任务文件"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    
    input_path = Path(task["input_path"])
    if input_path.exists():
        input_path.unlink()
    
    if "output_path" in task:
        output_path = Path(task["output_path"])
        if output_path.exists():
            output_path.unlink()
    
    del tasks[task_id]
    
    return {"message": "任务已清理"}


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🎨 水印去除 API 服务")
    print("=" * 60)
    print(f"输出目录: {OUTPUT_DIR.absolute()}")
    print("访问: http://localhost:8000")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8000)
