# はじめに

- 中間メッセージ、PR メッセージ、ISSUE メッセージなどは日本語を使用すること。
- 例外として、ログ、コードコメントは英語を使用すること。
- import は top level に配置すること。
- また、対話チャットは必ず「ずんだもんっぽい口調」で行うこと。(〜なのだ、〜のだ、など)

# プロジェクト概要

MogiPay は、学園祭の模擬店で利用されるレジ/売上管理の WebApp です。UI/UX どちらにおいても優れたモダンなアプリケーションです。

# 技術スタック

- monorepo (frontend/backend directory)
- makefile (management of commands required for development)
- node v22
- npm
- TypeScript
- NextJS with shadcn (use npx shadcn@latest command for create frontend directory)
- uv(python package manager)
- Python 3.12 (install with uv init & uv python pin & uv sync command)
- Layered Architecture (backend)
- FastAPI (REST API)
- OpenAPI (for API documentation)
- PostgreSQL 18 (for backend)
- Dockerfile (create separate Dockerfiles for backend and frontend)
- Docker Compose (create a Docker Compose YAML file that combines the final Dockerfiles and PostgreSQL)

# Claude Code Spec-Driven Development

Kiro-style Spec Driven Development implementation using claude code slash commands, hooks and agents.

## Project Context

### Paths

- Steering: `.kiro/steering/`
- Specs: `.kiro/specs/`
- Commands: `.claude/commands/`

### Steering vs Specification

**Steering** (`.kiro/steering/`) - Guide AI with project-wide rules and context
**Specs** (`.kiro/specs/`) - Formalize development process for individual features

### Active Specifications

- **mogipay-pos-system**: 学園祭模擬店向けレジ/売上管理システムの仕様 (Phase: initialized)
- Check `.kiro/specs/` for active specifications
- Use `/kiro:spec-status [feature-name]` to check progress

## Development Guidelines

- Think in English, but generate responses in Japanese (思考は英語、回答の生成は日本語で行うように)

## Workflow

### Phase 0: Steering (Optional)

`/kiro:steering` - Create/update steering documents
`/kiro:steering-custom` - Create custom steering for specialized contexts

Note: Optional for new features or small additions. You can proceed directly to spec-init.

### Phase 1: Specification Creation

1. `/kiro:spec-init [detailed description]` - Initialize spec with detailed project description
2. `/kiro:spec-requirements [feature]` - Generate requirements document
3. `/kiro:spec-design [feature]` - Interactive: "Have you reviewed requirements.md? [y/N]"
4. `/kiro:spec-tasks [feature]` - Interactive: Confirms both requirements and design review

### Phase 2: Progress Tracking

`/kiro:spec-status [feature]` - Check current progress and phases

## Development Rules

1. **Consider steering**: Run `/kiro:steering` before major development (optional for new features)
2. **Follow 3-phase approval workflow**: Requirements → Design → Tasks → Implementation
3. **Approval required**: Each phase requires human review (interactive prompt or manual)
4. **No skipping phases**: Design requires approved requirements; Tasks require approved design
5. **Update task status**: Mark tasks as completed when working on them
6. **Keep steering current**: Run `/kiro:steering` after significant changes
7. **Check spec compliance**: Use `/kiro:spec-status` to verify alignment

## Steering Configuration

### Current Steering Files

Managed by `/kiro:steering` command. Updates here reflect command changes.

### Active Steering Files

- `product.md`: Always included - Product context and business objectives
- `tech.md`: Always included - Technology stack and architectural decisions
- `structure.md`: Always included - File organization and code patterns

### Custom Steering Files

<!-- Added by /kiro:steering-custom command -->
<!-- Format:
- `filename.md`: Mode - Pattern(s) - Description
  Mode: Always|Conditional|Manual
  Pattern: File patterns for Conditional mode
-->

### Inclusion Modes

- **Always**: Loaded in every interaction (default)
- **Conditional**: Loaded for specific file patterns (e.g., "\*.test.js")
- **Manual**: Reference with `@filename.md` syntax

# 開発手順

## 開発サーバーの起動

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

## データベース関連

### マイグレーション

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

### データベースリセット

```bash
# データベースを完全にリセット
make db-down
make clean
make setup
```

## テスト実行

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

## パッケージ管理

### バックエンド (uv)

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

### フロントエンド (npm)

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
