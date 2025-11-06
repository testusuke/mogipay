# Requirements Document

## はじめに

MogiPayは、学園祭の模擬店運営を効率化するレジ/売上管理WebAppです。販売員が迅速に会計処理を行い、リアルタイムで売上・在庫状況を把握できるシステムを提供します。

### ビジネス価値
- **販売効率の向上**: 直感的なUIによる高速なレジ操作
- **正確な在庫管理**: 単品/セット販売の在庫連動による不整合の防止
- **売上の可視化**: 2日間の販売期間における進捗状況のリアルタイム表示
- **損益の把握**: 初期費用と売上の比較による経営判断の支援

---

## Requirements

### Requirement 1: 商品マスタ管理
**Objective:** As a 模擬店運営者, I want 商品情報を登録・管理できる機能, so that レジ販売と在庫管理の基礎データを準備できる

#### Acceptance Criteria

1. WHEN 運営者が新規商品登録画面を開く THEN MogiPayシステム SHALL 商品名、単価、販売価格、入荷個数の入力フォームを表示する
2. WHEN 運営者が商品情報を入力して登録ボタンを押す THEN MogiPayシステム SHALL 入力内容を検証し、商品マスタに保存する
3. WHEN 運営者が販売形態選択で「単品販売」を選ぶ THEN MogiPayシステム SHALL その商品を単品として登録する
4. WHEN 運営者が販売形態選択で「セット販売」を選ぶ THEN MogiPayシステム SHALL セット構成商品の選択UIを表示する
5. WHEN 運営者がセット構成商品を選択して登録する THEN MogiPayシステム SHALL セット商品と構成単品の関連を保存する
6. WHEN 運営者が商品一覧画面を開く THEN MogiPayシステム SHALL 登録済みの全商品情報をリスト表示する

---

### Requirement 2: 動的価格変更
**Objective:** As a 模擬店運営者, I want 販売途中で価格を変更できる機能, so that 市場状況に応じた柔軟な価格設定ができる

#### Acceptance Criteria

1. WHEN 運営者が商品編集画面で販売価格を変更して保存する THEN MogiPayシステム SHALL 新しい販売価格を有効化し、変更日時を記録する
2. WHEN 価格変更後に新規販売が行われる THEN MogiPayシステム SHALL 変更後の新価格で販売履歴を記録する
3. WHEN システムが過去の販売履歴を表示する THEN MogiPayシステム SHALL 各販売時点での実際の販売価格を表示する
4. IF 価格変更前の販売履歴が存在する THEN MogiPayシステム SHALL 過去の販売価格を変更せずに保持する

---

### Requirement 3: レジ販売処理
**Objective:** As a 販売員, I want +/-ボタンで商品と数量を入力して会計できる機能, so that 迅速かつ正確にお客様の会計処理ができる

#### Acceptance Criteria

1. WHEN 販売員がレジ画面を開く THEN MogiPayシステム SHALL 販売可能な全商品のリストを表示する
2. WHEN 販売員が商品を選択する THEN MogiPayシステム SHALL その商品を購入カートに追加し、数量を1にセットする
3. WHEN 販売員が+ボタンを押す THEN MogiPayシステム SHALL 該当商品の数量を1増やし、合計金額を再計算する
4. WHEN 販売員が-ボタンを押す AND 数量が2以上である THEN MogiPayシステム SHALL 該当商品の数量を1減らし、合計金額を再計算する
5. WHEN 販売員が-ボタンを押す AND 数量が1である THEN MogiPayシステム SHALL 該当商品を購入カートから削除する
6. WHILE 購入カートに商品が存在する THE MogiPayシステム SHALL 合計金額を大きく見やすく表示する（PayPay様式の大画面表示）
7. WHEN 販売員が精算ボタンを押す THEN MogiPayシステム SHALL 販売履歴を記録し、在庫を減算し、カートをクリアする
8. IF 精算時に在庫が不足している商品がある THEN MogiPayシステム SHALL エラーメッセージを表示し、精算を中断する

---

### Requirement 4: 販売履歴管理
**Objective:** As a 模擬店運営者, I want すべての販売取引が記録される機能, so that 売上分析と会計監査ができる

#### Acceptance Criteria

1. WHEN 精算処理が完了する THEN MogiPayシステム SHALL 販売日時、商品、数量、単価、販売価格、合計金額を販売履歴に記録する
2. WHEN 運営者が販売履歴画面を開く THEN MogiPayシステム SHALL すべての販売取引を時系列で表示する
3. WHERE 販売履歴画面 THE MogiPayシステム SHALL 各取引の詳細（商品明細、価格、数量）を表示できる
4. WHEN 運営者が日付でフィルタする THEN MogiPayシステム SHALL 指定日の販売履歴のみを表示する

---

### Requirement 5: 売上進捗管理
**Objective:** As a 模擬店運営者, I want 完売までの進捗状況をリアルタイムで確認できる機能, so that 販売戦略を調整できる

#### Acceptance Criteria

1. WHEN 運営者が売上管理画面を開く THEN MogiPayシステム SHALL 日別の売上金額を表示する
2. WHERE 売上管理画面 THE MogiPayシステム SHALL 各商品の完売達成率（%）を表示する
3. WHERE 売上管理画面 THE MogiPayシステム SHALL 各商品の残り販売個数を表示する
4. WHEN 新規販売が記録される THEN MogiPayシステム SHALL 売上進捗データをリアルタイムで更新する
5. WHERE 売上管理画面 THE MogiPayシステム SHALL 2日間の販売期間全体での進捗状況を表示する

---

### Requirement 6: 損益計算
**Objective:** As a 模擬店運営者, I want 初期費用と売上を比較できる機能, so that 収益状況を把握できる

#### Acceptance Criteria

1. WHEN システムが商品マスタを読み込む THEN MogiPayシステム SHALL 各商品の入荷個数×単価で初期費用を自動計算する
2. WHERE 損益管理画面 THE MogiPayシステム SHALL 総初期費用を表示する
3. WHERE 損益管理画面 THE MogiPayシステム SHALL 現在の総売上金額を表示する
4. WHERE 損益管理画面 THE MogiPayシステム SHALL 売上-初期費用の損益金額を表示する
5. WHEN 総売上が総初期費用を超える THEN MogiPayシステム SHALL 損益分岐点達成を視覚的に表示する

---

### Requirement 7: 在庫管理
**Objective:** As a 販売員, I want 単品とセットの在庫数をリアルタイムで確認できる機能, so that 在庫切れを把握して適切に対応できる

#### Acceptance Criteria

1. WHERE 在庫管理画面 THE MogiPayシステム SHALL 各単品商品の現在在庫数を表示する
2. WHERE 在庫管理画面 THE MogiPayシステム SHALL 各セット商品の現在在庫数を表示する
3. WHEN 単品商品が販売される THEN MogiPayシステム SHALL その商品の在庫数を販売数量分減算する
4. WHEN セット商品が販売される THEN MogiPayシステム SHALL セット在庫とセット構成単品の在庫を連動して減算する
5. IF セット構成単品のいずれかが在庫不足である THEN MogiPayシステム SHALL そのセット商品を販売不可として表示する
6. WHEN 在庫数が変動する THEN MogiPayシステム SHALL 在庫表示をリアルタイムで更新する
7. IF 商品在庫が0になる THEN MogiPayシステム SHALL その商品を視覚的に在庫切れと表示する

---

### Requirement 8: UI/UX
**Objective:** As a 販売員, I want 直感的で高速に操作できるインターフェース, so that お客様をスムーズに対応できる

#### Acceptance Criteria

1. WHERE すべての画面 THE MogiPayシステム SHALL タブレット/スマホでの操作に最適化されたレスポンシブデザインを提供する
2. WHEN 販売員が任意の操作を行う THEN MogiPayシステム SHALL 200ミリ秒以内にレスポンスを返す
3. WHERE レジ画面 THE MogiPayシステム SHALL 合計金額と重要情報を大きく見やすく表示する
4. WHERE すべての画面 THE MogiPayシステム SHALL 色分けとアイコンで状態を直感的に表現する
5. WHERE すべての画面 THE MogiPayシステム SHALL 操作手順が最小限で直感的な操作を提供する

---

### Requirement 9: データ整合性と信頼性
**Objective:** As a システム管理者, I want データの整合性と永続性が保証される機能, so that 正確な会計処理と監査対応ができる

#### Acceptance Criteria

1. WHEN 価格変更が行われる THEN MogiPayシステム SHALL 過去の販売履歴の価格データを保護する
2. WHEN セット販売で在庫が減算される THEN MogiPayシステム SHALL 単品在庫とセット在庫の整合性を保証する
3. WHEN 販売処理が実行される THEN MogiPayシステム SHALL トランザクション処理により販売記録と在庫減算の原子性を保証する
4. WHEN システム障害が発生する THEN MogiPayシステム SHALL すべての販売履歴データを永続化して保護する
5. WHERE すべての画面 THE MogiPayシステム SHALL 誤操作を防止する確認ダイアログを適切に表示する
6. WHEN 複数の販売員が同時にシステムを操作する THEN MogiPayシステム SHALL データの一貫性を維持する
