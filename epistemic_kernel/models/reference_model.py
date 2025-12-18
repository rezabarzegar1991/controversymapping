"""Immutable Reference object for ingestion provenance and content integrity."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from typing import List, Literal, Optional
from uuid import UUID, uuid4


IngestionSource = Literal["PubMed", "ClinicalTrials.gov"]


def _now() -> datetime:
    return datetime.utcnow()


def compute_source_hash(payload: dict) -> str:
    """Hash structured metadata for tamper evidence."""
    canonical = str(sorted(payload.items())).encode()
    return sha256(canonical).hexdigest()


@dataclass(frozen=True)
class IngestionProvenance:
    source: IngestionSource
    query: str
    timestamp: datetime
    raw_response: dict


@dataclass(frozen=True)
class ReferenceContent:
    title: str
    authors: List[str]
    abstract: str
    doi: str
    journal: str
    pub_date: datetime


@dataclass(frozen=True)
class Reference:
    """Immutable Reference; any change must produce a new instance."""

    content: ReferenceContent
    ingestion_provenance: IngestionProvenance
    source_hash: str
    created_at: datetime = field(default_factory=_now)
    id: UUID = field(default_factory=uuid4)
    locked: bool = field(default=True, init=False, repr=True)
    parent_hash: Optional[str] = field(default=None, repr=True)

    def new_version(self, updated_content: ReferenceContent) -> "Reference":
        """Create a new immutable version referencing the previous hash."""
        previous_hash = self.compute_content_hash()
        return Reference(
            content=updated_content,
            ingestion_provenance=self.ingestion_provenance,
            source_hash=self.source_hash,
            parent_hash=previous_hash,
        )

    def compute_content_hash(self) -> str:
        canonical = {
            "title": self.content.title.strip().lower(),
            "doi": self.content.doi.strip().lower(),
            "authors": [a.strip().lower() for a in self.content.authors],
            "journal": self.content.journal.strip().lower(),
            "pub_date": self.content.pub_date.isoformat(),
        }
        return sha256(str(canonical).encode()).hexdigest()


__all__ = [
    "Reference",
    "ReferenceContent",
    "IngestionProvenance",
    "compute_source_hash",
]
