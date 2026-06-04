# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""RCGov pipeline orchestration (spec v0.4 §5).

    Input Files
      -> Ingest -> Segment -> Scan (secret / prompt-injection)
      -> Propose (role / authority / temporal) -> Provenance
      -> Non-Compensatory Gates -> Priority Ranking -> Pack Placement
      -> Clean Context Pack + Non-Injection Report + Override / Outcome logs

STATUS: skeleton. The stages that are fully determined by the contract (scan,
gates, priority combine, friction routing) are implemented in their modules; the
proposal/provenance/segmentation stages raise NotImplementedError until built.
This module wires them together and defines the run configuration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .contract import OUTPUT_FILES

__all__ = ["RunConfig", "GovernanceRun", "run"]


@dataclass
class RunConfig:
    """Configuration for one governance run."""

    task: str
    profile: str = "Balanced"  # Conservative / Balanced / Aggressive / Research
    temporal_attention: bool = False  # experimental opt-in (spec §8.3)
    output_dir: Path = field(default_factory=lambda: Path("out"))
    injection_seeds_path: Path | None = Path("config/injection_seeds.yaml")
    secret_patterns_path: Path | None = Path("config/secret_patterns.yaml")


@dataclass
class GovernanceRun:
    """Result handle: produced artifact paths and a short summary."""

    config: RunConfig
    artifacts: dict[str, Path] = field(default_factory=dict)
    summary: str = ""


def run(input_files: list[str | Path], config: RunConfig) -> GovernanceRun:
    """Execute the full pipeline over ``input_files``.

    The wiring order is fixed by spec §5. Each stage is delegated to its module;
    this skeleton raises from the first un-built stage (ingest) so the failure is
    honest rather than silently producing an empty pack.
    """
    raise NotImplementedError(
        "pipeline.run: wire ingest -> segment -> scan -> propose -> provenance "
        f"-> gates -> priority -> pack, emitting {list(OUTPUT_FILES)} into "
        f"{config.output_dir}. Stage modules under src/rcgov/ carry the detail."
    )
