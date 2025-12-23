# `robot_face_animation.py` リファクタリングタスク (Tasks03.md)

`Plan03.md`で定義されたリファクタリング計画を、以下の具体的な作業手順に分解します。

---

### 計画1: アニメーションロジックのカプセル化

- [x] **`RobotFace`クラスの修正:**
    - [x] `__init__`メソッドに、アニメーションのタイミングを管理するインスタンス変数（例: `_next_mood_time`, `_next_gaze_time`）を追加する。
- [x] **`RobotFace`クラスへのロジック移管:**
    - [x] `animate_step()`メソッドを新規作成する。
    - [x] `RobotFaceApp`のメインループから、表情をランダムに変更するロジックを`animate_step()`内に移植する。
    - [x] 同様に、視線をランダムに変更するロジックも`animate_step()`内に移植する。
- [x] **`RobotFaceApp`クラスの修正:**
    - [x] `main`メソッドのメインループから、表情と視線を直接変更しているロジックを削除する。
    - [x] 削除した箇所に`self.face.animate_step()`の呼び出しを追加し、ループを簡素化する。

### 計画2: 出力クラスの責務分離（抽象化）

- [x] **`DisplayOutput`の抽象化:**
    - [x] `abc`モジュールから`ABC`と`abstractmethod`をインポートする。
    - [x] `DisplayOutput`のクラス定義を`class DisplayOutput(ABC):`に変更する。
    - [x] `__init__`からハードウェア検出ロジックを削除する。
    - [x] `show`メソッドと`close`メソッドに`@abstractmethod`デコレータを付与し、実装を`pass`にする。
- [x] **具象クラスの作成:**
    - [x] `LcdOutput(DisplayOutput)`クラスを新規作成し、`ST7789V`に依存する初期化、`show`、`close`処理を実装する。
    - [x] `PreviewOutput(DisplayOutput)`クラスを新規作成し、`OpenCV`に依存する`show`、`close`処理を実装する。
- [x] **ファクトリの作成と適用:**
    - [x] ハードウェアを判別して適切な`DisplayOutput`サブクラスのインスタンスを返す`create_output_device()`ファクトリ関数を新規作成する。
    - [x] `main`関数でこのファクトリ関数を呼び出し、生成されたインスタンスを`RobotFaceApp`に渡すように変更する。
    - [x] `RobotFaceApp`の`__init__`が、インスタンス化された`DisplayOutput`オブジェクトを引数として受け取るように修正する。

### 計画3: グローバル定数のカプセル化

- [x] **`FACE_BG_COLOR`の移動:**
    - [x] グローバルスコープから`FACE_BG_COLOR`を削除する。
    - [x] `RobotFace`クラスのクラス変数として`FACE_BG_COLOR`を定義する。
    - [x] `RobotFace.draw()`メソッド内で、`self.FACE_BG_COLOR`を参照するように修正する。
- [x] **画面サイズ関連定数の移動:**
    - [x] グローバルスコープから`SCREEN_WIDTH`, `SCREEN_HEIGHT`, `BG_COLOR`を削除する。
    - [x] これらの値を`RobotFaceApp`のコンストラクタで受け取れるように引数を追加する。
    - [x] `RobotFace.draw()`メソッドが、最終的な描画サイズ（`width`, `height`, `bg_color`）を引数として受け取れるようにシグネチャを修正する。
    - [x] `RobotFaceApp.main()`内で`self.face.draw()`を呼び出す際に、`RobotFaceApp`が保持している画面サイズ関連の値を渡すように修正する。
    - [x] `main`関数で`RobotFaceApp`をインスタンス化する際に、これまで定数として定義されていた値を渡す。

### 品質確認

- [x] すべての変更後、`mise run lint`を実行して、コードスタイルと型チェックに問題がないことを確認する。

---