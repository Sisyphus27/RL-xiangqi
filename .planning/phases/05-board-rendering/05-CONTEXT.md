# Phase 05: Board Rendering - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

使用 QGraphicsView + QGraphicsScene 渲染完整的 9×10 象棋盘，32 枚棋子正确摆放和分色。用户打开应用即可看到可读的初始局面。UI-01、UI-02 两个需求在此阶段完成。

</domain>

<decisions>
## Implementation Decisions

### 棋盘背景 + 网格风格
- **D-01:** 棋盘底色：绿色毛毡 `#7BA05B`
- **D-02:** 网格线风格：简化行列分隔线（不画所有交叉点连线）
- **D-03:** 河流区域：行 4-5 之间网格线断开（标准象棋画法）
- **D-04:** 网格线颜色：深绿色 `#2D5A1B`
- **D-05:** 河流文字：「楚河」「漢界」，左右分列（左侧「楚河」，右侧「漢界」）

### 九宫斜线 + 坐标视觉
- **D-06:** 九宫斜线：两侧对角线都绘制（标准象棋棋盘）
- **D-07:** 行列坐标：象棋传统双编号（红方视角 + 黑方视角，各自编号）

### 窗口大小 + 响应式缩放
- **D-08:** 默认窗口尺寸：舒适（480×600px 起）
- **D-09:** 缩放策略：棋盘固定比例缩放，有最小/最大限制
- **D-10:** 窗口最小尺寸：360×450px（紧凑）
- **D-11:** 窗口最大尺寸：舒适默认的 1.5 倍（720×900px）

### 棋子大小 + 字体样式
- **D-12:** 棋子直径：格子宽度的 80%（留足间距，防止邻子相碰）
- **D-13:** 棋子字体：宋体（常规字重）
- **D-14:** 棋子底色：实色圆形底（红方棋子红色底，黑方棋子黑色底）
- **D-15:** 棋子描边：白色描边，统一所有棋子
- **D-16:** 棋子效果：纯平面（无 3D 立体/阴影）

### Claude's Discretion
- 行列坐标的具体渲染位置（内边缘/外边缘）
- 棋盘背景 QGraphicsScene 绘制方式（setBackgroundBrush）
- QGraphicsSimpleTextItem vs QGraphicsTextItem 的具体使用
- 窗口标题栏的精确措辞（已由 ROADMAP 规定 "RL-Xiangqi v0.2"）
- 棋子在窗口最小尺寸下的最小可读尺寸
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Xiangqi Engine (v0.1 — 已完成)
- `src/xiangqi/engine/types.py` — Piece 枚举（红方 +1-+7，黑方 -1--7），`__str__` 返回中文字符，`rc_to_sq/sq_to_rc` 坐标转换
- `src/xiangqi/engine/constants.py` — ROWS=10, COLS=9, STARTING_FEN, IN_PALACE, IN_RIVER 边界掩码
- `src/xiangqi/engine/state.py` — XiangqiState.starting() 初始局面，`king_positions` 字段

### v0.2 PyQt6 架构研究
- `.planning/research/STACK.md` — PyQt6 技术栈决策、QGraphicsView vs QWidget
- `.planning/research/LIBRARIES.md` — PyQt6 安装、`conda env xqrl` 环境
- `.planning/research/ARCHITECTURE.md` — 三层分离（UI/Controller/AI/Engine）
- `.planning/research/PITFALLS.md` — PyQt6 已知陷阱
- `.planning/research/SUMMARY.md` — 研究总结

### 项目级参考
- `.planning/ROADMAP.md` — Phase 05 目标、5 条成功标准
- `.planning/REQUIREMENTS.md` — UI-01（棋盘渲染）、UI-02（棋子渲染）需求
- `.planning/STATE.md` — Conda 环境 `xqrl` 关键说明

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/xiangqi/engine/types.py` Piece 枚举：`str(Piece.R_SHUAI)` → `"帅"`，`str(Piece.B_JIANG)` → `"将"`
- `XiangqiState.starting()` — 返回初始局面，直接传给 UI 渲染
- `src/xiangqi/engine/constants.py` ROWS=10, COLS=9 — UI 网格尺寸已知

### Established Patterns
- Conda 环境 `xqrl` 运行所有命令（STATE.md 强制要求）
- 棋盘坐标系：row 0 = 黑方底线（顶），row 9 = 红方底线（底），col 0 = 左侧
- 红方棋子值 +1-+7，黑方棋子值 -1--7，正负区分颜色

### Integration Points
- Phase 05 输出：完整可渲染的 QGraphicsScene（含棋盘背景 + 32 枚棋子 QGraphicsItem）
- Phase 06 接入：Scene 不变，Controller 处理点击选子
- Phase 07 接入：EngineSnapshot 从 XiangqiState.starting() 初始化

</code_context>

<specifics>
## Specific Ideas

- 绿色毛毡 + 深绿线：传统象棋棋盘视觉
- 楚河/漢界分列：标准中国象棋盘惯例
- 象棋传统双编号：红方从右到左 1-9 + 1-10 行；黑方反向
- 棋子白色描边统一风格：红黑棋子均有白色边框，层次分明
- 棋子无 3D 效果：MVP 纯平面简化实现

</specifics>

<deferred>
## Deferred Ideas

### Ideas from Discussion
- 棋盘外边框（棋盘周围留白边框区域）— Phase 08 之后考虑
- 将军视觉高亮（被将军时王棋高亮）— Phase 08 UI 增强考虑
- 被吃棋子展示区域 — v0.2 之后考虑
- 音效/计时系统 — v0.3 考虑
- PGN/棋谱导入导出 — v1.0 考虑

</deferred>

---

*Phase: 05-board-rendering*
*Context gathered: 2026-03-23*
