# 総合リファクタリングタスク (Tasks07.md)

`Plan07.md`で定義されたリファクタリング計画を、以下の具体的な作業手順に分解します。

---

### 1. 口の左右対称性に基づいたパラメータの最適化

- [x] `RobotFace.LAYOUT`定数から`mouth_curve_p0_x`を削除する。
- [x] `RobotFace.LAYOUT`定数から`mouth_curve_p2_x`を削除する。
- [x] `RobotFace.LAYOUT`定数に`mouth_curve_half_width`を追加し、値は`15`を設定する。
- [x] `RobotFace._draw_mouth`メソッド内の`p0`の計算を`mouth_cx - self.LAYOUT["mouth_curve_half_width"]`を使用するように変更する。
- [x] `RobotFace._draw_mouth`メソッド内の`p2`の計算を`mouth_cx + self.LAYOUT["mouth_curve_half_width"]`を使用するように変更する。

### 2. 眉毛描画処理の呼び出し位置の最適化

- [x] `RobotFace._draw_eyes`メソッドのシグネチャに必要な引数を追加する（`draw`、`eye_offset`、`eye_y`、`brow_tilt`、`gaze_x`）。
- [x] `RobotFace._draw_eyes`メソッド内で、`_draw_brows()`を呼び出す。
    *   `_draw_brows`に渡す`left_brow_cx`と`right_brow_cx`は、`_draw_eyes`内で`left_eye_cx`と`right_eye_cx`から導出する。
    *   `eye_y`と`brow_tilt`は`_draw_eyes`の引数からそのまま渡す。
- [x] `RobotFace.draw`メソッドから、直接`_draw_brows()`を呼び出している行を削除する。
- [x] `RobotFace.draw`メソッド内の`left_eye_cx`と`right_eye_cx`の定義行を削除する（これらは`_draw_eyes`内で計算されるようになるため）。

## 品質確認

- [x] すべての変更完了後、`mise run lint` を実行して、コードスタイルと型チェックに問題がないことを確認する。
- [x] 必要に応じて、動作確認のための手動テスト（シミュレータでの描画確認など）を行う。