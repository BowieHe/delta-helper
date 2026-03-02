# 三角洲游戏助手 (Delta Force Game Assistant)

一个为《三角洲行动》玩家提供实时地图物资识别和最优搜索路线推荐的桌面辅助工具。

## 🎮 功能特性

- **自动地图检测**: 智能识别游戏地图打开状态
- **物资OCR识别**: 自动识别地图上的物资点
- **智能路线规划**: 推荐最优搜索路线
- **桌面悬浮窗**: 以桌宠形式展示路线指引
- **系统托盘**: 后台运行，不干扰游戏

## 🏗️ 技术架构

```
delta-helper/
├── src/
│   ├── main.py                 # 程序入口
│   ├── core/                   # 核心功能
│   │   ├── capture.py          # 屏幕捕获 (dxcam)
│   │   ├── map_detector.py     # 地图检测
│   │   ├── ocr_engine.py       # OCR识别
│   │   ├── route_planner.py    # 路线规划
│   │   └── config.py           # 配置管理
│   └── ui/                     # 界面
│       ├── main_window.py      # 主控制台
│       └── overlay.py          # 悬浮窗
└── tests/                      # 单元测试
```

## 🚀 快速开始

### 环境要求

- Windows 10/11
- Python 3.8+
- NVIDIA显卡（可选，用于GPU加速）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python src/main.py
```

### 运行测试

```bash
pytest tests/ -v
```

## 📦 打包发布

```bash
# 生产版本
python build.py

# 调试版本（带控制台）
python build.py --debug

# 清理构建文件
python build.py --clean
```

打包后的可执行文件位于 `dist/三角洲助手.exe`

## ⚙️ 配置说明

配置文件位于 `config/settings.json`，可以调整以下参数：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `capture.target_fps` | 屏幕捕获帧率 | 60 |
| `detection.map_key` | 地图按键 | 'm' |
| `ocr.use_gpu` | 使用GPU加速 | true |
| `ocr.use_tensorrt` | 使用TensorRT | true |
| `ui.overlay_x` | 悬浮窗X位置 | 1400 |
| `ui.overlay_y` | 悬浮窗Y位置 | 800 |

## 📊 性能指标

| 模块 | 延迟 | CPU占用 |
|------|------|---------|
| 屏幕捕获 | < 5ms | < 5% |
| 地图检测 | < 50ms | < 1% |
| OCR识别 | < 30ms | < 10% |
| 路线规划 | < 10ms | < 1% |

## 🧪 测试覆盖

- ✅ 屏幕捕获模块测试
- ✅ 地图检测模块测试
- ✅ OCR引擎模块测试
- ✅ 路线规划模块测试

运行测试:
```bash
pytest tests/ -v --cov=src --cov-report=html
```

## 🛡️ 兼容性

- ✅ Windows 10/11
- ✅ 支持NVIDIA GPU加速
- ✅ 兼容主流反作弊系统（使用系统级API）

## 📝 更新日志

### v1.0.0 (2026-03-01)
- 初始版本发布
- 实现核心功能：地图检测、OCR识别、路线规划
- 添加悬浮窗UI和主控制台
- 完整单元测试覆盖

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## ⚠️ 免责声明

本工具仅供学习交流使用，请遵守游戏用户协议。使用本工具产生的任何后果由用户自行承担。

---

**Made with ❤️ for Delta Force players**
