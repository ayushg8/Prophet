# NIST 800-171 And CMMC-Oriented Security Packet

Date: 2026-05-11

This packet is for defense-tech buyer and security-review conversations about
the current Prophet local buyer pilot. It is not a certification claim and it
does not make Prophet CMMC-ready, FedRAMP-ready, SOC 2-ready, or production
SaaS-ready.

## Source Basis

Use current official sources before changing this packet:

- DoD CMMC overview and resources:
  <https://dodcio.defense.gov/CMMC/> and
  <https://dodcio.defense.gov/CMMC/Resources-Documentation/>
- 32 CFR Part 170 CMMC Program final rule:
  <https://www.federalregister.gov/documents/2024/10/15/2024-22905/cybersecurity-maturity-model-certification-cmmc-program>
- 48 CFR DFARS CMMC implementation rule:
  <https://www.federalregister.gov/documents/2025/09/10/2025-17359/defense-federal-acquisition-regulation-supplement-assessing-contractor-implementation-of>
- NIST SP 800-171 Rev. 3:
  <https://csrc.nist.gov/pubs/sp/800/171/r3/final>
- NIST SP 800-171A Rev. 3:
  <https://csrc.nist.gov/pubs/sp/800/171/a/r3/final>

Current operating assumptions:

- CMMC Phase 1 implementation began on 2025-11-10 and runs through
  2026-11-09, primarily focused on Level 1 and Level 2 self-assessments.
- DoD CMMC Level 2 materials still reference the 110 requirements in
  NIST SP 800-171 Revision 2 for CMMC assessment purposes.
- NIST SP 800-171 Rev. 3 and NIST SP 800-171A Rev. 3 are final NIST
  publications and should inform forward-looking control language.
- Prophet's current public repo is a policy-bound local pilot, not a system
  authorized to process, store, or transmit CUI.

## Review Scope

Included:

- Local pilot architecture, evidence generation, policy, audit, and handoff
  review templates.
- Customer-safe asset/SBOM metadata boundary.
- Validation sprint artifacts that keep production work gated.
- Existing docs and tests that show safe handling, policy enforcement, and
  buyer-review packaging.

Excluded:

- Customer CUI, FCI, credentials, raw telemetry, raw scraper text, private
  hostnames, live IPs, or live target URLs.
- Hosted production services, tenant data stores, customer identity providers,
  production integrations, or push-mode remediation.
- CMMC certification evidence, SPRS submission support, eMASS submission
  support, or assessor-ready control operation evidence.

## SSP Draft

| Field | Current pilot answer |
|---|---|
| System name | Prophet local buyer pilot |
| System purpose | Produce policy-bound defensive prioritization evidence for "why this exposure first, why now, and what handoff follows?" |
| Operating model | Local workstation demo using fixtures, sanitized seeded OSINT, deterministic localhost sandbox, and review-template exports. |
| System boundary | Public repo code, local runtime outputs, local console, local control server, checked-in fixtures, policy files, and generated review artifacts. |
| Data boundary | Approved fictional fixtures and sanitized customer-owned metadata only. No CUI, credentials, raw telemetry, private hostnames, live IPs, payloads, or production pushes. |
| Users | Local operator and reviewer labels only; production identity is not implemented. |
| External connections | None required for the fixture path. Generated handoffs are files for review, not live integration pushes. |
| Evidence retention | Runtime outputs are ignored and governed by `docs/DATA_CLASSIFICATION_AND_ARTIFACT_INVENTORY.md` and policy retention notes. |
| Build gate | Production platform work remains closed until real target-backed validation reaches `build_next_slice`. |

Primary evidence:

- `README.md`
- `docs/PILOT_SCOPE.md`
- `docs/SAFETY_ARCHITECTURE.md`
- `docs/DATA_CLASSIFICATION_AND_ARTIFACT_INVENTORY.md`
- `docs/PRODUCTION_ARCHITECTURE.md`
- `docs/PROPHET_COMPLETION_AUDIT.md`

## CMMC/NIST Control Matrix

This matrix is a buyer-review starting point. It maps current pilot evidence to
security domains and records gaps that must stay in the POA&M.

| Domain | Current pilot evidence | Current gap |
|---|---|---|
| Access Control | Local operator identity guidance and policy-bound console controls. Evidence: `docs/OPERATOR_IDENTITY_GUIDE.md`, `docs/SIGNED_OPERATOR_APPROVAL_DESIGN.md`, `docs/SIGNED_POLICY_DESIGN.md`. | No production IdP, SSO, session management, service accounts, or enforced RBAC. |
| Awareness And Training | Operator docs describe safe validation, copy-only outreach, and prohibited data. Evidence: `AGENTS.md`, `docs/VALIDATION_SPRINT_CHECKLIST.md`, `docs/CLI_SAFETY_MATRIX.md`. | No formal employee security training program. |
| Audit And Accountability | Local audit events, approval hashes, retention report, and handoff manifests. Evidence: `evidence/`, `integrations/`, `docs/DATA_CLASSIFICATION_AND_ARTIFACT_INVENTORY.md`. | No durable production audit store, centralized review workflow, or customer tenant audit export. |
| Assessment, Authorization, And Monitoring | Production readiness scorecard, release hygiene, CI, and validation dashboard. Evidence: `scripts/production-readiness-scorecard.py`, `make release-hygiene`, `.github/workflows/ci.yml`. | No formal authorization boundary, continuous monitoring plan, or independent assessment. |
| Configuration Management | Policy files, smoke hash manifests, release checklist, and CI gates. Evidence: `policy/`, `scripts/pilot-demo-smoke.sha256`, `docs/RELEASE_CHECKLIST.md`. | No environment promotion workflow, deployment baseline, or production change approval system. |
| Identification And Authentication | Local labels only. Evidence: `docs/OPERATOR_IDENTITY_GUIDE.md`. | No production authentication, MFA, OIDC/SAML, password policy, or service identity. |
| Incident Response | Pilot incident response playbook covers data spill, credential exposure, policy bypass, integration misfire, sandbox escape, and customer notification. Evidence: `docs/INCIDENT_RESPONSE_PLAYBOOK.md`. | Tabletop exercise and customer-specific contact matrix are not complete. |
| Maintenance | Local development scripts and release checks are documented. Evidence: `docs/CLI_REFERENCE.md`, `Makefile`. | No production maintenance windows, privileged maintenance accounts, or customer maintenance notices. |
| Media Protection | Runtime outputs are ignored and scoped by the data classification inventory. Evidence: `.gitignore`, `docs/DATA_CLASSIFICATION_AND_ARTIFACT_INVENTORY.md`. | No production media handling, encryption-at-rest, backup media, or secure disposal workflow. |
| Physical Protection | Local pilot runs on operator-controlled machines. | No production facility, hosting, or inherited physical control package. |
| Planning | Completion audit, readiness backlog, production plan, and gap map exist. Evidence: `docs/PROPHET_COMPLETION_AUDIT.md`, `docs/production-readiness-backlog.json`, `docs/PRODUCTION_EXECUTION_PLAN.md`, `docs/COMPLIANCE_GAP_MAP.md`. | No assessor-ready SSP, customer-specific scope, or signed security plan. |
| Personnel Security | Not applicable to the public repo pilot. | No personnel screening, termination, or access removal process. |
| Risk Assessment | Threat model, safety architecture, readiness review, and secret-history review exist. Evidence: `docs/THREAT_MODEL.md`, `docs/SAFETY_ARCHITECTURE.md`, `docs/DEFENSE_TECH_READINESS_REVIEW.md`, `docs/SECRET_HISTORY_REVIEW.md`. | No recurring risk committee, vulnerability SLA evidence over time, or accepted POA&M owner signoff. |
| System And Services Acquisition | Supply-chain packet and dependency audit process exist. Evidence: `docs/SOFTWARE_SUPPLY_CHAIN_PACKET.md`. | No license review, machine-readable SBOM release asset, signed provenance, vendor review, or production procurement controls. |
| System And Communications Protection | Fixture/local policy blocks live targets, credentials, payloads, and private hosts. Evidence: `policy/prophet-pilot-policy.json`, `docs/SAFETY_ARCHITECTURE.md`. | No production TLS termination, network policy, customer connectivity design, or encryption-at-rest implementation. |
| System And Information Integrity | Validators, release safety scans, default output safety checks, dependency audit, and CI exist. Evidence: `scripts/check-release-safety.py`, `scripts/check-default-output-safety.py`, `.github/workflows/ci.yml`. | No production vulnerability scanning cadence, patch SLA evidence, SAST/DAST program, or container scanning. |
| Supply Chain Risk Management | Dependency inventory, lockfile hashes, vulnerability process, and update cadence exist. Evidence: `docs/SOFTWARE_SUPPLY_CHAIN_PACKET.md`. | No generated CycloneDX/SPDX release SBOM, signed attestations, or dependency license review. |

## Data Flows

Current local buyer-pilot flow:

1. Operator runs fixture-backed or approved-metadata pilot commands locally.
2. Asset/SBOM seedset uses fictional or sanitized customer-owned metadata.
3. Seeded OSINT snapshot is sanitized and provenance-manifested.
4. Forecaster emits a policy-bound forecast artifact.
5. Sandbox runner emits deterministic localhost evidence only.
6. Evidence bundle emits JSON/Markdown with policy and approval hashes.
7. Integration exporter emits SIEM/ticket/audit review templates and a review
   ZIP, not production pushes.
8. Console shows the local evidence workflow and guarded controls.

Primary references:

- `docs/PILOT_SCOPE.md`
- `docs/PILOT_DEMO.md`
- `docs/ASSET_IMPORT_GUIDE.md`
- `docs/DATA_CLASSIFICATION_AND_ARTIFACT_INVENTORY.md`
- `docs/CONSOLE_EXPECTED_SCREENSHOTS.md`

## Asset Inventory

Current pilot asset inventory is intentionally fictional or sanitized:

- CSV import guide: `docs/ASSET_IMPORT_GUIDE.md`
- Runtime seedset path: `assets/outputs/runtime/demo-dib-edge-appliance-seedset.json`
- Fixture inventory code and tests: `assets/`
- Pilot scope data boundary: `docs/PILOT_SCOPE.md`

Buyer-pilot rule:

- Do not accept CUI, raw environment exports, private hostnames, IP addresses,
  credentials, screenshots of customer systems, or raw scanner telemetry into
  this repo or any agent prompt.

## Access Controls

Current pilot controls:

- Local operator identity labels are constrained by
  `docs/OPERATOR_IDENTITY_GUIDE.md`.
- Policy-bound console actions require explicit local policy context.
- Signed operator approval, signed evidence manifest, and signed policy designs
  exist for future review, but they are not implemented as production controls.

Open access-control gaps:

- OIDC/SAML.
- MFA.
- Enforced RBAC roles.
- Tenant membership.
- Service accounts.
- Session timeout and revocation.
- Audit-backed approval quorum.

## Incident Response

Use `docs/INCIDENT_RESPONSE_PLAYBOOK.md` for the current pilot. It covers:

- Data spill.
- Credential exposure.
- Policy bypass.
- Integration misfire.
- Sandbox escape.
- Customer notification.

Before any paid pilot that touches approved customer metadata:

- Fill a customer-specific contact matrix.
- Run a tabletop exercise.
- Decide escalation owner and response window.
- Confirm whether the customer treats any supplied metadata as CUI or FCI.

## POA&M

| ID | Gap | Owner | Status | Next action |
|---|---|---|---|---|
| POAM-001 | Real buyer demand is not proven. | Founder | Open | Send current private outreach drafts, log sanitized outcomes, and reach target-backed `build_next_slice` before production build scope. |
| POAM-002 | Prophet is not authorized for CUI/FCI handling. | Security | Open | Keep the pilot to fixtures and approved sanitized metadata until a customer-specific data agreement and control boundary exist. |
| POAM-003 | Production identity and RBAC are missing. | Security/Engineering | Open | Design OIDC/SAML, roles, tenant membership, and audit-backed approvals after validation justifies production scope. |
| POAM-004 | Durable evidence and audit storage are missing. | Engineering | Open | Build only after `build_next_slice`; require tenant scoping, immutability, retention, and export tests. |
| POAM-005 | No machine-readable release SBOM or signed provenance artifact exists. | Security | Open | Generate SBOM and provenance artifacts from the exact release commit before public tagging. |
| POAM-006 | Incident response tabletop is not complete. | Security | Open | Run the tabletop and fill the pilot contact matrix before accepting customer metadata. |
| POAM-007 | External security review is not complete. | Security | Blocked | Requires production-shaped deployment, tenant isolation, identity, security packet review, and buyer/security-review demand. |
| POAM-008 | Historical secret-history finding is unresolved. | Founder/Security | Blocked | Record owner decision in `docs/SECRET_HISTORY_REVIEW.md` before public release tagging. |

## Buyer-Facing Non-Claims

Do not say:

- "Prophet is CMMC-ready."
- "Prophet is NIST 800-171 compliant."
- "Prophet can process CUI."
- "Prophet is assessor-ready."
- "Prophet is a production SaaS."

Accurate language:

- "Prophet has a local, policy-bound buyer pilot with safety gates, evidence
  hashes, audit exports, and review-template handoffs."
- "This packet maps current pilot evidence to security-review questions and
  lists the POA&M gaps before any CUI, CMMC, or production claim."
- "Production build scope remains gated until target-backed validation reaches
  `build_next_slice`."
