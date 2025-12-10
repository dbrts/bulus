"""Core stubs for the bulus package."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List


@dataclass
class IceLedger:
    """Simple immutable-ish ledger placeholder for future state management."""

    _entries: List[Any] = field(default_factory=list)

    def record(self, event: Any) -> "IceLedger":
        """Return a new ledger with the event appended."""
        return IceLedger([*self._entries, event])

    def replay(self) -> Iterable[Any]:
        """Iterate through recorded events in order."""
        return tuple(self._entries)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._entries)
