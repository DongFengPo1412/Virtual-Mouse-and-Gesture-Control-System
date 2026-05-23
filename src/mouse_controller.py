import pyautogui
import numpy as np
import time
import math

class MouseController:
    """
    鼠标控制与手势执行类
    处理坐标映射、平滑滤波以及具体手势的模拟（移动、左击、拖拽、右击、滚动）
    """
    def __init__(self, wCam, hCam, smoothening=7, frameR=100, click_ratio=0.32, right_click_ratio=0.32):
        self.wCam = wCam
        self.hCam = hCam
        self.smoothening = smoothening
        self.frameR = frameR
        
        # 归一化手势比例阈值（两指距离 / 手掌基准长度）
        self.click_ratio = click_ratio
        self.right_click_ratio = right_click_ratio

        # 获取屏幕分辨率
        self.wScr, self.hScr = pyautogui.size()
        
        # 禁用 PyAutoGUI 的 fail-safe 以防甩到角落报错
        pyautogui.FAILSAFE = False

        # 状态变量与滤波缓存
        self.plocX, self.plocY = 0, 0
        self.clocX, self.clocY = 0, 0
        
        self.is_left_clicked = False
        self.is_right_clicked = False
        self.prev_scroll_y = None
        
        # 简单的双击/防抖冷却时间
        self.last_right_click_time = 0

    def get_distance(self, p1_coord, p2_coord):
        """计算两点坐标的欧式距离"""
        return math.hypot(p2_coord[0] - p1_coord[0], p2_coord[1] - p1_coord[1])

    def move_and_action(self, lmList, fingers, palm_scale, img=None):
        """
        根据检测到的手部关键点及手指状态执行对应鼠标操作
        """
        if len(lmList) == 0:
            # 手消失时释放左键（防止卡在拖动状态）
            if self.is_left_clicked:
                pyautogui.mouseUp()
                self.is_left_clicked = False
            self.prev_scroll_y = None
            return

        # 提取关键手指的坐标
        # 4: 拇指尖, 8: 食指尖, 12: 中指尖, 16: 无名指尖
        x_thumb, y_thumb = lmList[4][1:]
        x_index, y_index = lmList[8][1:]
        x_middle, y_middle = lmList[12][1:]
        x_ring, y_ring = lmList[16][1:]

        # ==========================================
        # 1. 移动与拖拽/左击模式 (食指=1, 中指=1/0)
        # ==========================================
        if fingers[1] == 1 and fingers[3] == 0 and fingers[4] == 0:
            # 1.1 计算食指与中指尖的归一化距离
            dist_index_middle = self.get_distance((x_index, y_index), (x_middle, y_middle))
            ratio_index_middle = dist_index_middle / palm_scale

            # 1.2 映射坐标到屏幕
            # np.interp 将摄像头局部框内的坐标线性映射到屏幕分辨率
            x3 = np.interp(x_index, (self.frameR, self.wCam - self.frameR), (0, self.wScr))
            y3 = np.interp(y_index, (self.frameR, self.hCam - self.frameR), (0, self.hScr))

            # 1.3 一阶滞后平滑滤波
            self.clocX = self.plocX + (x3 - self.plocX) / self.smoothening
            self.clocY = self.plocY + (y3 - self.plocY) / self.smoothening

            # 1.4 如果中指也竖起并且两指并拢 -> 触发左击/拖拽
            if fingers[2] == 1 and ratio_index_middle < self.click_ratio:
                if not self.is_left_clicked:
                    pyautogui.mouseDown()
                    self.is_left_clicked = True
                pyautogui.moveTo(self.clocX, self.clocY)
            else:
                # 释手时松开左键
                if self.is_left_clicked:
                    pyautogui.mouseUp()
                    self.is_left_clicked = False
                
                # 仅食指竖起 -> 纯鼠标移动
                if fingers[2] == 0:
                    pyautogui.moveTo(self.clocX, self.clocY)

            # 更新历史坐标
            self.plocX, self.plocY = self.clocX, self.clocY
            self.prev_scroll_y = None

        # ==========================================
        # 2. 右击模式 (食指竖起，中指弯曲，但大拇指与中指捏合)
        # ==========================================
        elif fingers[1] == 1 and fingers[2] == 0:
            dist_thumb_middle = self.get_distance((x_thumb, y_thumb), (x_middle, y_middle))
            ratio_thumb_middle = dist_thumb_middle / palm_scale

            if ratio_thumb_middle < self.right_click_ratio:
                current_time = time.time()
                # 限制右键触发冷却，防止连续多次点击
                if not self.is_right_clicked and (current_time - self.last_right_click_time > 0.6):
                    pyautogui.rightClick()
                    self.is_right_clicked = True
                    self.last_right_click_time = current_time
            else:
                self.is_right_clicked = False
            
            # 清理其他状态
            if self.is_left_clicked:
                pyautogui.mouseUp()
                self.is_left_clicked = False
            self.prev_scroll_y = None

        # ==========================================
        # 3. 滚轮模式 (食指、中指、无名指均竖起，小指弯曲)
        # ==========================================
        elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0:
            # 用中指根部(9号点)的y坐标来跟踪手掌垂直运动
            curr_y = lmList[9][2]
            
            if self.prev_scroll_y is not None:
                diff_y = curr_y - self.prev_scroll_y
                # 设定阈值避免极其微小的抖动触发滚动
                if abs(diff_y) > 8:
                    # 摄像头 y 坐标向下为正，因此 diff_y > 0 说明手在往下移，对应页面往下滚（pyautogui scroll 负值）
                    # 缩放因子设为 2.0 保证滚动响应灵敏
                    scroll_amount = int(-diff_y * 2.0)
                    pyautogui.scroll(scroll_amount)
            
            self.prev_scroll_y = curr_y
            
            # 清理其他状态
            if self.is_left_clicked:
                pyautogui.mouseUp()
                self.is_left_clicked = False
        
        else:
            # 其它无效手势，清理所有状态
            if self.is_left_clicked:
                pyautogui.mouseUp()
                self.is_left_clicked = False
            self.prev_scroll_y = None
