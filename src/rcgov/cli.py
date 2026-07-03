# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""RCGov command-line entry point (``rcgov`` console script).

``rcgov`` (no subcommand) reports the pinned contract version; ``rcgov govern``
runs the full governance pipeline (``rcgov.pipeline.run``) end-to-end and writes
the Clean Pack and reports to ``--out``.
"""
from __future__ import annotations

import argparse
import sys

from . import __version__
from .contract import CONTRACT_VERSION, OUTPUT_FILES


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rcgov", description="Mobius Reflective Context Governor")
    p.add_argument("--version", action="store_true", help="print versions and exit")
    sub = p.add_subparsers(dest="command")

    g = sub.add_parser("govern", help="govern a set of input files into a clean pack")
    g.add_argument("files", nargs="+", help="input files to govern")
    g.add_argument("--task", required=True, help="describe the current task")
    g.add_argument(
        "--profile",
        default="Balanced",
        choices=["Conservative", "Balanced", "Aggressive", "Research"],
    )
    g.add_argument("--temporal-attention", action="store_true",
                   help="enable the experimental temporal-attention pack profile")
    g.add_argument("--commitments", default="config/commitments.yaml",
                   help="authority commitment manifest (Authority Stabilization Mode)")
    g.add_argument("--out", default="out", help="output directory")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.version or args.command is None:
        print(f"rcgov {__version__} (contract v{CONTRACT_VERSION})")
        print("outputs: " + ", ".join(OUTPUT_FILES))
        return 0
    if args.command == "govern":
        from pathlib import Path

        from .pipeline import RunConfig, run

        cfg = RunConfig(
            task=args.task, profile=args.profile,
            temporal_attention=args.temporal_attention,
            output_dir=Path(args.out),
            commitments_path=Path(args.commitments) if args.commitments else None,
        )
        result = run(args.files, cfg)
        print(result.summary)
        for name in sorted(result.artifacts):
            print(f"  {result.artifacts[name]}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
