# Prophet Glossary

This glossary defines Prophet terms for evaluators who are not deep cyber
operators. Use these words consistently in buyer reviews and documentation.

| Term | Meaning |
|---|---|
| Asset inventory | A customer-safe list of product families, packages, owners, exposure classes, and known CVE references. The pilot avoids hostnames, IPs, URLs, credentials, and raw target names. |
| Asset/SBOM seedset | Sanitized metadata derived from an asset inventory or SBOM. Prophet uses it to decide which exposure classes matter without importing sensitive environment details. |
| Approval record hash | A SHA-256 hash proving which local operator decision governed a generated artifact. It helps a reviewer connect evidence to the human gate. |
| Audit trail | Hash-chained local records for approvals, denials, sandbox artifact use, and handoff exports. The customer-facing export is redacted and does not embed raw event logs. |
| CISA KEV | The Known Exploited Vulnerabilities catalog from the Cybersecurity and Infrastructure Security Agency. Prophet uses KEV-style context as defensive prioritization evidence, not as a target list. |
| Console | The React web UI in `prophet-console/`. It shows forecast context, policy status, human approval, defense output, evidence, and integration handoff state. |
| CVE | A public vulnerability identifier. In Prophet, a CVE reference helps label exposure classes and evidence, but the pilot does not turn CVEs into live target workflows. |
| Defense artifact | The reviewable defensive output: patch summary, detection summary, validation status, and safety metadata. |
| Evidence bundle | JSON and Markdown files that collect the forecast, asset seed summary, source refs, defense artifact, validation result, policy hash, approval record hash, and artifact hashes. |
| Fixture-backed | Based on checked-in fictional or sanitized fixtures, not live customer systems. This is the default pilot mode. |
| Forecast | Prophet's defensive prioritization record: likely strike window, likely strike vector, confidence, source refs, and rationale. |
| Integration handoff | SIEM and ticketing review templates generated from validated evidence. They are files for customer review, not automatic production deployment. |
| Localhost-only | Runs on the evaluator's machine and talks only to local services such as `127.0.0.1`. It does not contact live targets. |
| Policy | A JSON file that defines allowed modes, approved source IDs, sandbox profiles, blocked controls, retention hints, and allowed handoff exports. |
| Policy hash | A SHA-256 hash of the reviewed policy. Runtime outputs include it so reviewers can detect policy drift. |
| Redaction report | A machine-checkable report showing that sensitive raw values were not copied into customer-facing exports. |
| Sandbox validation | Deterministic local validation that a defensive change blocks the modeled exposure class in a fixture profile. The public pilot does not validate against live infrastructure. |
| Seeded OSINT | Policy-approved public-source fixture context generated from safe seed metadata. The default pilot reads tracked fixtures rather than collecting live web data. |
| SIEM | Security information and event management tooling used by SOC teams to review alerts and detections. Prophet exports review templates for SIEMs. |
| Sigma rule | A detection-rule format that can describe suspicious behavior across multiple security tools. Prophet uses it as part of the defensive handoff. |
| Strike vector | The likely attack method category, such as edge-appliance initial access. Prophet keeps this at defensive class level. |
| Strike window | The time frame when a target class may need extra defensive attention because external pressure and historical patterns line up. |
| Validation failure evidence | Sanitized evidence that a defensive candidate failed or timed out in fixture validation. It helps buyers see unsuccessful outcomes without raw logs. |
| Exposure-class recommendation | Prophet's reviewable recommendation for the defensive class to harden first. It is not a claim that Prophet discovered a new vulnerability. |
| Preemptive defense | A patch, configuration, detection, or response recommendation prepared before pressure peaks, based on public context and approved fixture or metadata evidence. |

## Preferred Language

- Say "fixture-backed pilot" instead of "live demo."
- Say "exposure class" instead of "target."
- Say "defense artifact" instead of "exploit output" when discussing buyer
  evidence.
- Say "exposure-class recommendation" instead of "zero-day prediction."
- Say "integration handoff" instead of "deployment" unless a customer has
  explicitly approved a separate production process.
- Say "policy-blocked" when a control refuses an unsafe or out-of-scope action.
