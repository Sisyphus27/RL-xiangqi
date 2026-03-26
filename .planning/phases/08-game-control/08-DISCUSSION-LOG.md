# Phase 08: Game Control - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 08-game-control
**Areas discussed:** 按钮布局, 悔棋粒度, AI走子, 按钮状态, 随机执方, 交互控制

---

## 按钮位置与布局

| Option | Description | Selected |
|--------|-------------|----------|
| 工具栏 | 在窗口上方添加 QToolBar，按钮并排显示。符合桌面应用惯例。 | ✓ |
| 棋盘右侧面板 | 在棋盘右侧添加 QWidget，按钮垂直排列。与棋盘紧密关联。 | |
| 状态栏嵌入 | 在状态栏中嵌入按钮。空间有限，但保持窗口简洁。 | |

**User's choice:** 工具栏
**Notes:** 符合桌面应用惯例

---

## 悔棋粒度

| Option | Description | Selected |
|--------|-------------|----------|
| 双步悔棋 | 每次悔棋撤销一回合（人类+AI走法），回到上一次人类走棋前。更符合直觉。 | ✓ |
| 单步悔棋 | 每次悔棋撤销一步，可撤销到人类走棋后的状态（黑方回合）。灵活但可能困惑。 | |

**User's choice:** 双步悔棋
**Notes:** 更符合直觉，悔棋后总是轮到红方（人类）

---

## AI重新走子

| Option | Description | Selected |
|--------|-------------|----------|
| AI重新走子 | 悔棋后如果轮到黑方，AI重新走子。更自然，用户可以尝试不同走法。 | |
| 不自动走子 | 悔棋后停在当前状态，等待人类走棋。用户可以研究局面。 | |

**User's choice:** 不适用
**Notes:** 用户指出双步悔棋后总是轮到红方，不存在"轮到黑方"的情况，此问题不适用

---

## 按钮禁用状态

| Option | Description | Selected |
|--------|-------------|----------|
| AI思考时禁用悔棋 | AI思考期间禁用悔棋按钮，防止状态混乱。新对局按钮保持可用。 | ✓ |
| 无棋可悔时禁用悔棋 | 没有历史可悔时禁用悔棋按钮。 | ✓ |
| 新对局始终可用 | 新对局按钮始终可用，用户可以随时开始新游戏。 | ✓ |

**User's choice:** 全选
**Notes:** 悔棋按钮根据状态动态启用/禁用，新对局按钮始终可用

---

## 开局随机性（增强功能）

| Option | Description | Selected |
|--------|-------------|----------|
| 随机分配 | 新对局时随机决定谁执红，有时人类执红，有时AI执红。增加趣味性。 | ✓ |
| 固定人类执红 | 始终人类执红，保持简单。 | |
| 用户选择 | 让用户选择执红还是执黑。增加 UI 复杂度。 | |

**User's choice:** 随机分配
**Notes:** RandomAI 已支持任意执方，增加趣味性

---

## 执方指示器

| Option | Description | Selected |
|--------|-------------|----------|
| 状态栏显示 | 在状态栏显示"你执红方"或"你执黑方"，开局时显示。简单明了。 | ✓ |
| 工具栏标签 | 在工具栏添加标签显示当前执方。与按钮在同一个区域。 | |

**User's choice:** 状态栏显示
**Notes:** 与现有回合指示器保持一致

---

## 交互控制

| Option | Description | Selected |
|--------|-------------|----------|
| 按用户执方控制 | 根据用户执方决定何时可交互：执红时红方回合可交互，执黑时黑方回合可交互。 | ✓ |
| 固定红方回合交互 | 始终只在红方回合可交互。如果用户执黑则AI先走，用户等待。 | |

**User's choice:** 按用户执方控制
**Notes:** GameController 需要记录 _human_side 属性

---

## Claude's Discretion

- 工具栏图标选择
- 按钮快捷键绑定
- 状态栏文本措辞
- 悔棋确认弹窗

## Deferred Ideas

- 将军视觉高亮 — 未来 UI 增强考虑
- 走法历史记录 — v0.3 考虑
- 用户选择执方（下拉菜单）— 当前随机分配已足够
- 悔棋确认弹窗 — 当前直接执行
