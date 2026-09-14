<div align="center">

# 基于计算机视觉与深度学习的非接触式 AI 虚拟鼠标与人机交互系统
### Contactless AI Virtual Mouse & Gesture Control System via Real-Time Computer Vision and Multithreaded Interpolation

<p align="center">
  <a href="README.md"><b>简体中文</b></a> |
  <a href="README_EN.md"><b>English</b></a> |
  <a href="README_JA.md"><b>日本語</b></a>
</p>

![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-3776AB?logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-5C3EE8?logo=opencv&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands%200.10%2B-00758F?logo=google&logoColor=white)
![UI](https://img.shields.io/badge/GUI-CustomTkinter%20Dark-1f6aa5)
![Interpolation Engine](https://img.shields.io/badge/Cursor%20Interpolation-180Hz%20Threading-10b981)
![End-to-End Latency](https://img.shields.io/badge/Latency-%3C33ms-brightgreen)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

<p align="center">
  <b>融合 MediaPipe BlazePalm 拓扑回归、二次自适应低通平滑（Q-LPF）、MCP 掌骨锚点防抖锁定与 180Hz 独立高频插值引擎的工业级非接触人机交互（HCI）套件</b>
</p>

</div>

---

## 📸 实时运行与系统遥测演示 (Visual Showcase)

<div align="center">
<table>
  <tr>
    <td align="center" width="50%">
      <img src="docs/images/gui_dashboard.png" alt="CustomTkinter GUI Dashboard" width="100%"/>
      <br/>
      <b>图 1: CustomTkinter 现代深色遥测控制中控台 (180Hz 线程监控 & 参数动态微调)</b>
    </td>
    <td align="center" width="50%">
      <img src="docs/images/demo_cursor_tracking.png" alt="Cursor Motion Tracking" width="100%"/>
      <br/>
      <b>图 2: 单指微操移动与动态映射 ROI 追踪 (实测帧率 32 FPS, 消除屏幕边缘死区)</b>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <img src="docs/images/demo_pinch_click.png" alt="Pinch Click Trigger" width="100%"/>
      <br/>
      <b>图 3: 微距捏合点击与拖拽触发识别 (亚像素级欧氏判定 & MCP-5 物理锚点锁定)</b>
    </td>
    <td align="center" width="50%">
      <img src="docs/images/hand_landmarks_pipeline.png" alt="Hand Landmarks Pipeline" width="100%"/>
      <br/>
      <b>图 4: 21 点 3D 骨架拓扑结构与端到端算法处理流水线 (SSD 回归至 OS 事件)</b>
    </td>
  </tr>
</table>
</div>

---

## 📌 项目概述 (Project Overview)

本系统是一套面向高精度、低延迟、抗抖动场景设计的**非接触式 AI 虚拟鼠标与人机交互系统（Human-Computer Interaction, HCI）**。传统单目摄像头虚拟鼠标普遍存在三大行业工程通病：
1. **高频手部生理颤抖（Physiological Tremor）**：普通摄像头识别指尖坐标时存在微小随机噪声，映射到高分辨率屏幕后产生剧烈的光标抖动；
2. **点击动作坐标漂移（Click Displacement Drift）**：当手指下压执行点击指令瞬间，指尖在空间中的微小位移必然导致光标发生像素级偏移，导致“点击目标失准”或“误触为拖拽”；
3. **低帧率卡顿感与边缘盲区（Latency & Edge Inaccessibility）**：受限于普通网络摄像头 30 FPS 的采集帧率，光标运动迟滞严重；且未校正视场角导致手臂需超幅度伸展才能触及屏幕边缘。

针对上述瓶颈，本工程设计并实现了**全链路工程解耦与算法优化方案**：
- **180Hz 独立高频时间插值线程**：将 30 FPS 视频检测流水线与光标控制彻底解耦，在独立后台线程中以 180Hz 执行平滑渐进逼近插值，彻底消除光标顿挫感；
- **MCP Landmark-5 掌指关节物理锚点机制**：点击触发阶段光标定位锚定在运动惯性极小的掌指关节（Landmark 5），实现**点击位置物理级冻结锁定**；
- **二次自适应低通平滑算法（Quadratic Adaptive EWMA）**：根据位移速度动态调节平滑因子，微速移动时极大提升稳定性，高速移动时瞬间降低平滑阻尼，兼顾微操精准度与大范围追踪灵敏度；
- **手掌尺度不变性（Scale-Invariant Distance Ratio）**：所有手势判决阈值均按当前手掌掌心尺度自适应归一化，彻底消除前后景深距离对交互判定的干扰；
- **现代暗黑风 CustomTkinter 控制中控台**：提供实时遥测卡片（核心运行状态、实时推理帧率、左右手识别判别、手势模式）与平滑度/X-Y灵敏度滑块实时无感调节。

---

## 🔬 核心算法与数学模型 (Mathematical Formulation)

```mermaid
flowchart LR
    A[单目 RGB 摄像头] --> B[MediaPipe BlazePalm SSD]
    B --> C[21 关键点 3D 回归]
    C --> D[动态 ROI 边界截断归一化]
    D --> E[掌心尺度自适应归一化]
    E --> F[二次速度响应 LPF 平滑]
    F --> G[180Hz 独立多线程时间插值]
    G --> H[MCP-5 锚点锁定与 OS 鼠标派发]
```

### 1. MediaPipe BlazePalm 与 21 点 3D 骨架拓扑
系统采用单目单阶段 BlazePalm 检测网络完成掌心极坐标回归与旋转姿态估计，进而通过回归网络推断出 21 个 3D 关节坐标空间点集：
$$\mathcal{P} = \{P_i = (x_i, y_i, z_i) \mid i \in [0, 20]\}$$
其中 $P_0$ 为手腕关节点（Wrist），$P_5$ 为食指掌指关节（Index Finger MCP），$P_8$ 为食指指尖（Index Fingertip），$P_{12}$ 为中指指尖（Middle Fingertip）。

### 2. 动态自适应宽高比 ROI 映射模型
普通摄像头由于存在边缘畸变且人体手臂摆动范围有限，直接全图映射会导致屏幕边缘难以触达。系统构建了带有活动安全余量（Frame Reduction Margin）的动态感兴趣区域（ROI）：
设摄像头图像宽度为 $W_{cam}$、高度为 $H_{cam}$，X 轴与 Y 轴缩减边界分别为 $R_x, R_y$。归一化映射坐标定义为：

$$x_{norm} = \text{clamp}\left(\frac{x_{raw} - R_x}{W_{cam} - 2R_x}, 0.0, 1.0\right)$$

$$y_{norm} = \text{clamp}\left(\frac{y_{raw} - R_y}{H_{cam} - 2R_y}, 0.0, 1.0\right)$$

映射至目标屏幕分辨率 $(W_{screen}, H_{screen})$：

$$X_{target} = \text{round}\left( x_{norm} \cdot W_{screen} \cdot \gamma_x \right)$$

$$Y_{target} = \text{round}\left( y_{norm} \cdot H_{screen} \cdot \gamma_y \right)$$

其中 $\gamma_x, \gamma_y$ 为各轴灵敏度调节增益（GUI 可动态调整，默认 1.5）。

### 3. 手掌尺度不变性手势判定准则
用户操作过程中与摄像头距离不断变化，若采用固定像素距离阈值将导致景深误判。系统以手腕 $P_0$ 与中指掌指关节 $P_9$ 之间的欧氏距离作为**手掌基准尺度（Palm Scale）**：

$$S_{palm} = \|P_9 - P_0\|_2 = \sqrt{(x_9 - x_0)^2 + (y_9 - y_0)^2}$$

任意两关键点 $P_i, P_j$ 的尺度无量纲相对距离定义为：

$$\rho_{ij} = \frac{\|P_i - P_j\|_2}{S_{palm}}$$

当 $\rho_{thumb, index} < \tau_{click}$ 且持续维持时触发左键点击/拖拽，彻底消除由于手掌远近变化导致的误触发。

### 4. 二次自适应低通滤波 (Quadratic Adaptive EWMA Smoothing)
为了在单点静止微操时消除手颤抖动，同时在快速跨屏滑动时不产生视觉滞后，系统提出了二次速度响应平滑系数方程：

$$\Delta_t = \sqrt{(X_t - \hat{X}_{t-1})^2 + (Y_t - \hat{Y}_{t-1})^2}$$

$$\alpha_t = \text{clamp}\left( \frac{1}{\text{smooth}} \cdot \left(\frac{\Delta_t}{\delta_0}\right)^2, \alpha_{min}, \alpha_{max} \right)$$

其中基准位移常数 $\delta_0 = 45.0\text{ px}$，动态调节范围 $[\alpha_{min}, \alpha_{max}] = [0.05, 0.95]$：
- **微速移动（$\Delta_t \to 0$）**：$\alpha_t \to 0.05$，系统具备极强低通滤波平滑性能，死区滤波（Deadzone $<0.6\text{ px}$）将微小生理震颤完全滤除；
- **高速甩动（$\Delta_t \gg 45$）**：$\alpha_t \to 0.95$，平滑权重降低，光标以近乎 1:1 的即时响应极速跟随。

最终当前平滑坐标递推方程为：

$$\hat{X}_t = \alpha_t X_t + (1 - \alpha_t) \hat{X}_{t-1}$$

$$\hat{Y}_t = \alpha_t Y_t + (1 - \alpha_t) \hat{Y}_{t-1}$$

### 5. 180Hz 独立后台时间插值引擎
常规应用在主检测循环内调用系统光标 API，导致光标更新受限于摄像头帧率（约 30Hz）。本系统创建了**独立高频守护线程（Daemon Thread）**，以 $f_{interp} = 180\text{ Hz}$（周期约 5.5ms）执行双线性高频逼近：

$$\Delta X = X_{target} - X_{current},\quad \Delta Y = Y_{target} - Y_{current}$$

当 $\|\Delta\|_{2} > \epsilon$ 时，以自适应步长更新当前物理光标坐标并派发底层系统输入驱动。即使在普通 30FPS 摄像头环境下，也能输出媲美高刷新电竞鼠标的丝滑体验。

### 6. MCP Landmark-5 点击防抖锚点锁定
由于食指在弯曲点击瞬间，指尖骨骼绕 MCP 关节旋转产生不可避免的平面位移。本系统在判定手指处于点击收拢过渡期时，将光标跟踪坐标**立即切换并锚定在食指掌骨关节 Landmark 5**，并短暂锁定上一稳定位置，彻底根除传统虚拟鼠标“点击即位移”的痛点。

---

## 🖐️ 手势交互控制指令集 (Gesture Dictionary)

系统采用人体工程学设计，所有手势均经过操作舒适性验证，避免长时间悬空产生肌肉疲劳：

| 交互功能 (Action) | 手势形态 (Hand Gesture) | 判定规则 (Decision Logic) | 系统底层派发事件 |
|:---|:---|:---|:---|
| **光标平滑移动** | 食指伸出，其余手指收拢 | 仅 $F_{index} = 1$，其余为 0 | 180Hz 平滑更新鼠标坐标 $(X, Y)$ |
| **鼠标左键单击 / 拖拽** | 拇指与食指捏合 | $\rho_{4, 8} < 0.28 \times S_{palm}$ | 单击派发 `mouse.down/up`；捏住不放进入拖拽模式 |
| **鼠标右键点击** | 拇指与中指捏合 | $\rho_{4, 12} < 0.28 \times S_{palm}$ | 触发上下文菜单 `mouse.right_click()` |
| **虚拟滚轮平滑滚动** | 食指与中指同时伸出并拢 | $F_{index}=1, F_{mid}=1$，指尖横向位移 | 根据指间垂直位移差连续滚动 `mouse.scroll(dy)` |
| **空闲 / 待命模式** | 五指自然握拳或完全张开 | 不符合上述交互模式特征 | 光标保持原位，冻结触发，防止误动作 |

---

## 📊 硬件基准与性能评测 (Performance Benchmark)

系统在标配轻薄笔记本及单目 USB 摄像头环境下的实测基准数据如下（测试环境：Intel Core i7-11800H / 16GB RAM / 普通 720P 广角摄像头）：

| 分辨率配置 | 推理帧率 (FPS) | 算法端到端延迟 | 插值输出频率 | CPU 占用率 | 内存消耗 (RAM) | 综合评级 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **$640 \times 480$ (默认推荐)** | **$30 \sim 35\text{ FPS}$** | **$< 33\text{ ms}$** | **$180\text{ Hz}$** | **$16\% \sim 18\%$** | **$\sim 120\text{ MB}$** | 🌟 **卓越 (Optimal)** |
| **$1280 \times 720$ (高清采样)** | $22 \sim 25\text{ FPS}$ | $\sim 44\text{ ms}$ | $180\text{ Hz}$ | $32\% \sim 35\%$ | $\sim 155\text{ MB}$ | 良好 (High Precision) |
| **$1920 \times 1080$ (超清输入)** | $13 \sim 15\text{ FPS}$ | $\sim 71\text{ ms}$ | $180\text{ Hz}$ | $60\% \sim 65\%$ | $\sim 210\text{ MB}$ | 算力受限 (Heavy) |

> **评测结论**：$640 \times 480$ 模式下算法运算延迟小于单帧曝光周期，CPU 占用率低于 20%，不仅完全满足主流办公与人机交互操作，且为后台其它应用程序预留了充沛算力空间。

---

## 🗂️ 项目文件架构 (Repository Structure)

```
Virtual-Mouse-and-Gesture-Control-System/
├── docs/
│   └── images/                         # 真实演示录像截图与架构图
│       ├── gui_dashboard.png           # CustomTkinter 暗黑模式遥测中控面板
│       ├── demo_cursor_tracking.png    # 单指微操移动与动态映射 ROI 追踪截图
│       ├── demo_pinch_click.png        # 双指微距捏合点击与拖拽触发识别截图
│       └── hand_landmarks_pipeline.png # 21 关键点拓扑与 180Hz 算法处理流水线
├── src/                                # 核心模块源代码
│   ├── __init__.py                     # 模块包声明
│   ├── hand_detector.py                # MediaPipe Hands 封装、21点坐标提取与尺度计算
│   ├── mouse_controller.py             # 180Hz 插值引擎、低通平滑滤波与光标驱动
│   └── gui_app.py                      # CustomTkinter 现代 GUI 遥测与参数交互中控
├── LICENSE                             # 官方 MIT 开源许可协议
├── main.py                             # 应用程序主入口
├── requirements.txt                    # Python 依赖清单
├── README.md                           # 中文技术文档
├── README_EN.md                        # 英文技术文档
└── README_JA.md                        # 日文技术文档
```

---

## 🚀 快速启动指南 (Quick Start)

### 1. 环境准备
确保系统安装有 **Python 3.9+**（推荐在 Conda 独立虚拟环境中运行）：

```bash
# 克隆仓库代码
git clone https://github.com/DongFengPo1412/Virtual-Mouse-and-Gesture-Control-System.git
cd Virtual-Mouse-and-Gesture-Control-System

# 创建并激活隔离环境 (可选)
conda create -n ai_mouse_env python=3.10 -y
conda activate ai_mouse_env

# 安装项目依赖
pip install -r requirements.txt
```

### 2. 运行主程序
直接运行入口脚本，启动现代控制中控面板：

```bash
python main.py
```

### 3. 操作与中控交互说明
- **启动后中控面板将自动打开**，并同步启动后台摄像头线程与 180Hz 光标插值循环；
- 勾选 **“显示相机画面”** 可展开实时手势追踪视频窗口，直观查看 21 点关键点骨架与动态映射 ROI 边框；
- 通过中控左侧滑块可实时调节：
  - **移动延迟（平滑度）**：数值越小响应越灵敏，数值越大光标越平稳（默认值推荐为 4）；
  - **X/Y 轴灵敏度**：可根据多显示器或超宽屏幕自由调整水平与垂直移动增益。

---

## 🛠️ 技术栈与依赖库 (Tech Stack)

| 核心组件 | 技术方案 | 作用描述 |
|:---|:---|:---|
| **视觉骨架提取** | Google MediaPipe Hands | 轻量级单阶段 21 节点 3D 关节坐标回归模型 |
| **视频流处理** | OpenCV (`cv2`) | 摄像头采集、色彩空间转换与 OSD 骨架绘制渲染 |
| **光标驱动调度** | PyAutoGUI / ctypes | 系统底层硬件输入模拟、点击与滚轮消息派发 |
| **多线程与插值** | Python `threading` & `time` | 180Hz 独立高频时间插值线程与视频流水线解耦 |
| **交互控制面板** | CustomTkinter | 现代深色模式高 DPI 遥测控制面板与动态参数调节 |

---

## 📄 开源许可证 (License)

本项目遵循 [MIT 许可证](LICENSE)。允许商业及学术用途免费使用、修改与衍生，保留原作者著作权声明即可。

---

<div align="center">
  <b>Developed with precision and high-performance HCI engineering by <a href="https://github.com/DongFengPo1412">DongFengPo1412</a></b>
</div>
