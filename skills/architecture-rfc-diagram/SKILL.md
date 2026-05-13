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

> ⚠️ **A module's real dependencies live in *its own* manifest, not the root one.** Top-level `CMakeLists.txt` `link_directories` / `include_directories`, monorepo root `BUILD` / `pyproject.toml` workspace deps, or a Go `go.work` often list the *union* across all sub-modules. Any individual module may only use a subset. Before claiming "X depends on Y", check `target_link_libraries` in the module's own CMakeLists, `dependencies` in its own `package.json`, `[dependencies]` in its own `Cargo.toml`, etc. The cost of getting this wrong is high: it produces confident-looking arrows in the topology diagram that are pure fiction. When in doubt, also grep for actual `#include "Y/..."` / `import Y` / `use Y::...` in the module's source.

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

> ⚠️ **Trace request *and* response paths — don't assume push events bypass the request router.** A common failure mode: you see a message-type enum (e.g. `msg.h Event::Type { OrderAck, PositionUpdate, BalanceUpdate, ... }`) and conclude the push types must flow through a different channel than the request types. Often they don't — the same dispatcher / SPSC queue / router is reused for both directions, and only the type discriminator differs. Before drawing "A → B → C" with no return arrow, grep the consumer side: who calls `recv()` on B's response queue? Who calls `processResponse()` on each Executor? Pushes (UserDataStream, server-initiated events) frequently share the request dispatcher's plumbing because that's where vendor↔market routing already exists. Wiring this wrong produces sequence diagrams that omit the actual response path.

### Phase 3 — Pick diagrams and matrices

**Section letters A–F are *positions*, not topics.** Each slot's title should come from what this system actually needs the reader to understand, not from a fixed template. Common building blocks:

- **Topology** (`flowchart LR`) — runtime units, external systems, buses/queues/DBs between them. Answers: "what processes exist and how do they talk."
- **Interface / Modules** (`flowchart TB`) — internal layering, adapter/repository/client boundaries, prod-vs-sim implementations. Answers: "how is the code organized inside one unit."
- **Sequence** (`sequenceDiagram`) — one representative flow: a typical request, startup, or rollout. Answers: "what happens over time on the happy path."
- **Failure / Disconnect sequence** (`sequenceDiagram`) — what the system does when something breaks: reconnect, retry, fail-over, reconcile. Earn-its-place criterion: the system has a characteristic failure mode that the architecture explicitly handles (trading exchange disconnect, message broker rebalance, leader election).
- **State / Truth matrix** (table) — for each kind of state (orders, sessions, cache lines, leader epoch), who is authoritative, what's cached locally, how it's recovered. Earn-its-place: the system has eventual-consistency boundaries the reader must internalize.
- **Tradeoffs** (numbered list) — 3-5 architectural decisions, each with the rejected alternative.

**Pick the combination that matches the system.** Three common patterns:

| System type | Typical A–F |
|---|---|
| Real-time / trading / IoT | A topology · B interface · C happy sequence · D state truth · E disconnect sequence · F tradeoffs |
| Web API / CRUD service | A topology · B interface · C request sequence · D SLA/ownership matrix · E tradeoffs (drop one diagram if simple) |
| Library / SDK | A module layering · B public API surface matrix · C tradeoffs (no live topology, no sequence) |

Aim for **6–14 nodes per diagram**. If you have more, split or aggregate. If you have fewer, you're probably not yet looking hard enough — or this isn't a diagram, it's a sentence.

### Phase 4 — Render the HTML

The skill ships with the visual template at `assets/template.html`. You should produce a new HTML file that:

1. **Uses the same CSS, fonts, and Mermaid theme** as `assets/template.html`. The easiest path: read `assets/template.html`, copy its `<style>` block, `<script>` tags, and `mermaid.initialize({...})` call verbatim. Don't redesign — the visual identity is the point.
2. **Replaces ALL the example content.** The template's example content (lede, A/B/C/D/E topics, matrix headers, tradeoffs) describes the skill itself — it's meta-content, not a template for architecture topics. Inherit only the visual structure: masthead + lede + section blocks + matrix + tradeoffs + footer. Pick the section topics from Phase 3 based on what this system needs, not from the template's titles.
3. **Don't pad sections.** Every block has to earn its place. Red flags that a section is padded:
   - The matrix is a generic "module × {what it owns / what dies if it dies}" table where most rows say "process dies, things downstream stop". This is information-free — delete the block and pick a matrix that's load-bearing for *this* system (state truth / SLA + owner / rollout phases / data lineage).
   - A tradeoff's "rejected alternative" is something nobody would actually propose. Delete it.
   - A sequence diagram that just renders the topology as time-ordered messages. Either it's adding a real time dimension (concurrency, ordering, retries) or it's redundant.

Follow `references/style-guide.md` for visual conventions (which Mermaid `classDef` to use, when to use the red accent, tradeoff writing rules).

When writing the output file, default to writing it next to the analyzed repo as `architecture-rfc.html` unless the user asks otherwise.

### Phase 5 — Mark what you don't know

This is the most important step. For any node, edge, or claim that you couldn't verify from code:

- Add it to the diagram with a dashed border or a `?` suffix on the label.
- Add a note like `inferred from directory name` or `not found in repo — needs owner confirmation` to the section's notes list.
- For unknown ownership, fault domains, latency, or rollout strategy, include a placeholder row in the matrix table with the value `needs owner` rather than guessing.

It's better for the document to say "I don't know" in a marked way than to draw a confident-looking lie.

### Phase 6 — Surface review-worthy claims

Before declaring the document done, **proactively flag the high-risk claims you want the user to verify**. These are the categories that are most often wrong and most consequential when wrong:

1. **Inter-module dependency arrows** — did you actually read the *consuming* module's manifest/imports, or only the top-level build file? (Re-read the Phase 1 warning.)
2. **Request and push routing** — for every "A → B" you drew, do you have evidence for the corresponding "B → A" / "B → C" return path? Pushes especially: did you grep who consumes the response queue?
3. **State ownership / truth source claims** — when you wrote "X is the source of truth", does the code path actually update X first, or is X just a cache that gets reconciled?
4. **Concurrency / thread model** — did you confirm "main thread only" / "this queue is SPSC" by reading the actual handler code, or are you assuming from naming?
5. **Reconnect / retry / recovery behavior** — for anything labeled "automatic", did you find the timer/loop that drives it, or are you inferring from method names like `reconnect()`?

End your handoff message with: "I'd specifically like you to verify these claims: [list 3-5]." This forces the conversation into a verify-before-commit loop and prevents confident hallucinations from surviving review.

## Output rules

- **Single self-contained HTML file.** Inline all CSS. Use the Mermaid CDN script tag from the template; if the user wants offline, they can manually swap to an inlined `mermaid.min.js`.
- **Chinese or English** — match the user's language. If the user wrote in Chinese, write the headings, lede, notes, and tradeoffs in Chinese. Section tags (`A · TOPOLOGY`, `B · INTERFACE`, etc.) can stay in English for visual consistency.
- **Mermaid validity** — every `flowchart` and `sequenceDiagram` block must be syntactically valid. Test by mentally walking node IDs and edge syntax. Common gotchas: HTML in node labels needs `htmlLabels:true` (the template already sets this), `<br/>` for line breaks inside labels, double-quote node text containing special characters.
- **No fabricated metrics.** Don't write "p99: 80ms" or "throughput: 10k QPS" unless you found it in code/configs. Real architecture docs are useful precisely because they don't lie.

## Useful references

- `references/repo-scan-checklist.md` — comprehensive file-pattern checklist for Phase 1.
- `references/style-guide.md` — Mermaid `classDef` conventions and writing-style rules for Phase 4.
- `assets/template.html` — the canonical visual reference. Copy its CSS and Mermaid config verbatim.
