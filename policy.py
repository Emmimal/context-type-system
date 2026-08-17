"""
policy.py

Defines which context channels are "protected" — meaning content
cannot be silently reused under that type just because the caller
labeled it that way — and which type transformations are allowed to
happen explicitly, via a registered transform function.

This is deliberately boring, static configuration. Boundaries that
can be decided in advance shouldn't be left for the model, or for an
ad-hoc if-statement buried in application code, to decide at runtime.
"""

from context_types import ContextType

# Types where content cannot be promoted into this channel just by
# re-labeling it. The runtime must see an explicit, registered
# transformation before content of a different origin can enter.
PROTECTED_TYPES = {
    ContextType.INSTRUCTION,
}

# (from_type, to_type) -> True means a registered transform() call is
# permitted to move content across that boundary. Anything not listed
# here cannot be transformed at all, even explicitly.
ALLOWED_TRANSITIONS = {
    (ContextType.TOOL_OUTPUT, ContextType.EVIDENCE),
    (ContextType.EVIDENCE, ContextType.MEMORY),
}


def transition_allowed(from_type: ContextType, to_type: ContextType) -> bool:
    return (from_type, to_type) in ALLOWED_TRANSITIONS
