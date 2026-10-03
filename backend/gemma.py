"""Gemma 4 Client implementation using the Google GenAI SDK."""

try:
    from google import genai
    from google.genai import errors
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    errors = None
    GENAI_AVAILABLE = False

from logging import config

from backend import tools
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
        """Generate content with manual tool-calling support."""

        if not GENAI_AVAILABLE:
            raise GemmaAPIError(
                "The 'google-genai' SDK is not installed. "
                "Please install it with 'pip install google-genai'."
            )

        try:
            from google.genai import types

            # ---------------------------------------------------------
            # 1. Convert RepoPilot messages -> Google GenAI contents
            # ---------------------------------------------------------
            if isinstance(contents, str):
                google_contents = contents

            else:
                google_contents = []

                for message in contents:
                    role = message.get("role", "user")
                    parts = []

                    # Normal text
                    text = message.get("content")
                    if text:
                        parts.append(
                            types.Part.from_text(text=text)
                        )

                    # Model function calls
                    for call in message.get("function_calls", []):
                        name = call.get("name")
                        args = call.get("args", {})

                        if name:
                            parts.append(
                                types.Part.from_function_call(
                                    name=name,
                                    args=args,
                                )
                            )

                    # Function results
                    for result in message.get("function_results", []):
                        tool_name = (
                            result.get("tool_name")
                            or result.get("name")
                        )

                        if tool_name:
                            parts.append(
                                types.Part.from_function_response(
                                    name=tool_name,
                                    response={
                                        "output": result,
                                    },
                                )
                            )

                    if parts:
                        # Google GenAI expects model/user roles.
                        # Tool results are sent as a user turn containing
                        # function_response parts.
                        google_role = (
                            "model" if role == "model" else "user"
                        )

                        google_contents.append(
                            types.Content(
                                role=google_role,
                                parts=parts,
                            )
                        )

            # ---------------------------------------------------------
            # 2. Convert RepoPilot tool schemas -> Google Tool
            # ---------------------------------------------------------
            google_tools = None

            if tools:
                declarations = []

                for tool in tools:
                    declarations.append(
                        types.FunctionDeclaration(
                            name=tool["name"],
                            description=tool.get("description", ""),
                            parameters_json_schema=tool.get(
                                "parameters",
                                {
                                    "type": "object",
                                    "properties": {},
                                },
                            ),
                        )
                    )

                google_tools = [
                    types.Tool(
                        function_declarations=declarations
                    )
                ]

            # ---------------------------------------------------------
            # 3. Build configuration
            # ---------------------------------------------------------
            config_kwargs = {}

            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction

            if google_tools:
                config_kwargs["tools"] = google_tools

            config = types.GenerateContentConfig(
                **config_kwargs
            ) if config_kwargs else None

            # ---------------------------------------------------------
            # 4. Call Gemma
            # ---------------------------------------------------------
            response = self._client.models.generate_content(
                model=self._model,
                contents=google_contents,
                config=config,
            )

            # ---------------------------------------------------------
            # 5. Extract response
            # ---------------------------------------------------------
            text_content = response.text or ""
            calls = []

            for call in (response.function_calls or []):
                calls.append(
                    {
                        "name": call.name,
                        "args": dict(call.args or {}),
                    }
                )

            return {
                "text": text_content,
                "function_calls": calls,
            }

        except Exception as e:
            err_msg = str(e)

            if self._api_key and self._api_key in err_msg:
                err_msg = err_msg.replace(
                    self._api_key,
                    "[REDACTED]",
                )

            raise GemmaAPIError(
                f"Gemma API request failed: {err_msg}"
            ) from None

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
