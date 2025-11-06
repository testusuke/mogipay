# 実装計画

- [ ] 1. 開発環境のセットアップ
- [x] 1.1 monorepo 基本構造の作成

  - プロジェクトルートに frontend/と backend/ディレクトリを作成
  - ルートに.gitignore を作成(node_modules, .env, **pycache**等)
  - README を作成(プロジェクト概要と開発環境構築手順)
  - _Requirements: 全要件の基盤_

- [x] 1.2 バックエンドプロジェクトの作成

  - backend/ディレクトリで uv init を実行
  - uv python pin 3.12 で Python 3.12 を指定
  - uv add コマンドで依存関係を追加(pip install は使わない)
  - uv add fastapi uvicorn[standard] sqlalchemy psycopg2-binary alembic
  - uv add --dev pytest pytest-asyncio httpx でテスト依存関係を追加
  - backend/app/ディレクトリ構造を作成(api, services, repositories, models)
  - _Requirements: 9.1-9.6_

- [x] 1.3 フロントエンドプロジェクトの作成

  - npx shadcn@latest init で Next.js 15 プロジェクトを作成
  - TypeScript、App Router、Tailwind CSS を有効化
  - shadcn/ui を導入
  - 必要な shadcn/ui コンポーネントをインストール(button, card, form, input, label, badge, dialog, table)
  - _Requirements: 8.1-8.5_

- [x] 1.4 開発用 Docker Compose(PostgreSQL 16 のみ)

  - docker-compose.dev.yml を作成
  - PostgreSQL 16 サービスを定義(18 から 16 にダウングレード)
  - データベース名、ユーザー、パスワードを環境変数で設定
  - ポート 5432 をホストに公開
  - ボリュームマウントでデータ永続化
  - _Requirements: 9.1-9.6_

- [x] 1.5 Makefile で開発コマンド統一

  - db-up コマンド: docker compose -f docker-compose.dev.yml up -d
  - db-down コマンド: docker compose -f docker-compose.dev.yml down
  - backend-dev コマンド: cd backend && uv run uvicorn app.main:app --reload
  - frontend-dev コマンド: cd frontend && npm run dev
  - test コマンド: cd backend && uv run pytest
  - migrate コマンド: データベースマイグレーション実行
  - setup コマンド: db-up + migrate + 依存関係インストール
  - clean コマンド: Docker ボリューム削除、キャッシュクリア
  - _Requirements: 全要件の開発効率化_

- [x] 1.6 データベース接続設定とマイグレーション準備

  - backend/.env ファイルのテンプレート作成
  - DATABASE_URL 環境変数の設定
  - SQLAlchemy のデータベース接続設定
  - Alembic でマイグレーションツールをセットアップ
  - alembic init でマイグレーション環境を初期化
  - _Requirements: 9.1-9.6_

- [x] 1.7 PostgreSQL スキーマのマイグレーション実装

  - SQLAlchemy モデルを作成(Product, SetItem, SalesHistory, SaleItem)
  - Alembic の自動生成機能でマイグレーションファイルを生成
  - products テーブルの定義(商品マスタ)
  - set_items テーブルの定義(セット構成)
  - sales_history テーブルの定義(販売履歴)
  - sale_items テーブルの定義(販売明細)
  - インデックスと制約の定義
  - alembic upgrade でマイグレーション実行
  - _Requirements: 1.1-1.6, 7.1-7.7, 9.1-9.6_

- [x] 2. バックエンド - Repository 層の実装(TDD)
- [x] 2.1 ProductRepository の実装(TDD)

  - 商品の作成、取得、更新、削除機能を実装
  - 在庫減算機能を実装(同時実行制御を含む)
  - 在庫が負にならない制約のテストを先に記述
  - 同時販売での在庫不整合防止のテスト
  - セット商品削除時のカスケード削除テスト
  - InsufficientStockError 例外の実装
  - SELECT FOR UPDATE による行ロック実装
  - testcontainers を使用した統合テスト（9 テスト全てパス）
  - _Requirements: 1.1-1.6, 7.3-7.4_

- [x] 2.2 SetItemRepository の実装(TDD)

  - セット商品と構成単品の関連を管理する機能
  - セット構成の一括作成機能
  - セット商品 ID での構成取得機能
  - セット削除時の構成自動削除のテスト
  - ユニーク制約の検証テスト
  - 一括削除機能の実装
  - testcontainers を使用した統合テスト（6 テスト全てパス）
  - _Requirements: 1.4-1.5, 7.4-7.5_

- [x] 2.3 SalesHistoryRepository の実装(TDD)

  - 販売トランザクションの記録機能
  - 販売明細の保存(価格スナップショット)
  - 日付範囲での販売履歴取得機能
  - 総売上と日別売上の集計機能
  - 価格変更後も過去データが不変であることのテスト
  - カスケード削除の検証テスト
  - testcontainers を使用した統合テスト（7 テスト全てパス）
  - _Requirements: 2.1-2.4, 4.1-4.4, 9.1_

- [x] 3. バックエンド - Service 層の実装(TDD)
- [x] 3.1 InventoryService の実装(TDD)

  - 単品商品の在庫状況取得機能
  - セット商品の在庫計算機能(構成単品の在庫から算出)
  - 精算前の在庫可用性チェック機能
  - セット構成単品が不足している場合の検出
  - リアルタイム在庫状況の取得機能
  - モックを使用した単体テスト（9 テスト全てパス）
  - _Requirements: 7.1-7.7_

- [x] 3.2 SalesService の実装(TDD)

  - レジ精算処理のビジネスロジック
  - 在庫チェックと販売記録と在庫減算の統合処理
  - セット商品販売時の構成単品在庫連動
  - トランザクション処理で原子性を保証
  - 在庫不足時のエラーハンドリング
  - モックを使用した単体テスト（7 テスト全てパス）
  - _Requirements: 3.1-3.8, 7.3-7.5, 9.2-9.3_

- [x] 3.3 ProductService の実装(TDD)

  - 商品の登録、編集、削除機能
  - 単品商品とセット商品の作成処理の分岐
  - 動的な販売価格変更機能
  - 価格変更時に過去の販売履歴を保護
  - セット構成の検証とエラーハンドリング
  - モックを使用した単体テスト（11 テスト全てパス）
  - _Requirements: 1.1-1.6, 2.1-2.4_

- [x] 3.4 SalesHistoryService の実装(TDD)

  - 販売履歴の取得とフィルタリング機能
  - 日付範囲での販売記録の抽出
  - 時系列での販売履歴の並び替え
  - 販売明細の詳細表示機能
  - モックを使用した単体テスト（7 テスト全てパス）
  - _Requirements: 4.1-4.4_

- [x] 3.5 SalesAnalyticsService の実装(TDD)

  - 総売上金額の計算機能
  - 日別売上金額の集計機能
  - 商品別の完売達成率の計算
  - 残り販売個数の算出
  - 2 日間の販売期間全体での進捗状況の計算
  - モックを使用した単体テスト（6 テスト全てパス）
  - _Requirements: 5.1-5.5_

- [x] 3.6 FinancialService の実装(TDD)

  - 総初期費用の自動計算(入荷個数 × 単価)
  - 総売上金額の集計
  - 損益金額の計算(売上-初期費用)
  - 損益分岐点達成の判定
  - 利益率の計算
  - モックを使用した単体テスト（7 テスト全てパス）
  - _Requirements: 6.1-6.5_

- [x] 4. バックエンド - API 層の実装(TDD)
- [x] 4.1 ProductController の実装(TDD)

  - 商品登録 API エンドポイントの実装
  - 商品一覧取得 API の実装
  - 商品詳細取得 API の実装
  - 商品編集 API の実装
  - 価格変更専用 API の実装
  - 商品削除 API の実装
  - HTTP レスポンスとエラーハンドリングのテスト(13 テスト全てパス)
  - _Requirements: 1.1-1.6, 2.1-2.4_

- [x] 4.2 SalesController の実装(TDD)

  - レジ精算 API エンドポイントの実装
  - 販売履歴取得 API の実装
  - 売上サマリ取得 API の実装
  - バリデーションエラーの HTTP レスポンステスト
  - 在庫不足エラーの HTTP レスポンステスト
  - HTTP レスポンスとエラーハンドリングのテスト(9 テスト全てパス)
  - _Requirements: 3.1-3.8, 4.1-4.4, 5.1-5.5_

- [x] 4.3 InventoryController の実装(TDD)

  - 在庫状況取得 API エンドポイントの実装
  - 単品とセットの在庫数を含むレスポンス
  - 在庫切れ商品の識別フラグを含む
  - HTTP レスポンスのテスト(4 テスト全てパス)
  - _Requirements: 7.1-7.7_

- [x] 4.4 FinancialController の実装(TDD)

  - 損益サマリ取得 API エンドポイントの実装
  - 初期費用、売上、損益、損益分岐点達成状態のレスポンス
  - HTTP レスポンスのテスト(5 テスト全てパス)
  - _Requirements: 6.1-6.5_

- [x] 5. バックエンド統合テスト
- [x] 5.1 販売フロー全体の統合テスト

  - 商品登録から精算、在庫減算までの一連の流れをテスト
  - 実際の PostgreSQL データベースを使用
  - 販売履歴の記録を検証
  - 在庫数の変動を検証
  - トランザクションロールバックの動作確認
  - testcontainers を使用した統合テスト（5 テスト全てパス - TDD GREEN フェーズ完了）
  - _Requirements: 3.1-3.8, 7.3-7.4, 9.2-9.3_

- [x] 5.2 セット商品在庫連動の統合テスト

  - セット商品販売時の構成単品在庫減算を検証
  - セット在庫の動的計算を検証
  - 構成単品不足時のエラーハンドリング検証
  - トランザクション処理の整合性を確認
  - testcontainers を使用した統合テスト（5 テスト全てパス - TDD GREEN フェーズ完了）
  - _Requirements: 7.4-7.6, 9.2_

- [x] 5.3 価格変更の不変性テスト

  - 価格変更前の販売記録を作成
  - 価格を変更
  - 価格変更後の販売記録を作成
  - 過去の販売履歴の価格が変更されていないことを確認
  - 新規販売が新価格で記録されることを確認
  - testcontainers を使用した統合テスト（5 テスト全てパス - TDD GREEN フェーズ完了）
  - _Requirements: 2.1-2.4, 9.1_

- [ ] 6. フロントエンド実装
- [x] 6.1 Next.js プロジェクトのセットアップと shadcn/ui 導入

  - Next.js 15 の App Router でプロジェクトを初期化済み
  - TypeScript 設定済み
  - shadcn/ui コンポーネントライブラリの導入済み
  - 基本的なレイアウトとナビゲーション構造の作成
  - _Requirements: 8.1-8.5_

- [x] 6.2 API Client の実装

  - バックエンド API との通信を行うクライアント機能を実装(TDD)
  - クライアントサイドフェッチの実装(fetch API + retry logic)
  - エラーハンドリングとリトライロジック(exponential backoff)
  - レスポンスの型定義(TypeScript) - types.ts, errors.ts 完成
  - lib/api/client.ts - ApiClient クラス実装完了
  - lib/api/index.ts - エクスポート統一
  - ESLint チェック合格
  - _Requirements: 全要件(API との連携基盤)_

- [x] 6.3 POSScreen(レジ画面)の実装

  - 商品選択 UI の実装
  - +/-ボタンでの数量入力機能
  - 購入カートの表示と管理
  - 合計金額の大画面表示(PayPay 様式)
  - 精算ボタンと精算処理の実装
  - 在庫不足エラーの表示
  - レスポンシブデザイン(タブレット/スマホ対応)
  - 商品のソート表示機能(セット商品→単品商品、それぞれ名前順)
  - フロントエンド在庫バリデーションの実装
    - 仮想在庫管理システム(availableStock)の実装
    - セット商品在庫の動的計算機能(calculateSetStock)
    - カート操作時の在庫チェックと在庫更新
    - 単品追加時のセット商品在庫連動
    - 詳細な在庫不足エラーメッセージ
  - frontend/app/pos/page.tsx 実装完了
  - ESLint チェック合格
  - TypeScript 型チェック合格
  - _Requirements: 3.1-3.8, 7.3-7.5, 8.1-8.5_

- [x] 6.4 ProductManagement(商品管理)の実装

  - 商品登録フォームの実装
  - 単品/セット商品の選択 UI
  - セット構成商品の選択機能
  - 商品一覧表示とフィルタリング
  - 商品編集と削除機能
  - 価格変更機能
  - バリデーションとエラー表示
  - レスポンシブデザイン対応
    - デスクトップ（md以上）: テーブル表示
    - モバイル（md未満）: Card表示で見やすく改善
  - frontend/app/products/page.tsx 実装完了
  - Table, Select コンポーネント追加
  - ナビゲーションメニューに商品管理リンク追加
  - ESLint チェック合格
  - TypeScript 型チェック合格
  - _Requirements: 1.1-1.6, 2.1-2.4, 8.1, 8.3_

- [x] 6.5 SalesDashboard(売上ダッシュボード)の実装

  - 売上進捗の表示(総売上、日別売上)
  - 商品別完売達成率の表示
  - 在庫状況の表示(残り個数、在庫切れ表示)
  - 損益計算の表示(初期費用、売上、損益)
  - 損益分岐点達成の視覚的表示
  - グラフとチャートの実装(Recharts使用)
  - レスポンシブデザイン
  - 5秒間隔のポーリングによるリアルタイム更新機能
  - frontend/app/dashboard/page.tsx 実装完了
  - ESLintチェック合格
  - TypeScript型チェック合格
  - _Requirements: 5.1-5.5, 6.1-6.5, 7.1-7.2, 7.6-7.7_

- [ ] 7. システム統合と最終調整
- [ ] 7.1 フロントエンド-バックエンド統合

  - API エンドポイント URL の設定
  - CORS 設定の確認
  - 環境変数の管理
  - エンドツーエンドの動作確認
  - _Requirements: 全要件_

- [ ] 7.2 ポーリングメカニズムの実装

  - 5 秒間隔での API ポーリング機能
  - ダッシュボード画面でのリアルタイム更新
  - 在庫状況の自動更新
  - 売上進捗の自動更新
  - _Requirements: 5.4-5.5, 7.6_

- [ ] 7.3 エラーハンドリングとユーザーフィードバック

  - バリデーションエラーの表示
  - 在庫不足エラーのモーダル表示
  - システムエラーのトースト通知
  - 確認ダイアログの実装
  - ローディング状態の表示
  - _Requirements: 8.5, 9.5_

- [ ] 7.4 レスポンシブデザインの検証
  - タブレットサイズでの表示確認
  - スマホサイズでの表示確認
  - タッチ操作の検証
  - 重要情報の視認性確認
  - レイアウト崩れの修正
  - _Requirements: 8.1, 8.3, 8.4_
