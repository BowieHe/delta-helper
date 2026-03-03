"""
配置管理模块
"""

import json
import os
from dataclasses import dataclass, asdict, field
from typing import Optional, Tuple
from pathlib import Path


@dataclass
class CaptureConfig:
    """屏幕捕获配置"""

    fps: int = 60
    region: Optional[Tuple[int, int, int, int]] = None  # (left, top, width, height)


@dataclass
class DetectionConfig:
    """地图检测配置"""

    map_key: str = "m"
    check_interval: float = 0.05
    change_threshold: int = 5000
    change_ratio_threshold: float = 0.1
    confirm_count: int = 2
    history_size: int = 5
    detect_regions: list = field(default_factory=lambda: [
        (100, 50, 1820, 1030),
        (50, 50, 400, 400),
    ])


@dataclass
class OCRConfig:
    """OCR配置"""

    use_gpu: bool = True
    use_tensorrt: bool = True
    roi: Optional[Tuple[int, int, int, int]] = None


@dataclass
class UIConfig:
    """UI配置"""

    overlay_x: int = 1400
    overlay_y: int = 800
    overlay_width: int = 400
    overlay_height: int = 300


@dataclass
class Config:
    """应用配置"""

    # 屏幕捕获配置
    capture: CaptureConfig = field(default_factory=CaptureConfig)

    # 地图检测配置
    detection: DetectionConfig = field(default_factory=DetectionConfig)

    # OCR配置
    ocr: OCRConfig = field(default_factory=OCRConfig)

    # UI配置
    ui: UIConfig = field(default_factory=UIConfig)

    # 路线规划配置
    route_algorithm: str = "weighted"  # 'greedy', 'weighted', 'nearest'

    @classmethod
    def load(cls, path: str = "config/settings.json") -> "Config":
        """从文件加载配置"""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 处理嵌套配置
                if "capture" in data:
                    data["capture"] = CaptureConfig(**data["capture"])
                if "detection" in data:
                    data["detection"] = DetectionConfig(**data["detection"])
                if "ocr" in data:
                    data["ocr"] = OCRConfig(**data["ocr"])
                if "ui" in data:
                    data["ui"] = UIConfig(**data["ui"])
                return cls(**data)
        return cls()

    def save(self, path: str = "config/settings.json") -> None:
        """保存配置到文件"""
        # 确保目录存在
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        data = asdict(self)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
