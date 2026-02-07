"""Shared test fixtures for translator tests."""

import os
import pytest
from collections import namedtuple
from pathlib import Path
from unittest.mock import MagicMock


ModelInfo = namedtuple('ModelInfo', ['model'])


class MockListResponse:
    def __init__(self, models_list):
        self.models = models_list


@pytest.fixture
def mock_ollama_chat(mocker):
    """Fixture to mock ollama.chat() for unit tests."""

    def mock_chat_response(model, messages, **kwargs):
        mock_response = MagicMock()
        mock_response.message.content = f"Mocked translation for: {messages[-1]['content'][:50]}..."
        mock_response.message.role = "assistant"
        return mock_response

    return mocker.patch('ollama.chat', side_effect=mock_chat_response)


@pytest.fixture
def mock_ollama_list(mocker):
    """Fixture to mock ollama.list() for connection tests."""
    return mocker.patch('ollama.list')


def pytest_configure(config):
    """Configure pytest markers and asyncio mode."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (requires actual Ollama connection)"
    )
    config.option.asyncio_mode = "auto"


@pytest.fixture
def glossary_path():
    """glossary.json の絶対パスを返す."""
    rootdir = Path(__file__).parent.parent
    return os.path.join(rootdir, "glossary.json")
