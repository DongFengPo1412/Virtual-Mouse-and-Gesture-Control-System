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

移动用食指伸出；拇食捏合按住左键、松开释放，保持可拖动；右击需不满足移动分支，拇中捏合；滚动用三指伸出、小指收起，上下偏离初始位置，回死区停止。Q/Esc退出热键没有实现，正常关闭使用主窗口。关闭相机预览不会关闭检测。

<a id="lifecycle"></a>

## 停用与退出的已知问题

此程序会发送真实光标、点击和滚轮事件。源码关闭PyAutoGUI角落FAILSAFE，退出和停用也不保证释放按住的左键。进行实测前保持实体鼠标／键盘可用，先松开捏合再退出；这是当前具体缺陷，不代表已修复。

相机突然失效、线程异常、侧手导致掌尺度退化、后台Tk变量访问，都可能中断清理路径。不能把现有开关当成已验证的全局急停或安全输入隔离。

<a id="checks"></a>

## 检查与后续验证

本轮只解析四份Python源文件，不实例化MouseController，因为构造会读取桌面并启动常驻输入线程。没有运行仿造测试后声称相机或操作成功。

| 现象 | 检查 |
| :--- | :--- |
| MediaPipe无solutions | 所装API与源码接口不兼容，使用可提供Hands旧接口的环境。 |
| 光标范围／方向不合适 | 镜像、实际帧尺寸、固定640/480映射、边距、系统屏幕尺寸。 |
| 右击无效或重复 | 移动分支优先、食指状态、0.35阈值及0.5 s状态问题。 |
| 停用后按键仍按住 | 已知清理缺口，先以实体设备恢复；另行修复生命周期。 |
| FPS／响应与截图不同 | 计时仅循环估计，180 Hz文字固定，没有性能保证。 |

进一步验证应先确保输入释放和线程退出，再测追踪误差、不同姿态、点击／拖动／滚动及系统事件时间戳。
