# Exposure Classification Guide

Use this guide when a buyer, evaluator, or operator needs to choose the
exposure class Prophet should model first. The goal is to describe a defensive
workflow class clearly enough for prioritization without naming targetable
systems.

## Definition

An exposure class is a broad defensive category that groups product families,
SBOM components, owner queues, and public vulnerability context. It is not a
hostname, IP address, URL, customer system name, account ID, facility, subnet,
scanner export, exploit path, or production ticket.

Good exposure classes are:

- Specific enough to support a "why this first?" decision.
- Broad enough to avoid identifying a deployment.
- Tied to owner workflow and handoff format.
- Reviewable with approved asset/SBOM metadata and public vulnerability
  context.
- Safe to discuss in a fixture-backed or customer-approved metadata pilot.

## Current Fixture Examples

| Exposure class | Use when the buyer workflow is about | Fixture examples |
|---|---|---|
| `edge_appliance` | Internet-adjacent product or appliance families, remote access, perimeter management, or supplier access pressure. | `secure edge appliance family`, `enterprise VPN appliance family`, `managed firewall edge family` |
| `financial_workflow` | Transaction approval, settlement, financial messaging, or business-process continuity. | `financial messaging workflow family` |
| `custody_workflow` | Custody, privileged action approval, separation of duties, or restricted asset operations. | `digital asset custody workflow family` |
| `payment_operations` | Payment operations consoles, high-risk operational queues, or reconciliation workflows. | `payment operations console family` |

Add a new exposure class only when the current classes cannot describe the
workflow without losing the buyer's actual prioritization problem.

## Safe Label Rules

Use labels like:

- `edge_appliance`
- `financial_workflow`
- `custody_workflow`
- `payment_operations`
- `identity_infrastructure`
- `mission_support_platform`
- `managed_file_transfer`

Do not use labels that include:

- Hostnames, URLs, IPs, ports, regions, subnets, account IDs, cluster names, or
  facility identifiers.
- Real customer, program, project, team, person, Slack, email, or ticket names.
- Scanner plugin text, raw telemetry, raw log names, raw scraper text, exploit
  strings, payload terms, or procedural attack detail.
- Vendor account details, serial numbers, exact deployment topology, firewall
  rules, or production change IDs.

## Classification Workflow

1. Start with the buyer's painful prioritization event.
2. Ask what artifact they had to produce: leadership packet, SOC handoff,
   audit evidence, ticket packet, or exception rationale.
3. Identify the owner queue that would act on the result.
4. Pick the broadest product-family or workflow class that still explains the
   decision.
5. Confirm the buyer can provide only approved metadata: product family, package
   family, owner queue, business criticality, public CVE overlap, and high-level
   compensating controls.
6. Reject the class if the buyer must provide targetable details before Prophet
   can reason about it.
7. Record the exposure class in the asset import or interview artifact only
   after it passes the safety boundary.

## Review Questions

Use these questions before importing customer-owned metadata:

| Question | Good answer | Stop if |
|---|---|---|
| Can the class be described without naming a live system? | "Remote-access appliance family" | A hostname, URL, IP, region, account, or facility is required. |
| Does a real owner queue care about the result? | Product security, platform security, SOC review, mission assurance. | No owner, or only curiosity. |
| Does the class map to a recent prioritization event? | A painful remediation sequence, exception, customer pressure, or audit ask. | No recent event. |
| Can the buyer provide safe metadata? | Product-family, SBOM component families, public CVEs, business criticality. | Raw telemetry, scanner export, private hostnames, screenshots, or credentials are needed. |
| Is the requested output evidence, not action? | Review packet, audit rationale, SOC/ticket template. | Live validation, exploit testing, production push, or autonomous remediation. |

## Asset Import Mapping

When filling `assets` CSV rows:

- `exposure_class` should use a safe class label from this guide.
- `product_family` should be product-family or workflow-family level.
- `owner_group` should be a queue-style label, not a person or private team
  alias.
- `environment` should be class-level, such as `fixture`, `demo`,
  `staging-like`, or `customer-approved-metadata`.
- `known_cve_overlaps` should contain public CVE IDs only.
- `compensating_controls` should contain high-level review hints only.

Run the asset import safety checks before using a new fixture:

```bash
PYTHONPATH=. python3 -m assets.import_csv \
  --csv assets/fixtures/<new-fixture>.csv \
  --inventory-id <safe-fixture-id> \
  --scope "Fictional customer-safe fixture; product-family metadata only." \
  --generated-at 2026-05-10T00:00:00Z \
  --fixture \
  --out assets/outputs/runtime/<new-fixture>-inventory.json \
  --report-out assets/outputs/runtime/<new-fixture>-report.json \
  --seedset-out assets/outputs/runtime/<new-fixture>-seedset.json \
  --seedset-run-id <safe-fixture-id>-seedset

PYTHONPATH=.:cyber-side:world-side python3 scripts/check-release-safety.py \
  assets/fixtures/<new-fixture>.csv
```

Runtime outputs stay under ignored `assets/outputs/runtime/` paths.

## Validation Use

For discovery calls, the exposure class is a learning tool, not a product build
authorization. Record whether the buyer can describe:

- The exposure class they would review first.
- The current workflow and evidence gap.
- The stakeholder who trusts or rejects the packet.
- The safe metadata source they can provide.
- The handoff format they would review.

The production build gate stays closed unless the private validation dashboard
reaches `build_next_slice` with target-backed interviews.
