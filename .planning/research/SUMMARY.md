# Project Research Summary

**Project:** RL-Xiangqi v0.2 PyQt6 UI
**Domain:** Desktop board game UI with pluggable AI
**Researched:** 2026-03-23
**Confidence:** HIGH (PyQt6 patterns verified via multiple open-source projects and official docs; engine API confirmed from existing v0.1 codebase; threading patterns are canonical Qt practices)

---

## Executive Summary

RL-Xiangqi v0.2 adds a PyQt6 desktop UI on top of the existing v0.1 XiangqiEngine. The product is a minimal human-vs-AI Chinese Chess board where Red (human) plays first and Black (AI) responds with random legal moves. Experts build board game UIs with `QGraphicsView` + `QGraphicsScene` for rendering, a dedicated controller (not the UI itself) for game state management, and a worker-object pattern for background AI computation. The recommended stack is PyQt6 6.8+ with Python 3.12, using a `GameController` that owns the engine instance and mediates all UI-engine communication via `pyqtSignal`.

The biggest risk in this phase is not the UI rendering -- it is threading. The AI must run in a `QThread` worker (via `moveToThread`, never a `QThread` subclass), the engine must never be shared mutable state between threads, and every AI move must be validated against `engine.is_legal()` before `engine.apply()`. Research across all 4 documents converges on one structural decision: the `AIPlayer` / `EngineSnapshot` / `GameController` interface is the most critical deliverable because it is the foundation every future AI (Alpha-Beta, MCTS, RL) plugs into. The UI itself is straightforward by comparison.

---

## Key Findings

### Recommended Stack

PyQt6 6.8+ (minimum) on Python 3.12. PyQt6 6.7.x has Python 3.13 breakage; 6.8+ is fixed. Use `QGraphicsView` + `QGraphicsScene` for the board (built-in hit-testing, layering, coordinate mapping). Use `QGraphicsPixmapItem` for piece sprites with a font fallback stack (BabelStone Xiangqi Unicode font first, then CJK system font, then Chinese characters from the existing engine's `Piece.__str__`). Never use Qt's `QDrag` system for piece movement -- use manual mouse event handling on the graphics items instead. The canonical PyQt threading pattern is a bare `QThread` + a `QObject` worker moved onto it with `moveToThread()`; slots on the worker run in the worker thread.

**Core technologies:**
- **PyQt6 6.8+**: UI framework -- `QGraphicsView` for board rendering, `QThread` for AI offloading
- **Python 3.12**: Project default; fully compatible with PyQt6 6.8+
- **XiangqiEngine (existing)**: v0.1 engine already provides `apply()`, `legal_moves()`, `is_legal()`, `is_check()`, `result()`, `board` (np.ndarray), `to_fen()` -- zero work needed here
- **NumPy**: Already in stack; `board.copy()` is the thread-safety boundary for the AI

### Expected Features

**Must have (table stakes):**
- Board geometry: 9x10 grid, river, two palace diagonal boxes, drawn once as cached `QPixmap` background
- Piece rendering: read `engine.board` (np.ndarray), place one `QGraphicsPixmapItem` per non-zero square
- Click-to-select + click-to-move: click own piece to select, click destination to move -- no drag-and-drop in v0.2
- Legal move highlighting: on piece selection, compute `engine.legal_moves()`, decode destinations, show semi-transparent dot overlays -- the single highest-UX-value feature for the MVP
- Turn management: toggle after every `apply()`, disable board interaction during AI turn
- AI move execution: `GameController` QThread calls AI plugin, validates move, applies to engine, signals UI
- New Game / Reset: `engine.reset()` + re-render all state
- Game over display: check `engine.result()` after each apply; show status text or dialog

**Should have (competitive / worth the effort for v0.2):**
- Captured pieces display: two panels (one per side) showing captured piece symbols from `apply()` return value
- In-check visual warning: if `engine.is_check()` is True, flash the General's square or show a status banner
- Current turn indicator: colored label showing "Red to move" / "Black to move"

**Defer (v1.0+):**
- Drag-and-drop (click-to-move is sufficient for v0.2 validation)
- Move history log (WXF or ICCS notation)
- Board flip (rotate perspective)
- Time controls / clocks
- PGN / XQF game save/load
- Sound effects
- Multiple game tabs
- Hint / undo AI moves
- Network / online play

### Architecture Approach

Three-layer separation enforced strictly: **UI layer** (`src/xiangqi/ui/`) owns Qt widgets only and never imports the engine or AI; **Engine layer** (`src/xiangqi/engine/`) is pure Python with zero UI dependencies (already exists from v0.1); **AI layer** (`src/xiangqi/ai/`) receives immutable `EngineSnapshot` dataclasses and returns `Move` objects, never touching the engine. The only layer that imports from all three is `src/xiangqi/controller/` (`GameController` + `GameStateMachine` + `AIWorker`).

The `GameController` owns the engine instance, implements a `GameStateMachine` with states `WAITING_INPUT / AI_THINKING / ANIMATING / GAME_OVER`, and exposes all UI communication through a `GameSignals` object with typed `pyqtSignal` definitions. The `EngineSnapshot` dataclass (frozen, immutable) captures `board.copy()`, `turn`, `legal_moves`, `is_in_check`, `move_history`, `result`, and `fen` at the moment the AI is invoked -- this is the thread-safety boundary. The `AIPlayer` abstract base class defines `suggest_move(snapshot) -> Move | None`; any implementation (RandomAI, AlphaBetaAI, MCTSAI, RLAgent) satisfies this interface with no controller changes.

### Critical Pitfalls

1. **QThread subclass anti-pattern**: Subclassing `QThread` and putting slots on it causes those slots to run in the main thread. Always use a bare `QThread` + `QObject` worker + `moveToThread()`. Prevention: worker slots run in the thread the QObject lives on.

2. **AI returns illegal move**: Any AI implementation can bug out and return an illegal move encoding. The controller MUST call `engine.is_legal(move)` before `engine.apply()`. If illegal, fall back to a random legal move and log at ERROR level. Prevention: two-layer validation is mandatory, not optional.

3. **Race condition on engine state**: The AI thread and UI thread share `XiangqiEngine` if the engine reference is passed directly. Always pass a snapshot (`engine.board.copy()` + metadata) to the AI worker; never pass the live engine. Prevention: `EngineSnapshot` dataclass created on the main thread before `moveToThread()`.

4. **Event loop blocking**: Any AI computation on the main Qt thread freezes the UI. RandomAI is fast enough to inline, but any RL or Alpha-Beta search must use the worker thread. Prevention: worker object + `moveToThread()` from day one, even for RandomAI, so the pattern is established.

5. **Dual sources of truth for board state**: If piece positions live in both `XiangqiEngine.board` and in `QGraphicsItem` attributes, they can diverge after moves or undos. Prevention: treat the engine as the single source of truth; `render_board()` re-reads `engine.board` and rebuilds the scene from scratch after every state change.

6. **Stale AI result applied to wrong position**: If a human clicks "Undo" or "Reset" while the AI is thinking, the AI's result is for a position that no longer exists. Prevention: generation counter -- each game/undo increments a counter; AI results carry the generation number; stale results are silently discarded.

---

## Implications for Roadmap

### Phase 1: Board Rendering Shell (static board + pieces)

**Rationale:** Validate the visual output before wiring any interaction. Board geometry, coordinate mapping, and piece placement are the foundation -- if these are wrong, everything else is wrong. This phase is independent and low-risk.

**Delivers:** A `BoardWidget` (`QGraphicsView`) that renders the static board (grid, river, palace diagonals, file/rank labels) as a cached `QPixmap`, and renders all 32 pieces from a hardcoded starting position using `QGraphicsPixmapItem`. No interaction yet.

**Avoids:** Anti-pattern: do NOT wire `engine.board` reads in this phase -- hardcode the starting array so the renderer can be validated independently.

### Phase 2: Interaction Loop (click-to-select, legal highlighting, click-to-move)

**Rationale:** The interaction loop is the core user experience and the most fragile part architecturally. Wire it to the real engine from day one to catch encoding/decoding bugs early. This also validates the coordinate mapping (`px` to `from_sq/to_sq`) against the engine's flat-square convention.

**Delivers:** `BoardWidget` with `mousePressEvent` that emits `(from_sq, to_sq)` pairs. `GameController` with a minimal `apply_user_move()` that calls `engine.is_legal()` then `engine.apply()`. `board_changed` signal triggers `render_board()` from `engine.board`. Legal move highlighting via `engine.legal_moves()` on piece selection. Turn management: disable board when `engine.turn` is Black.

**Uses:** `GameSignals` -- define typed `pyqtSignal` objects upfront even though only `board_changed` and `move_applied` are wired in this phase.

**Avoids:** Pitfall 5 (dual state) -- render from engine state on every signal. Pitfall 8 (optimistic rendering) -- validate `is_legal()` before any visual update.

### Phase 3: AI Abstraction + GameController + RandomAI

**Rationale:** The AI interface is the most critical deliverable and must be designed before any AI implementation. `AIPlayer` ABC, `EngineSnapshot`, and `Move` must be in place. `GameController` wires engine + AI + state machine together. Black AI plays random legal moves -- this is the end-to-end validation that the threading model works.

**Delivers:** `src/xiangqi/ai/base.py` with `AIPlayer`, `EngineSnapshot`, `Move`. `src/xiangqi/controller/game_controller.py` with `GameStateMachine` (4 states). `src/xiangqi/ai/random_ai.py` implementing `AIPlayer`. `AIWorker(QObject)` that receives `EngineSnapshot`, calls `ai.suggest_move()`, emits `move_ready`. `GameController` wires `user_move_requested` -> `apply()` -> `ai_thinking_started` -> `AIWorker` -> `move_ready` -> `apply()` -> `board_changed`. Generation counter to discard stale results.

**Avoids:** Pitfall 1 (QThread subclass) -- use `moveToThread()`. Pitfall 2 (illegal moves) -- validate before `apply()`. Pitfall 3 (race condition) -- snapshot pass before worker start. Pitfall 4 (event loop block) -- worker thread from day one. Pitfall 6 (tight coupling) -- `AIPlayer` ABC is the only interface the controller knows.

### Phase 4: Game Polish + End-to-End Validation

**Rationale:** Add the remaining UX features that make the board feel complete: captured pieces, in-check warning, game over dialog, new game button. Validate the full human-vs-AI loop with 5+ complete games.

**Delivers:** Captured pieces panels updated from `engine.apply()` return value. In-check banner from `engine.is_check()`. Game over dialog from `engine.result()`. New game resets engine + UI state. Full end-to-end test: 5 complete games with no crashes, no illegal states.

**Avoids:** Pitfall 10 (no test isolation) -- add `MockEngine` for UI unit tests; keep engine unit tests authoritative.

### Phase Ordering Rationale

Board rendering (Phase 1) must precede any interaction wiring (Phase 2). Interaction wiring against the live engine (Phase 2) must precede AI integration (Phase 3) because AI integration depends on the controller already being able to apply and display moves. Game polish (Phase 4) is last because it depends on all prior phases being wired. The AI interface design (`AIPlayer` / `EngineSnapshot`) belongs in Phase 3, not Phase 2, because the AI interface is the primary deliverable of Phase 3 -- it cannot be an afterthought.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (AI Abstraction)**: The `EngineSnapshot` design and `AIPlayer` protocol are well-specified by research, but the exact signal wiring between `GameController` and `AIWorker` (especially the `request_ai_move` vs `thread.started` pattern) should be validated with a minimal prototype before full implementation.
- **Phase 4 (Polish)**: Unicode piece rendering with BabelStone Xiangqi font availability and graceful fallback should be validated on the target platform (Windows).

Phases with standard patterns (skip research-phase):
- **Phase 1 (Board Rendering)**: `QGraphicsView` + `QPixmap` background is a well-documented Qt pattern. `drawBackground()` override or cached pixmap approach is implementation preference.
- **Phase 2 (Interaction Loop)**: Click-to-select + legal highlighting is a standard board game pattern; the coordinate mapping (`px` <-> flat square index) is confirmed from the existing engine API.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | PyQt6 6.8+ with Python 3.12 confirmed via PyQt community docs and Stack Overflow. QGraphicsView + QThread patterns canonical from Qt official docs and multiple PyQt tutorials. |
| Features | HIGH | Board game feature set is well-understood; click-to-move vs drag-and-drop trade-off clearly reasoned. Anti-features explicitly defined. |
| Architecture | HIGH | `GameController` + `GameStateMachine` + `AIWorker` pattern is standard Qt practice. `EngineSnapshot` is GoF Memento pattern. Three-layer separation is clean software engineering. |
| Pitfalls | HIGH | All 13 pitfalls identified with concrete prevention strategies. Threading patterns verified against official Qt docs, KDAB, and Real Python. |

**Overall confidence:** HIGH

### Gaps to Address

- **Piece asset rendering**: Whether to use Unicode chess symbols (U+1FA60 range) with BabelStone Xiangqi font or Chinese characters via system CJK font needs a quick platform test. Implementation should use a font-stack fallback: BabelStone Xiangqi -> Noto Sans CJK SC -> Chinese characters from `Piece.__str__`.
- **Animation smoothness**: Piece animation duration (200-500ms) and easing are not researched; implementer preference for v0.2. `QPropertyAnimation` or `setPos` in a `QTimer.singleShot` are both viable.
- **PySide6 vs PyQt6 choice**: STACK.md recommends PyQt6 for ecosystem breadth. If LGPL licensing becomes relevant later, PySide6 is API-compatible and can be swapped without architectural changes.

---

## Sources

### Primary (HIGH confidence)
- Qt Official Documentation: QThread + signals/slot threading model (doc.qt.io/qt-6/threads-qobject.html) -- canonical threading rules
- KDAB: "The Eight Rules of Multithreaded Qt" -- PyQt threading best practices
- Real Python: "Use PyQt's QThread to Prevent Freezing GUIs" -- worker object pattern
- PythonGUIs: "Multithreading PyQt6 applications with QThreadPool" -- threading patterns
- Qt Official: QThread subclassing warning (doc.qt.io/qt-6/qthread.html) -- explicit warning against subclassing
- python-chess architecture: abstract MoveGen and Board separation -- clean interface design inspiration
- XiangqiEngine API: confirmed from `src/xiangqi/engine/engine.py` (existing v0.1 codebase) -- HIGH confidence

### Secondary (MEDIUM confidence)
- ChessQ (github.com/walker8088/ChessQ) -- active PyQt Xiangqi project, last updated Feb 2025
- sahinakkaya/chess PyQt6 implementation -- open-source PyQt chess reference
- Compart.com: Xiangqi Unicode Characters (U+1FA60-U+1FA6D) -- Unicode range confirmed
- hartwork/xiangqi-setup -- SVG rendering approach for xiangqi boards
- Medium: "A Clean Architecture for a PyQt GUI Using the MVP Pattern" -- design pattern article

### Tertiary (LOW-MEDIUM confidence)
- PyQt6 Python 3.13 compatibility reports (Stack Overflow / forum.qt.io) -- user reports, not official
- PhysicsKnight MCTS-Minimax -- reference for algorithm structure only
- game-ai-client PyPI -- generic SDK, not xiangqi-specific

---

*Research completed: 2026-03-23*
*Ready for roadmap: yes*
