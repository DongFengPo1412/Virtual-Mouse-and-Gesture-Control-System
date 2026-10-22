# Virtual Mouse and Gesture Control — 部署与操作

**简体中文** · [English](setup.en.md) · [日本語](setup.ja.md) · [项目首页](../README.md)

<a id="structure"></a>

## 目录与环境

```text
.
├── main.py
├── src/
│   ├── gui_app.py
│   ├── hand_detector.py
│   └── mouse_controller.py
├── requirements.txt
├── LICENSE
└── docs/   # 三语言指南、既有截图
```

推荐先准备独立Python3.10桌面环境，装requirements中的opencv-python、numpy、mediapipe、pyautogui、customtkinter。没有锁文件；所选MediaPipe需支持`mp.solutions.hands`。Tkinter、摄像头和OS输入权限需可用；本轮未验证所有操作系统。

<a id="operation"></a>

## 启动与操作

```powershell
python -m pip install -r requirements.txt
python main.py
```

从根目录启动。程序默认控制开启，检测固定摄像头0并请求640×480；没有相机选择菜单。主面板开关控制检测／预览，平滑值越大越慢、X/Y滑块缩小活动区从而提高灵敏度。

移动用食指伸出；拇食捏合按住左键、松开释放，保持可拖动；右击需不满足移动分支，拇中捏合；滚动用三指伸出、小指收起，上下偏离初始位置，回死区停止。主窗口Esc关闭，预览窗口Esc停用控制。关闭相机预览不会关闭检测。

<a id="lifecycle"></a>

## 停用与退出

主窗口Esc关闭；OpenCV预览窗口Esc停用控制，之后可在GUI重新启用。暂停、失手、无效掌尺度、读帧失败和退出都会调用统一释放。输入异常关闭控制并保存错误。相机驱动可能阻塞，等待检测线程退出设有1秒上限；这不是任意驱动都能立即终止的保证。

<a id="checks"></a>

## 检查与进一步验证

```powershell
python -B -m unittest discover -s tests -v
```

10项测试覆盖拖动释放、相机失败、持续右捏合、无效坐标/尺度、屏幕边界、输入错误和线程退出；使用假输入后端，没有发送OS事件。实机使用前验证物理鼠标回退、角落FAILSAFE、Esc和相机错误。历史性能数字不作为本次结果。
