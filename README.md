# SnapValid
一款轻量强大的**键盘鼠标自动化 + OCR验证码识别 + 截图相似度校验**工具，专为Windows平台设计，支持脚本录制/回放、智能OCR识别、页面相似度验证等核心能力。

## ✨ 功能特性
- 🎬 **键鼠录制/回放**：支持鼠标移动、点击、键盘按键全录制，可调节回放速度
- 🔍 **智能OCR识别**：集成Tesseract OCR，支持多语言验证码自动识别与输入
- 📸 **截图相似度校验**：基于OpenCV的模板匹配，验证页面元素是否符合预期
- ⚡ **全局快捷键**：无需窗口焦点，快捷键快速操作
- 📜 **结构化日志**：详细的日志记录，支持按天轮转、自动清理
- 🎛️ **灵活配置**：通过YAML配置文件自定义参数，支持多环境适配
- 📦 **绿色单文件**：打包为独立EXE，无需安装依赖

## 📋 环境要求
- Windows 7/10/11 (64位)
- Python 3.8+（开发环境）
- Tesseract OCR（需单独安装，用于OCR识别）

## 🚀 快速开始

### 1. 开发环境运行
```bash
# 克隆仓库
git clone https://github.com/yourname/SnapValid.git
cd SnapValid

# 安装依赖
pip install -r requirements.txt  # 或 pip install .

# 配置Tesseract路径（config.yml）
# 修改 ocr.tesseract_path 为你的Tesseract安装路径

# 运行程序
python main.py