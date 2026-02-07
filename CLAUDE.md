# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CodeTranslate is a TUI-based Japanese<->English translation tool using TranslateGemma models (local Ollama). It's optimized for translating Claude Code/OpenCode input/output with code block protection.

## Development Commands

```bash
# Install in editable mode
pip install -e .

# Run the TUI application
codetranslate
# or
python app.py

# Run all tests
pytest

# Run specific test file
pytest tests/test_translator.py

# Run with verbose output
pytest -v

# Run integration tests (requires Ollama running)
pytest -m integration
```

## Architecture

The project consists of two main modules:

### `translator.py` - Core Translation Engine

- **CodeTranslator**: Main class that handles translation via Ollama's TranslateGemma models
- **TranslationResult**: Dataclass for translation results (original, translated, direction, error flag)

Key features:
- **Code block protection**: Replaces code blocks (inline `code` and multiline ```code```) with `__CODE_BLOCK_N__` placeholders before translation, restores them after
- **Glossary support**: Loads `glossary.json` for technical term translation hints
- **Model flexibility**: Uses `TRANSLATEGEMMA_MODEL` env var or defaults to `translategemma:12b`

Translation flow:
1. `_protect_code_blocks()` - extracts code to placeholders
2. `_build_prompt()` - creates TranslateGemma prompt with glossary hints
3. `ollama.chat()` - calls local Ollama API
4. `_restore_code_blocks()` - restores original code blocks

### `app.py` - Textual TUI Application

- **CodeTranslateApp**: Main Textual app with input/output areas
- **DirectionToggle**: Widget showing translation direction (ja_to_en / en_to_ja)
- **StatusBar**: Widget showing translation status

Key bindings:
- `Ctrl+Enter` / `Ctrl+J` - Execute translation
- `Tab` - Toggle translation direction
- `Ctrl+Y` - Copy result to clipboard
- `Ctrl+H` - Toggle history panel
- `Ctrl+L` - Clear input/output
- `Ctrl+Q` - Quit

## Glossary Format

`glossary.json` supports multiple formats:

```json
{
  "ja_to_en": {"term": "translation"},
  "en_to_ja": {"term": "translation"},
  "preserve_as_is": ["API", "JSON"]
}
```

Or nested format:
```json
{
  "term": {
    "ja_to_en": "translation",
    "en_to_ja": "translation",
    "preserve_as_is": true
  }
}
```

### Asymmetric Glossary Design

The glossary is intentionally asymmetric: `ja_to_en` contains more comprehensive technical terms than `en_to_ja`. This design choice reflects the primary use case of translating Japanese technical documentation to English, where precise technical terminology is critical.

- **ja_to_en**: Comprehensive technical term dictionary (150+ terms)
- **en_to_ja**: Focused subset of essential reverse translations (50+ terms)
- **preserve_as_is**: Terms that should never be translated (API names, protocols, etc.)

When adding new terms, prioritize `ja_to_en` for technical terminology. Only add `en_to_ja` entries if the reverse translation is frequently needed or essential for the target audience.

## Testing

Tests use pytest with pytest-mock. Key fixtures in `tests/conftest.py`:
- `mock_ollama_chat` - mocks ollama.chat() calls
- `mock_ollama_list` - mocks ollama.list() for connection tests

Integration tests (marked with `@pytest.mark.integration`) require actual Ollama connection.

## Environment

- Python 3.10+ required
- Uses `.venv` for virtual environment (active)
- `venv` is legacy - ignore
