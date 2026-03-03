"""
统计对话框模块

提供3标签页的数据统计界面：
- 当前会话：实时效率追踪
- 历史记录：过往游戏记录
- 趋势分析：总体统计数据
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QPushButton,
    QComboBox,
    QGroupBox,
    QGridLayout,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QListWidget,
    QWidget,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from typing import Optional
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.database import DatabaseManager
from analytics.calculator import EfficiencyCalculator

class StatsDialog(QDialog):
    """数据统计对话框"""

    def __init__(
        self, db: DatabaseManager, calculator: EfficiencyCalculator, parent=None
    ):
        super().__init__(parent)
        self.db = db
        self.calculator = calculator
        self.setWindowTitle("📊 三角洲助手 - 数据统计")
        self.setGeometry(200, 200, 900, 700)
        self._setup_ui()
        self._start_refresh_timer()
        self.refresh_data()

    def _setup_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()

        # 标题
        title = QLabel("📊 游戏数据统计")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ecf0f1; margin: 10px;")
        layout.addWidget(title)

        # Tab组件
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #34495e;
                background: #2c3e50;
            }
            QTabBar::tab {
                background: #34495e;
                color: #bdc3c7;
                padding: 10px 20px;
                border: 1px solid #2c3e50;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
        """)

        # 三个标签页
        self.tab_current = self._setup_current_tab()
        self.tab_history = self._setup_history_tab()
        self.tab_trends = self._setup_trends_tab()

        self.tabs.addTab(self.tab_current, "🎮 当前会话")
        self.tabs.addTab(self.tab_history, "📜 历史记录")
        self.tabs.addTab(self.tab_trends, "📈 趋势分析")

        layout.addWidget(self.tabs)

        # 底部按钮
        btn_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("🔄 刷新数据")
        self.refresh_btn.setStyleSheet(self._button_style())
        self.refresh_btn.clicked.connect(self.refresh_data)
        btn_layout.addWidget(self.refresh_btn)

        btn_layout.addStretch()

        self.export_btn = QPushButton("💾 导出CSV")
        self.export_btn.setStyleSheet(self._button_style("#27ae60"))
        self.export_btn.clicked.connect(self._export_csv)
        btn_layout.addWidget(self.export_btn)

        self.close_btn = QPushButton("❌ 关闭")
        self.close_btn.setStyleSheet(self._button_style("#e74c3c"))
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.setStyleSheet("background-color: #2c3e50;")

    def _button_style(self, color: str = "#3498db") -> str:
        """按钮样式"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}aa;
            }}
        """

    def _setup_current_tab(self) -> QWidget:
        """设置当前会话标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 实时统计卡片
        stats_group = QGroupBox("⏱️ 实时统计")
        stats_group.setStyleSheet(self._group_style())
        stats_layout = QGridLayout()

        # 四个统计项
        self.lbl_total_value = self._create_stat_label("💰 当前收益", "0")
        self.lbl_time = self._create_stat_label("⏱️ 游戏时长", "00:00")
        self.lbl_efficiency = self._create_stat_label("⚡ 效率", "0/min")
        self.lbl_estimated = self._create_stat_label("📈 预估最终", "0")

        stats_layout.addWidget(self.lbl_total_value, 0, 0)
        stats_layout.addWidget(self.lbl_time, 0, 1)
        stats_layout.addWidget(self.lbl_efficiency, 1, 0)
        stats_layout.addWidget(self.lbl_estimated, 1, 1)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # 实时摘要文本
        self.lbl_live_summary = QLabel("等待数据...")
        self.lbl_live_summary.setFont(QFont("Microsoft YaHei", 12))
        self.lbl_live_summary.setStyleSheet("""
            color: #2ecc71;
            background: #1a252f;
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #27ae60;
        """)
        self.lbl_live_summary.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_live_summary)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _setup_history_tab(self) -> QWidget:
        """设置历史记录标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 过滤器
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("时间范围:"))
        filter_layout.addWidget(QLabel("时间范围:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["最近7天", "最近30天", "全部"])
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # 历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            ["时间", "地图", "结果", "物资数", "总价值", "效率(价值/分)"]
        )
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setStyleSheet(self._table_style())
        self.history_table.setAlternatingRowColors(True)
        layout.addWidget(self.history_table)

        widget.setLayout(layout)
        return widget

    def _setup_trends_tab(self) -> QWidget:
        """设置趋势分析标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 总体统计卡片
        overview_group = QGroupBox("📊 总体统计")
        overview_group.setStyleSheet(self._group_style())
        overview_layout = QGridLayout()

        self.lbl_total_games = self._create_stat_label("🎮 总局数", "0")
        self.lbl_all_value = self._create_stat_label("💰 总价值", "0")
        self.lbl_success_rate = self._create_stat_label("✅ 成功率", "0%")
        self.lbl_avg_eff = self._create_stat_label("⚡ 平均效率", "0/min")

        overview_layout.addWidget(self.lbl_total_games, 0, 0)
        overview_layout.addWidget(self.lbl_all_value, 0, 1)
        overview_layout.addWidget(self.lbl_success_rate, 1, 0)
        overview_layout.addWidget(self.lbl_avg_eff, 1, 1)

        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)

        # 热门物资
        items_group = QGroupBox("🔥 热门物资")
        items_group.setStyleSheet(self._group_style())
        items_layout = QVBoxLayout()

        self.top_items_list = QListWidget()
        self.top_items_list.setStyleSheet("""
            QListWidget {
                background: #34495e;
                color: #ecf0f1;
                border: 1px solid #2c3e50;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #2c3e50;
            }
            QListWidget::item:alternate {
                background: #3d566e;
            }
        """)
        items_layout.addWidget(self.top_items_list)
        items_group.setLayout(items_layout)
        layout.addWidget(items_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_stat_label(self, title: str, value: str) -> QLabel:
        """创建统计标签"""
        label = QLabel(f"<h3>{title}</h3><h1>{value}</h1>")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: #ecf0f1;
                border-radius: 10px;
                padding: 15px;
                min-width: 150px;
            }
            QLabel h3 {
                color: #bdc3c7;
                font-size: 12px;
                margin-bottom: 5px;
            }
            QLabel h1 {
                color: #3498db;
                font-size: 24px;
                margin: 0;
            }
        """)
        return label

    def _group_style(self) -> str:
        """分组样式"""
        return """
            QGroupBox {
                color: #ecf0f1;
                font-weight: bold;
                border: 2px solid #34495e;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """

    def _table_style(self) -> str:
        """表格样式"""
        return """
            QTableWidget {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #2c3e50;
                border-radius: 5px;
                gridline-color: #2c3e50;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: #ecf0f1;
                padding: 10px;
                border: 1px solid #34495e;
                font-weight: bold;
            }
        """

    def _start_refresh_timer(self):
        """启动自动刷新定时器"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)  # 每5秒刷新

    def refresh_data(self):
        """刷新所有数据"""
        self._refresh_current_tab()
        self._refresh_history_tab()
        self._refresh_trends_tab()

    def _refresh_current_tab(self):
        """刷新当前会话标签页"""
        # 从calculator获取实时数据
        stats = self.calculator.get_stats()

        # 更新显示
        total_value = stats.get("total_value", 0)
        elapsed = stats.get("elapsed_seconds", 0)
        vpm = stats.get("value_per_minute", 0)
        estimated = stats.get("estimated_final", 0)

        self.lbl_total_value.setText(f"<h3>💰 当前收益</h3><h1>{total_value:,}</h1>")

        minutes = elapsed // 60
        seconds = elapsed % 60
        self.lbl_time.setText(
            f"<h3>⏱️ 游戏时长</h3><h1>{minutes:02d}:{seconds:02d}</h1>"
        )

        self.lbl_efficiency.setText(f"<h3>⚡ 效率</h3><h1>{int(vpm):,}/min</h1>")
        self.lbl_estimated.setText(f"<h3>📈 预估最终</h3><h1>{estimated:,}</h1>")

        # 更新摘要
        summary = self.calculator.get_live_summary()
        self.lbl_live_summary.setText(summary)

    def _refresh_history_tab(self):
        """刷新历史记录标签页"""
        # 获取天数
        days_map = {0: 7, 1: 30, 2: 365}
        days = days_map.get(self.filter_combo.currentIndex(), 7)

        sessions = self.db.get_recent_sessions(limit=100)

        self.history_table.setRowCount(len(sessions))
        for i, session in enumerate(sessions):
            # 时间
            start_time = session.get("start_time", "")
            try:
                dt = datetime.fromisoformat(start_time)
                time_str = dt.strftime("%m-%d %H:%M")
            except:
                time_str = start_time
            self.history_table.setItem(i, 0, QTableWidgetItem(time_str))

            # 地图
            self.history_table.setItem(
                i, 1, QTableWidgetItem(session.get("map_name", "unknown"))
            )

            # 结果
            result = session.get("result", "")
            result_text = {
                "success": "✅ 成功",
                "death": "💀 阵亡",
                "disconnect": "⚠️ 断线",
            }.get(result, result)
            self.history_table.setItem(i, 2, QTableWidgetItem(result_text))

            # 物资数
            self.history_table.setItem(
                i, 3, QTableWidgetItem(str(session.get("materials_count", 0)))
            )

            # 总价值
            self.history_table.setItem(
                i, 4, QTableWidgetItem(f"{session.get('total_value', 0):,}")
            )

            # 效率
            vpm = session.get("value_per_minute", 0)
            self.history_table.setItem(i, 5, QTableWidgetItem(f"{int(vpm):,}"))

    def _refresh_trends_tab(self):
        """刷新趋势分析标签页"""
        stats = self.db.get_overall_stats(days=30)

        total_games = stats.get("total_games", 0)
        total_value = stats.get("total_value", 0)
        success_rate = stats.get("success_rate", 0) or 0
        avg_eff = stats.get("avg_efficiency", 0) or 0

        self.lbl_total_games.setText(f"<h3>🎮 总局数</h3><h1>{total_games}</h1>")
        self.lbl_all_value.setText(f"<h3>💰 总价值</h3><h1>{total_value:,}</h1>")
        self.lbl_success_rate.setText(f"<h3>✅ 成功率</h3><h1>{success_rate:.1f}%</h1>")
        self.lbl_avg_eff.setText(f"<h3>⚡ 平均效率</h3><h1>{int(avg_eff):,}/min</h1>")

        # 热门物资
        top_items = self.db.get_top_items(limit=10)
        self.top_items_list.clear()
        for item in top_items:
            name = item.get("name", "未知")
            count = item.get("times_found", 0)
            value = item.get("total_value", 0)
            self.top_items_list.addItem(f"{name} - 发现 {count} 次 (总价值: {value:,})")

    def _on_filter_changed(self):
        """过滤器改变"""
        self._refresh_history_tab()

    def _export_csv(self):
        """导出CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "导出数据",
            f"delta_stats_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Files (*.csv)",
        )

        if filename:
            if self.db.export_to_csv(filename):
                QMessageBox.information(self, "导出成功", f"数据已导出到:\n{filename}")
            else:
                QMessageBox.warning(self, "导出失败", "导出数据时出错，请重试")

    def closeEvent(self, event):
        """关闭事件"""
        self.refresh_timer.stop()
        event.accept()
