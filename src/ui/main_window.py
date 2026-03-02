"""
主控制台模块

实现系统托盘、配置管理和统计面板
"""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSystemTrayIcon,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QProgressBar,
    QApplication,
    QTextEdit,
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QIcon, QAction, QFont, QPalette, QColor
from datetime import datetime
from typing import Optional
from loguru import logger


class MainWindow(QMainWindow):
    """
    主控制台窗口

    功能：
    - 系统托盘支持
    - 实时状态显示
    - 本局统计
    - 运行日志
    """

    # 信号
    start_monitoring_signal = Signal()
    stop_monitoring_signal = Signal()
    show_overlay_signal = Signal()
    hide_overlay_signal = Signal()

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config

        self.setWindowTitle("三角洲助手 v1.0")
        self.setGeometry(100, 100, 500, 700)

        # 设置字体
        self.setFont(QFont("Microsoft YaHei", 10))

        # 初始化UI
        self._setup_ui()
        self._setup_tray()
        self._setup_styles()

        # 定时更新状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # 每秒更新

        self._is_monitoring = False

        logger.info("MainWindow initialized")

    def _setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("🎮 三角洲行动 - 游戏助手")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(title)

        # 状态面板
        status_group = QGroupBox("📊 实时状态")
        status_layout = QVBoxLayout(status_group)

        self.game_status_label = QLabel("游戏状态: 未检测到")
        self.game_status_label.setStyleSheet(
            "color: #e74c3c; font-size: 14px; font-weight: bold;"
        )
        status_layout.addWidget(self.game_status_label)

        self.map_status_label = QLabel("地图状态: 关闭")
        self.map_status_label.setStyleSheet("font-size: 14px;")
        status_layout.addWidget(self.map_status_label)

        layout.addWidget(status_group)

        # 本局统计
        stats_group = QGroupBox("📈 本局统计")
        stats_layout = QVBoxLayout(stats_group)

        # 物资进度
        progress_label = QLabel("物资收集进度:")
        stats_layout.addWidget(progress_label)

        self.material_progress = QProgressBar()
        self.material_progress.setValue(0)
        self.material_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3498db;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        stats_layout.addWidget(self.material_progress)

        # 统计表格
        self.stats_table = QTableWidget(4, 2)
        self.stats_table.setHorizontalHeaderLabels(["项目", "数值"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setItem(0, 0, QTableWidgetItem("已识别物资"))
        self.stats_table.setItem(0, 1, QTableWidgetItem("0"))
        self.stats_table.setItem(1, 0, QTableWidgetItem("已探索区域"))
        self.stats_table.setItem(1, 1, QTableWidgetItem("0%"))
        self.stats_table.setItem(2, 0, QTableWidgetItem("预计价值"))
        self.stats_table.setItem(2, 1, QTableWidgetItem("0万"))
        self.stats_table.setItem(3, 0, QTableWidgetItem("搜索效率"))
        self.stats_table.setItem(3, 1, QTableWidgetItem("N/A"))
        stats_layout.addWidget(self.stats_table)

        layout.addWidget(stats_group)

        # 快捷操作
        action_group = QGroupBox("⚡ 快捷操作")
        action_layout = QHBoxLayout(action_group)

        self.start_btn = QPushButton("▶️ 开始监测")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2ecc71; }
            QPushButton:pressed { background-color: #219a52; }
        """)
        self.start_btn.clicked.connect(self._toggle_monitoring)

        self.overlay_btn = QPushButton("👁️ 显示悬浮窗")
        self.overlay_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5dade2; }
            QPushButton:pressed { background-color: #2980b9; }
        """)
        self.overlay_btn.clicked.connect(self._toggle_overlay)

        action_layout.addWidget(self.start_btn)
        action_layout.addWidget(self.overlay_btn)

        layout.addWidget(action_group)

        # 日志区域
        log_group = QGroupBox("📝 运行日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(100)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #2ecc71;
                padding: 10px;
                border-radius: 5px;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 12px;
            }
        """)
        self.log_text.setPlaceholderText("等待启动...")
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        # 弹性空间
        layout.addStretch()

    def _setup_styles(self):
        """设置整体样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dcdde1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTableWidget {
                border: 1px solid #dcdde1;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 5px;
                font-weight: bold;
            }
        """)

    def _setup_tray(self):
        """设置系统托盘"""
        self.tray = QSystemTrayIcon(self)

        # 创建默认图标（如果找不到图标文件）
        icon = QIcon()
        self.tray.setIcon(icon)
        self.tray.setVisible(True)
        self.tray.setToolTip("三角洲助手")

        # 托盘菜单
        menu = QMenu()

        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        menu.addAction(show_action)

        overlay_action = QAction("显示悬浮窗", self)
        overlay_action.triggered.connect(self.show_overlay_signal.emit)
        menu.addAction(overlay_action)

        menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)

    def _tray_activated(self, reason):
        """托盘图标被点击"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()

    def _toggle_monitoring(self):
        """切换监测状态"""
        if self._is_monitoring:
            self._is_monitoring = False
            self.start_btn.setText("▶️ 开始监测")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    padding: 12px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #2ecc71; }
            """)
            self.stop_monitoring_signal.emit()
        else:
            self._is_monitoring = True
            self.start_btn.setText("⏹️ 停止监测")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    padding: 12px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #c0392b; }
            """)
            self.start_monitoring_signal.emit()

    def _toggle_overlay(self):
        """切换悬浮窗状态"""
        if self.overlay_btn.text() == "👁️ 显示悬浮窗":
            self.overlay_btn.setText("🙈 隐藏悬浮窗")
            self.show_overlay_signal.emit()
        else:
            self.overlay_btn.setText("👁️ 显示悬浮窗")
            self.hide_overlay_signal.emit()

    def _update_status(self):
        """更新状态显示"""
        # 可以在这里添加定期状态更新
        pass

    @Slot(bool)
    def update_game_status(self, detected: bool):
        """更新游戏检测状态"""
        if detected:
            self.game_status_label.setText("游戏状态: ✅ 已检测")
            self.game_status_label.setStyleSheet(
                "color: #27ae60; font-size: 14px; font-weight: bold;"
            )
        else:
            self.game_status_label.setText("游戏状态: ❌ 未检测")
            self.game_status_label.setStyleSheet(
                "color: #e74c3c; font-size: 14px; font-weight: bold;"
            )

    @Slot(bool)
    def update_map_status(self, is_open: bool):
        """更新地图状态"""
        if is_open:
            self.map_status_label.setText("地图状态: 🔴 开启")
            self.map_status_label.setStyleSheet(
                "color: #e74c3c; font-size: 14px; font-weight: bold;"
            )
        else:
            self.map_status_label.setText("地图状态: 🟢 关闭")
            self.map_status_label.setStyleSheet(
                "color: #27ae60; font-size: 14px; font-weight: bold;"
            )

    @Slot(str)
    def add_log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    @Slot(int, int, int)
    def update_stats(self, materials: int, explored: int, value: int):
        """更新统计数据"""
        self.stats_table.setItem(0, 1, QTableWidgetItem(str(materials)))
        self.stats_table.setItem(1, 1, QTableWidgetItem(f"{explored}%"))
        self.stats_table.setItem(2, 1, QTableWidgetItem(f"{value}万"))

        # 更新进度条
        progress = min(materials * 10, 100)
        self.material_progress.setValue(progress)

    def closeEvent(self, event):
        """关闭事件 - 最小化到托盘"""
        event.ignore()
        self.hide()
        self.tray.showMessage(
            "三角洲助手", "程序已最小化到系统托盘", QSystemTrayIcon.Information, 2000
        )

    def _quit(self):
        """完全退出"""
        self.tray.hide()
        QApplication.quit()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # 模拟数据
    window.update_game_status(True)
    window.update_map_status(False)
    window.add_log("程序启动成功")
    window.add_log("等待游戏运行...")

    sys.exit(app.exec())
