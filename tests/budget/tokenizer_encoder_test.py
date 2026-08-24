import tiktoken
from framework.budget.tokenCount import count_tokens



MODEL = "gpt-4"
enc = tiktoken.encoding_for_model(MODEL)

def test_known_token_counts():
    assert count_tokens("Hello, world!", MODEL) == len(enc.encode("Hello, world!"))
    assert count_tokens("Hello world", MODEL) == len(enc.encode("Hello world"))
    assert count_tokens("", MODEL) == len(enc.encode(""))
    assert count_tokens("tiktoken is great!", MODEL) == len(enc.encode("tiktoken is great!"))

def test_matches_known_expected_values():
    assert count_tokens("Hello, world!", MODEL) == 4
    assert count_tokens("Hello world", MODEL) == 2
    assert count_tokens("", MODEL) == 0
    assert count_tokens("tiktoken is great!", MODEL) == 6




