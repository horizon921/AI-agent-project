#!/usr/bin/env python3
"""
依赖安装脚本
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """运行命令并处理结果"""
    print(f"[安装] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"[安装] ✓ {description}完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[安装] ❌ {description}失败:")
        print(f"[安装] 错误信息: {e.stderr}")
        return False

def check_conda_env():
    """检查conda环境"""
    try:
        result = subprocess.run("conda info --envs", shell=True, capture_output=True, text=True)
        if "aiagent" in result.stdout:
            print("[安装] ✓ 检测到 aiagent conda环境")
            return True
        else:
            print("[安装] ⚠️  未检测到 aiagent conda环境")
            return False
    except:
        print("[安装] ⚠️  无法检测conda环境")
        return False

def main():
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("=" * 60)
    print("         📦 Chat-AI 依赖安装器")
    print("=" * 60)
    print()
    
    # 检查conda环境
    if check_conda_env():
        print("[安装] 建议激活aiagent环境: conda activate aiagent")
    
    print(f"[安装] 工作目录: {project_root}")
    print(f"[安装] Python版本: {sys.version}")
    print()
    
    # 升级pip
    print("[安装] 🔧 升级pip...")
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "升级pip"):
        print("[安装] ⚠️  pip升级失败，但继续安装")
    
    # 安装后端依赖
    print("\n[安装] 📚 安装后端依赖...")
    backend_deps = [
        "fastapi>=0.115.0",
        "uvicorn>=0.34.0", 
        "openai>=1.75.0",
        "python-dotenv>=0.21.0",
        "pydantic>=2.11.0",
        "pydantic-settings>=2.9.0",
        "jsonschema>=4.21.0",
        "matplotlib>=3.9.0",
        "numpy>=1.26.0",
        "cryptography>=42.0.0"
    ]
    
    for dep in backend_deps:
        if not run_command(f"{sys.executable} -m pip install {dep}", f"安装 {dep}"):
            print(f"[安装] ⚠️  {dep} 安装失败")
    
    # 安装前端依赖
    print("\n[安装] 🎨 安装前端依赖...")
    frontend_deps = [
        "streamlit",
        "scipy",
        "pandas", 
        "pillow",
        "requests",
        "duckduckgo-search",
        "speechrecognition",
        "pydub"
    ]
    
    for dep in frontend_deps:
        if not run_command(f"{sys.executable} -m pip install {dep}", f"安装 {dep}"):
            print(f"[安装] ⚠️  {dep} 安装失败")
    
    # 安装可选依赖（可能安装失败，但不影响核心功能）
    print("\n[安装] 🔧 安装可选依赖...")
    optional_deps = [
        "streamlit-audio-recorder"
    ]
    
    for dep in optional_deps:
        run_command(f"{sys.executable} -m pip install {dep}", f"安装可选依赖 {dep}")
    
    print("\n" + "=" * 60)
    print("[安装] 🎉 依赖安装完成!")
    print()
    print("💡 下一步:")
    print("  1. 检查 .env 文件中的API配置")
    print("  2. 运行后端: python start_backend.py")
    print("  3. 运行前端: python start_frontend.py") 
    print("  4. 或一键启动: python start_all.py")
    print("=" * 60)

if __name__ == "__main__":
    main()