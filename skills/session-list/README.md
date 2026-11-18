# /session-list

把本机的 Claude Code 会话列成一张表：在不在运行、在哪个目录、聊的是什么、留着还是删。包括终端里的 CLI 会话和 Claude 桌面版里的会话，也能单独列出已归档的会话并按需恢复。

## Installation

```bash
git clone https://github.com/UnicodeDigital/claude-skills.git /tmp/claude-skills
mkdir -p ~/.claude/skills
cp -r /tmp/claude-skills/skills/session-list ~/.claude/skills/
rm -rf /tmp/claude-skills
```

装完直接在 Claude Code 里运行 `/session-list`，无需重启（安装之前就已打开的会话看不到时，重新打开一下）。

## Features

- **只读收集**：`scripts/collect.py` 读运行中进程的注册信息、桌面版的会话元数据和对话记录，输出 JSON，不改任何文件。
- **固定表格**：sessionId、session name、cwd、PID / 入口、记录大小、一句话简介、建议（保留 / 看情况 / 可删）、上次活跃时间。
- **按目录筛选**：`--cwd <目录>` 只列该目录下（含子目录）的会话。
- **已归档的会话**：默认清单里排在最后；`--archived` 只列已归档的。桌面版侧边栏按分组分块显示时，归档的会话不在侧边栏里、搜索也搜不到，用这个找回来；说"恢复 X"即可取消归档，回到原来的分组。
- **历史会话**：`--history --since 30` 另外加上 30 天内在终端开过、已不在运行的会话。
- **只列不删**：删除仍由你在侧边栏里操作；归档、恢复只在你点名时做。

## Usage

```
/session-list
```

也可以直接说"看看我开了哪些会话""test 目录下有哪些会话""哪些会话能删""我归档了哪些会话""恢复 overview"等。

## Requirements

- macOS（读取桌面版在 `~/Library/Application Support/Claude/` 下的会话数据）与 Python 3。
- 恢复归档会话要用 Claude 桌面版（Code 标签页）提供的会话管理工具；纯命令行里只能列，不能恢复。

## Known Limitations

- 桌面版的会话元数据里没有归档时间，表里的时间是最后一条对话的时间。
