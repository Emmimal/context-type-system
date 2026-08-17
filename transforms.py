"""
transforms.py

Example of an explicit, application-defined transformation. Raw tool
output shouldn't become evidence just because it looks factual — this
function is the one place that promotion is allowed to happen, and it
runs a real check before letting it through.
"""

from context_item import ContextItem
from context_types import ContextTypeError
from validator import ContextStore


def validate_tool_result(store: ContextStore, tool_item: ContextItem) -> ContextItem:
    """Promote a TOOL_OUTPUT item to EVIDENCE, but only if it passes a
    minimal sanity check first. This is where real validation logic
    (schema checks, status-code checks, source allow-lists) would live."""
    if "error" in tool_item.content.lower() or "failed" in tool_item.content.lower():
        raise ContextTypeError(
            f"tool output from '{tool_item.source}' failed validation "
            f"and cannot become evidence: {tool_item.content!r}"
        )
    return store.transform(tool_item, to_type="evidence", source=tool_item.source)
