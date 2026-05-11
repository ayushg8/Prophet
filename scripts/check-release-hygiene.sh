#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH_SAFE="${PYTHONPATH_SAFE:-.:cyber-side:world-side}"

usage() {
  cat <<'USAGE'
Usage: ./scripts/check-release-hygiene.sh

Run read-only release hygiene checks for the current Prophet worktree:

- tracked diff whitespace
- untracked non-ignored file whitespace
- release safety over the current diff
- release safety over untracked non-ignored files
- tracked path policy-hash coverage
- staged-path safety
- current-worktree secrets scan
- pilot policy lint
- default output URL/provenance safety
- local Markdown link checking

This script does not stage, commit, push, tag, delete files, or copy ignored
private validation artifacts.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi
if [[ $# -gt 0 ]]; then
  echo "error: unknown argument: $1" >&2
  usage >&2
  exit 2
fi

printf '[1/10] Checking tracked diff whitespace\n'
git diff --check

printf '[2/10] Checking untracked non-ignored whitespace\n'
untracked_list="$(mktemp -t prophet-untracked.XXXXXX)"
trap 'rm -f "$untracked_list"' EXIT
git ls-files --others --exclude-standard -z | sort -z > "$untracked_list"
untracked_count=0
while IFS= read -r -d '' file; do
  [[ -n "$file" ]] || continue
  untracked_count=$((untracked_count + 1))
  set +e
  git diff --no-index --check /dev/null "$file"
  rc=$?
  set -e
  if [[ "$rc" -ne 0 && "$rc" -ne 1 ]]; then
    exit "$rc"
  fi
done < "$untracked_list"
printf 'Checked %s untracked non-ignored file(s).\n' "$untracked_count"

printf '[3/10] Running release safety over current diff\n'
PYTHONPATH="$PYTHONPATH_SAFE" python3 scripts/check-release-safety.py --diff

printf '[4/10] Running release safety over untracked non-ignored files\n'
if [[ "$untracked_count" -gt 0 ]]; then
  PYTHONPATH="$PYTHONPATH_SAFE" xargs -0 python3 scripts/check-release-safety.py < "$untracked_list"
else
  printf 'No untracked non-ignored files.\n'
fi

printf '[5/10] Checking tracked path policy-hash coverage\n'
PYTHONPATH="$PYTHONPATH_SAFE" python3 scripts/check-release-safety.py --tracked --paths-only

printf '[6/10] Running staged-path release safety\n'
PYTHONPATH="$PYTHONPATH_SAFE" python3 scripts/check-release-safety.py --staged

printf '[7/10] Running current-worktree secrets scan\n'
./scripts/check-secrets-archaeology.sh --current-only

printf '[8/10] Linting pilot policy\n'
PYTHONPATH="$PYTHONPATH_SAFE" python3 -m policy.lint --policy policy/prophet-pilot-policy.json >/dev/null

printf '[9/10] Checking default output URL/provenance safety\n'
PYTHONPATH="$PYTHONPATH_SAFE" python3 scripts/check-default-output-safety.py \
  --policy policy/prophet-pilot-policy.json \
  --format text

printf '[10/10] Checking local Markdown links\n'
python3 scripts/check-doc-links.py

printf 'Prophet release hygiene check passed.\n'
