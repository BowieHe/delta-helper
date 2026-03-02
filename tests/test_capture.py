"""
屏幕捕获模块测试
"""

import pytest
import numpy as np
import time
from core.capture import ScreenCapture, CaptureConfig, MockCapture


class TestScreenCapture:
    """测试屏幕捕获功能"""

    def test_mock_capture_basic(self):
        """测试模拟捕获基本功能"""
        capture = MockCapture(width=1920, height=1080)

        # 启动
        assert capture.start() == True

        # 获取帧
        frame = capture.get_frame()
        assert frame is not None
        assert frame.shape == (1080, 1920, 3)
        assert frame.dtype == np.uint8

        # 停止
        capture.stop()

    def test_mock_capture_fps(self):
        """测试帧率"""
        capture = MockCapture()
        capture.start()

        fps = capture.get_fps()
        assert fps > 0

        capture.stop()

    def test_capture_config(self):
        """测试配置"""
        config = CaptureConfig(target_fps=60, region=(0, 0, 800, 600))
        assert config.target_fps == 60
        assert config.region == (0, 0, 800, 600)

    def test_context_manager(self):
        """测试上下文管理器"""
        with MockCapture() as capture:
            frame = capture.get_frame()
            assert frame is not None


class TestPerformance:
    """性能测试"""

    def test_capture_speed(self):
        """测试捕获速度"""
        capture = MockCapture()
        capture.start()

        start = time.time()
        frame_count = 0

        # 尝试获取60帧
        for _ in range(60):
            frame = capture.get_frame(timeout=0.1)
            if frame is not None:
                frame_count += 1

        elapsed = time.time() - start

        capture.stop()

        # 应该在合理时间内完成
        assert elapsed < 5.0  # 5秒内
        assert frame_count > 0
