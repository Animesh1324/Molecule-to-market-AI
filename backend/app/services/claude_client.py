"""Thin async wrapper around the Anthropic Messages API.

Isolates every Claude-specific detail — model id, effort, refusal handling,
structured-output plumbing — so the rest of the app only sees "give me JSON
matching this schema, or tell me you couldn't".
"""
import json
import logging
from functools import lru_cache
from typing import Any, Dict, Optional

import anthropic

from ..config import get_settings

logger = logging.getLogger(__name__)

# Requests carry structured output plus a server-side fallback, so a safety
# classifier declining one request (life-sciences text occasionally trips the
# bio classifiers) is retried on another model instead of failing the call.
_FALLBACK_BETA = "server-side-fallback-2026-07-01"

_VALID_EFFORT = {"low", "medium", "high", "xhigh", "max"}


class ClaudeUnavailable(RuntimeError):
    """Raised when a draft could not be produced. Callers fall back to the template."""


def is_configured() -> bool:
    """Whether AI drafting is switched on and has a key to use."""
    return bool(get_settings()["ai_enabled"])


@lru_cache(maxsize=1)
def _client() -> "anthropic.AsyncAnthropic":
    settings = get_settings()
    # An explicit key wins; otherwise the SDK resolves its own credentials.
    if settings["anthropic_api_key"]:
        return anthropic.AsyncAnthropic(api_key=settings["anthropic_api_key"])
    return anthropic.AsyncAnthropic()


def _effort() -> str:
    configured = get_settings()["claude_effort"]
    if configured not in _VALID_EFFORT:
        logger.warning("Unknown CLAUDE_EFFORT %r; falling back to 'high'", configured)
        return "high"
    return configured


async def generate_json(
    *,
    system: str,
    prompt: str,
    schema: Dict[str, Any],
    max_tokens: int = 16000,
    timeout: float = 240.0,
) -> Dict[str, Any]:
    """Ask Claude for a JSON object matching `schema`.

    Raises ClaudeUnavailable for every failure mode the caller should treat the
    same way: not configured, refused, rate limited, malformed, or unreachable.
    """
    if not is_configured():
        raise ClaudeUnavailable("AI drafting is not configured (set ANTHROPIC_API_KEY).")

    settings = get_settings()
    client = _client()

    try:
        response = await client.beta.messages.create(
            model=settings["claude_model"],
            max_tokens=max_tokens,
            betas=[_FALLBACK_BETA],
            fallbacks="default",
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={
                "effort": _effort(),
                "format": {"type": "json_schema", "schema": schema},
            },
            timeout=timeout,
        )
    except anthropic.AuthenticationError as exc:
        raise ClaudeUnavailable("Anthropic API key was rejected.") from exc
    except anthropic.RateLimitError as exc:
        raise ClaudeUnavailable("Anthropic rate limit reached; try again shortly.") from exc
    except anthropic.APIConnectionError as exc:
        raise ClaudeUnavailable(f"Could not reach the Anthropic API: {exc}") from exc
    except anthropic.APIStatusError as exc:
        raise ClaudeUnavailable(f"Anthropic API error {exc.status_code}: {exc.message}") from exc

    # Check the stop reason before touching content: a refusal returns HTTP 200
    # with empty or partial content, so indexing content[0] would raise.
    if response.stop_reason == "refusal":
        category = getattr(response.stop_details, "category", None)
        logger.warning("Claude declined the drafting request (category=%s)", category)
        raise ClaudeUnavailable(
            f"The model declined this request{f' ({category})' if category else ''}."
        )

    text = "".join(block.text for block in response.content if block.type == "text")
    if not text.strip():
        raise ClaudeUnavailable("Model returned no text content.")

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        # Structured outputs make this unlikely, but max_tokens truncation can
        # still cut a response mid-object.
        detail = "output was truncated" if response.stop_reason == "max_tokens" else "output was not valid JSON"
        raise ClaudeUnavailable(f"Could not parse the model response: {detail}.") from exc

    if not isinstance(parsed, dict):
        raise ClaudeUnavailable("Model response was not a JSON object.")

    logger.info(
        "Claude draft complete: model=%s input_tokens=%s output_tokens=%s",
        response.model,
        response.usage.input_tokens,
        response.usage.output_tokens,
    )
    return parsed
