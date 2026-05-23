import cv2
import time
from src.hand_detector import HandDetector
from src.mouse_controller import MouseController

# ==========================================
# 参数配置区 (Parameters)
# ==========================================
wCam, hCam = 640, 480       # 摄像头分辨率
frameR_x = 130              # 左右边缘缩减宽度
frameR_y = 115              # 上下边缘缩减高度
smoothening = 4             # 平滑因子，调小（如4）响应更快，延迟更低；调大更平滑，但有滞后

def main():
    # 1. 初始化摄像头
    cap = cv2.VideoCapture(0)
    cap.set(3, wCam)
    cap.set(4, hCam)

    if not cap.isOpened():
        print("错误：无法打开摄像头！请检查设备连接。")
        return

    # 2. 初始化核心模块
    detector = HandDetector(maxHands=1, detectionCon=0.75, trackCon=0.55)
    controller = MouseController(wCam=wCam, hCam=hCam, smoothening=smoothening, frameR_x=frameR_x, frameR_y=frameR_y)

    pTime = 0
    print("AI 虚拟鼠标系统已启动。操作提示（已针对人类舒适度深度优化）：")
    print(" - 仅竖起食指: 移动鼠标光标（使用关节追踪，完全防抖）")
    print(" - 大拇指与食指捏合: 鼠标左击 / 按住拖拽")
    print(" - 大拇指与中指捏合: 鼠标右击")
    print(" - 食指、中指、无名指三指伸直: 激活虚拟摇杆滚动（手掌偏离中心线上移/下移即可平滑长距离滚动）")
    print(" - 按下 'q' 键退出程序。")

    while True:
        # 3. 读取摄像头帧
        success, img = cap.read()
        if not success:
            print("警告：无法从摄像头获取图像。")
            break

        # 4. 镜像翻转，使移动与物理直觉一致
        img = cv2.flip(img, 1)

        # 5. 运行手部检测
        img = detector.findHands(img, draw=True)
        lmList, bbox = detector.findPosition(img, draw=False)

        # 状态显示文本
        current_state = "No Hand"
        hand_type = "N/A"

        # 6. 如果检测到手部，处理鼠标逻辑
        if len(lmList) != 0:
            hand_type = detector.getHandedness(0)
            fingers = detector.fingersUp(0)
            palm_scale = detector.getPalmScale()

            # 执行鼠标控制
            controller.move_and_action(lmList, fingers, palm_scale, img)

            # 解析用于 OSD 显示的当前状态
            is_scroll_mode = (fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0)
            
            if is_scroll_mode:
                current_state = "Scrolling"
            else:
                x_thumb, y_thumb = lmList[4][1:]
                x_index, y_index = lmList[8][1:]
                x_middle, y_middle = lmList[12][1:]
                
                dist_ti = controller.get_distance((x_thumb, y_thumb), (x_index, y_index))
                ratio_ti = dist_ti / palm_scale
                
                dist_tm = controller.get_distance((x_thumb, y_thumb), (x_middle, y_middle))
                ratio_tm = dist_tm / palm_scale

                if ratio_ti < controller.click_ratio:
                    current_state = "Left Click / Drag"
                elif ratio_tm < controller.right_click_ratio:
                    current_state = "Right Click"
                elif fingers[1] == 1:
                    current_state = "Moving"
                else:
                    current_state = "Ready"

            # 绘制检测手部包围框 (稍微平滑美观一些)
            if bbox:
                xmin, ymin, xmax, ymax = bbox
                cv2.rectangle(img, (xmin - 15, ymin - 15), (xmax + 15, ymax + 15), (0, 255, 100), 2)

        # 7. 绘制 UI OSD 界面与映射区域框
        # 绘制操作活动区（紫色框，根据X/Y独立设定）
        cv2.rectangle(img, (frameR_x, frameR_y), (wCam - frameR_x, hCam - frameR_y), (255, 0, 180), 2)
        cv2.putText(img, "Active Area", (frameR_x + 10, frameR_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 180), 1)

        # 计算实时 FPS
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        # 绘制顶部半透明黑色状态栏背景
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (wCam, 45), (0, 0, 0), cv2.FILLED)
        cv2.addWeighted(overlay, 0.4, img, 0.6, 0, img)

        # 渲染运行状态、检测到的左右手与帧率
        cv2.putText(img, f"FPS: {int(fps)}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(img, f"Hand: {hand_type}", (140, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(img, f"Action: {current_state}", (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)

        # 8. 显示监控画面
        cv2.imshow("AI Virtual Mouse Controller", img)

        # 按 'q' 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()