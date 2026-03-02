# 三角洲游戏助手 - 产品需求文档 (PRD)

## 1. 项目概述

### 1.1 产品名称
三角洲游戏助手 (Delta Force Game Assistant)

### 1.2 产品定位
为《三角洲行动》玩家提供实时地图物资识别和最优搜索路线推荐的桌面辅助工具。

### 1.3 核心功能
| 功能模块 | 描述 | 优先级 |
|---------|------|--------|
| 地图检测 | 自动识别游戏地图打开状态 | P0 |
| 物资识别 | OCR识别地图上的物资点 | P0 |
| 路线规划 | 推荐最优搜索路线 | P0 |
| 悬浮展示 | 桌面悬浮窗/桌宠形式展示 | P0 |
| 控制台 | 配置管理和统计面板 | P1 |

## 2. 技术架构

### 2.1 技术栈
```yaml
GUI框架: PySide6>=6.6.0
屏幕捕获: dxcam>=0.2 (Windows DXGI)
图像处理: opencv-python>=4.8.0
OCR引擎: paddleocr>=2.7.0 + TensorRT加速
路径规划: pathfinding>=1.0.0 + 自定义A*
键盘监听: keyboard>=0.13.5
```

### 2.2 系统架构
```
delta-helper/
├── src/
│   ├── main.py                 # 程序入口
│   ├── core/                   # 核心功能模块
│   │   ├── capture.py          # 屏幕捕获 (dxcam)
│   │   ├── map_detector.py     # 地图状态检测
│   │   ├── ocr_engine.py       # OCR物资识别
│   │   ├── route_planner.py    # 路线规划算法
│   │   └── config.py           # 配置管理
│   ├── ui/                     # 界面模块
│   │   ├── main_window.py      # 主控制台
│   │   └── overlay.py          # 悬浮窗
│   └── utils/                  # 工具函数
├── tests/                      # 单元测试
├── assets/                     # 资源文件
├── config/                     # 配置文件
└── docs/                       # 文档
```

### 2.3 进程模型
- 主进程: UI + 协调器
- 子进程1: 屏幕捕获
- 子进程2: OCR识别
- 子进程3: 地图检测

## 3. 功能需求

### 3.1 屏幕捕获模块 (capture.py)
**需求**: 高性能屏幕捕获，支持区域捕获
- 使用dxcam库，目标240FPS
- 支持指定区域捕获
- 提供帧队列，支持丢帧保持实时性

**接口**:
```python
class ScreenCapture:
    def __init__(self, target_fps: int = 60, region: Optional[Tuple] = None)
    def start(self) -> None
    def get_frame(self, timeout: float = 0.1) -> Optional[np.ndarray]
    def stop(self) -> None
```

### 3.2 地图检测模块 (map_detector.py)
**需求**: 实时检测游戏地图打开状态
- 混合检测策略：键盘监听（主）+ 像素变化（确认）
- 响应延迟 < 50ms
- 状态变化回调机制

**接口**:
```python
class MapDetector:
    def __init__(self, capture: ScreenCapture, config: DetectionConfig)
    def add_listener(self, callback: Callable[[bool, str], None])
    def start(self) -> None
    def stop(self) -> None
```

### 3.3 OCR识别模块 (ocr_engine.py)
**需求**: 识别地图上的物资文字
- 使用PaddleOCR + TensorRT加速
- ROI裁剪优化（只识别地图区域）
- 目标延迟 < 30ms
- 物资类型自动分类

**接口**:
```python
class OCREngine:
    def __init__(self, use_gpu: bool = True, use_tensorrt: bool = True)
    def recognize(self, image: np.ndarray, roi: Optional[Tuple] = None) -> List[MaterialPoint]
```

### 3.4 路线规划模块 (route_planner.py)
**需求**: 多物资点最优访问顺序
- A*算法两点寻路
- 加权贪心TSP多目标优化
- 2-opt局部优化
- 复杂度 O(n²)

**接口**:
```python
class RouteOptimizer:
    def __init__(self, planner: AStarPlanner)
    def optimize_route(self, points: List[MaterialNode], player_pos: Tuple[int, int]) -> List[MaterialNode]
```

### 3.5 悬浮窗模块 (overlay.py)
**需求**: 透明悬浮窗展示路线
- 无边框透明窗口
- 始终置顶不抢焦点
- 点击穿透（不干扰游戏）
- 支持动画效果（淡入淡出、平滑移动）

**接口**:
```python
class PetOverlay(QWidget):
    def __init__(self)
    def set_route(self, points: List[Tuple[int, int]], player_pos: Tuple[int, int])
    def update_info(self, text: str)
    def fade_in(self) / fade_out(self)
    def smooth_move(self, target_x: int, target_y: int)
```

### 3.6 主控制台 (main_window.py)
**需求**: 配置管理和统计面板
- 系统托盘支持
- 实时状态显示
- 本局统计
- 运行日志

## 4. 性能指标

| 模块 | 延迟要求 | CPU占用 |
|------|---------|---------|
| 屏幕捕获 | < 5ms | < 5% |
| 地图检测 | < 50ms | < 1% |
| OCR识别 | < 30ms | < 10% |
| 路线规划 | < 10ms | < 1% |
| **总计** | **< 100ms** | **< 20%** |

## 5. 测试策略

### 5.1 单元测试覆盖
- [ ] ScreenCapture: 帧率测试、区域裁剪
- [ ] MapDetector: 状态检测准确性
- [ ] OCREngine: 识别准确率、延迟
- [ ] RoutePlanner: 路径最优性
- [ ] Overlay: UI响应

### 5.2 集成测试
- [ ] 端到端流程：截图 -> 检测 -> 识别 -> 规划 -> 显示
- [ ] 多进程通信稳定性
- [ ] 长时间运行稳定性（30分钟）

## 6. 里程碑

### Phase 1: 核心引擎 (Week 1)
- [x] PRD文档
- [ ] 项目结构搭建
- [ ] 屏幕捕获模块 + 测试
- [ ] 地图检测模块 + 测试

### Phase 2: 智能功能 (Week 2)
- [ ] OCR识别模块 + 测试
- [ ] 路线规划模块 + 测试
- [ ] 模块集成测试

### Phase 3: UI与交付 (Week 3)
- [ ] 悬浮窗实现
- [ ] 主控制台实现
- [ ] 打包与部署
- [ ] 完整系统测试

## 7. 风险与对策

| 风险 | 对策 |
|------|------|
| 反作弊检测 | 使用系统级API（DXGI），避免注入/Hook |
| OCR延迟高 | ROI裁剪 + TensorRT加速 |
| 多分辨率适配 | 配置文件支持不同分辨率 |
| 打包体积大 | 排除不必要依赖，UPX压缩 |

## 8. 附录

### 8.1 开发命令
```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v

# 打包
python build.py
```

### 8.2 参考资料
- DXcam: https://github.com/ra1nty/DXcam
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- PySide6: https://doc.qt.io/qtforpython/

---

**文档版本**: 1.0  
**最后更新**: 2026-03-01  
**状态**: 进行中
