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

## Boundary

The importer does not collect data, scan systems, or resolve targets. It only
turns approved metadata into Prophet's `asset_inventory.v0.1` shape and optional
`asset_osint_seedset.v0.1` output.
