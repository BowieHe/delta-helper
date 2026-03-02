"""
悬浮窗模块

实现透明悬浮窗，用于展示路线和物资信息
"""

from PySide6.QtWidgets import QWidget, QLabel, QGraphicsDropShadowEffect, QApplication
from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPolygon, QIcon
from typing import List, Tuple, Optional
import math
from loguru import logger


class PetOverlay(QWidget):
    """
    桌宠/悬浮窗

    特性：
    - 无边框透明窗口
    - 始终置顶不抢焦点
    - 点击穿透（不干扰游戏）
    - 平滑动画效果
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 窗口标志设置
        self.setWindowFlags(
            Qt.FramelessWindowHint  # 无边框
            | Qt.WindowStaysOnTopHint  # 始终置顶
            | Qt.Tool  # 不在任务栏显示
            | Qt.WindowDoesNotAcceptFocus  # 不抢焦点
        )

        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # 点击穿透

        # 窗口尺寸和位置
        self.setGeometry(1400, 800, 400, 300)

        # 动画
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.pos_animation = QPropertyAnimation(self, b"geometry")

        # 路线数据
        self.material_points: List[Tuple[int, int, str]] = []
        self.route_arrows: List[Tuple[QPoint, QPoint]] = []

        # 初始化UI
        self._setup_ui()

        logger.info("PetOverlay initialized")

    def _setup_ui(self):
        """初始化UI元素"""
        # 信息标签
        self.info_label = QLabel(self)
        self.info_label.setGeometry(10, 10, 380, 100)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-size: 14px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                background-color: rgba(0, 0, 0, 180);
                padding: 10px;
                border-radius: 8px;
                border: 1px solid rgba(0, 255, 0, 100);
            }
        """)
        self.info_label.setText("🎮 三角洲助手\n等待地图开启...")

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(3, 3)
        self.info_label.setGraphicsEffect(shadow)

    def set_route(
        self,
        points: List[Tuple[int, int]],
        player_pos: Optional[Tuple[int, int]] = None,
    ):
        """
        设置显示路线

        Args:
            points: 物资点坐标列表 [(x, y), ...]
            player_pos: 玩家位置 (x, y)
        """
        self.material_points = []

        # 转换坐标（游戏坐标 -> 屏幕坐标）
        scale = 0.25  # 缩放因子
        offset_x = 50
        offset_y = 150

        for i, (x, y) in enumerate(points):
            screen_x = int(x * scale) + offset_x
            screen_y = int(y * scale) + offset_y
            self.material_points.append((screen_x, screen_y, f"物资{i + 1}"))

        self.update()

    def update_info(self, text: str):
        """
        更新信息显示

        Args:
            text: 显示文本
        """
        self.info_label.setText(text)

    def fade_in(self, duration: int = 300):
        """
        淡入动画

        Args:
            duration: 动画时长（毫秒）
        """
        self.opacity_animation.stop()
        self.opacity_animation.setDuration(duration)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.opacity_animation.start()

    def fade_out(self, duration: int = 300):
        """
        淡出动画

        Args:
            duration: 动画时长（毫秒）
        """
        self.opacity_animation.stop()
        self.opacity_animation.setDuration(duration)
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.opacity_animation.start()

    def smooth_move(self, target_x: int, target_y: int, duration: int = 500):
        """
        平滑移动到新位置

        Args:
            target_x: 目标X坐标
            target_y: 目标Y坐标
            duration: 动画时长（毫秒）
        """
        self.pos_animation.stop()
        self.pos_animation.setDuration(duration)
        self.pos_animation.setStartValue(self.geometry())
        self.pos_animation.setEndValue(QRect(target_x, target_y, 400, 300))
        self.pos_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.pos_animation.start()

    def paintEvent(self, event):
        """绘制路线和指示"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制物资点
        for i, (x, y, label) in enumerate(self.material_points):
            # 圆圈
            if i == 0:
                # 第一个物资点用不同颜色
                painter.setPen(QPen(QColor(255, 200, 0, 200), 3))
                painter.setBrush(QBrush(QColor(255, 200, 0, 100)))
            else:
                painter.setPen(QPen(QColor(0, 255, 0, 200), 3))
                painter.setBrush(QBrush(QColor(0, 255, 0, 100)))

            painter.drawEllipse(x - 10, y - 10, 20, 20)

            # 标签
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
            painter.drawText(x + 15, y + 5, label)

        # 绘制箭头连接线
        if len(self.material_points) > 1:
            painter.setPen(QPen(QColor(255, 200, 0, 180), 3, Qt.DashLine))

            for i in range(len(self.material_points) - 1):
                x1, y1, _ = self.material_points[i]
                x2, y2, _ = self.material_points[i + 1]
                painter.drawLine(x1, y1, x2, y2)

                # 绘制箭头
                self._draw_arrow(painter, x1, y1, x2, y2)

    def _draw_arrow(self, painter: QPainter, x1: int, y1: int, x2: int, y2: int):
        """绘制箭头"""
        # 计算角度
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_len = 15
        arrow_angle = math.pi / 6  # 30度

        # 箭头两个端点
        ax1 = x2 - arrow_len * math.cos(angle - arrow_angle)
        ay1 = y2 - arrow_len * math.sin(angle - arrow_angle)
        ax2 = x2 - arrow_len * math.cos(angle + arrow_angle)
        ay2 = y2 - arrow_len * math.sin(angle + arrow_angle)

        arrow_head = QPolygon(
            [
                QPoint(int(x2), int(y2)),
                QPoint(int(ax1), int(ay1)),
                QPoint(int(ax2), int(ay2)),
            ]
        )

        painter.setBrush(QBrush(QColor(255, 200, 0, 180)))
        painter.drawPolygon(arrow_head)

    def clear_route(self):
        """清除路线"""
        self.material_points = []
        self.update()


if __name__ == "__main__":
    # 测试代码
    import sys

    app = QApplication(sys.argv)

    overlay = PetOverlay()
    overlay.show()
    overlay.fade_in()

    # 测试数据
    test_points = [(100, 100), (300, 200), (500, 150), (400, 300)]
    overlay.set_route(test_points)
    overlay.update_info("🎮 地图已开启\n📦 发现 4 个物资点\n➡️ 建议路线已规划")

    sys.exit(app.exec())
