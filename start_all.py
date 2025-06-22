#!/usr/bin/env python3
"""
一键启动所有服务脚本
"""
import os
import sys
import subprocess
import threading
import time
from pathlib import Path

def start_backend():
    """启动后端服务"""
    try:
        subprocess.run([sys.executable, "start_backend.py"])
    except Exception as e:
        print(f"[主启动] 后端启动失败: {e}")

def start_frontend():
    """启动前端服务"""
    try:
        # 等待后端启动
        time.sleep(3)
        subprocess.run([sys.executable, "start_frontend.py"])
    except Exception as e:
        print(f"[主启动] 前端启动失败: {e}")

def main():
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("=" * 60)
    print("         🚀 Chat-AI 项目启动器")
    print("=" * 60)
    print()
    
    print("[主启动] 正在启动所有服务...")
    print("[主启动] 后端服务: http://localhost:8000")
    print("[主启动] 前端服务: http://localhost:8501")
    print()
    print("💡 提示:")
    print("  - 按 Ctrl+C 停止所有服务")
    print("  - 后端API文档: http://localhost:8000/docs")
    print("  - 前端界面: http://localhost:8501")
    print()
    print("-" * 60)
    
    try:
        # 创建线程启动服务
        backend_thread = threading.Thread(target=start_backend, daemon=True)
        frontend_thread = threading.Thread(target=start_frontend, daemon=True)
        
        # 启动后端
        print("[主启动] 🔧 启动后端服务...")
        backend_thread.start()
        
        # 启动前端
        print("[主启动] 🎨 启动前端服务...")
        frontend_thread.start()
        
        # 等待线程结束
        backend_thread.join()
        frontend_thread.join()
        
    except KeyboardInterrupt:
        print("\n[主启动] 📴 正在停止所有服务...")
        print("[主启动] ✅ 服务已停止")
    except Exception as e:
        print(f"[主启动] ❌ 启动失败: {e}")

if __name__ == "__main__":
    main()