"""
三角洲游戏助手 - 主入口

程序入口，整合所有模块
"""

import sys
import os
import time
import threading
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot
from loguru import logger

# 添加src到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import (
    ScreenCapture,
    MapDetector,
    DetectionConfig,
    OCREngine,
    RouteOptimizer,
    MaterialNode,
    Config,
)
from ui import MainWindow, PetOverlay


class DeltaHelper(QObject):
    """
    三角洲游戏助手主控制器

    整合所有模块，协调工作流
    """

    # 信号
    map_state_changed = Signal(bool)
    materials_detected = Signal(list)
    route_calculated = Signal(list)
    log_message = Signal(str)

    def __init__(self):
        super().__init__()

        # 配置
        self.config = Config()

        # 核心模块
        self.capture: Optional[ScreenCapture] = None
        self.map_detector: Optional[MapDetector] = None
        self.ocr: Optional[OCREngine] = None
        self.route_optimizer: Optional[RouteOptimizer] = None

        # UI
        self.main_window: Optional[MainWindow] = None
        self.overlay: Optional[PetOverlay] = None

        # 状态
        self._running = False
        self._current_materials = []
        self._player_pos = (960, 540)  # 默认屏幕中心

        self._setup_logging()
        logger.info("DeltaHelper initialized")

    def _setup_logging(self):
        """配置日志"""
        logger.add(
            "logs/delta_helper.log",
            rotation="1 day",
            retention="7 days",
            level="INFO",
            encoding="utf-8",
        )

    def initialize(self) -> bool:
        """
        初始化所有模块

        Returns:
            是否成功初始化
        """
        try:
            logger.info("Initializing modules...")

            # 1. 屏幕捕获
            capture_config = self.config.capture
            self.capture = ScreenCapture(capture_config)
            if not self.capture.start():
                logger.error("Failed to start capture")
                return False
            logger.info("ScreenCapture started")

            # 2. 地图检测
            detection_config = self.config.detection
            self.map_detector = MapDetector(self.capture, detection_config)
            self.map_detector.add_listener(self._on_map_state_change)
            logger.info("MapDetector initialized")

            # 3. OCR引擎
            ocr_config = self.config.ocr
            self.ocr = OCREngine(
                use_gpu=ocr_config.use_gpu, use_tensorrt=ocr_config.use_tensorrt
            )
            logger.info("OCREngine initialized")

            # 4. 路线规划
            self.route_optimizer = RouteOptimizer()
            logger.info("RouteOptimizer initialized")

            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    def _on_map_state_change(self, is_open: bool, source: str):
        """地图状态变化回调"""
        logger.info(f"Map state changed: {is_open} (source: {source})")
        self.map_state_changed.emit(is_open)

        if self.main_window:
            self.main_window.update_map_status(is_open)

        if is_open:
            # 地图打开，开始识别
            self._recognize_materials()
        else:
            # 地图关闭，清除显示
            if self.overlay:
                self.overlay.clear_route()

    def _recognize_materials(self):
        """识别物资"""
        try:
            # 获取当前帧
            frame = self.capture.get_frame(timeout=0.5)
            if frame is None:
                logger.warning("No frame available for OCR")
                return

            # OCR识别
            materials = self.ocr.recognize(frame)

            if materials:
                logger.info(f"Detected {len(materials)} materials")
                self._current_materials = materials
                self.materials_detected.emit(materials)

                # 更新UI
                if self.main_window:
                    self.main_window.add_log(f"识别到 {len(materials)} 个物资点")

                # 规划路线
                self._plan_route()
            else:
                logger.info("No materials detected")

        except Exception as e:
            logger.error(f"Material recognition failed: {e}")

    def _plan_route(self):
        """规划路线"""
        try:
            if not self._current_materials:
                return

            # 转换为MaterialNode
            material_nodes = []
            for m in self._current_materials:
                node = MaterialNode(
                    x=m.center[0],
                    y=m.center[1],
                    value=m.confidence * 100,  # 置信度作为价值
                    name=m.text,
                )
                material_nodes.append(node)

            # 优化路线
            optimized = self.route_optimizer.optimize_route(
                material_nodes, self._player_pos, algorithm="weighted"
            )

            self.route_calculated.emit(optimized)

            # 更新悬浮窗
            if self.overlay and optimized:
                points = [(m.x, m.y) for m in optimized]
                self.overlay.set_route(points, self._player_pos)
                self.overlay.update_info(
                    f"🎮 地图已开启\n"
                    f"📦 发现 {len(optimized)} 个物资点\n"
                    f"➡️ 已规划最优路线"
                )

            logger.info(f"Route planned: {len(optimized)} points")

        except Exception as e:
            logger.error(f"Route planning failed: {e}")

    def start(self):
        """启动助手"""
        if self._running:
            logger.warning("Already running")
            return

        if not self.initialize():
            logger.error("Initialization failed")
            return

        self._running = True
        self.map_detector.start()

        logger.info("DeltaHelper started")
        self.log_message.emit("助手已启动")

    def stop(self):
        """停止助手"""
        self._running = False

        if self.map_detector:
            self.map_detector.stop()
        if self.capture:
            self.capture.stop()

        logger.info("DeltaHelper stopped")
        self.log_message.emit("助手已停止")

    def show_overlay(self):
        """显示悬浮窗"""
        if self.overlay is None:
            self.overlay = PetOverlay()
        self.overlay.show()
        self.overlay.fade_in()

    def hide_overlay(self):
        """隐藏悬浮窗"""
        if self.overlay:
            self.overlay.fade_out()

    def run(self):
        """运行应用"""
        # 创建Qt应用
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        # 创建主窗口
        self.main_window = MainWindow(self.config)
        self.main_window.show()

        # 连接信号
        self.main_window.start_monitoring_signal.connect(self.start)
        self.main_window.stop_monitoring_signal.connect(self.stop)
        self.main_window.show_overlay_signal.connect(self.show_overlay)
        self.main_window.hide_overlay_signal.connect(self.hide_overlay)

        self.log_message.connect(self.main_window.add_log)
        self.map_state_changed.connect(self.main_window.update_map_status)

        # 添加启动日志
        self.main_window.add_log("三角洲助手已启动")
        self.main_window.add_log("点击'开始监测'启动功能")

        # 运行
        return app.exec()


def main():
    """主函数"""
    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)

    # 创建并运行助手
    helper = DeltaHelper()
    return helper.run()


if __name__ == "__main__":
    sys.exit(main())
