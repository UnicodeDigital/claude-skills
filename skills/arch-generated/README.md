# /arch-generated

Read a project's source code and produce a single-file HTML doc — a hybrid of architecture overview (Mermaid topology + sequence diagrams) and onboarding guide (minimum-viable code sample, config example, callback inventory), in a black-and-white staff-engineering style.

## Installation

```bash
git clone https://github.com/UnicodeDigital/claude-skills.git /tmp/claude-skills
mkdir -p ~/.claude/skills
cp -r /tmp/claude-skills/skills/arch-generated ~/.claude/skills/
rm -rf /tmp/claude-skills
```

无需重启 Claude Code，下次提到"画架构图 / 分析这个 repo 的架构 / 生成 onboarding 文档"时会自动触发；也可以显式调用 `/arch-generated <repo-path>`。

## Features

- **Evidence-first workflow** — every node, edge, and code line must trace back to a file, symbol, or config; anything inferred is explicitly flagged.
- **Architecture + onboarding hybrid** — output combines runtime topology, sequence diagrams, state truth matrix AND a real "from zero to first action" code sample drawn from the repo's actual API.
- **Five-class Mermaid vocabulary** — `base` / `tool` / `opt` / `bus` / `risk` keeps diagrams stylistically consistent.
- **Built-in review loop** — Phase 6 forces Claude to flag high-risk claims (deps, routing, state truth, concurrency, reconnect) for the user to verify before declaring done.
- **Honest absence framing** — for things the framework doesn't do, the boundary section frames it as "abstraction is hard / pattern hasn't sedimented", not as smug "we chose not to".
- **Single-file HTML output** — inline CSS, Mermaid via CDN, opens in any browser.
- **Honest about unknowns** — `inferred` markers, `needs owner confirmation` rows.

## Usage

In Claude Code, point Claude at a repo and ask for an architecture / onboarding doc. Triggering phrases:

```
帮我画一下这个项目的架构图
analyze this repo and produce an architecture + onboarding doc
read /path/to/repo and generate a living architecture document
```

The skill triggers automatically when the request matches; you don't need to invoke it explicitly.

## Output

A single HTML file. Section letters A-E are **positions, not topics** — Claude picks subjects based on system type. The default pattern (for frameworks / SDKs people write code against):

- **Masthead + Lede** — title / metadata / one-paragraph central architectural move
- **A · OVERVIEW** (flowchart LR) — runtime units, external systems, buses
- **B · GETTING STARTED** — 3 numbered onboarding steps · `pre.code` minimum-viable code sample · callback/API inventory matrix · config example
- **C · SEQUENCE** (sequenceDiagram, often 2 diagrams) — happy-path request flow + data-subscription flow
- **D · STATE** — truth source + cache + recovery matrix per state kind
- **E · BOUNDARY** — 框架负责 / 用户负责 + tradeoffs combined

For non-framework systems (web services, libraries, real-time pipelines), the section mix shifts — see `SKILL.md` Phase 3.

## Files

- `SKILL.md` — workflow Claude follows (Phases 1–6)
- `assets/template.html` — canonical visual reference + structural skeleton (CSS, Mermaid theme, section flow)
- `references/repo-scan-checklist.md` — file/grep patterns for code archaeology + anti-patterns
- `references/style-guide.md` — Mermaid `classDef` conventions, writing style, tradeoff rules
