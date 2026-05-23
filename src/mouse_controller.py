import pyautogui
import numpy as np
import time
import math
import threading

class MouseController:
    """
    鼠标控制与手势执行类
    - 支持 180Hz 独立高频插值线程，保证屏幕在 180Hz 刷新率下的极致流畅体验
    - 针对点击时的“指尖收缩抖动”进行了定位点优化（追踪食指根部关节）
    - 提供了抗侧倾、更符合人体工学的“大拇指-食指捏合左击/拖拽”与“大拇指-中指捏合右击”手势
    - 提供了虚拟摇杆式持续滚动页面功能，回中位即停，解决画面颤抖和移动受限问题
    """
    def __init__(self, wCam, hCam, smoothening=4, frameR_x=130, frameR_y=115, click_ratio=0.35, right_click_ratio=0.35):
        self.wCam = wCam
        self.hCam = hCam
        self.smoothening = smoothening
        
        # 独立的 X、Y 活动框边缘缩减
        self.frameR_x = frameR_x
        self.frameR_y = frameR_y
        
        # 归一化点击判断阈值
        self.click_ratio = click_ratio
        self.right_click_ratio = right_click_ratio

        # 获取并配置 PyAutoGUI
        self.wScr, self.hScr = pyautogui.size()
        
        # 消除 PyAutoGUI 默认延迟
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = False

        # 系统运行开关（由 GUI 动态控制）
        self.active = True
        self.is_left_clicked = False
        self.is_right_clicked = False
        
        # 虚拟摇杆滚动的基准 Y 坐标
        self.scroll_start_y = None
        self.last_right_click_time = 0

        # OSD 共享状态数据，用于 GUI 面板渲染
        self.fps_val = 0
        self.hand_type_val = "N/A"
        self.action_val = "Ready"

        # ==========================================
        # 180Hz 鼠标高频插值引擎初始化
        # ==========================================
        self.clocX, self.clocY = pyautogui.position() # 初始化为当前系统光标的真实位置
        self.target_x, self.target_y = self.clocX, self.clocY
        self.has_target = False

        # 启动 180Hz 插值常驻线程
        self.mouse_thread = threading.Thread(target=self._mouse_interpolation_loop, daemon=True)
        self.mouse_thread.start()

    def _mouse_interpolation_loop(self):
        """
        以 180Hz 的高频微循环进行坐标平滑插值移动，模拟原生 180Hz 高刷鼠标手感
        """
        while True:
            if self.active and self.has_target:
                # 180Hz 平滑插值逼近计算 (一阶低通滤波)
                self.clocX = self.clocX + (self.target_x - self.clocX) / self.smoothening
                self.clocY = self.clocY + (self.target_y - self.clocY) / self.smoothening
                
                # 避开微小的浮点数波动，减少不必要的系统API调用开销
                if abs(self.target_x - self.clocX) > 0.1 or abs(self.target_y - self.clocY) > 0.1:
                    pyautogui.moveTo(int(self.clocX), int(self.clocY))
            
            # 1/180 秒 = 0.00555... 秒 (约 5.5ms)
            time.sleep(1.0 / 180.0)

    def get_distance(self, p1_coord, p2_coord):
        """计算两点坐标的欧氏距离"""
        return math.hypot(p2_coord[0] - p1_coord[0], p2_coord[1] - p1_coord[1])

    def move_and_action(self, lmList, fingers, palm_scale, img=None):
        """
        根据检测到的手部关键点及手指状态更新鼠标状态和插值终点
        """
        # 如果系统已关闭，释放按键并停止插值
        if not self.active:
            if self.is_left_clicked:
                pyautogui.mouseUp()
                self.is_left_clicked = False
            self.has_target = False
            self.scroll_start_y = None
            self.action_val = "System Off"
            self.prev_x_track = None  # 重置历史定位坐标
            return

        if len(lmList) == 0:
            # 手掌丢失时释放按键并重置滚动
            if self.is_left_clicked:
                pyautogui.mouseUp()
                self.is_left_clicked = False
            self.has_target = False
            self.scroll_start_y = None
            self.action_val = "No Hand"
            self.prev_x_track = None  # 重置历史定位坐标
            return

        # 提取关键手指的坐标
        # 4: 拇指尖, 8: 食指尖, 12: 中指尖, 5: 食指根部关节 (MCP)
        x_thumb, y_thumb = lmList[4][1:]
        x_index, y_index = lmList[8][1:]
        x_middle, y_middle = lmList[12][1:]
        
        # 使用食指根部关节(5)进行屏幕坐标映射追踪，防止手指捏合时指尖剧烈抖动导致光标漂移
        x_track, y_track = lmList[5][1:]

        # 【源头防抖核心 1】：初始化上一帧的相机坐标
        if not hasattr(self, 'prev_x_track') or self.prev_x_track is None:
            self.prev_x_track, self.prev_y_track = x_track, y_track

        # 【源头防抖核心 2】：在相机低分辨率坐标系（640x480）中计算微小噪声
        # 如果手部变化距离小于 1.3 像素，则判定为镜头噪点，强制锁定坐标为上一帧值
        dist_cam = math.hypot(x_track - self.prev_x_track, y_track - self.prev_y_track)
        if dist_cam < 1.3:
            x_track, y_track = self.prev_x_track, self.prev_y_track
        else:
            self.prev_x_track, self.prev_y_track = x_track, y_track

        # 计算最新的捏合比例
        dist_thumb_index = self.get_distance((x_thumb, y_thumb), (x_index, y_index))
        ratio_thumb_index = dist_thumb_index / palm_scale

        dist_thumb_middle = self.get_distance((x_thumb, y_thumb), (x_middle, y_middle))
        ratio_thumb_middle = dist_thumb_middle / palm_scale

        # 检查是否满足“滚轮滚动”的三指手势模式
        is_scroll_mode = (fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0)

        # ==========================================
        # 1. 移动与左击/拖拽模式 (非滚动模式下，食指伸直 或 处于左击按住状态中)
        # ==========================================
        if not is_scroll_mode and (fingers[1] == 1 or self.is_left_clicked):
            # 1.1 映射食指根部坐标到屏幕（支持越界截断，活动区更集中）
            x3 = np.interp(x_track, (self.frameR_x, self.wCam - self.frameR_x), (0, self.wScr))
            y3 = np.interp(y_track, (self.frameR_y, self.hCam - self.frameR_y), (0, self.hScr))

            # 1.2 如果前一帧手部不在移动态，则将插值起点与当前真实鼠标位置对齐，防大范围跳跃
            if not self.has_target:
                self.clocX, self.clocY = pyautogui.position()
                self.target_x, self.target_y = x3, y3
                self.has_target = True

            # 1.3 辅助屏幕死区（双重保障）
            dist_to_current = math.hypot(x3 - self.clocX, y3 - self.clocY)
            if dist_to_current > 2.0:
                self.target_x, self.target_y = x3, y3
                self.has_target = True

            # 1.4 如果大拇指与食指捏合 -> 触发左键按下（单击/拖拽）
            if ratio_thumb_index < self.click_ratio:
                if not self.is_left_clicked:
                    pyautogui.mouseDown()
                    self.is_left_clicked = True
                self.action_val = "Left Click / Drag"
            else:
                # 释放捏合 -> 松开左键
                if self.is_left_clicked:
                    pyautogui.mouseUp()
                    self.is_left_clicked = False
                self.action_val = "Moving"

            self.scroll_start_y = None

        # ==========================================
        # 2. 右击模式 (非滚动模式下，大拇指与中指捏合)
        # ==========================================
        elif not is_scroll_mode and ratio_thumb_middle < self.right_click_ratio:
            self.has_target = False  # 停止鼠标光标移动，静止状态下右击
            current_time = time.time()
            if not self.is_right_clicked and (current_time - self.last_right_click_time > 0.5):
                pyautogui.rightClick()
                self.is_right_clicked = True
                self.last_right_click_time = current_time
                self.action_val = "Right Click"
            else:
                self.is_right_clicked = False
                self.action_val = "Ready"
            
            # 清理左击状态
            if self.is_left_clicked:
                pyautogui.mouseUp()
                self.is_left_clicked = False
            self.scroll_start_y = None

        # ==========================================
        # 3. 页面滚动模式 (虚拟摇杆：三指竖起控制方向和速度)
        # ==========================================
        elif is_scroll_mode:
            self.has_target = False  # 滚动时锁定光标不进行移动
            self.action_val = "Scrolling"
            if self.is_left_clicked:
                pyautogui.mouseUp()
                self.is_left_clicked = False
            
            # 跟踪中指根部(9)的 y 坐标作为摇杆垂直位移量
            curr_y = lmList[9][2]
            
            # 记录刚进入滚动模式时的手部 Y 轴位置作为“中心中位线”
            if self.scroll_start_y is None:
                self.scroll_start_y = curr_y
            else:
                diff_y = curr_y - self.scroll_start_y
                deadzone = 15  # 中心死区
                
                if abs(diff_y) > deadzone:
                    # 计算超出死区的偏移量
                    offset = diff_y - np.sign(diff_y) * deadzone
                    # 速度计算
                    scroll_speed = -int(offset * 0.25)
                    if scroll_speed != 0:
                        pyautogui.scroll(scroll_speed)
                        
        else:
            # 其他手势或无效动作，清理所有状态
            self.has_target = False
            if self.is_left_clicked:
                pyautogui.mouseUp()
                self.is_left_clicked = False
            self.is_right_clicked = False
            self.scroll_start_y = None
            self.action_val = "Ready"
