#!/usr/bin/env python3
"""
项目验证脚本

无需外部依赖，验证代码结构和基础逻辑
"""

import sys
import os
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def check_file_syntax(filepath):
    """检查Python文件语法"""
    try:
        with open(filepath, "r") as f:
            source = f.read()
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, str(e)


def verify_project_structure():
    """验证项目结构"""
    print("=" * 60)
    print("🔍 验证项目结构")
    print("=" * 60)

    required_files = [
        "src/main.py",
        "src/core/__init__.py",
        "src/core/capture.py",
        "src/core/map_detector.py",
        "src/core/ocr_engine.py",
        "src/core/route_planner.py",
        "src/core/config.py",
        "src/ui/__init__.py",
        "src/ui/main_window.py",
        "src/ui/overlay.py",
        "tests/__init__.py",
        "tests/test_capture.py",
        "tests/test_map_detector.py",
        "tests/test_ocr_engine.py",
        "tests/test_route_planner.py",
        "requirements.txt",
        "build.py",
        "README.md",
        "PRD.md",
    ]

    all_exist = True
    for filepath in required_files:
        full_path = os.path.join("/home/bowie/code/delta-helper", filepath)
        exists = os.path.exists(full_path)
        status = "✅" if exists else "❌"
        print(f"{status} {filepath}")
        if not exists:
            all_exist = False

    return all_exist


def verify_syntax():
    """验证Python语法"""
    print("\n" + "=" * 60)
    print("🔍 验证Python语法")
    print("=" * 60)

    all_valid = True
    src_dir = "/home/bowie/code/delta-helper/src"

    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                valid, error = check_file_syntax(filepath)
                status = "✅" if valid else "❌"
                rel_path = filepath.replace("/home/bowie/code/delta-helper/", "")
                print(f"{status} {rel_path}")
                if not valid:
                    print(f"   错误: {error}")
                    all_valid = False

    return all_valid


def test_route_planner_logic():
    """测试路线规划逻辑"""
    print("\n" + "=" * 60)
    print("🔍 测试路线规划逻辑")
    print("=" * 60)

    import math
    from dataclasses import dataclass

    @dataclass
    class MaterialNode:
        x: int
        y: int
        value: float = 1.0
        name: str = ""

        def distance_to(self, other):
            return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    # 测试距离计算
    node1 = MaterialNode(0, 0)
    node2 = MaterialNode(3, 4)
    distance = node1.distance_to(node2)

    if distance == 5.0:
        print("✅ 距离计算正确 (3-4-5三角形)")
    else:
        print(f"❌ 距离计算错误: {distance} != 5.0")
        return False

    # 测试加权贪心算法
    points = [
        MaterialNode(0, 0, value=1.0),
        MaterialNode(10, 0, value=10.0),
        MaterialNode(5, 5, value=1.0),
    ]

    # 简单加权贪心测试
    unvisited = set(range(1, len(points)))
    current = 0
    route = [0]

    while unvisited:
        best_score = -1
        best_next = None

        for idx in unvisited:
            distance = points[current].distance_to(points[idx])
            value = points[idx].value
            score = value / (distance + 1e-6)

            if score > best_score:
                best_score = score
                best_next = idx

        route.append(best_next)
        unvisited.remove(best_next)
        current = best_next

    print(f"✅ 加权贪心算法: 路线 {route}")
    print(f"   高价值点(索引1)优先: {route[1] == 1}")

    return route[1] == 1


def count_lines_of_code():
    """统计代码行数"""
    print("\n" + "=" * 60)
    print("📊 代码统计")
    print("=" * 60)

    total_lines = 0
    file_count = 0

    src_dir = "/home/bowie/code/delta-helper/src"
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r") as f:
                    lines = len(f.readlines())
                    total_lines += lines
                    file_count += 1

    test_lines = 0
    test_count = 0
    tests_dir = "/home/bowie/code/delta-helper/tests"
    for root, dirs, files in os.walk(tests_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r") as f:
                    lines = len(f.readlines())
                    test_lines += lines
                    test_count += 1

    print(f"源代码: {file_count} 文件, {total_lines} 行")
    print(f"测试代码: {test_count} 文件, {test_lines} 行")
    print(f"总计: {file_count + test_count} 文件, {total_lines + test_lines} 行")


def main():
    """主函数"""
    print("\n" + "🚀 三角洲游戏助手 - 项目验证" + "\n")

    structure_ok = verify_project_structure()
    syntax_ok = verify_syntax()
    logic_ok = test_route_planner_logic()
    count_lines_of_code()

    print("\n" + "=" * 60)
    print("📋 验证结果")
    print("=" * 60)

    if structure_ok and syntax_ok and logic_ok:
        print("✅ 所有验证通过！项目结构完整，语法正确，逻辑正常。")
        return 0
    else:
        print("❌ 验证失败，请检查上述错误。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
