# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-07
**Project:** CodeTranslate

## OVERVIEW

TUI-based Japanese⇔English translation tool using TranslateGemma 12B model (local Ollama). Optimized for Claude Code/OpenCode input/output with code block protection.

## STRUCTURE

```
./
├── app.py                  # TUI entry point (currently placeholder)
├── translator.py           # Core translation logic + code block protection
├── tests/                  # pytest tests with extensive mock coverage
├── docs/                   # Japanese specification docs
├── venv/                   # Virtual environment (legacy)
└── .venv/                  # Virtual environment (active)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Translation core | `translator.py` | CodeTranslator class + TranslationResult |
| Tests | `tests/` | Comprehensive unit tests with mocks |
| Spec docs | `docs/` | Japanese language spec and task lists |

## CODE MAP

| Symbol | Type | Location | Refs | Role |
|--------|------|----------|------|------|
| CodeTranslator | class | translator.py:23 | tests/ | Main translation engine |
| TranslationResult | dataclass | translator.py:10 | tests/ | Result container |
| check_connection | method | translator.py:125 | tests/ | Ollama health check |
| translate | method | translator.py:144 | tests/ | Main translation entry |
| _protect_code_blocks | method | translator.py:87 | tests/ | Code → placeholders |
| _restore_code_blocks | method | translator.py:110 | tests/ | Placeholders → code |

## CONVENTIONS

- **Code block protection**: All code (inline `` `code` `` and multiline ```code```) is replaced with `__CODE_BLOCK_N__` placeholders before translation, restored after
- **Prompt format**: Two blank lines required before text (TranslateGemma requirement)
- **Model selection**: Use `TRANSLATEGEMMA_MODEL` env var or defaults to `translategemma:12b`
- **Test comments**: Japanese descriptions in docstrings/tests

## ANTI-PATTERNS (THIS PROJECT)

- Never modify code blocks during translation (always protect/restore)
- Never call ollama.chat with empty text
- Never suppress exceptions in translate() - wrap in TranslationResult

## COMMANDS

```bash
# Install
pip install -e .

# Run TUI
codetranslate  # or python app.py

# Run tests
pytest

# Check Ollama models
curl http://localhost:11434/api/tags
```

## NOTES

- `app.py` is currently a stub (pass only) - TUI not yet implemented
- Tests use pytest-mock fixtures (mock_ollama_chat, mock_ollama_list)
- Supports model switching via env var: `TRANSLATEGEMMA_MODEL=translategemma:4b codetranslate`
- Code pattern: `r"(```[\s\S]*?```|`[^`]+`)"` detects both inline and multiline code
- **Virtual environments**: Two venvs exist - `.venv` (active) and `venv` (legacy). Use `.venv` for development
