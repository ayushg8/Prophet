#!/usr/bin/env python3
"""Initialize a gitignored local workspace for Prophet validation sprint data."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any


PRIVATE_DIR = Path("validation/private")
DEFAULT_FILES = (
    ("docs/customer-validation-log.example.json", "customer-validation-log.json"),
    ("docs/validation-targets.example.json", "validation-targets.json"),
    ("docs/customer-validation-interview.template.json", "customer-validation-interview.template.json"),
)


class ValidationSprintInitError(ValueError):
    """Raised when the private validation workspace cannot be initialized."""


def initialize_workspace(
    *,
    repo_root: str | Path = ".",
    private_dir: str | Path = PRIVATE_DIR,
    force: bool = False,
    refresh_readme: bool = False,
    run_date: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root)
    destination_root = root / private_dir
    dates = _validation_dates(run_date)
    written: list[str] = []
    skipped: list[str] = []

    destination_root.mkdir(parents=True, exist_ok=True)
    for source_rel, dest_name in DEFAULT_FILES:
        source = root / source_rel
        destination = destination_root / dest_name
        if not source.exists():
            raise ValidationSprintInitError(f"missing template: {source}")
        if destination.exists() and not force:
            skipped.append(str(destination))
            continue
        shutil.copyfile(source, destination)
        written.append(str(destination))

    readme = destination_root / "README.md"
    if not readme.exists() or force or refresh_readme:
        readme.write_text(_private_readme(dates), encoding="utf-8")
        written.append(str(readme))
    else:
        skipped.append(str(readme))

    return {
        "ok": True,
        "private_dir": str(destination_root),
        "written": written,
        "skipped_existing": skipped,
        "next_commands": _next_commands(dates),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create gitignored private files for Prophet customer validation."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing docs/customer-validation-log.example.json.",
    )
    parser.add_argument(
        "--private-dir",
        default=str(PRIVATE_DIR),
        help="Gitignored directory for private validation files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing private validation templates.",
    )
    parser.add_argument(
        "--refresh-readme",
        action="store_true",
        help="Rewrite only validation/private/README.md without overwriting tracker/log templates.",
    )
    parser.add_argument(
        "--date",
        help="Date to use in generated dry-run commands, in YYYY-MM-DD form.",
    )
    args = parser.parse_args(argv)
    try:
        summary = initialize_workspace(
            repo_root=args.repo_root,
            private_dir=args.private_dir,
            force=args.force,
            refresh_readme=args.refresh_readme,
            run_date=args.date,
        )
    except (OSError, ValidationSprintInitError) as exc:
        print(f"validation sprint init failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _validation_dates(run_date: str | None) -> dict[str, str]:
    try:
        start = date.fromisoformat(run_date) if run_date else date.today()
    except ValueError as exc:
        raise ValidationSprintInitError("--date must be in YYYY-MM-DD form") from exc
    return {
        "send": start.isoformat(),
        "follow_up_due": (start + timedelta(days=3)).isoformat(),
        "call_booked": (start + timedelta(days=1)).isoformat(),
        "completed": (start + timedelta(days=2)).isoformat(),
    }


def _next_commands(dates: dict[str, str]) -> list[str]:
    return [
        "python3 scripts/validation-targets-scorecard.py --targets validation/private/validation-targets.json",
        "python3 scripts/validation-outreach-block.py --date "
        f"{dates['send']} --format json --out validation/private/today-outreach-block.json",
        "python3 scripts/validation-outreach-block.py --date "
        f"{dates['send']} --format markdown --out validation/private/today-outreach-block.md",
        "python3 scripts/validation-message-pack.py --block validation/private/today-outreach-block.json --require-date "
        f"{dates['send']} --format json --out validation/private/today-message-pack.json",
        "python3 scripts/validation-message-pack.py --block validation/private/today-outreach-block.json --require-date "
        f"{dates['send']} --format markdown --out validation/private/today-message-pack.md",
        f"make validation-dashboard DATE={dates['send']}",
        f"make validation-next-draft DATE={dates['send']}",
        f"make validation-send-copy DATE={dates['send']}",
        f"make validation-send-copy-batch DATE={dates['send']}",
        f"make validation-send-copy-check DATE={dates['send']}",
        f"make validation-draft-copy TARGET=target-dib-platform-004 DATE={dates['send']}",
        f"make validation-apply-draft TARGET=target-dib-platform-001 DATE={dates['send']}",
        "python3 scripts/validation-target-update.py --target-label target-dib-platform-001 --status outreach_sent --require-current-status identified --require-current-status intro_requested --last-touch "
        f"{dates['send']} --follow-up-due {dates['follow_up_due']} --next-action 'Send follow-up if no reply.' --dry-run",
        "python3 scripts/validation-target-update.py --target-label target-dib-platform-001 --status call_booked --require-current-status intro_requested --require-current-status outreach_sent --require-current-status follow_up_due --last-touch "
        f"{dates['call_booked']} --clear-follow-up-due --next-action 'Prepare discovery call.' --dry-run",
        "python3 scripts/validation-outreach-status.py --verify-dry-run-commands --require-date "
        f"{dates['send']} --format json --out validation/private/today-outreach-status.json",
        "python3 scripts/validation-outreach-status.py --verify-dry-run-commands --require-date "
        f"{dates['send']} --format markdown --out validation/private/today-outreach-status.md",
        f"make validation-team-update-save DATE={dates['send']}",
        f"make validation-weekly-review DATE={dates['send']}",
        "python3 scripts/validation-prepare-interview.py --target-label target-dib-platform-001 --date "
        f"{dates['call_booked']} --out validation/private/customer-validation-interview-next.json",
        "python3 scripts/customer-validation-log-add.py --interview-json validation/private/customer-validation-interview-next.json --updated-at "
        f"{dates['completed']} --require-target-status call_booked --dry-run",
        "python3 scripts/customer-validation-log-add.py --interview-json validation/private/customer-validation-interview-next.json --updated-at "
        f"{dates['completed']} --require-target-status call_booked --replace-example-seed --dry-run",
        "python3 scripts/validation-target-update.py --target-label target-dib-platform-001 --status completed --require-current-status call_booked --last-touch "
        f"{dates['completed']} --clear-follow-up-due --next-action 'Logged sanitized discovery outcome.' --dry-run",
        "python3 scripts/customer-validation-log-add.py --account-label example-dib-platform-002 --segment dib_platform_security --persona director_product_security --qualified true --current-workflow 'Scanner, SBOM review, ticket queue, manual briefing.' --recent-painful-event 'Had to justify edge appliance remediation order.' --existing-tool scanner --existing-tool ticketing --status-quo-gap 'No audit-ready packet for why this first.' --desired-output 'Evidence packet with source basis and SOC review handoff.' --workflow-pain-theme evidence_packet_gap --pain-score 5 --urgency-score 4 --status-quo-weakness-score 4 --buyer-access-score 3 --data-feasibility-score 4 --pilot-pull-score 3 --budget-signal could_sponsor_design_partner --pilot-signal asked_for_scoped_pilot --next-step 'Send pilot scope.' --updated-at "
        f"{dates['send']} --dry-run",
        "python3 scripts/customer-validation-scorecard.py --log validation/private/customer-validation-log.json",
        "python3 scripts/validation-sprint-dashboard.py --require-date "
        f"{dates['send']} --message-pack validation/private/today-message-pack.json",
    ]


def _private_readme(dates: dict[str, str]) -> str:
    return f"""# Private Prophet Validation Workspace

This directory is gitignored. Keep real prospect and customer discovery notes
here, not in committed docs.

Allowed:

- anonymized account labels
- segment/persona labels
- outreach status
- sanitized workflow notes
- scorecard fields

Do not store:

- names
- emails
- phone numbers
- LinkedIn URLs
- private hostnames
- IPs
- screenshots
- transcripts
- raw customer exports
- secrets

Seed warning:

`customer-validation-log.json` is initialized from the public example seed. The
dashboard will mark that state as `example_seed_log: true`, keep
`allowed_to_build_next_slice: false`, and warn that seed counts are not real buyer traction.
Replace the seed with real anonymized buyer interviews before
treating qualified-call, pilot-pull, or paid/sponsored counts as validation
evidence.
Use `DATE` as the actual sanitized interview/log date. The generated example
below assumes outreach on {dates['send']}, a booked call on
{dates['call_booked']}, and a logged interview on {dates['completed']}.
For the first real private interview, run
`make validation-log-interview DATE={dates['completed']} REPLACE_EXAMPLE_SEED=1`
as a dry-run, then add `CONFIRM_LOG=1` only after reviewing the sanitized
record. This removes the public example interview and clears
`example_seed_log`.

Run:

The dated commands below are examples. For a recovered or replayed outreach
day, run `python3 scripts/init-validation-sprint.py --date YYYY-MM-DD` and use
the printed `next_commands`; do not force-overwrite private tracker/log files
unless you intend to reset them.

The status commands write both `today-outreach-status.json` and
`today-outreach-status.md`. Use the JSON file for machine-readable checks and
the Markdown file for human review.

Normal outreach order:

1. Run `make validation-dashboard DATE={dates['send']}`.
   Use `make goal-resume DATE={dates['send']}` after a restored `/goal`
   session when you want the same no-write dashboard-first recovery path. The
   resume command prints pasteable outbound copy only inside
   `BEGIN COPY-ONLY SEND TEXT` / `END COPY-ONLY SEND TEXT`; anything below
   `DO NOT SEND BELOW THIS LINE` is tracker/audit metadata.
2. If it reports `next_draft_state: ready` and
   `next_draft_matches_next_pending: true`, use
   `validation/private/today-next-draft.md` as tracker/audit metadata.
   Otherwise run
   `make validation-next-draft DATE={dates['send']}`.
3. Run `make validation-send-copy DATE={dates['send']}` to write
   `validation/private/today-send-copy.txt`, the copy-only outbound text without
   target labels, tracker commands, or status metadata. Send from it only when
   the dashboard reports `send_copy_state: ready` and
   `send_copy_matches_next_pending: true`.
4. Use `make validation-draft-copy TARGET=target-dib-platform-004 DATE={dates['send']}`
   only when you need copy-only subject/body text for a selected target without
   writing `today-send-copy.txt`.
5. If sending the whole block, run
   `make validation-send-copy-batch DATE={dates['send']}` and copy only the
   generated `.txt` file contents after the dashboard reports
   `send_copy_batch_state: ready` and
   `send_copy_batch_matches_current_pack: true`. Do not attach the files.
6. Run `make validation-send-copy-check DATE={dates['send']}` to verify the
   existing numbered `.txt` files have neutral filenames, one `Subject:` line,
   matching SHA-256 values, and no target labels or tracker metadata.
7. Run `make validation-apply-draft TARGET=target-dib-platform-001 DATE={dates['send']}`.
8. Send the copy-only text outside the repo only after that dry-run is clean.
9. Rerun the same dated Make command with `CONFIRM_SENT=1` only after the
   message is actually sent, the actual send is confirmed, and the anonymized
   tracker update is correct.
10. Run `make validation-status DATE={dates['send']}`.
11. Run `make validation-team-update-save DATE={dates['send']}` if you need a
   local aggregate-only team handoff. It writes
   `validation/private/today-team-update.md` without target labels, commands,
   message bodies, or private validation paths.
12. Run `make validation-weekly-review DATE={dates['send']}` before pruning or
   rotating ignored artifacts. It writes a read-only private report and does
   not delete files or mutate trackers/logs.

The raw commands below are dry-run/reference commands for recovery and audit;
prefer the Make wrappers during normal outreach.

```bash
python3 scripts/validation-outreach-block.py --date {dates['send']} --format json --out validation/private/today-outreach-block.json
python3 scripts/validation-outreach-block.py --date {dates['send']} --format markdown --out validation/private/today-outreach-block.md
python3 scripts/validation-message-pack.py --block validation/private/today-outreach-block.json --require-date {dates['send']} --format json --out validation/private/today-message-pack.json
python3 scripts/validation-message-pack.py --block validation/private/today-outreach-block.json --require-date {dates['send']} --format markdown --out validation/private/today-message-pack.md
python3 scripts/validation-target-update.py --target-label target-dib-platform-001 --status outreach_sent --require-current-status identified --require-current-status intro_requested --last-touch {dates['send']} --follow-up-due {dates['follow_up_due']} --next-action 'Send follow-up if no reply.' --dry-run
python3 scripts/validation-target-update.py --target-label target-dib-platform-001 --status call_booked --require-current-status intro_requested --require-current-status outreach_sent --require-current-status follow_up_due --last-touch {dates['call_booked']} --clear-follow-up-due --next-action 'Prepare discovery call.' --dry-run
python3 scripts/validation-outreach-status.py --verify-dry-run-commands --require-date {dates['send']} --format json --out validation/private/today-outreach-status.json
python3 scripts/validation-outreach-status.py --verify-dry-run-commands --require-date {dates['send']} --format markdown --out validation/private/today-outreach-status.md
python3 scripts/validation-weekly-review.py --private-dir validation/private --targets validation/private/validation-targets.json --log validation/private/customer-validation-log.json --message-pack validation/private/today-message-pack.json --review-date {dates['send']} --format markdown --out validation/private/today-weekly-review.md
python3 scripts/validation-prepare-interview.py --target-label target-dib-platform-001 --date {dates['call_booked']} --out validation/private/customer-validation-interview-next.json
python3 scripts/customer-validation-log-add.py --interview-json validation/private/customer-validation-interview-next.json --updated-at {dates['completed']} --require-target-status call_booked --dry-run
python3 scripts/validation-target-update.py --target-label target-dib-platform-001 --status completed --require-current-status call_booked --last-touch {dates['completed']} --clear-follow-up-due --next-action 'Logged sanitized discovery outcome.' --dry-run
python3 scripts/customer-validation-log-add.py --account-label example-dib-platform-002 --segment dib_platform_security --persona director_product_security --qualified true --current-workflow 'Scanner, SBOM review, ticket queue, manual briefing.' --recent-painful-event 'Had to justify edge appliance remediation order.' --existing-tool scanner --existing-tool ticketing --status-quo-gap 'No audit-ready packet for why this first.' --desired-output 'Evidence packet with source basis and SOC review handoff.' --workflow-pain-theme evidence_packet_gap --pain-score 5 --urgency-score 4 --status-quo-weakness-score 4 --buyer-access-score 3 --data-feasibility-score 4 --pilot-pull-score 3 --budget-signal could_sponsor_design_partner --pilot-signal asked_for_scoped_pilot --next-step 'Send pilot scope.' --updated-at {dates['send']} --dry-run
python3 scripts/validation-sprint-dashboard.py --require-date {dates['send']} --message-pack validation/private/today-message-pack.json
```

The interview preparation helper writes an intentionally incomplete private
starter from a booked anonymized target. It should fail validation until real
sanitized call outcomes are filled.

The direct `customer-validation-log-add.py` CLI also validates without writing
by default. Normal confirmed raw writes require `--require-target-status
call_booked` with matching account label, segment, and persona metadata, or the
explicit `--allow-untracked-interview` bypass. First real interview seed replacement is stricter:
use the Make wrapper or `--replace-example-seed --require-target-status call_booked`
with matching target metadata, and do not use `--allow-untracked-interview`.
The untracked bypass is for out-of-band learning only. The dashboard's
`target_backed_validation` gate counts interviews toward production build
scope only when their `account_label` matches an anonymized target in
`call_booked` or `completed` with matching segment/persona metadata.

The raw target update CLI validates without writing by default and blocks
confirmed send-derived `intro_requested` / `outreach_sent` writes. Use
`make validation-apply-draft ...` after the real send and matching copy-only
artifact verification. Use
`--confirm-target` only after reviewing non-send transitions; prefer the Make
wrappers from the committed docs during normal outreach.
"""


if __name__ == "__main__":
    raise SystemExit(main())
