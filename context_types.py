"""
context_types.py

Defines the four primary semantic types a piece of context can carry
before it is serialized into a model prompt.

The vocabulary is intentionally small. The point isn't the specific
four names — it's that context stops being an undifferentiated string
the moment it enters the runtime.
"""

from enum import Enum


class ContextType(str, Enum):
    INSTRUCTION = "instruction"
    EVIDENCE = "evidence"
    MEMORY = "memory"
    TOOL_OUTPUT = "tool_output"


class ContextTypeError(Exception):
    """Raised when the runtime is asked to perform an invalid
    context operation — e.g. inserting tool output directly into
    the instruction channel without an explicit transformation."""
    pass
