"""
屏幕捕获模块

使用dxcam实现高性能屏幕捕获
"""

import numpy as np
from typing import Optional, Tuple, Callable
import threading
import queue
import time
from dataclasses import dataclass
from loguru import logger


@dataclass
class CaptureConfig:
    """捕获配置"""

    target_fps: int = 60
    region: Optional[Tuple[int, int, int, int]] = None  # (left, top, width, height)
    buffer_size: int = 2  # 帧队列大小


class ScreenCapture:
    """
    高性能屏幕捕获器

    使用dxcam库实现240FPS屏幕捕获
    支持区域捕获和帧队列缓冲
    """

    def __init__(self, config: Optional[CaptureConfig] = None):
        """
        初始化捕获器

        Args:
            config: 捕获配置，默认使用CaptureConfig()
        """
        self.config = config or CaptureConfig()
        self.camera = None
        self.frame_queue = queue.Queue(maxsize=self.config.buffer_size)
        self._running = False
        self._capture_thread: Optional[threading.Thread] = None
        self._last_frame_time = 0.0
        self._frame_count = 0
        self._fps = 0.0

        logger.info(
            f"ScreenCapture initialized: fps={self.config.target_fps}, region={self.config.region}"
        )

    def start(self) -> bool:
        """
        启动捕获

        Returns:
            是否成功启动
        """
        try:
            import dxcam

            if self.camera is None:
                self.camera = dxcam.create()
                self.camera.start(
                    target_fps=self.config.target_fps,
                    video_mode=True,  # 启用缓冲，降低延迟
                    region=self.config.region,
                )

            self._running = True
            self._capture_thread = threading.Thread(
                target=self._capture_loop, daemon=True
            )
            self._capture_thread.start()

            logger.info("ScreenCapture started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start ScreenCapture: {e}")
            return False

    def _capture_loop(self):
        """捕获循环（在后台线程运行）"""
        while self._running:
            try:
                if self.camera:
                    frame = self.camera.get_latest_frame()
                    if frame is not None:
                        # 丢弃旧帧，保持队列最新
                        if self.frame_queue.full():
                            try:
                                self.frame_queue.get_nowait()
                            except queue.Empty:
                                pass
                        self.frame_queue.put(frame)

                        # 计算FPS
                        self._frame_count += 1
                        current_time = time.time()
                        if current_time - self._last_frame_time >= 1.0:
                            self._fps = self._frame_count / (
                                current_time - self._last_frame_time
                            )
                            self._frame_count = 0
                            self._last_frame_time = current_time

            except Exception as e:
                logger.error(f"Capture loop error: {e}")
                time.sleep(0.01)

    def get_frame(self, timeout: float = 0.1) -> Optional[np.ndarray]:
        """
        获取最新帧

        Args:
            timeout: 等待超时时间（秒）

        Returns:
            图像帧（numpy数组，BGR格式），超时返回None
        """
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_fps(self) -> float:
        """获取当前帧率"""
        return self._fps

    def stop(self):
        """停止捕获"""
        self._running = False
        if self._capture_thread:
            self._capture_thread.join(timeout=1.0)
        if self.camera:
            self.camera.stop()
            self.camera = None
        logger.info("ScreenCapture stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False


class MockCapture:
    """模拟捕获器（用于测试）"""

    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height
        self._running = False

    def start(self) -> bool:
        self._running = True
        return True

    def get_frame(self, timeout: float = 0.1) -> Optional[np.ndarray]:
        if not self._running:
            return None
        # 生成随机测试图像
        return np.random.randint(0, 255, (self.height, self.width, 3), dtype=np.uint8)

    def get_fps(self) -> float:
        return 60.0

    def stop(self):
        self._running = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
