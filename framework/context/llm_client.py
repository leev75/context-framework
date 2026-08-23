import os
import time

from groq import Groq
from dotenv import load_dotenv
from framework.models.models import Message

_MODEL = "qwen/qwen3.6-27b"
_MAX_RETRIES = 2  # total attempts = 1 initial + 2 retries = 3


class LLMClientError(Exception):
    """Raised when the LLM call fails after all retries are exhausted."""


def _get_client() -> Groq:
    load_dotenv()  # load .env file if present, so os.environ.get() works
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise LLMClientError(
            "GROQ_API_KEY environment variable is not set. "
            "Get a free key at https://console.groq.com/keys"
        )
    return Groq(api_key=api_key)


def _to_provider_format(messages: list[Message], system_prompt: str) -> list[dict]:
    """
    Map internal Message objects to the provider's Chat Completions message
    format. This translation is intentionally boxed in here — nothing outside
    this file should know what shape Groq (or any provider) expects.
    """
    provider_messages = [{"role": "system", "content": system_prompt}]
    for message in messages:
        provider_messages.append({"role": message.role, "content": message.content})
    return provider_messages


def generate(messages: list[Message], system_prompt: str) -> str:
    """
    Send conversation history + a system prompt to the LLM and return the
    completion text.

    Retries up to _MAX_RETRIES times on transient errors (network issues,
    rate limits, 5xx). Raises LLMClientError if the key is missing or all
    attempts are exhausted.
    """
    client = _get_client()
    provider_messages = _to_provider_format(messages, system_prompt)

    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=_MODEL,
                messages=provider_messages,
            )
            return response.choices[0].message.content
        except Exception as error:  # noqa: BLE001 - deliberately broad for a thin v1 retry
            last_error = error
            if attempt < _MAX_RETRIES:
                time.sleep(1 * (attempt + 1))  # simple linear backoff: 1s, 2s
                continue

    raise LLMClientError(f"LLM call failed after {_MAX_RETRIES + 1} attempts: {last_error}")