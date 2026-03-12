#!/usr/bin/env python3
"""
Web 界面启动脚本
"""
import sys
from pathlib import Path
import time
import webbrowser

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """启动 Web 服务"""
    import uvicorn
    from app import app
    
    print("=" * 60)
    print("🎨 智能水印去除工具 - Web 界面")
    print("=" * 60)
    print()
    print("正在启动 Web 服务...")
    print()
    print("访问地址:")
    print("  🌐 http://localhost:8000")
    print("  🌐 http://127.0.0.1:8000")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    print()
    # 延迟后打开浏览器
    import threading
    def open_browser():
        time.sleep(2)
        webbrowser.open("http://localhost:8000")

    threading.Thread(target=open_browser, daemon=True).start()
    # 启动服务
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    main()
