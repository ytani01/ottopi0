# `robot_face_animation.py` の目に関するパラメータの改善計画

## 1. 現状の課題

現在の`robot_face_animation.py`では、目に関する以下のパラメータが`FaceState`クラスに直接含まれており、直感的でなく分かりにくい構造になっています。

*   `eye_height`: 目の縦半径
*   `eye_tilt`: 眉毛の角度
*   `wink_left`, `wink_right`: 目の開き具合を`0.1`～`1.0`のスケールで表現
*   `gaze_x`: 視線の水平位置
*   `eye_curve`: 目が閉じているときの曲がり具合

`wink`がスケール値であったり、眉毛に関する`eye_tilt`が同列に含まれていたりするため、パラメータの役割を理解しにくい状態です。

## 2. 改善計画

この問題を解決するため、目に関するパラメータをよりオブジェクト指向で直感的な構造にリファクタリングします。

### 計画の詳細

#### (1) `EyeState`データクラスの新規作成

目一つ分の状態を管理するための`EyeState`クラスを新たに作成します。

```python
@dataclass
class EyeState:
    openness: float = 1.0  # 目の開き具合 (0.0: 閉, 1.0: 開)
    size: float = 8.0      # 目の大きさの基準となる半径
    curve: float = 0.0     # 閉じたときの目の曲がり具合 (-1.0: 谷, 0.0: 直線, 1.0: 山)
```

#### (2) `FaceState`クラスの修正

`FaceState`クラスを修正し、`EyeState`を利用するように変更します。

*   **削除する属性:**
    *   `eye_height`
    *   `wink_left`
    *   `wink_right`
    *   `eye_curve`
*   **リネームする属性:**
    *   `eye_tilt` -> `brow_tilt` （眉毛のパラメータであることを明確化）
*   **追加する属性:**
    *   `left_eye: EyeState`
    *   `right_eye: EyeState`

これにより、`FaceState`は顔全体のパーツ（両目、眉、口、視線）を管理する役割に集中します。

#### (3) `MOODS`定義の更新

`RobotFace`クラスで定義されている表情の辞書`MOODS`を、新しい`EyeState`と`FaceState`の構造に合わせて更新します。

**例 (`wink`の場合):**
```python
"wink": FaceState(
    mouth_curve=15,
    brow_tilt=0,
    left_eye=EyeState(openness=1.0, size=8.0, curve=1.0),
    right_eye=EyeState(openness=0.1, size=8.0, curve=1.0), # 右目を閉じる
),
```

#### (4) 描画・更新ロジックの修正

*   **`_draw_eye`メソッドの修正:**
    *   引数として`eye_state: EyeState`を受け取るようにシグネチャを変更します。
    *   メソッド内部では、`eye_state.openness`, `eye_state.size`, `eye_state.curve` を使って目の描画ロジックを組み立てます。
*   **`update`メソッドの修正:**
    *   表情が滑らかに変化するよう、`left_eye`と`right_eye`の各属性（`openness`, `size`, `curve`）を線形補間する処理を追加します。
*   **`copy`メソッドの修正:**
    *   `FaceState`および`EyeState`の`copy`メソッドが、すべての属性を正しくコピーするように修正します。

## 3. 期待される効果

このリファクタリングにより、以下の効果が期待できます。

*   **可読性の向上:** 各パラメータの役割がクラス構造から明確になり、コードが読みやすくなります。
*   **メンテナンス性の向上:** 目に関するロジックが`EyeState`に集約されるため、修正や機能追加が容易になります。
*   **直感的な操作:** `openness`が`0.0`～`1.0`になるなど、パラメータの意味がより直感的になり、新しい表情の定義がしやすくなります。
