import pyautogui
import numpy as np
import time
import math

class MouseController:
    """
    鼠标控制与手势执行类
    - 支持高帧率无延迟操作 (pyautogui.PAUSE = 0)
    - 针对点击时的“指尖收缩抖动”进行了定位点优化（追踪食指根部关节）
    - 提供了抗侧倾、更符合人体工学的“大拇指-食指捏合左击/拖拽”与“大拇指-中指捏合右击”手势
    - 提供了虚拟摇杆式持续滚动页面功能，回中位即停，解决画面颤抖和移动受限问题
    """
    def __init__(self, wCam, hCam, smoothening=5, frameR_x=130, frameR_y=115, click_ratio=0.35, right_click_ratio=0.35):
        self.wCam = wCam
        self.hCam = hCam
        self.smoothening = smoothening
        
        # 独立的 X、Y 活动框边缘缩减（数值越大，活动区域越小，映射到屏幕越敏感，越容易够到死角和底部）
        self.frameR_x = frameR_x
        self.frameR_y = frameR_y
        
        # 归一化点击判断阈值（捏合指尖距离 / 手掌大小）
        self.click_ratio = click_ratio
        self.right_click_ratio = right_click_ratio

        # 获取并配置 PyAutoGUI
        self.wScr, self.hScr = pyautogui.size()
        
        # 【关键优化：消除 PyAutoGUI 默认延迟，使帧率上限解锁到 60+ FPS】
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = False

        # 滤波状态变量
        self.plocX, self.plocY = 0, 0
        self.clocX, self.clocY = 0, 0
        
        self.is_left_clicked = False
        self.is_right_clicked = False
        
        # 虚拟摇杆滚动的基准 Y 坐标
        self.scroll_start_y = None
        self.last_right_click_time = 0

    def get_distance(self, p1_coord, p2_coord):
        """计算两点坐标的欧氏距离"""
        return math.hypot(p2_coord[0] - p1_coord[0], p2_coord[1] - p1_coord[1])

    def move_and_action(self, lmList, fingers, palm_scale, img=None):
        """
        根据检测到的手部关键点及手指状态执行对应鼠标操作
        """
        if len(lmList) == 0:
            # 手掌丢失时释放按键并重置滚动
            if self.is_left_clicked:
                pyautogui.mouseUp()
                self.is_left_clicked = False
            self.scroll_start_y = None
            return

        # 提取关键手指的坐标
        # 4: 拇指尖, 8: 食指尖, 12: 中指尖, 5: 食指根部关节 (MCP)
        x_thumb, y_thumb = lmList[4][1:]
        x_index, y_index = lmList[8][1:]
        x_middle, y_middle = lmList[12][1:]
        
        # 【定位优化】使用食指根部关节(5)进行屏幕坐标映射追踪，防止手指捏合时指尖剧烈抖动导致光标漂移
        x_track, y_track = lmList[5][1:]

        # 计算最新的捏合比例
        dist_thumb_index = self.get_distance((x_thumb, y_thumb), (x_index, y_index))
        ratio_thumb_index = dist_thumb_index / palm_scale

        dist_thumb_middle = self.get_distance((x_thumb, y_thumb), (x_middle, y_middle))
        ratio_thumb_middle = dist_thumb_middle / palm_scale

        # 检查是否满足“滚轮滚动”的三指手势模式 (食指、中指、无名指伸直，小指弯曲)
        is_scroll_mode = (fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0)

        # ==========================================
        # 1. 移动与左击/拖拽模式 (非滚动模式下，食指伸直 或 处于左击按住状态中)
        # ==========================================
        if not is_scroll_mode and (fingers[1] == 1 or self.is_left_clicked):
            # 1.1 映射食指根部坐标到屏幕（支持越界截断，活动区更集中）
            x3 = np.interp(x_track, (self.frameR_x, self.wCam - self.frameR_x), (0, self.wScr))
            y3 = np.interp(y_track, (self.frameR_y, self.hCam - self.frameR_y), (0, self.hScr))

            # 1.2 平滑滤波处理
            self.clocX = self.plocX + (x3 - self.plocX) / self.smoothening
            self.clocY = self.plocY + (y3 - self.plocY) / self.smoothening

            # 1.3 如果大拇指与食指捏合 -> 触发左键按下（单击/拖拽）
            if ratio_thumb_index < self.click_ratio:
                if not self.is_left_clicked:
                    pyautogui.mouseDown()
                    self.is_left_clicked = True
                pyautogui.moveTo(self.clocX, self.clocY)
            else:
                # 释放捏合 -> 松开左键
                if self.is_left_clicked:
                    pyautogui.mouseUp()
                    self.is_left_clicked = False
                
                # 正常移动鼠标
                pyautogui.moveTo(self.clocX, self.clocY)

            # 更新上一帧位置
            self.plocX, self.plocY = self.clocX, self.clocY
            self.scroll_start_y = None

        # ==========================================
        # 2. 右击模式 (非滚动模式下，大拇指与中指捏合)
        # ==========================================
        elif not is_scroll_mode and ratio_thumb_middle < self.right_click_ratio:
            current_time = time.time()
            if not self.is_right_clicked and (current_time - self.last_right_click_time > 0.5):
                pyautogui.rightClick()
                self.is_right_clicked = True
                self.last_right_click_time = current_time
            
            # 清理左击状态
            if self.is_left_clicked:
                pyautogui.mouseUp()
                self.is_left_clicked = False
            self.scroll_start_y = None

        # ==========================================
        # 3. 页面滚动模式 (虚拟摇杆：三指竖起控制方向和速度)
        # ==========================================
        elif is_scroll_mode:
            # 释放左键
            if self.is_left_clicked:
                pyautogui.mouseUp()
                self.is_left_clicked = False
            
            # 跟踪中指根部(9)的 y 坐标作为摇杆垂直位移量
            curr_y = lmList[9][2]
            
            # 3.1 记录刚进入滚动模式时的手部 Y 轴位置作为“中心中位线”
            if self.scroll_start_y is None:
                self.scroll_start_y = curr_y
            else:
                diff_y = curr_y - self.scroll_start_y
                deadzone = 15  # 中心死区阈值，在此范围内不触发滚动，避免手部轻微自然抖动导致页面晃动
                
                if abs(diff_y) > deadzone:
                    # 计算超出死区的偏移量
                    offset = diff_y - np.sign(diff_y) * deadzone
                    # 速度计算：位移越远速度越快 (0.3 为缩放因子，可调整阻尼)
                    scroll_speed = -int(offset * 0.25)
                    if scroll_speed != 0:
                        pyautogui.scroll(scroll_speed)
                        
        else:
            # 其他手势或无效动作，清理所有状态
            if self.is_left_clicked:
                pyautogui.mouseUp()
                self.is_left_clicked = False
            self.is_right_clicked = False
            self.scroll_start_y = None
