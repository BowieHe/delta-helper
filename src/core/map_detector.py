"""
地图检测模块

实现游戏地图打开状态的自动检测
采用混合策略：键盘监听（主）+ 像素变化（确认）
"""

import cv2
import numpy as np
import time
import threading
from typing import Optional, Callable, List, Tuple
from dataclasses import dataclass, field
from collections import deque
from loguru import logger

from .capture import ScreenCapture


@dataclass
class DetectionConfig:
    """检测配置"""

    map_key: str = "m"  # 地图按键
    check_interval: float = 0.05  # 检测间隔 50ms
    change_threshold: int = 5000  # 像素变化阈值
    change_ratio_threshold: float = 0.1  # 变化比例阈值
    confirm_count: int = 2  # 确认次数
    history_size: int = 5  # 平滑窗口大小
    detect_regions: List[Tuple[int, int, int, int]] = field(
        default_factory=lambda: [
            (100, 50, 1820, 1030),  # 全屏地图区域
            (50, 50, 400, 400),  # 小地图区域
        ]
    )


class MapDetector:
    """
    游戏地图状态检测器

    采用混合策略：
    1. 优先检测键盘状态（即时响应）
    2. 键盘不稳定时，用像素变化确认
    """

    def __init__(
        self, capture: ScreenCapture, config: Optional[DetectionConfig] = None
    ):
        """
        初始化检测器

        Args:
            capture: 屏幕捕获器实例
            config: 检测配置
        """
        self.capture = capture
        self.config = config or DetectionConfig()

        self.is_map_open = False
        self._state_history = deque(maxlen=self.config.history_size)
        self._listeners: List[Callable[[bool, str], None]] = []

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_keyboard_state = False

        logger.info("MapDetector initialized")

    def add_listener(self, callback: Callable[[bool, str], None]):
        """
        添加状态变化监听器

        Args:
            callback: 回调函数，参数为(状态, 检测来源)
        """
        self._listeners.append(callback)

    def _notify(self, state: bool, source: str):
        """通知所有监听器"""
        for listener in self._listeners:
            try:
                listener(state, source)
            except Exception as e:
                logger.error(f"Listener error: {e}")

    def _check_keyboard(self) -> bool:
        """检查地图键状态"""
        try:
            import keyboard

            return keyboard.is_pressed(self.config.map_key)
        except Exception as e:
            logger.error(f"Keyboard check error: {e}")
            return False

    def _check_pixel_change(
        self, region: Tuple[int, int, int, int]
    ) -> Tuple[bool, int, float]:
        """
        检查区域像素变化

        Args:
            region: 检测区域 (x1, y1, x2, y2)

        Returns:
            (是否有变化, 变化像素数, 变化比例)
        """
        # 连续截取两帧
        frame1 = self.capture.get_frame()
        time.sleep(0.03)
        frame2 = self.capture.get_frame()

        if frame1 is None or frame2 is None:
            return False, 0, 0.0

        # 裁剪到检测区域
        x1, y1, x2, y2 = region
        h, w = frame1.shape[:2]

        # 边界检查
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            return False, 0, 0.0

        roi1 = frame1[y1:y2, x1:x2]
        roi2 = frame2[y1:y2, x1:x2]

        # 计算变化
        gray1 = cv2.cvtColor(roi1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(roi2, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(gray1, gray2)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

        change_pixels = cv2.countNonZero(thresh)
        total_pixels = diff.shape[0] * diff.shape[1]
        change_ratio = change_pixels / total_pixels if total_pixels > 0 else 0.0

        is_changed = (
            change_pixels > self.config.change_threshold
            or change_ratio > self.config.change_ratio_threshold
        )

        return is_changed, change_pixels, change_ratio

    def _detect(self) -> Tuple[bool, str]:
        """
        执行一次检测

        Returns:
            (地图是否打开, 检测来源)
        """
        # 1. 键盘检测
        kb_state = self._check_keyboard()

        # 2. 像素变化检测（多区域）
        px_state = False
        max_change_ratio = 0.0

        for region in self.config.detect_regions:
            try:
                is_changed, pixels, ratio = self._check_pixel_change(region)
                max_change_ratio = max(max_change_ratio, ratio)
                if is_changed:
                    px_state = True
                    break
            except Exception as e:
                logger.error(f"Pixel check error: {e}")

        # 3. 状态融合
        # 如果键盘状态变化，优先使用键盘
        if kb_state != self._last_keyboard_state:
            self._last_keyboard_state = kb_state
            return kb_state, "keyboard"

        # 否则使用像素变化
        return px_state, "pixel"

    def _detection_loop(self):
        """检测循环"""
        last_state = False
        stable_count = 0

        while self._running:
            try:
                state, source = self._detect()

                # 平滑处理（消除抖动）
                self._state_history.append(state)
                smoothed = sum(self._state_history) / len(self._state_history) > 0.5

                # 状态变化时通知
                if smoothed != last_state:
                    stable_count += 1
                    if stable_count >= self.config.confirm_count:
                        self.is_map_open = smoothed
                        self._notify(smoothed, source)
                        last_state = smoothed
                        stable_count = 0
                else:
                    stable_count = 0

            except Exception as e:
                logger.error(f"Detection loop error: {e}")

            time.sleep(self.config.check_interval)

    def start(self):
        """启动检测"""
        if self._running:
            logger.warning("MapDetector already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._detection_loop, daemon=True)
        self._thread.start()
        logger.info("MapDetector started")

    def stop(self):
        """停止检测"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        logger.info("MapDetector stopped")

    def force_state(self, state: bool):
        """强制设置状态（用于测试）"""
        self.is_map_open = state
        self._notify(state, "manual")


class MockMapDetector:
    """模拟地图检测器（用于测试）"""

    def __init__(self, *args, **kwargs):
        self.is_map_open = False
        self._listeners = []

    def add_listener(self, callback):
        self._listeners.append(callback)

    def start(self):
        pass

    def stop(self):
        pass

    def force_state(self, state: bool):
        self.is_map_open = state
        for listener in self._listeners:
            listener(state, "mock")
