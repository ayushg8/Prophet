#!/usr/bin/env python3
"""Release and pre-commit safety checks for the public Prophet repo."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


RUNTIME_PREFIXES = (
    "world-side/outputs/runtime/",
    "cyber-side/outputs/runtime/",
    "evidence/outputs/runtime/",
    "assets/outputs/runtime/",
    "integrations/outputs/runtime/",
)

RAW_COLLECTION_PREFIXES = (
    "world-side/data/chatter/raw/",
    "world-side/data/chatter/incoming/",
    "world-side/scraper/secrets/",
)

CONTENT_SCAN_EXCLUDE_PREFIXES = (
    "kve.json",
    "scripts/check-release-safety.py",
    "scripts/tests/",
)

SKIP_CONTENT_SUFFIXES = {
    ".ico",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".pptx",
    ".docx",
    ".xlsx",
    ".zip",
    ".gz",
    ".class",
}

PLACEHOLDER_VALUES = {
    "",
    "changeme",
    "change-me",
    "dummy",
    "example",
    "fixture",
    "placeholder",
    "redacted",
    "todo",
    "none",
    "null",
    "customer-filled",
    "customer_filled",
}

SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b("
    r"aws_secret_access_key|secret_access_key|api[_-]?key|api[_-]?token|access[_-]?token|"
    r"refresh[_-]?token|password|passwd|private[_-]?key"
    r")\b\s*[:=]\s*['\"]?([^'\"\s#]+)?"
)
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
TOKEN_RE = re.compile(
    r"\b("
    r"AKIA[0-9A-Z]{16}|"
    r"gh[pousr]_[A-Za-z0-9_]{20,}|"
    r"xox[baprs]-[A-Za-z0-9-]{20,}|"
    r"sk-[A-Za-z0-9]{20,}"
    r")\b"
)
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HOST_ASSIGNMENT_RE = re.compile(
    r"\b([A-Z0-9_]*(?:HOST|HOSTNAME|ENDPOINT)[A-Z0-9_]*)\b"
    r"\s*[:=]\s*['\"]?([^'\"\s#]+)?"
)
PRIVATE_HOST_RE = re.compile(
    r"(?i)\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)*"
    r"\.(?:internal|corp|local|lan|private)\b"
)
UNSAFE_COMMAND_RE = re.compile(
    r"(?i)("
    r"\bnc\s+-e\b|"
    r"\bncat\s+--exec\b|"
    r"\bbash\s+-i\b|"
    r"\bsh\s+-i\b|"
    r"\bpowershell(?:\.exe)?\s+-enc\b|"
    r"\bmsfvenom\b|"
    r"\bmeterpreter\b|"
    r"\binvoke-mimikatz\b"
    r")"
)
ALLOWED_PRIVATE_HOSTNAME_LITERALS = {
    "env.local",
    "prophet.local",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,120}$")
SOURCE_CATALOG_PATH = "world-side/scraper/config/source_catalog.json"
SOURCE_CATALOG_ALLOWLIST_PATH = "policy/source-catalog-allowlist.json"
SOURCE_CATALOG_SCHEMA_VERSION = "prophet.scraper.source_catalog.v0.1"
SOURCE_CATALOG_ALLOWLIST_SCHEMA_VERSION = "prophet.source_catalog_allowlist.v0.1"
CONSOLE_CLIENT_PREFIX = "prophet-console/src/"
CONSOLE_CONTROL_SERVER_PATH = "prophet-console/control-server.mjs"
CONSOLE_API_ENDPOINT_RE = re.compile(r"/api/[A-Za-z0-9_./:-]+")
CONSOLE_LIVE_ENDPOINT_POLICY_CONTROLS = {
    "/api/scraper/run": "live_vm_scraper_allowed",
}
CONSOLE_LIVE_ENDPOINT_TERMS = (
    "collect",
    "live",
    "raw",
    "target",
    "vm",
)

POLICY_HASH_REQUIRED_SCHEMAS: dict[str, tuple[str, tuple[tuple[str, ...], ...]]] = {
    "prophet_evidence_bundle.v0.1": (
        "evidence bundle",
        (("policy", "policy_sha256"), ("hashes", "policy_sha256")),
    ),
    "prophet.osint_snapshot_manifest.v0.1": (
        "OSINT manifest",
        (("policy", "policy_sha256"),),
    ),
    "prophet_integration_export.v0.1": (
        "integration manifest",
        (("evidence_refs", "policy_sha256"),),
    ),
    "prophet.sandbox_run_manifest.v0.1": (
        "sandbox run manifest",
        (("policy", "policy_sha256"),),
    ),
}


@dataclass(frozen=True)
class Issue:
    path: str
    line: int | None
    message: str

    def format(self) -> str:
        location = self.path if self.line is None else f"{self.path}:{self.line}"
        return f"{location}: {self.message}"


def run_git(args: Sequence[str]) -> list[str]:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def staged_paths() -> list[str]:
    return run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])


def tracked_paths() -> list[str]:
    return run_git(["ls-files"])


def changed_paths() -> list[str]:
    return run_git(["diff", "--name-only", "--diff-filter=ACMR"])


def changed_from_paths(revspec: str) -> list[str]:
    return run_git(["diff", "--name-only", "--diff-filter=ACMR", revspec])


def normalize_path(path: str | Path) -> str:
    return Path(path).as_posix().lstrip("./")


def is_runtime_or_raw_path(path: str) -> str | None:
    normalized = normalize_path(path)
    if normalized.startswith(RUNTIME_PREFIXES):
        return "generated runtime artifact must stay ignored and unstaged"
    if normalized.startswith(RAW_COLLECTION_PREFIXES):
        return "raw scraper or secret path must not be committed"
    return None


def is_placeholder(value: str) -> bool:
    cleaned = value.strip().strip("'\"").strip()
    lowered = cleaned.lower()
    if lowered in PLACEHOLDER_VALUES:
        return True
    if lowered.startswith("<") and lowered.endswith(">"):
        return True
    if lowered.startswith("${") and lowered.endswith("}"):
        return True
    if lowered in {"{", "[", "("}:
        return True
    if "customer-filled" in lowered or "customer_filled" in lowered:
        return True
    return False


def is_allowed_ip(raw_ip: str) -> bool:
    try:
        ip = ipaddress.ip_address(raw_ip)
    except ValueError:
        return True

    allowed_networks = (
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("0.0.0.0/32"),
        ipaddress.ip_network("192.0.2.0/24"),
        ipaddress.ip_network("198.51.100.0/24"),
        ipaddress.ip_network("203.0.113.0/24"),
    )
    return any(ip in network for network in allowed_networks)


def assigned_endpoint_is_allowed(value: str) -> bool:
    cleaned = value.strip().strip("'\"")
    lowered = cleaned.lower()
    if is_placeholder(cleaned):
        return True
    return (
        lowered.startswith("localhost")
        or lowered.startswith("127.0.0.1")
        or lowered.startswith("0.0.0.0")
        or lowered.startswith("http://localhost")
        or lowered.startswith("https://localhost")
        or lowered.startswith("http://127.0.0.1")
        or lowered.startswith("https://127.0.0.1")
    )


def should_scan_content(path: Path) -> bool:
    if path.suffix.lower() in SKIP_CONTENT_SUFFIXES:
        return False
    return path.is_file()


def content_scan_is_excluded(path_label: str) -> bool:
    normalized = normalize_path(path_label)
    return any(
        normalized == prefix or (prefix.endswith("/") and normalized.startswith(prefix))
        for prefix in CONTENT_SCAN_EXCLUDE_PREFIXES
    )


def scan_text(path_label: str, text: str) -> list[Issue]:
    issues: list[Issue] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if PRIVATE_KEY_RE.search(line):
            issues.append(Issue(path_label, index, "private key material is not allowed"))

        for match in TOKEN_RE.finditer(line):
            issues.append(Issue(path_label, index, f"secret-like token detected: {match.group(1)[:6]}..."))

        for match in SECRET_ASSIGNMENT_RE.finditer(line):
            value = match.group(2) or ""
            if not is_placeholder(value):
                issues.append(Issue(path_label, index, f"non-placeholder secret assignment for {match.group(1)}"))

        for match in IPV4_RE.finditer(line):
            raw_ip = match.group(0)
            if not is_allowed_ip(raw_ip):
                issues.append(Issue(path_label, index, f"non-localhost IP address detected: {raw_ip}"))

        host_match = HOST_ASSIGNMENT_RE.search(line)
        if host_match:
            host_key = host_match.group(1)
            value = host_match.group(2) or ""
            if host_key.endswith(("_RE", "_PATH", "_PATHS")):
                continue
            if value and not assigned_endpoint_is_allowed(value):
                issues.append(Issue(path_label, index, f"non-localhost endpoint assignment for {host_key}"))

        for match in PRIVATE_HOST_RE.finditer(line):
            token = match.group(0).lower()
            if token in ALLOWED_PRIVATE_HOSTNAME_LITERALS:
                continue
            issues.append(Issue(path_label, index, "private hostname detected"))

        if UNSAFE_COMMAND_RE.search(line):
            issues.append(Issue(path_label, index, "offensive command or exploit transport text detected"))

    return issues


def is_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def nested_value(value: dict[str, Any], path: tuple[str, ...]) -> object:
    current: object = value
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def dotted(path: tuple[str, ...]) -> str:
    return ".".join(path)


def is_sandbox_artifact(path_label: str, value: dict[str, Any]) -> bool:
    artifact_id = value.get("artifact_id")
    audit = value.get("audit")
    emitted_by = audit.get("emitted_by") if isinstance(audit, dict) else None
    normalized = normalize_path(path_label)
    return (
        (isinstance(artifact_id, str) and artifact_id.startswith("ee-sandbox-"))
        or emitted_by == "sandbox_runner.fixture"
        or normalized.startswith("sandbox_runner/outputs/")
        or "sandbox-artifact" in normalized
    )


def scan_policy_hash_coverage(path_label: str, text: str) -> list[Issue]:
    if not path_label.endswith(".json"):
        return []

    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, dict):
        return []

    schema_version = value.get("schema_version")
    requirements = POLICY_HASH_REQUIRED_SCHEMAS.get(str(schema_version))
    if schema_version == "exploit_engine_artifact.v0.1" and is_sandbox_artifact(
        path_label, value
    ):
        requirements = ("sandbox artifact", (("audit", "policy_sha256"),))
    if requirements is None:
        return []

    artifact_label, required_paths = requirements
    issues: list[Issue] = []
    for required_path in required_paths:
        if not is_sha256(nested_value(value, required_path)):
            issues.append(
                Issue(
                    path_label,
                    None,
                    f"{artifact_label} must include SHA-256 policy hash at {dotted(required_path)}",
                )
            )
    return issues


def scan_source_catalog_allowlist_coverage(
    paths: Iterable[str | Path],
    root: Path,
) -> list[Issue]:
    """Ensure enabled scraper catalog entries have explicit release allowlist coverage."""

    selected = {normalize_path(path) for path in paths if str(path).strip()}
    if not selected.intersection({SOURCE_CATALOG_PATH, SOURCE_CATALOG_ALLOWLIST_PATH}):
        return []

    catalog_path = root / SOURCE_CATALOG_PATH
    allowlist_path = root / SOURCE_CATALOG_ALLOWLIST_PATH
    if not catalog_path.exists():
        return [
            Issue(
                SOURCE_CATALOG_PATH,
                None,
                "source catalog is required for enabled-source allowlist coverage",
            )
        ]
    if not allowlist_path.exists():
        return [
            Issue(
                SOURCE_CATALOG_ALLOWLIST_PATH,
                None,
                "source catalog allowlist is required for enabled-source coverage",
            )
        ]

    catalog, catalog_issue = _load_release_json(catalog_path, SOURCE_CATALOG_PATH)
    if catalog_issue is not None:
        return [catalog_issue]
    allowlist, allowlist_issue = _load_release_json(
        allowlist_path,
        SOURCE_CATALOG_ALLOWLIST_PATH,
    )
    if allowlist_issue is not None:
        return [allowlist_issue]

    issues: list[Issue] = []
    enabled_source_ids = _enabled_source_catalog_ids(catalog, issues)
    allowed_source_ids = _allowlisted_source_catalog_ids(allowlist, issues)
    if issues:
        return issues

    missing = sorted(set(enabled_source_ids) - set(allowed_source_ids))
    if missing:
        issues.append(
            Issue(
                SOURCE_CATALOG_ALLOWLIST_PATH,
                None,
                "enabled source catalog entries missing allowlist coverage: "
                + _summarize_ids(missing),
            )
        )

    stale = sorted(set(allowed_source_ids) - set(enabled_source_ids))
    if stale:
        issues.append(
            Issue(
                SOURCE_CATALOG_ALLOWLIST_PATH,
                None,
                "source catalog allowlist contains entries that are not enabled: "
                + _summarize_ids(stale),
            )
        )
    return issues


def scan_console_live_action_policy_gates(
    paths: Iterable[str | Path],
    root: Path,
) -> list[Issue]:
    """Ensure console live-collection actions route through explicit policy gates."""

    selected = {normalize_path(path) for path in paths if str(path).strip()}
    if not any(_is_console_release_surface(path) for path in selected):
        return []

    client_paths = _console_client_paths(root)
    endpoints = sorted(
        {
            endpoint
            for path in client_paths
            for endpoint in _console_api_endpoints(path)
            if _is_console_live_endpoint(endpoint)
        }
    )
    if not endpoints:
        return []

    control_server_path = root / CONSOLE_CONTROL_SERVER_PATH
    if not control_server_path.exists():
        return [
            Issue(
                CONSOLE_CONTROL_SERVER_PATH,
                None,
                "console live-collection actions require the localhost control server policy gate",
            )
        ]

    try:
        control_server_text = control_server_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [
            Issue(
                CONSOLE_CONTROL_SERVER_PATH,
                None,
                "console control server must be UTF-8 text for release safety scanning",
            )
        ]

    issues: list[Issue] = []
    for endpoint in endpoints:
        policy_control = CONSOLE_LIVE_ENDPOINT_POLICY_CONTROLS.get(endpoint)
        if policy_control is None:
            issues.append(
                Issue(
                    CONSOLE_CONTROL_SERVER_PATH,
                    None,
                    f"console live-collection endpoint {endpoint} must be added to the release safety policy-gate allowlist",
                )
            )
            continue

        route_text = _control_server_route_text(control_server_text, endpoint)
        if route_text is None:
            issues.append(
                Issue(
                    CONSOLE_CONTROL_SERVER_PATH,
                    None,
                    f"console live-collection endpoint {endpoint} has no matching control-server route",
                )
            )
            continue

        if f"policyContext.policy.controls.{policy_control}" not in route_text:
            issues.append(
                Issue(
                    CONSOLE_CONTROL_SERVER_PATH,
                    None,
                    f"console live-collection endpoint {endpoint} must check policy.controls.{policy_control}",
                )
            )
        if "policy_blocked" not in route_text:
            issues.append(
                Issue(
                    CONSOLE_CONTROL_SERVER_PATH,
                    None,
                    f"console live-collection endpoint {endpoint} must return a policy_blocked denial path",
                )
            )
    return issues


def scan_paths(paths: Iterable[str | Path], root: Path, paths_only: bool = False) -> list[Issue]:
    issues: list[Issue] = []
    normalized_paths = sorted({normalize_path(path) for path in paths if str(path).strip()})
    for raw_path in normalized_paths:
        path_issue = is_runtime_or_raw_path(raw_path)
        if path_issue:
            issues.append(Issue(raw_path, None, path_issue))

        absolute_path = root / raw_path
        if not should_scan_content(absolute_path):
            continue

        try:
            text = absolute_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if not paths_only and not content_scan_is_excluded(raw_path):
            issues.extend(scan_text(raw_path, text))
        issues.extend(scan_policy_hash_coverage(raw_path, text))

    issues.extend(scan_source_catalog_allowlist_coverage(normalized_paths, root))
    issues.extend(scan_console_live_action_policy_gates(normalized_paths, root))
    return issues


def _load_release_json(path: Path, path_label: str) -> tuple[dict[str, Any], Issue | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, Issue(path_label, exc.lineno, f"invalid JSON: {exc.msg}")
    if not isinstance(value, dict):
        return {}, Issue(path_label, None, "release safety JSON must be an object")
    return value, None


def _enabled_source_catalog_ids(catalog: dict[str, Any], issues: list[Issue]) -> list[str]:
    if catalog.get("schema_version") != SOURCE_CATALOG_SCHEMA_VERSION:
        issues.append(
            Issue(
                SOURCE_CATALOG_PATH,
                None,
                f"source catalog schema_version must be {SOURCE_CATALOG_SCHEMA_VERSION}",
            )
        )
        return []

    sources = catalog.get("sources")
    if not isinstance(sources, list):
        issues.append(Issue(SOURCE_CATALOG_PATH, None, "source catalog sources must be a list"))
        return []

    enabled: list[str] = []
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            issues.append(Issue(SOURCE_CATALOG_PATH, None, f"source catalog entry {index} must be an object"))
            continue
        source_id = source.get("id")
        if source.get("enabled") is True:
            if not isinstance(source_id, str) or not SAFE_ID_RE.fullmatch(source_id):
                issues.append(
                    Issue(
                        SOURCE_CATALOG_PATH,
                        None,
                        f"enabled source catalog entry {index} has an unsafe id",
                    )
                )
                continue
            enabled.append(source_id)
    duplicates = sorted({source_id for source_id in enabled if enabled.count(source_id) > 1})
    if duplicates:
        issues.append(
            Issue(
                SOURCE_CATALOG_PATH,
                None,
                "source catalog has duplicate enabled ids: " + _summarize_ids(duplicates),
            )
        )
    return sorted(enabled)


def _allowlisted_source_catalog_ids(
    allowlist: dict[str, Any],
    issues: list[Issue],
) -> list[str]:
    if allowlist.get("schema_version") != SOURCE_CATALOG_ALLOWLIST_SCHEMA_VERSION:
        issues.append(
            Issue(
                SOURCE_CATALOG_ALLOWLIST_PATH,
                None,
                "source catalog allowlist schema_version must be "
                + SOURCE_CATALOG_ALLOWLIST_SCHEMA_VERSION,
            )
        )
        return []

    allowed = allowlist.get("allowed_enabled_source_ids")
    if not isinstance(allowed, list) or not all(isinstance(item, str) and item.strip() for item in allowed):
        issues.append(
            Issue(
                SOURCE_CATALOG_ALLOWLIST_PATH,
                None,
                "source catalog allowlist allowed_enabled_source_ids must be list[str]",
            )
        )
        return []

    cleaned = [item.strip() for item in allowed]
    duplicates = sorted({source_id for source_id in cleaned if cleaned.count(source_id) > 1})
    if duplicates:
        issues.append(
            Issue(
                SOURCE_CATALOG_ALLOWLIST_PATH,
                None,
                "source catalog allowlist has duplicate ids: " + _summarize_ids(duplicates),
            )
        )
    unsafe = sorted(source_id for source_id in cleaned if not SAFE_ID_RE.fullmatch(source_id))
    if unsafe:
        issues.append(
            Issue(
                SOURCE_CATALOG_ALLOWLIST_PATH,
                None,
                "source catalog allowlist has unsafe ids: " + _summarize_ids(unsafe),
            )
        )
    return sorted(cleaned)


def _summarize_ids(values: Sequence[str], limit: int = 10) -> str:
    ordered = list(values)
    if len(ordered) <= limit:
        return ", ".join(ordered)
    shown = ", ".join(ordered[:limit])
    return f"{shown}, ... (+{len(ordered) - limit} more)"


def _is_console_release_surface(path: str) -> bool:
    return path == CONSOLE_CONTROL_SERVER_PATH or path.startswith(CONSOLE_CLIENT_PREFIX)


def _console_client_paths(root: Path) -> list[Path]:
    src_dir = root / CONSOLE_CLIENT_PREFIX
    if not src_dir.is_dir():
        return []
    return sorted(
        path
        for path in src_dir.rglob("*")
        if path.suffix in {".js", ".jsx", ".ts", ".tsx"} and path.is_file()
    )


def _console_api_endpoints(path: Path) -> set[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return set()
    return set(CONSOLE_API_ENDPOINT_RE.findall(text))


def _is_console_live_endpoint(endpoint: str) -> bool:
    if endpoint in CONSOLE_LIVE_ENDPOINT_POLICY_CONTROLS:
        return True
    lowered = endpoint.lower()
    return any(term in lowered for term in CONSOLE_LIVE_ENDPOINT_TERMS)


def _control_server_route_text(server_text: str, endpoint: str) -> str | None:
    route_index = server_text.find(endpoint)
    if route_index == -1:
        return None

    next_route = server_text.find("if (req.method", route_index + len(endpoint))
    if next_route == -1:
        return server_text[route_index:]
    return server_text[route_index:next_route]


def selected_paths(args: argparse.Namespace) -> list[str]:
    paths: list[str] = []
    if args.staged:
        paths.extend(staged_paths())
    if args.tracked:
        paths.extend(tracked_paths())
    if args.diff:
        paths.extend(changed_paths())
    if args.changed_from:
        paths.extend(changed_from_paths(args.changed_from))
    if args.paths:
        paths.extend(args.paths)
    return sorted(set(paths))


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--staged",
        action="store_true",
        help="scan staged files, suitable for pre-commit hooks",
    )
    parser.add_argument(
        "--tracked",
        action="store_true",
        help="scan all tracked files, suitable for release and CI checks",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="scan modified tracked files in the current working tree",
    )
    parser.add_argument(
        "--changed-from",
        metavar="REVSPEC",
        help="scan files changed in a git diff revspec, for example origin/main...HEAD",
    )
    parser.add_argument(
        "--paths-only",
        action="store_true",
        help=(
            "skip unsafe text scanning and check forbidden paths plus release "
            "artifact policy-hash coverage"
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="explicit paths to scan; mainly used by tests or targeted local checks",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if not (args.staged or args.tracked or args.diff or args.changed_from or args.paths):
        args.staged = True

    root = Path.cwd()
    paths = selected_paths(args)
    issues = scan_paths(paths, root, paths_only=args.paths_only)
    if issues:
        print("Prophet release safety check failed:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue.format()}", file=sys.stderr)
        return 1

    print(f"Prophet release safety check passed ({len(paths)} path(s) scanned).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
