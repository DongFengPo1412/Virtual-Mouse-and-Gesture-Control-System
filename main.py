import cv2
import numpy as np
import mediapipe as mp
import pyautogui
import time
import math

##########################
# 参数配置区 (Parameters)
##########################
wCam, hCam = 640, 480       # 摄像头分辨率
frameR = 100                # 矩形框缩减 (Frame Reduction)，用于映射屏幕区域
smoothening = 7             # 平滑因子 (Smoothing Value)
##########################

class HandDetector:
    """
    手部检测模块封装类
    """
    def __init__(self, mode=False, maxHands=1, detectionCon=0.7, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(static_image_mode=self.mode,
                                        max_num_hands=self.maxHands,
                                        min_detection_confidence=self.detectionCon,
                                        min_tracking_confidence=self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils
        # 修复1：补全指尖的 Landmark ID (拇指4, 食指8, 中指12, 无名指16, 小指20)
        self.tipIds = [4, 8, 12, 16, 20]

    def findHands(self, img, draw=True):
        """检测手部并绘制骨架"""
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo=0, draw=True):
        """获取关键点坐标列表"""
        # 修复2：初始化为空列表 []
        self.lmList = []
        xList = []
        yList = []
        bbox = []

        if self.results.multi_hand_landmarks:
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

    def fingersUp(self):
        """判断5根手指是否竖起，返回列表 [0, 1, 1, 0, 0]"""
        fingers = []
        if len(self.lmList) == 0:
            return fingers

        # 修复3：拇指逻辑 (这里假设右手，拇指指尖x < 指节x 表示竖起)
        # 注意：MediaPipe中 4是拇指尖，3是第一指节
        if self.lmList[self.tipIds[0]][1] < self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # 修复4：其他4指 (指尖y < 指节y 表示竖起)
        for id in range(1, 5):
            # tipIds[id] 是指尖索引，-2 是为了取到更下面的关节(PIP)以确保准确
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers

    def findDistance(self, p1, p2, img, draw=True, r=15, t=3):
        """计算两点间欧几里得距离"""
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

# 主程序入口
def main():
    pTime = 0               # 上一帧时间
    plocX, plocY = 0, 0     # 上一帧光标位置
    clocX, clocY = 0, 0     # 当前帧光标位置

    cap = cv2.VideoCapture(0)
    cap.set(3, wCam)
    cap.set(4, hCam)

    detector = HandDetector(maxHands=1)

    # 获取屏幕分辨率
    wScr, hScr = pyautogui.size()

    # 防止 PyAutoGUI 鼠标甩到角落触发 FailSafe
    pyautogui.FAILSAFE = False

    print("系统已启动。按 'q' 键退出。")

    while True:
        # 1. 获取图像并检测手
        success, img = cap.read()
        if not success:
            break
        img = cv2.flip(img, 1) # 镜像翻转，让移动符合直觉
        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img)

        # 2. 绘制操作区域框
        cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR),
                      (255, 0, 255), 2)

        # 3. 如果检测到手
        if len(lmList) != 0:
            # 修复5：正确获取食指(8)和中指(12)的坐标
            # lmList结构是 [id, x, y]，所以切片[1:]取 [x,y]
            x1, y1 = lmList[8][1:]
            x2, y2 = lmList[12][1:]

            # 4. 检查手指竖起状态
            fingers = detector.fingersUp()

            # 5. 移动模式：只有食指竖起 (食指=1, 中指=0)
            if fingers[1] == 1 and fingers[2] == 0:
                # 5.1 坐标映射
                x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
                y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))

                # 5.2 平滑处理 (避免鼠标抖动)
                clocX = plocX + (x3 - plocX) / smoothening
                clocY = plocY + (y3 - plocY) / smoothening

                # 5.3 移动鼠标
                pyautogui.moveTo(clocX, clocY)

                # 更新历史位置
                plocX, plocY = clocX, clocY

                # 视觉反馈
                cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)

            # 6. 点击模式：食指和中指都竖起
            if fingers[1] == 1 and fingers[2] == 1:
                # 6.1 计算食指尖(8)与中指尖(12)的距离
                length, img, lineInfo = detector.findDistance(8, 12, img)

                # 6.2 距离小于阈值 -> 点击
                if length < 40:
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                    pyautogui.click()
                    # 简单的防连点延迟
                    # time.sleep(0.1)

        # 7. 计算并显示 FPS
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, f'FPS: {int(fps)}', (20, 50), cv2.FONT_HERSHEY_PLAIN,
                    3, (255, 0, 0), 3)

        # 8. 显示图像
        cv2.imshow("AI Virtual Mouse", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()