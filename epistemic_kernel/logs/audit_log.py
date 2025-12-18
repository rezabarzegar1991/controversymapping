"""Append-only audit log with signed hashing."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import List, Literal
from uuid import UUID, uuid4

Actor = Literal["human", "agent"]
Entity = Literal["Reference", "Protocol", "Extraction"]


def sign_log(payload: str) -> str:
    return sha256(payload.encode()).hexdigest()


@dataclass(frozen=True)
class AuditLog:
    id: UUID
    actor: Actor
    action_type: str
    entity: Entity
    entity_id: UUID
    timestamp: datetime
    payload: dict
    hash: str


class AppendOnlyAuditStore:
    """Enforces append-only semantics; entries cannot be mutated or removed."""

    def __init__(self) -> None:
        self._entries: List[AuditLog] = []

    def append(self, actor: Actor, action_type: str, entity: Entity, entity_id: UUID, payload: dict) -> AuditLog:
        serialized = f"{actor}|{action_type}|{entity}|{entity_id}|{payload}"
        digest = sign_log(serialized)
        entry = AuditLog(
            id=uuid4(),
            actor=actor,
            action_type=action_type,
            entity=entity,
            entity_id=entity_id,
            timestamp=datetime.utcnow(),
            payload=payload,
            hash=digest,
        )
        self._entries.append(entry)
        return entry

    def entries(self) -> List[AuditLog]:
        return list(self._entries)


__all__ = ["AuditLog", "AppendOnlyAuditStore", "sign_log"]
