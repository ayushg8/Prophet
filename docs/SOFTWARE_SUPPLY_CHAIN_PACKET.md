# Software Supply-Chain Packet

Date: 2026-05-11

This packet covers Prophet's current buyer-pilot repo state. It is intended for
internal alpha and paid-pilot security review. It does not claim SLSA,
FedRAMP, SOC 2, CMMC, or production SaaS readiness.

## Scope

Included:

- Python pilot scripts, validators, policies, evidence generation, integrations,
  sandbox runner, and validation-sprint tooling in this public repo.
- Console package metadata under `prophet-console/`.
- Isolated scraper dependency placeholder under `world-side/scraper/`.
- CI, release-safety checks, local pilot smoke, and release-hygiene wrappers.

Excluded:

- Ignored runtime outputs under `*/outputs/runtime/`.
- Ignored private validation artifacts under `validation/private/`.
- `node_modules/`, `dist/`, `test-results/`, screenshots, and other generated
  local build/test output.
- Private research/lab repositories, credentials, keys, live target data, raw
  scraper output, and customer-owned artifacts.

## Dependency Inventory

| Surface | Source of truth | Current state |
|---|---|---|
| Console runtime dependencies | `prophet-console/package.json` and `prophet-console/package-lock.json` | 5 direct runtime dependencies: `prismjs`, `react`, `react-dom`, `simplex-noise`, `three`. |
| Console development dependencies | `prophet-console/package.json` and `prophet-console/package-lock.json` | 15 direct dev dependencies for TypeScript, Vite, ESLint, Playwright, React types, and Node types. |
| Console transitive dependency lock | `prophet-console/package-lock.json` | Lockfile version 3 with 200 package entries. |
| Python product path | Stdlib imports plus checked-in package modules | No root `requirements.txt`, `pyproject.toml`, `poetry.lock`, or `Pipfile.lock` is present for the public product path. |
| Isolated scraper placeholder | `world-side/scraper/requirements.txt` | File exists and is intentionally empty until isolated scraper code lands; it must contain package names/versions only, not private indexes. |
| CI actions | `.github/workflows/*.yml` | GitHub Actions are pinned by major version and forced onto Node 24 runtime by workflow environment. |

Current console direct dependencies:

```text
Runtime:
- prismjs ^1.30.0
- react ^19.2.5
- react-dom ^19.2.5
- simplex-noise ^4.0.3
- three ^0.184.0

Development:
- @eslint/js ^10.0.1
- @playwright/test ^1.59.1
- @types/node ^24.12.2
- @types/prismjs ^1.26.6
- @types/react ^19.2.14
- @types/react-dom ^19.2.3
- @types/three ^0.184.0
- @vitejs/plugin-react ^6.0.1
- eslint ^10.2.1
- eslint-plugin-react-hooks ^7.1.1
- eslint-plugin-react-refresh ^0.5.2
- globals ^17.5.0
- typescript ~6.0.2
- typescript-eslint ^8.58.2
- vite ^8.0.10
```

## SBOM Summary

Prophet's current public SBOM source of truth is:

- `prophet-console/package-lock.json` for npm transitive packages.
- `prophet-console/package.json` for npm direct dependencies and scripts.
- `world-side/scraper/requirements.txt` for future isolated scraper Python
  dependencies. It is intentionally empty in this release state.
- The repository file tree for stdlib-only Python modules and first-party code.

The safe local generator is:

```bash
make supply-chain-sbom DATE=YYYY-MM-DD
make supply-chain-sbom-check DATE=YYYY-MM-DD
```

It writes a machine-readable first-party review artifact to
`evidence/outputs/runtime/supply-chain/prophet-supply-chain-sbom.json` by
default. That path is ignored and should be attached or shared only as a
review artifact for the exact commit being reviewed. The generated artifact is
not a CycloneDX/SPDX release asset, SLSA attestation, or compliance
certification.

Current hash anchors:

| Artifact | SHA-256 |
|---|---|
| `prophet-console/package.json` | `86a10dd48efd697c4fbf9dc66fe2862dae5393bce61bb64c2d831402ffa8d151` |
| `prophet-console/package-lock.json` | `6d2f4cb520ec57c718f2cfcfd3d708324ac53a3c44cf505a2088eb1e77801ff6` |
| `world-side/scraper/requirements.txt` | `eaabd2deb39a232453f588ed16ff1af407ee16b67bb330d1bf53dfc20f146861` |

Before a public release tag, run `make supply-chain-sbom DATE=YYYY-MM-DD` from
the exact release commit and store the generated machine-readable artifact as a
release asset or ignored runtime review artifact. Do not commit generated SBOM
output unless the release owner explicitly wants that artifact versioned.

## Generated Review Artifact Check

After generating the local review artifact, verify it is ignored and that its
source hashes still match the current dependency source files before sharing it
with a buyer or security reviewer:

```bash
make supply-chain-sbom DATE=YYYY-MM-DD
make supply-chain-sbom-check DATE=YYYY-MM-DD
git check-ignore -v evidence/outputs/runtime/supply-chain/prophet-supply-chain-sbom.json
```

Do not run `check-release-safety.py` directly on this generated runtime
artifact as a release-bound file. The path policy should reject it as an
ignored runtime artifact if someone tries to stage or scan it as commit
content. `make supply-chain-sbom-check` is the right validator for the ignored
review artifact: it checks the schema, requested date, source-file SHA-256
values, component counts, and review-boundary non-claims. Use
`make release-hygiene` for committed-state checks, and use the artifact only as
an ignored review attachment when explicitly approved.

## Provenance Target

For each internal alpha or paid-pilot review, record:

- Git commit SHA and branch.
- GitHub Actions run URL and conclusion.
- `prophet-console/package-lock.json` SHA-256.
- `prophet-console/package.json` SHA-256.
- `world-side/scraper/requirements.txt` SHA-256.
- `scripts/pilot-demo-smoke.sha256` verification result.
- Policy ID and policy hash from the generated evidence bundle.
- Validation dashboard verdict and build-gate state.

Minimum local provenance commands:

```bash
git rev-parse HEAD
shasum -a 256 prophet-console/package.json prophet-console/package-lock.json world-side/scraper/requirements.txt
make release-hygiene
make validation-dashboard DATE=YYYY-MM-DD
```

## Vulnerability Process

Default gates:

- `cd prophet-console && npm audit --audit-level=moderate`
- `make release-hygiene`
- `PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py --tracked --paths-only`
- `./scripts/check-secrets-archaeology.sh --current-only`
- GitHub Actions `ci` on `main`

Triage:

- Critical or high package vulnerability in a runtime dependency blocks pilot
  release unless the affected code path is unreachable and the exception is
  documented.
- Moderate runtime vulnerability requires owner review before buyer sharing.
- Development-only vulnerability may be accepted temporarily only when it cannot
  affect runtime artifacts, CI secrets, generated buyer evidence, or local
  operator machines.
- Any vulnerability involving credential exposure, install script compromise,
  arbitrary code execution during install/build, or provenance tampering is a
  security incident and should use `docs/INCIDENT_RESPONSE_PLAYBOOK.md`.

Remediation:

- Prefer lockfile-preserving patch updates.
- Rerun console acceptance, release hygiene, and pilot smoke after dependency
  changes.
- Do not commit `node_modules/`, `dist/`, audit caches, or generated runtime
  outputs.
- Document unresolved vulnerabilities as explicit exceptions with owner,
  rationale, affected package, affected path, and review date.

## Update Cadence

| Cadence | Action |
|---|---|
| Every commit touching dependencies | Rerun `npm ci`, console lint/build/tests, `npm audit --audit-level=moderate`, and release hygiene. |
| Before internal alpha or paid-pilot review | Recompute hashes above, rerun GitHub CI, release hygiene, validation dashboard, and pilot smoke. |
| Weekly during active validation | Review npm audit output and GitHub Dependabot/security alerts if enabled. |
| Before public release tag | Run `make supply-chain-sbom DATE=YYYY-MM-DD` and `make supply-chain-sbom-check DATE=YYYY-MM-DD` from the exact release commit, run full release checklist, and resolve the historical secret-history owner decision. |

## Current Gaps

- No committed CycloneDX/SPDX SBOM artifact for Prophet itself. The current
  `make supply-chain-sbom` output is an ignored local review inventory.
- No signed provenance attestation.
- No dependency license review packet.
- No production container image digest because the current product path is a
  local pilot, not a packaged production service.
- Public release tagging remains blocked by the historical secret-history owner
  decision in `docs/SECRET_HISTORY_REVIEW.md`.
