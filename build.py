"""
打包脚本

使用PyInstaller打包为独立可执行文件
"""

import PyInstaller.__main__
import os
import sys


def build():
    """打包三角洲助手"""

    print("🚀 开始打包三角洲助手...")

    # 确保目录存在
    os.makedirs("dist", exist_ok=True)
    os.makedirs("build", exist_ok=True)

    # PyInstaller参数
    args = [
        "src/main.py",
        "--name=三角洲助手",
        "--onefile",
        "--windowed",
        # 图标
        # '--icon=assets/icon.ico',
        # 添加数据文件
        "--add-data=config;config",
        "--add-data=assets;assets",
        # 隐藏导入
        "--hidden-import=paddleocr",
        "--hidden-import=dxcam",
        "--hidden-import=cv2",
        "--hidden-import=keyboard",
        "--hidden-import=pathfinding",
        "--hidden-import=loguru",
        # 排除不需要的库（减小体积）
        "--exclude-module=matplotlib",
        "--exclude-module=tkinter",
        "--exclude-module=unittest",
        "--exclude-module=pytest",
        "--exclude-module=sphinx",
        "--exclude-module=IPython",
        # 优化
        "--strip",
        "--clean",
        # 输出目录
        "--distpath=dist",
        "--workpath=build",
        "--specpath=build",
    ]

    try:
        PyInstaller.__main__.run(args)
        print("✅ 打包完成！")
        print(f"📦 输出文件: dist/三角洲助手.exe")

        # 显示文件大小
        exe_path = "dist/三角洲助手.exe"
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"📊 文件大小: {size_mb:.1f} MB")

        return True

    except Exception as e:
        print(f"❌ 打包失败: {e}")
        return False


def build_debug():
    """调试模式打包（控制台窗口）"""

    print("🐛 开始调试模式打包...")

    args = [
        "src/main.py",
        "--name=三角洲助手-debug",
        "--onefile",
        # '--windowed',  # 调试模式保留控制台
        "--add-data=config;config",
        "--add-data=assets;assets",
        "--hidden-import=paddleocr",
        "--hidden-import=dxcam",
        "--hidden-import=cv2",
        "--hidden-import=keyboard",
        "--hidden-import=pathfinding",
        "--hidden-import=loguru",
        "--exclude-module=matplotlib",
        "--exclude-module=tkinter",
        "--strip",
        "--clean",
        "--distpath=dist",
        "--workpath=build",
        "--specpath=build",
    ]

    try:
        PyInstaller.__main__.run(args)
        print("✅ 调试版本打包完成！")
        return True

    except Exception as e:
        print(f"❌ 打包失败: {e}")
        return False


def clean():
    """清理构建文件"""
    import shutil

    print("🧹 清理构建文件...")

    dirs_to_remove = ["build", "__pycache__"]
    for d in dirs_to_remove:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"  已删除: {d}")

    print("✅ 清理完成")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="三角洲助手打包工具")
    parser.add_argument("--debug", action="store_true", help="调试模式打包")
    parser.add_argument("--clean", action="store_true", help="清理构建文件")

    args = parser.parse_args()

    if args.clean:
        clean()
    elif args.debug:
        build_debug()
    else:
        build()
