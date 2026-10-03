"""Gemma 4 Client implementation using the Google GenAI SDK."""

try:
    from google import genai
    from google.genai import errors
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    errors = None
    GENAI_AVAILABLE = False

from backend.config import get_settings, ConfigurationError


class GemmaAPIError(Exception):
    """Raised when an API request to the Gemma model fails."""
    pass


class GemmaClient:
    """Client for generating content using the Google GenAI SDK and Gemma models."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize Gemma client.

        Args:
            api_key: Optional explicit API key. If omitted, loaded from configuration.
            model: Optional explicit model ID. If omitted, loaded from configuration.
        """
        if api_key is None or model is None:
            settings = get_settings()
            self._api_key = api_key if api_key is not None else settings.api_key
            self._model = model if model is not None else settings.model
        else:
            self._api_key = api_key
            self._model = model

        if not self._api_key:
            raise ConfigurationError("GEMMA_API_KEY must be provided.")
        if not self._model:
            raise ConfigurationError("GEMMA_MODEL must be provided.")

        if not GENAI_AVAILABLE:
            raise GemmaAPIError("The 'google-genai' SDK is not installed. Please install it with 'pip install google-genai'.")

        self._client = genai.Client(api_key=self._api_key)

    @property
    def model(self) -> str:
        """Return the configured model identifier."""
        return self._model

    def generate(self, prompt: str) -> str:
        """Generate text from a prompt using the configured Gemma model.

        Args:
            prompt: Text prompt to send to the model.

        Returns:
            The generated response text.

        Raises:
            ValueError: If the prompt is not a non-empty string.
            GemmaAPIError: If the API request fails or returns an empty response.
        """
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt must be a non-empty string.")

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
            if response.text is not None and response.text.strip():
                return response.text
            raise GemmaAPIError("Gemma API returned an empty response.")
        except errors.APIError as e:
            # Sanitize error message to ensure API key is never exposed
            err_msg = str(e)
            if self._api_key and self._api_key in err_msg:
                err_msg = err_msg.replace(self._api_key, "[REDACTED]")
            raise GemmaAPIError(f"Gemma API request failed: {err_msg}") from None
        except Exception as e:
            err_msg = str(e)
            if self._api_key and self._api_key in err_msg:
                err_msg = err_msg.replace(self._api_key, "[REDACTED]")
            raise GemmaAPIError(f"Unexpected error while communicating with Gemma API: {err_msg}") from None

    def generate_with_tools(
        self,
        contents: str | list,
        tools: list | None = None,
        system_instruction: str | None = None,
    ) -> dict:
        """Generate content with tool calling support.

        Args:
            contents: Prompt string or list of conversation message dicts.
            tools: List of tool declarations.
            system_instruction: Optional system instruction prompt.

        Returns:
            dict: Structured response with 'text' and 'function_calls'.
        """
        if not GENAI_AVAILABLE:
            raise GemmaAPIError("The 'google-genai' SDK is not installed. Please install it with 'pip install google-genai'.")

        try:
            config = {}
            if system_instruction:
                config["system_instruction"] = system_instruction
            if tools:
                config["tools"] = tools

            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=config if config else None,
            )

            text_content = response.text if response.text else ""
            calls = []

            if hasattr(response, "function_calls") and response.function_calls:
                for call in response.function_calls:
                    calls.append({
                        "name": getattr(call, "name", ""),
                        "args": dict(getattr(call, "args", {})),
                    })

            return {
                "text": text_content,
                "function_calls": calls,
            }
        except Exception as e:
            err_msg = str(e)
            if self._api_key and self._api_key in err_msg:
                err_msg = err_msg.replace(self._api_key, "[REDACTED]")
            raise GemmaAPIError(f"Gemma API request failed: {err_msg}") from None


def generate_response(prompt: str) -> str:
    """Generate a response using the configured Gemma 4 model.

    This abstraction keeps caller code independent from the underlying Google GenAI SDK.

    Args:
        prompt: The input prompt string.

    Returns:
        The generated response string.
    """
    client = GemmaClient()
    return client.generate(prompt)
