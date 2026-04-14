# Claude Skills

UnicodeDigital team shared skills for [Claude Code](https://claude.ai/code).

## Available Skills

### `/setup-statusline`

One-command setup for [ccstatusline](https://github.com/sirmalloc/ccstatusline) with team-standard defaults.

**Features:**
- Three-line layout: Model & Context / Session & Reset Timer / Git info
- Optimized for 80-column terminals
- Optimized for Team Plan (no cost widget, includes usage reset timer)
- `hideNoGit` on git widgets for clean display in non-git directories

**Usage:**

```
/setup-statusline            # Full three-line layout (default)
/setup-statusline --minimal  # Single-line compact layout
/setup-statusline --reset    # Remove statusline config
```

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/UnicodeDigital/claude-skills.git /tmp/claude-skills

# 2. Copy skills to your local Claude skills directory
mkdir -p ~/.claude/skills
cp -r /tmp/claude-skills/setup-statusline ~/.claude/skills/

# 3. Clean up
rm -rf /tmp/claude-skills
```

Then run `/setup-statusline` in Claude Code. No restart needed.
