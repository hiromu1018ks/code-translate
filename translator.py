from dataclasses import dataclass
import json
import os
import re
from typing import Literal, Any

import httpx
import ollama


@dataclass
class TranslationResult:
    """Result of a translation operation.

    Original text before translation.
    Translated text after translation.
    Translation direction (ja_to_en or en_to_ja).
    Error flag indicating if translation failed.
    """

    original: str
    translated: str
    direction: str
    error: bool = False


class CodeTranslator:
    """Code translator using TranslateGemma models."""

    DEFAULT_MODEL: str = "translategemma:12b"
    CODE_BLOCK_PATTERN: str = r"(```[\s\S]*?```|`[^`]+`)"
    PLACEHOLDER_FORMAT: str = "__CODE_BLOCK_{}__"

    PROMPT_TEMPLATE: str = """You are a professional {source_lang} ({source_code}) to {target_lang} ({target_code}) translator. Translate the following text accurately while preserving technical meaning and context.


{TEXT}"""

    def __init__(self, model: str | None = None):
        """Initialize CodeTranslator with specified model.

        Args:
            model: Model name to use. If None, reads from TRANSLATEGEMMA_MODEL
                   environment variable or uses DEFAULT_MODEL.
        """
        self.MODEL = model or os.getenv("TRANSLATEGEMMA_MODEL", self.DEFAULT_MODEL)
        self.glossary: dict[str, Any] | None = self._load_glossary("glossary.json")

    def _build_prompt(self, text: str, direction: str) -> str:
        """Build prompt for TranslateGemma model.

        Args:
            text: Text to translate
            direction: "ja_to_en" or "en_to_ja"

        Returns:
            Formatted prompt string

        Raises:
            ValueError: If direction is invalid
        """
        direction_map = {
            "ja_to_en": {
                "source_lang": "Japanese",
                "source_code": "ja",
                "target_lang": "English",
                "target_code": "en-US",
            },
            "en_to_ja": {
                "source_lang": "English",
                "source_code": "en-US",
                "target_lang": "Japanese",
                "target_code": "ja",
            },
        }

        if direction not in direction_map:
            raise ValueError(
                f"Invalid direction: {direction}. Must be 'ja_to_en' or 'en_to_ja'"
            )

        lang_info = direction_map[direction]

        prompt = self.PROMPT_TEMPLATE.format(
            source_lang=lang_info["source_lang"],
            source_code=lang_info["source_code"],
            target_lang=lang_info["target_lang"],
            target_code=lang_info["target_code"],
            TEXT=text,
        )

        # Add glossary hints if available
        if hasattr(self, "glossary") and self.glossary:
            glossary_hint = self._build_glossary_hint(self.glossary, direction)
            if glossary_hint:
                coding_context = "Coding context: This is a programming context translation. Technical terms should be translated accurately using standard programming terminology.\n"
                prompt += "\n" + coding_context
                prompt += "Glossary: " + glossary_hint

        return prompt

    def _protect_code_blocks(self, text: str) -> tuple[str, dict[str, str]]:
        """Protect code blocks by replacing them with placeholders.

        Args:
            text: Text containing code blocks

        Returns:
            tuple: (protected_text, placeholders_dict)
                   placeholders_dict maps placeholder -> original_code_block
        """
        code_pattern = re.compile(self.CODE_BLOCK_PATTERN)
        placeholders = {}
        protected_text = text

        def replace_with_placeholder(match):
            nonlocal placeholders
            placeholder = self.PLACEHOLDER_FORMAT.format(len(placeholders))
            placeholders[placeholder] = match.group(0)
            return placeholder

        protected_text = code_pattern.sub(replace_with_placeholder, protected_text)
        return protected_text, placeholders

    def _restore_code_blocks(self, text: str, placeholders: dict[str, str]) -> str:
        """Restore code blocks by replacing placeholders with original code.

        Args:
            text: Text containing placeholders
            placeholders: Dictionary mapping placeholders to original code blocks

        Returns:
            Text with placeholders replaced by original code blocks
        """
        restored_text = text
        for placeholder, code_block in placeholders.items():
            restored_text = restored_text.replace(placeholder, code_block)
        return restored_text

    def _load_glossary(self, path: str) -> dict[str, Any]:
        """Load glossary from JSON file.

        Args:
            path: Path to glossary JSON file

        Returns:
            Loaded glossary dictionary or empty dict on error
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
        except OSError:
            return {}
        except Exception:
            return {}

        if not isinstance(data, dict):
            return {}

        return data

    def _build_glossary_hint(self, glossary: dict[str, Any], direction: str) -> str:
        """Build glossary hint string for translation direction.

        Args:
            glossary: Glossary dictionary with term translations.
                     Supports multiple formats:
                     1. {"ja_to_en": {...}, "en_to_ja": {...}, "preserve_as_is": [...]}
                     2. {"term": {"ja_to_en": "...", "en_to_ja": "..."}, ...}
                     3. {"term": "translation", "_preserve_as_is": [...]}
            direction: "ja_to_en" or "en_to_ja"

        Returns:
            Formatted hint string with first 30 terms, or empty string if direction not found
        """
        if not glossary:
            return ""

        # Determine format and extract data
        if direction in glossary and isinstance(glossary[direction], dict):
            # Format 1: {"ja_to_en": {...}, "en_to_ja": {...}, "preserve_as_is": [...]}
            direction_dict = glossary[direction]
            preserve_as_is = set(glossary.get("preserve_as_is", []))
        else:
            # Check if using nested format: {"term": {"ja_to_en": "...", "en_to_ja": "..."}}
            has_nested_format = any(
                isinstance(v, dict) and ("ja_to_en" in v or "en_to_ja" in v)
                for v in glossary.values()
            )

            if has_nested_format:
                # Format 2: {"term": {"ja_to_en": "...", "en_to_ja": "..."}, ...}
                items = []
                for term, term_data in glossary.items():
                    if isinstance(term_data, dict) and direction in term_data:
                        items.append((term, term_data[direction], term_data))
                if not items:
                    return ""
                items = items[:30]

                formatted_terms = []
                for term, translation, term_data in items:
                    if term_data.get("preserve_as_is"):
                        formatted_terms.append(f"{term} → {translation} (do not translate)")
                    else:
                        formatted_terms.append(f"{term} → {translation}")
                return "\n".join(formatted_terms)
            else:
                # Format 3: {"term": "translation", "_preserve_as_is": [...]}
                direction_dict = {k: v for k, v in glossary.items() if not k.startswith("_")}
                preserve_as_is = set(glossary.get("_preserve_as_is", []))

        # Handle Formats 1 and 3
        if not direction_dict or not isinstance(direction_dict, dict):
            return ""

        # Take first 30 items, also include preserve_as_is terms
        items = list(direction_dict.items())[:30]

        formatted_terms = []
        for term, translation in items:
            if term in preserve_as_is:
                formatted_terms.append(f"{term} → {translation} (do not translate)")
            else:
                formatted_terms.append(f"{term} → {translation}")

        # Add preserve_as_is terms that aren't in direction_dict (without translation)
        for term in preserve_as_is:
            if term not in direction_dict and len(formatted_terms) < 30:
                formatted_terms.append(f"{term} (do not translate)")

        return ", ".join(formatted_terms)

    def check_connection(self) -> tuple[bool, str]:
        """Check if Ollama is running and model is available.

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            response = ollama.list()
            available_models = [m.model for m in response.models]

            if self.MODEL in available_models:
                return True, "OK"
            else:
                return False, f"モデルが見つかりません: {self.MODEL}"
        except ConnectionError:
            return False, "Ollama に接続できません"
        except ollama.ResponseError:
            return False, "Ollama に接続できません"
        except Exception as e:
            return False, f"接続エラー: {str(e)}"

    def translate(
        self, text: str, direction: Literal["ja_to_en", "en_to_ja"]
    ) -> TranslationResult:
        """Translate text using TranslateGemma model.

        Args:
            text: Text to translate
            direction: "ja_to_en" or "en_to_ja"

        Returns:
            TranslationResult with original, translated, and direction
        """
        if not text:
            return TranslationResult(original="", translated="", direction=direction)

        protected_text, placeholders = self._protect_code_blocks(text)
        prompt = self._build_prompt(protected_text, direction)

        try:
            response = ollama.chat(
                model=self.MODEL, messages=[{"role": "user", "content": prompt}]
            )
            translated_text = response.message.content or ""
            restored_text = self._restore_code_blocks(translated_text, placeholders)
            return TranslationResult(
                original=text, translated=restored_text, direction=direction, error=False
            )
        except ConnectionError:
            return TranslationResult(
                original=text,
                translated="[翻訳エラー] Ollama に接続できません",
                direction=direction,
                error=True,
            )
        except ollama.ResponseError as e:
            if e.status_code == 404:
                return TranslationResult(
                    original=text,
                    translated="[翻訳エラー] モデルが見つかりません",
                    direction=direction,
                    error=True,
                )
            else:
                return TranslationResult(
                    original=text, translated=str(e.error), direction=direction, error=True
                )
        except httpx.TimeoutException:
            return TranslationResult(
                original=text,
                translated="[翻訳エラー] タイムアウトしました",
                direction=direction,
                error=True,
            )
        except Exception as e:
            return TranslationResult(
                original=text, translated=str(e), direction=direction, error=True
            )
