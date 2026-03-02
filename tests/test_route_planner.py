"""
路线规划模块测试
"""

import pytest
import numpy as np
from core.route_planner import AStarPlanner, RouteOptimizer, MaterialNode, Node


class TestAStarPlanner:
    """测试A*规划器"""

    def test_simple_path(self):
        """测试简单路径规划"""
        planner = AStarPlanner()

        # 从(0,0)到(5,5)
        path = planner.find_path((0, 0), (5, 5))

        assert len(path) > 0
        assert path[0] == (0, 0)
        assert path[-1] == (5, 5)

    def test_path_with_obstacles(self):
        """测试带障碍物的路径规划"""
        # 创建10x10地图，中间有障碍物
        grid = np.zeros((10, 10))
        grid[4, 2:8] = 1  # 中间横条障碍

        planner = AStarPlanner(grid)
        path = planner.find_path((0, 5), (9, 5))

        # 应该能找到绕过障碍物的路径
        assert len(path) > 0
        assert path[0] == (0, 5)
        assert path[-1] == (9, 5)

    def test_no_path(self):
        """测试无法到达的情况"""
        # 创建地图，起点终点被隔开
        grid = np.zeros((5, 5))
        grid[:, 2] = 1  # 中间竖条障碍

        planner = AStarPlanner(grid)
        path = planner.find_path((0, 0), (4, 4))

        # 应该返回空路径
        assert len(path) == 0

    def test_node_comparison(self):
        """测试节点比较"""
        node1 = Node(0, 0, g=0, h=10)  # f=10
        node2 = Node(1, 1, g=5, h=3)  # f=8

        assert node2 < node1  # f值小的应该更小


class TestRouteOptimizer:
    """测试路线优化器"""

    def test_greedy_tsp(self):
        """测试贪心TSP"""
        optimizer = RouteOptimizer()

        points = [
            MaterialNode(0, 0, value=1.0, name="A"),
            MaterialNode(10, 0, value=1.0, name="B"),
            MaterialNode(5, 10, value=1.0, name="C"),
        ]

        route = optimizer.greedy_tsp(points, start_idx=0)

        assert len(route) == 3
        assert route[0] == 0  # 从起点开始

    def test_weighted_greedy(self):
        """测试加权贪心"""
        optimizer = RouteOptimizer()

        points = [
            MaterialNode(0, 0, value=1.0, name="A"),
            MaterialNode(10, 0, value=10.0, name="B"),  # 高价值
            MaterialNode(5, 5, value=1.0, name="C"),
        ]

        route = optimizer.weighted_greedy(points, start_idx=0)

        assert len(route) == 3
        # 高价值点应该优先

    def test_two_opt_optimization(self):
        """测试2-opt优化"""
        optimizer = RouteOptimizer()

        points = [
            MaterialNode(0, 0, value=1.0),
            MaterialNode(10, 0, value=1.0),
            MaterialNode(10, 10, value=1.0),
            MaterialNode(0, 10, value=1.0),
        ]

        # 初始路线
        route = [0, 2, 1, 3]

        # 优化
        optimized = optimizer.two_opt(route, points)

        assert len(optimized) == 4

    def test_full_optimization(self):
        """测试完整优化流程"""
        optimizer = RouteOptimizer()

        points = [
            MaterialNode(100, 100, value=100.0, name="高价值物资"),
            MaterialNode(200, 150, value=50.0, name="普通物资"),
            MaterialNode(150, 200, value=30.0, name="低价值物资"),
        ]

        player_pos = (50, 50)

        optimized = optimizer.optimize_route(points, player_pos, algorithm="weighted")

        assert len(optimized) == 3
        # 高价值物资应该排在前面
        assert optimized[0].value >= optimized[-1].value

    def test_calculate_total_distance(self):
        """测试距离计算"""
        optimizer = RouteOptimizer()

        route = [
            MaterialNode(0, 0),
            MaterialNode(3, 4),  # 距离5
            MaterialNode(6, 8),  # 距离5
        ]

        total = optimizer.calculate_total_distance(route)

        assert total == 10.0  # 5 + 5

    def test_calculate_total_value(self):
        """测试价值计算"""
        optimizer = RouteOptimizer()

        route = [
            MaterialNode(0, 0, value=100.0),
            MaterialNode(10, 10, value=50.0),
        ]

        total = optimizer.calculate_total_value(route)

        assert total == 150.0


class TestMaterialNode:
    """测试MaterialNode"""

    def test_distance_calculation(self):
        """测试距离计算"""
        node1 = MaterialNode(0, 0)
        node2 = MaterialNode(3, 4)

        dist = node1.distance_to(node2)

        assert dist == 5.0  # 3-4-5直角三角形

    def test_default_values(self):
        """测试默认值"""
        node = MaterialNode(10, 20)

        assert node.x == 10
        assert node.y == 20
        assert node.value == 1.0
        assert node.name == ""
