"""
OCR引擎模块测试
"""

import pytest
import numpy as np
from core.ocr_engine import OCREngine, MaterialPoint, MockOCREngine


class TestOCREngine:
    """测试OCR引擎功能"""

    def test_mock_ocr_initialization(self):
        """测试模拟OCR初始化"""
        ocr = MockOCREngine()
        assert ocr.initialize() == True

    def test_mock_ocr_recognize(self):
        """测试模拟OCR识别"""
        ocr = MockOCREngine()

        # 创建测试图像
        image = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

        # 识别
        results = ocr.recognize(image)

        # 验证结果
        assert len(results) > 0
        assert isinstance(results[0], MaterialPoint)
        assert hasattr(results[0], "text")
        assert hasattr(results[0], "confidence")
        assert hasattr(results[0], "bbox")
        assert hasattr(results[0], "center")

    def test_mock_ocr_with_roi(self):
        """测试ROI裁剪识别"""
        ocr = MockOCREngine()

        image = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        roi = (100, 100, 500, 500)

        results = ocr.recognize(image, roi=roi)
        assert len(results) > 0

    def test_ocr_stats(self):
        """测试性能统计"""
        ocr = MockOCREngine()

        image = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        ocr.recognize(image)

        stats = ocr.get_stats()
        assert "calls" in stats
        assert "avg_time_ms" in stats
        assert stats["calls"] == 1


class TestMaterialPoint:
    """测试MaterialPoint数据类"""

    def test_material_point_creation(self):
        """测试创建MaterialPoint"""
        point = MaterialPoint(
            text="医疗包",
            confidence=0.95,
            bbox=(100, 100, 200, 150),
            center=(150, 125),
            material_type="medical",
        )

        assert point.text == "医疗包"
        assert point.confidence == 0.95
        assert point.bbox == (100, 100, 200, 150)
        assert point.center == (150, 125)
        assert point.material_type == "medical"

    def test_material_point_optional_type(self):
        """测试可选的material_type"""
        point = MaterialPoint(
            text="未知物品",
            confidence=0.8,
            bbox=(100, 100, 200, 150),
            center=(150, 125),
        )

        assert point.material_type is None


class TestOCRPerformance:
    """OCR性能测试"""

    def test_recognition_speed(self):
        """测试识别速度"""
        ocr = MockOCREngine()
        image = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

        import time

        start = time.time()
        results = ocr.recognize(image)
        elapsed = time.time() - start

        # 模拟OCR应该很快
        assert elapsed < 1.0
