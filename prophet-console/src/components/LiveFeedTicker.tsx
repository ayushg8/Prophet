// LiveFeedTicker: thin horizontal ticker at the bottom of the console.
// Scrolls sanitized demo/control-plane entries only: no real IPs, credentials,
// payload strings, or live-target indicators.

import { useEffect, useRef } from 'react';

// Amber tick mark prefix per entry
const TICK = '▸';

const ENTRIES: string[] = [
  `[Console] operator console ready · deterministic demo mode`,
  `[KEV] CVE-2021-44228 · Apache Log4j2 · rank #4 · entry rank +0`,
  `[Control] demo-refresh endpoint · world_forecast.v0.1`,
  `[Sandbox] localhost-only validation scope · OK`,
  `[Codex] terminal workflow ready · operator-in-the-loop`,
  `[Validation] public template metadata loaded · fixture-safe`,
  `[EPSS] CVE-2021-44228 score 0.97 · percentile 0.999`,
  `[Fixture] vulnerable-by-design sandbox profile loaded · no live target`,
  `[NVD] CVE-2021-44228 · CVSS 10.0 · AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H`,
  `[Prophet] Forecaster · fetch_kev() · sanitized records · OK`,
  `[Fixture] Log4j sandbox dependency profile · VULNERABLE before patch`,
  `[Control] scraper VM run gate · requires SSH key auth`,
  `[Prophet] score_epss() · CVE-2021-44228 · 0.97454 · p99.9`,
  `[Sandbox] network isolation enforced · no raw scrape content`,
  `[Validation] pre-patch fixture result · VULNERABLE`,
  `[Validation] post-patch fixture result · NOT VULNERABLE`,
  `[Cyber] Direction C artifact loaded · post_patch_status=blocked`,
  `[Prophet] Validate phase · fixture result rendered`,
  `[Guardrail] no payloads · no credentials · no live indicators`,
  `[KEV] 3,612 total entries · last updated 2026-05-02T00:00:00Z`,
  `[Codex] model path · terminal/agent-in-loop · no API key required`,
  `[Prophet] patch primitive rendered · defense artifact applied in fixture`,
  `[Fixture] sandbox service restarted · defensive config active`,
  `[Validation] verify_blocked() · NOT VULNERABLE · OK`,
  `[Sigma] rule generated · status: stable · level: critical · 4 fields`,
  `[Prophet] Defence phase · patch validated · block confirmed`,
  `[Audit] fixture run signed · raw artifacts remain local`,
  `[NVD] CWE-917 · Improper Neutralization of Special Elements in Logs`,
  `[Prophet] emit_artifact() · run_id: PRO-20260502-001 · SHA256: a3f9…c142`,
  `[Public index] Log4Shell references counted · raw entries not loaded`,
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
