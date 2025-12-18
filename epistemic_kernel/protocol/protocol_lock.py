"""Protocol lock engine enforcing amendment flow and immutability."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ProtocolAmendment:
    id: UUID
    protocol_id: UUID
    reason: str
    timestamp: datetime
    diff: dict


@dataclass
class Protocol:
    id: UUID
    title: str
    objective: str
    registered_on: datetime
    locked: bool = False
    lock_timestamp: datetime | None = None
    amendments: List[ProtocolAmendment] = field(default_factory=list)

    def lock(self) -> None:
        if self.locked:
            return
        self.locked = True
        self.lock_timestamp = datetime.utcnow()

    def assert_editable(self) -> None:
        if self.locked:
            raise PermissionError("Protocol is locked; edits require amendments.")

    def amend(self, reason: str, diff: dict) -> ProtocolAmendment:
        if not self.locked:
            raise PermissionError("Protocol must be locked before amendments are recorded.")
        amendment = ProtocolAmendment(
            id=uuid4(),
            protocol_id=self.id,
            reason=reason,
            timestamp=datetime.utcnow(),
            diff=diff,
        )
        self.amendments.append(amendment)
        return amendment


class ProtocolRegistry:
    """Minimal registry for storing and enforcing protocol locks."""

    def __init__(self) -> None:
        self._protocols: Dict[UUID, Protocol] = {}

    def register(self, title: str, objective: str, registered_on: datetime | None = None) -> Protocol:
        protocol = Protocol(
            id=uuid4(),
            title=title,
            objective=objective,
            registered_on=registered_on or datetime.utcnow(),
        )
        self._protocols[protocol.id] = protocol
        return protocol

    def get(self, protocol_id: UUID) -> Protocol:
        return self._protocols[protocol_id]

    def require_locked(self, protocol_id: UUID) -> Protocol:
        protocol = self.get(protocol_id)
        if not protocol.locked:
            raise PermissionError("Protocol is not locked; operation blocked.")
        return protocol


__all__ = ["Protocol", "ProtocolAmendment", "ProtocolRegistry"]
