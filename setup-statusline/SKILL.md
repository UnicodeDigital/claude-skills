---
name: setup-statusline
description: Install and configure ccstatusline with team best-practice defaults. Sets up Claude Code statusLine in settings.json and writes optimized widget layout to ccstatusline config. Optimized for 80-column terminals and Team Plan users.
disable-model-invocation: true
argument-hint: "[--minimal | --full | --reset]"
allowed-tools: Bash(mkdir *) Bash(npx *) Read Write Edit
---

# Setup ccstatusline

Install and configure [ccstatusline](https://github.com/sirmalloc/ccstatusline) with team-standard best practices.

## What you should do

### Step 1: Parse arguments

- `$ARGUMENTS` may be one of:
  - `--minimal` — single-line layout (model + context + git branch only), good for small terminals
  - `--full` — three-line layout with all recommended widgets (default if no argument)
  - `--reset` — remove statusline configuration entirely
- If no argument is given, use `--full`

### Step 2: Ensure ccstatusline is available

Run `npx -y ccstatusline@latest --help` to verify the package is accessible. If it fails, inform the user.

### Step 3: Configure Claude Code settings

Read `~/.claude/settings.json`. If the `statusLine` key is missing or different, update it to:

```json
{
  "statusLine": {
    "type": "command",
    "command": "npx -y ccstatusline@latest",
    "padding": 0
  }
}
```

If `$ARGUMENTS` is `--reset`, remove the `statusLine` key from settings.json and delete `~/.config/ccstatusline/settings.json`, then stop.

### Step 4: Write ccstatusline widget config

Create directory `~/.config/ccstatusline/` if it does not exist.

Write `~/.config/ccstatusline/settings.json` with the layout matching the chosen mode:

#### --full (default): Three-line layout (optimized for 80-col terminals and Team Plan)

**Line 1 — Model & Context:**
| Widget | Type | Color | Purpose |
|--------|------|-------|---------|
| Model | `model` | `cyan` | Current model name |
| (separator) | `separator` | | flex space |
| Thinking Effort | `thinking-effort` | `brightYellow` | Effort level |
| (separator) | `separator` | | flex space |
| Context Bar | `context-bar` | `green` | Visual progress bar with percentage |
| (separator) | `separator` | | flex space |

**Line 2 — Session & Usage (uses custom-text for fixed `|` separators):**
| Widget | Type | Color | Purpose |
|--------|------|-------|---------|
| Session Name | `session-name` | `brightCyan` | Session name (via /rename, empty if not set) |
| Pipe | `custom-text` (" \| ") | `brightBlack` | Fixed separator |
| Usage Label | `custom-text` ("Usage: ") | `brightBlue` | Custom label for usage |
| Usage Value | `session-usage` (rawValue) | `brightBlue` | Team Plan usage percentage |
| Pipe | `custom-text` (" \| ") | `brightBlack` | Fixed separator |
| Reset Timer | `reset-timer` | `brightBlue` | 5hr usage limit reset countdown |

**Line 3 — Git info (widgets use `hideNoGit: true` to hide in non-git dirs):**
| Widget | Type | Color | Purpose |
|--------|------|-------|---------|
| Branch | `git-branch` | `brightBlue` | Current branch |
| Worktree | `worktree-branch` | (default) | Worktree branch (hideNoGit) |
| Changes | `git-changes` | `magenta` | Lines added/removed e.g. (+266,-67) |
| (separator) | `separator` | | flex space |
| Ahead/Behind | `git-ahead-behind` | `brightCyan` | Commits vs remote (hideNoGit) |
| PR | `git-pr` | `brightMagenta` | Associated PR link (hideNoGit) |

Full JSON config:

```json
{
  "version": 3,
  "lines": [
    [
      {"id": "1", "type": "model", "color": "cyan"},
      {"id": "16", "type": "separator"},
      {"id": "10", "type": "thinking-effort", "color": "brightYellow"},
      {"id": "4", "type": "separator"},
      {"id": "3", "type": "context-bar", "color": "green"},
      {"id": "6", "type": "separator"}
    ],
    [
      {"id": "20", "type": "session-name", "color": "brightCyan"},
      {"id": "25", "type": "custom-text", "customText": " | ", "color": "brightBlack"},
      {"id": "27", "type": "custom-text", "customText": "Usage: ", "color": "brightBlue"},
      {"id": "24", "type": "session-usage", "color": "brightBlue", "rawValue": true},
      {"id": "26", "type": "custom-text", "customText": " | ", "color": "brightBlack"},
      {"id": "23", "type": "reset-timer", "color": "brightBlue"}
    ],
    [
      {"id": "5", "type": "git-branch", "color": "brightBlue"},
      {"id": "2", "type": "worktree-branch", "hideNoGit": true},
      {"id": "7", "type": "git-changes", "color": "magenta", "hideNoGit": true},
      {"id": "13", "type": "separator"},
      {"id": "14", "type": "git-ahead-behind", "color": "brightCyan", "hideNoGit": true},
      {"id": "15", "type": "git-pr", "color": "brightMagenta", "hideNoGit": true}
    ]
  ],
  "flexMode": "full-minus-40",
  "compactThreshold": 60,
  "colorLevel": 2,
  "inheritSeparatorColors": false,
  "globalBold": false,
  "minimalistMode": false,
  "powerline": {
    "enabled": false,
    "separators": [""],
    "separatorInvertBackground": [false],
    "startCaps": [],
    "endCaps": [],
    "autoAlign": false,
    "continueThemeAcrossLines": false
  }
}
```

#### --minimal: Single-line layout

```json
{
  "version": 3,
  "lines": [
    [
      {"id": "1", "type": "model", "color": "cyan"},
      {"id": "4", "type": "separator"},
      {"id": "3", "type": "context-bar", "color": "green"},
      {"id": "6", "type": "separator"},
      {"id": "5", "type": "git-branch", "color": "brightBlue"}
    ]
  ],
  "flexMode": "full-minus-40",
  "compactThreshold": 60,
  "colorLevel": 2,
  "inheritSeparatorColors": false,
  "globalBold": false,
  "minimalistMode": true,
  "powerline": {
    "enabled": false,
    "separators": [""],
    "separatorInvertBackground": [false],
    "startCaps": [],
    "endCaps": [],
    "autoAlign": false,
    "continueThemeAcrossLines": false
  }
}
```

### Step 5: Confirm to the user

Print a summary of what was configured and which mode was applied. Remind them that the status line will refresh automatically, or they can restart Claude Code to see changes immediately.
