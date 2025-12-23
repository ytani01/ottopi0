# `robot_face_animation.py` リファクタリングタスクリスト

`Plan02.md`に基づき、以下の手順で`samples/robot_face_animation.py`をリファクタリングします。

### 1. `EyeState`データクラスの作成

- [x] `FaceState`クラスの上に、`EyeState`データクラスを新規作成します。
- [x] `EyeState`に以下の属性を定義します。
    - `openness: float = 1.0`
    - `size: float = 8.0`
    - `curve: float = 0.0`
- [x] `EyeState`に、自分自身のコピーを返す`copy(self)`メソッドを追加します。

### 2. `FaceState`クラスの修正

- [x] `FaceState`から以下の属性を削除します。
    - `eye_height`
    - `wink_left`
    - `wink_right`
    - `eye_curve`
- [x] `eye_tilt`属性を`brow_tilt`にリネームします。
- [x] `FaceState`に以下の属性を追加します。
    - `left_eye: EyeState`
    - `right_eye: EyeState`
- [x] `FaceState`の`__post_init__`メソッドを追加し、`left_eye`と`right_eye`が`None`の場合に`EyeState()`で初期化されるようにします。
- [x] `FaceState`の`copy`メソッドを修正し、`left_eye.copy()`と`right_eye.copy()`を呼び出すように変更します。

### 3. `RobotFace`クラスの`MOODS`辞書の更新

- [x] `RobotFace`クラス内の`MOODS`辞書を、新しい`FaceState`と`EyeState`の構造に合わせて更新します。
- [x] 各表情（`neutral`, `happy`, `sad`など）の定義を、`left_eye=EyeState(...)`と`right_eye=EyeState(...)`を含む形に修正します。

### 4. `RobotFace`クラスの`update`メソッドの修正

- [x] `update`メソッドを修正し、`left_eye`と`right_eye`の各属性（`openness`, `size`, `curve`）がターゲットの状態に向かって線形補間されるようにロジックを追加します。

### 5. `RobotFace`クラスの`_draw_eye`メソッドの修正

- [x] `_draw_eye`メソッドのシグネチャを、`eye_state: EyeState`を引数として受け取るように変更します。
- [x] `draw`メソッド内の`_draw_eye`の呼び出し部分を、`self.current_state.left_eye`と`self.current_state.right_eye`を渡すように修正します。
- [x] `_draw_eye`メソッド内のロジックを、`eye_state.openness`, `eye_state.size`, `eye_state.curve`を参照するように全面的に書き換えます。
- [x] `brow_tilt`を`_draw_eye`に渡すように修正します。

### 6. 動作確認

- [x] `mise run lint`を実行し、コードスタイルや文法に問題がないことを確認します。
- [x] スクリプトを実行し、表情が意図通りに描画・アニメーションされることを確認します。（特に、悲しい顔の時に目が谷なりになること、ウィンクが正しく動作することを確認）