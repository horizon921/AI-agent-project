#!/usr/bin/env python3
"""
启动后端服务脚本
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    # 确保在正确的目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("[启动后端] 正在启动FastAPI后端服务...")
    print(f"[启动后端] 工作目录: {project_root}")
    
    # 检查Python环境
    try:
        import uvicorn
        import fastapi
        print("[启动后端] ✓ 依赖检查通过")
    except ImportError as e:
        print(f"[启动后端] ❌ 依赖缺失: {e}")
        print("[启动后端] 请先安装后端依赖: pip install -r backend/requirements.txt")
        return
    
    # 添加项目根目录到Python路径
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    try:
        # 启动FastAPI服务
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "backend.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ]
        
        print("[启动后端] 启动命令:", " ".join(cmd))
        print("[启动后端] 服务地址: http://localhost:8000")
        print("[启动后端] API文档: http://localhost:8000/docs")
        print("-" * 50)
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n[启动后端] 服务已停止")
    except Exception as e:
        print(f"[启动后端] ❌ 启动失败: {e}")

if __name__ == "__main__":
    main()