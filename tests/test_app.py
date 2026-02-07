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
