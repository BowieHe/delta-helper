"""
UV 包管理器设置脚本

UV 是一个快速的 Python 包管理器，比 pip 快 10-100 倍
"""

import subprocess
import sys
import os


def check_uv():
    """检查是否安装了 uv"""
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uv 已安装: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    return False


def install_uv():
    """安装 uv"""
    print("📥 安装 uv...")
    print("   方法1: 使用 pip")
    print("   pip install uv")
    print()
    print("   方法2: 使用官方安装脚本 (推荐)")
    print("   Windows PowerShell:")
    print('   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"')
    print()
    print("   macOS/Linux:")
    print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
    print()

    choice = input("是否现在使用 pip 安装 uv? (y/n): ").strip().lower()
    if choice == "y":
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "uv"])
            print("✅ uv 安装成功!")
            return True
        except Exception as e:
            print(f"❌ 安装失败: {e}")
            return False
    return False


def setup_project():
    """设置项目环境"""
    print("\n🔧 设置项目环境...")

    # 创建虚拟环境
    print("\n1️⃣ 创建虚拟环境...")
    subprocess.run(["uv", "venv"], check=True)
    print("   ✅ 虚拟环境创建完成")

    # 安装依赖
    print("\n2️⃣ 安装生产依赖...")
    subprocess.run(["uv", "pip", "install", "-e", "."], check=True)
    print("   ✅ 依赖安装完成")

    # 安装开发依赖（可选）
    print("\n3️⃣ 安装开发依赖...")
    choice = input("   是否安装开发依赖 (pytest, black, ruff)? (y/n): ").strip().lower()
    if choice == "y":
        subprocess.run(["uv", "pip", "install", "-e", ".[dev]"], check=True)
        print("   ✅ 开发依赖安装完成")

    # 安装打包依赖
    print("\n4️⃣ 安装打包依赖...")
    choice = input("   是否安装打包依赖 (pyinstaller)? (y/n): ").strip().lower()
    if choice == "y":
        subprocess.run(["uv", "pip", "install", "-e", ".[build]"], check=True)
        print("   ✅ 打包依赖安装完成")

    print("\n" + "=" * 50)
    print("✅ 项目设置完成!")
    print("=" * 50)
    print("\n使用方法:")
    print("  激活环境: .venv\\Scripts\\activate (Windows)")
    print("  运行程序: python src/main.py")
    print("  打包exe : python build.py")


def main():
    print("🚀 三角洲助手 - UV 环境设置\n")

    # 检查 uv
    if not check_uv():
        print("❌ uv 未安装")
        if not install_uv():
            print("\n请手动安装 uv 后重试:")
            print("pip install uv")
            return

    # 设置项目
    setup_project()


if __name__ == "__main__":
    main()
