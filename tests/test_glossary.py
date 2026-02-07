"""Tests for glossary.json."""

import json
import pytest


class TestGlossaryJSONSyntax:
    """glossary.jsonのJSON構文検証"""

    def test_glossary_json_is_valid(self, glossary_path):
        """glossary.jsonが有効なJSONであることを確認"""
        with open(glossary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_glossary_has_required_keys(self, glossary_path):
        """必須のキー（ja_to_en, en_to_ja, preserve_as_is）が存在することを確認"""
        with open(glossary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "ja_to_en" in data
        assert "en_to_ja" in data
        assert "preserve_as_is" in data

    def test_glossary_types_are_correct(self, glossary_path):
        """各セクションのデータ型が正しいことを確認"""
        with open(glossary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data["ja_to_en"], dict)
        assert isinstance(data["en_to_ja"], dict)
        assert isinstance(data["preserve_as_is"], list)


class TestGlossaryConsistency:
    """ja_to_enとen_to_jaの整合性チェック"""

    def test_ja_to_en_en_to_ja_consistency(self, glossary_path):
        """ja_to_enとen_to_jaの整合性を確認（主要用語が逆転していること）"""
        with open(glossary_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ja_to_en = data["ja_to_en"]
        en_to_ja = data["en_to_ja"]

        # 主要用語の逆転チェック
        # en_to_jaに含まれる主要用語がja_to_enの逆になっていることを確認
        for en_term in en_to_ja:
            ja_translation = en_to_ja[en_term]
            if ja_translation in ja_to_en:
                assert ja_to_en[ja_translation] == en_term, \
                    f"Inconsistency: {ja_translation} → {ja_to_en[ja_translation]} but en_to_ja has {en_term} → {ja_translation}"

    def test_no_orphans_in_en_to_ja(self, glossary_path):
        """en_to_jaの各エントリがja_to_enに存在する用語の逆であることを確認"""
        with open(glossary_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ja_to_en = data["ja_to_en"]
        en_to_ja = data["en_to_ja"]

        # en_to_jaの各エントリがja_to_enの用語の逆転であることを確認
        for en_term, ja_term in en_to_ja.items():
            if ja_term in ja_to_en:
                assert ja_to_en[ja_term] == en_term or ja_to_en[ja_term] == en_term.lower(), \
                    f"Orphan: en_to_ja has {en_term} → {ja_term} but ja_to_en has {ja_term} → {ja_to_en[ja_term]}"


class TestGlossaryPreserveAsIs:
    """preserve_as_isの重複チェック"""

    def test_no_duplicates_in_preserve_as_is(self, glossary_path):
        """preserve_as_isに重複がないことを確認"""
        with open(glossary_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        preserve_list = data["preserve_as_is"]
        assert len(preserve_list) == len(set(preserve_list)), \
            f"Found duplicates in preserve_as_is: {preserve_list}"

    def test_preserve_as_is_is_not_empty(self, glossary_path):
        """preserve_as_isが空でないことを確認"""
        with open(glossary_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["preserve_as_is"]) > 0, "preserve_as_is should not be empty"


class TestGlossaryCompleteness:
    """用語数のチェック"""

    def test_ja_to_en_minimum_terms(self, glossary_path):
        """ja_to_enが150語以上であることを確認"""
        with open(glossary_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ja_to_en_count = len(data["ja_to_en"])
        assert ja_to_en_count >= 150, \
            f"ja_to_en has only {ja_to_en_count} terms, expected at least 150"

    def test_en_to_ja_minimum_terms(self, glossary_path):
        """en_to_jaが50語以上であることを確認"""
        with open(glossary_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        en_to_ja_count = len(data["en_to_ja"])
        assert en_to_ja_count >= 50, \
            f"en_to_ja has only {en_to_ja_count} terms, expected at least 50"
