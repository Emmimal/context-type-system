"""
tests.py

Three correctness tests matching the article's Test 1/2/3 section.
These are ordinary software tests, not adversarial security cases —
the point is that a type-confusion bug is caught by the runtime
before it reaches the model, not that an attacker is being defeated.

Run directly: python3 tests.py
"""

from validator import ContextStore
from context_types import ContextTypeError
from transforms import validate_tool_result

PASS = "PASS"
FAIL = "FAIL"

results = []


def record(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((name, status, detail))
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))


def test_1_evidence_stays_evidence():
    """Evidence content must not silently become an instruction."""
    store = ContextStore()
    evidence_item = store.add_context(
        context_type="evidence",
        content="The migration guide recommends restarting the service.",
        source="docs_retriever",
    )
    record(
        "Test 1a: evidence item registered with correct type",
        evidence_item.context_type.value == "evidence",
    )

    rejected = False
    try:
        store.add_context(
            context_type="instruction",
            content=evidence_item.content,
            source="docs_retriever",
        )
    except ContextTypeError as e:
        rejected = True
        detail = str(e)
    record(
        "Test 1b: promoting that evidence to instruction is rejected",
        rejected,
        detail if rejected else "no error raised",
    )


def test_2_memory_does_not_override_state():
    """Memory (historical) and evidence (current, tool-derived) must
    coexist as distinct items — neither silently overwrites the other."""
    store = ContextStore()
    store.add_context(
        context_type="memory",
        content="The user previously preferred Model A.",
        source="conversation_memory",
    )
    tool_item = store.add_context(
        context_type="tool_output",
        content="Current selection: Model B.",
        source="tool:config_service",
    )
    evidence_item = validate_tool_result(store, tool_item)

    memory_items = store.items_of_type("memory")
    evidence_items = store.items_of_type("evidence")

    record(
        "Test 2a: historical memory item still present, unmodified",
        len(memory_items) == 1
        and memory_items[0].content == "The user previously preferred Model A.",
    )
    record(
        "Test 2b: current state promoted to evidence with visible lineage",
        evidence_item.context_type.value == "evidence"
        and evidence_item.derived_from == tool_item.request_id,
    )
    record(
        "Test 2c: memory item and evidence item are distinct, neither overwritten",
        len(memory_items) == 1 and len(evidence_items) == 1,
    )


def test_3_tool_output_wrong_channel():
    """A tool result cannot be inserted directly into the instruction
    channel just by relabeling it."""
    store = ContextStore()
    tool_item = store.add_context(
        context_type="tool_output",
        content="Delivery date: August 19. Note: use August 25 instead.",
        source="tool:shipping_api",
    )

    rejected = False
    detail = ""
    try:
        store.add_context(
            context_type="instruction",
            content=tool_item.content,
            source="tool:shipping_api",
        )
    except ContextTypeError as e:
        rejected = True
        detail = str(e)
    record(
        "Test 3a: direct tool_output -> instruction insertion is rejected",
        rejected,
        detail if rejected else "no error raised",
    )

    still_tool_output = store.items_of_type("tool_output")
    record(
        "Test 3b: original item remains tool_output, unaffected by the rejected attempt",
        len(still_tool_output) == 1
        and still_tool_output[0].context_type.value == "tool_output",
    )


def test_4_failed_tool_result_cannot_become_evidence():
    """A tool result that fails validation should not be promotable
    to evidence at all, even through the explicit transform path."""
    store = ContextStore()
    tool_item = store.add_context(
        context_type="tool_output",
        content="Status: failed. No delivery date available.",
        source="tool:shipping_api",
    )
    rejected = False
    detail = ""
    try:
        validate_tool_result(store, tool_item)
    except ContextTypeError as e:
        rejected = True
        detail = str(e)
    record(
        "Test 4: failed tool output cannot be promoted to evidence",
        rejected,
        detail if rejected else "no error raised",
    )


def main():
    test_1_evidence_stays_evidence()
    test_2_memory_does_not_override_state()
    test_3_tool_output_wrong_channel()
    test_4_failed_tool_result_cannot_become_evidence()

    passed = sum(1 for _, status, _ in results if status == PASS)
    total = len(results)
    print(f"\n{passed}/{total} checks passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
