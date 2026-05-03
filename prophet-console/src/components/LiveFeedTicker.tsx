// LiveFeedTicker: thin horizontal ticker at the bottom of the console.
// Scrolls ~30 realistic Windows-event-log / sandbox-feed entries.
// Marquee scroll at ~40px/s. Sanitized — no real IPs or credentials.

import { useEffect, useRef } from 'react';

// Amber tick mark prefix per entry
const TICK = '▸';

const ENTRIES: string[] = [
  `[LAB-HOST] Service spawned · w3wp.exe · PID 4828 · token: LOCAL_SYSTEM`,
  `[KEV] CVE-2021-44228 · Apache Log4j2 · rank #4 · entry rank +0`,
  `[Sandbox] iptables egress block · OK`,
  `[Qwen] response.ok=true · 0.34s · 412 tokens`,
  `[Nuclei] template loaded · http/cves/2021/CVE-2021-44228.yaml`,
  `[EPSS] CVE-2021-44228 score 0.97 · percentile 0.999`,
  `[LAB-HOST] VulnerableApp.java started · port 8080 · LocalSystem context`,
  `[NVD] CVE-2021-44228 · CVSS 10.0 · AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H`,
  `[Prophet] Phase I INTEL · fetch_kev() · 3,612 entries · OK`,
  `[LAB-HOST] Log4j 2.14.0 detected · ClassPath verified · VULNERABLE`,
  `[Qwen] SSH session established · [LAB-HOST] · cmd.exe context`,
  `[Prophet] score_epss() · CVE-2021-44228 · 0.97454 · p99.9`,
  `[Sandbox] network isolation enforced · no egress routes active`,
  `[Nuclei] JNDI callback received · out-of-band DNS · [critical]`,
  `[LAB-HOST] logger.info() received crafted User-Agent · JNDI lookup fired`,
  `[Prophet] Phase III EXECUTE · run_nuclei() · 2.84s · VULNERABLE`,
  `[CVP] Anthropic Cyber Verification Program · authorization: ACTIVE`,
  `[KEV] 3,612 total entries · last updated 2026-05-02T00:00:00Z`,
  `[Qwen] model=qwen/qwen3.5-35b-a3b · temperature=0.2 · max_tokens=512`,
  `[Prophet] apply_patch() · -Dlog4j2.formatMsgNoLookups=true · applied`,
  `[LAB-HOST] Service restarted · VulnerableApp · Log4j 2.14.0 + patch`,
  `[Nuclei] verify_blocked() · no callback received · NOT VULNERABLE · OK`,
  `[Sigma] rule generated · status: stable · level: critical · 4 fields`,
  `[Prophet] Phase IV DEFEND · patch validated · block confirmed`,
  `[LAB-HOST] exploit_proof.txt · C:\\lab · filesystem evidence · sandbox only`,
  `[NVD] CWE-917 · Improper Neutralization of Special Elements in Logs`,
  `[Prophet] emit_maven_fusion_object() · run_id: PRO-20260502-001 · SHA256: a3f9…c142`,
  `[ExploitDB] EDB-51183 · EDB-51214 · Log4Shell · 2 entries · java · webapps`,
  `[ATT&CK] T1190 · Exploit Public-Facing Application · confirmed`,
  `[Prophet] DEFEND complete · Sigma rule deployed · audit record signed`,
];

// Duplicate entries to ensure seamless looping
const TICKER_TEXT = [...ENTRIES, ...ENTRIES];

export function LiveFeedTicker() {
  const innerRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef<number>(0);
  const posRef = useRef(0);

  useEffect(() => {
    const el = innerRef.current;
    if (!el) return;

    // Measure total scrollable width after a brief settle
    const raf = requestAnimationFrame(() => {
      const totalWidth = el.scrollWidth / 2; // half because we doubled entries
      const SPEED = 40; // px/s
      let lastTs: number | null = null;

      const tick = (ts: number) => {
        if (lastTs === null) lastTs = ts;
        const dt = (ts - lastTs) / 1000;
        lastTs = ts;

        posRef.current += SPEED * dt;
        if (posRef.current >= totalWidth) {
          posRef.current -= totalWidth;
        }

        el.style.transform = `translateX(-${posRef.current}px)`;
        rafRef.current = requestAnimationFrame(tick);
      };

      rafRef.current = requestAnimationFrame(tick);
    });

    return () => {
      cancelAnimationFrame(raf);
      cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return (
    <div className="live-ticker" aria-label="Live feed" aria-hidden="true">
      <div className="live-ticker-inner" ref={innerRef}>
        {TICKER_TEXT.map((entry, i) => (
          <span key={i} className="live-ticker-entry">
            <span className="live-ticker-tick" aria-hidden>{TICK}</span>
            {entry}
          </span>
        ))}
      </div>
    </div>
  );
}
