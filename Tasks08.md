# 総合リファクタリングタスク (Tasks08.md)

`Plan08.md`で定義されたリファクタリング計画を、以下の具体的な作業手順に分解します。

---

## 1. 状態クラスに補間（lerp）ロジックを集約する

### 1.1 EyeState
- [ ] `EyeState`クラスの`_init_`メソッドの直後に`lerp_to(self, target: EyeState, t: float)`メソッドを追加する。
- [ ] `EyeState.lerp_to`メソッド内で`self.openness`、`self.size`、`self.curve`を`target`の対応する属性に向けて`t`の割合で補間するロジックを実装する（例: `self.openness = lerp(self.openness, target.openness, t)`）。
- [ ] `RobotFace.update`メソッドから、`self.current_state.left_eye.openness = lerp(...)`のような`EyeState`オブジェクトの`openness`、`size`、`curve`の直接補間ロジックを削除する。

### 1.2 FaceState
- [ ] `FaceState`クラスの`_init_`メソッドの直後に`lerp_to(self, target: FaceState, t: float)`メソッドを追加する。
- [ ] `FaceState.lerp_to`メソッド内で`self.mouth_curve`、`self.brow_tilt`、`self.mouth_open`を`target`の対応する属性に向けて`t`の割合で補間するロジックを実装する。
- [ ] `FaceState.lerp_to`メソッド内で、左右の`EyeState`オブジェクトに対して`lerp_to`メソッドを呼び出す。
- [ ] `RobotFace.update`メソッドの既存の補間ロジックを削除し、`self.current_state.lerp_to(self.target_state, speed)`の呼び出しに置き換える。

---

## 2. MOODS を「不変な定義データ」に変更する

- [ ] `RobotFace.MOODS`の型ヒントを`dict[str, FaceState]`から`dict[str, dict]`に変更する。
- [ ] `RobotFace`クラス内に`@staticmethod`デコレータを持つ`make_face_state(defn: dict) -> FaceState`ファクトリ関数を追加する。
- [ ] `make_face_state`ファクトリ関数内で、入力`defn`辞書から`FaceState`オブジェクトとそれに含まれる`EyeState`オブジェクトを生成するロジックを実装する。
    *   `EyeState`は辞書内の`"left_eye"`や`"right_eye"`キーから生成する。
- [ ] `RobotFace.__init__`メソッド内で、`self.MOODS[self.mood]`を直接`FaceState`として使用する代わりに、`make_face_state(self.MOODS[self.mood])`を呼び出して`current_state`と`target_state`を初期化するように変更する。
- [ ] `RobotFace.set_target_mood()`メソッド内で、`self.MOODS[mood_name]`を直接`FaceState`として使用する代わりに、`make_face_state(self.MOODS[mood_name])`を呼び出して`target_state`を更新するように変更する。
- [ ] `MOODS`の定義が、将来的にJSONやYAMLファイルからロードされることを想定したシンプルな辞書構造になっていることをコードレビューで確認する。

---

## 3. RobotFace クラスの責務分割

### 3.1 描画責務の分離
- [ ] `RobotFace`クラスと同じファイルに`FaceRenderer`クラスを新しく定義する。
- [ ] `FaceRenderer`クラスの`_init_`メソッドに、描画に必要な`size`, `colors`, `layout`などの情報を引数として受け取るように定義する。
- [ ] `RobotFace`クラスから`_draw_eye`、`_draw_brows`、`_draw_mouth`、`_draw_outline`メソッドを`FaceRenderer`クラスに移動する。
- [ ] `FaceRenderer.draw(draw, state: FaceState, gaze_x: float)`形式に変更し、描画ロジックを`FaceRenderer`に移譲する。
    *   `FaceRenderer.draw`メソッド内で、移動した描画系メソッドを呼び出す。
    *   `FaceRenderer.draw`メソッドが`draw`オブジェクト（PIL.ImageDraw.Draw）を直接受け取るようにする。
- [ ] `RobotFace`クラスの`_init_`メソッド内で`FaceRenderer`のインスタンス（例: `self.renderer = FaceRenderer(...)`）を生成する。
- [ ] `RobotFace.draw`メソッドの内容を、`img = Image.new(...)`と`draw = ImageDraw.Draw(img)`を実行した後、`self.renderer.draw(draw, self.current_state, self.current_gaze_x)`を呼び出し、その後`ImageOps.pad`と`return final_img`を行うように変更する。

### 3.2 レイアウト定数の整理
- [ ] `RobotFace`クラスの定義前に`dataclasses`モジュールから`dataclass`をインポートする。
- [ ] `RobotFace`クラスと同じファイルに`@dataclass`デコレータを持つ`FaceLayout`クラスを新しく定義する。
- [ ] `FaceLayout` dataclassに`RobotFace.LAYOUT`辞書のキーに対応するフィールドを定義し、それぞれのフィールドに適切な型ヒントとデフォルト値を設定する。
- [ ] `FaceLayout` dataclassの各フィールド名が、数値の意味を明確に表すものになっていることをコードレビューで確認する。
- [ ] `RobotFace.__init__`メソッド内で`self.layout = FaceLayout(...)`のように`FaceLayout`のインスタンスを生成し、`RobotFace.LAYOUT`辞書の代わりに`self.layout`を使用するように変更する。
- [ ] `_draw_eye`、`_draw_brows`、`_draw_mouth`、`_draw_outline`などのメソッド内で`self.LAYOUT[...]`を使用している箇所を、`self.layout.field_name`のように`FaceLayout`の属性を参照するように変更する。
- [ ] `FaceRenderer`クラスにも`FaceLayout`のインスタンスが渡されるように調整し、`FaceRenderer`内の描画メソッドで`FaceLayout`の属性を使用するように変更する。

---

## 4. マジックナンバーの定数化

- [ ] `RobotFace._draw_eye`メソッド内の目が閉じている判定値`ry < 4`を`EYE_CLOSED_THRESHOLD = 4`というクラス定数またはモジュール定数として定義し、その定数を使用するように変更する。
- [ ] `RobotFace._draw_mouth`メソッド内の`mouth_open > 0.5`の閾値を`MOUTH_OPEN_THRESHOLD = 0.5`というクラス定数またはモジュール定数として定義し、その定数を使用するように変更する。
- [ ] `RobotFace._draw_bezier_curve`メソッド内のベジェ曲線の`steps=10`を`BEZIER_CURVE_STEPS = 10`というクラス定数またはモジュール定数として定義し、その定数を使用するように変更する。
- [ ] `RobotFaceApp.main`メソッド内の`time.sleep(0.1)`を`FRAME_INTERVAL = 0.1`というクラス定数またはモジュール定数として定義し、`time.sleep(FRAME_INTERVAL)`を使用するように変更する。
- [ ] 必要に応じて`FRAME_RATE = 10`（FPS）のような定数を定義し、`FRAME_INTERVAL = 1 / FRAME_RATE`のように計算で導出するように変更する。
- [ ] 上記のすべての定数名が、その意味を明確に表す「意味が分かる名前」になっていることをコードレビューで確認する。

---

## 5. RobotFaceApp のループ構造改善

- [ ] `RobotFaceApp.main`メソッド内の`while True`ループを`while self.running:`に変更する。
- [ ] `RobotFaceApp`クラスの`_init_`メソッド内で`self.running = True`を初期化する。
- [ ] `RobotFaceApp`クラスに`stop()`メソッドを追加し、`self.running = False`を設定するようにする。
- [ ] 1フレームの処理ロジックを`RobotFaceApp.tick(now: float)`メソッドとして分離する。`tick`メソッドは、表情変更、視線変更、`self.face.update()`、`self.face.draw()`、`self.output.show()`の処理を含むようにする。
- [ ] `RobotFaceApp.main`メソッド内で`self.running`フラグをチェックしながら`self.tick(time.time())`を呼び出し、`time.sleep(FRAME_INTERVAL)`を行うように変更する。
- [ ] `RobotFaceApp.tick`メソッドが、イベント駆動システム（例: 入力処理、ネットワーク通信）が将来的に統合されることを妨げない柔軟な設計になっていることをコードレビューで確認する。

---

## 完了条件 (最終確認)

- [ ] `RobotFace`クラスが状態管理（`current_state`, `target_state`, `current_gaze_x`, `target_gaze_x`の更新）に専念していることを、`RobotFace`クラスのコードをレビューして確認する。
- [ ] 描画コードが`FaceRenderer`クラスに完全に集約されており、`RobotFace`クラスから描画ロジックが削除されていることを、関連ファイルを確認して検証する。
- [ ] 表情定義（`MOODS`）が、`make_face_state`ファクトリ関数を通じて`FaceState`オブジェクトを生成する「データ」として扱える構造になっていることを、`MOODS`の定義と`make_face_state`の実装をレビューして確認する。
- [ ] 将来の拡張（新しい表情、アニメーション、出力形式など）が、既存のコードを大幅に「壊す」ことなく容易に行えるような堅牢な構造になっていることを、コードのモジュール性、凝集度、結合度を評価して確認する。
- [ ] すべての変更完了後、`mise run lint` を実行して、コードスタイルと型チェックに問題がないことを確認する。
- [ ] 必要に応じて、動作確認のための手動テスト（シミュレータでの描画確認など）を行う。
