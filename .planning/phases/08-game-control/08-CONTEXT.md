# Phase 08: Game Control - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

新对局按钮、悔棋功能（支持连续悔棋）。Phase 05 已完成棋盘渲染，Phase 06 已完成棋子交互，Phase 07 已完成 AI 接口和游戏状态 UI，Phase 08 在此基础上添加游戏控制功能。

**Phase 08 完成时：** 用户可以通过工具栏开始新对局、悔棋，开局时随机分配红黑方。

**范围扩展：** 原需求 UI-08/09 仅包含新对局和悔棋，本次讨论增加了"随机执方"功能作为可选增强。

</domain>

<decisions>
## Implementation Decisions

### 按钮布局
- **D-01:** 使用 QMainWindow 工具栏（QToolBar）放置新对局和悔棋按钮，位于窗口上方

### 悔棋逻辑
- **D-02:** 双步悔棋 — 每次撤销一回合（人类+AI各一步），回到上一次人类走棋前
- **D-03:** 悔棋后总是轮到红方（人类），无需 AI 重新走子逻辑

### 按钮状态管理
- **D-04:** AI 思考期间禁用悔棋按钮，新对局按钮保持可用
- **D-05:** 无棋可悔时（undo_stack 为空）禁用悔棋按钮
- **D-06:** 新对局按钮始终可用，用户可以随时开始新游戏

### 随机执方（增强功能）
- **D-07:** 新对局时随机分配红黑方（50% 概率人类执红，50% 概率 AI 执红）
- **D-08:** 状态栏显示用户执方（"你执红方"或"你执黑方"），开局时更新

### 交互控制调整
- **D-09:** 根据用户执方控制棋盘交互：
  - 执红方时：红方回合（turn == +1）可交互
  - 执黑方时：黑方回合（turn == -1）可交互

### Claude's Discretion
- 工具栏图标选择（新对局/悔棋按钮的图标样式）
- 按钮的快捷键绑定（如 Ctrl+N 新对局，Ctrl+Z 悔棋）
- 状态栏文本的具体措辞
- 悔棋时是否需要确认弹窗

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Xiangqi Engine API (v0.1 — 已完成)
- `src/xiangqi/engine/engine.py` — XiangqiEngine 公共 API：`reset()`, `undo()`, `result()`, `turn`
- `src/xiangqi/engine/types.py` — Move 编码，Piece 枚举

### Phase 05-07 UI 实现
- `src/xiangqi/ui/board.py` — QXiangqiBoard 类：`set_interactive(bool)`, `move_applied` signal
- `src/xiangqi/ui/main.py` — MainWindow 类：QMainWindow，可添加 QToolBar
- `src/xiangqi/controller/game_controller.py` — GameController 类：管理 engine, AI, board, window

### Phase 05-07 上下文
- `.planning/phases/05-board-rendering/05-CONTEXT.md` — 棋盘渲染
- `.planning/phases/06-piece-interaction/06-CONTEXT.md` — 选子高亮、落子执行
- `.planning/phases/07-ai-interface/07-CONTEXT.md` — AI 接口、回合指示、游戏结束

### 项目级参考
- `.planning/ROADMAP.md` — Phase 08 目标、5 条成功标准
- `.planning/REQUIREMENTS.md` — UI-08（新对局）、UI-09（悔棋）
- `.planning/STATE.md` — Conda 环境 `xqrl` 关键说明

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `XiangqiEngine.reset()` — 重置到初始局面，清空 undo stack
- `XiangqiEngine.undo()` — 撤销最近一步走法，支持连续调用
- `GameController` — 已有 engine, board, window 引用，可添加控制方法
- `QXiangqiBoard.set_interactive()` — 交互控制，Phase 06 已实现
- `QMainWindow.addToolBar()` — Qt 标准 API，可直接使用

### Established Patterns
- 棋盘交互通过 `_interactive` 布尔属性控制
- 状态栏通过 `window.statusBar().showMessage()` 更新
- AI 通过 QThread + moveToThread 模式运行
- Conda 环境 `xqrl` 运行所有命令

### Integration Points
- Phase 07 输出：GameController 完整可用
- Phase 08 接入：在 MainWindow 添加 QToolBar，在 GameController 添加 new_game() 和 undo() 方法
- 交互控制调整：GameController 需要记录 `_human_side` (+1 红方，-1 黑方)

</code_context>

<specifics>
## Specific Ideas

- 工具栏按钮简洁明了：新对局（重置图标）、悔棋（箭头图标）
- 双步悔棋更符合用户直觉：撤销"一回合"而非"一步"
- 随机执方增加趣味性，RandomAI 已支持任意执方
- 状态栏信息完整：显示"你执红方" + "红方回合"或"你执黑方" + "黑方回合"

</specifics>

<deferred>
## Deferred Ideas

### Ideas from Discussion
- 将军视觉高亮 — 未来 UI 增强考虑
- 走法历史记录 — v0.3 考虑
- 用户选择执方（下拉菜单）— 当前随机分配已足够，未来可扩展
- 悔棋确认弹窗 — 当前直接执行，未来可按需添加

</deferred>

---

*Phase: 08-game-control*
*Context gathered: 2026-03-26*
