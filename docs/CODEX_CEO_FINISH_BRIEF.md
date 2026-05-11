# Codex CEO Finish Brief For Prophet

Use this brief as the main instruction set when asking Codex to finish Prophet.
This is intentionally CEO/product-level first and technical second.

## The Company-Level Goal

Prophet should become a trusted defensive cyber product for teams that need to
decide what to harden first under pressure and prove why that decision was
reasonable.

The final product is not an exploit platform. It is not a zero-day prediction
machine. It is not an autonomous patching system.

The final product is:

> A policy-bound evidence system for defensive prioritization. Prophet helps a
> security team turn asset/SBOM context, public vulnerability context, forecast
> reasoning, sandbox-safe validation, and SOC handoff artifacts into an
> auditable "why this first" package.

## The Buyer

Think like a CEO selling to one narrow first buyer, not everyone.

Best first buyer:

- DIB / defense-adjacent product security team.
- Federal-adjacent platform security or mission-assurance team.
- Vulnerability management leader who briefs leadership.
- SOC/CTI leader who has to translate threat/vulnerability pressure into
  tickets, detections, and executive justification.

The buyer already has scanners, SIEM, ticketing, SBOM tools, threat intel, and
vulnerability management. Prophet wins only if it connects those pieces into a
better decision/evidence workflow.

## The Core Pain To Prove

The painful question is:

> "When pressure hits, how do we prove what to harden first?"

The customer pain is not "I need more vulnerabilities." They already have too
many. The pain is prioritization, justification, and handoff:

- Which exposure class matters first?
- Why now?
- What asset/SBOM context supports this?
- What source evidence supports this?
- What should SOC/platform teams review next?
- What artifact can leadership, auditors, or a government customer trust?

## The Product Wedge

The wedge is evidence-backed vulnerability/exposure prioritization.

Do not lead with:

- AI.
- Zero-day prediction.
- Live validation.
- Offensive security.
- Autonomous remediation.
- "We replace your scanner."

Lead with:

- Evidence-backed prioritization.
- Audit-ready defensive evidence.
- Policy-bound workflow.
- Safe handoff templates.
- Customer-owned metadata only.
- No live targets, no payloads, no raw scraper text.

## What Codex Should Do First

Before building more product, Codex should verify the current truth:

1. Read the current repo docs.
2. Run the existing validation dashboards.
3. Inspect whether customer validation has proven demand.
4. Research the current market and buyer landscape.
5. Update the plan based on evidence, not optimism.

Codex should research:

- CISA KEV and BOD pressure.
- EPSS / vulnerability prioritization.
- Exposure management incumbents.
- DIB / defense contractor cybersecurity requirements.
- SIEM/ticketing/security workflow products.
- Buyer language around vulnerability management, CTI, SBOM, and mission
  assurance.

Research should be used to sharpen positioning and identify buyer objections,
not to add unsafe capabilities.

## Hard Safety Boundaries

Codex must not enable or set up dangerous VM/lab/offensive workflows.

Do not:

- Enable VM scraper workflows.
- Run exploit labs.
- Add live target validation.
- Add payload generation.
- Add arbitrary target input.
- Add raw scraper text to evidence.
- Add credentials, secrets, private hostnames, or live IPs.
- Add autonomous production push actions.
- Reintroduce archived lab exploit material into product paths.

Default Prophet behavior must stay:

- Fixture-backed.
- Policy-bound.
- Localhost or approved sandbox only.
- Review-template-only for integrations.
- Safe for a buyer evaluator.

If Codex sees dangerous VM/lab/archive files, it should ignore them or keep them
excluded. It should not delete user files unless explicitly asked.

## Final Product Shape

The eventual product should have four clear user-facing jobs:

1. **Prioritize**
   - Ingest approved asset/SBOM metadata.
   - Combine it with safe public vulnerability/source context.
   - Produce a clear recommendation for what exposure class deserves attention.

2. **Explain**
   - Show why this matters now.
   - Show source basis, asset basis, confidence, freshness, and assumptions.
   - Make the reasoning reviewable by humans.

3. **Validate Safely**
   - Use deterministic fixtures or approved sandbox/digital-twin validation.
   - Never touch live third-party targets.
   - Record validation results as evidence, not exploit procedures.

4. **Hand Off**
   - Generate evidence bundles.
   - Generate SIEM/ticketing review templates.
   - Record policy, approval, audit, and hashes.
   - Help SOC/platform teams act without trusting magic.

## What Needs To Be Finished

### 1. Demand Validation

This is the highest-level gate.

Codex should make sure the validation sprint is operational and then use the
scorecards to decide whether the build gate is open.

Demand is proven only if the repo or private validation data shows:

- Enough qualified buyer conversations.
- Repeated high-pain workflow.
- Real design-partner or paid pilot pull.
- Clear buyer segment and buyer language.

If not proven, Codex should improve validation materials and stop building
platform features.

### 2. Pilot Packaging

The current pilot should be easy for a serious evaluator to run.

Finish:

- Fresh-clone smoke path.
- Clear evaluator docs.
- Clear "what this proves / does not prove."
- Demo evidence sample.
- Buyer follow-up package.
- Release tag/checklist if appropriate.

### 3. Buyer-Facing Narrative

Make the product easy to understand:

- One-line pitch.
- Target buyer.
- Pain.
- Why existing tools are insufficient.
- What Prophet produces.
- Why it is safe.
- What a pilot looks like.
- What success means.

### 4. Minimal Production Slice

Only after real pull exists, build the smallest required production slice.

Likely first slice:

- Durable evidence store.
- Tenant/RBAC API around policy and evidence.
- Customer-safe SBOM/asset import.
- One integration dry-run mode.
- Sandbox provenance.

Avoid building broad SaaS infrastructure before a committed pilot needs it.

### 5. Trust And Security

The product must earn trust.

Finish over time:

- Policy enforcement.
- Audit trail.
- Tenant isolation.
- RBAC/SSO.
- Evidence integrity.
- Retention/deletion.
- Secrets handling.
- Observability.
- Incident response.
- Compliance/security review packet.

## CEO Decision Rules

Codex should use these rules:

1. If buyer demand is not proven, do not build production platform features.
2. If customers ask for live/offensive capability, do not build it.
3. If a feature does not help prioritization, explanation, safe validation, or
   handoff, deprioritize it.
4. If the product becomes hard to explain in one minute, simplify.
5. If current tools already solve the buyer pain, pivot or stop.
6. If one narrow buyer pulls hard, build only for that buyer's repeated pain.

## Research Expectations

Codex should use web research for current market and buyer reality. It should
prefer official/vendor/primary sources and cite what it uses in docs or notes.

Research outputs should answer:

- Who has this pain?
- What do they use today?
- Why is the status quo insufficient?
- Who controls budget?
- What integrations matter first?
- What claims are unsafe or unbelievable?
- What is the narrowest paid pilot?

## Definition Of Done

Prophet is finished as a product only when:

- The buyer segment is specific.
- Demand is proven by real buyer behavior.
- The pilot is repeatable and safe.
- The product narrative is clear and honest.
- Evidence output is useful enough for a buyer workflow.
- The minimum production slice exists for a real pilot.
- Safety boundaries are enforced.
- Dangerous VM/offensive workflows remain disabled and out of product paths.

Until demand is proven, "done" means the validation sprint is running and the
team is learning from buyers every week.
