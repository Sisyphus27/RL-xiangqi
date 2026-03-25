# Roadmap: RL-Xiangqi v0.2 PyQt6 UI

**Milestone:** v0.2
**Started:** 2026-03-23
**Core Deliverable:** Human-vs-AI Chinese Chess board (PyQt6) with RandomAI and extensible AI interface
**Depends on:** Phase 05
**Requirements:** UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07, UI-08, UI-09
**Success Criteria** (what must be TRUE):
1. 棋盘显示 9 列 x 10 行网格，河流区域(第五行与第六行之间)无横线,九宫斜线正确绘制
2. 所有 32 枚棋子(帅/将 x1,车/炮x2,马x2,象/士 x2,兵x5个2方)按初始局面排列
3. 红方棋子(帅/车/马/炮/士/兵)显示红色,黑方棋子(将/车/马/炮/士/卒)显示黑色
4. 棋盘在窗口缩放时保持宽高比不变，棋子大小与格宽匹配
5. 窗口标题显示 "RL-Xiangqi v0.2"

**Plans:** 9/9 plans complete
- [x] 05-01-PLAN.md — UI constants (constants.py, __init__.py)
- [x] 05-02-PLAN.md — PieceItem rendering (board_items.py)
- [x] 05-03-PLAN.md — QXiangqiBoard + MainWindow + tests
- [x] 05-04-PLAN.md through 05-41-PLAN.md — Phase 05 iterations (COMPLETE)

### Phase 05 (Board Rendering) — COMPLETE
### Phase 06 (Piece Interaction) — IN PROGRESS (3/5 plans complete, 2 gap closure plans)

**Architecture Notes:**
- Three-layer separation: UI (`src/xiangqi/ui/`) -- GameController (`src/xiangqi/controller/`) -- AI (`src/xiangqi/ai/`) -- Engine (`src/xiangqi/engine/`, v0.1 existing)
- Thread safety: Engine reference never crosses thread boundary
- AI threading: QThread worker via `moveToThread()`
- is_legal() guard: Every AI move validated with engine.is_legal() before engine.apply()
- Generation counter: stale AI results discarded by generation comparison

---

### Phase 06: Piece Interaction
**Goal:** 用户点击己方棋子(红方)选中，合法走法目标格高亮,点击合法目标格落子
**Depends on:** Phase 05
**Requirements:** UI-03, UI-04, UI-05
**Success Criteria** (what must be TRUE):
1. 点击红方棋子:该格显示选中状态(金色边框高亮),所有合法目标格显示半透明圆点进行高亮
2. 点击高亮目标格:棋子移动到目标格,棋盘刷新,走法生效(调用 engine.apply)
3. 点击己方另一枚棋子:取消前一枚选中状态,选中新棋子,更新高亮
4. 点击非合法目标格、敌方棋子格、空白格:取消当前选子,选中状态清除
5. 轮到黑方(AI)回合时,棋盘交互被禁用(鼠标点击无响应)

**Plans:** 5 plans (1 wave-0 + 2 wave-1 + 1 wave-2 + 1 gap closure)
- [x] **06-00-PLAN.md** — Test scaffold (Wave 0) ✓ COMPLETE
- [x] **06-01-PLAN.md** — Selection highlighting infrastructure (Wave 1) ✓ COMPLETE
- [x] **06-02-PLAN.md** — Mouse interaction & move execution (Wave 1) ✓ COMPLETE
- [x] **06-04-PLAN.md** — Engine wiring gap closure ✓ COMPLETE
- [ ] **06-05-PLAN.md** — Click offset & turn management gap closure (Wave 1)

### Phase 07 (AI Interface + Game State) — Not started
### Phase 08 (Game Control) — Not started

*Roadmap created: 2026-03-23*
*Phase numbering continues from v0.1 (v0.1 ended at 04.1)*
