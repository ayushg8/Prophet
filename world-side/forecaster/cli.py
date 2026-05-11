"""Command line entrypoint for the World Side forecaster."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from .generator import SCHEMA_VERSION, assemble_forecast
except ImportError:  # pragma: no cover - direct script fallback
    from generator import SCHEMA_VERSION, assemble_forecast  # type: ignore


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        candidate = _load_candidate(args.candidate)
        forecast = assemble_forecast(
            candidate,
            data_dir=args.data_dir,
            generated_at=args.generated_at,
            chatter_paths=args.chatter,
            osint_snapshot_paths=args.osint_snapshot,
            osint_manifest_paths=args.osint_manifest,
            asset_seedset_paths=args.asset_seedset,
        )
        _write_forecast(forecast, args.out, compact=args.compact)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"forecaster: {exc}", file=sys.stderr)
        return 1

    if args.out:
        print(
            f"wrote {forecast['schema_version']} forecast to {args.out}",
            file=sys.stderr,
        )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m forecaster.cli",
        description="Assemble a Prophet World Side strike-window forecast JSON.",
    )
    parser.add_argument(
        "--candidate",
        required=True,
        type=Path,
        help="Path to a Cyber Side Direction A candidate JSON file.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Path to write the world_forecast.v0.1 JSON. Defaults to stdout.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=_default_data_dir(),
        help="Directory containing World Side markdown data files.",
    )
    parser.add_argument(
        "--generated-at",
        help="Optional ISO 8601 UTC timestamp for reproducible output.",
    )
    parser.add_argument(
        "--chatter",
        action="append",
        type=Path,
        default=[],
        help=(
            "Optional sanitized chatter JSONL file. May be repeated. "
            "Raw scraper output must never be passed here."
        ),
    )
    parser.add_argument(
        "--osint-snapshot",
        action="append",
        type=Path,
        default=[],
        help=(
            "Optional sanitized OSINT snapshot JSONL file. May be repeated. "
            "Only scraper_side.snapshot output or equivalent sanitized JSONL is allowed."
        ),
    )
    parser.add_argument(
        "--osint-manifest",
        action="append",
        type=Path,
        default=[],
        help="Optional OSINT snapshot manifest JSON file. May be repeated.",
    )
    parser.add_argument(
        "--asset-seedset",
        action="append",
        type=Path,
        default=[],
        help=(
            "Optional asset_osint_seedset.v0.1 JSON file. May be repeated. "
            "Use assets.inventory output, not raw asset exports."
        ),
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Write compact JSON instead of pretty-printed JSON.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=SCHEMA_VERSION,
    )
    return parser


def _default_data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


def _load_candidate(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"candidate file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("candidate JSON must be an object")
    return data


def _write_forecast(
    forecast: dict[str, Any],
    out_path: Path | None,
    *,
    compact: bool,
) -> None:
    if compact:
        payload = json.dumps(forecast, separators=(",", ":"), sort_keys=False)
    else:
        payload = json.dumps(forecast, indent=2, sort_keys=False)
    payload += "\n"

    if out_path is None:
        sys.stdout.write(payload)
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
