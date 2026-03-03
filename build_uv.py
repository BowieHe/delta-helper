"""
使用 UV + PyInstaller 打包 Delta Helper

优势：
- 使用 uv 的快速依赖解析
- 自动处理隐藏导入
- 支持增量构建
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path


def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    dirs_to_remove = ["build", "dist", "*.spec"]
    for pattern in dirs_to_remove:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
    print("✅ 清理完成")


def install_deps():
    """使用 uv 安装依赖"""
    print("📦 安装依赖...")
    try:
        # 检查是否安装了 uv
        subprocess.run(["uv", "--version"], check=True, capture_output=True)

        # 使用 uv 安装
        subprocess.run(["uv", "pip", "install", "-e", ".", "--quiet"], check=True)
        subprocess.run(["uv", "pip", "install", "pyinstaller", "--quiet"], check=True)
        print("✅ 依赖安装完成")
    except subprocess.CalledProcessError:
        print("❌ uv 未安装，使用 pip 作为后备...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)


def build_exe(debug=False):
    """构建 exe"""
    print(f"\n🚀 开始打包{'(调试模式)' if debug else ''}...")
    print("⏳ 这可能需要 3-10 分钟，请耐心等待...\n")

    # 基础参数
    name = "三角洲助手-debug" if debug else "三角洲助手"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "src/main.py",
        f"--name={name}",
        "--onefile",
        "--windowed" if not debug else "--console",
        "--clean",
        "--noconfirm",
        # 数据文件
        "--add-data",
        "config;config",
        "--add-data",
        "assets;assets",
        # 隐藏导入 - 核心模块
        "--hidden-import",
        "src.core",
        "--hidden-import",
        "src.core.capture",
        "--hidden-import",
        "src.core.map_detector",
        "--hidden-import",
        "src.core.ocr_engine",
        "--hidden-import",
        "src.core.route_planner",
        "--hidden-import",
        "src.core.config",
        # 隐藏导入 - UI模块
        "--hidden-import",
        "src.ui",
        "--hidden-import",
        "src.ui.main_window",
        "--hidden-import",
        "src.ui.overlay",
        "--hidden-import",
        "src.ui.stats_dialog",
        # 隐藏导入 - 分析模块
        "--hidden-import",
        "src.analytics",
        "--hidden-import",
        "src.analytics.database",
        "--hidden-import",
        "src.analytics.calculator",
        "--hidden-import",
        "src.analytics.models",
        # 第三方库
        "--hidden-import",
        "paddleocr",
        "--hidden-import",
        "dxcam",
        "--hidden-import",
        "cv2",
        "--hidden-import",
        "keyboard",
        "--hidden-import",
        "pathfinding",
        "--hidden-import",
        "loguru",
        "--hidden-import",
        "pydantic",
        # 排除大体积库
        "--exclude-module",
        "matplotlib",
        "--exclude-module",
        "tkinter",
        "--exclude-module",
        "unittest",
        "--exclude-module",
        "pytest",
        "--exclude-module",
        "sphinx",
        "--exclude-module",
        "IPython",
        "--exclude-module",
        "pandas",
        "--exclude-module",
        "scipy",
        "--exclude-module",
        "sklearn",
        # 输出目录
        "--distpath",
        "dist",
        "--workpath",
        "build",
        "--specpath",
        "build",
        # 优化
        "--strip",
    ]

    # 如果存在 UPX，使用它压缩
    upx_path = shutil.which("upx")
    if upx_path:
        print(f"📦 发现 UPX: {upx_path}")
        cmd.extend(["--upx-dir", os.path.dirname(upx_path)])

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)

        print("\n" + "=" * 60)
        print("✅ 打包成功!")
        print("=" * 60)

        exe_path = f"dist/{name}.exe"
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n📦 文件: {exe_path}")
            print(f"📊 大小: {size_mb:.1f} MB")

            if size_mb > 500:
                print("⚠️  文件较大，建议检查是否有不必要的依赖")

            print(f"\n🎉 可以直接双击运行!")
            print(f"\n提示: 首次启动可能需要 10-30 秒加载 OCR 模型")

        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败!")
        print(f"错误代码: {e.returncode}")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Delta Helper 打包工具 (UV版)")
    parser.add_argument("--debug", action="store_true", help="调试模式（带控制台窗口）")
    parser.add_argument("--clean", action="store_true", help="清理构建文件")
    parser.add_argument("--skip-deps", action="store_true", help="跳过依赖安装")

    args = parser.parse_args()

    print("🎯 Delta Helper - 高级打包工具\n")
    print(f"Python: {sys.executable}")
    print(f"工作目录: {os.getcwd()}\n")

    if args.clean:
        clean_build()
        return

    if not args.skip_deps:
        install_deps()

    success = build_exe(debug=args.debug)

    if success and not args.debug:
        print("\n💡 提示:")
        print("   - 运行 ./dist/三角洲助手.exe 启动程序")
        print("   - 如果出错，使用 --debug 参数打包调试版本查看错误")


if __name__ == "__main__":
    main()
