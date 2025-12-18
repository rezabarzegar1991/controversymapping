"""Hash-based deduplication for Reference objects (PRISMA 16a)."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Dict, Set
from uuid import UUID

from epistemic_kernel.models.reference_model import Reference


def hash_reference(reference: Reference) -> str:
    canonical = {
        "title": reference.content.title.strip().lower(),
        "doi": reference.content.doi.strip().lower(),
        "authors": [a.strip().lower() for a in reference.content.authors],
    }
    return sha256(str(canonical).encode()).hexdigest()


@dataclass
class DedupResult:
    is_duplicate: bool
    existing_id: UUID | None = None


@dataclass
class DedupEngine:
    """In-memory deduplication index.

    Replace with persistent storage in production; interface stays the same.
    """

    index: Dict[str, UUID] = field(default_factory=dict)

    def check(self, reference: Reference) -> DedupResult:
        digest = hash_reference(reference)
        if digest in self.index:
            return DedupResult(is_duplicate=True, existing_id=self.index[digest])
        return DedupResult(is_duplicate=False)

    def add(self, reference: Reference) -> str:
        digest = hash_reference(reference)
        self.index[digest] = reference.id
        return digest

    def seen_hashes(self) -> Set[str]:
        return set(self.index.keys())


__all__ = ["hash_reference", "DedupEngine", "DedupResult"]
