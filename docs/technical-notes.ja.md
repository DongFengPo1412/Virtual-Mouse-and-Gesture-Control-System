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
X=W_s\operatorname{clip}\left(\frac{x_5-R_x}{640-2R_x},0,1\right),\quad Y=H_s\operatorname{clip}\left(\frac{y_5-R_y}{480-2R_y},0,1\right)
```

初期余白130/115、スライダーは`int(320-280/vx)`／`int(240-188/vy)`で、表示1.5と初期130は完全一致しません。カメラが640×480を返す仮定で、複数解像度・画面は未検証です。

時刻から求めた速度ではなく、目標までの残距離dを使います。

```math
\alpha=\frac4{\max(1,s)}\left[0.008+(0.25-0.008)\min\left(1,(d/45)^2\right)\right],\quad \hat p_{t+1}=\hat p_t+\alpha(p_{target}-\hat p_t)
```

s=4で0.008–0.25、s=1なら1.0までです。旧0.05–0.95や双線形・Kalmanではありません。計算とシステム呼出しの後にsleep1/180するため180 Hz固定ではありません。

<a id="states"></a>

## 優先順位と終了処理

無効→手なし→移動／左→右→スクロール→待機の順です。移動は人差し指だけが条件で他指の収納を要求せず、開掌でも動き、中指ピンチより優先されます。

ピンチ閾値は両方0.35。右は保持中にフラグを交互解除し、0.5 s後に再発火し得るため、1ピンチ1回ではありません。左はdown/upで保持中にドラッグし、専用ダブルクリック状態はありません。

スクロールは人・中・薬指を伸ばし小指を曲げ、親指は無関係です。Landmark9開始y、15画素デッドゾーン、超過×0.25を整数化・反転し、検出ループごとに送ります。2指をそろえる横スクロールではありません。

通常の手なしは左を解放しますが、GUI無効時は`move_and_action`を呼ばず、内部解放分岐を迂回します。終了はrunning/activeを変えて0.2 s待つだけでmouseUp・joinなし、補間はデーモンの無限ループです。撮像失敗も解放を迂回します。PyAutoGUI FAILSAFEを無効にし、画面隅での停止は保証しません。

<a id="evidence"></a>

## 過去の画像と計測範囲

| 過去の追従 | 過去のピンチ |
| :---: | :---: |
| ![追従](images/demo_cursor_tracking.png) | ![ピンチ](images/demo_pinch_click.png) |

180 Hzは定数、FPSは検出ループ全体の時間差を整数化した値で、初回は0から測ります。モデル単独速度ではありません。共有座標・状態はロックなし、ワーカーがTk変数を読み、入力・終了の実機検証が必要です。

Python4本の解析のみ通過し、カメラ・GUI・入力は試していません。旧33 ms、30–35 FPS、CPU16–18%、120 MB、720p/1080p表はスクリプト・生ログがなく成果表示を削除しました。パッケージのメタ情報は動作成功ではありません。
