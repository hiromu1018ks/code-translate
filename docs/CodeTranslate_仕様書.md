# CodeTranslate 仕様書

**プロジェクト名:** CodeTranslate  
**バージョン:** v0.1.0  
**最終更新日:** 2026-02-06  

---

## 1. 概要

CodeTranslate は、TranslateGemma 12B モデルを Ollama 経由でローカル実行し、プログラミング文脈に特化した日本語⇔英語翻訳を行うターミナルUI（TUI）アプリケーションである。

主な利用シーンとして、Claude Code や OpenCode への入力プロンプトを日本語から英語に翻訳すること、および返答の英語を日本語に翻訳することを想定している。

---

## 2. 目的・背景

- AI コーディングツール（Claude Code, OpenCode 等）は英語での入力が最も精度が高い
- 日本語話者が自然に日本語で考えた指示を、適切な英語プロンプトに変換したい
- 一般的な翻訳ツールではプログラミング用語の誤訳が頻発する（例：「配列」→「arrangement」）
- ローカル実行によりデータを外部に送信しないプライバシー保護

---

## 3. システム構成

### 3.1 ハードウェア要件

| 項目 | 要件 |
|------|------|
| GPU | NVIDIA RTX 3060 12GB（またはそれ以上） |
| VRAM | 12GB（12Bモデルで約8.1GB、4Bモデルで約3.3GB使用） |
| RAM | 16GB 以上推奨 |
| ストレージ | モデルファイル用に約 10GB の空き |

### 3.2 ソフトウェア要件

| 項目 | バージョン |
|------|-----------|
| OS | Linux（Ubuntu 22.04+）/ macOS / Windows（WSL2） |
| Python | 3.10 以上 |
| Ollama | 最新版 |
| TranslateGemma | 4B/12B（`translategemma:4b`または`translategemma:12b`） |

### 3.3 Python 依存パッケージ

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| textual | >= 0.85.0 | TUI フレームワーク |
| ollama | >= 0.4.0 | Ollama Python クライアント |
| pyperclip | >= 1.9.0 | クリップボード操作 |

### 3.4 アーキテクチャ図

```
┌─────────────────────────────────────────────┐
│              CodeTranslate TUI              │
│                 (app.py)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 入力     │  │ 方向切替 │  │ 履歴     │  │
│  │ エリア   │  │ トグル   │  │ パネル   │  │
│  └────┬─────┘  └──────────┘  └──────────┘  │
│       │                                     │
│  ┌────▼──────────────────────────────────┐  │
│  │        翻訳エンジン (translator.py)    │  │
│  │  ┌────────────┐  ┌────────────────┐   │  │
│  │  │コードブロック│  │ 用語辞書       │   │  │
│  │  │保護        │  │ (glossary.json)│   │  │
│  │  └────────────┘  └────────────────┘   │  │
│  └────┬──────────────────────────────────┘  │
│       │                                     │
└───────┼─────────────────────────────────────┘
         │ Ollama API (localhost:11434)
┌───────▼─────────────────────────────────────┐
│         TranslateGemma 4B/12B/27B         │
│         MODEL環境変数で切り替え可能           │
│         4B: 3.3GB / 12B: 8.1GB         │
└─────────────────────────────────────────────┘
```

---

## 4. ファイル構成

```
code-translator/
├── app.py             # TUI メインアプリケーション
├── translator.py      # 翻訳エンジンモジュール
├── glossary.json      # コーディング特化用語辞書
├── requirements.txt   # Python 依存パッケージ
└── README.md          # セットアップ手順・使い方
```

| ファイル | 行数目安 | 責務 |
|---------|---------|------|
| `app.py` | ~200行 | UI レイアウト、キーバインド、イベント処理 |
| `translator.py` | ~150行 | プロンプト構築、コード保護、Ollama API 呼び出し |
| `glossary.json` | ~200行 | 日英・英日の対訳辞書データ |

---

## 5. 機能仕様

### 5.1 翻訳機能

| 機能 | 説明 |
|------|------|
| 日本語 → 英語翻訳 | 日本語テキストをプログラミング文脈で英語に翻訳 |
| 英語 → 日本語翻訳 | 英語テキストをプログラミング文脈で日本語に翻訳 |
| 翻訳方向の切り替え | Tab キーでワンタッチ切り替え |

### 5.2 コーディング特化機能

| 機能 | 説明 |
|------|------|
| コードブロック保護 | バッククォート（`` ` `` および `` ``` ``）で囲まれた部分を翻訳対象から除外 |
| 用語辞書（Glossary） | `glossary.json` の対訳データをプロンプトに注入し、技術用語の翻訳精度を向上 |
| プログラミング文脈指示 | TranslateGemma へのプロンプトにソフトウェア開発文脈であることを明示 |
| 技術用語の保持 | 言語名・ツール名・フレームワーク名等をそのまま保持（`preserve_as_is` リスト） |

### 5.3 UI 機能

| 機能 | 説明 |
|------|------|
| 入力エリア | Markdown 対応の TextArea。複数行入力可能 |
| 出力エリア | 翻訳結果を表示。シンタックスハイライト対応 |
| 翻訳方向表示 | 現在の翻訳方向をアイコン付きで視覚的に表示 |
| ステータスバー | 翻訳状態（待機/翻訳中/完了/エラー）を表示 |
| 履歴パネル | 過去の翻訳結果を一覧表示（直近20件） |
| クリップボードコピー | 翻訳結果をワンキーでクリップボードにコピー |

### 5.4 キーバインド一覧

| キー | 動作 |
|------|------|
| `Ctrl+Enter` / `Ctrl+J` | 翻訳を実行 |
| `Tab` | 翻訳方向を切り替え（日→英 ⇔ 英→日） |
| `Ctrl+Y` | 翻訳結果をクリップボードにコピー |
| `Ctrl+H` | 翻訳履歴パネルの表示/非表示 |
| `Ctrl+L` | 入力・出力をクリア |
| `Ctrl+Q` | アプリを終了 |

---

## 6. 翻訳エンジン仕様

### 6.1 使用モデル

- **デフォルト:** TranslateGemma 12B（`translategemma:12b`）
- **モデル切り替え:** `TRANSLATEGEMMA_MODEL` 環境変数で設定可能
- **量子化:** Q4（Ollama デフォルト）
- **VRAM 使用量:** 12Bで約8.1GB、4Bで約3.3GB
- **推論バックエンド:** Ollama（localhost:11434）

### 6.2 プロンプトフォーマット

TranslateGemma 公式の推奨プロンプト形式に準拠する：

```
You are a professional {source_lang} ({source_code}) to {target_lang}
({target_code}) translator. Your goal is to accurately convey the meaning
and nuances of the original {source_lang} text while adhering to
{target_lang} grammar, vocabulary, and cultural sensitivities. Produce
only the {target_lang} translation, without any additional explanations
or commentary. Please translate the following {source_lang} text into
{target_lang}:


{text}
```

これに加えて以下を付加する：

- **コーディング文脈指示:** コード・変数名・ファイルパス・コマンドの保持を指示
- **用語辞書ヒント:** `glossary.json` から最大30件の対訳をプロンプト末尾に付加

### 6.3 コードブロック保護の処理フロー

```
1. 入力テキストからコードブロックを正規表現で検出
   - マルチラインブロック: ```...```
   - インラインコード: `...`

2. 検出したコードブロックをプレースホルダー（__CODE_BLOCK_N__）に置換

3. プレースホルダー置換済みテキストを TranslateGemma で翻訳

4. 翻訳結果内のプレースホルダーを元のコードブロックに復元
```

### 6.4 用語辞書（glossary.json）の構造

```json
{
  "ja_to_en": {
    "日本語の用語": "English term",
    ...
  },
  "en_to_ja": {
    "English term": "日本語の用語",
    ...
  },
  "preserve_as_is": [
    "Python", "React", "Docker", ...
  ]
}
```

- `ja_to_en`: 日本語→英語翻訳時に使用する対訳辞書（約100語収録）
- `en_to_ja`: 英語→日本語翻訳時に使用する対訳辞書（約30語収録）
- `preserve_as_is`: 翻訳せずそのまま保持するべき固有名詞のリスト

ユーザーが自由に追加・編集可能。使用中に発見した誤訳パターンを蓄積することで翻訳精度が向上する。

---

## 7. セットアップ手順

### 7.1 Ollama のインストール

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 7.2 TranslateGemma モデルのダウンロード

```bash
# デフォルト（12Bモデル）
ollama pull translategemma:12b

# より高速な4Bモデル（RTX 3060 12GB推奨）
ollama pull translategemma:4b
```

### 7.3 モデルの切り替え

TranslateGemma には4B、12B、27Bのモデルサイズが用意されています。環境に応じて切り替え可能です。

| モデル | VRAM使用量 | 速度 | 精度 | おすすめ環境 |
|--------|-----------|------|------|------------|
| `translategemma:4b` | 3.3GB | ⚡⚡⚡⚡⚡ | ★★★☆☆ | RTX 3060 12GB (推奨) |
| `translategemma:12b` | 8.1GB | ⚡⚡ | ★★★★★ | RTX 3060 12GB+ |

**モデル切り替え手順:**

```bash
# 環境変数を設定してアプリ起動
TRANSLATEGEMMA_MODEL=translategemma:4b python app.py

# 永続的に設定する場合（.bashrcまたは.zshrcに追加）
echo 'export TRANSLATEGEMMA_MODEL=translategemma:4b' >> ~/.bashrc
source ~/.bashrc
```

### 7.4 Python 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 7.5 起動

```bash
python app.py
```

### 7.3 Python 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 7.4 起動

```bash
python app.py
```

起動時に Ollama への接続確認と TranslateGemma モデルの存在確認が自動実行される。問題がある場合はステータスバーおよび出力エリアにエラーメッセージが表示される。

---

## 8. 将来の拡張計画

| フェーズ | 内容 | 優先度 |
|---------|------|--------|
| v0.2 | ストリーミング翻訳（逐次表示） | 高 |
| v0.2 | 原文/翻訳の左右分割ビュー | 中 |
| v0.3 | Claude Code / OpenCode ラッパーモード | 高 |
| v0.3 | 翻訳履歴の永続化（SQLite） | 中 |
| v0.4 | 誤訳データの収集・エクスポート機能 | 中 |
| v1.0 | LoRA ファインチューニング用データセット生成 | 低 |
| v1.0 | LoRA ファインチューニング済みモデルへの切り替え | 低 |

### 8.1 ラッパーモード構想

将来的に Claude Code / OpenCode のラッパーとして動作するモードを実装予定：

```
ユーザー（日本語） → CodeTranslate（日→英翻訳）
    → Claude Code / OpenCode（英語で実行）
        → CodeTranslate（英→日翻訳） → ユーザー（日本語で表示）
```

---

## 9. 制約・既知の課題

| 項目 | 内容 |
|------|------|
| ネストしたコードブロック | ` ``` ` 内にさらに ` ``` ` がある場合、正しく検出できない可能性がある |
| 長文の翻訳速度 | 12B モデルでは長文で数十秒かかる場合がある。4B モデルを使用することで高速化可能 |
| 用語辞書の上限 | プロンプト長の制約により、辞書ヒントは30件に制限 |
| クリップボード | ヘッドレス環境では `xclip` または `xsel` のインストールが必要 |
| Windows | ネイティブ Windows では Textual の一部表示が崩れる可能性あり（WSL2 推奨） |
