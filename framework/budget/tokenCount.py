"""
Token counting utilities.

tiktoken has no encoding for Llama/Groq models, so we approximate using
OpenAI's cl100k_base encoding for any non-OpenAI model. This is not an
exact count for Llama's actual tokenizer, but it's consistent and close
enough for budget-management purposes (staying under a context window,
comparing relative sizes). Documented here rather than silently assumed.
"""

from functools import lru_cache
import tiktoken

_FALLBACK_ENCODING = "cl100k_base"


@lru_cache(maxsize=None)
def _get_encoding(model: str) -> tiktoken.Encoding:
    """
    Return a cached tiktoken encoding for the given model name.

    Cached because loading an encoding (merge tables etc.) is not free,
    and we'll be calling this once per message at minimum.
    """
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding(_FALLBACK_ENCODING)


def count_tokens(text: str, model: str) -> int:
    """
    Return the token count of `text` under the given model's encoding.

    For models tiktoken doesn't recognize (e.g. Llama/Groq), falls back
    to cl100k_base as an approximation — see module docstring.

    NOTE on repeated counting: if we ever need to re-count the same
    conversation's messages many times, we could cache per-(text, model)
    results too. Skipped for now — a portfolio-sized dataset doesn't
    justify the memory/staleness tradeoff, and Message.token_count is
    already computed once at write time, not re-tokenized on every read.
    """
    encoding = _get_encoding(model)
    return len(encoding.encode(text))