# Milestone v0.2 — Project Summary

**Generated:** 2026-03-26
**Purpose:** Team onboarding and project review

---

## 1. Project Overview

**RL-Xiangqi** is a heterogeneous multi-agent reinforcement learning platform for Chinese Chess (Xiangqi). Human players compete against AI via a desktop UI, while the AI — driven by multiple "piece agents" — learns continuously during play. The core value: **AI visibly improves as it plays against humans**.

**v0.2 Milestone Goal:** Human-vs-AI board interface (PyQt6) with RandomAI opponent and extensible AI interface.

This milestone delivers:
- A fully playable PyQt6 GUI with click-to-move interaction
- AI opponent (RandomAI) that makes legal moves
- Turn management, game-over detection, and status bar indicators
- New Game and Undo controls with keyboard shortcuts

**Status:** Complete. All 4 phases delivered, all 13 v1 requirements satisfied.

---

## 2. Architecture & Technical Decisions

- **PyQt6 QGraphicsView + QGraphicsScene** for board rendering
  - **Why:** QGraphicsView provides hardware-accelerated scene graph ideal for chess board; QRectF/QLineF wrappers required for float coordinates in PyQt6
  - **Phase:** 05

- **Three-layer separation:** UI (`src/xiangqi/ui/`) — Controller (`src/xiangqi/controller/`) — AI (`src/xiangqi/ai/`) — Engine (`src/xiangqi/engine/`)
  - **Why:** Decouples rendering, game orchestration, and AI logic; enables independent testing and future替换
  - **Phase:** 05-08

- **QThread + moveToThread() for AI off the main thread**
  - **Why:** Qt-recommended pattern for background computation; prevents GUI freezing during AI "thinking"
  - **Phase:** 07

- **EngineSnapshot frozen dataclass for thread safety**
  - **Why:** Engine reference never crosses thread boundary; snapshot holds board.copy() and list of legal moves as immutable data
  - **Phase:** 07

- **is_legal() guard on every AI-returned move before apply()**
  - **Why:** Validates AI output before executing; prevents corrupted state from bad AI moves
  - **Phase:** 07

- **Generation counter for stale AI result discarding**
  - **Why:** Prevents race condition where AI computes on old board state; stale results discarded by generation comparison
  - **Phase:** 07

- **Click-to-move (not drag-and-drop)**
  - **Why:** Simpler implementation for MVP; drag adds complexity without gameplay benefit
  - **Phase:** 06

- **Gold ring (0.85×cell) for selection + gold dot (0.50×cell) for legal targets**
  - **Why:** Gold (#FFD700) traditional highlight color; two sizes differentiate selection from targets
  - **Phase:** 06

- **Double-step undo (human + AI move together)**
  - **Why:** More intuitive UX — undo "one turn" rather than one ply; restores board to player's previous decision point
  - **Phase:** 08

- **Random side assignment at game start (50% human=red, 50% human=black)**
  - **Why:** Tests both sides of the game; increases variety and surfaces bugs in turn management
  - **Phase:** 08

---

## 3. Phases Delivered

| Phase | Name | Status | One-Liner |
|-------|------|--------|-----------|
| 05 | Board Rendering | ✅ Complete | PyQt6 QGraphicsView renders 9×10 board with green felt, grid, river, palace diagonals, 32 Chinese-character pieces |
| 06 | Piece Interaction | ✅ Complete | Click-to-select with gold ring, legal move dots, click-to-move, alternating red/black gameplay |
| 07 | AI Interface + Game State | ✅ Complete | AIPlayer ABC + EngineSnapshot + RandomAI, status bar turn indicator, "AI 思考中..." indicator, game-over QMessageBox |
| 08 | Game Control | ✅ Complete | Toolbar (新对局 + 悔棋), Ctrl+N/Z shortcuts, double-step undo, random side assignment, undo_available signal |

---

## 4. Requirements Coverage

All 13 v1 requirements satisfied:

- ✅ **UI-01**: PyQt6 QGraphicsView + QGraphicsScene renders 9×10 board (grid + river + palace diagonals)
- ✅ **UI-02**: Pieces via Piece enum Chinese characters, red/black fill colors
- ✅ **UI-03**: Click己方棋子选中，合法走法目标格高亮显示
- ✅ **UI-04**: Click合法目标格执行走法，调用 engine.apply()
- ✅ **UI-05**: Click非法目标格时取消选子
- ✅ **UI-06**: 当前回合提示（红方/黑方）
- ✅ **UI-07**: 对局结束提示（红胜/黑胜/和棋），QMessageBox弹窗
- ✅ **AI-01**: AIPlayer 抽象基类，suggest_move(snapshot) -> Move | None
- ✅ **AI-02**: EngineSnapshot 数据类，线程安全（frozen=True, board.copy()）
- ✅ **AI-03**: RandomAI 实现，黑方随机选合法走法
- ✅ **AI-04**: AI 走子时 UI 显示"AI 思考中..."
- ✅ **UI-08**: 新对局按钮，重置到初始局面
- ✅ **UI-09**: 悔棋功能，支持连续悔棋

**v1 Requirements: 13/13 complete. Coverage: 100%.**

---

## 5. Key Decisions Log

| ID | Decision | Phase | Rationale |
|----|----------|-------|-----------|
| D-01 | PyQt6 float coordinate wrappers (QRectF/QLineF) | 05 | PyQt6 drawLine/fillRect require float wrappers for non-integer coordinates |
| D-02 | Green felt #7BA05B board, deep green #2D5A1B grid lines | 05 | Traditional Chinese chess visual aesthetic |
| D-03 | Palace diagonals at center columns 3-5 (x=3.6/5.6*cell) | 05 | Palace X-pattern must be in the center zone, not at side columns |
| D-04 | Gold ring #FFD700 for selection, gold dots for legal targets | 06 | Standard high-contrast highlight; two sizes distinguish intent |
| D-05 | Gold ring z=1.1 (above pieces), dots z=0.5 (below pieces) | 06 | Layering ensures ring doesn't obscure piece; dots don't distract |
| D-06 | mapToScene() for coordinate conversion | 06 | Replaces hardcoded offset; handles dynamic viewport centering automatically |
| D-07 | Turn-aware selection: `piece_value * engine.turn > 0` | 06 | Enables alternating red/black gameplay without separate two-player toggle |
| D-08 | QThread + moveToThread() for AI threading | 07 | Qt official recommended pattern; queued connections for thread-safe signals |
| D-09 | EngineSnapshot frozen=True dataclass with board.copy() | 07 | Engine reference never crosses thread boundary; snapshot is immutable snapshot |
| D-10 | is_legal() guard before every AI move apply | 07 | Validates AI output before executing; fail-fast on bad AI moves |
| D-11 | Generation counter for stale AI result discarding | 07 | Prevents race conditions from AI computing on outdated board state |
| D-12 | QMessageBox.information() for game over | 07 | Qt modal dialog; blocks until user acknowledges |
| D-13 | Double-step undo (human + AI together) | 08 | Undo "one turn" rather than one ply — more intuitive for user |
| D-14 | Random side assignment each new game | 08 | 50% human=red, 50% human=black; increases variety and test coverage |
| D-15 | undo_available signal controls undo button enabled state | 08 | Decoupled: controller emits signal, UI responds; no direct state inspection |
| D-16 | New game always available during AI thinking | 08 | User can interrupt any game state; no artificial constraints |
| D-17 | sync_state(engine.state) called after undo() | 08 | Gap closure 08-03: board must reflect engine state after undo |

---

## 6. Tech Debt & Deferred Items

### Gaps Found and Resolved

| Phase | Gap | Fix | Status |
|-------|-----|-----|--------|
| 05 | Palace diagonals at side columns (0-2, 6-8) instead of center (3-5) | Plan 05-07: corrected x-coordinates to 3.6/5.6*cell | ✅ Closed |
| 05 | Missing horizontal line at row 4 | Plan 05-08: removed `if row == 4: continue` | ✅ Closed |
| 05 | Vertical lines overflow to y=10.6*cell | Plan 05-09: changed to 9.6*cell | ✅ Closed |
| 06 | Hardcoded click offset (103.5, 2.0) caused misalignment | Plan 06-05: replaced with mapToScene() | ✅ Closed |
| 06 | Turn-unaware selection broke alternating gameplay | Plan 06-05: added `piece_value * engine.turn > 0` check | ✅ Closed |
| 08 | sync_state not called after undo, board stale | Plan 08-03: added board.sync_state(engine.state) | ✅ Closed |
| 08 | Continuous undo deadlock when human plays Black | Plan 08-04: restore AI turn after undo when human is black | ✅ Closed |

### Deferred to Future Milestones

- **Drag-and-drop** — MVP click-to-move is sufficient; drag adds complexity
- **将军 visual highlight** — red/green indicator when king is in check
- **Move animation** — slide effect when pieces move (v0.3)
- **Sound effects** —落子音效 (v0.3)
- **Captured pieces display** — 被吃棋子区域 (v0.2+)
- **Move history** — 走法历史记录 (v0.3)
- **Timer system** — 计时系统 (out of scope)
- **PGN/棋谱 export** — future feature
- **AlphaBetaAI / MCTSAI** — Phase 09+ (v1.0)
- **Gymnasium RL environment** — v0.3
- **Heterogeneous piece agents** — v1.0
- **AI 思考 animation** (spinning indicator) — v0.3
- **AI 思考 timeout handling** — v0.3

### Lessons Learned (Process)

1. **UAT catches what automated tests miss** — visual bugs (palace diagonals, click offset) surfaced only in human testing
2. **Gap closure is a feature** — 4 of 12 plans were gap closures; this is normal and healthy
3. **Float coordinate wrappers are a PyQt6 gotcha** — QLineF/QRectF required for non-integer coordinates
4. **Turn-aware selection must be explicit** — initial implementation assumed red-only; needed `engine.turn` multiplication check
5. **Double-step undo surfaces subtle AI turn restoration bugs** — continuous undo with Black-side human revealed a deadlock in AI turn triggering

---

## 7. Getting Started

### Run the project

```bash
conda activate xqrl
python -m src.xiangqi.ui.main
```

### Key directories

| Path | Purpose |
|------|---------|
| `src/xiangqi/engine/` | Pure-Python Xiangqi engine (v0.1 — 207 tests) |
| `src/xiangqi/ui/` | PyQt6 UI — board rendering, piece items, main window |
| `src/xiangqi/controller/` | Game orchestration — turn management, AI wiring |
| `src/xiangqi/ai/` | AI interface — AIPlayer ABC, EngineSnapshot, RandomAI |
| `tests/` | pytest suite (AI + Controller + UI) |

### Run tests

```bash
conda activate xqrl
pytest tests/ -v
```

### Architecture overview

```
MainWindow (src/xiangqi/ui/main.py)
  └── GameController (src/xiangqi/controller/game_controller.py)
        ├── XiangqiEngine (src/xiangqi/engine/engine.py)
        ├── QXiangqiBoard (src/xiangqi/ui/board.py)
        └── AIWorker + RandomAI (src/xiangqi/ai/)
```

### Where to look first

- **New to the codebase?** Start with `src/xiangqi/ui/main.py` — entry point and top-level composition
- **Want to understand the AI interface?** Read `src/xiangqi/ai/base.py` — AIPlayer ABC and EngineSnapshot
- **Want to change piece rendering?** `src/xiangqi/ui/board_items.py` — PieceItem class
- **Want to add a new AI type?** Subclass `AIPlayer` in `src/xiangqi/ai/`, implement `suggest_move(snapshot)`

---

## Stats

- **Timeline:** 2026-03-23 → 2026-03-26 (3 days)
- **Phases:** 4/4 complete
- **Plans:** 12/12 complete (including 4 gap closures)
- **Commits:** 111
- **Files changed:** 101 (+15,594 / -122 lines)
- **Contributors:** 1 (rorschach_zhao@outlook.com)
- **Test suite:** 28 new tests (UI), 22 new tests (AI/Controller) — all passing
- **Requirements:** 13/13 v1 requirements satisfied

---

*Summary generated: 2026-03-26*
*Source artifacts: ROADMAP.md, REQUIREMENTS.md, PROJECT.md, RETROSPECTIVE.md, phase CONTEXT/VERIFICATION/SUMMARY files*
