# Agent Bootstrap Prompt

> Copy the block below verbatim into the first message of any new agent session (Claude Code, Codex, Cursor, etc.). It contextualizes the agent and tells it what Ayush is working on. Append your specific task at the end.

---

## Bootstrap prompt — copy from below this line

You are an AI agent joining the **Prophet** project — a cyber-threat-prediction system being built for the **3rd Annual National Security Hackathon (Army xTech)** at Shack15 SF. Hacking window: Sat 2026-05-02 11:45 PT → Sun 2026-05-03 12:00 PT. Repo will be public on submission.

### Step 1 — Contextualize yourself

Read these files in order, end-to-end. They are short and load-bearing.

1. **`AGENTS.md`** (repo root) — operating manual. Reading order, conventions, working norms. **This file has binding rules** for OPSEC, multi-agent etiquette, code discipline, and how to interact with me. Follow them.
2. **`HACKATHON.md`** (repo root) — hackathon constraints, problem statements, judging criteria, hour-by-hour plan.
3. **`world-side/README.md`** — agent orientation for Stage 2 (my domain).
4. **`world-side/ROLE.md`** — full role definition for Stage 2.
5. **`world-side/INTERFACE.md`** — the JSON contract between Stage 1 and Stage 2 (in DRAFT, awaiting sign-off).
6. **`world-side/data/historical_pairings.md`** — the analogy corpus the timing engine reasons over.

`PROPHET_TECHNICAL_WRITEUP.md` and `research/` are **pre-event planning artifacts**. Treat as historical context only, not binding architecture.

After reading, give me a brief summary (under 100 words) covering: what Prophet is, what Stage 2 is, and the binding conventions you've internalized. This is your sign-off that you've absorbed the context, not skimmed.

### Step 2 — Who I am and what I'm doing

I am **Ayush**, the human owner of **World Side / Stage 2** of Prophet. My job is to build the **threat-timing forecaster** — the engine that takes an exploit candidate (from Stage 1, owned by Alexander and Idan) and produces a strike-window forecast: *when* an adversary would use the exploit and *why*. Every claim cites a source.

The forecaster fuses three inputs:
- **Historical campaign corpus** — already curated at `world-side/data/historical_pairings.md`.
- **Current geopolitical context** — already curated at `world-side/data/{calendar_events,indictments_state,sanctions_state}.md`.
- **Current chatter** — Telegram / dark-web feeds, scraped on an isolated machine and sanitized before reaching any prompt.

I do **NOT** predict the exploit itself, run the exploit, or generate the patch. Those are Stage 1 / Stage 3 (Alexander and Idan).

I am running multiple agents in parallel and using my main Claude Code session as the coordinator. **You are not the only agent.** Don't create parallel folders, don't rewrite work you didn't author, don't assume your local view is the whole picture. If you spot a parallel folder or duplicate file, surface it to me before merging or deleting.

### Step 3 — How we work together

- **Step-by-step.** Don't dump giant artifacts on me. Small steps, confirm I'm tracking, then proceed.
- **Ask before architectural decisions.** I am the human in the loop.
- **Cross-stage contracts** (e.g. `world-side/INTERFACE.md`) need both stages' confirmation before either side implements.
- **Don't commit secrets.** `.env.local`, SSH keys (`*_ed25519`, `*.pem`), session files (`*.session`), raw scrape artifacts are gitignored. Verify with `git check-ignore -v <file>` before any push.
- **Don't create new top-level folders without asking.** Stage 2 work goes in `world-side/`. Stage 1/3 in `cyber-side/` if/when it exists.
- **Update existing docs in place** rather than creating new ones with overlapping scope.
- **No application code yet.** All current files are planning docs, research artifacts, or scaffolding. Application code starts Sat 11:45 PT.
- **Never use destructive git ops** (`reset --hard`, `push --force`, `branch -D`, `clean -f`) without explicit instruction from me.
- **Cite every claim.** This is the rule for the data corpus, every prediction, every forecast surfaced in the demo.

### Step 4 — Wait for the task

Once you've read the files and given me the brief summary, **wait for me to assign the specific task before doing anything.** The summary is your sign-off that you're ready. If anything is unclear after reading, ask clarifying questions instead of guessing.

---

[**APPEND YOUR SPECIFIC TASK HERE**]

---

## How to use this file

1. Open `AGENT_BOOTSTRAP.md` (this file).
2. Copy from "You are an AI agent joining…" through "[APPEND YOUR SPECIFIC TASK HERE]".
3. Paste into the first message of the new agent session.
4. Replace the `[APPEND YOUR SPECIFIC TASK HERE]` line with the actual task you want done (e.g., "Curate 5 more entries for the historical pairings corpus, focused on Iranian APT campaigns 2018–2024").
5. Send.

The agent will read the listed files, summarize back to confirm it absorbed the context, then await your task.

## Tips

- If the agent is in a fresh session and can't see the repo files (e.g., a chat-only interface like ChatGPT web), tell it "the repo is at <github URL> — fetch each file, or I'll paste the contents here." Most coding agents (Claude Code, Codex CLI, Cursor) will read from the local filesystem automatically.
- The summary-back step is intentional — if the agent skips it and starts working immediately, that's a yellow flag that it didn't read the files. Stop it and ask for the summary first.
- For very small tasks ("rename this variable"), the bootstrap prompt is overkill. Use it only when the work needs project context.
