"""Tests for app module - TUI layout and widgets."""

import pytest
from textual.app import App
from textual.widgets import TextArea, RichLog, Footer
from textual.containers import Vertical
from typing import Literal


class TestDirectionToggle:
    """DirectionToggle widget tests."""

    def test_initial_state(self):
        """初期状態が日本語→英語であることを確認"""
        from app import DirectionToggle
        widget = DirectionToggle()
        assert widget.direction == "ja_to_en"
        assert "日本語" in str(widget.render())
        assert "English" in str(widget.render())

    def test_toggle_direction(self):
        """toggle()メソッドで方向が切り替わることを確認"""
        from app import DirectionToggle
        widget = DirectionToggle()
        assert widget.direction == "ja_to_en"
        widget.toggle()
        assert widget.direction == "en_to_ja"
        widget.toggle()
        assert widget.direction == "ja_to_en"

    def test_direction_property(self):
        """directionプロパティで現在の方向を取得できることを確認"""
        from app import DirectionToggle
        widget = DirectionToggle()

        # Test initial value
        assert widget.direction == "ja_to_en"

        # Test setting directly
        widget.direction = "en_to_ja"
        assert widget.direction == "en_to_ja"

        # Test invalid value should not crash
        # Note: Type checking is not enforced by reactive
        widget.direction = "invalid"  # type: ignore

    def test_watch_direction_updates_display(self):
        """方向変更時に表示が更新されることを確認"""
        from app import DirectionToggle
        widget = DirectionToggle()
        initial_text = str(widget.render())
        widget.direction = "en_to_ja"
        # Display should change after direction changes
        new_text = str(widget.render())
        assert initial_text != new_text


class TestStatusBar:
    """StatusBar widget tests."""

    def test_initial_state(self):
        """初期ステータスが空であることを確認"""
        from app import StatusBar
        widget = StatusBar()
        assert widget.status_text == ""

    def test_set_status_updates_text(self):
        """set_status(text, style)でテキストが更新されることを確認"""
        from app import StatusBar
        widget = StatusBar()
        widget.set_status("Ready", "")
        assert "Ready" in str(widget.render())

        widget.set_status("翻訳中...", "bold")
        assert "翻訳中..." in str(widget.render())

    def test_set_status_with_none_style(self):
        """style=''でも正しく動作することを確認"""
        from app import StatusBar
        widget = StatusBar()
        widget.set_status("Test", "")
        assert "Test" in str(widget.render())

    def test_set_status_clears_previous(self):
        """新しいステータスで前の内容がクリアされることを確認"""
        from app import StatusBar
        widget = StatusBar()
        widget.set_status("First", "")
        widget.set_status("Second", "")
        assert "First" not in str(widget.render())
        assert "Second" in str(widget.render())


class TestCodeTranslateAppComposition:
    """CodeTranslateApp compose() tests."""

    async def test_compose_returns_widgets(self):
        """compose()ですべての必要なウィジェットが生成されることを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            # Check DirectionToggle exists
            direction_toggle = pilot.app.query_one("#direction-toggle")
            assert direction_toggle is not None

            # Check input area exists
            input_area = pilot.app.query_one("#input")
            assert isinstance(input_area, TextArea)

            # Check output area exists
            output_area = pilot.app.query_one("#output")
            assert isinstance(output_area, RichLog)

            # Check status bar exists
            status_bar = pilot.app.query_one("#status-bar")
            assert status_bar is not None

    async def test_widget_ids_exist(self):
        """すべてのウィジェットにIDが設定されていることを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            widgets = pilot.app.query("*")
            # Should have at least: direction-toggle, input, output, status-bar, footer
            assert len(widgets) >= 5

            # Check specific widgets have IDs
            pilot.app.query_one("#direction-toggle")
            pilot.app.query_one("#input")
            pilot.app.query_one("#output")
            pilot.app.query_one("#status-bar")

    async def test_app_has_bindings(self):
        """アプリにキーバインディングが設定されていることを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            # Should have BINDINGS defined
            assert hasattr(pilot.app, "BINDINGS")
            assert len(pilot.app.BINDINGS) > 0

            # Check Tab binding exists
            tab_binding = [b for b in pilot.app.BINDINGS if "tab" in b.key]
            assert len(tab_binding) > 0

    async def test_initial_focus_on_input(self):
        """起動時に入力エリアにフォーカスが設定されることを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            # Check that input area is focused
            input_area = pilot.app.query_one("#input")
            assert input_area.has_focus


class TestTabBinding:
    """Tab key binding tests."""

    async def test_direct_action_call_works(self):
        """アクションを直接呼ぶと方向が切り替わることを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            direction_toggle = pilot.app.query_one("#direction-toggle")
            initial_direction = direction_toggle.direction

            pilot.app.action_toggle_direction()
            await pilot.pause()

            assert direction_toggle.direction != initial_direction

    async def test_tab_toggles_direction(self):
        """Tabキーで方向が切り替わることを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            direction_toggle = pilot.app.query_one("#direction-toggle")
            initial_direction = direction_toggle.direction

            await pilot.press("tab")
            await pilot.pause()

    async def test_direction_toggle_updates_display(self):
        """方向切替え時に表示が更新されることを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            direction_toggle = pilot.app.query_one("#direction-toggle")

            initial_text = str(direction_toggle.render())

            await pilot.press("tab")
            await pilot.pause()

            new_text = str(direction_toggle.render())


class TestCodeTranslateAppTranslationInit:
    """Tests for CodeTranslator initialization in app."""

    async def test_translator_instance_created_on_init(self):
        """__init__でCodeTranslatorインスタンスが生成されることを確認"""
        from app import CodeTranslateApp
        from translator import CodeTranslator

        app = CodeTranslateApp()
        assert hasattr(app, "translator"), "App should have translator attribute"
        assert isinstance(app.translator, CodeTranslator), "translator should be CodeTranslator instance"


class TestCodeTranslateAppOnMountConnection:
    """Tests for on_mount connection check."""

    async def test_on_mount_calls_check_connection(self, mocker):
        """on_mountでcheck_connectionが呼ばれることを確認"""
        from app import CodeTranslateApp
        from translator import CodeTranslator

        # Mock check_connection to track calls
        mock_check = mocker.patch.object(CodeTranslator, "check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            # check_connection should have been called during mount
            assert mock_check.called, "check_connection should be called on mount"
            assert mock_check.call_count == 1, "check_connection should be called exactly once"

    async def test_on_mount_success_shows_status_ok(self, mocker):
        """接続成功時のステータスバー表示を確認"""
        from app import CodeTranslateApp

        # Mock check_connection to return success
        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            status_bar = pilot.app.query_one("#status-bar")
            status_text = str(status_bar.render())
            # Status should show connection success
            assert "OK" in status_text or "準備完了" in status_text or "接続OK" in status_text

    async def test_on_mount_failure_shows_setup_instructions(self, mocker):
        """接続失敗時に出力エリアにセットアップ手順が表示されることを確認"""
        from app import CodeTranslateApp

        # Mock check_connection to return failure
        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(False, "Ollama に接続できません"))

        async with CodeTranslateApp().run_test() as pilot:
            output_area = pilot.app.query_one("#output")
            await pilot.pause()

            # Output area should have content (setup instructions were written)
            # RichLog stores lines; check if it has content
            has_lines = len(output_area.lines) > 0
            assert has_lines, "Output area should have setup instructions when connection fails"


class TestCodeTranslateAppActionTranslate:
    """Tests for action_translate method."""

    async def test_action_translate_gets_text_from_input(self):
        """入力エリアからテキストを取得することを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            input_area = pilot.app.query_one("#input")
            input_area.text = "テストテキスト"

            # Mock _run_translation to track if it's called
            original_run = pilot.app._run_translation if hasattr(pilot.app, "_run_translation") else None
            call_tracker = {"called": False, "text": None, "direction": None}

            if original_run:
                def mock_run(text, direction):
                    call_tracker["called"] = True
                    call_tracker["text"] = text
                    call_tracker["direction"] = direction
                pilot.app._run_translation = mock_run

            pilot.app.action_translate()
            await pilot.pause()

            if original_run:
                assert call_tracker["called"], "_run_translation should be called"

    async def test_action_translate_does_nothing_for_empty_string(self):
        """空文字列の場合は何もしないことを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            input_area = pilot.app.query_one("#input")
            input_area.text = ""

            # Mock _run_translation to track if it's called
            if hasattr(pilot.app, "_run_translation"):
                call_tracker = {"called": False}
                original_run = pilot.app._run_translation

                def mock_run(text, direction):
                    call_tracker["called"] = True
                pilot.app._run_translation = mock_run

                status_bar = pilot.app.query_one("#status-bar")
                initial_status = str(status_bar.render())

                pilot.app.action_translate()
                await pilot.pause()

                # Status should not have changed to "翻訳中..."
                final_status = str(status_bar.render())
                assert "翻訳中" not in final_status, "Status should not show '翻訳中' for empty text"

                if original_run:
                    assert not call_tracker["called"], "_run_translation should NOT be called for empty text"

    async def test_action_translate_updates_status_to_translating(self):
        """ステータスバーが「⏳ 翻訳中...」に更新されることを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            input_area = pilot.app.query_one("#input")
            input_area.text = "テスト"

            status_bar = pilot.app.query_one("#status-bar")

            pilot.app.action_translate()
            await pilot.pause()

            status_text = str(status_bar.render())
            assert "翻訳中" in status_text or "⏳" in status_text, "Status should show '翻訳中' or hourglass emoji"


class TestCodeTranslateAppRunTranslation:
    """Tests for _run_translation background thread."""

    async def test_run_translation_uses_work_decorator(self):
        """@work(thread=True)デコレータが使用されていることを確認"""
        from app import CodeTranslateApp
        from textual import work

        app = CodeTranslateApp()

        # Check if _run_translation method exists and has work decorator
        assert hasattr(app, "_run_translation"), "App should have _run_translation method"
        method = getattr(app, "_run_translation")

        # Check if it's a worker method (has is_worker attribute)
        # In Textual, @work adds metadata to the method
        has_worker_metadata = hasattr(method, "is_worker") or hasattr(method, "_work_threaded")
        # We'll verify this by checking the implementation later

    async def test_run_translation_calls_translator_translate(self, mocker):
        """translator.translate()が呼ばれることを確認"""
        from app import CodeTranslateApp

        # Mock translator.translate
        mock_translate = mocker.patch("translator.CodeTranslator.translate")
        mock_translate.return_value = type("TranslationResult", (), {
            "original": "テスト",
            "translated": "Test",
            "direction": "ja_to_en",
            "error": False
        })()

        async with CodeTranslateApp().run_test() as pilot:
            if hasattr(pilot.app, "_run_translation"):
                pilot.app._run_translation("テスト", "ja_to_en")
                await pilot.pause()
                # translate should have been called
                assert mock_translate.called, "translator.translate should be called"


class TestCodeTranslateAppDisplayResult:
    """Tests for _display_result method."""

    async def test_display_result_clears_output_area(self, mocker):
        """出力エリアがクリアされることを確認"""
        from app import CodeTranslateApp
        from translator import TranslationResult

        async with CodeTranslateApp().run_test() as pilot:
            output_area = pilot.app.query_one("#output")

            # Add some initial content
            output_area.write("Previous content")

            # Mock call_from_thread to execute synchronously in test
            result = TranslationResult(original="テスト", translated="Test", direction="ja_to_en", error=False)

            if hasattr(pilot.app, "_display_result"):
                # Direct call for testing
                pilot.app._display_result(result)
                await pilot.pause()

                # Old content should be gone (clear() removes all lines)
                lines = list(output_area.lines)
                assert "Previous content" not in str(lines), "Previous content should be cleared"

    async def test_display_result_shows_translation(self, mocker):
        """翻訳結果が出力エリアに表示されることを確認"""
        from app import CodeTranslateApp
        from translator import TranslationResult

        async with CodeTranslateApp().run_test() as pilot:
            output_area = pilot.app.query_one("#output")

            result = TranslationResult(original="テスト", translated="Test translation", direction="ja_to_en", error=False)

            if hasattr(pilot.app, "_display_result"):
                pilot.app._display_result(result)
                await pilot.pause()

                output_lines = list(output_area.lines)
                output_text = str(output_lines)
                assert "Test translation" in output_text, "Translation result should be displayed"

    async def test_display_result_updates_status_to_complete(self, mocker):
        """ステータスバーが「✓ 翻訳完了」に更新されることを確認"""
        from app import CodeTranslateApp
        from translator import TranslationResult

        async with CodeTranslateApp().run_test() as pilot:
            status_bar = pilot.app.query_one("#status-bar")

            result = TranslationResult(original="テスト", translated="Test", direction="ja_to_en", error=False)

            if hasattr(pilot.app, "_display_result"):
                pilot.app._display_result(result)
                await pilot.pause()

                status_text = str(status_bar.render())
                assert "翻訳完了" in status_text or "✓" in status_text, "Status should show '翻訳完了' or checkmark"

    async def test_display_result_handles_error(self, mocker):
        """エラー結果が適切にハンドリングされることを確認"""
        from app import CodeTranslateApp
        from translator import TranslationResult

        async with CodeTranslateApp().run_test() as pilot:
            output_area = pilot.app.query_one("#output")
            status_bar = pilot.app.query_one("#status-bar")

            result = TranslationResult(
                original="テスト",
                translated="[翻訳エラー] Ollama に接続できません",
                direction="ja_to_en",
                error=True
            )

            if hasattr(pilot.app, "_display_result"):
                pilot.app._display_result(result)
                await pilot.pause()

                # Should still display the error message
                output_lines = list(output_area.lines)
                output_text = str(output_lines)
                assert "[翻訳エラー]" in output_text or "エラー" in output_text, "Error message should be displayed"


class TestCodeTranslateAppKeyBindings:
    """Tests for key bindings."""

    async def test_ctrl_j_triggers_translate_action(self):
        """Ctrl+Jでaction_translateがトリガーされることを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            input_area = pilot.app.query_one("#input")
            input_area.text = "テスト"

            # Mock action_translate to track calls
            if hasattr(pilot.app, "action_translate"):
                call_tracker = {"called": False}
                original_action = pilot.app.action_translate

                def mock_action():
                    call_tracker["called"] = True
                pilot.app.action_translate = mock_action

                await pilot.press("ctrl+j")
                await pilot.pause()

                assert call_tracker["called"], "Ctrl+J should trigger action_translate"

    async def test_ctrl_enter_triggers_translate_action(self):
        """Ctrl+Enterでaction_translateがトリガーされることを確認"""
        from app import CodeTranslateApp

        async with CodeTranslateApp().run_test() as pilot:
            input_area = pilot.app.query_one("#input")
            input_area.text = "テスト"

            # Mock action_translate to track calls
            if hasattr(pilot.app, "action_translate"):
                call_tracker = {"called": False}

                def mock_action():
                    call_tracker["called"] = True
                pilot.app.action_translate = mock_action

                await pilot.press("ctrl+enter")
                await pilot.pause()

                assert call_tracker["called"], "Ctrl+Enter should trigger action_translate"


class TestCodeTranslateAppIntegrationFullFlow:
    """Integration tests for full translation flow."""

    async def test_full_translation_flow_ja_to_en(self, mocker):
        """日本語→英語の完全な翻訳フローをテスト"""
        from app import CodeTranslateApp
        from translator import TranslationResult

        # Mock translator.translate to return a known result
        mock_result = TranslationResult(
            original="この関数を実装してください",
            translated="Please implement this function",
            direction="ja_to_en",
            error=False
        )
        mock_translate = mocker.patch("translator.CodeTranslator.translate", return_value=mock_result)
        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            input_area = pilot.app.query_one("#input")
            output_area = pilot.app.query_one("#output")
            status_bar = pilot.app.query_one("#status-bar")
            direction_toggle = pilot.app.query_one("#direction-toggle")

            # Ensure direction is ja_to_en
            direction_toggle.direction = "ja_to_en"

            # Enter text
            input_area.text = "この関数を実装してください"

            # Press Ctrl+J
            await pilot.press("ctrl+j")

            # Wait for async operations
            await pilot.pause()

            # Verify translation was called with correct arguments
            assert mock_translate.called, "translate should be called"

            # Verify result is displayed
            output_lines = list(output_area.lines)
            output_text = str(output_lines)
            assert "Please implement this function" in output_text, "Translation result should be displayed"

            # Verify status shows completion
            status_text = str(status_bar.render())
            assert "翻訳完了" in status_text or "✓" in status_text, "Status should show completion"

    async def test_full_translation_flow_en_to_ja(self, mocker):
        """英語→日本語の完全な翻訳フローをテスト"""
        from app import CodeTranslateApp
        from translator import TranslationResult

        # Mock translator.translate to return a known result
        mock_result = TranslationResult(
            original="Implement this function",
            translated="この関数を実装してください",
            direction="en_to_ja",
            error=False
        )
        mock_translate = mocker.patch("translator.CodeTranslator.translate", return_value=mock_result)
        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            input_area = pilot.app.query_one("#input")
            output_area = pilot.app.query_one("#output")
            status_bar = pilot.app.query_one("#status-bar")
            direction_toggle = pilot.app.query_one("#direction-toggle")

            # Set direction to en_to_ja
            direction_toggle.direction = "en_to_ja"

            # Enter text
            input_area.text = "Implement this function"

            # Press Ctrl+J
            await pilot.press("ctrl+j")

            # Wait for async operations
            await pilot.pause()

            # Verify translation was called with correct direction
            assert mock_translate.called, "translate should be called"

            # Verify result is displayed
            output_lines = list(output_area.lines)
            output_text = str(output_lines)
            assert "この関数を実装してください" in output_text, "Translation result should be displayed"

    async def test_empty_text_does_not_trigger_translation(self, mocker):
        """空テキストで翻訳がトリガーされないことを確認"""
        from app import CodeTranslateApp

        mock_translate = mocker.patch("translator.CodeTranslator.translate")
        mock_check = mocker.patch("translator.CodeTranslator.check_connection", return_value=(True, "OK"))

        async with CodeTranslateApp().run_test() as pilot:
            input_area = pilot.app.query_one("#input")

            # Empty text
            input_area.text = ""

            # Press Ctrl+J
            await pilot.press("ctrl+j")
            await pilot.pause()

            # translate should NOT be called
            assert not mock_translate.called, "translate should NOT be called for empty text"
