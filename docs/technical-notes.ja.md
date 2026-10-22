# Virtual Mouse and Gesture Control — 技術ノート

[简体中文](technical-notes.zh-CN.md) · [English](technical-notes.en.md) · **日本語** · [概要](../README_JA.md)

<a id="source-map"></a>

## モジュールと呼出し

| ファイル | 役割 |
| :--- | :--- |
| [main.py](../main.py) | VirtualMouseApp生成とループ。 |
| [src/gui_app.py](../src/gui_app.py) | カメラ、鏡像、表示、ワーカー、操作、状態。 |
| [src/hand_detector.py](../src/hand_detector.py) | Hands、21浮動小数x/y点、左右手、指規則、掌スケール。 |
| [src/mouse_controller.py](../src/mouse_controller.py) | np.interp、平滑化、ボタン・スクロール状態、PyAutoGUI。 |

`src/__init__.py`は存在しません。名前空間パッケージで読み込めるため、旧ツリーの不存在ファイルを必須資源とはしません。依存版は未固定です。

<a id="detection"></a>

## 点と尺度

GUIは片手、`model_complexity=0`、検出0.75・追跡0.55です。包装クラス既定0.7/0.5とは異なります。RGBをMediaPipeへ渡し、21点のx/yだけを保存してzを捨てます。浮動小数は物理的サブピクセル精度の実測を意味しません。

```math
S=\sqrt{(x_9-x_0)^2+(y_9-y_0)^2},\qquad r_{ij}=\frac{\sqrt{(x_i-x_j)^2+(y_i-y_j)^2}}{S}
```

親指4–5/Sは0.58、他の指先から手首は1.35/1.35/1.35/1.25です。画像平面の回転には距離が不変ですが、透視・遮蔽・側面・S近傍0には保証がありません。点不足は1を返しても、同一点による0距離を防ぎません。

補助`findDistance(draw=True)`は浮動小数をOpenCV描画へ直接渡します。主GUIは呼ばず、補助経路すべての実行検証は主張しません。

<a id="mapping"></a>

## 座標写像と平滑化

常にLandmark5を使い、クリック前後で切替・固定しません。縮小活動域を`np.interp`で画面へ写し、範囲外は端点です。レンズ校正や追加gamma感度係数はありません。

```math
X=(W_s-1)\mathrm{clip}\left(\frac{x_5-R_x}{640-2R_x},0,1\right),\quad Y=(H_s-1)\mathrm{clip}\left(\frac{y_5-R_y}{480-2R_y},0,1\right)
```

初期余白130/115、スライダーは`int(320-280/vx)`／`int(240-188/vy)`で、表示1.5と初期130は完全一致しません。カメラが640×480を返す仮定で、複数解像度・画面は未検証です。

時刻から求めた速度ではなく、目標までの残距離dを使います。

```math
\alpha=\frac4{\max(1,s)}\left[0.008+(0.25-0.008)\min\left(1,(d/45)^2\right)\right],\quad \hat p_{t+1}=\hat p_t+\alpha(p_{target}-\hat p_t)
```

s=4で0.008–0.25、s=1なら1.0までです。旧0.05–0.95や双線形・Kalmanではありません。計算とシステム呼出しの後にsleep1/180するため180 Hz固定ではありません。

<a id="states"></a>

## 優先順位と終了処理

優先順位は停止/無効入力、移動・左、右、スクロール、待機です。右はピンチ開始で発火し、解放まで保持、0.5 s間隔も残します。移動優先は同じで開掌も移動し得ます。左はdown/upによるドラッグで、専用ダブルクリック分類はありません。

スクロールは人・中・薬指を伸ばし小指を曲げる条件です。Landmark9の開始y、15画素デッドゾーン、0.25係数を使用します。21点の有限座標、5指状態、正の有限な掌尺度を検査します。

`set_active`・`release_input`・`close`で解放を統一しました。RLockで状態を保護し、Eventで平滑化を停止してjoinします。GUIの失敗・finallyでも入力と撮像を解放します。PyAutoGUI FAILSAFEは有効で、強制左解放だけロック内で角チェックを一時回避し、直ちに戻します。ワーカーはGUIが保存したプレビュー真偽値を読みます。

<a id="evidence"></a>

## 過去の画像と計測範囲

| 過去の追従 | 過去のピンチ |
| :---: | :---: |
| ![追従](images/demo_cursor_tracking.png) | ![ピンチ](images/demo_pinch_click.png) |

180 Hzは今回「ループ目標」と明記し、実測値ではありません。撮像後640×480へリサイズして解析し、画面座標を0から幅/高さ−1に写像します。偽入力バックエンドによる回帰10件と4ソースの構文確認が通過しました。実カメラ・GUI・ドライバの停止は別途検証が必要です。
