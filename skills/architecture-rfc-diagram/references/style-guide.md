# Style Guide — Architecture RFC Diagrams

This is what makes the output recognizable. Don't deviate without a reason.

## Visual identity

The CSS is already baked into `assets/template.html`. The variables to know:

| Variable     | Value      | Used for                                        |
|--------------|------------|-------------------------------------------------|
| `--ink`      | `#111`     | Body text, borders, foundation nodes (filled)   |
| `--ink-2`    | `#333`     | Secondary text (notes, lede)                    |
| `--ink-3`    | `#666`     | Tertiary text (eyebrow, meta, sub-labels)       |
| `--paper`    | `#fafaf7`  | Page background (warm off-white)                |
| `--paper-2`  | `#f1efe8`  | Inline code background                          |
| `--accent`   | `#c93a2a`  | **Risk / canary / critical-path only**          |
| `--green`    | `#2a7a3a`  | Success markers in matrix tables (✓)            |

The 32px grid background, the masthead with top/bottom rules, the eyebrow → H1 hierarchy, the lede with the left rule — all of these are signature. Keep them.

Fonts: Inter (body), Noto Sans SC (CJK fallback), JetBrains Mono (everything that should "feel like code": tags, sub-labels, eyebrow, meta, code spans, edge labels, axis ticks).

## Mermaid `classDef` vocabulary

Use this five-class palette for flowcharts. Defining all five at the top of each diagram is fine even if not all are used — it keeps diagrams stylistically consistent across the document.

```mermaid
classDef base fill:#111,stroke:#111,color:#fff,stroke-width:2px;
classDef tool fill:#fff,stroke:#111,color:#111;
classDef opt  fill:#fff,stroke:#444,stroke-dasharray:5 4,color:#111;
classDef bus  fill:#f4f2eb,stroke:#111,stroke-dasharray:2 2,color:#111;
classDef risk fill:#fff,stroke:#c93a2a,color:#111,stroke-width:2px;
```

Mapping:

- **`base`** (black fill, white text) — the core/foundation. The thing the document is centrally about. Use sparingly: 1–3 nodes per diagram max.
- **`tool`** (white fill, black border) — regular runtime units, services, modules. The default.
- **`opt`** (dashed border) — optional, replaceable, or hot-swappable units. Things you can run with/without. Also useful for "this might exist depending on config."
- **`bus`** (warm gray fill, dashed border) — queues, streams, topics, shared files, caches used as channels, message buses. Always a *channel*, never an endpoint.
- **`risk`** (red border) — canary, critical path, single point of failure, security boundary, anything the reader should pay attention to.

Apply with `:::class` after the node ID:

```mermaid
CC["<b>Claude Code</b><br/>interactive agent"]:::base
FS["filesystem MCP<br/>read files · tree · grep"]:::tool
DOC["docs / README / ADR<br/>optional evidence"]:::opt
CACHE[("evidence index<br/>symbols · modules · flows")]:::bus
HTML["<b>single-file HTML RFC</b><br/>black-white line-art style"]:::risk
```

Note the `[(...)]` cylinder shape for `bus`-style nodes that are storage/queues — visually distinguishing them from regular boxes helps.

## Edge conventions

- Use `==>` for the "happy path" / main flow (thick arrow).
- Use `-->` for normal flow.
- Use `-. label .->` (dotted with label) for optional/conditional paths.
- **Always label channels** with what flows on them: `"HTTP /v1/quote"`, `"kafka: orders.v2"`, `"unix socket"`, `"source facts"`. Untyped edges are a smell.

## Subgraphs

Group nodes into subgraphs (`subgraph L1["L1 · CONTEXT SOURCES"] ... end`) to express logical tiers. Use the pattern `<short-id> · <UPPERCASE NAME>` so the cluster labels render as small caps in the JetBrains Mono style. The template's `.mermaid .cluster` CSS rule handles the styling — you just need to follow the naming convention.

## Sequence diagrams

- Use `autonumber` for steps you want to refer back to in notes.
- Use `Note over X,Y: ...` for invariants or contracts that span actors.
- Keep messages terse: `"list tree + read build/config/entrypoints"` is better than a full sentence.

## Writing style

- **Terse and concrete.** Engineering nouns: process, stream, topic, adapter, repository, cache, owner, restart path, schema, rollout, fault domain. Avoid generic words like "system", "component", "module" if you can be more specific.
- **Notes explain *why*, not what.** The diagram already shows the *what*. A good note is "all architecture conclusions must carry evidence; nodes without evidence are marked `inferred`." A bad note is "this diagram shows the topology."
- **Mark uncertainty explicitly.** Phrases that signal honesty: "inferred from config", "not found in repo", "needs owner confirmation", "assumes default Kubernetes deployment".
- **Lede in one paragraph.** Stake the central architectural move in 2–3 sentences. The reader should be able to skip the rest and still know what's going on.

## Matrix table

Use it for one of: fault domains, ownership, risk register, rollout phases. Don't use it for things a list would do.

Typical columns:

| 进程/Module | Impact when down | Recovery | Owner | Observability |
|-------------|------------------|----------|-------|---------------|

The template has `td.ok` (✓ green) and `td.no` (✗ red) helpers — use them for binary columns like "self-healing?".

## Tradeoffs section

Three to five entries, each a single sentence answering "why this design and not the obvious alternative?". They render as `01`, `02`, `03` in monospace boxes. If you can't articulate the alternative being rejected, the tradeoff probably isn't real.

**Honest absence framing.** When a tradeoff covers something the framework deliberately doesn't do (no risk gate, no auto-reconcile, no observability layer), don't frame it as "we chose not to" — that reads as smug and overconfident. Frame it as the actual reason it isn't there yet:

- ✓ "X is not in the framework layer because the abstraction is hard — strategies want very different X policies, and the common pattern hasn't sedimented yet. Will revisit when 2-3 production callers converge on a shape."
- ✗ "We deliberately omit X to keep the framework lean." (Too smug, and usually wrong — most "deliberate omissions" are actually "haven't gotten around to it" or "designing it well is hard".)

The honest version invites the reader into the real decision space; the smug version closes the conversation.

## Anti-patterns

- Rainbow colors. The palette is monochrome plus red. That's it.
- "System X" boxes containing five sub-boxes containing fifteen more boxes. Aggregate or split into another diagram.
- Edges without labels.
- Putting class names or file paths as the *only* identifier of a node. Use a human-readable name + an annotation: `Order Service<br/><i>order_service/main.go</i>`.
- Inventing performance numbers, SLAs, or org-chart facts.
