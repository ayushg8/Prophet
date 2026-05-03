import { useEffect, useState } from 'react';
import { PerlinHero } from './PerlinHero';
import './landing.css';

type Props = {
  onEnter: () => void;
};

export function Landing({ onEnter }: Props) {
  const [clock, setClock] = useState(() => new Date());
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const handleEnter = () => {
    if (exiting) return;
    setExiting(true);
    window.setTimeout(onEnter, 500);
  };

  const zulu = clock
    .toISOString()
    .slice(11, 19)
    .concat('Z');

  return (
    <div className={`landing${exiting ? ' landing--exiting' : ''}`}>
      <PerlinHero className="landing__mesh" />
      <div className="landing__dither" aria-hidden />
      <div className="landing__vignette" aria-hidden />
      <div className="landing__scanlines" aria-hidden />

      <div className="landing__topbar">
        <span className="landing__classification">UNCLASSIFIED // FOUO</span>
        <span className="landing__topbar-spacer" />
        <span className="landing__clock">{zulu}</span>
      </div>

      <div className="landing__sidebar landing__sidebar--left">
        <span>CISA · KEV FEED · LIVE</span>
        <span>NVD CVE 2.0 · STREAMING</span>
        <span>EPSS v4 · BASELINE</span>
      </div>

      <div className="landing__sidebar landing__sidebar--right">
        <span>ANTHROPIC API · ONLINE</span>
        <span>CVP · AUTHORIZED</span>
        <span>SANDBOX · ISOLATED</span>
      </div>

      <main className="landing__hero">
        <div className="landing__eyebrow">PROJECT // PROPHET</div>
        <h1 className="landing__title">PROPHET</h1>
        <div className="landing__divider" />
        <div className="landing__tagline">
          PREDICT &nbsp;·&nbsp; EXPLOIT &nbsp;·&nbsp; DEFEND
        </div>
        <p className="landing__lede">
          A Claude-orchestrated agent loop that grounds on the CISA KEV catalog
          to forecast the next class of weaponized vulnerability, validates the
          exploit in an isolated sandbox, and co-generates the patch in the
          same run.
        </p>

        <button
          type="button"
          className="landing__cta"
          onClick={handleEnter}
          aria-label="Enter the operator console"
        >
          <span className="landing__cta-bracket">[</span>
          <span className="landing__cta-label">ENTER OPERATOR CONSOLE</span>
          <span className="landing__cta-bracket">]</span>
        </button>

        <div className="landing__meta">
          <span>NATSEC HACKATHON</span>
          <span className="landing__meta-dot">·</span>
          <span>SHACK15 · SF</span>
          <span className="landing__meta-dot">·</span>
          <span>03 MAY 2026</span>
        </div>
      </main>

      <footer className="landing__footer">
        <span>v0.1.0-alpha</span>
        <span className="landing__footer-sep">|</span>
        <span>SESSION ID: {clock.getTime().toString(16).slice(-8).toUpperCase()}</span>
        <span className="landing__footer-sep">|</span>
        <span>FRAME RATE: 60Hz</span>
      </footer>
    </div>
  );
}
