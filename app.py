from textual.app import App, ComposeResult
from textual.widgets import Static, TextArea, RichLog, Label, Footer
from textual.reactive import Reactive, reactive
from textual.binding import Binding
from textual.containers import Vertical
from textual import work
from typing import Literal, TYPE_CHECKING, cast, Optional
import pyperclip

from translator import CodeTranslator, TranslationResult

if TYPE_CHECKING:
    from app import DirectionToggle, StatusBar


class DirectionToggle(Static):
    """翻訳方向を表示・切り替えするウィジェット.
    
    日本語→英語 / 英語→日本語の方向を表示し、Tabキーで切り替えます。
    """
    
    direction: Reactive[Literal["ja_to_en", "en_to_ja"]] = reactive("ja_to_en")
    
    DEFAULT_CSS = """
    DirectionToggle {
        content-align: center middle;
        text-style: bold;
        height: 2;
        width: 100%;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_display()
    
    def toggle(self) -> None:
        """翻訳方向を切り替える.
        
        ja_to_en ⇔ en_to_ja の交互に切り替えます。
        """
        new_direction = "en_to_ja" if self.direction == "ja_to_en" else "ja_to_en"
        self.direction = new_direction
    
    def watch_direction(
        self, 
        old_direction: Literal["ja_to_en", "en_to_ja"], 
        new_direction: Literal["ja_to_en", "en_to_ja"]
    ) -> None:
        """方向が変更された時のハンドラ.
        
        Args:
            old_direction: 変更前の方向
            new_direction: 変更後の方向
        """
        self._update_display()
    
    def _update_display(self) -> None:
        """現在の方向に基づいて表示テキストを更新."""
        if self.direction == "ja_to_en":
            display_text = "🇯🇵 日本語 → 🇺🇸 English"
        else:
            display_text = "🇺🇸 English → 🇯🇵 日本語"
        self.update(display_text)


class StatusBar(Static):
    """ステータスを表示するウィジェット。
    
    翻訳状態（待機/翻訳中/完了/エラー）を表示します。
    """
    
    status_text: Reactive[str] = reactive("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._style: str = ""
    
    DEFAULT_CSS = """
    StatusBar {
        content-align: left middle;
        height: 1;
        width: 100%;
        color: $text;
        background: $panel;
    }
    """
    
    def set_status(self, text: str, style: str = "") -> None:
        """ステータスを更新.
        
        Args:
            text: 表示するステータステキスト
            style: Textualのスタイル（例: "bold", "italic", "red"）
        """
        self._style = style
        self.status_text = text
        if style:
            styled_text = f"[{style}]{text}[/{style}]"
        else:
            styled_text = text
        self.update(styled_text)
    
    def watch_status_text(self, old_value: str, new_value: str) -> None:
        """status_textが変更された時のハンドラ。
        
        Args:
            old_value: 変更前のテキスト
            new_value: 変更後のテキスト
        """
        # Display is updated by set_status() directly
        # self.update(display_text) is called by reactive() when status_text changes
        if self._style:
            styled_text = f"[{self._style}]{new_value}[/{self._style}]"
        else:
            styled_text = new_value
        self.update(styled_text)


class CodeTranslateApp(App[None]):
    """CodeTranslate TUI メインアプリケーション。

    日本語⇔英語翻訳TUIツールのエントリーポイントです。
    """

    TITLE = "CodeTranslate"
    SUB_TITLE = "TranslateGemma コーディング翻訳"

    def __init__(self):
        super().__init__()
        self.translator = CodeTranslator()
        self._is_translating: bool = False
        self._last_result: TranslationResult | None = None
        self.history: list[TranslationResult] = []
    
    CSS = """
    Screen {
        layout: vertical;
        padding: 1;
    }

    #direction-toggle {
        dock: top;
        height: 2;
        background: $primary;
        text-align: center;
    }

    #input {
        height: 10;
        margin: 0 1;
        border: thick $primary;
    }

    #output {
        height: 1fr;
        margin: 1;
        border: thick $success;
        background: $panel;
    }

    #history-panel {
        display: none;
        border: thick $warning;
        height: 20;
        margin: 1;
    }

    Label {
        text-style: bold;
        height: 1;
    }

    #history-log {
        height: 1fr;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $panel;
        border-top: solid $primary;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+j", "translate", "翻訳", show=True, priority=True),
        Binding("ctrl+enter", "translate", "翻訳", show=False, priority=False),
        Binding("tab", "toggle_direction", "方向切替", show=True, priority=True),
        Binding("ctrl+y", "copy_result", "コピー", show=True, priority=True),
        Binding("ctrl+l", "clear", "クリア", show=True, priority=True),
        Binding("ctrl+h", "toggle_history", "履歴", show=True, priority=True),
        Binding("ctrl+q", "quit", "終了", show=True),
    ]
    
    def compose(self) -> ComposeResult:
        """ウィジェットツリーを構成。

        Yields:
            ComposeResult: アプリケーションのウィジェット
        """
        # 上部：翻訳方向
        yield DirectionToggle(id="direction-toggle")

        # 中央：入力・出力エリア
        with Vertical(id="main-content"):
            yield TextArea(
                id="input",
                placeholder="翻訳したいテキストを入力してください...",
                soft_wrap=True,
            )
            yield RichLog(
                id="output",
                auto_scroll=True,
                wrap=True,
            )

        # 履歴パネル
        with Vertical(id="history-panel"):
            yield Label("翻訳履歴")
            yield RichLog(id="history-log", wrap=True, auto_scroll=True)

        # 下部：ステータスバー
        yield StatusBar(id="status-bar")

        # Footer: キーバインド表示
        yield Footer()
    
    def on_mount(self) -> None:
        """アプリケーション起動時の初期化。

        入力エリアにフォーカスを設定し、Ollama接続をチェックします。
        """
        input_area = self.query_one("#input")
        input_area.focus()

        success, message = self.translator.check_connection()
        status_bar = cast(StatusBar, self.query_one("#status-bar"))
        status_bar.set_status(message)

        if not success:
            output_area = cast(RichLog, self.query_one("#output"))
            setup_guide = """Ollamaのセットアップ手順:

1. Ollamaをインストール:
   curl -fsSL https://ollama.com/install.sh | sh

2. TranslateGemmaモデルをダウンロード:
   ollama pull translategemma:12b

3. Ollamaを起動:
   ollama serve

詳細: https://github.com/ollama/ollama"""
            output_area.write(setup_guide)
    
    def action_translate(self) -> None:
        """翻訳を実行するアクション。"""
        if self._is_translating:
            return

        input_area = cast(TextArea, self.query_one("#input"))
        text = input_area.text

        if not text.strip():
            return

        status_bar = cast(StatusBar, self.query_one("#status-bar"))
        status_bar.set_status("⏳ 翻訳中...")

        direction_toggle = cast(DirectionToggle, self.query_one("#direction-toggle"))
        direction = direction_toggle.direction

        self._is_translating = True
        self._run_translation(text, direction)

    @work(thread=True)
    def _run_translation(self, text: str, direction: Literal["ja_to_en", "en_to_ja"]) -> None:
        """バックグラウンドスレッドで翻訳を実行。"""
        result = self.translator.translate(text, direction)
        self.call_from_thread(self._display_result, result)

    def _display_result(self, result: TranslationResult) -> None:
        """翻訳結果を表示する。"""
        output_area = cast(RichLog, self.query_one("#output"))
        output_area.clear()

        output_area.write(result.translated)

        status_bar = cast(StatusBar, self.query_one("#status-bar"))
        if result.error:
            status_bar.set_status("✗ 翻訳失敗")
        else:
            status_bar.set_status("✓ 翻訳完了")

        self._is_translating = False
        self._last_result = result
        self.history.append(result)

        history_panel = self.query_one("#history-panel")
        if history_panel.display:
            history_log = cast(RichLog, self.query_one("#history-log"))
            entry_number = len(self.history)
            formatted = self._format_history_entry(entry_number, result)
            history_log.write(formatted)

    def action_copy_result(self) -> None:
        """翻訳結果をクリップボードにコピーするアクション。"""
        if self._last_result is None:
            return

        try:
            pyperclip.copy(self._last_result.translated)
            status_bar = cast(StatusBar, self.query_one("#status-bar"))
            status_bar.set_status("📋 翻訳結果をコピーしました")
        except Exception:
            # Catch all clipboard-related errors: PyperclipException, OSError, RuntimeError, etc.
            status_bar = cast(StatusBar, self.query_one("#status-bar"))
            status_bar.set_status("✗ クリップボードコピー失敗")

    def action_clear(self) -> None:
        """入力エリア、出力エリア、および最後の翻訳結果をクリアし、フォーカスを入力エリアに戻すアクション。"""
        input_area = cast(TextArea, self.query_one("#input"))
        output_area = cast(RichLog, self.query_one("#output"))

        input_area.text = ""
        output_area.clear()
        self._last_result = None
        input_area.focus()

    def action_toggle_direction(self) -> None:
        """Tabキーで翻訳方向を切り替えるアクション。"""
        direction_toggle = cast(DirectionToggle, self.query_one("#direction-toggle"))
        direction_toggle.toggle()

    def _format_history_entry(self, index: int, result: TranslationResult) -> str:
        direction_label = "日→英" if result.direction == "ja_to_en" else "英→日"
        return f"--- #{index} ({direction_label}) ---\n{result.original[:80]}\n{result.translated[:80]}"

    def action_toggle_history(self) -> None:
        """履歴パネルの表示/非表示を切り替えるアクション。"""
        history_panel = self.query_one("#history-panel")
        history_panel.display = not history_panel.display

        if history_panel.display:
            history_log = cast(RichLog, self.query_one("#history-log"))
            history_log.clear()

            entries = self.history[-20:]
            for idx, result in enumerate(reversed(entries), 1):
                entry_number = len(self.history) - idx + 1
                formatted = self._format_history_entry(entry_number, result)
                history_log.write(formatted)


def main():
    """CodeTranslate TUI Application entry point."""
    app = CodeTranslateApp()
    app.run()


if __name__ == "__main__":
    main()
