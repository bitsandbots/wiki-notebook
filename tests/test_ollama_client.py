"""Tests for Ollama client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from wiki_notebook.ai.ollama_client import OllamaClient, OllamaError


class TestOllamaClient:
    """Tests for OllamaClient class."""

    def test_is_available_true(self):
        """is_available returns True when Ollama responds successfully."""
        client = OllamaClient(url="http://localhost:11434")

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            assert client.is_available() is True

    def test_is_available_false_on_error(self):
        """is_available returns False on connection error."""
        client = OllamaClient(url="http://localhost:11434")

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()

            assert client.is_available() is False

    def test_is_available_false_on_timeout(self):
        """is_available returns False on timeout."""
        client = OllamaClient(url="http://localhost:11434")

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()

            assert client.is_available() is False

    def test_is_available_false_on_non_200(self):
        """is_available returns False on non-200 status."""
        client = OllamaClient(url="http://localhost:11434")

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response

            assert client.is_available() is False

    def test_generate_success(self):
        """generate returns response text on success."""
        client = OllamaClient(url="http://localhost:11434", model="test-model")

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Hello, world!"}
            mock_post.return_value = mock_response

            result = client.generate("Test prompt")

            assert result == "Hello, world!"

    def test_generate_raises_on_non_200(self):
        """generate raises OllamaError on non-200 response."""
        client = OllamaClient(url="http://localhost:11434", model="test-model")

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response

            with pytest.raises(OllamaError):
                client.generate("Test prompt")

    def test_generate_raises_on_connection_error(self):
        """generate raises OllamaError on connection error."""
        client = OllamaClient(url="http://localhost:11434", model="test-model")

        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError()

            with pytest.raises(OllamaError):
                client.generate("Test prompt")

    def test_generate_json_success(self):
        """generate_json parses valid JSON response."""
        client = OllamaClient(url="http://localhost:11434", model="test-model")

        with patch.object(client, "generate") as mock_generate:
            mock_generate.return_value = '{"category": "test", "tags": ["a", "b"]}'
            result = client.generate_json("Test prompt")

            assert result == {"category": "test", "tags": ["a", "b"]}

    def test_generate_json_retries_on_invalid_json(self):
        """generate_json retries when first attempt returns invalid JSON."""
        client = OllamaClient(url="http://localhost:11434", model="test-model")

        with patch.object(client, "generate") as mock_generate:
            # First call returns invalid JSON, second call succeeds
            mock_generate.side_effect = [
                "not valid json",
                '{"category": "test", "tags": ["a"]}',
            ]
            result = client.generate_json("Test prompt")

            assert result == {"category": "test", "tags": ["a"]}
            assert mock_generate.call_count == 2

    def test_generate_json_raises_on_persistent_failure(self):
        """generate_json raises OllamaError if both attempts fail."""
        client = OllamaClient(url="http://localhost:11434", model="test-model")

        with patch.object(client, "generate") as mock_generate:
            mock_generate.side_effect = [
                "not valid json",
                "still not valid",
            ]

            with pytest.raises(OllamaError):
                client.generate_json("Test prompt")

    def test_config_values_used(self):
        """Client uses config values when not explicitly provided."""
        # This test verifies the client reads from config
        client = OllamaClient()

        assert client.url == "http://localhost:11434"
        assert client.model == "qwen2.5:7b-instruct"
        assert client.timeout == 30
