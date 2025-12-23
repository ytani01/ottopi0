# samples/robot_face_animation.py の修正タスクリスト

`Plan01.md`に基づき、以下の手順で`samples/robot_face_animation.py`を修正します。

### 1. `FaceState`クラスの修正

- [x] `samples/robot_face_animation.py`の`FaceState`データクラスに`eye_curve: float = 0`を追加します。
- [x] `eye_curve`の初期値を`0`に設定します。
- [x] `FaceState`の`copy`メソッドも`eye_curve`をコピーするように修正します。

### 2. `RobotFace`クラスの`MOODS`辞書の更新

- [x] `RobotFace`クラス内の`MOODS`辞書で定義されている各表情に`eye_curve`属性を追加します。
    - [x] `neutral`: `eye_curve=0`
    - [x] `happy`: `eye_curve=1`
    - [x] `sad`: `eye_curve=-1`
    - [x] `angry`: `eye_curve=0`
    - [x] `wink`: `eye_curve=1`
    - [x] `surprised`: `eye_curve=0`
    - [x] `sleepy`: `eye_curve=0`
    - [x] `nikoniko`: `eye_curve=1`

### 3. `RobotFace`クラスの`_draw_eye`メソッドの修正

- [x] `_draw_eye`メソッド内の、目が閉じている場合（`ry < 4`）の描画ロジックを修正します。
- [x] `self.current_state.mouth_curve > 5` という条件を削除し、`self.current_state.eye_curve`の値に基づいて描画を分岐させます。
    - [x] `eye_curve`が`0`の場合：直線を描画します。
    - [x] `eye_curve`が`0`でない場合：ベジェ曲線を描画します。
        - [x] ベジェ曲線の制御点`p1`のY座標を `eye_y - 8 * self.current_state.eye_curve` のように、`eye_curve`の値に応じて動的に変更します。（`eye_curve`が1なら山なり、-1なら谷なりになる）

### 4. `RobotFace`クラスの`update`メソッドの修正

- [x] `update`メソッド内に、`eye_curve`属性を線形補間するための処理を追加します。
    - [x] `c.eye_curve = lerp(c.eye_curve, t.eye_curve, speed)` の行を追加します。
