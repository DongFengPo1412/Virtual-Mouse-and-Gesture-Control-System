import cv2
import mediapipe as mp
import math

class HandDetector:
    """
    手部检测与手势分析类
    封装了 MediaPipe Hands 解决方案，提供手势状态及坐标检测服务
    """
    def __init__(self, mode=False, maxHands=1, detectionCon=0.7, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            model_complexity=0,  # 使用极速轻量级检测模型，大幅降低推理延迟
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon
        )
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]
        self.lmList = []
        self.results = None

    def findHands(self, img, draw=True):
        """检测图像中的手部并在图像上绘制手部骨架"""
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo=0, draw=True):
        """获取手部所有关键点坐标及包围框"""
        self.lmList = []
        xList = []
        yList = []
        bbox = []

        if self.results and self.results.multi_hand_landmarks:
            if handNo < len(self.results.multi_hand_landmarks):
                myHand = self.results.multi_hand_landmarks[handNo]
                for id, lm in enumerate(myHand.landmark):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    xList.append(cx)
                    yList.append(cy)
                    self.lmList.append([id, cx, cy])
                    if draw:
                        cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

                xmin, xmax = min(xList), max(xList)
                ymin, ymax = min(yList), max(yList)
                bbox = xmin, ymin, xmax, ymax

                if draw:
                    cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20),
                                  (0, 255, 0), 2)
        return self.lmList, bbox

    def getHandedness(self, handNo=0):
        """
        获取当前检测到的手是左手还是右手
        返回 'Left' 或 'Right'，若未检测到则返回 'Right' 作为默认值
        """
        if self.results and self.results.multi_handedness:
            if handNo < len(self.results.multi_handedness):
                # classification[0].label 可能是 "Left" 或 "Right"
                return self.results.multi_handedness[handNo].classification[0].label
        return "Right"

    def fingersUp(self, handNo=0):
        """
        根据指点与手腕（或相邻关节）的欧氏距离比值判定手指是否竖起。
        此算法完全旋转无关（Rotation-Invariant），无论手部侧倾、旋转还是倒置，均能精准检测。
        """
        fingers = []
        if len(self.lmList) == 0:
            return fingers

        palm_scale = self.getPalmScale()

        # 1. 大拇指判定：计算大拇指尖(4)到食指根部关节(5)的距离
        # 伸直时距离较大（通常 > 0.58 * palm_scale），弯折时贴近食指根部
        x4, y4 = self.lmList[4][1:]
        x5, y5 = self.lmList[5][1:]
        dist_thumb_to_index_base = math.hypot(x5 - x4, y5 - y4)
        if dist_thumb_to_index_base / palm_scale > 0.58:
            fingers.append(1)
        else:
            fingers.append(0)

        # 2. 其他四指判定：计算指尖到手腕(0)的距离与手掌比例的比值
        # 伸直时通常 > 1.35（小指 > 1.25），弯折时因卷缩在掌心，该比值会降到 1.1 以下
        x0, y0 = self.lmList[0][1:]
        
        # 对应：食指(8), 中指(12), 无名指(16), 小指(20)
        tip_ids = [8, 12, 16, 20]
        thresholds = [1.35, 1.35, 1.35, 1.25]
        
        for idx, tip_id in enumerate(tip_ids):
            x_tip, y_tip = self.lmList[tip_id][1:]
            dist_to_wrist = math.hypot(x_tip - x0, y_tip - y0)
            ratio = dist_to_wrist / palm_scale
            
            if ratio > thresholds[idx]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def getPalmScale(self):
        """
        计算手腕(0号点)到中指根部(9号点)的欧式距离
        作为手掌在镜头中大小的基准比例值，用于各种手势距离的自适应归一化
        """
        if len(self.lmList) < 10:
            return 1.0  # 避免除以 0
        x0, y0 = self.lmList[0][1:]
        x9, y9 = self.lmList[9][1:]
        return math.hypot(x9 - x0, y9 - y0)

    def findDistance(self, p1, p2, img, draw=True, r=15, t=3):
        """计算两点间欧式距离"""
        if len(self.lmList) == 0:
            return 0, img, []

        x1, y1 = self.lmList[p1][1:]
        x2, y2 = self.lmList[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        length = math.hypot(x2 - x1, y2 - y1)

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)
        return length, img, [x1, y1, x2, y2, cx, cy]
