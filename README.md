# CodeTranslate

プログラミング文脈に特化した日本語⇔英語翻訳TUIツール。TranslateGemma 12B モデルをローカル実行し、Claude Code や OpenCode への入力・出力翻訳に最適化されています。

## 機能

- 日本語 → 英語翻訳 / 英語 → 日本語翻訳（Tabキーで切り替え）
- コードブロック保護（コード部分は翻訳対象から除外）
- 用語辞書による技術用語の正確な翻訳
- クリップボードコピー機能
- 翻訳履歴表示

## 要件

| 項目 | 要件 |
|------|------|
| GPU | NVIDIA RTX 3060 12GB（またはそれ以上） |
| VRAM | 12GB（TranslateGemma 12B Q4 量子化で約 8.1GB 使用） |
| RAM | 16GB 以上推奨 |
| Python | 3.10 以上 |
| OS | Linux（Ubuntu 22.04+）/ macOS / Windows（WSL2） |

## セットアップ手順

### 1. Ollama のインストール

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. TranslateGemma 12B モデルのダウンロード

```bash
ollama pull translategemma:12b
```

### 3. CodeTranslate のインストール

```bash
cd code-translator
pip install -e .
```

## 使い方

### 起動

```bash
codetranslate
```

または

```bash
python app.py
```

### キーバインド

| キー | 動作 |
|------|------|
| `Ctrl+Enter` / `Ctrl+J` | 翻訳を実行 |
| `Tab` | 翻訳方向を切り替え（日→英 ⇔ 英→日） |
| `Ctrl+Y` | 翻訳結果をクリップボードにコピー |
| `Ctrl+H` | 翻訳履歴パネルの表示/非表示 |
| `Ctrl+L` | 入力・出力をクリア |
| `Ctrl+Q` | アプリを終了 |

## 用語辞書のカスタマイズ

`glossary.json` を編集して、独自の用語辞書を追加できます。翻訳精度を向上させるために、プロジェクト固有の用語を登録することをお勧めします。

## トラブルシューティング

### Ollama が起動しない場合

Ollama が正常に動作しているか確認します：

```bash
curl http://localhost:11434/api/tags
```

### モデルのダウンロードが失敗する場合

ネットワーク接続を確認し、再実行します：

```bash
ollama pull translategemma:12b
```

### モデルの切り替え

TranslateGemma には4B、12B、27Bのモデルサイズが用意されています。環境に応じて切り替え可能です。

| モデル | VRAM使用量 | 速度 | 精度 | おすすめ環境 |
|--------|-----------|------|------|------------|
| `translategemma:4b` | 3.3GB | ⚡⚡⚡⚡⚡ | ★★★☆☆ | RTX 3060 12GB (推奨) |
| `translategemma:12b` | 8.1GB | ⚡⚡ | ★★★★★ | RTX 3060 12GB+ |

**モデル切り替え手順:**

```bash
# 使用したいモデルをダウンロード（初回のみ）
ollama pull translategemma:4b

# 環境変数を設定してアプリ起動
TRANSLATEGEMMA_MODEL=translategemma:4b codetranslate

# 永続的に設定する場合
echo 'export TRANSLATEGEMMA_MODEL=translategemma:4b' >> ~/.bashrc
source ~/.bashrc
```

### VRAM 不足の場合

VRAM 8GB 以下の場合は、より小さなモデル（translategemma:4b 等）の使用を検討してください。

### クリップボードが動作しない場合（Linux）

`xclip` または `xsel` をインストールしてください：

```bash
# Ubuntu/Debian
sudo apt-get install xclip

# Fedora
sudo dnf install xclip
```

## ライセンス

MIT License
