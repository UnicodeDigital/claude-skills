# /session-sync

在主会话与它 fork / 派生出来的子会话之间同步进展：几个会话并行干活时，让彼此知道对方做了什么、定了什么、还有什么待办。

## Installation

```bash
git clone https://github.com/UnicodeDigital/claude-skills.git /tmp/claude-skills
mkdir -p ~/.claude/skills
cp -r /tmp/claude-skills/skills/session-sync ~/.claude/skills/
rm -rf /tmp/claude-skills
```

装完直接在 Claude Code 里运行 `/session-sync`，无需重启（安装之前就已打开的会话看不到时，重新打开一下）。

## Features

- **自动判断方向**：有父会话的是子会话，把自己的进展汇总发给父会话；没有父会话的是主会话，分别发给它直接派生出来的每个子会话。
- **兄弟会话互通**：子会话同步时，会影响其他子会话的部分（共用代码与接口的改动、新约定）另发一条精简版给同一主会话下的其他子会话；无关的不发。
- **只发对方不知道的**：起点取 fork 时刻与上次同步中较晚的一个；对方汇报过的事不再发回给它。
- **按用处排序**：用户的决定 → 完成的工作 → 改动（git 提交与当前 HEAD、仓库之外的改动） → 待办与待定。
- **不外带敏感信息**：凭据、账号等身份信息、大段代码与日志不写进消息。
- **直接发送**：每个接收方一条，第一行就说明是什么，发完向你汇报发给了谁。

## Usage

```
/session-sync        # 在主会话里：同步给各子会话；在子会话里：同步回主会话，相关部分同步给兄弟会话
```

也可以直接说"同步到子会话""把改动同步过去""转告主会话"等。

## Requirements

- Claude 桌面版（Code 标签页）：用到它提供的会话管理工具（`get_session`、`list_sessions`）和会话间消息（`SendMessage`）。纯命令行的 Claude Code 里没有这些工具时，skill 会提示后退出。
- 主、子会话之间要有派生关系（在桌面版里 fork 出来，或由一个会话启动另一个）。

## Known Limitations

- 发送成功只表示送达对方的收件箱，对方是否已读看不到。
- 只同步直接的父子与兄弟会话，不跨到孙会话。
