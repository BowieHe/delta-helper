"""
路线规划模块

实现A*寻路和TSP多目标优化
"""

import heapq
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import numpy as np
from collections import defaultdict
import math
from loguru import logger


@dataclass
class Node:
    """A*路径节点"""

    x: int
    y: int
    g: float = 0.0  # 从起点到当前节点的实际代价
    h: float = 0.0  # 启发式估计代价
    parent: Optional["Node"] = None

    @property
    def f(self) -> float:
        return self.g + self.h

    def __lt__(self, other):
        return self.f < other.f

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


@dataclass
class MaterialNode:
    """物资节点（用于TSP）"""

    x: int
    y: int
    value: float = 1.0  # 物资价值权重
    name: str = ""

    def distance_to(self, other: "MaterialNode") -> float:
        """计算到另一个节点的欧氏距离"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class AStarPlanner:
    """
    A*路径规划器

    用于计算两点之间的最短路径（支持障碍物避让）
    """

    def __init__(self, grid_map: Optional[np.ndarray] = None):
        """
        初始化规划器

        Args:
            grid_map: 二值地图，0表示可通行，1表示障碍
        """
        self.grid_map = grid_map

    def set_map(self, grid_map: np.ndarray):
        """设置地图"""
        self.grid_map = grid_map

    def heuristic(self, node: Node, goal: Node) -> float:
        """
        启发式函数：欧氏距离

        Args:
            node: 当前节点
            goal: 目标节点

        Returns:
            估计代价
        """
        return math.sqrt((node.x - goal.x) ** 2 + (node.y - goal.y) ** 2)

    def get_neighbors(self, node: Node) -> List[Node]:
        """
        获取相邻节点（8方向）

        Args:
            node: 当前节点

        Returns:
            邻居节点列表
        """
        neighbors = []
        # 8方向移动
        directions = [
            (-1, -1),
            (0, -1),
            (1, -1),
            (-1, 0),
            (1, 0),
            (-1, 1),
            (0, 1),
            (1, 1),
        ]

        for dx, dy in directions:
            nx, ny = node.x + dx, node.y + dy

            # 边界检查
            if self.grid_map is not None:
                h, w = self.grid_map.shape
                if not (0 <= nx < w and 0 <= ny < h):
                    continue
                if self.grid_map[ny, nx] == 1:  # 障碍
                    continue

            neighbors.append(Node(nx, ny))

        return neighbors

    def find_path(
        self, start: Tuple[int, int], goal: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """
        A*寻路

        Args:
            start: 起点坐标 (x, y)
            goal: 目标坐标 (x, y)

        Returns:
            路径点列表，失败返回空列表
        """
        start_node = Node(start[0], start[1])
        goal_node = Node(goal[0], goal[1])

        open_set = [start_node]
        closed_set = set()
        g_scores = defaultdict(lambda: float("inf"))
        g_scores[(start_node.x, start_node.y)] = 0.0

        iterations = 0
        max_iterations = 10000  # 防止无限循环

        while open_set and iterations < max_iterations:
            iterations += 1
            current = heapq.heappop(open_set)

            if current.x == goal_node.x and current.y == goal_node.y:
                # 重构路径
                path = []
                while current:
                    path.append((current.x, current.y))
                    current = current.parent
                return path[::-1]

            closed_set.add((current.x, current.y))

            for neighbor in self.get_neighbors(current):
                if (neighbor.x, neighbor.y) in closed_set:
                    continue

                # 计算移动代价（对角线移动代价为√2）
                dx = abs(neighbor.x - current.x)
                dy = abs(neighbor.y - current.y)
                move_cost = 1.41421356 if dx + dy == 2 else 1.0

                tentative_g = g_scores[(current.x, current.y)] + move_cost

                if tentative_g < g_scores[(neighbor.x, neighbor.y)]:
                    neighbor.parent = current
                    neighbor.g = tentative_g
                    neighbor.h = self.heuristic(neighbor, goal_node)

                    g_scores[(neighbor.x, neighbor.y)] = tentative_g
                    heapq.heappush(open_set, neighbor)

        if iterations >= max_iterations:
            logger.warning("A* search exceeded max iterations")

        return []  # 未找到路径


class RouteOptimizer:
    """
    路线优化器

    解决多物资点访问的顺序问题（TSP变种）
    算法：加权贪心 + 2-opt局部优化
    """

    def __init__(self, planner: Optional[AStarPlanner] = None):
        """
        初始化优化器

        Args:
            planner: A*规划器实例，为None时使用欧氏距离
        """
        self.planner = planner

    def calculate_distance_matrix(self, points: List[MaterialNode]) -> np.ndarray:
        """
        计算点之间的距离矩阵

        Args:
            points: 物资点列表

        Returns:
            距离矩阵
        """
        n = len(points)
        dist_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                if self.planner:
                    # 使用A*计算实际路径长度
                    path = self.planner.find_path(
                        (points[i].x, points[i].y), (points[j].x, points[j].y)
                    )
                    if path:
                        dist = len(path)
                    else:
                        dist = points[i].distance_to(points[j])  #  fallback
                else:
                    # 使用欧氏距离
                    dist = points[i].distance_to(points[j])

                dist_matrix[i, j] = dist
                dist_matrix[j, i] = dist

        return dist_matrix

    def greedy_tsp(self, points: List[MaterialNode], start_idx: int = 0) -> List[int]:
        """
        贪心算法求解TSP

        每次选择最近的未访问节点

        Args:
            points: 物资点列表
            start_idx: 起始点索引

        Returns:
            访问顺序索引列表
        """
        if not points:
            return []

        n = len(points)
        if n == 1:
            return [0]

        dist_matrix = self.calculate_distance_matrix(points)

        unvisited = set(range(n))
        unvisited.remove(start_idx)
        route = [start_idx]
        current = start_idx

        while unvisited:
            # 找到最近的未访问节点
            nearest = min(unvisited, key=lambda x: dist_matrix[current, x])
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest

        return route

    def weighted_greedy(
        self, points: List[MaterialNode], start_idx: int = 0
    ) -> List[int]:
        """
        带权重的贪心算法（推荐）

        综合考虑：价值 / 距离
        优先级 = 价值 / (距离 + epsilon)

        Args:
            points: 物资点列表
            start_idx: 起始点索引

        Returns:
            访问顺序索引列表
        """
        if not points:
            return []

        n = len(points)
        if n == 1:
            return [0]

        dist_matrix = self.calculate_distance_matrix(points)

        unvisited = set(range(n))
        unvisited.remove(start_idx)
        route = [start_idx]
        current = start_idx

        while unvisited:
            best_score = -1.0
            best_next = None

            for idx in unvisited:
                distance = dist_matrix[current, idx]
                value = points[idx].value
                # 价值密度 = 价值 / 距离
                score = value / (distance + 1e-6)

                if score > best_score:
                    best_score = score
                    best_next = idx

            route.append(best_next)
            unvisited.remove(best_next)
            current = best_next

        return route

    def two_opt(self, route: List[int], points: List[MaterialNode]) -> List[int]:
        """
        2-opt局部优化

        改进贪心结果，减少路径交叉

        Args:
            route: 当前路线
            points: 物资点列表

        Returns:
            优化后的路线
        """
        if len(route) < 4:
            return route

        dist_matrix = self.calculate_distance_matrix(points)
        improved = True
        max_iterations = 100
        iteration = 0

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            for i in range(1, len(route) - 2):
                for j in range(i + 1, len(route)):
                    if j - i == 1:
                        continue

                    # 计算交换前后的路径长度
                    old_dist = (
                        dist_matrix[route[i - 1], route[i]]
                        + dist_matrix[route[j - 1], route[j]]
                    )
                    new_dist = (
                        dist_matrix[route[i - 1], route[j - 1]]
                        + dist_matrix[route[i], route[j]]
                    )

                    if new_dist < old_dist:
                        # 反转i到j之间的路径
                        route[i:j] = route[i:j][::-1]
                        improved = True

        return route

    def optimize_route(
        self,
        points: List[MaterialNode],
        player_pos: Tuple[int, int],
        algorithm: str = "weighted",
    ) -> List[MaterialNode]:
        """
        优化访问路线

        Args:
            points: 物资点列表
            player_pos: 玩家当前位置 (x, y)
            algorithm: 算法选择 ("greedy" | "weighted" | "nearest")

        Returns:
            排序后的物资点列表
        """
        if not points:
            return []

        if len(points) == 1:
            return points

        # 添加玩家位置作为起点
        player_node = MaterialNode(
            player_pos[0], player_pos[1], value=0.0, name="Player"
        )
        all_points = [player_node] + points

        # 选择算法
        if algorithm == "greedy":
            route_indices = self.greedy_tsp(all_points, start_idx=0)
        elif algorithm == "weighted":
            route_indices = self.weighted_greedy(all_points, start_idx=0)
        else:
            route_indices = self.greedy_tsp(all_points, start_idx=0)

        # 2-opt优化
        route_indices = self.two_opt(route_indices, all_points)

        # 移除起点，返回物资点顺序
        route_indices = [i for i in route_indices if i > 0]
        return [points[i - 1] for i in route_indices]

    def calculate_total_distance(self, route: List[MaterialNode]) -> float:
        """
        计算路线总长度

        Args:
            route: 物资点列表

        Returns:
            总距离
        """
        if len(route) < 2:
            return 0.0

        total = 0.0
        for i in range(len(route) - 1):
            total += route[i].distance_to(route[i + 1])

        return total

    def calculate_total_value(self, route: List[MaterialNode]) -> float:
        """
        计算路线总价值

        Args:
            route: 物资点列表

        Returns:
            总价值
        """
        return sum(p.value for p in route)
