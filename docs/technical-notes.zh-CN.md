# Virtual Mouse and Gesture Control — 技术说明

**简体中文** · [English](technical-notes.en.md) · [日本語](technical-notes.ja.md) · [项目首页](../README.md)

<a id="source-map"></a>

## 模块与调用链

| 文件 | 实际责任 |
| :--- | :--- |
| [main.py](../main.py) | 实例化VirtualMouseApp并启动事件循环。 |
| [src/gui_app.py](../src/gui_app.py) | 摄像头、镜像、预览、线程、设置及状态轮询。 |
| [src/hand_detector.py](../src/hand_detector.py) | Hands封装、21点x/y浮点坐标、手别、指伸展和掌尺度。 |
| [src/mouse_controller.py](../src/mouse_controller.py) | np.interp映射、平滑、按键与滚动状态、PyAutoGUI调用。 |

仓库没有`src/__init__.py`，Python可按命名空间包导入，不把旧目录树里的不存在文件列成必需资源。requirements未锁定版本。

<a id="detection"></a>

## 关键点和尺度

GUI选择单手、`model_complexity=0`、检测阈值0.75、跟踪0.55；包装类默认值0.7/0.5不是主入口实参。RGB图交给MediaPipe，取其21点x/y，忽略z。保留浮点坐标不等于亚像素级物理精度测量。

```math
S=\sqrt{(x_9-x_0)^2+(y_9-y_0)^2},\qquad r_{ij}=\frac{\sqrt{(x_i-x_j)^2+(y_i-y_j)^2}}{S}
```

拇指4到5距离／S阈值0.58；其余指尖到腕0阈值为1.35/1.35/1.35/1.25。二维平面距离对图像内旋转有一定不变性，但透视、遮挡、侧手或S接近零时不能保证。`getPalmScale`对点数不足回1，却不防实际0距离。

`findDistance(draw=True)`把浮点点位直接送OpenCV绘图，主GUI没有调用这条辅助路径；不宣称所有辅助函数已运行验证。

<a id="mapping"></a>

## 映射与自适应平滑

相机坐标始终用Landmark5，并非点击前后切换或冻结。`np.interp`在缩减活动区内线性映射，越界取端点；没有畸变标定或额外gamma灵敏度乘数：

```math
X=(W_s-1)\mathrm{clip}\left(\frac{x_5-R_x}{640-2R_x},0,1\right),\quad Y=(H_s-1)\mathrm{clip}\left(\frac{y_5-R_y}{480-2R_y},0,1\right)
```

初始边距130/115。滑块回调把边距设为`int(320-280/vx)`／`int(240-188/vy)`；滑块显示1.5和初始130并非完全相同。依赖实际相机兑现640×480，不能直接声称多分辨率和多屏映射已验证。

以目标到当前平滑位置的剩余距离d，而非按时间测得速度，计算：

```math
\alpha=\frac4{\max(1,s)}\left[0.008+(0.25-0.008)\min\left(1,(d/45)^2\right)\right],\quad \hat p_{t+1}=\hat p_t+\alpha(p_{target}-\hat p_t)
```

s=4时范围0.008–0.25，s=1可到1.0；不是旧版0.05–0.95，也不是双线性或Kalman滤波。线程每次还需计算与系统调用，再sleep1/180，因此没有固定180 Hz保证。

<a id="states"></a>

## 状态优先级和生命周期

处理顺序为停用/无效输入、移动与左键、右键、滚动、待机。右键按捏合边沿触发，保持期间不重复，松开后重新使能；仍保留0.5 s防连击间隔。移动优先级与原版相同，张掌可能移动。左键使用down/up保持拖动，没有独立双击分类。

滚动仍为食指/中指/无名指伸出、小指收起；Landmark9初始y为中心，死区15像素、比例0.25。输入加入21点、有限坐标、5指状态及正掌尺度检查。

`set_active`、`release_input`、`close`统一清理。共享输入状态由RLock保护，平滑线程用Event退出并join；GUI失败与finally也清理输入/相机。保持PyAutoGUI FAILSAFE开启，仅强制释放左键时在锁内临时绕过角落检查并立即恢复。后台读取的是GUI缓存的预览布尔值。

<a id="evidence"></a>

## 历史画面和测量边界

| 历史移动 | 历史捏合 |
| :---: | :---: |
| ![移动](images/demo_cursor_tracking.png) | ![捏合](images/demo_pinch_click.png) |

180 Hz是线程循环目标，当前界面明确标注目标；没有实测输入刷新率。相机帧统一缩放到640×480后分析，映射终点为屏幕合法像素范围0至宽/高减1。10项回归使用注入的假输入后端，不操作真实桌面；四份源码解析通过。实际相机、GUI、驱动阻塞与OS事件仍需平台测试。
