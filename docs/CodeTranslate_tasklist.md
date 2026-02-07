# CodeTranslate タスクリスト

**粒度:** AIコーディングエージェント（Claude Code / OpenCode）が1セッションで完結できる単位
**前提:** 仕様書 `CodeTranslate_仕様書.md` を参照すること

---

## 進捗サマリー

| Phase | ステータス | タスク数 | 完了数 | 進捗 |
|-------|-----------|---------|--------|------|
| Phase 0 | ✅ 完了 | 1 | 1 | 100% |
| Phase 1 | ⏳ 未着手 | 4 | 0 | 0% |
| Phase 2 | ⏳ 未着手 | 5 | 0 | 0% |
| Phase 3 | ⏳ 未着手 | 3 | 0 | 0% |
| Phase 4 | ⏳ 未着手 | 2 | 0 | 0% |
| **合計** | | **15** | **1** | **6.7%** |

---

## Phase 0: プロジェクト初期化

### ~~Task 0-1: プロジェクトスキャフォールディング~~ ✅ 完了
**入力:** なし  
**成果物:** プロジェクトディレクトリ一式  
**内容:**
- `code-translator/` ディレクトリを作成
- `requirements.txt` を作成（textual>=0.85.0, ollama>=0.4.0, pyperclip>=1.9.0）
- `pyproject.toml` を作成（プロジェクトメタデータ、依存関係、エントリポイント `codetranslate = "app:main"`）
- `.gitignore` を作成（`__pycache__/`, `.venv/`, `*.egg-info/` 等）
- 空の `app.py`, `translator.py` をプレースホルダーとして配置
- `README.md` を仕様書に基づいて作成（セットアップ手順・使い方）

**完了条件:** `pip install -e .` が通り、`codetranslate` コマンドが（空の状態で）実行できること

---

## Phase 1: 翻訳エンジン（translator.py）

### Task 1-1: 基本翻訳クラスの実装
**入力:** なし  
**成果物:** `translator.py`（基本翻訳のみ）  
**内容:**
- `CodeTranslator` クラスを作成
- `MODEL = "translategemma:12b"` を定数として定義
- TranslateGemma 公式プロンプトフォーマットの `PROMPT_TEMPLATE` を定義
- `_build_prompt(text, direction)` メソッドを実装
  - `direction="ja_to_en"` の場合: source=Japanese(ja), target=English(en-US)
  - `direction="en_to_ja"` の場合: source=English(en-US), target=Japanese(ja)
- `translate(text, direction)` メソッドを実装
  - `ollama.chat()` を呼び出し、レスポンスの `message.content` を返す
- `TranslationResult` データクラスを定義（original, translated, direction フィールド）
- `check_connection()` メソッドを実装
  - `ollama.list()` でモデル一覧を取得し、translategemma が存在するか確認
  - 接続エラー時は適切なメッセージを返す

**完了条件:** 以下のコードが動作すること
```python
t = CodeTranslator()
ok, msg = t.check_connection()
result = t.translate("この関数のバグを直して", "ja_to_en")
print(result.translated)
```

---

### Task 1-2: コードブロック保護機能の実装
**入力:** Task 1-1 完了済みの `translator.py`  
**成果物:** `translator.py` にコードブロック保護を追加  
**内容:**
- `_protect_code_blocks(text)` メソッドを実装
  - 正規表現 `(```[\s\S]*?```|`[^`\n]+`)` でコードブロックを検出
  - 検出したブロックを `__CODE_BLOCK_0__`, `__CODE_BLOCK_1__`, ... に置換
  - 置換マッピング辞書を返す
- `_restore_code_blocks(text, placeholders)` メソッドを実装
  - プレースホルダーを元のコードブロックに復元
- `translate()` メソッドを修正
  - 翻訳前に `_protect_code_blocks()` を呼ぶ
  - 翻訳後に `_restore_code_blocks()` を呼ぶ
- テスト: 以下の入力でコードが壊れないことを確認
  ```
  `print("hello")` を使ってください。
  ```

**完了条件:** コードブロック内のテキストが翻訳されず、そのまま保持されること

---

### Task 1-3: 用語辞書（Glossary）の実装
**入力:** Task 1-2 完了済みの `translator.py`  
**成果物:** `glossary.json` + `translator.py` に辞書機能を追加  
**内容:**
- `glossary.json` を作成
  - `ja_to_en`: 日本語→英語の対訳（約100語）。主要なプログラミング用語をカバー
    - データ構造系: 配列→array, 連想配列→associative array, 連結リスト→linked list 等
    - OOP系: クラス→class, 継承→inheritance, インターフェース→interface 等
    - 開発プロセス系: デプロイ→deploy, リファクタリング→refactoring 等
    - 動詞系: バグを直す→fix the bug, 実装する→implement 等
  - `en_to_ja`: 英語→日本語の対訳（約30語）。主要な用語のみ
  - `preserve_as_is`: 翻訳しない固有名詞リスト（Python, React, Docker, Claude Code 等）
- `_load_glossary(path)` メソッドを実装
  - JSON ファイルを読み込む。ファイルが無い場合は空の辞書を返す
- `_build_glossary_hint(direction)` メソッドを実装
  - 指定方向の辞書から最大30件を `"用語 → 訳語"` 形式の文字列に変換
- `_build_prompt()` を修正
  - プロンプト末尾にコーディング文脈指示と用語辞書ヒントを付加

**完了条件:** 用語辞書の内容がプロンプトに反映され、「配列」が "array" と翻訳されること

---

### Task 1-4: 翻訳エンジンのエラーハンドリング強化
**入力:** Task 1-3 完了済みの `translator.py`  
**成果物:** `translator.py` のエラー処理改善  
**内容:**
- `translate()` の `ollama.chat()` 呼び出しを try-except で囲む
  - 接続エラー時: `[翻訳エラー] Ollama に接続できません` を返す
  - モデルエラー時: `[翻訳エラー] モデルが見つかりません` を返す
  - タイムアウト時: `[翻訳エラー] タイムアウトしました` を返す
  - その他: エラーメッセージをそのまま返す
- 空文字列の入力に対して空の `TranslationResult` を返す
- `TranslationResult` に `error: bool = False` フィールドを追加
- `check_connection()` の戻り値を改善
  - Ollama 未起動 / モデル未インストール / 正常 の3パターンを明確に区別

**完了条件:** Ollama が停止した状態でもアプリがクラッシュせず、適切なエラーメッセージが返ること

---

## Phase 2: TUI アプリケーション（app.py）

### Task 2-1: 基本レイアウトの構築
**入力:** なし（translator.py は未使用でOK）  
**成果物:** `app.py`（UIのみ、翻訳ロジック未接続）  
**内容:**
- `CodeTranslateApp(App)` クラスを作成
- Textual CSS でレイアウトを定義
  - 画面上部: 翻訳方向表示バー（`DirectionToggle` ウィジェット）
  - 画面中央上: 入力エリア（`TextArea`, Markdown モード）
  - 画面中央下: 出力エリア（`RichLog`, ハイライト有効）
  - 画面下部: ステータスバー（`StatusBar` カスタムウィジェット）+ Footer
- `DirectionToggle(Static)` カスタムウィジェットを実装
  - 🇯🇵 日本語 → 🇺🇸 English / 🇺🇸 English → 🇯🇵 日本語 を表示
  - `toggle()` メソッドで方向を切り替え
  - `direction` プロパティで現在の方向を取得
- `StatusBar(Static)` カスタムウィジェットを実装
  - `set_status(text, style)` メソッドでステータスを更新
- `compose()` メソッドでウィジェットを配置
- 起動時に入力エリアにフォーカスを設定

**完了条件:** `python app.py` でTUIが表示され、入力エリアにテキストが入力でき、Tab で方向が切り替わること

---

### Task 2-2: 翻訳実行の接続
**入力:** Task 1-4, Task 2-1 完了済み  
**成果物:** `app.py` に翻訳ロジックを接続  
**内容:**
- `__init__` で `CodeTranslator` インスタンスを生成
- `on_mount()` で `check_connection()` を呼び、結果をステータスバーに表示
  - 接続失敗時は出力エリアにセットアップ手順を表示
- `action_translate()` を実装
  - 入力エリアからテキストを取得
  - 空文字列の場合は何もしない
  - ステータスバーを「⏳ 翻訳中...」に更新
  - `_run_translation()` を呼び出す
- `_run_translation()` を `@work(thread=True)` デコレータ付きで実装
  - バックグラウンドスレッドで `translator.translate()` を実行
  - 完了後 `call_from_thread()` で `_display_result()` を呼び出す
- `_display_result(result)` を実装
  - 出力エリアをクリアし、翻訳結果を表示
  - ステータスバーを「✓ 翻訳完了」に更新
- キーバインド `Ctrl+Enter` / `Ctrl+J` → `action_translate` を設定

**完了条件:** テキストを入力して Ctrl+J を押すと翻訳結果が出力エリアに表示されること

---

### Task 2-3: クリップボードコピーとクリア機能
**入力:** Task 2-2 完了済み  
**成果物:** `app.py` にコピー・クリア機能を追加  
**内容:**
- `_last_result` インスタンス変数を追加（直前の翻訳結果を保持）
- `_display_result()` で `_last_result` を更新
- `action_copy_result()` を実装
  - `_last_result` が None なら何もしない
  - `pyperclip.copy()` で翻訳結果をクリップボードにコピー
  - ステータスバーに「📋 コピーしました」を表示
  - pyperclip が使えない環境（xclip 未インストール等）ではエラーメッセージを表示
- `action_clear()` を実装
  - 入力エリアと出力エリアをクリア
  - `_last_result` を None にリセット
  - 入力エリアにフォーカスを戻す
- キーバインド設定
  - `Ctrl+Y` → `action_copy_result`
  - `Ctrl+L` → `action_clear`

**完了条件:** 翻訳後に Ctrl+Y でコピーされ、Ctrl+L で全体がクリアされること

---

### Task 2-4: 翻訳履歴パネルの実装
**入力:** Task 2-3 完了済み  
**成果物:** `app.py` に履歴パネルを追加  
**内容:**
- `history: list[TranslationResult]` インスタンス変数を追加
- `_display_result()` で翻訳結果を `history` に追加
- 履歴パネル用の UI を `compose()` に追加
  - `Vertical(id="history-panel")` に `Label("翻訳履歴")` と `RichLog(id="history-log")` を配置
  - CSS で `display: none` を初期状態とする
  - ボーダーカラーを `$warning`（他パネルと区別）
- `action_toggle_history()` を実装
  - 履歴パネルの `display` を toggle
  - 表示時に `history` の直近20件を逆順で `history-log` に書き込む
  - 各エントリの表示: `--- #N (日→英) ---` + 原文（80文字まで）+ 翻訳文（80文字まで）
- キーバインド `Ctrl+H` → `action_toggle_history` を設定

**完了条件:** 翻訳を数回実行した後、Ctrl+H で履歴パネルが表示され、過去の翻訳が一覧できること

---

### Task 2-5: Footer にキーバインドヘルプを表示
**入力:** Task 2-4 完了済み  
**成果物:** `app.py` の BINDINGS 定義を整理  
**内容:**
- `BINDINGS` リストを整理し、すべてのキーバインドに適切な `show` フラグを設定
  - 表示する: 翻訳(Ctrl+J), 方向切替(Tab), コピー(Ctrl+Y), 履歴(Ctrl+H), クリア(Ctrl+L), 終了(Ctrl+Q)
  - 非表示: Ctrl+Enter（Ctrl+J と同じ動作のエイリアス）
- `Header` の TITLE と SUB_TITLE を設定
  - TITLE: "CodeTranslate"
  - SUB_TITLE: "TranslateGemma コーディング翻訳"
- 各 `Binding` の `description` を簡潔な日本語に統一

**完了条件:** 画面下部のフッターに全操作のキーバインドが表示されること

---

## Phase 3: 品質向上

### Task 3-1: 翻訳エンジンのユニットテスト
**入力:** Phase 1 完了済み  
**成果物:** `tests/test_translator.py`  
**内容:**
- `tests/` ディレクトリと `conftest.py` を作成
- `test_protect_code_blocks()`: コードブロック保護が正しく動作するか
  - インラインコード `` `code` `` が保護される
  - マルチラインブロック ` ```python\ncode\n``` ` が保護される
  - コードブロックが無いテキストはそのまま
  - 複数のコードブロックが混在するケース
- `test_restore_code_blocks()`: プレースホルダーが正しく復元されるか
- `test_build_prompt_ja_to_en()`: 日→英プロンプトが正しい形式か
  - "Japanese" と "English" が含まれる
  - 入力テキストが含まれる
  - コーディング文脈指示が含まれる
- `test_build_prompt_en_to_ja()`: 英→日プロンプトが正しい形式か
- `test_load_glossary()`: 辞書が正しく読み込まれるか
  - 正常な JSON ファイル
  - ファイルが存在しない場合のフォールバック
- `test_build_glossary_hint()`: 辞書ヒント文字列が正しく生成されるか
  - 30件上限が適用されるか
- `test_translate_empty_string()`: 空文字列で空の結果が返るか
- Ollama への実際の接続が必要なテストには `@pytest.mark.integration` を付与

**完了条件:** `pytest tests/test_translator.py` が全件パスすること（integration テストは除く）

---

### Task 3-2: 用語辞書の拡充と検証
**入力:** Task 1-3 完了済みの `glossary.json`  
**成果物:** 拡充された `glossary.json` + `tests/test_glossary.py`  
**内容:**
- `glossary.json` の `ja_to_en` を以下のカテゴリで拡充（合計150語程度）
  - Web 開発系: サーバーサイド→server-side, フロントエンド→frontend 等
  - DB 系: テーブル→table, クエリ→query, インデックス→index 等
  - インフラ系: ロードバランサー→load balancer, オートスケール→auto scaling 等
  - AI/ML 系: モデル→model, 推論→inference, 学習→training 等
- `en_to_ja` を50語程度に拡充
- `preserve_as_is` に不足している固有名詞を追加
- `tests/test_glossary.py` を作成
  - JSON の構文が正しいか
  - `ja_to_en` と `en_to_ja` の整合性チェック（キーと値が逆転しているべき項目の確認）
  - `preserve_as_is` に重複がないか

**完了条件:** テストがパスし、辞書が150語以上収録されていること

---

### Task 3-3: エッジケース対応
**入力:** Phase 1, Phase 2 完了済み  
**成果物:** `translator.py` と `app.py` の修正  
**内容:**
- 非常に長いテキスト（5000文字以上）の場合の処理
  - 入力テキストが長すぎる場合にステータスバーに警告を表示
  - TranslateGemma のコンテキスト長（128K）を超えることはまず無いが、応答時間の目安を表示
- コードブロックのみの入力（翻訳対象の自然言語が無い場合）
  - 「翻訳対象のテキストがありません」と表示
- 翻訳結果が空の場合のハンドリング
- TranslateGemma が余計な説明文を付けて返す場合の後処理
  - "Here is the translation:" 等のプレフィックスを除去
- 入力中に改行を含むテキストの正しい処理

**完了条件:** 上記の各エッジケースで適切なメッセージが表示され、アプリがクラッシュしないこと

---

## Phase 4: 配布準備

### Task 4-1: pyproject.toml の完成とパッケージ化
**入力:** Phase 1〜3 完了済み  
**成果物:** 完成した `pyproject.toml`、動作確認済みのパッケージ  
**内容:**
- `pyproject.toml` を完成させる
  - `[project]` セクション: name, version, description, requires-python, dependencies, license
  - `[project.scripts]` セクション: `codetranslate = "app:main"` エントリポイント
  - `[build-system]` セクション: setuptools 設定
- `glossary.json` がパッケージに同梱されるよう `package_data` を設定
- `pip install -e .` でインストールし、`codetranslate` コマンドで起動できることを確認

**完了条件:** `pip install -e .` → `codetranslate` でアプリが起動すること

---

### Task 4-2: README の最終化
**入力:** 全 Phase 完了済み  
**成果物:** 完成した `README.md`  
**内容:**
- セットアップ手順の最終確認・修正
- スクリーンショット用の説明（実際のスクリーンショットは手動で追加）
- トラブルシューティングセクションの追加
  - Ollama が起動しない場合
  - モデルのダウンロードが失敗する場合
  - VRAM 不足の場合（4B モデルへのフォールバック手順）
  - クリップボードが動作しない場合
- 用語辞書のカスタマイズ方法の説明
- ライセンス表記

**完了条件:** README だけを読んで、ゼロからアプリをセットアップ・起動できること

---

## タスク依存関係

```
Phase 0
  └─ ~~Task 0-1~~ ✅

Phase 1（翻訳エンジン）
  ├─ Task 1-1（基本翻訳）
  ├─ Task 1-2（コード保護）    ← 1-1 に依存
  ├─ Task 1-3（用語辞書）      ← 1-2 に依存
  └─ Task 1-4（エラー処理）    ← 1-3 に依存

Phase 2（TUI）
  ├─ Task 2-1（レイアウト）
  ├─ Task 2-2（翻訳接続）      ← 1-4, 2-1 に依存
  ├─ Task 2-3（コピー/クリア） ← 2-2 に依存
  ├─ Task 2-4（履歴）          ← 2-3 に依存
  └─ Task 2-5（フッター）      ← 2-4 に依存

Phase 3（品質向上）
  ├─ Task 3-1（ユニットテスト） ← Phase 1 に依存
  ├─ Task 3-2（辞書拡充）       ← 1-3 に依存
  └─ Task 3-3（エッジケース）   ← Phase 1, 2 に依存

Phase 4（配布準備）
  ├─ Task 4-1（パッケージ化）   ← Phase 1〜3 に依存
  └─ Task 4-2（README）         ← 全タスクに依存
```

---

## サマリー

| Phase | タスク数 | 完了 | 進捗 | 概要 |
|-------|---------|------|------|------|
| Phase 0 | 1 | 1 | 100% | プロジェクト初期化 |
| Phase 1 | 4 | 0 | 0% | 翻訳エンジン |
| Phase 2 | 5 | 0 | 0% | TUI アプリケーション |
| Phase 3 | 3 | 0 | 0% | 品質向上 |
| Phase 4 | 2 | 0 | 0% | 配布準備 |
| **合計** | **15** | **1** | **6.7%** | |
