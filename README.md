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

## 環境変数設定

### バックエンド環境変数

バックエンドの環境変数は `backend/.env` ファイルで管理されます。

```bash
# backend/.env.example をコピーして .env を作成
cd backend
cp .env.example .env
```

| 変数名 | 説明 | デフォルト値 | 必須 |
|--------|------|--------------|------|
| `DATABASE_URL` | PostgreSQL接続URL | `postgresql://mogipay_user:mogipay_password@localhost:5432/mogipay_dev` | ✅ |
| `POSTGRES_DB` | データベース名 | `mogipay_dev` | ✅ |
| `POSTGRES_USER` | データベースユーザー | `mogipay_user` | ✅ |
| `POSTGRES_PASSWORD` | データベースパスワード | `mogipay_password` | ✅ |
| `POSTGRES_PORT` | PostgreSQLポート | `5432` | ✅ |
| `ENVIRONMENT` | アプリケーション環境 | `development` | ⚠️ |
| `DEBUG` | デバッグモード（SQL出力） | `True` | ⚠️ |

**注意事項:**
- `DATABASE_URL` は他のPostgreSQL環境変数から自動構成されます
- `DEBUG=True` の場合、SQLクエリがコンソールに出力されます
- 本番環境では `ENVIRONMENT=production` および `DEBUG=False` に設定してください

### フロントエンド環境変数

フロントエンドの環境変数は `frontend/.env.local` ファイルで管理されます。

```bash
# frontend/.env.local.example をコピーして .env.local を作成
cd frontend
cp .env.local.example .env.local
```

| 変数名 | 説明 | デフォルト値 | 必須 |
|--------|------|--------------|------|
| `NEXT_PUBLIC_API_URL` | バックエンドAPIのベースURL | `http://localhost:8000` | ✅ |

**注意事項:**
- `NEXT_PUBLIC_` プレフィックスはNext.jsでブラウザに公開される環境変数に必要です
- 本番環境では実際のAPIサーバーのURLに変更してください（例: `https://api.mogipay.example.com`）
- この変数は `frontend/lib/api/client.ts:295` で使用されます

### Docker Compose環境変数

`docker-compose.dev.yml` では、PostgreSQLコンテナの環境変数として以下が使用されます:

```yaml
POSTGRES_DB: ${POSTGRES_DB:-mogipay_dev}
POSTGRES_USER: ${POSTGRES_USER:-mogipay_user}
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-mogipay_password}
POSTGRES_PORT: ${POSTGRES_PORT:-5432}
```

これらは `backend/.env` ファイルから自動的に読み込まれます。

## 開発手順

### 初回セットアップ

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd mogipay

# 2. 環境変数ファイルを作成
# バックエンド
cd backend
cp .env.example .env
cd ..

# フロントエンド
cd frontend
cp .env.local.example .env.local
cd ..

# 3. 初回セットアップコマンド実行
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

## 本番環境デプロイ

### 前提条件

- Docker と Docker Compose がインストールされていること
- Cloudflare アカウントと Tunnel の設定が完了していること

### デプロイ手順

#### 1. 環境変数の設定

```bash
# .env.example をコピーして .env を作成
cp .env.example .env

# .env ファイルを編集
nano .env
```

必須の環境変数を設定してください：

- `POSTGRES_PASSWORD`: 強力なパスワードに変更
- `DATABASE_URL`: PostgreSQL パスワードを更新
- `TUNNEL_TOKEN`: Cloudflare Tunnel トークンを設定

#### 2. Cloudflare Tunnel の設定

1. [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/) にアクセス
2. "Access" → "Tunnels" から新しい Tunnel を作成
3. Tunnel トークンを取得して `.env` の `TUNNEL_TOKEN` に設定
4. Public Hostname を設定:
   - **フロントエンド**: `mogipay.yourdomain.com` → `http://frontend:3000`
   - **バックエンドAPI**: `api.mogipay.yourdomain.com` → `http://backend:8000`

#### 3. アプリケーションのビルドと起動

```bash
# Docker イメージをビルド
docker compose build

# コンテナを起動（デタッチモード）
docker compose up -d

# ログを確認
docker compose logs -f
```

#### 4. 動作確認

```bash
# コンテナの状態を確認
docker compose ps

# ヘルスチェック
# すべてのコンテナが "healthy" になっていることを確認
docker compose ps

# バックエンドのヘルスチェック
curl http://localhost:8000/api/health  # ※ローカルではアクセス不可（Cloudflared経由のみ）

# ブラウザで確認
# https://mogipay.yourdomain.com にアクセス
```

### デプロイ後の管理

#### コンテナの管理

```bash
# コンテナの起動
docker compose up -d

# コンテナの停止
docker compose down

# コンテナの再起動
docker compose restart

# ログの確認
docker compose logs -f [service-name]
# 例: docker compose logs -f backend
```

#### データベースのバックアップ

```bash
# データベースをバックアップ
docker compose exec postgres pg_dump -U mogipay_user mogipay_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# バックアップからリストア
docker compose exec -T postgres psql -U mogipay_user mogipay_prod < backup_file.sql
```

#### アプリケーションの更新

```bash
# 1. 最新のコードを取得
git pull origin main

# 2. イメージを再ビルド
docker compose build

# 3. コンテナを再起動（ダウンタイムあり）
docker compose up -d

# 4. 古いイメージを削除
docker image prune -f
```

#### マイグレーション実行（本番環境）

マイグレーションは backend コンテナ起動時に自動実行されます。
手動で実行する場合：

```bash
# backend コンテナ内でマイグレーション実行
docker compose exec backend alembic upgrade head

# マイグレーション履歴確認
docker compose exec backend alembic history

# ロールバック
docker compose exec backend alembic downgrade -1
```

### セキュリティ注意事項

1. **環境変数の管理**
   - `.env` ファイルは絶対にコミットしない
   - 本番環境では強力なパスワードを使用
   - 定期的にパスワードをローテーション

2. **Cloudflare Tunnel**
   - ポートは一切露出させない（全て Cloudflared 経由）
   - Cloudflare のアクセスポリシーを適切に設定
   - Tunnel トークンは厳重に管理

3. **Docker コンテナ**
   - 定期的にイメージを更新
   - セキュリティアップデートを適用
   - 不要なコンテナ・イメージを削除

4. **データベース**
   - 定期的なバックアップを実施
   - バックアップの暗号化を検討
   - アクセス制限を適切に設定

### トラブルシューティング

#### コンテナが起動しない

```bash
# ログを確認
docker compose logs

# 特定のサービスのログを詳しく確認
docker compose logs backend
docker compose logs postgres

# コンテナの状態を確認
docker compose ps -a
```

#### データベース接続エラー

```bash
# PostgreSQL コンテナの状態確認
docker compose exec postgres pg_isready -U mogipay_user -d mogipay_prod

# 環境変数の確認
docker compose exec backend env | grep DATABASE_URL

# PostgreSQL のログ確認
docker compose logs postgres
```

#### Cloudflare Tunnel が動作しない

```bash
# cloudflared のログ確認
docker compose logs cloudflared

# Tunnel トークンの確認
docker compose exec cloudflared env | grep TUNNEL_TOKEN

# Cloudflare Zero Trust Dashboard で Tunnel の状態を確認
# https://one.dash.cloudflare.com/
```

## ライセンス

MIT License
