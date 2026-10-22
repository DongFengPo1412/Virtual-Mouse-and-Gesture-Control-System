# Virtual Mouse and Gesture Control — 導入と操作

[简体中文](setup.zh-CN.md) · [English](setup.en.md) · **日本語** · [概要](../README_JA.md)

<a id="structure"></a>

## 構成と環境

```text
.
├── main.py
├── src/
│   ├── gui_app.py
│   ├── hand_detector.py
│   └── mouse_controller.py
├── requirements.txt
├── LICENSE
└── docs/   # 三言語ガイドと既存画像
```

独立したデスクトップPython3.10にopencv-python・numpy・mediapipe・pyautogui・customtkinterを用意します。固定版はなく、MediaPipeには`mp.solutions.hands`が必要です。Tkinter・カメラ・OS入力権限を確認し、全OS対応の検証はしていません。

<a id="operation"></a>

## 起動と操作

```powershell
python -m pip install -r requirements.txt
python main.py
```

ルートから起動します。初期操作は有効、カメラ0／640×480固定要求で、選択メニューはありません。スイッチは検出／表示、平滑度を上げると遅く、XY感度は活動域を縮めます。

人差し指で移動、親指とのピンチ保持で左・ドラッグ、離して解放します。右は移動条件を外して親指と中指です。3指を伸ばし小指を曲げて上下移動するとスクロールし、中心域で止まります。Escは主窓を閉じ、プレビューでは操作を停止します。表示を消しても検出は止まりません。

<a id="lifecycle"></a>

## 停止と終了

主ウィンドウのEscは終了、OpenCV画面のEscは操作停止です。GUIから再開できます。停止、手なし・無効、読込失敗、終了は共通解放を使います。入力例外は停止してエラーを保持します。撮像スレッドのjoinは1秒までで、すべてのブロッキングドライバを即停止できる保証ではありません。

<a id="checks"></a>

## 検査と今後

```powershell
python -B -m unittest discover -s tests -v
```

ドラッグ解放、撮像失敗、右ピンチ保持、無効座標・尺度、画面範囲、入力例外、スレッド終了の10件を偽バックエンドで確認し、OSイベントは送っていません。対象環境で物理入力への復帰、角FAILSAFE、Esc、撮像異常を検証してください。旧性能値を今回の実測とはしません。
