# AI Virtual Mouse & Gesture Control System

An AI-based virtual mouse and gesture control system using OpenCV, MediaPipe, NumPy, and PyAutoGUI. This application detects hand gestures using a computer webcam and maps them to control the system mouse cursor (move and click).

## Features

- **Smooth Cursor Movement**: Move the cursor by pointing with only your index finger. Implements a smoothing factor to minimize cursor jitter.
- **Click Action**: Click by raising both the index and middle fingers and bringing them close together (distance < 40 pixels).
- **Fail-safe disabled**: Allows the cursor to reach all corners of the screen without throwing PyAutoGUI fail-safe errors.
- **FPS Display**: Displays the current processing frame rate on the camera feed.

## Gesture Definition

1. **Cursor Control (Moving)**:
   - Raise only the **Index Finger** (Index finger = Up, Middle finger = Down).
   - Move your hand to move the mouse cursor across the screen.

2. **Clicking**:
   - Raise both the **Index Finger** and the **Middle Finger**.
   - Bring them close together to trigger a mouse click action.

## Getting Started

### Prerequisites

You need Python installed. Install the required Python packages using pip:

```bash
pip install opencv-python numpy mediapipe pyautogui
```

### Running the Application

Simply run the main Python script:

```bash
python main.py
```

### Exit

Press the **'q'** key in the camera window to safely exit the program.
