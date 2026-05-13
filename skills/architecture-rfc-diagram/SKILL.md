---
name: architecture-rfc-diagram
description: Reads a repository's source code and produces a polished, single-file architecture RFC HTML page with Mermaid diagrams in a black-and-white staff-engineering style. Use this whenever the user wants to "understand a new project's architecture", "draw the architecture", "generate an architecture diagram from code", "produce an architecture RFC", or "map modules/services/data flows" — even if they don't explicitly say "diagram" or "RFC". Also use when the user references this skill's visual style (monochrome line-art HTML with Mermaid topology/interface/sequence diagrams).
disable-model-invocation: false
argument-hint: "[path-to-repo]"
allowed-tools: Read Glob Grep Bash Write
---

# Architecture RFC Diagram

Turn an unfamiliar codebase into a polished, single-file HTML architecture RFC. The output is opinionated: monochrome line-art, Mermaid diagrams (topology + interface + sequence), evidence-backed nodes, and explicit `inferred` markers for anything you couldn't verify.

## Why this exists

Most "LLM, draw the architecture" results are pretty pictures that don't match reality. This skill's contract is the opposite: **every node and edge must be traceable to a file, symbol, or config**, and anything that can't be is flagged so the reviewer knows where to dig.

## Workflow

Do these phases in order. Don't skip ahead to drawing.

### Phase 1 — Repo census (find the shape before reading details)

The goal here is to identify what kind of project this is, where the entry points live, and what languages/frameworks are involved. Don't try to understand the logic yet.

Read in this order — earlier files are more authoritative than directory names:

1. **Build/manifest files** — `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `CMakeLists.txt`, `BUILD`, `Makefile`. They tell you the language, dependencies, and what gets built.
2. **Top-level README** and anything in `docs/`, `adr/`, `design/`, `architecture/`. Skim, don't deep-read.
3. **Entry points** — `main.*`, `index.*`, `cmd/`, `bin/`, `app.*`, `server.*`, files named after a `main` function in the manifest.
4. **Deployment/runtime configs** — `Dockerfile`, `docker-compose.yml`, `k8s/`, `helm/`, `systemd/`, `*.service`, supervisor configs, cron files.
5. **Routing/wiring files** — anything that registers handlers, routes, subscribers, jobs. Names vary: `routes.*`, `router.*`, `wire.*`, `registry.*`, `*_handler.*`.

Use `Glob` for file discovery and `Read` for content. Use `Grep` with patterns like `class\s+\w+Service`, `@RestController`, `def\s+main`, `fn\s+main`, `addEventListener`, `consume`, `subscribe` to find boundaries.

See `references/repo-scan-checklist.md` for a more exhaustive checklist.

### Phase 2 — Build the evidence ledger

Before drawing anything, write down a flat list of architectural units you found, each with a path and one-line role. Keep this in your working memory (or a scratch file if useful).

Capture, for each unit:

- **Type**: process, service, daemon, library, CLI, lambda, web handler, worker, scheduled job.
- **Path**: file or directory.
- **Talks to**: other units, by name. Annotate the channel: HTTP, gRPC, queue topic, DB table, file, shared memory, stdin/stdout.
- **State it owns**: DB tables, caches, files, in-memory state.
- **Confidence**: did you actually read code confirming this, or are you inferring from naming/structure? Mark inferences clearly.

This ledger is the single source of truth for the diagrams. If you can't add a node to a diagram from the ledger, you can't add it.

### Phase 3 — Pick diagrams

Default to three diagrams. Don't try to cram everything into one. Per-diagram rules of thumb:

- **Topology** (`flowchart LR`) — runtime units, external systems, buses/queues/DBs between them. Goal: "what processes exist and how do they talk."
- **Interface / Modules** (`flowchart TB`) — internal layering, adapter/repository/client boundaries, prod-vs-sim/test implementations. Goal: "how is the code organized inside one unit."
- **Sequence** (`sequenceDiagram`) — one representative flow: a typical request, startup, or a rollout/failure path. Goal: "what happens over time."

Aim for **6–14 nodes per diagram**. If you have more, split or aggregate. If you have fewer, you're probably not yet looking hard enough.

### Phase 4 — Render the HTML

The skill ships with the visual template at `assets/template.html`. You should produce a new HTML file that:

1. **Uses the same CSS, fonts, and Mermaid theme** as `assets/template.html`. The easiest path: read `assets/template.html`, copy its `<style>` block, `<script>` tags, and `mermaid.initialize({...})` call verbatim. Don't redesign — the visual identity is the point.
2. **Replaces the example content** (the "Claude Code — Repo Architecture Diagram Skill" demo content in the template) with content driven by the evidence ledger.
3. **Keeps the section structure**: masthead + lede + section blocks A/B/C + matrix D + tradeoffs E + footer. Drop sections if you have nothing real to put there — don't pad.

Follow `references/style-guide.md` for visual conventions (which Mermaid `classDef` to use for which kind of node, when to use the red accent, etc.).

When writing the output file, default to writing it next to the analyzed repo as `architecture-rfc.html` unless the user asks otherwise.

### Phase 5 — Mark what you don't know

This is the most important step. For any node, edge, or claim that you couldn't verify from code:

- Add it to the diagram with a dashed border or a `?` suffix on the label.
- Add a note like `inferred from directory name` or `not found in repo — needs owner confirmation` to the section's notes list.
- For unknown ownership, fault domains, latency, or rollout strategy, include a placeholder row in the matrix table with the value `needs owner` rather than guessing.

It's better for the document to say "I don't know" in a marked way than to draw a confident-looking lie.

## Output rules

- **Single self-contained HTML file.** Inline all CSS. Use the Mermaid CDN script tag from the template; if the user wants offline, they can manually swap to an inlined `mermaid.min.js`.
- **Chinese or English** — match the user's language. If the user wrote in Chinese, write the headings, lede, notes, and tradeoffs in Chinese. Section tags (`A · TOPOLOGY`, `B · INTERFACE`, etc.) can stay in English for visual consistency.
- **Mermaid validity** — every `flowchart` and `sequenceDiagram` block must be syntactically valid. Test by mentally walking node IDs and edge syntax. Common gotchas: HTML in node labels needs `htmlLabels:true` (the template already sets this), `<br/>` for line breaks inside labels, double-quote node text containing special characters.
- **No fabricated metrics.** Don't write "p99: 80ms" or "throughput: 10k QPS" unless you found it in code/configs. Real architecture docs are useful precisely because they don't lie.

## Useful references

- `references/repo-scan-checklist.md` — comprehensive file-pattern checklist for Phase 1.
- `references/style-guide.md` — Mermaid `classDef` conventions and writing-style rules for Phase 4.
- `assets/template.html` — the canonical visual reference. Copy its CSS and Mermaid config verbatim.
