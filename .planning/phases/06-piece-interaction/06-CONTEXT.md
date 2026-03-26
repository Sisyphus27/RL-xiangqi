# Phase 06: Piece Interaction - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

用户点击己方棋子（红方）选中，合法走法目标格高亮，点击合法目标格落子。实现 UI-03、UI-04、UI-05 三个需求。交互逻辑包括选子、高亮显示合法走法、落子、回合控制。Phase 05 已完成棋盘渲染和棋子显示，Phase 06 在此基础上添加交互层。

</domain>

<decisions>
## Implementation Decisions

### 选子视觉反馈
- **D-01:** 选中棋子显示金黄色外圈高亮（#FFD700），保持原白色描边不变
- **D-02:** 外圈 item 动态创建/删除：选中时创建 QGraphicsEllipseItem，取消选中时删除
- **D-03:** 外圈在棋子上层（z-value > 1.0），半透明不完全遮挡棋子

### 合法走法高亮
- **D-04:** 合法走法目标格显示半透明圆点（QGraphicsEllipseItem）
- **D-05:** 圆点颜色金黄色 #FFD700，与选中外圈颜色统一
- **D-06:** 圆点实现为 QGraphicsEllipseItem，选子时创建，取消选子时删除
- **D-07:** 圆点透明度 50%，半透明不遮挡棋盘网格
- **D-08:** 圆点大小为 0.5*cell 直径（中等圆点）

### 走法执行 UX
- **D-09:** 落子时立即移动，无动画（简化实现）
- **D-10:** 棋盘增量更新：只更新移动棋子和被吃棋子（如有），其余不变
- **D-11:** 状态更新顺序：调用 engine.apply(move) → 更新 self._state → 刷新棋盘
- **D-12:** 增量更新逻辑封装在 QXiangqiBoard.apply_move() 方法中
- **D-13:** 落子后清除所有高亮（选中外圈 + 合法走法圆点）
- **D-14:** 移动棋子时更新现有 item 的 pos 和内部 _row/_col 属性，复用 item
- **D-15:** QXiangqiBoard 维护 {(row, col): PieceItem} 字典索引，O(1) 查找棋子 item
- **D-16:** 被吃棋子从 scene 移除并从字典删除
- **D-17:** 字典索引立即更新：移动/删除棋子后立即更新字典，保持一致性
- **D-18:** 无需异常处理：UI 层已确保只调用合法走法（从 legal_moves 中选择）
- **D-19:** 走法完成后发出信号通知外部状态已改变
- **D-20:** 自定义 pyqtSignal，携带 move 信息（from_sq, to_sq, captured）
- **D-21:** 走法执行期间临时禁用交互，防止重复操作
- **D-22:** 交互禁用通过布尔属性 _interactive: bool 实现，mousePressEvent 检查该标志
- **D-23:** UI 构建 move（16-bit int）：从选中棋子位置 + 目标格位置构建，使用 rc_to_sq 和位运算

### 回合交互控制
- **D-24:** 黑方回合时通过布尔标志 _interactive=False 禁用交互
- **D-25:** 禁用时静默忽略点击，无视觉反馈（mousePressEvent 直接返回）
- **D-26:** 外部 Controller（Phase 07）设置 _interactive 标志：红方回合 True，黑方回合 False
- **D-27:** _interactive 默认值 True（启用），黑方回合前设置为 False，走子后恢复 True

### Claude's Discretion
- 外圈高亮的具体透明度（建议 50-70%）
- 外圈的具体粗细（建议 2-3px）
- 圆点的 z-value（应在棋子下方，z < 1.0）
- 字典索引的初始化时机（在 _load_pieces 中同步构建）
- 信号命名的具体风格（如 moveApplied 或 on_move_applied）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Engine API (v0.1 — 已完成)
- `src/xiangqi/engine/engine.py` — XiangqiEngine 公共 API：`apply(move)`, `legal_moves()`, `is_legal(move)`, `board`, `turn` 属性
- `src/xiangqi/engine/types.py` — Move 编码（16-bit int），`rc_to_sq(row, col)` 和 `sq_to_rc(sq)` 坐标转换
- `src/xiangqi/engine/constants.py` — ROWS=10, COLS=9 棋盘尺寸

### Phase 05 UI 实现
- `src/xiangqi/ui/board.py` — QXiangqiBoard 类：QGraphicsView 子类，`_load_pieces()` 方法，`_state` 属性
- `src/xiangqi/ui/board_items.py` — PieceItem 类：QGraphicsEllipseItem 子类，`_row`, `_col`, `_piece_value` 属性
- `src/xiangqi/ui/constants.py` — UI 常量：CELL_RATIO=0.80, PIECE_FONT_RATIO=0.56, 颜色常量
- `src/xiangqi/ui/main.py` — MainWindow 类：窗口管理

### 项目级参考
- `.planning/ROADMAP.md` — Phase 06 目标、5 条成功标准、Requirements UI-03/04/05
- `.planning/REQUIREMENTS.md` — UI-03（选子/高亮）、UI-04（落子）、UI-05（取消选子）需求
- `.planning/phases/05-board-rendering/05-CONTEXT.md` — Phase 05 上下文：棋盘渲染、棋子显示、坐标系统
- `.planning/STATE.md` — Conda 环境 `xqrl` 关键说明

### PyQt6 交互模式
- `.planning/research/ARCHITECTURE.md` — 三层分离（UI/Controller/AI/Engine），Phase 06 属于 UI 层交互
- `.planning/research/PITFALLS.md` — PyQt6 已知陷阱（信号槽、事件处理）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `QXiangqiBoard` 类：已实现棋盘渲染和棋子加载，可直接添加交互方法
- `PieceItem` 类：已有 `_row`, `_col`, `_piece_value` 属性，可更新位置
- `XiangqiEngine` API：`legal_moves()` 返回所有合法走法，`apply(move)` 执行走法
- 坐标转换函数：`rc_to_sq(row, col)` → sq (0-89)，`sq_to_rc(sq)` → (row, col)

### Established Patterns
- 棋盘坐标系：row 0 = 黑方底线（顶），row 9 = 红方底线（底），col 0 = 左侧
- Scene 坐标系：piece center at (col + 0.6, row + 0.6) * cell，cell = min(vw, vh) / 11.2
- 红方棋子值 +1-+7，黑方棋子值 -1--7，正负区分颜色
- Conda 环境 `xqrl` 运行所有命令（STATE.md 强制要求）

### Integration Points
- Phase 05 输出：QXiangqiBoard + PieceItem 渲染完成
- Phase 06 接入：添加选子、高亮、落子逻辑到 QXiangqiBoard
- Phase 07 接入：外部 Controller 控制 _interactive 标志，AI 行棋时禁用交互

</code_context>

<specifics>
## Specific Ideas

- 金黄色外圈高亮：与象棋传统高亮色一致，视觉突出
- 半透明圆点标记合法走法：简洁不遮挡棋盘，金黄色与选中外圈统一
- 增量更新优化性能：只更新移动棋子和被吃棋子，不重建整个 scene
- 字典索引加速查找：O(1) 时间找到指定位置的棋子 item
- 静默忽略黑方回合点击：简单直接，无额外视觉反馈
- 自定义信号通知外部：解耦 board 与 controller，Phase 07 可监听信号更新回合提示

</specifics>

<deferred>
## Deferred Ideas

### Ideas from Discussion
- 拖拽落子（drag-and-drop）— MVP 阶段点击落子已足够，拖拽增加复杂度
- 将军视觉高亮（被将军时王棋高亮）— Phase 08 UI 增强考虑
- 走法动画（滑动效果）— MVP 阶段立即移动，动画在 v0.3 考虑
- 音效（落子音效）— v0.3 考虑
- 被吃棋子展示区域 — v0.2 之后考虑

</deferred>

---

*Phase: 06-piece-interaction*
*Context gathered: 2026-03-24*
