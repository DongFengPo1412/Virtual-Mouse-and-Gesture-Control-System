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

Prepare an isolated desktop Python3.10 environment with opencv-python,numpy,mediapipe,pyautogui,customtkinter. No lockfile exists; MediaPipe must expose`mp.solutions.hands`. Tkinter/camera/OS input access are required. This audit did not validate every platform.

<a id="operation"></a>

## Launch and controls

```powershell
python -m pip install -r requirements.txt
python main.py
```

Launch from the root. Control starts enabled; camera0 requests640×480, without a camera-selection menu. Switches control detection/preview. Higher smoothing slows response; X/Y sliders shrink the active area to increase sensitivity.

Extend index to move; pinch thumb/index to hold left and release to let go/finish drag. Right pinch uses thumb/middle only when movement is not selected. Scroll with three fingers up/little down, displacing vertically from entry center; recenter to stop. Q/Esc quit shortcuts are absent: close the main window normally. Hiding preview does not stop detection.

<a id="lifecycle"></a>

## Known disable/exit behavior

The program emits real cursor/button/wheel events. It disables PyAutoGUI corner FAILSAFE, and disable/close may leave left held. Keep physical input available and release the pinch before closing during trials. This is a current defect, not a documented fix.

Camera failure, worker exceptions, degenerate palm scale, and background Tk-variable access can interrupt cleanup. The switch is not a verified global emergency stop or input-isolation mechanism.

<a id="checks"></a>

## Checks and further validation

This audit parsed four sources without instantiating MouseController: construction reads the desktop and starts a permanent input worker. No mocked test is presented as successful camera/OS operation.

| Symptom | Inspect |
| :--- | :--- |
| No MediaPipe solutions | Installed API differs; use an environment exposing the required Hands interface. |
| Incorrect cursor range/direction | Mirroring, actual frame size, fixed640/480 mapping, margins, desktop dimensions. |
| Missing/repeated right click | Movement priority, index state,0.35 threshold,0.5 s logic. |
| Held button after disabling | Known cleanup gap; recover with physical input and fix lifecycle separately. |
| Different FPS/responsiveness | Loop estimate and fixed180 Hz label are not performance guarantees. |

First verify input release/thread exit, then tracking error, poses, clicks/drags/scrolls, and timestamped OS events.
