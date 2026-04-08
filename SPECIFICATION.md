# 釣具EC カスタマーサポートAI回答支援システム（RAG）

## 完全仕様書 v1.0

---

## 1. プロジェクト概要

### 1.1 目的
釣具ECサイト「ますびと商店」のカスタマーサポート業務を、RAG（Retrieval-Augmented Generation）により支援する。
過去3ヶ月分の問い合わせ対応履歴（160件）をベクトルDB化し、新規問い合わせに対してAIが類似事例を参照しながら回答ドラフトを自動生成する。

### 1.2 対象ユーザー
- 釣りの専門知識が少ないサポートスタッフ
- 日々大量の問い合わせを処理する運用者

### 1.3 コアコンセプト
- **専門知識不要**: AIが過去事例から適切な回答を生成
- **画面遷移ゼロ**: SPAで完結するワンページUI
- **ワンクリック学習**: 回答確定時にナレッジDBへ自動蓄積

---

## 2. アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                    Vercel (Hosting)                       │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │  Static Files │    │  Serverless Functions (API)   │   │
│  │  HTML/CSS/JS  │    │  FastAPI (Python Runtime)     │   │
│  │  + htmx       │    │                              │   │
│  └──────────────┘    └──────────┬───────────────────┘   │
│                                  │                       │
└──────────────────────────────────┼───────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
              ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
              │  Gemini    │ │  Gemini    │ │ Supabase  │
              │  3.1 Pro   │ │  Embedding │ │ pgvector  │
              │ (生成)     │ │  (検索)    │ │ (保存)    │
              └───────────┘ └───────────┘ └───────────┘
```

### 2.1 技術スタック

| レイヤー | 技術 | 役割 |
|---------|------|------|
| フロントエンド | HTML5 + Tailwind CSS + htmx | SPA風の非同期UI |
| バックエンド | FastAPI (Python 3.12) | API処理、AI連携 |
| データベース | Supabase (PostgreSQL + pgvector) | ベクトル検索・データ永続化 |
| AI（生成） | Gemini 2.5 Pro (`gemini-2.5-pro`) | 回答ドラフト生成 |
| AI（埋め込み）| text-embedding-004 (768次元) | テキストのベクトル化 |
| ホスティング | Vercel | サーバーレスデプロイ |

---

## 3. データベース設計

### 3.1 テーブル: `qa_knowledge`

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE qa_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    category TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HNSWインデックス（高速近似最近傍探索）
CREATE INDEX idx_qa_knowledge_embedding
ON qa_knowledge USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### 3.2 RPC関数: `match_qa_knowledge`

```sql
CREATE OR REPLACE FUNCTION match_qa_knowledge(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 3
)
RETURNS TABLE (
    id UUID,
    question_text TEXT,
    answer_text TEXT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        qk.id,
        qk.question_text,
        qk.answer_text,
        1 - (qk.embedding <=> query_embedding) AS similarity
    FROM qa_knowledge qk
    WHERE 1 - (qk.embedding <=> query_embedding) > match_threshold
    ORDER BY qk.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

---

## 4. データライフサイクル

### Phase 1: 初期データロード（セットアップスクリプト）

1. CSVファイル（Shift-JIS）を読み込み
2. データクレンジング:
   - 質問・回答の両方が存在する行のみ抽出（160件）
   - 前後の空白・改行をトリム
   - 重複行の除去
3. 各レコードの `question_text + answer_text` を結合してベクトル化
4. Supabaseへ一括INSERT（バッチ処理、レート制限考慮）

### Phase 2: 継続学習（運用中）

- スタッフが回答を確定（「この内容で学習して次へ進む」ボタン）するたびに:
  1. 質問+確定回答をベクトル化
  2. `qa_knowledge`にINSERT
  3. 以降の検索対象に即座に反映

---

## 5. API設計

### 5.1 `POST /api/generate`

**目的**: 新規問い合わせに対するAI回答ドラフトの生成

**リクエスト** (htmxフォーム送信):
```
Content-Type: application/x-www-form-urlencoded
question=顧客からの問い合わせ本文
```

**処理フロー**:
1. `question`を`text-embedding-004`でベクトル化
2. Supabase RPCで類似Q&A上位3件を取得
3. プロンプトテンプレートに類似事例と新規質問を注入
4. Gemini 2.5 Proで回答ドラフトを生成
5. htmx用HTMLフラグメントを返却（エディタ + リファレンスカード）

**レスポンス**: HTMLフラグメント（2つのセクション）
```html
<!-- メインペイン: AI回答エディタ -->
<div id="editor-area">
    <textarea id="answer-editor">...</textarea>
    <div class="button-group">...</div>
</div>

<!-- 右ペイン: リファレンスカード -->
<div id="reference-area">
    <div class="ref-card">...</div>
    ...
</div>
```

### 5.2 `POST /api/learn`

**目的**: 確定した回答をナレッジDBに学習

**リクエスト**:
```
Content-Type: application/x-www-form-urlencoded
question=元の顧客質問
answer=スタッフが編集・確定した回答
```

**処理フロー**:
1. `question + answer`を結合してベクトル化
2. `qa_knowledge`にINSERT
3. 成功トースト通知のHTMLフラグメントを返却

**レスポンス**: トースト通知HTML
```html
<div id="toast" class="toast-success" hx-swap-oob="true">
    学習が完了しました
</div>
```

### 5.3 `GET /api/stats`

**目的**: ナレッジDB統計情報の表示

**レスポンス**:
```json
{
    "total_records": 160,
    "last_learned_at": "2026-04-07T10:30:00Z"
}
```

---

## 6. AI プロンプト設計

### 6.1 回答生成プロンプト

```
あなたは釣具ECサイト「ますびと商店」のベテランカスタマーサポートです。
以下の【過去の対応ナレッジ】を参考に、【顧客からの新規問い合わせ】に対する丁寧な返信メールのドラフトを作成してください。

【過去の対応ナレッジ】
---ナレッジ1 (類似度: {similarity_1}%)---
質問: {question_1}
回答: {answer_1}

---ナレッジ2 (類似度: {similarity_2}%)---
質問: {question_2}
回答: {answer_2}

---ナレッジ3 (類似度: {similarity_3}%)---
質問: {question_3}
回答: {answer_3}

【顧客からの新規問い合わせ】
{new_customer_query}

【制約事項】
- ますびと商店のトーン＆マナー（丁寧・親切）に合わせること。
- 挨拶は「お客様\nいつも大変お世話になっております。」で始める。
- 署名は「ますびと商店」で締める。
- 過去のナレッジにない不明な釣り用語・仕様に関する断定は避け、事実に基づき回答すること。
- 不明な点がある場合は「確認してご連絡いたします」等の対応を提案すること。
- 返送先が必要な場合: 〒180-0011 東京都武蔵野市八幡町1-1-3-203 ますびと商店 TEL：0422-66-2710
```

---

## 7. UI/UX設計

### 7.1 レイアウト（3ペイン構成）

```
┌──────────────┬───────────────────────┬────────────────┐
│  左ペイン     │   メインペイン         │  右ペイン       │
│  (30%)       │   (45%)               │  (25%)         │
│              │                       │                │
│  問い合わせ   │   AI回答エディタ       │  参考事例       │
│  入力エリア   │                       │  (Top 3)       │
│              │                       │                │
│  [テキスト    │   [生成された回答      │  ┌──────────┐ │
│   エリア]     │    テキストエリア      │  │ 事例1     │ │
│              │    (編集可能)]         │  │ 類似度92% │ │
│              │                       │  └──────────┘ │
│              │   [コピー] [学習&次へ]  │  ┌──────────┐ │
│  [回答案を    │                       │  │ 事例2     │ │
│   生成]      │                       │  │ 類似度85% │ │
│              │                       │  └──────────┘ │
│              │                       │  ┌──────────┐ │
│              │                       │  │ 事例3     │ │
│  ナレッジ数:  │                       │  │ 類似度71% │ │
│  160件       │                       │  └──────────┘ │
└──────────────┴───────────────────────┴────────────────┘
```

### 7.2 カラーパレット

| 用途 | 色 | Tailwind |
|------|-----|---------|
| 背景 | #F8FAFC | bg-slate-50 |
| カード背景 | #FFFFFF | bg-white |
| プライマリ | #2563EB | bg-blue-600 |
| セカンダリ | #10B981 | bg-emerald-500 |
| テキスト | #1E293B | text-slate-800 |
| ボーダー | #E2E8F0 | border-slate-200 |

### 7.3 インタラクション

| 操作 | トリガー | htmx属性 | 動作 |
|------|---------|----------|------|
| 回答生成 | ボタン or Ctrl+Enter | `hx-post="/api/generate"` `hx-target="#main-pane"` | 左ペインの質問を送信→メイン&右ペインを更新 |
| 学習&次へ | ボタン or Shift+Enter | `hx-post="/api/learn"` `hx-swap="none"` | 確定回答を学習→トースト表示→入力欄クリア |
| クリップボードコピー | ボタン | JavaScript | エディタ内容をコピー |
| リセット | Escキー | JavaScript | 全ペインを初期状態に |

### 7.4 ローディングUX

生成中（3-5秒）はスケルトンスクリーンを表示:
- メインペイン: テキストエリアの形をしたパルスアニメーション
- 右ペイン: カード3枚分のパルスアニメーション
- htmx `hx-indicator` でトリガー

### 7.5 トースト通知

- 学習完了: 緑色、右上に3秒表示後フェードアウト
- エラー: 赤色、手動で閉じるまで表示

---

## 8. ファイル構成

```
cs/
├── api/
│   ├── index.py              # FastAPIアプリ本体（Vercelエントリポイント）
│   ├── generate.py           # /api/generate エンドポイント
│   ├── learn.py              # /api/learn エンドポイント
│   └── stats.py              # /api/stats エンドポイント
├── lib/
│   ├── gemini_client.py      # Gemini API (生成 + Embedding)
│   ├── supabase_client.py    # Supabase接続・クエリ
│   ├── prompt_template.py    # プロンプトテンプレート
│   └── html_fragments.py     # htmx用HTMLフラグメント生成
├── static/
│   └── index.html            # メインHTML（Tailwind CDN + htmx）
├── scripts/
│   ├── init_db.sql           # DB初期化SQL
│   └── seed_data.py          # CSV→Supabase初期データ投入
├── vercel.json               # Vercelデプロイ設定
├── requirements.txt          # Python依存パッケージ
├── .env.example              # 環境変数テンプレート
├── .gitignore
└── SPECIFICATION.md          # 本仕様書
```

---

## 9. 環境変数

```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
```

---

## 10. デプロイ設定

### vercel.json
```json
{
    "builds": [
        {
            "src": "api/index.py",
            "use": "@vercel/python"
        },
        {
            "src": "static/**",
            "use": "@vercel/static"
        }
    ],
    "routes": [
        { "src": "/api/(.*)", "dest": "api/index.py" },
        { "src": "/(.*)", "dest": "static/$1" }
    ]
}
```

---

## 11. 初期データ投入仕様

### seed_data.py の処理フロー

1. CSVファイル読み込み（Shift-JIS → UTF-8）
2. クレンジング:
   - 質問・回答が両方空でない行のみ抽出
   - 前後空白トリム
   - 完全重複行の除去
3. バッチ処理（10件ずつ）:
   - 各レコードの `question_text + "\n\n" + answer_text` をEmbedding API送信
   - rate limit対策: バッチ間に1秒のsleep
4. Supabaseへbulk INSERT
5. 完了ログ出力（投入件数、スキップ件数）

---

## 12. セキュリティ考慮

- APIキーはすべて環境変数で管理（.envはgitignore）
- Supabaseはサービスロールキーを使用（サーバーサイドのみ）
- ユーザー入力はサニタイズ後にプロンプトへ注入
- CORS設定はVercelのデフォルト（同一オリジン）に依存

---

## 13. 将来の拡張案（スコープ外）

- カテゴリ自動分類（キャンセル/配送/商品問い合わせ等）
- 回答品質のフィードバック機能（良い/要改善）
- 管理画面（ナレッジの一覧・編集・削除）
- 複数チャネル対応（メール以外）

---

## 14. マルチチャネル拡張

### 14.1 概要
CSシステムを複数のビジネス/ユースケースで利用可能に拡張。各チャネルは独自のナレッジDB・AIプロンプト・設定を持つ。

### 14.2 チャネルテーブル: `channels`
| カラム | 型 | 説明 |
|--------|-----|------|
| id | UUID | プライマリキー |
| name | TEXT | チャネル名 |
| slug | TEXT | URL用識別子（ユニーク） |
| description | TEXT | 説明文 |
| system_prompt | TEXT | AI生成用のシステムプロンプト |
| greeting_prefix | TEXT | 回答冒頭の挨拶文 |
| signature | TEXT | 回答末尾の署名 |
| color | TEXT | テーマカラー（HEX） |
| created_by | UUID | 作成者 |

### 14.3 データ分離
- `qa_knowledge`テーブルに`channel_id`カラムを追加
- チャネル別のベクトル検索RPC `match_qa_knowledge_by_channel`
- 既存データは「ますびと商店」デフォルトチャネルに自動マッピング

### 14.4 ユーザーフロー
1. ログイン → チャネル選択画面（/channels）
2. チャネルをクリック → CS画面（/?channel={slug}）
3. チャネル固有のナレッジで回答生成・学習

### 14.5 管理機能（管理者のみ）
- チャネルの作成・編集・削除（/admin）
- AIプロンプトのカスタマイズ
- チャネルメンバー管理

### 14.6 後方互換性
- 既存の`/api/generate`、`/api/learn`は`channel_slug`パラメータなしでも動作
- 既存の157件のナレッジデータはデフォルトチャネルに帰属
