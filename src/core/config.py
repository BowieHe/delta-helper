"""
配置管理模块
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional, Tuple
from pathlib import Path


@dataclass
class Config:
    """应用配置"""

    # 屏幕捕获配置
    capture_fps: int = 60
    capture_region: Optional[Tuple[int, int, int, int]] = (
        None  # (left, top, width, height)
    )

    # 地图检测配置
    map_key: str = "m"
    check_interval: float = 0.05
    change_threshold: int = 5000
    confirm_count: int = 2

    # OCR配置
    ocr_use_gpu: bool = True
    ocr_use_tensorrt: bool = True
    ocr_roi: Optional[Tuple[int, int, int, int]] = None

    # UI配置
    overlay_x: int = 1400
    overlay_y: int = 800
    overlay_width: int = 400
    overlay_height: int = 300

    # 路线规划配置
    route_algorithm: str = "weighted"  # 'greedy', 'weighted', 'nearest'

    @classmethod
    def load(cls, path: str = "config/settings.json") -> "Config":
        """从文件加载配置"""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 处理tuple类型
                if "capture_region" in data and data["capture_region"]:
                    data["capture_region"] = tuple(data["capture_region"])
                if "ocr_roi" in data and data["ocr_roi"]:
                    data["ocr_roi"] = tuple(data["ocr_roi"])
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
