"""
context_item.py

A ContextItem is the unit the runtime operates on instead of a raw
string. It carries the content plus enough metadata (type, source,
lineage) for the runtime to reason about it before assembly.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from context_types import ContextType


@dataclass
class ContextItem:
    context_type: ContextType
    content: str
    source: Optional[str] = None
    priority: int = 0
    created: float = field(default_factory=time.time)
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    derived_from: Optional[str] = None  # request_id of the item this was transformed from

    def __post_init__(self):
        if not isinstance(self.context_type, ContextType):
            self.context_type = ContextType(self.context_type)
        if not self.content or not self.content.strip():
            raise ValueError("ContextItem content cannot be empty")

    def describe(self) -> str:
        origin = f" <- {self.derived_from}" if self.derived_from else ""
        return (
            f"[{self.context_type.value:<12}] "
            f"source={self.source or 'unknown':<20} "
            f"id={self.request_id}{origin}"
        )
