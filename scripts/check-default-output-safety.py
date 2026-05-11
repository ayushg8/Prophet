#!/usr/bin/env python3
"""Check policy-listed default outputs for live-target URL leakage."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEFAULT_POLICY = Path("policy/prophet-pilot-policy.json")
URL_RE = re.compile(r"https?://[^\s<>'\")]+", re.IGNORECASE)
DISALLOWED_URL_KEYS = {
    "asset_endpoint",
    "asset_url",
    "callback_endpoint",
    "callback_url",
    "customer_endpoint",
    "customer_url",
    "exploit_url",
    "external_endpoint",
    "external_url",
    "host_url",
    "hostname_url",
    "live_endpoint",
    "live_target_endpoint",
    "live_target_url",
    "live_url",
    "payload_url",
    "request_endpoint",
    "request_url",
    "system_endpoint",
    "system_url",
    "target_endpoint",
    "target_url",
    "validation_endpoint",
    "validation_url",
    "webhook_endpoint",
    "webhook_url",
}
DISALLOWED_PARENT_TERMS = {
    "asset",
    "callback",
    "customer",
    "exploit",
    "external",
    "host",
    "hostname",
    "live",
    "payload",
    "request",
    "system",
    "target",
    "validation",
    "webhook",
}
DISALLOWED_TEXT_URL_CONTEXT_RE = re.compile(
    r"(?i)\b("
    r"asset|callback|customer|exploit|external|host|hostname|live\s+target|"
    r"payload|request|system|target|validation|webhook"
    r")\s+(?:url|uri|endpoint)s?\b"
)
PRIVATE_HOST_SUFFIXES = (".internal", ".corp", ".local", ".lan", ".private")
ALLOWED_NONLIVE_NETWORKS = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("0.0.0.0/32"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
)


@dataclass(frozen=True)
class Issue:
    artifact: str
    location: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "artifact": self.artifact,
            "location": self.location,
            "message": self.message,
        }

    def format(self) -> str:
        return f"{self.artifact}:{self.location}: {self.message}"


def check_default_outputs(policy_path: Path, root: Path) -> dict[str, Any]:
    root = root.resolve()
    policy = _load_json(_resolve_path(policy_path, root))
    default_outputs = policy.get("default_outputs")
    if not isinstance(default_outputs, dict) or not default_outputs:
        raise ValueError("policy.default_outputs must be a non-empty object")

    issues: list[Issue] = []
    checked_outputs = 0
    url_count = 0
    for output_name, output_path in sorted(default_outputs.items()):
        if not isinstance(output_path, str) or not output_path:
            issues.append(
                Issue(
                    artifact=str(output_name),
                    location="policy.default_outputs",
                    message="default output path must be a non-empty string",
                )
            )
            continue
        artifact_path = _resolve_path(Path(output_path), root)
        artifact_label = str(output_path)
        if not artifact_path.exists():
            issues.append(
                Issue(
                    artifact=artifact_label,
                    location="path",
                    message="default output is missing",
                )
            )
            continue
        checked_outputs += 1
        url_count += _scan_artifact(artifact_path, artifact_label, issues)
    provenance_manifest_count = _check_osint_provenance(default_outputs, root, issues)

    return {
        "ok": not issues,
        "checked_outputs": checked_outputs,
        "provenance_manifest_count": provenance_manifest_count,
        "url_count": url_count,
        "issues": [issue.as_dict() for issue in issues],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify policy-listed default outputs do not contain live-target URL "
            "fields while allowing public source citation URLs."
        )
    )
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format.",
    )
    args = parser.parse_args(argv)

    try:
        summary = check_default_outputs(Path(args.policy), Path(args.root))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"default output safety check failed: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    elif summary["ok"]:
        print(
            "Default output safety check passed "
            f"({summary['checked_outputs']} output(s), "
            f"{summary['url_count']} URL(s) scanned, "
            f"{summary['provenance_manifest_count']} OSINT provenance manifest(s) checked)."
        )
    else:
        print("Default output safety check failed:", file=sys.stderr)
        for issue in summary["issues"]:
            print(
                f"- {issue['artifact']}:{issue['location']}: {issue['message']}",
                file=sys.stderr,
            )
    return 0 if summary["ok"] else 1


def _check_osint_provenance(
    default_outputs: dict[str, Any],
    root: Path,
    issues: list[Issue],
) -> int:
    checked = 0
    for output_name, output_path in sorted(default_outputs.items()):
        if not _is_osint_snapshot_output(str(output_name), output_path):
            continue
        snapshot_label = str(output_path)
        manifest_name = _manifest_key_for_snapshot(str(output_name))
        manifest_path = default_outputs.get(manifest_name)
        if not isinstance(manifest_path, str) or not manifest_path:
            issues.append(
                Issue(
                    artifact=snapshot_label,
                    location="policy.default_outputs",
                    message=f"OSINT snapshot default output must have paired {manifest_name}",
                )
            )
            continue
        snapshot = _resolve_path(Path(snapshot_label), root)
        manifest = _resolve_path(Path(manifest_path), root)
        checked += _check_osint_manifest(snapshot, snapshot_label, manifest, str(manifest_path), issues)
    return checked


def _check_osint_manifest(
    snapshot: Path,
    snapshot_label: str,
    manifest: Path,
    manifest_label: str,
    issues: list[Issue],
) -> int:
    if not snapshot.exists() or not manifest.exists():
        return 0
    try:
        value = _load_json(manifest)
    except json.JSONDecodeError as exc:
        issues.append(
            Issue(
                artifact=manifest_label,
                location="$",
                message=f"invalid OSINT manifest JSON: {exc.msg}",
            )
        )
        return 0
    if not isinstance(value, dict):
        issues.append(
            Issue(
                artifact=manifest_label,
                location="$",
                message="OSINT manifest must be a JSON object",
            )
        )
        return 0
    if value.get("schema_version") != "prophet.osint_snapshot_manifest.v0.1":
        issues.append(
            Issue(
                artifact=manifest_label,
                location="$.schema_version",
                message="OSINT provenance manifest schema is unsupported",
            )
        )
    expected_hash = _sha256_file(snapshot)
    actual_hash = ((value.get("hashes") or {}).get("snapshot_jsonl_sha256"))
    if actual_hash != expected_hash:
        issues.append(
            Issue(
                artifact=manifest_label,
                location="$.hashes.snapshot_jsonl_sha256",
                message=f"OSINT manifest hash does not match {snapshot_label}",
            )
        )
    if not isinstance(value.get("record_count"), int) or value["record_count"] <= 0:
        issues.append(
            Issue(
                artifact=manifest_label,
                location="$.record_count",
                message="OSINT manifest must report at least one sanitized record",
            )
        )
    if not isinstance(value.get("source_count"), int) or value["source_count"] <= 0:
        issues.append(
            Issue(
                artifact=manifest_label,
                location="$.source_count",
                message="OSINT manifest must report at least one source",
            )
        )
    safety = value.get("safety_attestation") or {}
    if safety.get("sanitized_records_only") is not True:
        issues.append(
            Issue(
                artifact=manifest_label,
                location="$.safety_attestation.sanitized_records_only",
                message="OSINT manifest must attest sanitized records only",
            )
        )
    if safety.get("raw_content_written") is not False:
        issues.append(
            Issue(
                artifact=manifest_label,
                location="$.safety_attestation.raw_content_written",
                message="OSINT manifest must attest raw content was not written",
            )
        )
    policy = value.get("policy") or {}
    if not _is_sha256(policy.get("policy_sha256")):
        issues.append(
            Issue(
                artifact=manifest_label,
                location="$.policy.policy_sha256",
                message="OSINT manifest must include policy SHA-256",
            )
        )
    retention = policy.get("retention") or {}
    if retention.get("raw_collection_retained") is not False:
        issues.append(
            Issue(
                artifact=manifest_label,
                location="$.policy.retention.raw_collection_retained",
                message="OSINT manifest must keep raw collection retention disabled",
            )
        )
    return 1


def _scan_artifact(path: Path, artifact_label: str, issues: list[Issue]) -> int:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _scan_json_value(
            _load_json(path),
            path_parts=(),
            artifact_label=artifact_label,
            issues=issues,
        )
    if suffix == ".jsonl":
        return _scan_jsonl(path, artifact_label, issues)
    return _scan_text(path.read_text(encoding="utf-8"), artifact_label, issues)


def _is_osint_snapshot_output(output_name: str, output_path: object) -> bool:
    if not isinstance(output_path, str):
        return False
    lowered_name = output_name.lower()
    lowered_path = output_path.lower()
    return (
        lowered_path.endswith(".jsonl")
        and "osint" in lowered_name
        and "snapshot" in lowered_name
    )


def _manifest_key_for_snapshot(output_name: str) -> str:
    if output_name.endswith("_snapshot"):
        return f"{output_name[:-len('_snapshot')]}_manifest"
    return f"{output_name}_manifest"


def _scan_jsonl(path: Path, artifact_label: str, issues: list[Issue]) -> int:
    url_count = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append(
                Issue(
                    artifact=artifact_label,
                    location=f"line {line_number}",
                    message=f"invalid JSONL record: {exc.msg}",
                )
            )
            continue
        url_count += _scan_json_value(
            value,
            path_parts=(f"line[{line_number}]",),
            artifact_label=artifact_label,
            issues=issues,
        )
    return url_count


def _scan_json_value(
    value: Any,
    *,
    path_parts: tuple[str, ...],
    artifact_label: str,
    issues: list[Issue],
) -> int:
    if isinstance(value, dict):
        url_count = 0
        for key, child in value.items():
            url_count += _scan_json_value(
                child,
                path_parts=(*path_parts, str(key)),
                artifact_label=artifact_label,
                issues=issues,
            )
        return url_count
    if isinstance(value, list):
        url_count = 0
        for index, child in enumerate(value):
            url_count += _scan_json_value(
                child,
                path_parts=(*path_parts, f"[{index}]"),
                artifact_label=artifact_label,
                issues=issues,
            )
        return url_count
    if isinstance(value, str):
        return _scan_string(value, path_parts=path_parts, artifact_label=artifact_label, issues=issues)
    return 0


def _scan_text(text: str, artifact_label: str, issues: list[Issue]) -> int:
    url_count = 0
    for line_number, line in enumerate(text.splitlines(), 1):
        urls = _extract_urls(line)
        if not urls:
            continue
        url_count += len(urls)
        if DISALLOWED_TEXT_URL_CONTEXT_RE.search(line):
            issues.append(
                Issue(
                    artifact=artifact_label,
                    location=f"line {line_number}",
                    message="live-target URL context is not allowed in default output text",
                )
            )
        for url in urls:
            host_issue = _host_safety_issue(url)
            if host_issue:
                issues.append(
                    Issue(
                        artifact=artifact_label,
                        location=f"line {line_number}",
                        message=host_issue,
                    )
                )
    return url_count


def _scan_string(
    value: str,
    *,
    path_parts: tuple[str, ...],
    artifact_label: str,
    issues: list[Issue],
) -> int:
    urls = _extract_urls(value)
    if not urls:
        return 0
    location = _format_path(path_parts)
    if _is_disallowed_url_path(path_parts):
        issues.append(
            Issue(
                artifact=artifact_label,
                location=location,
                message="live-target URL field is not allowed in default outputs",
            )
        )
    if DISALLOWED_TEXT_URL_CONTEXT_RE.search(value):
        issues.append(
            Issue(
                artifact=artifact_label,
                location=location,
                message="live-target URL context is not allowed in default output text",
            )
        )
    for url in urls:
        host_issue = _host_safety_issue(url)
        if host_issue:
            issues.append(Issue(artifact=artifact_label, location=location, message=host_issue))
    return len(urls)


def _is_disallowed_url_path(path_parts: tuple[str, ...]) -> bool:
    key_parts = [part.lower() for part in path_parts if not part.startswith("[")]
    if not key_parts:
        return False
    leaf = key_parts[-1]
    if leaf in DISALLOWED_URL_KEYS:
        return True
    if leaf in {"url", "uri", "endpoint"}:
        return any(_contains_disallowed_parent_term(part) for part in key_parts[:-1])
    return False


def _contains_disallowed_parent_term(value: str) -> bool:
    normalized_terms = re.split(r"[^a-z0-9]+", value.lower())
    return any(term in DISALLOWED_PARENT_TERMS for term in normalized_terms)


def _host_safety_issue(url: str) -> str | None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if not host:
        return "URL must include a hostname"
    if host == "localhost":
        return None
    if host.endswith(PRIVATE_HOST_SUFFIXES):
        return f"private hostname URL is not allowed: {host}"
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return None
    if any(ip in network for network in ALLOWED_NONLIVE_NETWORKS):
        return None
    if ip.is_private or ip.is_link_local or ip.is_loopback or ip.is_multicast or ip.is_reserved:
        return f"non-public URL host is not allowed: {host}"
    return None


def _extract_urls(value: str) -> list[str]:
    return [match.group(0).rstrip(".,;:]}") for match in URL_RE.finditer(value)]


def _format_path(path_parts: tuple[str, ...]) -> str:
    if not path_parts:
        return "$"
    rendered = "$"
    for part in path_parts:
        if part.startswith("["):
            rendered += part
        elif rendered == "$":
            rendered += f".{part}"
        else:
            rendered += f".{part}"
    return rendered


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _resolve_path(path: Path, root: Path) -> Path:
    if path.is_absolute():
        return path
    return root / path


if __name__ == "__main__":
    raise SystemExit(main())
