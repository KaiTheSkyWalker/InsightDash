from typing import Optional, Tuple

from config.settings import (
    GOOGLE_API_KEY as SETTINGS_API_KEY,
    MODEL_NAME as SETTINGS_MODEL,
)

HAVE_NEW_GENAI = False
HAVE_LEGACY_GENAI = False

try:
    from google import genai

    HAVE_NEW_GENAI = True
except Exception:
    try:
        import google.generativeai as genai_legacy

        HAVE_LEGACY_GENAI = True
    except Exception:
        pass


def generate_markdown_from_prompt(
    prompt: str,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Generate markdown text from a prompt using Gemini (new or legacy client).

    Returns a tuple of (text, error). If both clients are unavailable or no api_key,
    returns a helpful message as text and None for error.
    """
    model = model_name or SETTINGS_MODEL
    key = api_key or SETTINGS_API_KEY

    try:
        if HAVE_NEW_GENAI and key:
            client = genai.Client(api_key=key)
            resp = client.models.generate_content(model=model, contents=[prompt])
            return getattr(resp, "text", None), None

        if HAVE_LEGACY_GENAI and key:
            genai_legacy.configure(api_key=key)
            model_client = genai_legacy.GenerativeModel(model)
            resp = model_client.generate_content([prompt])
            return getattr(resp, "text", None), None

        # Not configured
        return (
            "LLM not configured. Install `google-genai` or `google-generativeai` and set `GOOGLE_API_KEY`.",
            None,
        )
    except Exception as e:
        return None, str(e)


# OpenRouter path removed; Gemini-only support retained.
