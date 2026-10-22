# Virtual Mouse and Gesture Control — Setup and operation

[简体中文](setup.zh-CN.md) · **English** · [日本語](setup.ja.md) · [Overview](../README_EN.md)

<a id="structure"></a>

## Structure and environment

```text
.
├── main.py
├── src/
│   ├── gui_app.py
│   ├── hand_detector.py
│   └── mouse_controller.py
├── requirements.txt
├── LICENSE
└── docs/   # trilingual guides and existing screenshots
```

Prepare an isolated desktop Python 3.10 environment with opencv-python,numpy,mediapipe,pyautogui,customtkinter. No lockfile exists; MediaPipe must expose `mp.solutions.hands`. Tkinter/camera/OS input access are required. This audit did not validate every platform.

<a id="operation"></a>

## Launch and controls

```powershell
python -m pip install -r requirements.txt
python main.py
```

Launch from the root. Control starts enabled; camera 0 requests 640×480, without a camera-selection menu. Switches control detection/preview. Higher smoothing slows response; X/Y sliders shrink the active area to increase sensitivity.

Extend index to move; pinch thumb/index to hold left and release to finish drag. Right pinch uses thumb/middle only when movement is not selected. Scroll with three fingers up/little down, displacing from the entry center; recenter to stop. Esc closes the main window or disables control from the preview. Hiding preview does not stop detection.

<a id="lifecycle"></a>

## Disable and exit

Esc in the main window closes it; Esc in the OpenCV preview disables control, which can be re-enabled in the GUI. Pause, missing/invalid hands, failed camera reads, and exit use shared release. Backend errors disable control and retain an error. Detection-thread join has a one-second timeout; it cannot guarantee immediate termination of every blocking camera driver.

<a id="checks"></a>

## Checks and further validation

```powershell
python -B -m unittest discover -s tests -v
```

Ten tests cover drag release, camera failure, held right pinch, invalid coordinates/scale, screen bounds, input failures, and worker exit using a fake input backend. No OS events are emitted. Validate physical-input fallback, corner FAILSAFE, Esc, and camera errors on the target desktop. Historical performance numbers are not new results.
