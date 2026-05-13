# Claude Skills

UnicodeDigital team shared skills for [Claude Code](https://claude.ai/code).

## Available Skills

| Skill | Description                                       |
|-------|---------------------------------------------------|
| [/setup-statusline](skills/setup-statusline/) | Configure ccstatusline with team-standard defaults |
| [/starrocks-query](skills/starrocks-query/) | 自然语言查询公司 StarRocks 数据仓库（需配套 MCP Server）           |
| [/starrocks-ops](skills/starrocks-ops/) | 用本地个人账号跑 StarRocks SQL（读写）需Python环境               |
| [/architecture-rfc-diagram](skills/architecture-rfc-diagram/) | 读项目代码生成黑白线条风格的架构图 RFC（单文件 HTML + Mermaid）            |

## Installation

每个 skill 的 README 里都有一份可直接复制的安装命令（cd 到上面表格里点 skill 名）。通用三步如下，把 `<skill-name>` 替换成你想装的那一个：

```bash
# 1. Clone the repo
git clone https://github.com/UnicodeDigital/claude-skills.git /tmp/claude-skills

# 2. Copy the skill you need
mkdir -p ~/.claude/skills
cp -r /tmp/claude-skills/skills/<skill-name> ~/.claude/skills/

# 3. Clean up
rm -rf /tmp/claude-skills
```

装完直接在 Claude Code 里 `/<skill-name>` 调用，无需重启。一次装多个就把第 2 步重复多遍即可。
