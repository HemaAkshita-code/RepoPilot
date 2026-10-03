"""Entry point for testing Gemma 4 model generation in RepoPilot."""

import sys
from pathlib import Path

# Add project root to sys.path to support running as script or module
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.config import get_settings, ConfigurationError
from backend.gemma import generate_response, GemmaAPIError


def main() -> None:
    """Execute simple test prompt with the configured Gemma 4 model."""
    try:
        settings = get_settings()
        print(f"Loaded configuration for model: {settings.model}")
    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    prompt = "Explain what a GitHub repository is in one sentence."
    print(f"Prompt: {prompt}\n")

    try:
        response = generate_response(prompt)
        print("Response:")
        print(response)
    except GemmaAPIError as e:
        print(f"Error generating response: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
