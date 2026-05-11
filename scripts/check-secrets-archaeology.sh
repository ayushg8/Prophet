#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./scripts/check-secrets-archaeology.sh [--current-only]

Run read-only secrets archaeology for the current Prophet worktree.

Checks:

- suspicious secret-bearing filenames in tracked and untracked non-ignored files
- high-signal secret patterns in tracked and untracked non-ignored files
- suspicious secret-bearing filenames across git history
- high-signal secret patterns across git history

The scanner reports only file paths and commit IDs. It does not print matched secret values.
Ignored files such as validation/private/ and node_modules/ are not scanned.
USAGE
}

scan_history=1
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
elif [[ "${1:-}" == "--current-only" ]]; then
  scan_history=0
  shift
fi
if [[ $# -gt 0 ]]; then
  echo "error: unknown argument: $1" >&2
  usage >&2
  exit 2
fi

SECRET_PATTERN='AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|-----BEGIN (RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----|xox[baprs]-[A-Za-z0-9-]{10,}|ghp_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|(?i:(api[_-]?key|secret|token|password)[[:space:]]*[:=][[:space:]]*[A-Za-z0-9_./+=:-]{24,})'

current_files=()
while IFS= read -r -d '' file; do
  current_files+=("$file")
done < <(git ls-files -co --exclude-standard -z | sort -z)

finding_count=0

is_allowed_secret_filename() {
  case "$1" in
    .env.example|*/.env.example)
      return 0
      ;;
  esac
  return 1
}

is_suspicious_secret_filename() {
  local path="$1"
  local base="${path##*/}"
  case "$base" in
    .env|.env.*|*.pem|*.key|*.session|*_ed25519)
      return 0
      ;;
  esac
  return 1
}

record_finding() {
  finding_count=$((finding_count + 1))
  printf '%s\n' "$1" >&2
}

find_secret_matches() {
  if command -v rg >/dev/null 2>&1; then
    rg -l -I --pcre2 "$SECRET_PATTERN" "$@"
    return $?
  fi
  grep -I -l -P -e "$SECRET_PATTERN" -- "$@"
}

printf '[1/4] Checking current tracked/untracked non-ignored filenames\n'
for file in "${current_files[@]}"; do
  if is_allowed_secret_filename "$file"; then
    continue
  fi
  if is_suspicious_secret_filename "$file"; then
    record_finding "suspicious current filename: $file"
  fi
done

printf '[2/4] Checking current tracked/untracked non-ignored content\n'
if [[ "${#current_files[@]}" -gt 0 ]]; then
  set +e
  current_matches=$(find_secret_matches "${current_files[@]}")
  rc=$?
  set -e
  if [[ "$rc" -gt 1 ]]; then
    exit "$rc"
  fi
  if [[ -n "${current_matches:-}" ]]; then
    while IFS= read -r file; do
      [[ -n "$file" ]] || continue
      record_finding "suspicious current content: $file"
    done <<< "$current_matches"
  fi
fi

if [[ "$scan_history" -eq 1 ]]; then
  printf '[3/4] Checking historical filenames\n'
  history_names=$(git log --all --name-only --pretty=format: | sort -u)
  if [[ -n "${history_names:-}" ]]; then
    while IFS= read -r file; do
      [[ -n "$file" ]] || continue
      if is_allowed_secret_filename "$file"; then
        continue
      fi
      if is_suspicious_secret_filename "$file"; then
        record_finding "suspicious historical filename: $file"
      fi
    done <<< "$history_names"
  fi

  printf '[4/4] Checking historical content\n'
  while IFS= read -r rev; do
    [[ -n "$rev" ]] || continue
    set +e
    history_matches=$(git grep -l -I --perl-regexp "$SECRET_PATTERN" "$rev" -- .)
    rc=$?
    set -e
    if [[ "$rc" -gt 1 ]]; then
      exit "$rc"
    fi
    if [[ -n "${history_matches:-}" ]]; then
      while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        record_finding "suspicious historical content: $file"
      done <<< "$history_matches"
    fi
  done < <(git rev-list --all)
else
  printf '[3/4] Skipping historical filenames (--current-only)\n'
  printf '[4/4] Skipping historical content (--current-only)\n'
fi

if [[ "$finding_count" -gt 0 ]]; then
  printf 'Prophet secrets archaeology found %s potential issue(s).\n' "$finding_count" >&2
  exit 1
fi

printf 'Prophet secrets archaeology passed (%s current tracked/untracked non-ignored file(s) scanned).\n' "${#current_files[@]}"
