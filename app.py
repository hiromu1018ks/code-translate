from textual.app import App, ComposeResult
from textual.widgets import Static, TextArea, RichLog, Footer
from textual.reactive import reactive
from textual.binding import Binding
from textual.containers import Vertical
from typing import Literal


class DirectionToggle(Static):
    """翻訳方向を表示・切り替えするウィジェット.
    
    日本語→英語 / 英語→日本語の方向を表示し、Tabキーで切り替えます。
    """
    
    direction: Literal["ja_to_en", "en_to_ja"] = reactive("ja_to_en")
    
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
    
    status_text: str = reactive("")
    
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
        styled_text = f"[{self._style}]{new_value}[/{self._style}]" if hasattr(self, '_style') else new_value
        self.update(styled_text)


class CodeTranslateApp(App):
    """CodeTranslate TUI メインアプリケーション。
    
    日本語⇔英語翻訳TUIツールのエントリーポイントです。
    """
    
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
    
    #status-bar {
        dock: bottom;
        height: 1;
        background: $panel;
        border-top: solid $primary;
    }
    """
    
    BINDINGS = [
        Binding("tab", "toggle_direction", "方向切替", show=True, priority=True),
        Binding("q", "quit", "終了", show=True),
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
        
        # 下部：ステータスバー
        yield StatusBar(id="status-bar")
    
    def on_mount(self) -> None:
        """アプリケーション起動時の初期化。
        
        入力エリアにフォーカスを設定します。
        """
        input_area = self.query_one("#input")
        input_area.focus()
    
    def action_toggle_direction(self) -> None:
        """Tabキーで翻訳方向を切り替えるアクション。"""
        direction_toggle = self.query_one("#direction-toggle")
        direction_toggle.toggle()


def main():
    """CodeTranslate TUI Application entry point."""
    pass
