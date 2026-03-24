# Roadmap: RL-Xiangqi v0.2 PyQt6 UI

**Milestone:** v0.2
**Started:** 2026-03-23
**Core Deliverable:** Human-vs-AI Chinese Chess board (PyQt6) with RandomAI and extensible AI interface

---

## Phases

- [x] **Phase 05: Board Rendering** — QGraphicsView + QGraphicsScene 渲染 9x10 棋盘与 32 枚棋子 ✓ COMPLETE
- [ ] **Phase 06: Piece Interaction** — 点击选子、合法走法高亮、点击落子
- [ ] **Phase 07: AI Interface + Game State** — AIPlayer ABC / EngineSnapshot / RandomAI + 回合提示 + 终局弹窗
- [ ] **Phase 08: Game Control** — 新对局按钮 + 连续悔棋

---

## Phase Details

### Phase 05: Board Rendering

**Goal:** 用户打开应用，看到完整可读的 9x10 象棋盘，32 枚棋子位置正确，红黑分色

**Depends on:** Nothing

**Requirements:** UI-01, UI-02

**Success Criteria** (what must be TRUE):

1. 棋盘显示 9 列 x 10 行网格，河流区域（第五行与第六行之间）无横线，九宫斜线正确绘制
2. 所有 32 枚棋子（帅/将 x1、车/炮 x2、马 x2、象/士 x2、兵 x5 x2 方）按初始局面排列
3. 红方棋子（帅/车/马/炮/士/兵）显示红色，黑方棋子（将/车/马/炮/士/卒）显示黑色
4. 棋盘在窗口缩放时保持宽高比不变，棋子大小与格宽匹配
5. 窗口标题显示 "RL-Xiangqi v0.2"

**Plans:** 9/9 plans complete
- [x] 05-01-PLAN.md — UI constants (constants.py, __init__.py)
- [x] 05-02-PLAN.md — PieceItem rendering (board_items.py)
- [x] 05-03-PLAN.md — QXiangqiBoard + MainWindow + tests ✓ COMPLETE

---

### Phase 06: Piece Interaction

**Goal:** 用户点击己方棋子（红方）选中，合法走法目标格高亮，点击合法目标格落子

**Depends on:** Phase 05

**Requirements:** UI-03, UI-04, UI-05

**Success Criteria** (what must be TRUE):

1. 点击红方棋子：该格显示选中状态（如边框高亮），所有合法目标格显示半透明圆点或高亮
2. 点击高亮目标格：棋子移动到目标格，棋盘刷新，走法生效（调用 engine.apply）
3. 点击己方另一枚棋子：取消前一枚选中状态，选中新棋子，更新高亮
4. 点击非合法目标格、敌方棋子格（无合法走法）、空白格（无合法走法）：取消当前选子，选中状态清除
5. 轮到黑方（AI）回合时，棋盘交互被禁用（鼠标点击无响应）

**Plans:** TBD

---

### Phase 07: AI Interface + Game State

**Goal:** 黑方 AI 自动在回合内行棋；UI 实时显示当前回合与终局状态

**Depends on:** Phase 06

**Requirements:** AI-01, AI-02, AI-03, AI-04, UI-06, UI-07

**Success Criteria** (what must be TRUE):

1. `AIPlayer` 抽象基类定义了 `suggest_move(snapshot: EngineSnapshot) -> Move | None` 接口
2. `EngineSnapshot` 数据类封装棋盘数组、回合、合法走法，可在多线程间安全传递
3. `RandomAI` 实现了 `AIPlayer`，从合法走法中随机返回一步；行棋后棋盘正确更新
4. AI 行棋期间（黑方回合），UI 显示 "AI 思考中..." 提示，行棋完成后提示自动消失
5. 棋盘旁或状态栏显示当前回合：红方回合显示 "红方回合"，黑方回合显示 "黑方回合（AI）"
6. 对局结束时（将死/困毙/和棋），弹出消息框显示结果（"红方胜"/"黑方胜"/"和棋"）

**Plans:** TBD

---

### Phase 08: Game Control

**Goal:** 用户可以随时开始新对局或撤销上一步走法（支持连续悔棋）

**Depends on:** Phase 07

**Requirements:** UI-08, UI-09

**Success Criteria** (what must be TRUE):

1. 新对局按钮存在，点击后棋盘恢复到初始局面，回合重置为红方先手
2. 新对局后可以正常进行新的对弈（Phase 05-07 功能不受影响）
3. 悔棋按钮存在，点击后撤销最后一步走法（无论该步是红方还是 AI 所走）
4. 支持连续悔棋：可连续多次点击撤销多步，直到回到初始局面
5. 悔棋到初始局面后，悔棋按钮不再可用（新对局按钮保持可用）

**Plans:** TBD

---

## Phase Map

| Phase | Goal | Requirements | Success Criteria |
|-------|------|--------------|-------------------|
| 05 - Board Rendering | 9/9 | Complete   | 2026-03-24 |
| 06 - Piece Interaction | 点击选子/高亮/落子 | UI-03, UI-04, UI-05 | 5 criteria |
| 07 - AI Interface + Game State | AI 行棋 + 回合/终局提示 | AI-01, AI-02, AI-03, AI-04, UI-06, UI-07 | 6 criteria |
| 08 - Game Control | 新对局 + 悔棋 | UI-08, UI-09 | 5 criteria |

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 05. Board Rendering | 3/3 | ✓ Complete | 05-01, 05-02, 05-03 |
| 06. Piece Interaction | 0/? | Not started | - |
| 07. AI Interface + Game State | 0/? | Not started | - |
| 08. Game Control | 0/? | Not started | - |

---

## Architecture Notes (from research)

- **Three-layer separation:** UI (`src/xiangqi/ui/`) -- GameController (`src/xiangqi/controller/`) -- AI (`src/xiangqi/ai/`) -- Engine (`src/xiangqi/engine/`, v0.1 existing)
- **Thread safety:** Engine reference never crosses thread boundary; `EngineSnapshot` (frozen dataclass) passes board copy across thread boundary
- **AI threading:** QThread worker via `moveToThread()` (NOT QThread subclass); slots on worker run in worker thread
- **is_legal() guard:** Every AI-returned move validated with `engine.is_legal()` before `engine.apply()`
- **Generation counter:** Each game/undo increments counter; stale AI results discarded by generation comparison

---

*Roadmap created: 2026-03-23*
*Phase numbering continues from v0.1 (v0.1 ended at 04.1)*
