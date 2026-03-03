"""
一键打包exe脚本
"""

import subprocess
import sys
import os


def install_pyinstaller():
    """安装PyInstaller"""
    print("📦 检查PyInstaller...")
    try:
        import PyInstaller

        print("✅ PyInstaller 已安装")
        return True
    except ImportError:
        print("📥 安装PyInstaller...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller", "-q"]
        )
        print("✅ PyInstaller 安装完成")
        return True


def build_exe():
    """打包exe"""
    print("\n🚀 开始打包三角洲助手...")
    print("⏳ 这可能需要几分钟，请耐心等待...\n")

    # 确保目录存在
    os.makedirs("dist", exist_ok=True)
    os.makedirs("build", exist_ok=True)

    # PyInstaller命令
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "src/main.py",
        "--name=三角洲助手",
        "--onefile",
        "--windowed",
        "--add-data=config;config",
        "--add-data=assets;assets",
        "--hidden-import=paddleocr",
        "--hidden-import=dxcam",
        "--hidden-import=cv2",
        "--hidden-import=keyboard",
        "--hidden-import=pathfinding",
        "--hidden-import=loguru",
        "--hidden-import=src.analytics",
        "--hidden-import=src.analytics.database",
        "--hidden-import=src.analytics.calculator",
        "--hidden-import=src.analytics.models",
        "--exclude-module=matplotlib",
        "--exclude-module=tkinter",
        "--exclude-module=unittest",
        "--exclude-module=pytest",
        "--clean",
        "--distpath=dist",
        "--workpath=build",
        "--specpath=build",
    ]

    try:
        subprocess.check_call(cmd)
        print("\n" + "=" * 50)
        print("✅ 打包成功!")
        print("=" * 50)

        exe_path = "dist/三角洲助手.exe"
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n📦 文件: {exe_path}")
            print(f"📊 大小: {size_mb:.1f} MB")
            print(f"\n🎉 可以直接双击运行: {exe_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败: {e}")
        return False


if __name__ == "__main__":
    print("🎯 三角洲助手 - EXE打包工具\n")

    # 安装依赖
    if install_pyinstaller():
        # 开始打包
        build_exe()
    else:
        print("❌ 无法安装PyInstaller，请手动运行: pip install pyinstaller")
