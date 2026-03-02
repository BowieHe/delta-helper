"""
OCR识别模块

使用PaddleOCR实现游戏物资文字识别
支持GPU加速和TensorRT优化
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
import time
from loguru import logger


@dataclass
class MaterialPoint:
    """物资点"""

    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]
    material_type: Optional[str] = None


class OCREngine:
    """
    OCR识别引擎

    基于PaddleOCR，支持：
    - GPU加速
    - TensorRT优化
    - ROI区域裁剪
    """

    # 物资类型关键词映射
    MATERIAL_KEYWORDS = {
        "weapon": ["枪", "步枪", "狙击", "手枪", "弹药", "弹匣", "枪管"],
        "medical": ["医疗", "急救", "绷带", "血包", "药", "注射器"],
        "equipment": ["头盔", "护甲", "背包", "弹挂", "护甲板"],
        "valuables": ["金条", "显卡", "情报", "钥匙", "加密", "硬盘"],
        "ammo": ["弹药", "子弹", "霰弹", "榴弹"],
    }

    def __init__(self, use_gpu: bool = True, use_tensorrt: bool = True):
        """
        初始化OCR引擎

        Args:
            use_gpu: 是否使用GPU
            use_tensorrt: 是否使用TensorRT加速
        """
        self.use_gpu = use_gpu
        self.use_tensorrt = use_tensorrt
        self.ocr = None
        self._initialized = False

        # 性能统计
        self._total_calls = 0
        self._total_time = 0.0

    def initialize(self) -> bool:
        """
        初始化OCR引擎

        Returns:
            是否成功初始化
        """
        if self._initialized:
            return True

        try:
            from paddleocr import PaddleOCR

            logger.info("Initializing OCR engine...")
            start = time.time()

            # 根据硬件选择配置
            if self.use_gpu and self.use_tensorrt:
                logger.info("Using GPU + TensorRT acceleration")
                self.ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang="ch",
                    use_gpu=True,
                    show_log=False,
                    use_tensorrt=True,
                    precision="fp16",
                    det_limit_side_len=640,
                )
            elif self.use_gpu:
                logger.info("Using GPU acceleration")
                self.ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang="ch",
                    use_gpu=True,
                    show_log=False,
                    det_limit_side_len=640,
                )
            else:
                logger.info("Using CPU")
                self.ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang="ch",
                    use_gpu=False,
                    show_log=False,
                    det_limit_side_len=640,
                )

            elapsed = time.time() - start
            logger.info(f"OCR engine initialized in {elapsed:.2f}s")
            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize OCR: {e}")
            return False

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理

        优化步骤：
        1. 对比度增强（CLAHE）
        2. 轻微锐化

        Args:
            image: 输入图像 (BGR格式)

        Returns:
            预处理后的图像
        """
        try:
            # 对比度增强
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

            # 轻微锐化
            kernel = np.array([[-0.5, -0.5, -0.5], [-0.5, 5, -0.5], [-0.5, -0.5, -0.5]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)

            return sharpened
        except Exception as e:
            logger.error(f"Preprocess error: {e}")
            return image

    def recognize(
        self, image: np.ndarray, roi: Optional[Tuple[int, int, int, int]] = None
    ) -> List[MaterialPoint]:
        """
        识别图像中的物资文字

        Args:
            image: 输入图像 (BGR格式)
            roi: 感兴趣区域 (x1, y1, x2, y2)，None表示全图

        Returns:
            识别到的物资点列表
        """
        if not self._initialized:
            if not self.initialize():
                return []

        start_time = time.time()

        try:
            # ROI裁剪
            if roi:
                x1, y1, x2, y2 = roi
                h, w = image.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                if x2 > x1 and y2 > y1:
                    image = image[y1:y2, x1:x2]

            # 预处理
            processed = self.preprocess(image)

            # OCR识别
            result = self.ocr.ocr(processed, cls=True)

            # 解析结果
            materials = []
            if result and result[0]:
                for line in result[0]:
                    if line:
                        bbox, (text, confidence) = line

                        # 过滤低置信度
                        if confidence < 0.5:
                            continue

                        # 转换坐标
                        points = np.array(bbox, dtype=np.int32)
                        x1, y1 = points[:, 0].min(), points[:, 1].min()
                        x2, y2 = points[:, 0].max(), points[:, 1].max()
                        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2

                        # ROI偏移修正
                        if roi:
                            offset_x, offset_y = roi[0], roi[1]
                            x1 += offset_x
                            x2 += offset_x
                            y1 += offset_y
                            y2 += offset_y
                            center_x += offset_x
                            center_y += offset_y

                        # 识别物资类型
                        material_type = self._classify_material(text)

                        material = MaterialPoint(
                            text=text,
                            confidence=confidence,
                            bbox=(x1, y1, x2, y2),
                            center=(center_x, center_y),
                            material_type=material_type,
                        )
                        materials.append(material)

            # 性能统计
            elapsed = time.time() - start_time
            self._total_calls += 1
            self._total_time += elapsed

            avg_time = self._total_time / self._total_calls
            logger.info(
                f"OCR: {len(materials)} materials, {elapsed * 1000:.1f}ms (avg: {avg_time * 1000:.1f}ms)"
            )

            return materials

        except Exception as e:
            logger.error(f"OCR recognition error: {e}")
            return []

    def _classify_material(self, text: str) -> Optional[str]:
        """
        根据文字内容分类物资类型

        Args:
            text: 识别到的文字

        Returns:
            物资类型，无法分类返回None
        """
        text_lower = text.lower()
        for material_type, keywords in self.MATERIAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return material_type
        return None

    def get_stats(self) -> dict:
        """获取性能统计"""
        if self._total_calls == 0:
            return {"calls": 0, "avg_time_ms": 0}
        return {
            "calls": self._total_calls,
            "avg_time_ms": (self._total_time / self._total_calls) * 1000,
        }


class MockOCREngine:
    """模拟OCR引擎（用于测试）"""

    def __init__(self, *args, **kwargs):
        self._initialized = True

    def initialize(self):
        return True

    def recognize(
        self, image: np.ndarray, roi: Optional[Tuple] = None
    ) -> List[MaterialPoint]:
        # 返回模拟数据
        return [
            MaterialPoint("医疗包", 0.95, (100, 100, 200, 150), (150, 125), "medical"),
            MaterialPoint("弹药箱", 0.88, (300, 200, 400, 250), (350, 225), "ammo"),
        ]

    def get_stats(self):
        return {"calls": 1, "avg_time_ms": 10.0}
