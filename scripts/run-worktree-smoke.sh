#!/usr/bin/env bash
set -euo pipefail

KEEP_TMP=0

usage() {
  cat <<'USAGE'
Usage: ./scripts/run-worktree-smoke.sh [--keep]

Clone the current HEAD into a temporary directory, overlay the current
non-ignored dirty worktree files, and run the safe root pilot smoke there.

This is a pre-commit release hygiene check for the current local package. It
does not stage, commit, push, tag, copy ignored private validation files, or run
production platform work.

Options:
  --keep       Keep the temporary clone and print its path.
  -h, --help   Show this help text.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep)
      KEEP_TMP=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

tmpdir="$(mktemp -d /tmp/prophet-worktree-smoke.XXXXXX)"
clone_dir="$tmpdir/Prophet"

cleanup() {
  if [[ "$KEEP_TMP" -eq 0 ]]; then
    if [[ "$tmpdir" == /tmp/prophet-worktree-smoke.* ]]; then
      rm -rf "$tmpdir"
    else
      echo "refusing to remove unexpected temporary path: $tmpdir" >&2
    fi
  else
    printf 'Kept temporary worktree smoke clone: %s\n' "$clone_dir"
  fi
}
trap cleanup EXIT

printf 'Creating temporary local clone: %s\n' "$clone_dir"
git clone --local . "$clone_dir" >/dev/null

overlay_count=0
delete_count=0

overlay_path() {
  local relpath="$1"
  if [[ -z "$relpath" || "$relpath" == .git/* ]]; then
    return
  fi
  if [[ -f "$relpath" || -L "$relpath" ]]; then
    mkdir -p "$clone_dir/$(dirname "$relpath")"
    cp -p "$relpath" "$clone_dir/$relpath"
    overlay_count=$((overlay_count + 1))
  fi
}

remove_deleted_path() {
  local relpath="$1"
  if [[ -z "$relpath" || "$relpath" == .git/* ]]; then
    return
  fi
  rm -f "$clone_dir/$relpath"
  delete_count=$((delete_count + 1))
}

while IFS= read -r -d '' relpath; do
  overlay_path "$relpath"
done < <(
  {
    git diff --name-only -z --diff-filter=ACMRTUXB
    git ls-files --others --exclude-standard -z
  }
)

while IFS= read -r -d '' relpath; do
  remove_deleted_path "$relpath"
done < <(git diff --name-only -z --diff-filter=D)

printf 'Overlayed %s non-ignored dirty file(s); applied %s tracked deletion(s).\n' \
  "$overlay_count" "$delete_count"
printf 'Ignored files such as validation/private/ are not copied.\n'

(
  cd "$clone_dir"
  ./scripts/check-local-env.sh
  ./scripts/run-pilot-demo-smoke.sh
)

printf 'Worktree overlay smoke passed in %s\n' "$clone_dir"
