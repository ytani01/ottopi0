# ロボット顔描画のリファクタリング計画 (Plan07)

## 目的

`samples/robot_face_animation.py`内のロボット顔描画ロジックにおいて、冗長なパラメータの排除と、描画処理の論理的な順序および凝集度向上を図り、コードの可読性、保守性、再利用性をさらに向上させる。

## 計画詳細

### 1. 口の左右対称性に基づいたパラメータの最適化

#### 現状

`RobotFace.LAYOUT`定数には、口のカーブの始点と終点のX座標として`mouth_curve_p0_x`と`mouth_curve_p2_x`が個別に定義されている。これらは口の中心を基準に左右対称であるため、片方から計算可能であり冗長である。

#### 修正内容

1.  `RobotFace.LAYOUT`定数から`mouth_curve_p0_x`と`mouth_curve_p2_x`を削除する。
2.  `RobotFace.LAYOUT`定数に`mouth_curve_half_width` (口のカーブの半分の幅) を追加する。
    *   値は現在の`mouth_curve_p2_x - mouth_cx` (または`mouth_cx - mouth_curve_p0_x`) から計算する。例えば、口の中心X座標が`50`、`mouth_curve_p0_x`が`35`の場合、半分の幅は`15`となる。
3.  `RobotFace._draw_mouth`メソッド内で、口のカーブの始点と終点のX座標を、`mouth_cx`と`mouth_curve_half_width`を使って計算するように変更する。
    *   `p0_x = mouth_cx - self.LAYOUT["mouth_curve_half_width"]`
    *   `p2_x = mouth_cx + self.LAYOUT["mouth_curve_half_width"]`

### 2. 眉毛描画処理の呼び出し位置の最適化

#### 現状

`RobotFace.draw`メソッド内で、`_draw_eyes()`が呼び出された後に、`_draw_brows()`が別途呼び出されている。眉毛は目の上部に描画されるため、目の描画処理の一部として眉毛の描画を呼び出す方が論理的に自然であり、コードの凝集度も高まる。

#### 修正内容

1.  `RobotFace._draw_eyes`メソッドの内部で`_draw_brows()`を呼び出すように変更する。
    *   `_draw_eyes`メソッド内で、現在の`draw`メソッドから`_draw_brows`に渡していた引数を適切に引き継ぐ形で`_draw_brows()`を呼び出す。
2.  `RobotFace.draw`メソッドから、直接`_draw_brows()`を呼び出している行を削除する。

## 品質確認

-   すべての変更完了後、`mise run lint` を実行して、コードスタイルと型チェックに問題がないことを確認する。
-   必要に応じて、動作確認のための手動テスト（シミュレータでの描画確認など）を行う。
