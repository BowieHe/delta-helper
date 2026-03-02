"""
地图检测模块测试
"""

import pytest
import time
import threading
from core.map_detector import MapDetector, DetectionConfig, MockMapDetector
from core.capture import MockCapture


class TestMapDetector:
    """测试地图检测功能"""

    def test_mock_detector(self):
        """测试模拟检测器"""
        detector = MockMapDetector()

        # 添加监听器
        events = []

        def listener(state, source):
            events.append((state, source))

        detector.add_listener(listener)

        # 启动
        detector.start()

        # 强制设置状态
        detector.force_state(True)
        assert detector.is_map_open == True

        detector.force_state(False)
        assert detector.is_map_open == False

        # 停止
        detector.stop()

    def test_detection_config(self):
        """测试检测配置"""
        config = DetectionConfig(
            map_key="m", check_interval=0.05, change_threshold=5000
        )
        assert config.map_key == "m"
        assert config.check_interval == 0.05
        assert config.change_threshold == 5000

    def test_config_default_values(self):
        """测试默认配置值"""
        config = DetectionConfig()
        assert config.map_key == "m"
        assert config.confirm_count == 2
        assert config.history_size == 5


class TestMapDetectorIntegration:
    """集成测试"""

    def test_detector_with_capture(self):
        """测试检测器与捕获器集成"""
        capture = MockCapture()
        capture.start()

        detector = MapDetector(capture)

        # 添加监听器
        events = []

        def listener(state, source):
            events.append((state, source))

        detector.add_listener(listener)

        # 启动检测
        detector.start()
        time.sleep(0.1)

        # 停止
        detector.stop()
        capture.stop()
