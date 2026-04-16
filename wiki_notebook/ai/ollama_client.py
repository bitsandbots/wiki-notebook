"""Ollama HTTP API client."""

from __future__ import annotations

import json
from typing import Any

import requests

from ..config import config


class OllamaError(Exception):
    """Raised when Ollama API call fails."""


class OllamaClient:
    """Client for Ollama HTTP API."""

    def __init__(
        self,
        url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ):
        """Initialize the Ollama client.

        Args:
            url: Ollama URL (default from config)
            model: Model name (default from config)
            timeout: Request timeout in seconds (default from config)
        """
        self.url = url or config.ollama_url.rstrip("/")
        self.model = model or config.ollama_model
        self.timeout = timeout or config.ollama_timeout

    def is_available(self) -> bool:
        """Check if Ollama is reachable.

        Uses /api/tags with a short timeout to detect availability.
        Never raises - always returns True or False.
        """
        try:
            response = requests.get(
                f"{self.url}/api/tags",
                timeout=(2, self.timeout),
            )
            return response.status_code == 200
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            return False

    def generate(
        self,
        prompt: str,
        *,
        format: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        """Call Ollama /api/generate endpoint.

        Args:
            prompt: The prompt to send to the model
            format: Optional format (e.g., "json")
            options: Optional model options

        Returns:
            The model's response text

        Raises:
            OllamaError: If the request fails or response is not 200
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        if format:
            payload["format"] = format

        if options:
            payload["options"] = options

        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json=payload,
                timeout=(2, self.timeout),
            )

            if response.status_code != 200:
                raise OllamaError(f"Ollama API returned status {response.status_code}")

            data = response.json()
            return data.get("response", "")

        except requests.exceptions.RequestException as e:
            raise OllamaError(f"Request failed: {e}") from e
        except json.JSONDecodeError as e:
            raise OllamaError(f"Failed to parse response: {e}") from e

    def generate_json(
        self,
        prompt: str,
        schema_hint: str = "",
    ) -> dict[str, Any]:
        """Call Ollama with JSON format and parse result.

        Args:
            prompt: The prompt to send
            schema_hint: Optional hint about expected JSON structure

        Returns:
            The parsed JSON response as a dictionary

        Raises:
            OllamaError: If the request fails or parsing fails
        """
        # First attempt with format="json"
        try:
            response = self.generate(prompt, format="json")
            result = json.loads(response)
            return result
        except (OllamaError, json.JSONDecodeError):
            pass

        # Retry with stricter prompt instructions if first attempt failed
        retry_prompt = f"""
{prompt}

IMPORTANT: Return ONLY valid JSON with no explanation, no code fences, no markdown.
The JSON must be valid and parseable.
"""

        try:
            response = self.generate(retry_prompt, format="json")
            result = json.loads(response)
            return result
        except (OllamaError, json.JSONDecodeError) as e:
            raise OllamaError(f"Failed to get valid JSON response: {e}") from e
