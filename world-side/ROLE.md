# World Side — Threat-Timing Forecaster

> Codename: **World Side** (mine). Counterpart: **Cyber Side** (Alexander + Idan).
> Owner: Ayush. Drafted 2026-05-02 from a working conversation with Alexander, before the hackathon clock starts. This is just the role definition — not a plan yet, not a schema yet.

## One line

**Cyber Side** predicts *what* the adversary will exploit. **World Side** predicts *when* they will use it and *why*.

## The split

**Cyber Side — "the what."** Alexander + Idan.
They identify the next likely zero-day or vulnerability and run the loop that proves a defense works. Their output is a specific exploit candidate: a CVE class or a concrete CVE plus a validated patch and detection rule.

**World Side — "the when and the why."** Me.
They hand me the exploit candidate. I figure out the moment when an adversary would actually use it, and the strategic reason they'd choose that moment.

The premise we're building on: exploits are *strategic*. Nobody burns a zero-day randomly. There is a window when the value is highest — geopolitical pressure, operational tempo, an upcoming event the attacker wants to influence. Find the window, you blunt the strike.

## What I read

Two streams, in parallel:

1. **Chatter.** Telegram channels, dark-web forums, Tor leak sites — the places threat actors actually communicate. Not mainstream news.
2. **Geopolitical context.** Sanctions, military escalations, indictments, election cycles, sentencing rulings, corporate actions — the open-source signal that creates motive.

The fusion of the two is the value. Either alone is noise.

## The deliverable

For each exploit candidate Cyber Side hands me, I produce one forecast that answers three questions and shows its work:

1. **Why this exploit?** — what makes this specific exploit valuable to the adversary right now.
2. **Why now?** — what time-sensitive geopolitical pressure puts the value at peak in this window.
3. **What's the window?** — a concrete date range with a confidence level.

Every claim cites a source: a news event, a sanctions action, a historical campaign that rhymes, a piece of chatter. No claim without provenance.

Alerts and defense recommendations are *what someone does* with the forecast — they aren't separate deliverables. The forecast itself is the thing.

## What the engine combines to produce the forecast

- **Historical corpus** — past geopolitical trends paired with past zero-day usage. The analogy anchor: "when X happened before, actor Y used a Z-class exploit within N days."
- **Current geopolitical context** — what's happening right now that mirrors a past pattern. Time-sensitive open-source signal.
- **Current chatter** — what adversaries are actively talking about (Telegram channels, dark-web sources).

The historical corpus is the bedrock. Chatter and current geopolitics tell us which historical pattern is rhyming right now.

## What I do *not* do

- I do not predict the exploit itself. That's Cyber Side.
- I do not run the exploit or generate the patch. Cyber Side again.
- I do not claim live attribution of named threat actors with high confidence. I work in classes ("Sandworm-class," "APT29-class") grounded in cited historical patterns.

## Open questions to resolve before building

- How much chatter scraping is realistic in the hackathon window? (Telegram public channels: doable. Dark web live: risky in 24h. Probably need to curate a historical chatter dataset alongside any live feed.)
- What does Cyber Side's exploit-candidate handoff look like as a data shape? Need to lock this with Alexander to mock it and unblock my development.
- Where does Palantir AIP fit — as the surface for the forecasts, the storage for the historical chatter corpus, or both?
- How do my outputs merge with Cyber Side's validated defense into the final alert?

These get answered in the next steps. This file is just the role.
