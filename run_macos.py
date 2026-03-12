#!/usr/bin/env python3
"""
macOS 应用启动脚本
自动启动 Web 服务并打开浏览器
"""
import sys
import os
import time
import webbrowser
from pathlib import Path


def get_app_path():
    """获取应用程序路径"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        return Path(sys._MEIPASS)
    else:
        # 开发环境
        return Path(__file__).parent


def main():
    """主函数"""
    # 获取应用路径
    app_path = get_app_path()
    
    # 设置工作目录
    os.chdir(app_path)
    
    print("=" * 60)
    print("🎨 水印去除工具")
    print("=" * 60)
    print(f"应用路径: {app_path}")
    print("启动中...")
    print()
    
    # 创建必要的目录
    (app_path / "uploads").mkdir(exist_ok=True)
    (app_path / "outputs").mkdir(exist_ok=True)
    
    # 启动 Web 服务
    try:
        # 导入并启动服务
        sys.path.insert(0, str(app_path))
        
        import uvicorn
        from app import app as fastapi_app
        
        print("🚀 正在启动 Web 服务...")
        print("📍 访问地址: http://localhost:8000")
        print()
        print("提示:")
        print("  - 浏览器会自动打开")
        print("  - 关闭此窗口将停止服务")
        print("  - 按 Ctrl+C 也可停止服务")
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
            fastapi_app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n\n服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n请检查:")
        print("  1. 是否已安装所有依赖")
        print("  2. 端口 8000 是否被占用")
        print("  3. 是否有足够的权限")
        input("\n按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()
