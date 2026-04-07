# CS - カスタマーサポートAI回答支援システム

## プロジェクト概要
釣具ECサイト「ますびと商店」のカスタマーサポートRAGシステム。
過去のQ&Aナレッジをベクトル検索し、Gemini AIで回答ドラフトを生成する。

## 技術スタック
- Backend: FastAPI (Python 3.12)
- Frontend: HTML5 + Tailwind CSS + htmx
- DB: Supabase (PostgreSQL + pgvector)
- AI: Gemini 2.5 Pro (生成) + text-embedding-004 (768次元)
- Hosting: Vercel

## ローカル開発
```bash
# 環境変数を設定
cp .env.example .env
# .envにAPIキーを記入

# 依存関係インストール
pip install -r requirements.txt

# 初期データ投入
python scripts/seed_data.py

# ローカルサーバー起動
uvicorn api.index:app --reload --port 8000
```

## ディレクトリ構成
- api/ — FastAPIアプリ（Vercelサーバーレス関数）
- lib/ — 共有ライブラリ（AI連携、DB連携、テンプレート）
- static/ — フロントエンド（HTML）
- scripts/ — DB初期化・データ投入スクリプト
- data/ — 元データCSV

## APIエンドポイント
- POST /api/generate — 回答ドラフト生成（htmx HTML返却）
- POST /api/learn — 確定回答の学習（DB保存）
- GET /api/stats — ナレッジDB統計

## デプロイ
```bash
vercel deploy
```
