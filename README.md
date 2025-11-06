# MogiPay - 学園祭模擬店レジ/売上管理システム

学園祭の模擬店で利用されるレジ/売上管理の WebApp です。UI/UX どちらにおいても優れたモダンなアプリケーションです。

## 技術スタック

### 全体構成
- **Monorepo**: frontend/ と backend/ に分離
- **開発管理**: Makefile でコマンド統一
- **Node.js**: v22
- **パッケージマネージャ**: npm (frontend), uv (backend)

### フロントエンド
- **Framework**: Next.js 14 (App Router)
- **言語**: TypeScript
- **UI Library**: shadcn/ui
- **スタイリング**: Tailwind CSS

### バックエンド
- **Framework**: FastAPI
- **言語**: Python 3.12
- **パッケージ管理**: uv
- **アーキテクチャ**: Layered Architecture
- **データベース**: PostgreSQL 18
- **ORM**: SQLAlchemy
- **マイグレーション**: Alembic

### インフラ
- **コンテナ**: Docker, Docker Compose
- **データベース**: PostgreSQL 18

## 開発手順

### 初回セットアップ

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd mogipay

# 2. 初回セットアップコマンド実行
make setup
# → PostgreSQL起動 + マイグレーション実行 + 依存関係インストール
```

### 開発サーバーの起動

開発時は 3 つのターミナルを開いて実行してください:

```bash
# ターミナル1: PostgreSQL起動
make db-up

# ターミナル2: バックエンド起動
make backend-dev
# → http://localhost:8000 でFastAPIが起動
# → http://localhost:8000/docs でOpenAPI(Swagger)が確認可能

# ターミナル3: フロントエンド起動
make frontend-dev
# → http://localhost:3000 でNext.jsが起動
```

### データベース関連

#### マイグレーション

```bash
# マイグレーション実行
make migrate

# 新しいマイグレーションファイル作成
cd backend
uv run alembic revision --autogenerate -m "description"

# マイグレーション履歴確認
cd backend
uv run alembic history

# 特定バージョンにロールバック
cd backend
uv run alembic downgrade <revision>
```

#### データベースリセット

```bash
# データベースを完全にリセット
make db-down
make clean
make setup
```

### テスト実行

```bash
# バックエンドのテストを実行
make test

# カバレッジ付きテスト
cd backend
uv run pytest --cov=app --cov-report=term-missing

# 特定のテストのみ実行
cd backend
uv run pytest tests/services/test_sales_service.py -v
```

### パッケージ管理

#### バックエンド (uv)

```bash
cd backend

# 本番依存関係を追加
uv add <package-name>

# 開発依存関係を追加
uv add --dev <package-name>

# 依存関係の同期(pip installは使わない)
uv sync

# 依存関係の一覧表示
uv pip list
```

#### フロントエンド (npm)

```bash
cd frontend

# パッケージ追加
npm install <package-name>

# shadcn/uiコンポーネント追加
npx shadcn@latest add <component-name>
# 例: npx shadcn@latest add button card form
```

## Git 操作

### コミット手順

```bash
# 変更を確認
git status
git diff

# ステージング
git add .

# コミット (日本語メッセージ)
git commit -m "feat: レジ画面のUI実装"
git commit -m "fix: 在庫計算ロジックの修正"
git commit -m "test: SalesServiceのテスト追加"

# プッシュ
git push origin <branch-name>
```

### ブランチ戦略

```bash
# 新機能開発
git checkout -b feature/pos-screen
git checkout -b feature/product-management

# バグ修正
git checkout -b fix/inventory-calculation

# リファクタリング
git checkout -b refactor/service-layer
```

## 開発終了時

```bash
# PostgreSQL停止
make db-down

# 全サービス停止 (Ctrl+C で各サーバーを停止)
```

## トラブルシューティング

### ポートが既に使用されている

```bash
# PostgreSQL (5432)
lsof -ti:5432 | xargs kill -9

# バックエンド (8000)
lsof -ti:8000 | xargs kill -9

# フロントエンド (3000)
lsof -ti:3000 | xargs kill -9
```

### データベース接続エラー

```bash
# PostgreSQLの状態確認
docker compose -f docker-compose.dev.yml ps

# ログ確認
docker compose -f docker-compose.dev.yml logs postgres

# コンテナ再起動
make db-down
make db-up
```

### 依存関係のトラブル

```bash
# バックエンド
cd backend
rm -rf .venv
uv sync

# フロントエンド
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 便利な Make コマンド一覧

```bash
make setup          # 初回セットアップ
make db-up          # PostgreSQL起動
make db-down        # PostgreSQL停止
make backend-dev    # バックエンド開発サーバー起動
make frontend-dev   # フロントエンド開発サーバー起動
make test           # テスト実行
make migrate        # マイグレーション実行
make clean          # クリーンアップ(Dockerボリューム削除)
```

## ライセンス

MIT License
