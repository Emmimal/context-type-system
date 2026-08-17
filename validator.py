"""
validator.py

ContextStore is the runtime boundary. Every piece of context enters
through add_context(). The store keeps a ledger of what type each
piece of content was first registered under, so it can catch the
specific failure mode this project is about: content that originated
as one type (say, tool output) being silently re-labeled as a more
trusted type (say, an instruction) somewhere downstream.

Legitimate type changes still happen — a tool result really can
become evidence once it's been checked. Those go through transform(),
which leaves a visible record (derived_from) instead of happening as
an invisible side effect of string concatenation.
"""

from typing import Dict, List, Tuple

from context_item import ContextItem
from context_types import ContextType, ContextTypeError
from policy import PROTECTED_TYPES, transition_allowed


class ContextStore:
    def __init__(self):
        self._items: List[ContextItem] = []
        # content (normalized) -> (original ContextType, request_id)
        self._ledger: Dict[str, Tuple[ContextType, str]] = {}

    @staticmethod
    def _key(content: str) -> str:
        return " ".join(content.split()).lower()

    def add_context(
        self,
        context_type,
        content: str,
        source: str = None,
        priority: int = 0,
        _via_transform: bool = False,
        _derived_from: str = None,
    ) -> ContextItem:
        context_type = ContextType(context_type)
        key = self._key(content)

        existing = self._ledger.get(key)
        if existing is not None:
            origin_type, origin_id = existing
            if origin_type != context_type:
                if context_type in PROTECTED_TYPES and not _via_transform:
                    raise ContextTypeError(
                        f"{origin_type.value} cannot be inserted into "
                        f"{context_type.value} context "
                        f"(content first registered as {origin_type.value}, id={origin_id})"
                    )
        item = ContextItem(
            context_type=context_type,
            content=content,
            source=source,
            priority=priority,
            derived_from=_derived_from,
        )

        if existing is None:
            # First time this content has been seen — this item becomes
            # the permanent origin record for the ledger key.
            self._ledger[key] = (context_type, item.request_id)

        self._items.append(item)
        return item

    def transform(self, item: ContextItem, to_type, source: str = None) -> ContextItem:
        """Explicitly move content from one type to another. Raises
        ContextTypeError if the transition isn't in the allowed policy."""
        to_type = ContextType(to_type)
        if not transition_allowed(item.context_type, to_type):
            raise ContextTypeError(
                f"transition {item.context_type.value} -> {to_type.value} "
                f"is not permitted by policy"
            )
        new_item = self.add_context(
            context_type=to_type,
            content=item.content,
            source=source or item.source,
            priority=item.priority,
            _via_transform=True,
            _derived_from=item.request_id,
        )
        return new_item

    def items(self) -> List[ContextItem]:
        return list(self._items)

    def items_of_type(self, context_type) -> List[ContextItem]:
        context_type = ContextType(context_type)
        return [i for i in self._items if i.context_type == context_type]
