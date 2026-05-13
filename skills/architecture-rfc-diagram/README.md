# /architecture-rfc-diagram

Read a project's source code and produce a single-file architecture RFC HTML page with Mermaid diagrams in a black-and-white staff-engineering style.

## Features

- **Evidence-first workflow** — every node and edge must trace back to a file, symbol, or config; anything inferred is explicitly flagged.
- **Five-class Mermaid vocabulary** — `base` / `tool` / `opt` / `bus` / `risk` keeps diagrams stylistically consistent.
- **Three diagrams by default**: Topology (flowchart LR) + Interface (flowchart TB) + Sequence.
- **Matrix + tradeoffs section** for fault domains, ownership, and "why this design".
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

A single `architecture-rfc.html` file with these sections:

- **Masthead** — title, eyebrow, owner/status metadata
- **Lede** — one paragraph on the central architectural move
- **A · TOPOLOGY** — runtime units, external systems, buses
- **B · INTERFACE / MODULES** — internal layering, adapter boundaries
- **C · SEQUENCE** — one representative flow (request, startup, or rollout)
- **D · MATRIX** — fault domains, ownership, or risks
- **E · TRADEOFFS** — 3–5 design decisions and their alternatives

## Files

- `SKILL.md` — workflow Claude follows
- `assets/template.html` — the canonical visual reference (CSS + Mermaid theme + section structure)
- `references/repo-scan-checklist.md` — comprehensive file/grep patterns for code archaeology
- `references/style-guide.md` — Mermaid `classDef` conventions, writing style, anti-patterns
