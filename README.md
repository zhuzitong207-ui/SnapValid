# SnapValid
一款轻量强大的**键盘鼠标自动化 + OCR验证码识别 + 截图相似度校验**工具

## 功能特性
✅ 键盘鼠标全操作录制/回放  
✅ OCR自动识别验证码并输入  
✅ 区域截图相似度校验（页面验证）  
✅ 多屏复制模式自动检测  
✅ 浏览器自动最大化  
✅ 详细日志+结果文件输出  
✅ 绿色单文件打包  

## 快捷键
- `F9` 开始录制  
- `F10` 开始回放  
- `F11` 停止  
- `Ctrl+Alt+I` 插入OCR识别步骤  
- `Ctrl+Alt+S` 插入截图校验步骤  

## 快速启动
```bash
python SnapValid.py

打包为 exe
pyinstaller -Fw --add-data './assets;assets' SnapValid.py
