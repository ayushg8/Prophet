# Open Source Data Expansion

Prophet's scraper catalog now includes a broader open-source data fabric for
pilot-ready forecasting and evidence generation. The collectors emit only
sanitized metadata records that pass `scraper_side.records.SanitizedRecord`.

## Enabled Metadata Sources

- CVEProject cvelistV5 delta log: CVE ID, update time, and public CVE link.
- CISA Vulnrichment repository commits: update timing only, no file diffs.
- Red Hat Security Data API: CVE, severity, CWE, package-family, and link metadata.
- MITRE ATT&CK Enterprise STIX: object ID/name/type/tactic metadata only.
- MITRE CWE XML: weakness ID/name taxonomy metadata only.
- MITRE CAPEC XML: attack-pattern ID/name/abstraction metadata only.
- MITRE D3FEND JSON-LD: D3FEND ID/label defensive taxonomy metadata only.

These join the existing CISA KEV, NVD, FIRST EPSS, GitHub Advisory Database,
MSRC, vendor RSS, official advisory, public community, and coarse context feeds.

## Seeded Or Explicit-Source Collectors

- CISA Vulnrichment CVE record collector is disabled by default until a CVE seed
  is produced by a forecast or asset match.
- OSV.dev query collector is disabled by default until a package, commit, CVE, or
  OSV identifier seed exists.

Seeded collectors prevent broad scraping while still making asset/SBOM-driven
enrichment straightforward in the next milestone.

## Asset/SBOM Seedset Workflow

Convert fictional or customer-owned inventory into safe OSINT query seeds:

```bash
PYTHONPATH=. python3 -m assets.inventory \
  --inventory assets/fixtures/dib-edge-appliance-inventory.json \
  --out assets/outputs/runtime/asset-osint-seeds-edge-appliance.json
```

The emitted `asset_osint_seedset.v0.1` artifact contains only CVE IDs, package
names, product families, exposure classes, owner queues, source IDs, and hashes.
It explicitly rejects IPs, hostnames, URLs, secret-like values, and live target
names. The seedset is a query plan for open-source enrichment; it does not
perform collection.

Seeded collectors can execute that plan against explicit source IDs. The demo
path below stays offline by using checked-in source-specific fixtures:

```bash
PYTHONPATH=world-side/scraper:. python3 -m scraper_side.snapshot \
  --catalog world-side/scraper/config/source_catalog.json \
  --source cisa_vulnrichment_cve_record_seed \
  --source osv_query_api_seed \
  --source redhat_security_data_cve_api \
  --asset-seedset assets/fixtures/dib-edge-appliance-seedset.json \
  --seed-fixture-dir world-side/fixtures/seeded-osint \
  --limit-per-source 1 \
  --out-jsonl world-side/outputs/runtime/seeded-osint-edge-appliance.jsonl \
  --out-manifest world-side/outputs/runtime/seeded-osint-edge-appliance.manifest.json
```

Live collection for seeded sources still requires `--live`, explicit `--source`
selection, and an approved public-HTTPS collection boundary. The seeded path
never enables broad scraping by default.

Feed the seedset into the forecaster:

```bash
PYTHONPATH=world-side:. python3 -m forecaster.cli \
  --candidate world-side/fixtures/exploit-candidate-edge-appliance.json \
  --osint-snapshot world-side/fixtures/osint-snapshot-sample.jsonl \
  --osint-manifest world-side/fixtures/osint-snapshot-sample.manifest.json \
  --asset-seedset assets/fixtures/dib-edge-appliance-seedset.json \
  --out world-side/outputs/runtime/forecast-with-asset-seeds.json
```

Forecasts now include `asset_seed_context` with asset counts, package/CVE seed
counts, owner queues, recommended open-source source IDs, seedset paths, and
hashes. Evidence bundles render the same basis in the `Asset/SBOM Seeds`
section when `--asset-seedset` is supplied.

## Snapshot Workflow

Generate a sanitized snapshot and manifest from selected collector-ready
sources:

```bash
PYTHONPATH=world-side/scraper python3 -m scraper_side.snapshot \
  --catalog world-side/scraper/config/source_catalog.json \
  --source cveproject_cvelistv5_delta_log \
  --source redhat_security_data_cve_api \
  --source mitre_d3fend_ontology_json \
  --live \
  --limit-per-source 25 \
  --out-jsonl world-side/outputs/runtime/osint-snapshot-demo.jsonl \
  --out-manifest world-side/outputs/runtime/osint-snapshot-demo.manifest.json
```

The forecaster can ingest that snapshot directly:

```bash
PYTHONPATH=world-side python3 -m forecaster.cli \
  --candidate world-side/fixtures/exploit-candidate-edge-appliance.json \
  --chatter world-side/fixtures/sanitized-chatter-sample.jsonl \
  --osint-snapshot world-side/outputs/runtime/osint-snapshot-demo.jsonl \
  --osint-manifest world-side/outputs/runtime/osint-snapshot-demo.manifest.json \
  --out world-side/outputs/runtime/forecast-with-osint.json
```

Forecasts now include `open_source_signals` with sanitized record counts,
source-type counts, source failures, snapshot paths, and hashes. Evidence
bundles render the same basis in the `Open Source Basis` section and collapse
duplicate source IDs, repeated failure rows, and repeated snapshot/manifest
paths before they reach buyer-facing summaries.

## Safety Boundary

The expanded collectors do not retain raw advisory bodies, descriptions,
procedure text, code examples, relationship bodies, version event ranges,
credential material, target lists, or exploit material. Large source files are
parsed in memory and reduced to the common sanitized JSONL contract before they
can feed forecasts or evidence bundles.

## Primary Sources

- https://github.com/CVEProject/cvelistV5
- https://github.com/cisagov/vulnrichment
- https://api.osv.dev
- https://access.redhat.com/hydra/rest/securitydata/cve.json
- https://github.com/mitre-attack/attack-stix-data
- https://cwe.mitre.org/data/downloads
- https://capec.mitre.org/data/downloads
- https://d3fend.mitre.org/resources/ontology/
