import os
import subprocess
import sys
from pathlib import Path

def build_exe():
    """自动化打包SnapValid为单文件EXE"""
    # 检查pyinstaller是否安装
    try:
        import PyInstaller
    except ImportError:
        print("安装PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0.0"])
    
    # 定义打包参数
    project_root = Path(__file__).parent
    main_script = project_root / "main.py"
    build_cmd = [
        "pyinstaller",
        "-F", "-w",  # 单文件、无控制台
        "--name", "SnapValid",
        f"--add-data={project_root / 'assets'};assets",
        f"--add-data={project_root / 'config.yml'};.",
        "--distpath", str(project_root / "dist"),
        "--workpath", str(project_root / "build"),
        str(main_script)
    ]
    
    # 执行打包
    print("开始打包...")
    subprocess.check_call(build_cmd)
    print(f"打包完成！EXE文件路径: {project_root / 'dist' / 'SnapValid.exe'}")

if __name__ == "__main__":
    build_exe()