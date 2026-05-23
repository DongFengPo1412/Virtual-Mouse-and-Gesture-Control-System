import customtkinter as ctk
import cv2
import threading
import time
from src.hand_detector import HandDetector
from src.mouse_controller import MouseController

# 设置 CustomTkinter 的全局视觉风格
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VirtualMouseApp(ctk.CTk):
    """
    AI 虚拟鼠标控制面板 GUI 界面
    采用多线程分治架构，将视频检测、鼠标插值和 UI 渲染在独立线程中执行，实现无卡顿的高帧率交互。
    """
    def __init__(self):
        super().__init__()

        # 1. 窗口基础设置
        self.title("AI 虚拟鼠标控制面板 (180Hz 极速优化版)")
        self.geometry("780x480")
        self.resizable(False, False)

        # 2. 初始化检测参数与控制器
        self.detector = HandDetector(maxHands=1, detectionCon=0.75, trackCon=0.55)
        # 初始化 MouseController，默认平滑度为 4
        self.controller = MouseController(wCam=640, hCam=480, smoothening=4, frameR_x=130, frameR_y=115)

        self.running = True

        # 3. 创建界面布局
        self._create_widgets()

        # 4. 绑定窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # 5. 启动后台摄像头检测线程
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()

        # 6. 启动 GUI 遥测数据刷新定时器
        self._update_telemetry_loop()

    def _create_widgets(self):
        """创建 GUI 所有的微件"""
        # ==========================================
        # 布局：左侧控制栏 (Sidebar Frame)
        # ==========================================
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", rowspan=4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 标题 OSD
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="AI VIRTUAL MOUSE", font=ctk.CTkFont(size=18, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        # 主系统开关
        self.switch_system = ctk.CTkSwitch(self.sidebar_frame, text="启用手势控制", command=self._toggle_system)
        self.switch_system.select()  # 默认开启
        self.switch_system.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        # 视频预览窗口开关
        self.show_preview = ctk.BooleanVar(value=True)
        self.switch_preview = ctk.CTkSwitch(self.sidebar_frame, text="显示相机画面", variable=self.show_preview)
        self.switch_preview.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        # 平滑度调节滑块 (Low Pass Filter smoothing)
        self.smooth_label = ctk.CTkLabel(self.sidebar_frame, text="移动延迟 (平滑度): 4", font=ctk.CTkFont(size=12))
        self.smooth_label.grid(row=3, column=0, padx=20, pady=(15, 2), sticky="w")
        self.smooth_slider = ctk.CTkSlider(self.sidebar_frame, from_=1, to=15, number_of_steps=14, command=self._update_smooth)
        self.smooth_slider.set(4)
        self.smooth_slider.grid(row=4, column=0, padx=20, pady=2, sticky="ew")

        # X 轴灵敏度
        self.sens_x_label = ctk.CTkLabel(self.sidebar_frame, text="X轴 灵敏度: 1.5", font=ctk.CTkFont(size=12))
        self.sens_x_label.grid(row=5, column=0, padx=20, pady=(15, 2), sticky="w")
        self.sens_x_slider = ctk.CTkSlider(self.sidebar_frame, from_=1.0, to=3.0, command=self._update_sens_x)
        self.sens_x_slider.set(1.5)
        self.sens_x_slider.grid(row=6, column=0, padx=20, pady=2, sticky="ew")

        # Y 轴灵敏度
        self.sens_y_label = ctk.CTkLabel(self.sidebar_frame, text="Y轴 灵敏度: 1.5", font=ctk.CTkFont(size=12))
        self.sens_y_label.grid(row=7, column=0, padx=20, pady=(15, 2), sticky="w")
        self.sens_y_slider = ctk.CTkSlider(self.sidebar_frame, from_=1.0, to=3.0, command=self._update_sens_y)
        self.sens_y_slider.set(1.5)
        self.sens_y_slider.grid(row=8, column=0, padx=20, pady=2, sticky="ew")

        # ==========================================
        # 布局：右侧看板 (Dashboard Frame)
        # ==========================================
        self.dashboard_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dashboard_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.dashboard_frame.grid_columnconfigure(0, weight=1)
        self.dashboard_frame.grid_columnconfigure(1, weight=1)

        # 仪表盘标题
        self.dash_title = ctk.CTkLabel(self.dashboard_frame, text="系统实时监控状态", font=ctk.CTkFont(size=20, weight="bold"))
        self.dash_title.grid(row=0, column=0, columnspan=2, padx=10, pady=(0, 20), sticky="w")

        # 卡片 1：系统状态
        self.card_status = ctk.CTkFrame(self.dashboard_frame, height=100)
        self.card_status.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.status_title = ctk.CTkLabel(self.card_status, text="手势检测状态", font=ctk.CTkFont(size=12, weight="bold"))
        self.status_title.pack(padx=10, pady=(10, 2), anchor="w")
        self.status_value = ctk.CTkLabel(self.card_status, text="就绪", font=ctk.CTkFont(size=22, weight="bold", family="Consolas"), text_color="#2ECC71")
        self.status_value.pack(padx=10, pady=(2, 10), anchor="w")

        # 卡片 2：相机检测 FPS
        self.card_fps = ctk.CTkFrame(self.dashboard_frame, height=100)
        self.card_fps.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.fps_title = ctk.CTkLabel(self.card_fps, text="相机采集帧率", font=ctk.CTkFont(size=12, weight="bold"))
        self.fps_title.pack(padx=10, pady=(10, 2), anchor="w")
        self.fps_value = ctk.CTkLabel(self.card_fps, text="0 FPS", font=ctk.CTkFont(size=22, weight="bold", family="Consolas"), text_color="#3498DB")
        self.fps_value.pack(padx=10, pady=(2, 10), anchor="w")

        # 卡片 3：手势类别
        self.card_hand = ctk.CTkFrame(self.dashboard_frame, height=100)
        self.card_hand.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.hand_title = ctk.CTkLabel(self.card_hand, text="当前检测手别", font=ctk.CTkFont(size=12, weight="bold"))
        self.hand_title.pack(padx=10, pady=(10, 2), anchor="w")
        self.hand_value = ctk.CTkLabel(self.card_hand, text="N/A", font=ctk.CTkFont(size=22, weight="bold", family="Consolas"), text_color="#E67E22")
        self.hand_value.pack(padx=10, pady=(2, 10), anchor="w")

        # 卡片 4：插值刷新率
        self.card_rate = ctk.CTkFrame(self.dashboard_frame, height=100)
        self.card_rate.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        self.rate_title = ctk.CTkLabel(self.card_rate, text="鼠标平滑插值率", font=ctk.CTkFont(size=12, weight="bold"))
        self.rate_title.pack(padx=10, pady=(10, 2), anchor="w")
        self.rate_value = ctk.CTkLabel(self.card_rate, text="180 Hz", font=ctk.CTkFont(size=22, weight="bold", family="Consolas"), text_color="#9B59B6")
        self.rate_value.pack(padx=10, pady=(2, 10), anchor="w")

        # 帮助提示条
        self.help_textbox = ctk.CTkTextbox(self.dashboard_frame, height=120, activate_scrollbars=False)
        self.help_textbox.grid(row=3, column=0, columnspan=2, padx=10, pady=(15, 0), sticky="ew")
        self.help_textbox.insert("0.0", "【高刷操控指南】\n"
                                       "1. 仅指食指：在活动框内划动可控制鼠标，追踪节点为关节根部，杜绝抖动。\n"
                                       "2. 大拇指 + 食指捏合：鼠标左击 / 按住不放进行窗口拖拽。\n"
                                       "3. 大拇指 + 中指捏合：鼠标右击。\n"
                                       "4. 三指竖起（食、中、无名指）：进入虚拟摇杆滚动模式，手掌上下位移即可控制长距平滑滚动。")
        self.help_textbox.configure(state="disabled")

    # ==========================================
    # 动态参数绑定函数
    # ==========================================
    def _toggle_system(self):
        """开启或关闭鼠标控制器的检测响应"""
        self.controller.active = self.switch_system.get()

    def _update_smooth(self, value):
        """更新平滑因子（延迟度）"""
        self.smooth_label.configure(text=f"移动延迟 (平滑度): {int(value)}")
        self.controller.smoothening = int(value)

    def _update_sens_x(self, value):
        """根据灵敏度因子，动态改变控制器中 X 活动边界框"""
        self.sens_x_label.configure(text=f"X轴 灵敏度: {value:.2f}")
        # wCam=640. 默认灵敏度 1.5 对应 130 像素边界。
        self.controller.frameR_x = int(320 - 280 / value)

    def _update_sens_y(self, value):
        """根据灵敏度因子，动态改变控制器中 Y 活动边界框"""
        self.sens_y_label.configure(text=f"Y轴 灵敏度: {value:.2f}")
        # hCam=480. 默认灵敏度 1.5 对应 115 像素边界。
        self.controller.frameR_y = int(240 - 188 / value)

    # ==========================================
    # 视频采集与核心分析线程
    # ==========================================
    def _detection_loop(self):
        """后台独立视频分析与检测逻辑，避免阻塞 GUI 渲染"""
        cap = cv2.VideoCapture(0)
        cap.set(3, 640)
        cap.set(4, 480)

        p_time = 0

        while self.running:
            if not self.controller.active:
                self.controller.fps_val = 0
                time.sleep(0.1)
                continue

            success, img = cap.read()
            if not success:
                time.sleep(0.03)
                continue

            # 镜像翻转，并运行手部定位
            img = cv2.flip(img, 1)
            img = self.detector.findHands(img, draw=self.show_preview.get())
            lmList, bbox = self.detector.findPosition(img, draw=False)

            # 更新手别共享数据
            if len(lmList) != 0:
                hand_type = self.detector.getHandedness(0)
                fingers = self.detector.fingersUp(0)
                palm_scale = self.detector.getPalmScale()

                self.controller.hand_type_val = hand_type
                # 更新坐标，传给控制器由 180Hz 线程去插值移动
                self.controller.move_and_action(lmList, fingers, palm_scale, img)

                # 如果开启画面监控，绘制边界框
                if self.show_preview.get() and bbox:
                    xmin, ymin, xmax, ymax = bbox
                    cv2.rectangle(img, (xmin - 15, ymin - 15), (xmax + 15, ymax + 15), (0, 255, 100), 2)
            else:
                self.controller.move_and_action([], [], 1.0)
                self.controller.hand_type_val = "N/A"

            # 计算摄像头采集帧率
            c_time = time.time()
            fps = 1.0 / (c_time - p_time) if (c_time - p_time) > 0 else 0
            p_time = c_time
            self.controller.fps_val = int(fps)

            # 如果显示相机监控画面，使用 OpenCV GUI 展示
            if self.show_preview.get():
                # 绘制当前动态生效的灵敏度活动红框
                fr_x = self.controller.frameR_x
                fr_y = self.controller.frameR_y
                cv2.rectangle(img, (fr_x, fr_y), (640 - fr_x, 480 - fr_y), (255, 0, 180), 2)
                cv2.putText(img, "Active Area", (fr_x + 10, fr_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 180), 1)

                # 绘制顶部半透明 OSD 面板
                overlay = img.copy()
                cv2.rectangle(overlay, (0, 0), (640, 45), (0, 0, 0), cv2.FILLED)
                cv2.addWeighted(overlay, 0.4, img, 0.6, 0, img)

                cv2.putText(img, f"FPS: {self.controller.fps_val}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                cv2.putText(img, f"Hand: {self.controller.hand_type_val}", (140, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(img, f"Action: {self.controller.action_val}", (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)

                cv2.imshow("AI Virtual Mouse Monitor", img)
                cv2.waitKey(1)
            else:
                # 若开关关闭，销毁 OpenCV 窗口释放硬件渲染开销
                try:
                    cv2.destroyWindow("AI Virtual Mouse Monitor")
                except Exception:
                    pass

        cap.release()
        cv2.destroyAllWindows()

    # ==========================================
    # GUI 数据定时刷新循环 (约 10Hz)
    # ==========================================
    def _update_telemetry_loop(self):
        """定期从控制器的共享状态中读取数据，刷新 GUI 面板上的卡片内容"""
        if not self.running:
            return

        # 1. 刷新相机采集帧率
        self.fps_value.configure(text=f"{self.controller.fps_val} FPS")

        # 2. 刷新手别
        self.hand_value.configure(text=self.controller.hand_type_val)

        # 3. 刷新检测状态与显示颜色
        action = self.controller.action_val
        self.status_value.configure(text=action)

        if action == "Left Click / Drag":
            self.status_value.configure(text_color="#E74C3C")  # 红色
        elif action == "Scrolling":
            self.status_value.configure(text_color="#9B59B6")  # 紫色
        elif action == "Right Click":
            self.status_value.configure(text_color="#F1C40F")  # 黄色
        elif action == "Moving":
            self.status_value.configure(text_color="#2ECC71")  # 绿色
        elif action == "System Off":
            self.status_value.configure(text_color="#7F8C8D")  # 灰色
        else:
            self.status_value.configure(text_color="#3498DB")  # 蓝色

        # 每 100ms 刷新一次
        self.after(100, self._update_telemetry_loop)

    def _on_closing(self):
        """关闭窗口时的安全释放逻辑"""
        self.running = False
        self.controller.active = False
        # 等待后台摄像头释放
        time.sleep(0.2)
        self.destroy()
