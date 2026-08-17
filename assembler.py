"""
assembler.py

Takes a list of typed ContextItems and produces the final string
sent to the model. Grouping happens by type, not by insertion order,
so the serialized prompt keeps the same semantic boundaries the
runtime enforced upstream.
"""

from typing import List

from context_item import ContextItem
from context_types import ContextType

SECTION_ORDER = [
    ContextType.INSTRUCTION,
    ContextType.MEMORY,
    ContextType.EVIDENCE,
    ContextType.TOOL_OUTPUT,
]

SECTION_LABELS = {
    ContextType.INSTRUCTION: "Instructions",
    ContextType.MEMORY: "Memory",
    ContextType.EVIDENCE: "Evidence",
    ContextType.TOOL_OUTPUT: "Tool Output",
}


class ContextAssembler:
    def assemble(self, items: List[ContextItem]) -> str:
        sections = []
        for context_type in SECTION_ORDER:
            matching = [i for i in items if i.context_type == context_type]
            if not matching:
                continue
            label = SECTION_LABELS[context_type]
            lines = [f"{label}:"]
            for item in sorted(matching, key=lambda i: -i.priority):
                lines.append(f"- {item.content}")
            sections.append("\n".join(lines))
        return "\n\n".join(sections)
