#!/usr/bin/env python3
"""Check the qualified-buyer follow-up package and generated runtime artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "prophet_buyer_follow_up_package_check.v0.1"
DEFAULT_DOCS = (
    "docs/BUYER_FOLLOW_UP_PACKAGE.md",
    "docs/EVALUATOR_START_HERE.md",
    "docs/PILOT_SCOPE.md",
    "docs/DESIGN_PARTNER_PILOT_OFFER.md",
    "docs/EVALUATOR_WORKSHEET.md",
    "docs/BUYER_FAQ.md",
)
REQUIRED_DOC_PHRASES = {
    "docs/BUYER_FOLLOW_UP_PACKAGE.md": (
        "Use this after a qualified buyer has described a real prioritization workflow",
        "Do not send if the buyer only asked for offensive validation, live target",
        "Production pushes require a separate approved scope.",
        "the pilot should not be represented as CMMC, FedRAMP, SOC 2, or production SaaS ready.",
    ),
    "docs/PILOT_SCOPE.md": (
        "a hosted production architecture.",
        "no production pushes.",
        "`build_next_slice` opens production implementation scope.",
    ),
    "docs/DESIGN_PARTNER_PILOT_OFFER.md": (
        "a broad production platform. Offer one evidence workflow.",
        "Private validation reaches `build_next_slice`.",
        "Unvalidated platform roadmap, multi-tenant production scope, unrelated features.",
    ),
    "docs/EVALUATOR_WORKSHEET.md": (
        "no live targets, no payloads, no raw telemetry, no production pushes",
        "Does the validation dashboard still keep production build scope closed unless it reaches `build_next_slice`?",
    ),
}
DEFAULT_RUNTIME_ARTIFACTS = (
    "evidence/outputs/runtime/latest-edge-appliance.json",
    "evidence/outputs/runtime/latest-edge-appliance.md",
    "integrations/outputs/runtime/latest-edge-appliance/manifest.json",
    "integrations/outputs/runtime/latest-edge-appliance/review_checklist.md",
    "integrations/outputs/runtime/latest-edge-appliance-review-bundle.zip",
)
SMOKE_HASHES = Path("scripts/pilot-demo-smoke.sha256")
TRUE_SAFETY_FLAGS = (
    "no_credentials",
    "no_live_target_data_included",
    "no_live_targets",
    "no_payloads",
    "no_private_hostnames",
)


class BuyerFollowUpCheckError(ValueError):
    """Raised when the buyer follow-up package cannot be checked."""


def check_package(
    *,
    root: Path,
    docs: tuple[str, ...] = DEFAULT_DOCS,
    runtime_artifacts: tuple[str, ...] = DEFAULT_RUNTIME_ARTIFACTS,
    smoke_hashes: Path = SMOKE_HASHES,
    check_git: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    issues: list[dict[str, str]] = []
    doc_summaries = [_check_doc(root, doc, check_git, issues) for doc in docs]
    expected_hashes = _load_smoke_hashes(root / smoke_hashes)
    runtime_summaries = [
        _check_runtime_artifact(root, artifact, expected_hashes, check_git, issues)
        for artifact in runtime_artifacts
    ]
    evidence_summary = _check_evidence(root / runtime_artifacts[0], runtime_artifacts[0], issues)
    handoff_summary = _check_handoff_manifest(root / runtime_artifacts[2], runtime_artifacts[2], issues)
    zip_summary = _check_zip(root / runtime_artifacts[4], runtime_artifacts[4], expected_hashes, issues)
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "doc_count": len(doc_summaries),
        "runtime_artifact_count": len(runtime_summaries),
        "docs": doc_summaries,
        "runtime_artifacts": runtime_summaries,
        "evidence": evidence_summary,
        "handoff_manifest": handoff_summary,
        "review_zip": zip_summary,
        "issues": issues,
        "operator_notes": [
            "Run ./scripts/run-pilot-demo-smoke.sh before this check if runtime artifacts are missing or hashes are stale.",
            "Run release-safety on committed docs/code, not ignored runtime artifacts.",
            "Keep generated runtime artifacts ignored, untracked, and unstaged.",
            "Use this package only after a qualified buyer has described a real prioritization workflow.",
        ],
    }


def render_text(summary: dict[str, Any]) -> str:
    lines = [
        "# Prophet Buyer Follow-Up Package Check",
        "",
        f"- OK: {str(summary['ok']).lower()}",
        f"- Docs: {summary['doc_count']}",
        f"- Runtime artifacts: {summary['runtime_artifact_count']}",
        f"- Evidence bundle: {summary['evidence'].get('bundle_id', 'unknown')}",
        f"- Handoff manifest: {summary['handoff_manifest'].get('export_id', 'unknown')}",
        f"- Review ZIP SHA-256: {summary['review_zip'].get('sha256', 'unknown')}",
        "",
        "## Runtime Boundary",
    ]
    for artifact in summary["runtime_artifacts"]:
        lines.append(
            "- {path}: exists={exists}, ignored={ignored}, tracked={tracked}, hash_match={hash_match}".format(
                path=artifact["path"],
                exists=str(artifact["exists"]).lower(),
                ignored=str(artifact.get("ignored", False)).lower(),
                tracked=str(artifact.get("tracked", False)).lower(),
                hash_match=str(artifact.get("hash_matches_expected", False)).lower(),
            )
        )
    if summary["issues"]:
        lines.extend(["", "## Issues"])
        for issue in summary["issues"]:
            lines.append(f"- {issue['path']}: {issue['message']}")
    lines.extend(["", "## Operator Notes"])
    for note in summary["operator_notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the qualified-buyer follow-up package readiness."
    )
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument(
        "--skip-git-boundary",
        action="store_true",
        help="Skip git tracked/ignored checks. Intended only for isolated unit tests.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format.",
    )
    args = parser.parse_args(argv)
    try:
        summary = check_package(
            root=Path(args.root),
            check_git=not args.skip_git_boundary,
        )
    except (OSError, json.JSONDecodeError, BuyerFollowUpCheckError) as exc:
        print(f"buyer follow-up package check failed: {exc}", file=sys.stderr)
        return 1
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(render_text(summary), end="")
    return 0 if summary["ok"] else 1


def _check_doc(root: Path, path: str, check_git: bool, issues: list[dict[str, str]]) -> dict[str, Any]:
    full_path = root / path
    exists = full_path.is_file()
    tracked = _git_path_is_tracked(root, path) if check_git and exists else False
    missing_required_phrases: list[str] = []
    if not exists:
        _issue(issues, path, "required follow-up document is missing")
    elif check_git and not tracked:
        _issue(issues, path, "follow-up document must be tracked")
    if exists:
        text = full_path.read_text(encoding="utf-8")
        missing_required_phrases = [
            phrase
            for phrase in REQUIRED_DOC_PHRASES.get(path, ())
            if phrase not in text
        ]
        for phrase in missing_required_phrases:
            _issue(issues, path, f"missing required buyer-boundary phrase: {phrase}")
    return {
        "path": path,
        "exists": exists,
        "tracked": tracked,
        "required_phrase_count": len(REQUIRED_DOC_PHRASES.get(path, ())),
        "missing_required_phrases": missing_required_phrases,
    }


def _check_runtime_artifact(
    root: Path,
    path: str,
    expected_hashes: dict[str, str],
    check_git: bool,
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    full_path = root / path
    exists = full_path.is_file()
    tracked = _git_path_is_tracked(root, path) if check_git and exists else False
    ignored = _git_path_is_ignored(root, path) if check_git and exists else False
    sha256 = _sha256(full_path) if exists else None
    expected = expected_hashes.get(path)
    hash_matches = bool(sha256 and expected and sha256 == expected)
    if not exists:
        _issue(issues, path, "runtime artifact is missing; run ./scripts/run-pilot-demo-smoke.sh")
    if exists and check_git and not ignored:
        _issue(issues, path, "runtime artifact must stay ignored")
    if exists and check_git and tracked:
        _issue(issues, path, "runtime artifact must stay untracked")
    if exists and expected is None:
        _issue(issues, path, "runtime artifact is not listed in scripts/pilot-demo-smoke.sha256")
    if exists and expected is not None and sha256 != expected:
        _issue(issues, path, "runtime artifact hash does not match smoke manifest; rerun pilot smoke")
    return {
        "path": path,
        "exists": exists,
        "ignored": ignored,
        "tracked": tracked,
        "sha256": sha256,
        "expected_sha256": expected,
        "hash_matches_expected": hash_matches,
    }


def _check_evidence(path: Path, label: str, issues: list[dict[str, str]]) -> dict[str, Any]:
    if not path.is_file():
        return {"path": label, "exists": False}
    evidence = json.loads(path.read_text(encoding="utf-8"))
    safety = _dict(evidence.get("safety_attestation"))
    redaction = _dict(evidence.get("redaction_report"))
    if evidence.get("schema_version") != "prophet_evidence_bundle.v0.1":
        _issue(issues, label, "unexpected evidence schema_version")
    for flag in (*TRUE_SAFETY_FLAGS, "no_raw_scraper_text"):
        if safety.get(flag) is not True:
            _issue(issues, label, f"safety_attestation.{flag} must be true")
    for flag in (
        "raw_asset_inventory_embedded",
        "raw_defense_artifact_embedded",
        "raw_forecast_embedded",
        "raw_osint_records_embedded",
        "raw_prediction_portfolio_embedded",
        "raw_validation_logs_embedded",
    ):
        if redaction.get(flag) is not False:
            _issue(issues, label, f"redaction_report.{flag} must be false")
    return {
        "path": label,
        "exists": True,
        "schema_version": evidence.get("schema_version"),
        "bundle_id": evidence.get("bundle_id"),
        "policy_id": (_dict(evidence.get("policy"))).get("policy_id"),
        "safety_flags_ok": all(safety.get(flag) is True for flag in (*TRUE_SAFETY_FLAGS, "no_raw_scraper_text")),
        "redaction_summary_only": redaction.get("summary_fields_only") is True,
    }


def _check_handoff_manifest(path: Path, label: str, issues: list[dict[str, str]]) -> dict[str, Any]:
    if not path.is_file():
        return {"path": label, "exists": False}
    manifest = json.loads(path.read_text(encoding="utf-8"))
    safety = _dict(manifest.get("safety_attestation"))
    placeholders = _dict(manifest.get("customer_placeholder_validation"))
    files = _dict(manifest.get("files"))
    if manifest.get("schema_version") != "prophet_integration_export.v0.1":
        _issue(issues, label, "unexpected handoff manifest schema_version")
    if manifest.get("mode") != "review_template_only":
        _issue(issues, label, "handoff manifest mode must be review_template_only")
    for flag in (*TRUE_SAFETY_FLAGS, "no_external_api_calls", "review_templates_only"):
        if safety.get(flag) is not True:
            _issue(issues, label, f"safety_attestation.{flag} must be true")
    if placeholders.get("review_template_only") is not True:
        _issue(issues, label, "customer placeholder validation must be review-template-only")
    if placeholders.get("status") != "customer_mapping_required":
        _issue(issues, label, "customer placeholder status must require mapping")
    if files.get("review_checklist") != "review_checklist.md":
        _issue(issues, label, "manifest must include review_checklist.md")
    return {
        "path": label,
        "exists": True,
        "schema_version": manifest.get("schema_version"),
        "export_id": manifest.get("export_id"),
        "mode": manifest.get("mode"),
        "policy_id": (_dict(manifest.get("policy_restrictions"))).get("policy_id"),
        "review_template_only": manifest.get("mode") == "review_template_only",
        "customer_mapping_required": placeholders.get("status") == "customer_mapping_required",
    }


def _check_zip(
    path: Path,
    label: str,
    expected_hashes: dict[str, str],
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    exists = path.is_file()
    sha256 = _sha256(path) if exists else None
    expected = expected_hashes.get(label)
    if not exists:
        _issue(issues, label, "review ZIP is missing")
    elif path.stat().st_size <= 0:
        _issue(issues, label, "review ZIP is empty")
    elif not zipfile.is_zipfile(path):
        _issue(issues, label, "review ZIP is not a valid ZIP archive")
    return {
        "path": label,
        "exists": exists,
        "sha256": sha256,
        "expected_sha256": expected,
        "hash_matches_expected": bool(sha256 and expected and sha256 == expected),
        "size_bytes": path.stat().st_size if exists else 0,
    }


def _load_smoke_hashes(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise BuyerFollowUpCheckError(f"missing smoke hash manifest: {path}")
    hashes: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 1)
        if len(parts) != 2:
            raise BuyerFollowUpCheckError(f"invalid smoke hash line: {line}")
        hashes[parts[1].strip()] = parts[0].strip()
    return hashes


def _git_path_is_tracked(root: Path, path: str) -> bool:
    return _git(root, ["ls-files", "--error-unmatch", path]).returncode == 0


def _git_path_is_ignored(root: Path, path: str) -> bool:
    return _git(root, ["check-ignore", "-q", path]).returncode == 0


def _git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _issue(issues: list[dict[str, str]], path: str, message: str) -> None:
    issues.append({"path": path, "message": message})


if __name__ == "__main__":
    raise SystemExit(main())
