# /setup-statusline

One-command setup for [ccstatusline](https://github.com/sirmalloc/ccstatusline) with team-standard defaults.

## Features

- Three-line layout optimized for 80-column terminals
  - **Line 1**: Model | Effort | Ctx (progress bar)
  - **Line 2**: Session | Usage | Reset
  - **Line 3**: Git Branch | Changes | Ahead/Behind | PR
- Optimized for Team Plan (no cost widget, includes usage reset timer)
- `hideNoGit` on git widgets for clean display in non-git directories
- Custom "Usage:" label via `rawValue` + `custom-text` combo
- Fixed `|` separators via `custom-text` (not flex separators)

## Usage

```
/setup-statusline            # Full three-line layout (default)
/setup-statusline --minimal  # Single-line compact layout
/setup-statusline --reset    # Remove statusline config
```

## Preview

```
Model: Opus 4.7 (1M context) | Effort: high | Ctx: [██░░░░░░░░░░░░░░] 105k/1000k (11%)
Session: my-session | Usage: 9.0% | Reset: 3hr 8m
⎇ dev_mengjia (+266,-67) | (no PR)
```

## Known Limitations

- The `thinking-effort` widget doesn't recognize Opus 4.7's `xhigh` level and falls back to `medium`. This is an upstream ccstatusline limitation.
