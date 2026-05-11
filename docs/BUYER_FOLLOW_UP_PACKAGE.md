# Buyer Follow-Up Package

Use this after a qualified buyer has described a real prioritization workflow
and reviewed the fixture-backed Prophet evidence path. Do not send it as a cold
deck substitute. The goal is to convert real pain into a scoped discovery or
paid pilot next step.

## When To Send

Send only when at least one of these is true:

- The buyer described a recent painful prioritization event.
- The buyer asked for the evidence sample.
- The buyer named a SOC, platform, product-security, mission, or leadership
  stakeholder who would review the output.
- The buyer asked what a safe pilot would require.

Do not send if the buyer only asked for offensive validation, live target
testing, autonomous remediation, or generic AI cyber capability.

## Package Contents

Attach or link only customer-safe artifacts:

- `docs/EVALUATOR_START_HERE.md`
- `docs/PILOT_SCOPE.md`
- `docs/DESIGN_PARTNER_PILOT_OFFER.md`
- `docs/EVALUATOR_WORKSHEET.md`
- `docs/BUYER_FAQ.md`
- Generated fixture evidence after a smoke run:
  `evidence/outputs/runtime/latest-edge-appliance.md`
- Generated handoff manifest after a smoke run:
  `integrations/outputs/runtime/latest-edge-appliance/manifest.json`
- Generated handoff review checklist after a smoke run:
  `integrations/outputs/runtime/latest-edge-appliance/review_checklist.md`
- Generated handoff review ZIP after a smoke run:
  `integrations/outputs/runtime/latest-edge-appliance-review-bundle.zip`

Before using the generated evidence or handoff artifacts, run:

```bash
make buyer-follow-up-check
```

The Make target refreshes the deterministic fixture smoke before verification,
then checks that the generated runtime artifacts are ignored, untracked, and
match the smoke hash manifest. Use the lower-level
`python3 scripts/check-buyer-follow-up-package.py --format text` only when you
intentionally want to check the current runtime files without refreshing them.

Do not include raw customer data, raw scraper text, credentials, private
hostnames, live IPs, screenshots of customer systems, or lab/offensive material.

## Follow-Up Email

```text
Subject: Prophet follow-up: evidence-backed prioritization pilot

Thanks for walking through the current workflow.

My read of the pain:
- Trigger:
- Current tools involved:
- Manual evidence work:
- Stakeholders who need the answer:
- Handoff format that matters:

The narrow Prophet pilot I would propose is one approved asset/SBOM family and
one exposure-class decision packet. The output would be a policy-bound evidence
bundle, audit/hash manifest, and SOC/ticket review templates. No live targets,
no payloads, no raw telemetry, and no production pushes.

For review, I included:
- What the fixture-backed pilot proves and does not prove.
- The pilot scope and out-of-scope boundaries.
- A worksheet your team can use to judge evidence quality.
- The design-partner pilot shape.

The next useful meeting would include the person who owns the prioritization
decision and one SOC/platform reviewer. The question to answer is whether this
evidence packet is worth a paid design-partner pilot on one approved asset/SBOM
slice.
```

## Pilot Conversion Checklist

Before proposing custom work, confirm:

- Recent painful prioritization event named.
- Existing scanner/exposure-management workflow described.
- Evidence gap is specific and repeated.
- Safe asset/SBOM metadata source identified.
- SOC or platform handoff format identified.
- Budget owner, executive sponsor, or procurement sponsor named.
- Written success criteria agreed.
- Unsafe asks rejected or removed from scope.

## Procurement / Security Questionnaire Draft

Use these short answers when a qualified buyer asks what security or procurement
review would need. Do not use this as a certification claim.

| Question | Draft Answer |
|---|---|
| What is Prophet in the pilot? | A policy-bound defensive evidence workflow that helps a security team decide what exposure class to review first and why. |
| What is Prophet not? | It is not live attack prediction, exploit tooling, live target validation, autonomous remediation, or a production control system. |
| What data is required? | Sanitized asset/SBOM or workflow metadata at product-family or package-family level, plus agreed policy and handoff preferences. |
| What data is prohibited? | Credentials, secrets, live IPs, private hostnames, target URLs, raw telemetry, raw scanner exports, raw scraper text, screenshots, payloads, and CUI unless separately scoped. |
| Where does pilot data live? | The public pilot uses fictional fixtures. Any customer metadata must stay inside the agreed customer data boundary and must not enter the public repo. |
| What leaves the customer environment? | Only customer-approved summaries, hashes, evidence bundles, and review templates inside the agreed pilot boundary. |
| Does Prophet push to production systems? | No. Current SIEM and ticketing outputs are review templates only. Production pushes require a separate approved scope. |
| How is evidence integrity shown? | Runtime artifacts include SHA-256 hashes, policy hash, approval record hash, audit events, and handoff manifest hashes. |
| Is Prophet compliance-certified? | No. Compliance gaps are tracked in `docs/COMPLIANCE_GAP_MAP.md`; the pilot should not be represented as CMMC, FedRAMP, SOC 2, or production SaaS ready. |
| What is the smallest approval path? | One approved asset/SBOM slice, written success criteria, named sponsor, named operating reviewer, and written data-boundary agreement. |

## Export-Control Review Placeholder

This is not legal advice. Use it to decide when the buyer's export-control,
legal, or contracting owner must review the pilot before any customer metadata
or artifact is shared.

Trigger review if any are true:

- The buyer says the work involves defense articles, technical data, defense
  services, CUI, controlled software, encryption controls, export-controlled
  systems, or non-U.S. person access restrictions.
- The pilot would share customer-owned technical details across borders or with
  people outside the approved review group.
- The pilot would move beyond product-family or package-family metadata into
  design, operation, maintenance, repair, testing, or modification details of a
  defense system.
- The buyer asks Prophet to handle artifacts governed by ITAR, EAR, contract
  export-control clauses, or program-specific dissemination rules.

Default answer until review is complete:

- Keep the pilot fixture-only or use sanitized product-family metadata only.
- Do not accept technical data, controlled software, raw telemetry, screenshots,
  live target details, private hostnames, IPs, or payload material.
- Do not involve additional reviewers, contractors, or non-U.S. persons unless
  the buyer's export-control owner approves the sharing path.
- Record the approved data boundary, reviewer group, and retention expectation
  before any customer-owned metadata is used.

Useful official references for the reviewer:

- BIS Export Administration Regulations:
  <https://www.bis.gov/regulations/ear/export-administration-regulations>
- BIS deemed exports overview:
  <https://www.bis.gov/deemed-exports>
- BIS export compliance programs:
  <https://www.bis.gov/developing-an-export-compliance-program>
- DDTC ITAR landing page:
  <https://www.pmddtc.state.gov/ddtc_public/ddtc_public?id=ddtc_public_portal_itar_landing&tab-itar=>

## Data Processing Addendum Notes

These are scoping notes for counsel or procurement, not a DPA. Use them to
decide whether a full data processing addendum is required before a pilot.

Default pilot position:

- The public pilot uses fictional fixtures and does not require personal data.
- A qualified customer pilot should use sanitized asset/SBOM or workflow
  metadata only.
- Prophet should not receive credentials, live IPs, private hostnames, raw
  telemetry, raw logs, raw scanner exports, screenshots, regulated personal
  data, CUI, or payload material.

Items to define if customer metadata is approved:

| Topic | Pilot Note |
|---|---|
| Roles | Identify the customer data owner, customer operator, security reviewer, and Prophet operator. |
| Purpose | Limit processing to one evidence-backed prioritization workflow and agreed handoff review. |
| Data categories | Product-family, package-family, exposure class, owner queue label, business criticality, policy choices, and handoff format. |
| Excluded data | Personal data, credentials, target details, raw telemetry, raw logs, screenshots, payloads, CUI unless separately approved. |
| Location | Keep customer metadata inside the agreed pilot boundary; do not commit it to the public repo. |
| Access | Limit access to named pilot operators and reviewers. |
| Subprocessors | Do not introduce subprocessors or hosted services without separate written approval. |
| Retention | Define deletion or return timing before accepting customer metadata. |
| Security | Run release-safety on committed docs/code, run the pilot smoke/runtime validators for generated evidence and handoff outputs, keep runtime artifacts ignored and unstaged, and review hash manifests before sharing. |
| Return/delete | At closeout, delete or rotate local runtime outputs and private notes unless the customer approves retaining summaries and hashes. |

Useful official references for the reviewer:

- FTC protecting personal information:
  <https://www.ftc.gov/business-guidance/resources/protecting-personal-information-guide-business>
- NIST Privacy Framework:
  <https://www.nist.gov/privacy-framework>
- NIST Privacy Framework FAQ:
  <https://www.nist.gov/privacy-framework/frequently-asked-questions>

## Success Criteria Template

Use this in the next meeting:

```text
The pilot succeeds if the customer can say at least three are true:

- Prophet reduced time to create a leadership/SOC-ready prioritization packet.
- Prophet connected approved asset/SBOM context and public vulnerability context
  better than the current manual workflow.
- Prophet produced a defensible "why this first?" artifact that stakeholders
  trusted enough to review.
- Policy, audit events, and hashes made the evidence easier to assess.
- The team would run the workflow again for another exposure class.
- The team wants a dry-run integration with an existing scanner, SIEM, ticketing,
  or SBOM workflow.
```

## Disqualifiers

Pause or disqualify the pilot if:

- The buyer cannot name a recent painful event.
- The buyer's current platform already produces the trusted evidence packet.
- The buyer wants live exploitation, payloads, arbitrary target input, or
  autonomous remediation.
- The buyer will not provide any sanitized workflow or metadata artifact.
- No stakeholder with budget, operational pain, or authority will join the next
  review.
