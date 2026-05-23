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
        判断各手指是否竖起，返回形如 [0, 1, 1, 0, 0] 的列表
        完美支持左右手自适应大拇指检测
        """
        fingers = []
        if len(self.lmList) == 0:
            return fingers

        # 获取当前手是左手还是右手
        handType = self.getHandedness(handNo)

        # 1. 大拇指自适应判定
        # 右手：大拇指尖(4)的 x 坐标小于第一指节(3)的 x 坐标，代表向外伸展（竖起）
        # 左手：大拇指尖(4)的 x 坐标大于第一指节(3)的 x 坐标，代表向外伸展（竖起）
        if handType == "Right":
            if self.lmList[self.tipIds[0]][1] < self.lmList[self.tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        else:  # Left Hand
            if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)

        # 2. 其他 4 指判定（指尖 y 坐标小于指节 y 坐标代表伸直）
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
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
