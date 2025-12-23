# `robot_face_animation.py` の視線状態分離リファクタリング計画 (Plan04.md)

## 1. 目的

`samples/robot_face_animation.py`の`RobotFace`クラスにおいて、「表情」の状態と「視線」の状態を分離する。これにより、関心の分離の原則を徹底し、コードの可読性、保守性、および状態管理の明瞭性を向上させる。

## 2. 背景

現状の実装では、視線の水平位置を管理する`gaze_x`は、表情の状態を定義する`FaceState`データクラスの一部として含まれている。しかし、視線は表情とは独立して制御されるべき要素である。

この設計により、`set_target_mood`メソッド内で表情を切り替える際に、一度視線の目標値(`gaze_x`)を退避させ、表情の状態を更新した後に再設定するという、回りくどい実装が必要になっている。これは、表情と視線の関心が完全に分離できていないことを示している。

このリファクタリングでは、`gaze_x`を`FaceState`から独立させ、`RobotFace`クラスが直接管理する状態変数に変更する。

## 3. 改善計画

### 計画1: `FaceState`から`gaze_x`を分離

*   `FaceState`データクラスの定義から`gaze_x: float = 0`の行を削除する。

### 計画2: `RobotFace`クラスでの視線状態の直接管理

*   `RobotFace`クラスの`__init__`メソッドで、視線の現在値と目標値を管理する新しいインスタンス変数を追加する。
    *   `self.current_gaze_x: float = 0.0`
    *   `self.target_gaze_x: float = 0.0`
*   `MOODS`辞書内の`FaceState`定義には、`gaze_x`に関する記述は元々ほとんどないため、修正は不要。

### 計画3: 関連メソッドの修正

*   **`set_target_mood`メソッドの簡素化:**
    *   表情を切り替える際に視線を維持するための特別な処理（`gaze_x`の退避と再設定）を削除する。このメソッドは表情の状態（`FaceState`）の更新にのみ責任を持つようになる。
*   **`set_gaze`メソッドの修正:**
    *   視線の目標値を、`self.target_state.gaze_x = x`ではなく、新しく作成した`self.target_gaze_x = x`に設定するように変更する。
*   **`update`メソッドの修正:**
    *   `gaze_x`の線形補間処理を、`current_state`を介さず、`self.current_gaze_x`と`self.target_gaze_x`の間で行うように変更する。
*   **`draw`メソッドの修正:**
    *   描画処理（主に`_draw_eye`メソッドへの引数）で、`self.current_state.gaze_x`ではなく、`self.current_gaze_x`を参照するように変更する。

---

この計画を実行することで、`set_target_mood`メソッドが簡潔になり、表情と視線の状態が明確に分離され、コード全体の理解が容易になることが期待されます。