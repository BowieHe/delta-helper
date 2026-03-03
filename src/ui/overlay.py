"""
桌面宠物悬浮窗模块

实现完整的桌宠体验：
- 可拖拽移动
- 右键菜单
- 呼吸动画
- 几何宠物角色
- 状态切换
- 发光效果
- 通知气泡
"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QGraphicsDropShadowEffect,
    QApplication,
    QMenu,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
)
from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QRect, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPolygon, QIcon, QAction
from typing import List, Tuple, Optional
from enum import Enum
import math
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger


class PetState(Enum):
    """宠物状态枚举"""

    IDLE = "idle"  # 默认待机 - 蓝色
    WORKING = "working"  # 工作中 - 绿色
    SUCCESS = "success"  # 成功 - 金色
    ERROR = "error"  # 错误 - 红色


class PetAvatar(QWidget):
    """几何宠物角色组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self.state = PetState.IDLE
        self.animation_frame = 0

        # 动画定时器
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._update_animation)
        self.anim_timer.start(100)  # 10 FPS

    def set_state(self, state: PetState):
        """切换动画状态"""
        self.state = state
        self.animation_frame = 0
        self.update()

    def _update_animation(self):
        """更新动画帧"""
        self.animation_frame = (self.animation_frame + 1) % 100
        self.update()

    def paintEvent(self, event):
        """绘制宠物"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x, center_y = 30, 30

        # 根据状态设置参数
        if self.state == PetState.IDLE:
            # 待机：呼吸效果
            breathe = 1 + 0.08 * math.sin(self.animation_frame * 0.1)
            radius = 20 * breathe
            color = QColor(100, 200, 255)  # 蓝色

        elif self.state == PetState.WORKING:
            # 工作中：快速脉冲
            pulse = abs(math.sin(self.animation_frame * 0.3))
            radius = 20 + pulse * 5
            color = QColor(0, 255, 150)  # 绿色

        elif self.state == PetState.SUCCESS:
            # 成功：开心跳动
            bounce = abs(math.sin(self.animation_frame * 0.2))
            center_y = 30 - bounce * 8
            radius = 22
            color = QColor(255, 200, 50)  # 金色

        else:  # ERROR
            # 错误：抖动
            shake = math.sin(self.animation_frame * 0.8) * 2
            center_x = 30 + shake
            radius = 20
            color = QColor(255, 80, 80)  # 红色

        # 绘制主体（圆形）
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(
            int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2)
        )

        # 绘制眼睛
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        eye_y = int(center_y - 3)
        # 左眼
        painter.drawEllipse(int(center_x - 6), eye_y, 4, 4)
        # 右眼
        painter.drawEllipse(int(center_x + 2), eye_y, 4, 4)

        # 绘制嘴巴（根据状态）
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        if self.state == PetState.SUCCESS:
            # 开心的微笑
            painter.drawArc(int(center_x - 5), int(center_y + 2), 10, 6, 0, 180 * 16)
        elif self.state == PetState.ERROR:
            # 难过的表情
            painter.drawArc(int(center_x - 5), int(center_y + 4), 10, 6, 180 * 16, 180 * 16)
        else:
            # 平静的嘴巴
            painter.drawLine(
                int(center_x - 3), int(center_y + 5), int(center_x + 3), int(center_y + 5)
            )


class NotificationBubble(QFrame):
    """通知气泡组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 60)
        self.hide()

        # 样式
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(44, 62, 80, 220);
                border: 2px solid rgba(52, 152, 219, 200);
                border-radius: 10px;
                color: #ecf0f1;
            }
        """)

        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        self.title_label = QLabel("通知")
        self.title_label.setStyleSheet("font-weight: bold; color: #3498db;")
        layout.addWidget(self.title_label)

        self.message_label = QLabel("消息内容")
        layout.addWidget(self.message_label)

        # 动画
        self.slide_animation = QPropertyAnimation(self, b"geometry")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.OutCubic)

        # 自动隐藏定时器
        self.hide_timer = QTimer(self)
        self.hide_timer.timeout.connect(self.hide)

    def show_notification(self, title: str, message: str, duration: int = 3000):
        """显示通知"""
        self.title_label.setText(title)
        self.message_label.setText(message)

        # 从右侧滑入
        start_rect = QRect(self.parent().width(), 10, 200, 60)
        end_rect = QRect(self.parent().width() - 210, 10, 200, 60)

        self.setGeometry(start_rect)
        self.show()

        self.slide_animation.setStartValue(start_rect)
        self.slide_animation.setEndValue(end_rect)
        self.slide_animation.start()

        # 自动隐藏
        self.hide_timer.start(duration)


class PetOverlay(QWidget):
    """
    桌面宠物悬浮窗

    特性：
    - 无边框透明窗口
    - 始终置顶
    - 可拖拽移动
    - 右键菜单
    - 呼吸动画
    - 宠物角色
    """

    # 信号
    state_changed = Signal(str)  # 状态变化信号

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

        # 窗口尺寸
        self.setFixedSize(250, 200)

        # 初始化状态
        self.current_state = PetState.IDLE
        self.dragging = False
        self.drag_start_pos = QPoint()
        self.main_window = None

        # 初始化UI
        self._setup_ui()
        self._setup_drag_handle()
        self._setup_context_menu()
        self._setup_breathing_animation()
        self._setup_pet_avatar()
        self._setup_notification()

        # 恢复位置
        self.restore_position()

        logger.info("PetOverlay initialized")

    def _setup_ui(self):
        """初始化UI元素"""
        # 主容器（用于控制透明点击）
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 250, 200)
        self.container.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        # 信息标签
        self.info_label = QLabel(self.container)
        self.info_label.setGeometry(10, 80, 230, 70)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-size: 12px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                background-color: rgba(0, 0, 0, 180);
                padding: 8px;
                border-radius: 8px;
                border: 1px solid rgba(0, 255, 0, 100);
            }
        """)
        self.info_label.setText("🎮 三角洲助手\n等待地图开启...")

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self.info_label)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(3, 3)
        self.info_label.setGraphicsEffect(shadow)

        # 状态标签
        self.status_label = QLabel(self.container)
        self.status_label.setGeometry(80, 155, 160, 25)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 11px;
                background-color: rgba(52, 152, 219, 180);
                padding: 3px 8px;
                border-radius: 12px;
            }
        """)
        self.status_label.setText("● 待机中")
        self.status_label.setAlignment(Qt.AlignCenter)

    def _setup_drag_handle(self):
        """设置拖拽手柄"""
        self.drag_handle = QLabel(self.container)
        self.drag_handle.setGeometry(0, 0, 20, 20)
        self.drag_handle.setStyleSheet("""
            QLabel {
                background-color: rgba(100, 200, 255, 180);
                border: 2px solid rgba(255, 255, 255, 200);
                border-radius: 3px;
            }
            QLabel:hover {
                background-color: rgba(100, 200, 255, 250);
                border-color: #ffffff;
            }
        """)
        self.drag_handle.setCursor(Qt.OpenHandCursor)
        self.drag_handle.setToolTip("拖拽移动")

    def _setup_context_menu(self):
        """设置右键菜单"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #3498db;
            }
            QMenu::separator {
                height: 1px;
                background-color: #34495e;
                margin: 5px 10px;
            }
        """)

        # 显示/隐藏主窗口
        main_visible = self.main_window.isVisible() if self.main_window else False
        toggle_action = QAction("🙈 隐藏主窗口" if main_visible else "👁️ 显示主窗口", self)
        toggle_action.triggered.connect(self._toggle_main_window)
        menu.addAction(toggle_action)

        menu.addSeparator()

        # 透明度子菜单
        opacity_menu = menu.addMenu("🔅 透明度")
        current_opacity = int(self.windowOpacity() * 100)
        for opacity in [100, 80, 60, 40]:
            action = QAction(f"{opacity}%", self)
            action.setCheckable(True)
            action.setChecked(current_opacity == opacity)
            action.triggered.connect(lambda checked, o=opacity: self._set_opacity(o))
            opacity_menu.addAction(action)

        # 置顶切换
        menu.addSeparator()
        topmost_action = QAction("📌 始终置顶", self)
        topmost_action.setCheckable(True)
        topmost_action.setChecked(True)
        topmost_action.triggered.connect(self._toggle_topmost)
        menu.addAction(topmost_action)

        menu.addSeparator()

        # 退出
        exit_action = QAction("❌ 退出程序", self)
        exit_action.triggered.connect(self._exit_app)
        menu.addAction(exit_action)

        menu.exec(self.mapToGlobal(pos))

    def _setup_breathing_animation(self):
        """设置呼吸发光动画"""
        # 发光效果
        self.glow_effect = QGraphicsDropShadowEffect(self.container)
        self._update_glow_color()
        self.glow_effect.setBlurRadius(20)
        self.glow_effect.setOffset(0, 0)
        self.container.setGraphicsEffect(self.glow_effect)

        # 呼吸动画
        self.breath_animation = QPropertyAnimation(self.glow_effect, b"blurRadius")
        self.breath_animation.setDuration(2000)
        self.breath_animation.setStartValue(15)
        self.breath_animation.setEndValue(30)
        self.breath_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.breath_animation.setLoopCount(-1)
        self.breath_animation.start()

    def _update_glow_color(self):
        """根据状态更新发光颜色"""
        colors = {
            PetState.IDLE: QColor(100, 200, 255, 120),  # 蓝色
            PetState.WORKING: QColor(0, 255, 150, 150),  # 绿色
            PetState.SUCCESS: QColor(255, 200, 50, 180),  # 金色
            PetState.ERROR: QColor(255, 80, 80, 180),  # 红色
        }
        if hasattr(self, "glow_effect"):
            self.glow_effect.setColor(colors.get(self.current_state, colors[PetState.IDLE]))

    def _setup_pet_avatar(self):
        """设置宠物形象"""
        self.pet_avatar = PetAvatar(self.container)
        self.pet_avatar.move(10, 10)

        # 点击宠物切换状态（测试用）
        self.pet_avatar.mousePressEvent = self._on_pet_clicked

    def _setup_notification(self):
        """设置通知气泡"""
        self.notification = NotificationBubble(self.container)

    def _on_pet_clicked(self, event):
        """点击宠物时的处理"""
        # 循环切换状态（测试用）
        states = [PetState.IDLE, PetState.WORKING, PetState.SUCCESS, PetState.ERROR]
        current_idx = states.index(self.current_state)
        next_idx = (current_idx + 1) % len(states)
        self.set_state(states[next_idx])

    def set_state(self, state: PetState):
        """设置宠物状态"""
        self.current_state = state
        self.pet_avatar.set_state(state)
        self._update_glow_color()

        # 更新状态标签
        status_texts = {
            PetState.IDLE: "● 待机中",
            PetState.WORKING: "● 扫描中...",
            PetState.SUCCESS: "● 发现物资!",
            PetState.ERROR: "● 需要关注",
        }
        self.status_label.setText(status_texts.get(state, "● 未知"))

        # 调整动画速度
        if state == PetState.WORKING:
            self.breath_animation.setDuration(800)  # 更快
        elif state == PetState.ERROR:
            self.breath_animation.setDuration(500)  # 很快
        else:
            self.breath_animation.setDuration(2000)  # 正常

        self.state_changed.emit(state.value)
        logger.info(f"Pet state changed to: {state.value}")

    def show_notification(self, title: str, message: str, duration: int = 3000):
        """显示通知"""
        self.notification.show_notification(title, message, duration)

    def update_info(self, text: str):
        """更新信息文本"""
        self.info_label.setText(text)

    def set_route(
        self, points: List[Tuple[int, int]], player_pos: Optional[Tuple[int, int]] = None
    ):
        """设置路线（保留原有功能）"""
        # TODO: 实现路线绘制
        pass

    def clear_route(self):
        """清除路线"""
        # TODO: 清除路线绘制
        pass

    # ===== 拖拽功能 =====

    def mousePressEvent(self, event):
        """鼠标按下"""
        if event.button() == Qt.LeftButton:
            # 检查是否点在拖拽手柄上
            if self.drag_handle.geometry().contains(event.pos()):
                self.dragging = True
                self.drag_start_pos = event.globalPos() - self.frameGeometry().topLeft()
                self.drag_handle.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """鼠标移动"""
        if self.dragging:
            new_pos = event.globalPos() - self.drag_start_pos
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            self.drag_handle.setCursor(Qt.OpenHandCursor)
            self.save_position()

    # ===== 位置持久化 =====

    def save_position(self):
        """保存窗口位置"""
        try:
            from core.config import Config

            config = Config.load()
            config.ui.overlay_x = self.x()
            config.ui.overlay_y = self.y()
            config.save()
            logger.debug(f"Position saved: ({self.x()}, {self.y()})")
        except Exception as e:
            logger.error(f"Failed to save position: {e}")

    def restore_position(self):
        """恢复窗口位置"""
        try:
            from core.config import Config

            config = Config.load()
            x = getattr(config.ui, "overlay_x", 1400)
            y = getattr(config.ui, "overlay_y", 800)
            self.move(x, y)
            logger.info(f"Position restored: ({x}, {y})")
        except Exception as e:
            logger.error(f"Failed to restore position: {e}")
            self.move(1400, 800)  # 默认位置

    # ===== 菜单功能 =====

    def _toggle_main_window(self):
        """切换主窗口显示"""
        if self.main_window:
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self.main_window.show()
                self.main_window.raise_()
                self.main_window.activateWindow()

    def _set_opacity(self, percent: int):
        """设置透明度"""
        self.setWindowOpacity(percent / 100.0)
        logger.debug(f"Opacity set to {percent}%")

    def _toggle_topmost(self, checked: bool):
        """切换置顶状态"""
        # 需要重新创建窗口才能改变置顶状态
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def _exit_app(self):
        """退出程序"""
        logger.info("Exit requested from context menu")
        QApplication.quit()

    # ===== 动画效果 =====

    def fade_in(self):
        """淡入动画"""
        self.setWindowOpacity(0)
        self.show()

        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(300)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()

    def fade_out(self):
        """淡出动画"""
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(300)
        anim.setStartValue(1)
        anim.setEndValue(0)
        anim.setEasingCurve(QEasingCurve.InCubic)
        anim.finished.connect(self.hide)
        anim.start()


if __name__ == "__main__":
    # 测试代码
    app = QApplication(sys.argv)

    overlay = PetOverlay()
    overlay.fade_in()

    # 测试状态切换
    def test_states():
        states = [PetState.IDLE, PetState.WORKING, PetState.SUCCESS, PetState.ERROR]
        current = 0

        def switch():
            nonlocal current
            overlay.set_state(states[current])
            current = (current + 1) % len(states)

        timer = QTimer()
        timer.timeout.connect(switch)
        timer.start(3000)  # 每3秒切换一次

    test_states()

    # 测试通知
    QTimer.singleShot(2000, lambda: overlay.show_notification("发现物资", "医疗包 x2, 弹药箱 x1"))

    sys.exit(app.exec())
