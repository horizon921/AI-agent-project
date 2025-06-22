#!/usr/bin/env python3
"""
启动前端服务脚本
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    # 确保在正确的目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("[启动前端] 正在启动Streamlit前端服务...")
    print(f"[启动前端] 工作目录: {project_root}")
    
    # 检查Python环境
    try:
        import streamlit
        print("[启动前端] ✓ 依赖检查通过")
    except ImportError as e:
        print(f"[启动前端] ❌ 依赖缺失: {e}")
        print("[启动前端] 请先安装前端依赖: pip install -r frontend/requirements.txt")
        return
    
    # 添加项目根目录到Python路径
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    try:
        # 启动Streamlit服务
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            "frontend/app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
        
        print("[启动前端] 启动命令:", " ".join(cmd))
        print("[启动前端] 服务地址: http://localhost:8501")
        print("-" * 50)
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n[启动前端] 服务已停止")
    except Exception as e:
        print(f"[启动前端] ❌ 启动失败: {e}")

if __name__ == "__main__":
    main()