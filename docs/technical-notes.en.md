# Virtual Mouse and Gesture Control — Technical notes

[简体中文](technical-notes.zh-CN.md) · **English** · [日本語](technical-notes.ja.md) · [Overview](../README_EN.md)

<a id="source-map"></a>

## Modules and calls

| File | Responsibility |
| :--- | :--- |
| [main.py](../main.py) | Instantiate VirtualMouseApp/start its loop. |
| [src/gui_app.py](../src/gui_app.py) | Camera, mirroring, preview, workers, controls, telemetry. |
| [src/hand_detector.py](../src/hand_detector.py) | Hands wrapper,21 float x/y landmarks, handedness, finger rules, palm scale. |
| [src/mouse_controller.py](../src/mouse_controller.py) | np.interp mapping, smoothing, button/scroll state, PyAutoGUI. |

There is no `src/__init__.py`; namespace-package imports work without inventing the old tree's missing file. Requirements are unpinned.

<a id="detection"></a>

## Landmarks and scale

GUI selects one hand,`model_complexity=0`, detection 0.75/tracking 0.55. Wrapper defaults 0.7/0.5 are not the entry's settings. MediaPipe receives RGB; the wrapper retains 21 x/y points and discards z. Floating coordinates are not measured subpixel physical accuracy.

```math
S=\sqrt{(x_9-x_0)^2+(y_9-y_0)^2},\qquad r_{ij}=\frac{\sqrt{(x_i-x_j)^2+(y_i-y_j)^2}}{S}
```

Thumb 4-to-5/S uses 0.58; other fingertip-to-wrist ratios use 1.35/1.35/1.35/1.25. Plane distances are invariant to image-plane rotation, but perspective/occlusion/side views/near-zero S remain problematic. Insufficient landmarks return scale 1; actual coincident points are not guarded.

Unused `findDistance(draw=True)` passes floating points to OpenCV drawing calls. The main GUI does not call this helper, so all auxiliary paths are not claimed runtime-tested.

<a id="mapping"></a>

## Mapping and adaptive smoothing

Tracking always uses Landmark 5; it does not switch or freeze at click onset. `np.interp` maps the reduced active area to screen coordinates and clamps outside endpoints. There is no distortion calibration or extra gamma sensitivity multiplier:

```math
X=W_s\mathrm{clip}\left(\frac{x_5-R_x}{640-2R_x},0,1\right),\quad Y=H_s\mathrm{clip}\left(\frac{y_5-R_y}{480-2R_y},0,1\right)
```

Initial margins are 130/115. Slider callbacks set `int(320-280/vx)`/`int(240-188/vy)`; displayed 1.5 and initial 130 are not identical. Mapping assumes the camera supplies 640×480; multiple resolutions/monitors are not verified.

The coefficient uses remaining target distance d, not time-measured hand velocity:

```math
\alpha=\frac4{\max(1,s)}\left[0.008+(0.25-0.008)\min\left(1,(d/45)^2\right)\right],\quad \hat p_{t+1}=\hat p_t+\alpha(p_{target}-\hat p_t)
```

For s=4 the range is 0.008–0.25; s=1 can reach 1.0. It is not the old 0.05–0.95 formula, bilinear interpolation, or a Kalman filter. Calculation/system calls precede sleep 1/180, so 180 Hz is not guaranteed.

<a id="states"></a>

## Priority and lifecycle

Priority is inactive→no hand→move/left→right→scroll→ready. Movement requires an extended index, not all other fingers folded: an open palm may move, and movement takes priority over a middle pinch.

Both pinch thresholds are 0.35. Right-click logic alternately clears its flag while held and can click again after 0.5 s; it is not one click per pinch. Left uses down/up, holding permits dragging, and no explicit double-click state exists.

Scroll requires index/middle/ring up and little down, ignoring thumb state. Landmark 9's entry y defines the center;15 camera pixels form a deadzone, then signed excess×0.25 is truncated/reversed and sent each detection iteration. It is not two-finger horizontal scrolling.

Normal no-hand processing releases left. However, disabled GUI detection skips `move_and_action`, bypassing its inactive-release branch. Close only sets running/active and waits 0.2 s, without explicit mouseUp/join; interpolation loops forever as a daemon. Camera failure also skips cleanup. Source disables PyAutoGUI FAILSAFE, so corner escape is not promised.

<a id="evidence"></a>

## Historical views and measurement limits

| Historical tracking | Historical pinch |
| :---: | :---: |
| ![Tracking](images/demo_cursor_tracking.png) | ![Pinch](images/demo_pinch_click.png) |

The 180 Hz card is a constant. FPS is an integer estimate from complete detection-loop time, initially measured from zero, not isolated model throughput. Targets/state have no locks, the worker reads Tk variables, and input/exit behavior needs platform validation.

Four Python sources parsed, without camera/GUI/input testing. Former 33 ms,30–35 FPS,16–18% CPU,120 MB,720p/1080p tables lack scripts/raw logs and are removed as achievements. Installed-package metadata is not end-to-end validation.
