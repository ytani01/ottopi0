# `gaze_x` 分離リファクタリングタスク (Tasks04.md)

`Plan04.md`で定義されたリファクタリング計画を、以下の具体的な作業手順に分解します。

---

### 1. `FaceState` クラスの修正

- [x] `FaceState` データクラスの定義から `gaze_x: float = 0` の行を削除する。
- [x] `FaceState` の `copy` メソッドから `self.gaze_x` のコピー処理を削除する。

### 2. `RobotFace` クラスの修正

- [x] **`__init__` メソッド:**
    - [x] `gaze_x` を管理するためのインスタンス変数 `self.current_gaze_x: float = 0.0` と `self.target_gaze_x: float = 0.0` を追加する。
- [x] **`update` メソッド:**
    - [x] `gaze_x` の線形補間処理を、`self.current_gaze_x` と `self.target_gaze_x` を使うように修正する。
- [x] **`set_target_mood` メソッド:**
    - [x] `gaze_x` の値を一時的に保存・復元している処理を削除し、メソッドを簡素化する。
- [x] **`set_gaze` メソッド:**
    - [x] `self.target_gaze_x` に値を設定するように修正する。
- [x] **`draw` メソッド:**
    - [x] `_draw_eye` メソッドに渡す `gaze_x` の値を、`self.current_gaze_x` から取得するように修正する。

### 3. 品質確認

- [x] すべての変更後、`mise run lint` を実行して、コードスタイルと型チェックに問題がないことを確認する。