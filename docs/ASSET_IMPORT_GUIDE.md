# Asset CSV Import Guide

Prophet accepts customer-owned asset metadata only. The CSV importer rejects
hostnames, IPs, URLs, credentials, secrets, payload-like fields, unsupported
columns, and live target names.

## CSV Columns

Required columns:

```text
asset_id,product_family,exposure_class,owner_group,environment,business_criticality,sbom_components,known_cve_overlaps,compensating_controls
```

`sbom_components` uses semicolon-separated entries:

```text
name|version_family|package_type;name|version_family|package_type
```

`known_cve_overlaps` and `compensating_controls` use semicolon-separated values.
The importer also accepts the earlier fixture delimiter style
`name@version_family:package_type|name@version_family:package_type` for
backward compatibility with checked-in tests.

Choose `exposure_class` values using
`docs/EXPOSURE_CLASSIFICATION_GUIDE.md`. The class should describe a safe
product-family or workflow-family decision, not a targetable customer system.

## Import Command

```bash
PYTHONPATH=. python3 -m assets.import_csv \
  --csv assets/fixtures/dib-edge-appliance-inventory.csv \
  --inventory-id customer-safe-import \
  --scope "Customer-owned product-family metadata; no live targets named." \
  --generated-at 2026-05-05T08:00:00Z \
  --fixture \
  --out assets/outputs/runtime/customer-safe-inventory.json \
  --report-out assets/outputs/runtime/customer-safe-import-report.json \
  --seedset-out assets/outputs/runtime/customer-safe-seedset.json \
  --seedset-run-id customer-safe-seedset
```

The report includes accepted and rejected row counts, source CSV SHA-256, and
cleanup errors without echoing unsafe row values.

## Fixture Packs

- `assets/fixtures/dib-edge-appliance-inventory.csv`
- `assets/fixtures/dib-edge-appliance-inventory.json`
- `assets/fixtures/dib-edge-appliance-seedset.json`
- `assets/fixtures/financial-workflow-inventory.csv`
- `assets/fixtures/financial-workflow-inventory.json`
- `assets/fixtures/financial-workflow-seedset.json`

Both fixture packs are fictional and product-family level only.

## Generating Customer-Safe Fixture Examples

Use this workflow when creating a new example fixture for a buyer review,
design-partner discussion, demo sector, or regression test. The goal is to
preserve the shape of a real remediation workflow without importing targetable
customer data.

1. Start from a workflow class, not a named customer environment.
   Examples: `edge-appliance`, `financial-workflow`,
   `identity-infrastructure`, or `mission-support-platform`.
2. Use synthetic `asset_id` values such as `fixture-edge-001`. Do not use
   customer asset names, hostnames, URLs, serial numbers, ticket IDs, project
   names, or internal system labels.
3. Keep `product_family` broad enough for prioritization but too generic to
   identify a deployment. Good examples are `remote-access-gateway`,
   `java-application-service`, and `managed-file-transfer`.
4. Use queue-style `owner_group` values such as `platform-security`,
   `product-security`, `soc-review`, or `mission-assurance`. Do not use real
   names, emails, aliases, Slack handles, team codes, or vendor account names.
5. Keep `environment` class-level: `fixture`, `demo`, `lab`, `staging-like`,
   or `customer-approved-metadata`. Do not use region names, subnet labels,
   cluster names, cloud account names, or facility identifiers.
6. Limit `sbom_components` to package or component families. Version families
   such as `major-2`, `2024-family`, or `supported-lts` are acceptable; exact
   internal build numbers are not.
7. Use public CVE IDs only in `known_cve_overlaps`. Do not include scanner
   plugin output, raw advisory text, exploit strings, or customer ticket notes.
8. Describe `compensating_controls` as high-level review hints such as
   `waf-rule-review`, `network-segmentation`, or `manual-change-window`.
   Do not include firewall rules, IP ranges, URLs, hostnames, credentials, or
   production change IDs.

Minimum review before committing a fixture:

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

Commit only the reviewed fixture source. Runtime inventory, report, and
seedset outputs stay under ignored `assets/outputs/runtime/` paths unless a
separate release process intentionally promotes a sanitized golden fixture.

Reject the fixture if review finds any of these:

- Live IPs, private hostnames, URLs, or target endpoints.
- Customer names, real team/person names, emails, handles, account IDs, site
  codes, facility names, serial numbers, or ticket IDs.
- Credentials, secrets, tokens, cookies, SSH material, or session files.
- Raw scanner exports, raw telemetry, raw logs, raw scraper text, screenshots,
  exploit strings, payloads, or procedural attack content.
- Exact deployment topology, subnet layout, cloud account detail, firewall
  rules, or production change instructions.

## Boundary

The importer does not collect data, scan systems, or resolve targets. It only
turns approved metadata into Prophet's `asset_inventory.v0.1` shape and optional
`asset_osint_seedset.v0.1` output.
