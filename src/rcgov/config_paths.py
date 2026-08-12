# SPDX-License-Identifier: AGPL-3.0-or-later
"""Locate RCGov's YAML configuration regardless of the process's cwd.

Before this module existed, ``RunConfig`` defaulted to the *relative* path
``config/injection_seeds.yaml``. That resolves only when the process happens
to run from a checkout root, and ``load_seeds`` treats a missing file as
"no extra seeds" **silently** — so every library consumer (proxy, secretary,
Space, any wheel install) ran with the five built-in seeds alone while the
report still printed "Prompt-Injection Residue: (none)". The failure was
invisible, which is what made it dangerous.

Resolution order, first hit wins:

1. ``./config/<name>``            — an operator override in the working dir
2. ``<repo>/config/<name>``       — a source checkout / editable install
3. ``rcgov/config/<name>``        — the packaged default (ships in the wheel)

Returns ``None`` only when no copy exists anywhere, which now means the file
is genuinely absent rather than merely out of reach.
"""
from __future__ import annotations

from pathlib import Path

__all__ = ["resolve_config", "packaged_config_dir"]

_PKG_DIR = Path(__file__).resolve().parent


def packaged_config_dir() -> Path:
    """Directory holding the defaults that ship inside the distribution."""
    return _PKG_DIR / "config"


def resolve_config(name: str) -> Path | None:
    """Return the first existing copy of config file ``name``, or None."""
    candidates = (
        Path("config") / name,                       # 1. operator override
        _PKG_DIR.parents[1] / "config" / name,       # 2. source checkout
        packaged_config_dir() / name,                # 3. packaged default
    )
    for candidate in candidates:
        try:
            if candidate.is_file():
                # Absolute: a relative hit would silently break if anything
                # changes the working directory between resolution and use.
                return candidate.resolve()
        except OSError:  # unreadable path must not break governance
            continue
    return None
