"""Tests for translation history panel (Task 2-4)."""

import pytest
from textual.widgets import RichLog, Label
from textual.containers import Vertical
from translator import TranslationResult


class TestHistoryInitialization:
    """Tests for history instance variable."""

    def test_history_initialized_as_empty_list(self):
        """historyが初期状態で空のリストであることを確認"""
        from app import CodeTranslateApp

        app = CodeTranslateApp()
        assert hasattr(app, "history"), "App should have history attribute"
        assert isinstance(app.history, list), "history should be a list"
        assert len(app.history) == 0, "history should be empty on init"

    def test_history_type_is_list(self):
        """historyの型がlist[TranslationResult]であることを確認"""
        from app import CodeTranslateApp

        app = CodeTranslateApp()
        assert hasattr(app, "history"), "App should have history attribute"
        assert isinstance(app.history, list), "history should be a list"


class TestHistoryPopulation:
    """Tests for history appending in _display_result()."""

    async def test_display_result_appends_to_history(self, mocker):
        """_display_result()がhistoryに追加することを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            result = TranslationResult(
                original="テスト",
                translated="Test",
                direction="ja_to_en",
                error=False
            )

            # Direct call for testing
            pilot.app._display_result(result)
            await pilot.pause()

            assert len(pilot.app.history) == 1, "history should have 1 entry"
            assert pilot.app.history[0].original == "テスト"
            assert pilot.app.history[0].translated == "Test"

    async def test_multiple_translations_in_history(self, mocker):
        """複数の翻訳がhistoryに順番に保存されることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            # First translation
            result1 = TranslationResult(
                original="最初",
                translated="First",
                direction="ja_to_en",
                error=False
            )
            pilot.app._display_result(result1)
            await pilot.pause()

            # Second translation
            result2 = TranslationResult(
                original="二番目",
                translated="Second",
                direction="ja_to_en",
                error=False
            )
            pilot.app._display_result(result2)
            await pilot.pause()

            assert len(pilot.app.history) == 2, "history should have 2 entries"
            assert pilot.app.history[0].original == "最初"
            assert pilot.app.history[1].original == "二番目"

    async def test_history_preserves_original_result_fields(self, mocker):
        """historyがTranslationResultのすべてのフィールドを保存することを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            result = TranslationResult(
                original="日本語テキスト",
                translated="English text",
                direction="en_to_ja",
                error=True
            )
            pilot.app._display_result(result)
            await pilot.pause()

            assert len(pilot.app.history) == 1
            saved = pilot.app.history[0]
            assert saved.original == "日本語テキスト"
            assert saved.translated == "English text"
            assert saved.direction == "en_to_ja"
            assert saved.error is True


class TestHistoryPersistence:
    """Tests for history persistence across clear()."""

    async def test_action_clear_preserves_history(self, mocker):
        """action_clear()がhistoryをクリアしないことを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            # Add some history
            result = TranslationResult(
                original="テスト",
                translated="Test",
                direction="ja_to_en",
                error=False
            )
            pilot.app._display_result(result)
            await pilot.pause()

            initial_history_count = len(pilot.app.history)
            assert initial_history_count > 0

            # Clear input/output
            pilot.app.action_clear()
            await pilot.pause()

            # History should still have the same count
            assert len(pilot.app.history) == initial_history_count
            assert pilot.app.history[0].original == "テスト"

    async def test_history_accessible_after_clear(self, mocker):
        """clear()後にhistoryにアクセスできることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            # Add multiple translations to history
            for i in range(3):
                result = TranslationResult(
                    original=f"翻訳{i}",
                    translated=f"Translation{i}",
                    direction="ja_to_en",
                    error=False
                )
                pilot.app._display_result(result)
                await pilot.pause()

            # Verify all 3 are in history
            assert len(pilot.app.history) == 3

            # Clear input/output
            pilot.app.action_clear()
            await pilot.pause()

            # All history entries should still be intact
            assert len(pilot.app.history) == 3
            for i in range(3):
                assert pilot.app.history[i].original == f"翻訳{i}"
                assert pilot.app.history[i].translated == f"Translation{i}"


class TestHistoryPanelComposition:
    """Tests for history panel in compose()."""

    async def test_history_panel_exists_in_dom(self):
        """history-panelがDOMに存在することを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            # Should be able to query history panel
            history_panel = pilot.app.query_one("#history-panel")
            assert history_panel is not None

    async def test_history_panel_contains_label_and_richlog(self):
        """history-panelがLabelとRichLogを含んでいることを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            history_panel = pilot.app.query_one("#history-panel")

            # Should have children: Label and RichLog
            children = list(history_panel.children)
            assert len(children) >= 2, "Should have at least Label and RichLog"

            # Check for Label
            labels = [c for c in children if isinstance(c, Label)]
            assert len(labels) > 0, "Should have a Label widget"

            # Check for RichLog
            rich_logs = [c for c in children if isinstance(c, RichLog)]
            assert len(rich_logs) > 0, "Should have a RichLog widget"


class TestHistoryPanelStyling:
    """Tests for CSS styling."""

    async def test_history_panel_has_display_none(self):
        """history-panelの初期表示がdisplay:noneであることを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            history_panel = pilot.app.query_one("#history-panel")
            assert history_panel.display is False

    async def test_history_panel_has_warning_border(self):
        """history-panelのボーダーカラーが$warningであることを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            # Check that CSS contains border styling for history-panel
            # The CSS class should have border: thick $warning
            css = CodeTranslateApp.CSS
            assert "border:" in css, "CSS should contain border styling"
            assert "$warning" in css, "CSS should use $warning color for history-panel border"


class TestToggleHistoryBinding:
    """Tests for Ctrl+H key binding."""

    def test_ctrl_h_binding_exists(self):
        """Ctrl+Hキーバインドが存在することを確認"""
        from app import CodeTranslateApp

        app = CodeTranslateApp()

        # Find Ctrl+H binding
        ctrl_h_bindings = [b for b in app.BINDINGS if "ctrl+h" in b.key]
        assert len(ctrl_h_bindings) > 0, "Should have Ctrl+H binding"
        assert ctrl_h_bindings[0].show is True, "Ctrl+H should be visible in footer"

    async def test_ctrl_h_triggers_toggle_history(self, mocker):
        """Ctrl+Hキーでaction_toggle_historyがトリガーされることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            # Mock action_toggle_history to track calls
            call_tracker = {"called": False}
            original_action = pilot.app.action_toggle_history

            def mock_toggle_history():
                call_tracker["called"] = True
            pilot.app.action_toggle_history = mock_toggle_history

            # Press Ctrl+H
            await pilot.press("ctrl+h")
            await pilot.pause()

            # Verify action was called
            assert call_tracker["called"], "Ctrl+H should trigger action_toggle_history"

            # Restore original action
            pilot.app.action_toggle_history = original_action


class TestToggleHistoryAction:
    """Tests for action_toggle_history()."""

    async def test_action_toggle_history_shows_panel(self, mocker):
        """action_toggle_history()でパネルが表示されることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            history_panel = pilot.app.query_one("#history-panel")

            # Initially should be hidden
            assert history_panel.display is False

            # Toggle to show
            pilot.app.action_toggle_history()
            await pilot.pause()

            # Should now be visible
            assert history_panel.display is True

    async def test_action_toggle_history_hides_panel(self, mocker):
        """action_toggle_history()でパネルが非表示になることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            history_panel = pilot.app.query_one("#history-panel")

            # Show panel first
            pilot.app.action_toggle_history()
            await pilot.pause()
            assert history_panel.display is True

            # Toggle again to hide
            pilot.app.action_toggle_history()
            await pilot.pause()

            # Should now be hidden
            assert history_panel.display is False

    async def test_toggle_history_twice_returns_to_original_state(self, mocker):
        """トグルを2回押すと元の状態に戻ることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            history_panel = pilot.app.query_one("#history-panel")

            # Initial state
            initial_display = history_panel.display
            assert initial_display is False

            # Toggle once
            pilot.app.action_toggle_history()
            await pilot.pause()
            first_toggle = history_panel.display

            # Toggle twice
            pilot.app.action_toggle_history()
            await pilot.pause()
            second_toggle = history_panel.display

            # Should return to initial state
            assert first_toggle is not initial_display
            assert second_toggle is initial_display


class TestHistoryEntryFormat:
    """Tests for entry formatting."""

    def test_history_entry_format_includes_number(self, mocker):
        """履歴エントリに番号が含まれることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        app = CodeTranslateApp()

        # Create test result
        result = TranslationResult(
            original="テスト",
            translated="Test",
            direction="ja_to_en",
            error=False
        )

        # Format entry - first entry should be #1
        formatted = app._format_history_entry(1, result)

        # Should contain "#1" (1-based indexing)
        assert "#1" in formatted

    def test_history_entry_format_includes_direction(self, mocker):
        """履歴エントリに方向が含まれることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        app = CodeTranslateApp()

        # Test ja_to_en
        result1 = TranslationResult(
            original="テスト",
            translated="Test",
            direction="ja_to_en",
            error=False
        )
        formatted1 = app._format_history_entry(0, result1)
        assert "日→英" in formatted1

        # Test en_to_ja
        result2 = TranslationResult(
            original="Test",
            translated="テスト",
            direction="en_to_ja",
            error=False
        )
        formatted2 = app._format_history_entry(0, result2)
        assert "英→日" in formatted2

    def test_history_entry_format_includes_text_snippets(self, mocker):
        """履歴エントリにテキストの一部が含まれることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        app = CodeTranslateApp()

        # Test with long text (should be truncated to 80 chars)
        long_original = "a" * 100
        long_translated = "b" * 100

        result = TranslationResult(
            original=long_original,
            translated=long_translated,
            direction="ja_to_en",
            error=False
        )

        formatted = app._format_history_entry(0, result)

        # Should contain first 80 chars
        assert long_original[:80] in formatted
        assert long_translated[:80] in formatted

        # Should NOT contain full text
        assert long_original not in formatted
        assert long_translated not in formatted

    def test_entry_number_starts_at_one(self, mocker):
        """エントリ番号が1始まりであることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        app = CodeTranslateApp()

        result = TranslationResult(
            original="テスト",
            translated="Test",
            direction="ja_to_en",
            error=False
        )

        # First entry should be #1, not #0
        formatted_first = app._format_history_entry(1, result)
        assert "#1" in formatted_first

        # Second entry should be #2
        formatted_second = app._format_history_entry(2, result)
        assert "#2" in formatted_second


class TestHistoryDisplay:
    """Tests for populating history panel."""

    async def test_toggle_history_shows_all_entries(self, mocker):
        """トグル時にすべての履歴エントリが表示されることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            # Add 3 entries to history
            for i in range(3):
                result = TranslationResult(
                    original=f"翻訳{i}",
                    translated=f"Translation{i}",
                    direction="ja_to_en",
                    error=False
                )
                pilot.app._display_result(result)
                await pilot.pause()

            # Toggle to show
            pilot.app.action_toggle_history()
            await pilot.pause()

            # Check that history-log has content
            history_log = pilot.app.query_one("#history-log")
            assert len(history_log.lines) > 0, "History log should have entries"

    async def test_toggle_history_shows_last_20_only(self, mocker):
        """履歴が20件以上の場合、最後の20件のみが表示されることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            for i in range(25):
                result = TranslationResult(
                    original=f"翻訳{i}",
                    translated=f"Translation{i}",
                    direction="ja_to_en",
                    error=False
                )
                pilot.app._display_result(result)
                await pilot.pause()

            pilot.app.action_toggle_history()
            await pilot.pause()

            history_log = pilot.app.query_one("#history-log")

            assert len(pilot.app.history) == 25, "All 25 entries should be in history"

            log_text = str(history_log.lines)

            assert "--- #1 (" not in log_text
            assert "--- #2 (" not in log_text
            assert "--- #3 (" not in log_text
            assert "--- #4 (" not in log_text
            assert "--- #5 (" not in log_text

            assert "--- #6 (" in log_text
            assert "--- #25 (" in log_text
            assert "--- #24 (" in log_text
            assert "--- #23 (" in log_text

    async def test_empty_history_shows_no_content(self, mocker):
        """空の履歴の場合、何も表示されないことを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            # Toggle without any history
            pilot.app.action_toggle_history()
            await pilot.pause()

            # History log should be empty
            history_log = pilot.app.query_one("#history-log")
            assert len(history_log.lines) == 0, "Empty history should show no content"

    async def test_entries_in_reverse_chronological_order(self, mocker):
        """エントリが逆順（最新が先）で表示されることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            # Add entries in order
            for i in range(5):
                result = TranslationResult(
                    original=f"翻訳{i}",
                    translated=f"Translation{i}",
                    direction="ja_to_en",
                    error=False
                )
                pilot.app._display_result(result)
                await pilot.pause()

            # Toggle to show
            pilot.app.action_toggle_history()
            await pilot.pause()

            # Check that newest entries appear first
            history_log = pilot.app.query_one("#history-log")
            log_lines = list(history_log.lines)
            log_text = str(log_lines)

            # Entry 4 (newest) should appear before Entry 0 (oldest)
            entry4_pos = log_text.find("翻訳4")
            entry0_pos = log_text.find("翻訳0")

            assert entry4_pos < entry0_pos, "Newest entries should appear first"

    async def test_history_log_has_auto_scroll_enabled(self, mocker):
        """history-logでauto_scrollが有効になっていることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            history_log = pilot.app.query_one("#history-log")
            assert history_log.auto_scroll is True, "RichLog should have auto_scroll enabled"

    async def test_history_panel_updates_when_visible(self, mocker):
        """履歴パネルが表示されている場合、新しい翻訳で更新されることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            history_log = pilot.app.query_one("#history-log")

            pilot.app.action_toggle_history()
            await pilot.pause()

            result1 = TranslationResult(
                original="最初の翻訳",
                translated="First translation",
                direction="ja_to_en",
                error=False
            )
            pilot.app._display_result(result1)
            await pilot.pause()

            assert "#1 (" in str(history_log.lines)

            result2 = TranslationResult(
                original="二番目の翻訳",
                translated="Second translation",
                direction="ja_to_en",
                error=False
            )
            pilot.app._display_result(result2)
            await pilot.pause()

            log_text = str(history_log.lines)
            assert "#1 (" in log_text
            assert "#2 (" in log_text


class TestHistoryEdgeCases:
    """Tests for edge cases in history functionality."""

    async def test_multiline_text_in_history(self, mocker):
        """複数行のテキストが履歴に保存されることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            multiline_original = "一行目\n二行目\n三行目"
            multiline_translated = "Line 1\nLine 2\nLine 3"

            result = TranslationResult(
                original=multiline_original,
                translated=multiline_translated,
                direction="ja_to_en",
                error=False
            )
            pilot.app._display_result(result)
            await pilot.pause()

            assert len(pilot.app.history) == 1
            assert pilot.app.history[0].original == multiline_original
            assert pilot.app.history[0].translated == multiline_translated

    async def test_short_text_in_history(self, mocker):
        """非常に短いテキストが履歴に保存されることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            result = TranslationResult(
                original="a",
                translated="b",
                direction="ja_to_en",
                error=False
            )
            pilot.app._display_result(result)
            await pilot.pause()

            assert len(pilot.app.history) == 1
            assert pilot.app.history[0].original == "a"
            assert pilot.app.history[0].translated == "b"

    async def test_unicode_characters_in_history(self, mocker):
        """Unicode文字を含むテキストが履歴に保存されることを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            result = TranslationResult(
                original="日本語🎌テスト✨",
                translated="Japanese🇯🇵test🌟",
                direction="ja_to_en",
                error=False
            )
            pilot.app._display_result(result)
            await pilot.pause()

            assert len(pilot.app.history) == 1
            assert "🎌" in pilot.app.history[0].original
            assert "✨" in pilot.app.history[0].original
            assert "🇯🇵" in pilot.app.history[0].translated
            assert "🌟" in pilot.app.history[0].translated


class TestHistoryIntegration:
    """Integration tests for complete history workflow."""

    async def test_full_workflow_multiple_toggles(self, mocker):
        """複数回の履歴トグルを含む完全なワークフローを確認"""
        from app import CodeTranslateApp

        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            history_panel = pilot.app.query_one("#history-panel")
            history_log = pilot.app.query_one("#history-log")

            for i in range(3):
                result = TranslationResult(
                    original=f"翻訳{i}",
                    translated=f"Translation{i}",
                    direction="ja_to_en",
                    error=False
                )
                pilot.app._display_result(result)
                await pilot.pause()

            assert len(pilot.app.history) == 3

            pilot.app.action_toggle_history()
            await pilot.pause()
            assert history_panel.display is True
            log_text = str(history_log.lines)
            assert "#3 (" in log_text
            assert "#2 (" in log_text
            assert "#1 (" in log_text

            pilot.app.action_toggle_history()
            await pilot.pause()
            assert history_panel.display is False

            result4 = TranslationResult(
                original="翻訳3",
                translated="Translation3",
                direction="ja_to_en",
                error=False
            )
            pilot.app._display_result(result4)
            await pilot.pause()

            assert len(pilot.app.history) == 4

            pilot.app.action_toggle_history()
            await pilot.pause()
            assert history_panel.display is True
            log_text = str(history_log.lines)
            assert "#4 (" in log_text
            assert "#1 (" in log_text
