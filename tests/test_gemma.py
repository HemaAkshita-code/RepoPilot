"""Tests for Gemma 4 configuration and generation."""

import os
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.config import get_settings, ConfigurationError
from backend.gemma import GemmaClient, generate_response, GemmaAPIError


class TestGemmaConfiguration(unittest.TestCase):
    """Test configuration loading and basic validation."""

    def test_missing_credentials_raises_configuration_error(self):
        """Verify that missing environment variables raise a clear ConfigurationError."""
        saved_key = os.environ.get("GEMMA_API_KEY")
        saved_model = os.environ.get("GEMMA_MODEL")
        try:
            os.environ.pop("GEMMA_API_KEY", None)
            os.environ.pop("GEMMA_MODEL", None)

            with self.assertRaises(ConfigurationError) as ctx:
                get_settings()

            err = str(ctx.exception)
            self.assertIn("GEMMA_API_KEY", err)
            self.assertIn("GEMMA_MODEL", err)
        finally:
            if saved_key is not None:
                os.environ["GEMMA_API_KEY"] = saved_key
            if saved_model is not None:
                os.environ["GEMMA_MODEL"] = saved_model

    def test_empty_prompt_validation(self):
        """Verify that an empty or whitespace prompt raises a ValueError."""
        saved_key = os.environ.get("GEMMA_API_KEY")
        saved_model = os.environ.get("GEMMA_MODEL")
        try:
            os.environ["GEMMA_API_KEY"] = "dummy_key_for_test"
            os.environ["GEMMA_MODEL"] = "gemma-4-31b-it"

            with patch("backend.gemma.GENAI_AVAILABLE", True), patch("backend.gemma.genai"):
                client = GemmaClient()
                with self.assertRaises(ValueError):
                    client.generate("")
                with self.assertRaises(ValueError):
                    client.generate("   \n\t  ")
        finally:
            if saved_key is not None:
                os.environ["GEMMA_API_KEY"] = saved_key
            else:
                os.environ.pop("GEMMA_API_KEY", None)
            if saved_model is not None:
                os.environ["GEMMA_MODEL"] = saved_model
            else:
                os.environ.pop("GEMMA_MODEL", None)


class TestGemmaLiveIntegration(unittest.TestCase):
    """Live integration test against the real Gemma 4 API.

    This test executes a real API request ONLY when valid credentials are provided.
    It does not fake or mock responses.
    """

    def test_live_gemma_api_request(self):
        """Make a real Gemma 4 API request when credentials are available."""
        api_key = os.environ.get("GEMMA_API_KEY", "").strip()
        model = os.environ.get("GEMMA_MODEL", "").strip()

        if not api_key or not model:
            self.skipTest(
                "Skipping live integration test: GEMMA_API_KEY and/or GEMMA_MODEL environment variables are not set."
            )

        prompt = "Explain what a GitHub repository is in one sentence."
        response = generate_response(prompt)

        self.assertIsInstance(response, str, "Response must be a string")
        self.assertTrue(len(response.strip()) > 0, "Response must not be empty")


if __name__ == "__main__":
    unittest.main()
