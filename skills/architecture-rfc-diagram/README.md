# /architecture-rfc-diagram

Read a project's source code and produce a single-file architecture RFC HTML page with Mermaid diagrams in a black-and-white staff-engineering style.

## Installation

```bash
git clone https://github.com/UnicodeDigital/claude-skills.git /tmp/claude-skills
mkdir -p ~/.claude/skills
cp -r /tmp/claude-skills/skills/architecture-rfc-diagram ~/.claude/skills/
rm -rf /tmp/claude-skills
```

无需重启 Claude Code，下次提到"画架构图 / 分析这个 repo 的架构"时会自动触发；也可以显式调用 `/architecture-rfc-diagram <repo-path>`。

## Features

- **Evidence-first workflow** — every node and edge must trace back to a file, symbol, or config; anything inferred is explicitly flagged.
- **Five-class Mermaid vocabulary** — `base` / `tool` / `opt` / `bus` / `risk` keeps diagrams stylistically consistent.
- **Built-in review loop** — Phase 6 forces Claude to flag high-risk claims (deps, routing, state truth, concurrency, reconnect) for the user to verify before declaring done.
- **Honest absence framing** — for things the framework doesn't do, the tradeoff section frames it as "abstraction is hard / pattern hasn't sedimented", not as smug "we chose not to".
- **Single-file HTML output** — inline CSS, Mermaid via CDN, opens in any browser.
- **Honest about unknowns** — dashed borders, `inferred` markers, `needs owner confirmation` rows.

## Usage

In Claude Code, point Claude at a repo and ask for an architecture page. Triggering phrases:

```
帮我画一下这个项目的架构图
analyze this repo and produce an architecture RFC
read /path/to/repo and generate an architecture diagram
```

The skill triggers automatically when the request matches; you don't need to invoke it explicitly.

## Output

A single `architecture-rfc.html` file. Section letters A-F are **positions, not topics** — Claude picks the actual subjects based on what the system needs:

- **Masthead + Lede** — title / metadata / one-paragraph central architectural move
- **A · TOPOLOGY** (flowchart LR) — runtime units, external systems, buses
- **B · INTERFACE / MODULES** (flowchart TB) — internal layering, adapter boundaries
- **C · SEQUENCE** (sequenceDiagram) — happy path of a representative flow
- **D / E / F** — chosen from: state-truth matrix · disconnect choreography · SLA / owner matrix · tradeoffs. Real-time / trading systems often get state-truth + disconnect-sequence + tradeoffs; web APIs get SLA matrix + tradeoffs; libraries skip the dynamic diagrams.

The skill's `SKILL.md` Phase 3 has a table of typical section combos per system type.

## Files

- `SKILL.md` — workflow Claude follows
- `assets/template.html` — the canonical visual reference (CSS + Mermaid theme + section structure)
- `references/repo-scan-checklist.md` — comprehensive file/grep patterns for code archaeology
- `references/style-guide.md` — Mermaid `classDef` conventions, writing style, anti-patterns
