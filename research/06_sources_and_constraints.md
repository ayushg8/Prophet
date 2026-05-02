# Sources and Constraints

This note captures the external facts that materially shaped the research recommendations.

## Current Repo State

- The current workspace contains a frontend shell at [/Users/macintosh/Documents/hackathon_0526/vantage-console](/Users/macintosh/Documents/hackathon_0526/vantage-console).
- The app already expresses the core demo shape: alert queue, operational canvas, agent stack, evidence panel, and human approval controls in [App.tsx](/Users/macintosh/Documents/hackathon_0526/vantage-console/src/App.tsx:1).

## Dependency Constraints

- OpenSky's FAQ says the REST API is provided "as is" and that rate limits currently apply to `/states/all`, `/flights/*`, and `/tracks/all`.
- OpenSky also notes that access policies may change as needed to protect system performance.
- OpenSanctions exposes separate status components for its APIs and data pipeline, which supports using it as prefetched enrichment rather than a live on-stage dependency.
- The OpenAI Agents SDK is positioned for code-first orchestration, tool execution, approvals, and state, which makes it a good future-fit architecture even if V1 keeps the runtime staged.
- FreeTAKServer exists as an open source TAK-compatible server, but it should remain a stretch integration because it does not improve the core judging path unless the main demo is already stable.

## Why Replay-First Won

- Public API rate limits and availability variance increase demo risk without materially improving the one-minute judging arc.
- The current repo is already strong enough to support a deterministic console demo without requiring backend maturity first.
- A replay-first path lets the team make honest claims about analyst workflow, human review, and evidence handling while avoiding brittle promises about live multi-domain fusion.

## Source Links

- [OpenSky FAQ](https://opensky-network.org/about/faq)
- [OpenSanctions status](https://status.opensanctions.org/)
- [OpenAI Agents SDK guide](https://developers.openai.com/api/docs/guides/agents)
- [FreeTAKServer](https://github.com/FreeTAKTeam/FreeTakServer)
