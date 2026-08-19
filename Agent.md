# Context Assembly Framework — v1 Spec (condensed)

Goal: answer "given everything we know, what should be sent to the LLM right now?" and prove it beats a naive baseline.

## In scope (M1–M5)
- Single/multi-session chat, persistent history
- Token-aware context assembly (sliding window + budget-fit)
- Long-term memory (store, embed, retrieve, inject)
- RAG over a small corpus (PDF/MD/text)
- Eval harness proving assembled context beats a naive baseline

## Explicitly OUT for v1 — do not build, do not suggest
- Multi-provider abstraction (OpenAI only)
- Multiple vector stores (ChromaDB only)
- Compression beyond sliding window (no recursive summarization)
- Dashboard (CLI + FastAPI/Swagger only)
- Tool calling, observability (OpenTelemetry), auth, Docker, CI/CD

If a task seems to need one of these, stop and flag it instead of building it.

## Folder structure (already scaffolded — extend, don't restructure)
```
app/api/  app/cli/
framework/context/    # ContextBuilder, ConversationManager
framework/memory/     # long-term memory store + retrieval
framework/retrieval/  # ingestion + RAG
framework/budget/     # token counting + trimming
framework/ranking/    # scoring function
framework/prompts/    # system.md + task templates
framework/models/     # Message, RetrievedItem, ContextPackage, Memory
eval/baseline.py  eval/harness.py  eval/testset/
tests/  examples/
```
Rule: don't create a new top-level module unless a second thing needs it.

## Core models
```python
class Message(BaseModel):
    id: str; session_id: str
    role: Literal["user","assistant","system"]
    content: str; timestamp: datetime; token_count: int

class RetrievedItem(BaseModel):
    text: str; source: str  # "memory" | "document"
    score: float; metadata: dict

class ContextPackage(BaseModel):
    system_prompt: str
    conversation: list[Message]
    retrieved: list[RetrievedItem]
    token_usage: dict[str, int]  # conversation, retrieved, total
    dropped: list[dict]  # id, score, reason — every drop must be logged
```

## Pipeline order
retrieve candidates → score (ranking) → sliding window on conversation → fit_budget (drop lowest-scored retrieved first, then oldest turns) → assemble ContextPackage

## Ranking formula
`score = 0.6*similarity + 0.2*recency + 0.2*importance` — log each component per item.

## Memory importance rule (v1, must be explicit — never default to 0.5)
Explicit user "remember this" → 1.0. Otherwise: LLM classifier scores 0–1 on "is this durable/useful later."

## Eval harness (M5)
20–30 labeled examples: conversation history + candidate memories/docs + gold facts.
Baseline = naive: last N messages, no ranking, no retrieval, truncate oldest-first.
Metrics: gold-fact recall, token efficiency (recall/token), drop correctness.

## Milestones
M1 chat engine (done) · M2 token/budget · M3 memory · M4 RAG · M5 eval harness

## Definition of done
- [ ] harness.py shows ContextBuilder beats baseline on recall at ≤ equal tokens
- [ ] every dropped item logged with score + reason
- [ ] importance scoring is documented, not a placeholder
- [ ] README leads with the eval report, not the architecture

# Conventions

## Stack
- Python 3.12+, `uv` for packages (never pip/poetry)
- FastAPI + Pydantic v2 for API/validation
- SQLite for persistence (metadata, sessions, messages, memory rows)
- ChromaDB for vectors (local, one collection per type: `memories`, `documents`)
- OpenAI Responses API for LLM calls, `text-embedding-3-small` for embeddings
- `tiktoken` for token counting
- `pytest` + `pytest-asyncio` for tests

## Rules
- One provider (OpenAI), one vector store (ChromaDB) — no abstraction layers "for later."
- Don't create a new top-level module until a second thing needs it.
- Every public function gets a docstring stating any non-obvious assumption (e.g. what "N turns" means).
- Token counts are computed once at write time (e.g. on `Message` creation), not recomputed on every read.
- Mock all OpenAI/embedding calls in tests — no live network calls in the test suite.
- Any drop/trim decision (budget-fit) must be logged with the item id, score, and reason. No silent drops.
- Memory and document retrieval must produce the same `RetrievedItem` shape and flow through the same ranking + budget-fit path — no special-casing one over the other.

## Naming
- `snake_case` for functions/variables, `PascalCase` for Pydantic models.
- Test files: `tests/test_<module>.py`, mirroring `framework/<module>/`.
- Prompt templates live in `framework/prompts/*.md`, referenced by filename, not inlined in code.

## When unsure
If a task seems to require something in the "explicitly out" list (see 01-spec.md), stop and flag it rather than implementing a workaround or partial version of it.

# Glossary (terms as used in this project)

- **ContextPackage** — the final assembled bundle sent to the LLM: system prompt + conversation + retrieved items + token usage + drop trace.
- **ContextBuilder** — the orchestrator that runs the full pipeline (retrieve → score → window → budget-fit → assemble).
- **Sliding window** — taking the last N turns/messages of a conversation, no ranking involved.
- **Budget-fit** — the algorithm that trims a candidate set to fit `max_tokens - reserved_output`, dropping lowest-scored retrieved items first, then oldest conversation turns.
- **Drop trace** — the logged record of what was cut during budget-fit and why (score + reason).
- **RetrievedItem** — a candidate (memory or document chunk) with a similarity/ranking score, before it's decided whether it makes the final context.
- **Ranking function** — `score = 0.6*similarity + 0.2*recency + 0.2*importance`, applied identically to memory and document candidates.
- **Importance** — a 0–1 score on a memory: 1.0 if the user explicitly asked to remember it, otherwise an LLM classifier's judgment of durability/usefulness.
- **Naive baseline** — the eval harness comparison point: last N messages only, no ranking, no retrieval, truncate oldest-first.
- **Gold-fact recall** — did a required fact from the test set actually make it into the assembled context.
- **Token efficiency** — gold-fact recall achieved per token spent.
- **Drop correctness** — whether budget-fit dropped the right items (low-score) vs. wrong items (a gold-labeled one).
- **v2 / deferred** — anything on the "explicitly out" list in 01-spec.md: multi-provider abstraction, multiple vector stores, recursive summarization, dashboard, tool calling, observability, auth, Docker, CI/CD.