# context-type-system

A pure-Python runtime layer that assigns explicit types to AI agent context — instructions, evidence, memory, tool output — and enforces rules about how those types can change before context is serialized into a prompt.

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)

Most agent pipelines flatten instructions, retrieved documents, memory, and tool output into one string before it ever reaches the model. Once it's a string, a tool result can read like an instruction and nothing stops it. This library keeps context typed and provenance-tracked right up until the last possible moment, so that specific class of bug gets caught by a runtime check instead of an editor squinting at five thousand tokens.

Read the full write-up on Towards Data Science → [AI Agents Don’t Need More Context — I Built a Context Type System](https://towardsdatascience.com/author/emmimalp-alexander/)


## What It Does

```
Raw context → ContextStore.add_context() → typed ContextItem
                        │
                        ▼
              ledger check (first-seen type wins)
                    │             │
              [protected type]  [ok]
                    │             │
                 reject      allowed in
                    │             │
        explicit transform()      │
        (policy-checked,          │
         leaves derived_from)     │
                    └──────┬──────┘
                           ▼
              ContextAssembler.assemble()
                           │
                           ▼
                    serialized prompt
```

Five small modules, one enforcement boundary:

| Component | Job |
|---|---|
| `ContextType` | four explicit semantic types — `INSTRUCTION`, `EVIDENCE`, `MEMORY`, `TOOL_OUTPUT` |
| `ContextItem` | the typed unit the runtime operates on — carries `source`, `created`, `request_id`, `derived_from` |
| `ContextStore` | the ledger-backed enforcement boundary — rejects silent relabeling into a protected type, allows explicit `transform()` |
| `transforms.validate_tool_result` | example validated promotion (`TOOL_OUTPUT` → `EVIDENCE`), with a real check that can refuse |
| `ContextAssembler` | groups typed items into a labeled prompt, in a fixed section order |

## Installation

```bash
git clone https://github.com/Emmimal/context-type-system.git
cd context-type-system
```

No dependencies to install. Everything runs on the Python 3 standard library — no `pip install` required, not even for testing.

## Quick Start

```python
from validator import ContextStore
from assembler import ContextAssembler
from transforms import validate_tool_result
from context_types import ContextTypeError

store = ContextStore()

store.add_context(
    context_type="instruction",
    content="Answer using current order information.",
    source="system",
)

tool_item = store.add_context(
    context_type="tool_output",
    content="Order #1842: estimated delivery August 19.",
    source="tool:order_lookup",
)

# Legitimate promotion — validated, leaves a derived_from lineage trail
evidence_item = validate_tool_result(store, tool_item)

# The same content, relabeled straight into the instruction channel, is rejected
try:
    store.add_context(
        context_type="instruction",
        content=tool_item.content,
        source="tool:order_lookup",
    )
except ContextTypeError as e:
    print(f"REJECTED: {e}")

print(ContextAssembler().assemble(store.items()))
```

## Running the Demos

Two runnable scripts, no network calls, no API keys:

```bash
python demo.py
python tests.py
```

| Script | What it shows |
|---|---|
| `demo.py` | the order-lookup walkthrough — provenance ledger, a legitimate promotion, a rejected relabel, final assembled prompt |
| `tests.py` | eight correctness checks — type registration, invalid promotion, provenance across transformation, separation of memory and evidence, failed-tool-output validation |

Both finish in well under a second. `request_id` values come from unseeded `uuid.uuid4()`, so your hex strings won't match any example output — the pass/fail behavior and structure will.

## Configuration Reference

Policy is two static definitions in `policy.py`:

```python
PROTECTED_TYPES = {
    ContextType.INSTRUCTION,
}

ALLOWED_TRANSITIONS = {
    (ContextType.TOOL_OUTPUT, ContextType.EVIDENCE),
    (ContextType.EVIDENCE, ContextType.MEMORY),
}
```

`PROTECTED_TYPES` — channels that can't be silently relabeled into; content of a different origin type needs an explicit, policy-checked `transform()` call to enter. Only `INSTRUCTION` is protected in this version.

`ALLOWED_TRANSITIONS` — the whitelist of `(from_type, to_type)` pairs a `transform()` call is permitted to cross. Anything not listed here can't be transformed at all, even explicitly.

Both are plain module-level sets. Extending either is a one-line edit, not a config format to learn.

## Project Structure

```
context-type-system/
├── __init__.py          # Public API surface
├── context_types.py      # ContextType enum, ContextTypeError
├── context_item.py       # ContextItem dataclass with provenance fields
├── policy.py              # PROTECTED_TYPES, ALLOWED_TRANSITIONS
├── validator.py           # ContextStore — the ledger and enforcement logic
├── assembler.py           # ContextAssembler — typed items to final prompt
├── transforms.py          # Example explicit transform (tool_output → evidence)
├── demo.py                # Order-lookup walkthrough
└── tests.py                # Eight correctness checks
```

## When to Use This

Worth it when you have:
- An agent pipeline that assembles prompts from more than one source — retrieved documents, tool results, conversation memory, system instructions
- A bug that looked like a model quality problem but turned out to be a tool result or stale memory item getting treated as something it wasn't
- A debugging process that currently means staring at one giant serialized prompt string trying to trace where a line came from

Skip it when you have:
- A single system prompt and a single user message, with nothing retrieved, remembered, or tool-derived
- A need for a benchmark showing improved task accuracy — this measures structural correctness, not model performance
- A need for a drop-in orchestration framework — this is one narrow mechanism, not retrieval, memory, or tool routing

## Known Limitations

- **Ledger key is a normalized string, not a content hash.** Two different pieces of content that normalize to the same string collide and share an origin record. Fine at prototype scale; a real hash with explicit collision handling is the honest next step for high-volume use.
- **Only `INSTRUCTION` is a protected type.** Evidence, memory, and tool output can be relabeled into each other more freely. Deliberate scope decision, not an oversight — extending `PROTECTED_TYPES` to cover more channels is a one-line change if your use case needs it.
- **IDs are not reproducible across runs.** `request_id` uses unseeded `uuid.uuid4()`. Logical behavior (what gets rejected, what gets promoted) is identical run to run; the specific hex strings never are.
- **No persistence, no concurrency handling.** `ContextStore` is in-memory for the lifetime of a single process. No thread locks, no serialization layer.
- **No type inference.** The caller declares a value's type when it enters the store (`add_context(context_type=...)`). Nothing here scans text to guess whether a string looks like an instruction or evidence — that's a separate, much harder problem, deliberately left out.
- **No performance numbers.** The type checks here run in microseconds — noise next to any real model call. A benchmark table would measure something that doesn't matter yet.

## License

MIT. See [LICENSE](LICENSE).
