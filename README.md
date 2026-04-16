# Claude Skills

UnicodeDigital team shared skills for [Claude Code](https://claude.ai/code).

## Available Skills

| Skill | Description |
|-------|-------------|
| [/setup-statusline](skills/setup-statusline/) | Configure ccstatusline with team-standard defaults |
| [/starrocks-query](skills/starrocks-query/) | 自然语言查询公司 StarRocks 数据仓库（需配套 MCP Server） |

## Installation

Install a specific skill by cloning this repo and copying the skill folder:

```bash
# 1. Clone the repo
git clone https://github.com/UnicodeDigital/claude-skills.git /tmp/claude-skills

# 2. Copy the skill you need (e.g. setup-statusline)
mkdir -p ~/.claude/skills
cp -r /tmp/claude-skills/skills/setup-statusline ~/.claude/skills/

# 3. Clean up
rm -rf /tmp/claude-skills
```

Then run the skill in Claude Code (e.g. `/setup-statusline`). No restart needed.
