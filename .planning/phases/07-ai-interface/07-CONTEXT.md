# Phase 07: AI Interface + Game State - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

实现AI抽象接口（AIPlayer ABC）、RandomAI黑方、回合/游戏状态UI提示。Phase 05 已完成棋盘渲染，Phase 06 已完成棋子交互，Phase 07 在此基础上连接AI玩家和游戏状态UI。

**Phase 07 完成时：** 人类（红方）可以与 RandomAI（黑方）对弈，UI 显示回合指示、"AI 思考中"、游戏结束弹窗。

</domain>

<decisions>
## Implementation Decisions

### UI 组件定位
- **D-01:** 回合指示器使用 QMainWindow.statusBar() 显示文本，位于窗口底部
- **D-02:** "AI 思考中..." 提示使用同一状态栏，黑方回合时显示
- **D-03:** 游戏结束使用 QMessageBox.information() 模态弹窗显示结果

### AI 线程模型
- **D-04:** 使用 QThread + moveToThread() 模式（Qt 官方推荐）
- **D-05:** AI worker 对象调用 moveToThread(QThread)，信号槽跨线程通信
- **D-06:** 线程运行事件循环，主线程通过 queued connection 接收结果

### AI 接口设计
- **D-07:** AIPlayer 是 abstract base class，定义 suggest_move(snapshot: EngineSnapshot) -> int | None
- **D-08:** EngineSnapshot 包含 board 数组副本、turn、legal_moves 列表（完整数据副本，线程安全）
- **D-09:** EngineSnapshot 为 dataclass，持有 numpy array 副本，AI 只读访问
- **D-10:** RandomAI 支持可选 seed 参数（默认 None），方便测试复现

### AI 错误处理
- **D-11:** AI 返回走法后，Controller 用 is_legal() 校验（is_legal guard）
- **D-12:** is_legal() 校验失败时抛出 ValueError，游戏终止（开发阶段早发现 bug）

### 状态转换流程
- **D-13:** 用户落子 → 检查 result() → 切换回合 → 启动 AI（禁用棋盘交互）
- **D-14:** AI 走子后 → 检查 result() → 切换回合 → 恢复棋盘交互
- **D-15:** AI 走子时机：AI 返回后立即执行，无人工延迟
- **D-16:** 游戏结束弹窗关闭后：棋盘保持终局状态，等待用户手动重置（Phase 08 实现）

### 代码组织
- **D-17:** AI 模块放在 src/xiangqi/ai/ 目录（与 engine/、ui/ 平级）

### 从 Phase 06 继承
- **D-18:** QXiangqiBoard.set_interactive(False) 控制棋盘交互（Phase 06 已实现）
- **D-19:** QXiangqiBoard.move_applied 信号通知外部走法已执行
- **D-20:** 回合切换通过 engine.turn 属性判断（+1 红方，-1 黑方）

### Claude's Discretion
- EngineSnapshot dataclass 的具体字段名称
- 状态栏文本的具体措辞（如 "红方回合" vs "轮到红方"）
- AI 思考中文本的样式（颜色、字体）
- GameController 类的具体实现细节
- 信号命名风格（如 move_completed vs on_move_applied）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Xiangqi Engine API (v0.1 — 已完成)
- `src/xiangqi/engine/engine.py` — XiangqiEngine 公共 API：`apply(move)`, `legal_moves()`, `is_legal(move)`, `board`, `turn`, `result()`, `reset()`, `undo()`
- `src/xiangqi/engine/types.py` — Move 编码（16-bit int），`rc_to_sq/sq_to_rc` 坐标转换，Piece 枚举
- `src/xiangqi/engine/constants.py` — ROWS=10, COLS=9

### Phase 05-06 UI 实现
- `src/xiangqi/ui/board.py` — QXiangqiBoard 类：`set_interactive(bool)`, `move_applied` pyqtSignal
- `src/xiangqi/ui/main.py` — MainWindow 类：QMainWindow，statusBar() 可用
- `src/xiangqi/ui/board_items.py` — PieceItem 类

### Phase 05-06 上下文
- `.planning/phases/05-board-rendering/05-CONTEXT.md` — 棋盘渲染、棋子显示、坐标系统
- `.planning/phases/06-piece-interaction/06-CONTEXT.md` — 选子高亮、落子执行、set_interactive 控制

### 架构研究（已确定的设计决策）
- `.planning/research/ARCHITECTURE.md` — 三层分离（UI/Controller/AI/Engine），QThread worker 模式
- `.planning/research/PITFALLS.md` — PyQt6 已知陷阱（信号槽跨线程、事件循环）

### 项目级参考
- `.planning/ROADMAP.md` — Phase 07 目标、7 条成功标准
- `.planning/REQUIREMENTS.md` — AI-01（AIPlayer ABC）、AI-02（EngineSnapshot）、AI-03（RandomAI）、AI-04（AI 思考提示）、UI-06（回合提示）、UI-07（结束提示）
- `.planning/STATE.md` — Conda 环境 `xqrl` 关键说明

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `XiangqiEngine` API：完整可用，无需修改
- `QXiangqiBoard.set_interactive(False)`：已实现，Phase 07 直接使用
- `QXiangqiBoard.move_applied` signal：已定义，Controller 监听此信号
- `QMainWindow.statusBar()`：Qt 标准 API，可直接调用

### Established Patterns
- 棋盘坐标系：row 0 = 黑方底线（顶），row 9 = 红方底线（底）
- 红方棋子值 +1-+7，黑方棋子值 -1--7，正负区分颜色
- Conda 环境 `xqrl` 运行所有命令（STATE.md 强制要求）
- 线程安全约定：EngineSnapshot 持有数据副本，engine 引用不跨线程边界

### Integration Points
- Phase 06 输出：QXiangqiBoard（交互完成）+ move_applied signal
- Phase 07 接入：GameController 监听 move_applied，驱动 AI 和状态转换
- Phase 08 接入：Controller.add_new_game_button()，Controller.add_undo_button()

</code_context>

<specifics>
## Specific Ideas

- 状态栏简洁显示：红方回合显示 "红方回合"，黑方回合显示 "AI 思考中..."
- 模态弹窗清晰提示：显示 "红胜"、"黑胜" 或 "和棋"，用户点击确定关闭
- AI 接口面向未来：AIPlayer ABC 设计要考虑未来 AlphaBetaAI、MCTSAI 的需求

</specifics>

<deferred>
## Deferred Ideas

### Ideas from Discussion
- AlphaBetaAI / MCTSAI — Phase 09+ 考虑，当前只有 RandomAI
- 将军视觉高亮 — Phase 08 UI 增强考虑
- AI 思考动画（转圈效果）— v0.3 考虑，当前只有文本提示
- AI 思考超时处理 — v0.3 考虑，当前 RandomAI 不会超时

</deferred>

---

*Phase: 07-ai-interface*
*Context gathered: 2026-03-25*
