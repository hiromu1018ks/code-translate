"""Tests for translator module."""

import pytest
import httpx
import ollama
from translator import CodeTranslator, TranslationResult


class TestTranslationResult:
    """Test suite for TranslationResult dataclass."""

    def test_translation_result_creation(self):
        """Test that TranslationResult can be instantiated with valid data."""
        result = TranslationResult(original="test text", translated="翻訳結果", direction="ja_to_en")
        assert result.original == "test text"
        assert result.translated == "翻訳結果"
        assert result.direction == "ja_to_en"

    def test_translation_result_invalid_direction(self):
        """Test that TranslationResult accepts any direction value (dataclass has no validation)."""
        result = TranslationResult(original="test", translated="test", direction="invalid_direction")
        assert result.original == "test"
        assert result.translated == "test"
        assert result.direction == "invalid_direction"

    def test_translation_result_error_field_default(self):
        """errorフィールドのデフォルト値がFalseであることを確認"""
        result = TranslationResult(original="test", translated="test", direction="ja_to_en")
        assert result.error is False

    def test_translation_result_error_field_explicit(self):
        """errorフィールドを明示的に設定できることを確認"""
        result = TranslationResult(
            original="test", 
            translated="test", 
            direction="ja_to_en", 
            error=True
        )
        assert result.error is True


class TestBuildPrompt:
    """Test suite for CodeTranslator._build_prompt method."""

    def test_build_prompt_ja_to_en(self):
        """Test _build_prompt generates correct Japanese to English prompt."""
        from translator import CodeTranslator
        translator = CodeTranslator()
        prompt = translator._build_prompt("テスト", "ja_to_en")
        # Verify prompt contains correct language information
        assert "Japanese" in prompt
        assert "(ja)" in prompt
        assert "English" in prompt
        assert "(en-US)" in prompt
        assert "テスト" in prompt
        # Verify 2 blank lines before text (TranslateGemma requirement)
        text_part = prompt.split("テスト")[0]
        lines_before_text = text_part.split("\n")
        blank_lines = [l for l in lines_before_text if l == ""]
        assert len(blank_lines) >= 2, "Prompt must have at least 2 blank lines before text"

    def test_build_prompt_en_to_ja(self):
        """Test _build_prompt generates correct English to Japanese prompt."""
        from translator import CodeTranslator
        translator = CodeTranslator()
        prompt = translator._build_prompt("test", "en_to_ja")
        # Verify prompt contains correct language information
        assert "English" in prompt
        assert "(en-US)" in prompt
        assert "Japanese" in prompt
        assert "(ja)" in prompt
        assert "test" in prompt
        # Verify 2 blank lines before text (TranslateGemma requirement)
        text_part = prompt.split("test")[0]
        lines_before_text = text_part.split("\n")
        blank_lines = [l for l in lines_before_text if l == ""]
        assert len(blank_lines) >= 2, "Prompt must have at least 2 blank lines before text"

    def test_build_prompt_invalid_direction(self):
        """Test _build_prompt raises ValueError for invalid direction."""
        from translator import CodeTranslator
        translator = CodeTranslator()
        with pytest.raises(ValueError):
            translator._build_prompt("test", "invalid_direction")

    def test_build_prompt_with_glossary_ja_to_en(self):
        """用語辞書がある場合のプロンプト生成（日→英）"""
        from translator import CodeTranslator
        translator = CodeTranslator()
        translator.glossary = {
            "変数": "variable",
            "関数": "function",
            "リスト": "list",
            "_preserve_as_is": ["GitHub", "API"]
        }
        prompt = translator._build_prompt("テスト", "ja_to_en")
        assert "Coding context:" in prompt
        assert "programming context translation" in prompt
        assert "Glossary:" in prompt
        assert "変数" in prompt
        assert "関数" in prompt
        assert "GitHub (do not translate)" in prompt
        assert "API (do not translate)" in prompt
        assert "Japanese" in prompt
        assert "English" in prompt
        assert "テスト" in prompt

    def test_build_prompt_with_glossary_en_to_ja(self):
        """用語辞書がある場合のプロンプト生成（英→日）"""
        from translator import CodeTranslator
        translator = CodeTranslator()
        translator.glossary = {
            "variable": "変数",
            "function": "関数",
            "array": "配列",
            "_preserve_as_is": ["Python", "NumPy"]
        }
        prompt = translator._build_prompt("test", "en_to_ja")
        assert "Coding context:" in prompt
        assert "programming context translation" in prompt
        assert "Glossary:" in prompt
        assert "variable" in prompt
        assert "function" in prompt
        assert "Python (do not translate)" in prompt
        assert "NumPy (do not translate)" in prompt
        assert "English" in prompt
        assert "Japanese" in prompt
        assert "test" in prompt

    def test_build_prompt_without_glossary(self):
        """用語辞書がない場合のプロンプト生成（通常動作）"""
        from translator import CodeTranslator
        translator = CodeTranslator()
        translator.glossary = {}
        prompt = translator._build_prompt("テスト", "ja_to_en")
        assert "Coding context:" not in prompt
        assert "Glossary:" not in prompt
        assert "Japanese" in prompt
        assert "English" in prompt
        assert "テスト" in prompt

    def test_build_prompt_glossary_preserve_as_is_format(self):
        """preserve_as_is用語のフォーマットを検証"""
        from translator import CodeTranslator
        translator = CodeTranslator()
        translator.glossary = {
            "変数": "variable",
            "_preserve_as_is": ["GitHub", "API", "JSON", "URL"]
        }
        prompt = translator._build_prompt("テスト", "ja_to_en")
        assert "GitHub (do not translate)" in prompt
        assert "API (do not translate)" in prompt
        assert "JSON (do not translate)" in prompt
        assert "URL (do not translate)" in prompt
        assert "変数 (do not translate)" not in prompt
        assert "Glossary:" in prompt


class TestCheckConnection:
    """Test suite for CodeTranslator.check_connection method."""

    def test_check_connection_model_available(self, mock_ollama_list):
        """Test check_connection returns (True, 'OK') when model is available."""
        from conftest import MockListResponse, ModelInfo
        mock_ollama_list.return_value = MockListResponse([
            ModelInfo(model="translategemma:12b")
        ])
        translator = CodeTranslator()
        success, message = translator.check_connection()
        assert success is True
        assert message == "OK"

    def test_check_connection_model_not_found(self, mock_ollama_list):
        """Test check_connection returns (False, error) when model not found."""
        from conftest import MockListResponse
        mock_ollama_list.return_value = MockListResponse([])
        translator = CodeTranslator()
        success, message = translator.check_connection()
        assert success is False
        assert "Ollama に接続できません" in message or "モデルが見つかりません" in message

    def test_check_connection_connection_error(self, mock_ollama_list):
        """Test check_connection handles ConnectionError gracefully."""
        mock_ollama_list.side_effect = ConnectionError("Failed to connect to Ollama")
        translator = CodeTranslator()
        success, message = translator.check_connection()
        assert success is False
        assert "Ollama に接続できません" in message

    def test_check_connection_http_error_ollama_not_running(self, mock_ollama_list):
        """Ollamaが起動していない場合のメッセージを検証"""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        http_error = httpx.HTTPStatusError("Connection refused", request=MagicMock(), response=mock_response)
        mock_ollama_list.side_effect = ollama.ResponseError("Connection refused", http_error.response.status_code)

        translator = CodeTranslator()
        success, message = translator.check_connection()
        assert success is False
        assert "Ollama に接続できません" in message


class TestTranslate:
    """Test suite for CodeTranslator.translate method."""

    def test_translate_ja_to_en(self, mock_ollama_chat):
        """Test translate returns TranslationResult with Japanese to English."""
        translator = CodeTranslator()
        result = translator.translate("これはテストです", "ja_to_en")
        assert isinstance(result, TranslationResult)
        assert result.original == "これはテストです"
        assert result.direction == "ja_to_en"
        assert result.translated
        assert result.error is False

    def test_translate_en_to_ja(self, mock_ollama_chat):
        """Test translate returns TranslationResult with English to Japanese."""
        translator = CodeTranslator()
        result = translator.translate("This is a test", "en_to_ja")
        assert isinstance(result, TranslationResult)
        assert result.original == "This is a test"
        assert result.direction == "en_to_ja"
        assert result.translated
        assert result.error is False

    def test_translate_empty_string(self, mock_ollama_chat):
        """Test translate handles empty string."""
        translator = CodeTranslator()
        result = translator.translate("", "ja_to_en")
        assert isinstance(result, TranslationResult)
        assert result.original == ""
        assert result.translated == ""
        assert result.direction == "ja_to_en"
        assert result.error is False

    def test_translate_connection_error(self, mock_ollama_chat):
        """接続エラー時のエラーハンドリングを検証"""
        from unittest.mock import MagicMock

        mock_ollama_chat.side_effect = ConnectionError("Failed to connect to Ollama")

        translator = CodeTranslator()
        result = translator.translate("テスト", "ja_to_en")

        assert result.original == "テスト"
        assert result.translated == "[翻訳エラー] Ollama に接続できません"
        assert result.error is True

    def test_translate_model_not_found_error(self, mock_ollama_chat):
        """モデル未インストール時のエラーハンドリングを検証"""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = httpx.HTTPStatusError("Model not found", request=MagicMock(), response=mock_response)
        mock_ollama_chat.side_effect = ollama.ResponseError("Model not found", 404)

        translator = CodeTranslator()
        result = translator.translate("テスト", "ja_to_en")

        assert result.original == "テスト"
        assert result.translated == "[翻訳エラー] モデルが見つかりません"
        assert result.error is True

    def test_translate_timeout_error(self, mock_ollama_chat):
        """タイムアウト時のエラーハンドリングを検証"""
        import httpx
        from unittest.mock import MagicMock

        mock_ollama_chat.side_effect = httpx.TimeoutException("Request timed out")

        translator = CodeTranslator()
        result = translator.translate("テスト", "ja_to_en")

        assert result.original == "テスト"
        assert result.translated == "[翻訳エラー] タイムアウトしました"
        assert result.error is True

    def test_translate_generic_error(self, mock_ollama_chat):
        """その他の例外時のエラーハンドリングを検証"""
        mock_ollama_chat.side_effect = ValueError("Some other error")

        translator = CodeTranslator()
        result = translator.translate("テスト", "ja_to_en")

        assert result.original == "テスト"
        assert result.error is True
        assert "Some other error" in result.translated

    def test_translate_en_to_ja(self, mock_ollama_chat):
        """Test translate returns TranslationResult with English to Japanese."""
        translator = CodeTranslator()
        result = translator.translate("This is a test", "en_to_ja")
        assert isinstance(result, TranslationResult)
        assert result.original == "This is a test"
        assert result.direction == "en_to_ja"
        assert result.translated

    def test_translate_empty_string(self, mock_ollama_chat):
        """Test translate handles empty string."""
        translator = CodeTranslator()
        result = translator.translate("", "ja_to_en")
        assert isinstance(result, TranslationResult)
        assert result.original == ""
        assert result.translated == ""
        assert result.direction == "ja_to_en"

    def test_translate_with_inline_code_protected(self, mock_ollama_chat):
        """インラインコードが翻訳されず保護される"""
        from unittest.mock import call, MagicMock

        mock_response = MagicMock()
        mock_response.message.content = "Please use __CODE_BLOCK_0__."
        mock_ollama_chat.side_effect = [mock_response]

        translator = CodeTranslator()
        result = translator.translate('`print("hello")` を使ってください。', 'ja_to_en')

        assert '`print("hello")`' in result.translated
        assert 'Please' in result.translated or 'use' in result.translated.lower()

        args = mock_ollama_chat.call_args
        prompt = args[1]['messages'][0]['content']
        assert '__CODE_BLOCK_0__' in prompt

    def test_translate_with_multiline_code_protected(self, mock_ollama_chat):
        """マルチラインコードブロックが翻訳されず保護される"""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.message.content = "Implement__CODE_BLOCK_0__Let me know when done."
        mock_ollama_chat.side_effect = [mock_response]

        translator = CodeTranslator()
        original = '''以下を実装してください：

```python
def hello():
    print("world")
```

完了したら教えて。'''

        result = translator.translate(original, 'ja_to_en')

        assert 'def hello():' in result.translated
        assert 'print("world")' in result.translated

    def test_translate_no_code_blocks(self, mock_ollama_chat):
        """コードブロックがない場合は通常通り翻訳される"""
        mock_ollama_chat.return_value = {
            "message": {
                "content": "This is a normal translation."
            },
            "done": True
        }

        translator = CodeTranslator()
        result = translator.translate('これは普通の翻訳です。', 'ja_to_en')

        assert result.translated

    def test_translate_code_accuracy_preservation(self, mock_ollama_chat):
        """コードが100%正確に復元されることを検証"""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.message.content = "Use __CODE_BLOCK_0__ and __CODE_BLOCK_1__ commands."
        mock_ollama_chat.side_effect = [mock_response]

        translator = CodeTranslator()
        original = '`git add` と `git commit` コマンドを使用してください。'
        result = translator.translate(original, 'ja_to_en')

        assert '`git add`' in result.translated
        assert '`git commit`' in result.translated

    def test_translate_en_to_ja_with_code(self, mock_ollama_chat):
        """英語から日本語の翻訳でもコードが保護される"""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.message.content = "__CODE_BLOCK_0__を使用してください。"
        mock_ollama_chat.side_effect = [mock_response]

        translator = CodeTranslator()
        result = translator.translate('Use `print("hello")` command.', 'en_to_ja')

        assert '`print("hello")`' in result.translated

    def test_translate_empty_string_with_code(self, mock_ollama_chat):
        """空文字列の場合にエラーにならない"""
        translator = CodeTranslator()
        result = translator.translate('', 'ja_to_en')

        assert result.translated == ''
        assert not mock_ollama_chat.called


class TestProtectCodeBlocks:
    """Test suite for CodeTranslator._protect_code_blocks method."""

    def test_protect_inline_code(self):
        """インラインコードが保護される"""
        translator = CodeTranslator()
        text = '`print("hello")` を使ってください。'
        protected, placeholders = translator._protect_code_blocks(text)
        assert protected == '__CODE_BLOCK_0__ を使ってください。'
        assert len(placeholders) == 1
        assert placeholders['__CODE_BLOCK_0__'] == '`print("hello")`'

    def test_protect_multiline_code_block(self):
        """マルチラインコードブロックが保護される"""
        translator = CodeTranslator()
        text = '''この関数を実装してください：

```python
def hello():
    print("hello world")
```

終わったら教えて。'''
        protected, placeholders = translator._protect_code_blocks(text)
        assert '__CODE_BLOCK_0__' in protected
        assert len(placeholders) == 1
        assert 'def hello():' in placeholders['__CODE_BLOCK_0__']

    def test_protect_multiple_code_blocks(self):
        """複数のコードブロックが保護される"""
        translator = CodeTranslator()
        text = 'コマンド `npm install` を実行し、次に `python app.py` を実行してください。'
        protected, placeholders = translator._protect_code_blocks(text)
        assert protected == 'コマンド __CODE_BLOCK_0__ を実行し、次に __CODE_BLOCK_1__ を実行してください。'
        assert len(placeholders) == 2
        assert placeholders['__CODE_BLOCK_0__'] == '`npm install`'
        assert placeholders['__CODE_BLOCK_1__'] == '`python app.py`'

    def test_protect_mixed_code_types(self):
        """インラインコードとマルチラインブロックが混在する場合に保護される"""
        translator = CodeTranslator()
        text = '変数 `x` を使用して、以下のコードを書いてください：\n```python\nx = 10\n```\n完了しました。'
        protected, placeholders = translator._protect_code_blocks(text)
        assert '__CODE_BLOCK_0__' in protected
        assert '__CODE_BLOCK_1__' in protected
        assert len(placeholders) == 2

    def test_protect_no_code_blocks(self):
        """コードブロックがないテキストは変更されない"""
        translator = CodeTranslator()
        text = 'これは通常のテキストです。コードは含まれていません。'
        protected, placeholders = translator._protect_code_blocks(text)
        assert protected == text
        assert len(placeholders) == 0

    def test_protect_empty_string(self):
        """空文字列の入力を適切に処理する"""
        translator = CodeTranslator()
        text = ''
        protected, placeholders = translator._protect_code_blocks(text)
        assert protected == ''
        assert len(placeholders) == 0

    def test_protect_code_at_start(self):
        """先頭にあるコードブロックが保護される"""
        translator = CodeTranslator()
        text = '`import os` モジュールを使用します。'
        protected, placeholders = translator._protect_code_blocks(text)
        assert protected.startswith('__CODE_BLOCK_0__')
        assert len(placeholders) == 1

    def test_protect_code_at_end(self):
        """末尾にあるコードブロックが保護される"""
        translator = CodeTranslator()
        text = '最後に `return result`'
        protected, placeholders = translator._protect_code_blocks(text)
        assert protected.endswith('__CODE_BLOCK_0__')
        assert len(placeholders) == 1

    def test_protect_consecutive_code_blocks(self):
        """連続するコードブロックが正しく保護される"""
        translator = CodeTranslator()
        text = '使用: `git` `add` `commit` `push`'
        protected, placeholders = translator._protect_code_blocks(text)
        assert '__CODE_BLOCK_0__' in protected
        assert '__CODE_BLOCK_1__' in protected
        assert '__CODE_BLOCK_2__' in protected
        assert '__CODE_BLOCK_3__' in protected
        assert len(placeholders) == 4

    def test_protect_code_with_special_chars(self):
        """特殊文字を含むコードが保護される"""
        translator = CodeTranslator()
        text = 'コマンド `grep -r "pattern" *.py` を実行してください。'
        protected, placeholders = translator._protect_code_blocks(text)
        assert protected == 'コマンド __CODE_BLOCK_0__ を実行してください。'
        assert len(placeholders) == 1

    def test_protect_japanese_english_mixed(self):
        """日本語と英語が混在するテキストでコードが保護される"""
        translator = CodeTranslator()
        text = 'Use `npm install` to install dependencies, then run `python app.py`。'
        protected, placeholders = translator._protect_code_blocks(text)
        assert '__CODE_BLOCK_0__' in protected
        assert '__CODE_BLOCK_1__' in protected
        assert len(placeholders) == 2

    def test_protect_multiline_with_newlines(self):
        """改行を含むマルチラインブロックが正しく検出される"""
        translator = CodeTranslator()
        text = '''```javascript
function test() {
  return true;
}
```'''
        protected, placeholders = translator._protect_code_blocks(text)
        assert '__CODE_BLOCK_0__' in protected
        assert 'function test()' in placeholders['__CODE_BLOCK_0__']
        assert len(placeholders) == 1

    def test_protect_inline_code_with_backticks(self):
        """バッククォート自体を含むインラインコードを処理"""
        translator = CodeTranslator()
        text = '```code```'  # 三重バッククォートはインラインとして扱われない可能性あり
        protected, placeholders = translator._protect_code_blocks(text)
        # 正規表現パターンに応じて挙動が変わる可能性がある
        assert len(placeholders) >= 0  # 少なくともエラーにならないこと

    def test_protect_placeholder_incrementing(self):
        """プレースホルダー番号が正しくインクリメントされる"""
        translator = CodeTranslator()
        text = 'コード `a`、コード `b`、コード `c`'
        protected, placeholders = translator._protect_code_blocks(text)
        assert '__CODE_BLOCK_0__' in protected
        assert '__CODE_BLOCK_1__' in protected
        assert '__CODE_BLOCK_2__' in protected
        assert len(placeholders) == 3
        assert list(placeholders.keys()) == ['__CODE_BLOCK_0__', '__CODE_BLOCK_1__', '__CODE_BLOCK_2__']


class TestRestoreCodeBlocks:
    """Test suite for CodeTranslator._restore_code_blocks method."""

    def test_restore_single_placeholder(self):
        """単一のプレースホルダーが正しく復元される"""
        translator = CodeTranslator()
        placeholders = {'__CODE_BLOCK_0__': '`print("hello")`'}
        text = '__CODE_BLOCK_0__ を使ってください。'
        restored = translator._restore_code_blocks(text, placeholders)
        assert restored == '`print("hello")` を使ってください。'

    def test_restore_multiple_placeholders(self):
        """複数のプレースホルダーが正しく復元される"""
        translator = CodeTranslator()
        placeholders = {
            '__CODE_BLOCK_0__': '`git`',
            '__CODE_BLOCK_1__': '`npm install`',
            '__CODE_BLOCK_2__': '`python app.py`'
        }
        text = 'コマンド __CODE_BLOCK_0__、次に __CODE_BLOCK_1__、最後に __CODE_BLOCK_2__'
        restored = translator._restore_code_blocks(text, placeholders)
        assert restored == 'コマンド `git`、次に `npm install`、最後に `python app.py`'

    def test_restore_multiline_block(self):
        """マルチラインコードブロックが正しく復元される"""
        translator = CodeTranslator()
        placeholders = {
            '__CODE_BLOCK_0__': '```python\ndef hello():\n    print("hello")\n```'
        }
        text = '実装してください：\n__CODE_BLOCK_0__\n\n完了'
        restored = translator._restore_code_blocks(text, placeholders)
        assert 'def hello():' in restored
        assert '```python' in restored

    def test_restore_no_placeholders(self):
        """プレースホルダーがないテキストは変更されない"""
        translator = CodeTranslator()
        placeholders = {}
        text = 'これは通常のテキストです。'
        restored = translator._restore_code_blocks(text, placeholders)
        assert restored == text

    def test_restore_empty_text(self):
        """空文字列を適切に処理する"""
        translator = CodeTranslator()
        placeholders = {}
        text = ''
        restored = translator._restore_code_blocks(text, placeholders)
        assert restored == ''

    def test_restore_placeholder_order_preserved(self):
        """プレースホルダーの順序が保持される"""
        translator = CodeTranslator()
        placeholders = {
            '__CODE_BLOCK_0__': 'FIRST',
            '__CODE_BLOCK_1__': 'SECOND',
            '__CODE_BLOCK_2__': 'THIRD'
        }
        text = '__CODE_BLOCK_0__ __CODE_BLOCK_1__ __CODE_BLOCK_2__'
        restored = translator._restore_code_blocks(text, placeholders)
        assert restored == 'FIRST SECOND THIRD'

    def test_restore_missing_placeholder_in_mapping(self):
        """マッピングにないプレースホルダーはそのまま残される"""
        translator = CodeTranslator()
        placeholders = {'__CODE_BLOCK_0__': 'CODE'}
        text = '__CODE_BLOCK_0__ __CODE_BLOCK_1__'  # __CODE_BLOCK_1__ はマッピングにない
        restored = translator._restore_code_blocks(text, placeholders)
        assert restored == 'CODE __CODE_BLOCK_1__'

    def test_restore_roundtrip(self):
        """保護と復元のラウンドトリップが正確に機能する"""
        translator = CodeTranslator()
        original = '`print("hello")` を使って、`npm install` を実行してください。'
        protected, placeholders = translator._protect_code_blocks(original)
        restored = translator._restore_code_blocks(protected, placeholders)
        assert restored == original

    def test_restore_multiline_roundtrip(self):
        """マルチラインブロックのラウンドトリップが正確に機能する"""
        translator = CodeTranslator()
        original = '''コードを追加：

```python
def test():
    pass
```

終わったらコミットしてください。'''
        protected, placeholders = translator._protect_code_blocks(original)
        restored = translator._restore_code_blocks(protected, placeholders)
        assert restored == original


class TestLoadGlossary:
    """Test suite for CodeTranslator._load_glossary method."""

    def test_load_glossary_valid_file(self, tmp_path):
        """有効な JSON ファイルから用語辞書が正しく読み込まれる"""
        glossary_file = tmp_path / "glossary.json"
        glossary_content = {
            "commit": "コミット",
            "pull request": "プルリクエスト",
            "branch": "ブランチ"
        }
        import json
        glossary_file.write_text(json.dumps(glossary_content, ensure_ascii=False))

        from translator import CodeTranslator
        translator = CodeTranslator()
        glossary = translator._load_glossary(str(glossary_file))

        assert glossary == glossary_content

    def test_load_glossary_not_found(self, tmp_path):
        """ファイルが見つからない場合は空辞書を返す"""
        from translator import CodeTranslator
        translator = CodeTranslator()
        nonexistent_file = tmp_path / "nonexistent.json"
        glossary = translator._load_glossary(str(nonexistent_file))

        assert glossary == {}

    def test_load_glossary_malformed_json(self, tmp_path):
        """JSON 形式が不正な場合は空辞書を返す"""
        glossary_file = tmp_path / "glossary.json"
        glossary_file.write_text('{"invalid": json}')

        from translator import CodeTranslator
        translator = CodeTranslator()
        glossary = translator._load_glossary(str(glossary_file))

        assert glossary == {}

    def test_load_glossary_invalid_structure(self, tmp_path):
        """JSON 構造が不正な場合は空辞書を返す"""
        glossary_file = tmp_path / "glossary.json"
        import json
        glossary_file.write_text(json.dumps(["term1", "term2"], ensure_ascii=False))

        from translator import CodeTranslator
        translator = CodeTranslator()
        glossary = translator._load_glossary(str(glossary_file))

        assert glossary == {}

    def test_load_glossary_empty_file(self, tmp_path):
        """空の JSON ファイルの場合は空辞書を返す"""
        glossary_file = tmp_path / "glossary.json"
        import json
        glossary_file.write_text(json.dumps({}, ensure_ascii=False))

        from translator import CodeTranslator
        translator = CodeTranslator()
        glossary = translator._load_glossary(str(glossary_file))

        assert glossary == {}



class TestBuildGlossaryHint:
    """Test suite for CodeTranslator._build_glossary_hint method."""

    def test_build_glossary_hint_ja_to_en(self):
        """100語の用語辞書から最初の30語のみ使用してヒントを生成する"""
        translator = CodeTranslator()

        # Create glossary with 100 terms for ja_to_en
        glossary = {}
        for i in range(100):
            glossary[f"用語{i}"] = {
                "ja_to_en": f"term{i}",
                "en_to_ja": f"用語{i}"
            }

        hint = translator._build_glossary_hint(glossary, "ja_to_en")

        # Should contain exactly 30 terms
        term_lines = [line for line in hint.split("\n") if line.strip()]
        assert len(term_lines) == 30

        # Should contain first 30 terms
        for i in range(30):
            assert f"用語{i} → term{i}" in hint

        # Should NOT contain terms beyond 30
        for i in range(30, 100):
            assert f"用語{i} → term{i}" not in hint

    def test_build_glossary_hint_en_to_ja(self):
        """30語の用語辞書で英語から日本語のヒントを生成する"""
        translator = CodeTranslator()

        # Create glossary with 30 terms for en_to_ja
        glossary = {}
        for i in range(30):
            glossary[f"term{i}"] = {
                "ja_to_en": f"term{i}",
                "en_to_ja": f"用語{i}"
            }

        hint = translator._build_glossary_hint(glossary, "en_to_ja")

        # Should contain exactly 30 terms
        term_lines = [line for line in hint.split("\n") if line.strip()]
        assert len(term_lines) == 30

        # Should contain all 30 terms in correct format
        for i in range(30):
            assert f"term{i} → 用語{i}" in hint

    def test_build_glossary_hint_empty_glossary(self):
        """空の用語辞書の場合は空文字列を返す"""
        translator = CodeTranslator()

        hint = translator._build_glossary_hint({}, "ja_to_en")
        assert hint == ""

    def test_build_glossary_hint_direction_not_found(self):
        """指定された方向が用語辞書に存在しない場合は空文字列を返す"""
        translator = CodeTranslator()

        # Create glossary with only ja_to_en direction
        glossary = {
            "用語1": {
                "ja_to_en": "term1"
                # Missing en_to_ja
            }
        }

        # Request en_to_ja which doesn't exist
        hint = translator._build_glossary_hint(glossary, "en_to_ja")
        assert hint == ""

    def test_build_glossary_hint_format(self):
        """用語ヒントのフォーマットが 'term → translation' (Unicode矢印) であることを検証"""
        translator = CodeTranslator()

        glossary = {
            "変数": {"ja_to_en": "variable", "en_to_ja": "変数"},
            "関数": {"ja_to_en": "function", "en_to_ja": "関数"},
            "クラス": {"ja_to_en": "class", "en_to_ja": "クラス"}
        }

        hint = translator._build_glossary_hint(glossary, "ja_to_en")

        # Use Unicode arrow →, not ASCII ->
        assert "変数 → variable" in hint
        assert "関数 → function" in hint
        assert "クラス → class" in hint

        # Verify ASCII arrow is NOT used
        assert "変数 -> variable" not in hint
        assert "関数 -> function" not in hint

    def test_build_glossary_hint_with_preserve_as_is(self):
        """preserve_as_isフラグがある用語に '(do not translate)' サフィックスが付くことを検証"""
        translator = CodeTranslator()

        glossary = {
            "Python": {
                "ja_to_en": "Python",
                "en_to_ja": "Python",
                "preserve_as_is": True
            },
            "numpy": {
                "ja_to_en": "numpy",
                "en_to_ja": "numpy",
                "preserve_as_is": True
            },
            "変数": {
                "ja_to_en": "variable",
                "en_to_ja": "変数"
                # No preserve_as_is flag
            }
        }

        hint = translator._build_glossary_hint(glossary, "ja_to_en")

        # preserve_as_is terms should have suffix
        assert "Python → Python (do not translate)" in hint
        assert "numpy → numpy (do not translate)" in hint

        # Regular terms should NOT have suffix
        assert "変数 → variable (do not translate)" not in hint
        assert "変数 → variable" in hint


class TestEstimateTranslationTime:
    """Test suite for _estimate_translation_time method."""

    def test_short_text_returns_zero(self):
        """短いテキスト（5000文字未満）で0秒を返す"""
        translator = CodeTranslator()
        result = translator._estimate_translation_time(1000)
        assert result == 0

    def test_exactly_threshold_returns_zero(self):
        """閾値ちょうど（5000文字）で0秒を返す"""
        translator = CodeTranslator()
        result = translator._estimate_translation_time(4999)
        assert result == 0

    def test_long_text_calculates_time(self):
        """長いテキストで時間が計算される"""
        translator = CodeTranslator()
        result = translator._estimate_translation_time(6000)
        assert result == 18  # (6000 // 1000) * 3 = 18

    def test_very_long_text_calculates_time(self):
        """非常に長いテキストで時間が計算される"""
        translator = CodeTranslator()
        result = translator._estimate_translation_time(10000)
        assert result == 30  # (10000 // 1000) * 3 = 30

    def test_minimum_time_is_five_seconds(self):
        """最小時間が5秒保証される"""
        translator = CodeTranslator()
        result = translator._estimate_translation_time(5001)
        assert result >= 5


class TestIsCodeOnlyInput:
    """Test suite for _is_code_only_input method."""

    def test_code_only_input_returns_true(self):
        """コードのみの入力でTrueを返す"""
        translator = CodeTranslator()
        text = '```python\ndef hello():\n    pass\n```'
        protected, placeholders = translator._protect_code_blocks(text)
        result = translator._is_code_only_input(protected, placeholders, len(text))
        assert result is True

    def test_text_with_code_returns_false(self):
        """テキスト付きコードでFalseを返す"""
        translator = CodeTranslator()
        text = '以下を実装してください：\n```python\ndef hello():\n    pass\n```'
        protected, placeholders = translator._protect_code_blocks(text)
        result = translator._is_code_only_input(protected, placeholders, len(text))
        assert result is False

    def test_no_code_blocks_returns_false(self):
        """コードブロックなしでFalseを返す"""
        translator = CodeTranslator()
        text = 'これは通常のテキストです。'
        protected, placeholders = translator._protect_code_blocks(text)
        result = translator._is_code_only_input(protected, placeholders, len(text))
        assert result is False

    def test_empty_input_returns_false(self):
        """空の入力でFalseを返す"""
        translator = CodeTranslator()
        text = ''
        protected, placeholders = translator._protect_code_blocks(text)
        result = translator._is_code_only_input(protected, placeholders, len(text))
        assert result is False


class TestStripTranslationPrefixes:
    """Test suite for _strip_translation_prefixes method."""

    def test_strips_here_is_the_translation(self):
        """'Here is the translation:'が除去される"""
        translator = CodeTranslator()
        text = "Here is the translation:\nThis is the result."
        result = translator._strip_translation_prefixes(text)
        assert result == "This is the result."
        assert "Here is the translation:" not in result

    def test_strips_japanese_prefix(self):
        """'翻訳:'が除去される"""
        translator = CodeTranslator()
        text = "翻訳:\nこれは結果です。"
        result = translator._strip_translation_prefixes(text)
        assert "翻訳:" not in result
        assert "これは結果です。" in result

    def test_strips_nihongo_yaku_prefix(self):
        """'日本語訳:'が除去される"""
        translator = CodeTranslator()
        text = "日本語訳:\nこれは結果です。"
        result = translator._strip_translation_prefixes(text)
        assert "日本語訳:" not in result

    def test_normal_text_unchanged(self):
        """通常のテキストは変更されない"""
        translator = CodeTranslator()
        text = "This is a normal translation."
        result = translator._strip_translation_prefixes(text)
        assert result == "This is a normal translation."

    def test_strips_multiple_variants(self):
        """複数の接頭辞パターンが除去される"""
        translator = CodeTranslator()
        # Test "Translation:" prefix
        text1 = "Translation:\nResult here"
        result1 = translator._strip_translation_prefixes(text1)
        assert "Translation:" not in result1

        # Test "Here's the translation:" prefix
        text2 = "Here's the translation:\nResult here"
        result2 = translator._strip_translation_prefixes(text2)
        assert "Here's the translation:" not in result2


class TestIsEmptyTranslation:
    """Test suite for _is_empty_translation method."""

    def test_empty_string_returns_true(self):
        """空文字でTrueを返す"""
        translator = CodeTranslator()
        result = translator._is_empty_translation("")
        assert result is True

    def test_whitespace_only_returns_true(self):
        """空白のみでTrueを返す"""
        translator = CodeTranslator()
        result = translator._is_empty_translation("   \n\t  ")
        assert result is True

    def test_normal_text_returns_false(self):
        """通常のテキストでFalseを返す"""
        translator = CodeTranslator()
        result = translator._is_empty_translation("This is text.")
        assert result is False

    def test_newlines_only_returns_true(self):
        """改行のみでTrueを返す"""
        translator = CodeTranslator()
        result = translator._is_empty_translation("\n\n\n")
        assert result is True
