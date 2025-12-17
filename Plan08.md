# Robot Face Animation リファクタリング チェックリスト

このドキュメントは、`robot_face_animation.py` に対して提案された
リファクタリング内容を **実作業向けのチェックリスト** として整理したものです。

---

## 1. 状態クラスに補間（lerp）ロジックを集約する

### EyeState
- [ ] `lerp_to(self, target: EyeState, t: float)` メソッドを追加
- [ ] `openness / size / curve` の補間を EyeState 側に移動
- [ ] RobotFace.update から EyeState の直接補間を削除

### FaceState
- [ ] `lerp_to(self, target: FaceState, t: float)` メソッドを追加
- [ ] `mouth_curve / brow_tilt / mouth_open` を補間
- [ ] 左右の EyeState に対して `lerp_to` を呼び出す
- [ ] RobotFace.update を以下の形に簡略化
  - `self.current_state.lerp_to(self.target_state, speed)`

---

## 2. MOODS を「不変な定義データ」に変更する

- [ ] `MOODS: dict[str, FaceState]` を廃止
- [ ] `MOODS: dict[str, dict]` として定義
- [ ] FaceState を生成するファクトリ関数を追加
  - [ ] `make_face_state(defn: dict) -> FaceState`
- [ ] `set_target_mood()` 内でファクトリを使用
- [ ] 将来の JSON/YAML 外部定義を想定した構造にする

---

## 3. RobotFace クラスの責務分割

### 描画責務の分離
- [ ] `FaceRenderer` クラスを新設
- [ ] 描画系メソッドを RobotFace から移動
  - [ ] `_draw_eye`
  - [ ] `_draw_brows`
  - [ ] `_draw_mouth`
  - [ ] `_draw_outline`
- [ ] `FaceRenderer.draw(state, gaze_x, size, colors, layout)` 形式に整理

### レイアウト定数の整理
- [ ] `FaceLayout` dataclass を作成
- [ ] `LAYOUT` 辞書を dataclass に置き換え
- [ ] 数値の意味が分かる名前を付ける

---

## 4. マジックナンバーの定数化

- [ ] 目が閉じている判定値 `ry < 4` を定数化
- [ ] `mouth_open > 0.5` の閾値を定数化
- [ ] ベジェ曲線の `steps=10` を定数化
- [ ] `time.sleep(0.1)` を FPS / INTERVAL 定数に変更
- [ ] すべての定数に「意味が分かる名前」を付与

---

## 5. RobotFaceApp のループ構造改善

- [ ] `while True` を廃止
- [ ] `self.running` フラグを導入
- [ ] 1フレーム処理を `tick(now: float)` に分離
- [ ] 将来的なイベント駆動（入力・通信）を考慮

---

## 6. DummyOutput の追加

- [ ] `DummyOutput(DisplayOutput)` を追加
- [ ] `show()` / `close()` は no-op
- [ ] `create_output_device()` の最終フォールバックに使用
- [ ] CI / SSH / 描画不要環境でも実行可能にする

---

## 7. テスト容易性の向上（余力があれば）

- [ ] FaceState / EyeState の補間テスト追加
- [ ] Renderer を PIL Image 単位でテスト可能にする
- [ ] 乱数（mood / gaze）を注入可能にする

---

## 8. 将来拡張のための下準備（Optional）

- [ ] 表情遷移シナリオ（スクリプト）対応
- [ ] 瞬き・呼吸などの自動アニメーション
- [ ] SVG / ベクタ出力への対応
- [ ] 表情定義の外部ファイル化

---

## 完了条件

- RobotFace が「状態管理」に専念している
- 描画コードが Renderer に集約されている
- 表情定義がデータとして扱える
- 将来の拡張で「壊す必要がない」構造になっている
