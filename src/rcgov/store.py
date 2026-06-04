# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Content-addressed text store (Decision Record 3a).

Segment and document text live *behind a reference*, not inline. This keeps the
contract objects light, makes hashes stable, and avoids duplicating sensitive
text across many records. The MVP backend is the local filesystem; the ``ref``
scheme is ``rcgovstore://<sha256hex>`` so it round-trips through JSON cleanly.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

__all__ = ["TextStore", "REF_SCHEME"]

REF_SCHEME = "rcgovstore://"


class TextStore:
    """Filesystem-backed content-addressed store under ``root``."""

    def __init__(self, root: str | Path = ".rcgov_store") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, sha_hex: str) -> Path:
        return self.root / f"{sha_hex}.txt"

    def put(self, text: str) -> str:
        """Store ``text`` and return its ``rcgovstore://`` reference."""
        data = text.encode("utf-8")
        sha_hex = hashlib.sha256(data).hexdigest()
        path = self._path(sha_hex)
        if not path.exists():  # content-addressed: identical text writes once
            path.write_bytes(data)
        return REF_SCHEME + sha_hex

    def get(self, ref: str) -> str:
        """Resolve a reference back to its stored text."""
        if not ref.startswith(REF_SCHEME):
            raise ValueError(f"not a store ref: {ref!r}")
        sha_hex = ref[len(REF_SCHEME):]
        path = self._path(sha_hex)
        if not path.exists():
            raise KeyError(f"ref not found in store: {ref}")
        return path.read_text(encoding="utf-8")

    @staticmethod
    def hash_of(text: str) -> str:
        """Contract-form hash (``sha256:...``) of ``text``."""
        return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
