from typing import Optional, Tuple
import os
import json
import requests

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


def generate_markdown_openrouter(
    prompt: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Generate markdown text using OpenRouter (e.g., DeepSeek R1).

    Reads defaults from environment when args are None:
      - OPENROUTER_API_KEY
      - OPENROUTER_MODEL (default: deepseek/deepseek-r1)
      - OPENROUTER_BASE_URL (default: https://openrouter.ai/api/v1)
    Returns (text, error).
    """
    # WARNING: Hard-coded API key fallback per user request. Do NOT commit this in shared repos.
    key = (
        api_key
        or os.environ.get("OPENROUTER_API_KEY", "").strip()
        or "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"
    )
    mdl = model or os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-r1")
    url = (
        base_url
        or os.environ.get("OPENROUTER_BASE_URL")
        or "https://openrouter.ai/api/v1"
    ).rstrip("/") + "/chat/completions"

    if not key:
        return None, "OpenRouter API key not configured (set OPENROUTER_API_KEY)."

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        # Optional but recommended by OpenRouter for attribution
        "HTTP-Referer": os.environ.get("OPENROUTER_REFERRER", "http://localhost"),
        "X-Title": os.environ.get("OPENROUTER_TITLE", "CR KPI Insights"),
    }

    body = {
        "model": mdl,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful, concise data analyst. Return clean markdown only.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": float(os.environ.get("OPENROUTER_TEMPERATURE", 0.2)),
        "stream": False,
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=60)
        if resp.status_code != 200:
            return None, f"OpenRouter error {resp.status_code}: {resp.text[:500]}"
        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            return None, "OpenRouter returned no choices."
        msg = choices[0].get("message", {})
        text = msg.get("content")
        return text, None
    except Exception as e:
        return None, str(e)
