"""
demo.py

Recreates the order-delivery example from the article: a tool result
contains a delivery date plus an unrelated "historical note" line.
The historical note should stay TOOL_OUTPUT provenance and must not
silently become MEMORY or an INSTRUCTION just because it reads like one.
"""

from validator import ContextStore
from assembler import ContextAssembler
from context_types import ContextTypeError
from transforms import validate_tool_result


def main():
    store = ContextStore()

    store.add_context(
        context_type="instruction",
        content="Answer using current order information.",
        source="system",
    )

    store.add_context(
        context_type="memory",
        content="The customer prefers concise answers.",
        source="conversation_memory",
    )

    tool_item = store.add_context(
        context_type="tool_output",
        content=(
            "Order #1842: estimated delivery August 19. "
            "Historical note: customer previously requested delivery on August 25."
        ),
        source="tool:order_lookup",
    )

    print("--- Provenance ledger after ingestion ---")
    for item in store.items():
        print(item.describe())

    print("\n--- Attempting to promote raw tool output straight to evidence ---")
    try:
        evidence_item = validate_tool_result(store, tool_item)
        print(
            f"PROMOTED: {evidence_item.context_type.value} "
            f"id={evidence_item.request_id} <- {evidence_item.derived_from}"
        )
    except ContextTypeError as e:
        print(f"REJECTED: {e}")

    print("\n--- Attempting to promote tool output directly into instruction ---")
    try:
        store.add_context(
            context_type="instruction",
            content=tool_item.content,
            source="tool:order_lookup",
        )
    except ContextTypeError as e:
        print(f"REJECTED: {e}")

    print("\n--- Final assembled prompt (tool output stays tool output) ---")
    assembler = ContextAssembler()
    print(assembler.assemble(store.items()))


if __name__ == "__main__":
    main()
