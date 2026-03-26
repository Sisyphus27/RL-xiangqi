# Phase 07: AI Interface + Game State — Research

**Researched:** 2026-03-25
**Domain:** PyQt6 threading, AI abstraction layer, game state UI
**Confidence:** HIGH (PyQt6 patterns verified via official docs and established community resources; AI/engine integration patterns from ARCHITECTURE.md research)

---

## Summary

Phase 07 implements the AI player integration, turn/game state UI, and the GameController orchestration layer. The core technical challenge is the QThread + moveToThread() pattern for off-main-thread AI computation while maintaining thread safety through EngineSnapshot data copies.

**Primary recommendation:** Follow the worker-object pattern exactly as specified in CONTEXT.md (D-04 to D-06). The EngineSnapshot must be a deep copy created on the main thread before passing to the AI worker. The GameController is the single orchestrator — it owns the engine instance, manages AI thread lifecycle, and emits all state-change signals.

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**UI Components:**
- **D-01:** Status bar via `QMainWindow.statusBar()` for turn indicator
- **D-02:** "AI 思考中..." shown in same status bar during black turn
- **D-03:** Game over via `QMessageBox.information()` modal

**AI Threading Model:**
- **D-04:** QThread + moveToThread() pattern (Qt official recommended)
- **D-05:** AI worker object calls `moveToThread(QThread)`, signals/slots for cross-thread
- **D-06:** Thread runs event loop, main thread receives results via queued connection

**AI Interface Design:**
- **D-07:** AIPlayer ABC with `suggest_move(snapshot: EngineSnapshot) -> int | None`
- **D-08:** EngineSnapshot contains board array copy, turn, legal_moves list (complete data copy, thread-safe)
- **D-09:** EngineSnapshot is dataclass holding numpy array copy, AI has read-only access
- **D-10:** RandomAI supports optional seed parameter (default None) for test reproducibility

**AI Error Handling:**
- **D-11:** AI-returned move validated with `engine.is_legal()` (is_legal guard)
- **D-12:** `is_legal()` failure raises ValueError, game terminates (development-phase early bug detection)

**State Flow:**
- **D-13:** User move -> check `result()` -> switch turn -> start AI (disable board interaction)
- **D-14:** AI move -> check `result()` -> switch turn -> re-enable board interaction
- **D-15:** AI timing: immediate execution after return, no artificial delay
- **D-16:** Game-over popup closes -> board stays in final state, await manual reset (Phase 08)

**Code Organization:**
- **D-17:** AI module in `src/xiangqi/ai/` directory (parallel with engine/, ui/)

**From Phase 06:**
- **D-18:** `QXiangqiBoard.set_interactive(False)` controls board interaction
- **D-19:** `QXiangqiBoard.move_applied` signal notifies external of move execution
- **D-20:** Turn switching via `engine.turn` property (+1 red, -1 black)

### Claude's Discretion

- EngineSnapshot dataclass field names
- Status bar text wording (e.g., "红方回合" vs "轮到红方")
- AI thinking text style (color, font)
- GameController class implementation details
- Signal naming style

### Deferred Ideas (OUT OF SCOPE)

- AlphaBetaAI / MCTSAI — Phase 09+
- Check visual highlight — Phase 08
- AI thinking animation (spinning) — v0.3
- AI timeout handling — v0.3

</user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AI-01 | AIPlayer ABC with `suggest_move(snapshot) -> Move \| None` | Standard Stack: ABC + dataclass pattern; Code Examples below |
| AI-02 | EngineSnapshot dataclass (board copy, turn, legal_moves — thread-safe) | Architecture Patterns: Snapshot pattern; Don't Hand-Roll section |
| AI-03 | RandomAI implementation, called on black turn, returns random legal move | Code Examples: RandomAI with seed |
| AI-04 | AI thinking indicator in UI (black turn shows "AI 思考中...") | Architecture Patterns: QThread worker flow |
| UI-06 | Turn indicator (红方回合 / AI 思考中...) | Code Examples: Status bar update |
| UI-07 | Game over modal (红胜/黑胜/和棋 via QMessageBox) | Code Examples: QMessageBox usage |

</phase_requirements>

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-qt (already in pyproject.toml) |
| Config file | None — see Wave 0 |
| Quick run command | `conda activate xqrl && pytest tests/ai/ -v -x` |
| Full suite command | `conda activate xqrl && pytest tests/ -v` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| AI-01 | AIPlayer ABC defines suggest_move signature | unit | `pytest tests/ai/test_base.py -x` | Wave 0 |
| AI-02 | EngineSnapshot captures complete state copy | unit | `pytest tests/ai/test_snapshot.py -x` | Wave 0 |
| AI-03 | RandomAI returns legal move, respects seed | unit | `pytest tests/ai/test_random_ai.py -x` | Wave 0 |
| AI-04 | "AI 思考中..." appears during black turn | integration | `pytest tests/ui/test_game_controller.py -x` | Wave 0 |
| UI-06 | Turn indicator updates after each move | integration | `pytest tests/ui/test_game_controller.py -x` | Wave 0 |
| UI-07 | Game over popup shows correct result | integration | `pytest tests/ui/test_game_controller.py -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/ai/ -v -x` (AI module tests only)
- **Per wave merge:** `pytest tests/ -v` (full suite)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/ai/__init__.py` — package init
- [ ] `tests/ai/test_base.py` — AIPlayer ABC contract tests
- [ ] `tests/ai/test_snapshot.py` — EngineSnapshot immutability/copy tests
- [ ] `tests/ai/test_random_ai.py` — RandomAI with seed reproducibility
- [ ] `tests/ai/conftest.py` — shared AI test fixtures
- [ ] `tests/controller/__init__.py` — package init
- [ ] `tests/controller/test_game_controller.py` — GameController integration tests
- [ ] Framework install: Already present (pytest, pytest-qt in pyproject.toml)

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyQt6 | 6.x | UI framework, QThread, signals/slots | Project-wide UI layer |
| numpy | 2.x | Board array in EngineSnapshot | Engine uses np.ndarray |
| abc (stdlib) | — | AIPlayer abstract base class | Python standard for interfaces |
| dataclasses (stdlib) | — | EngineSnapshot immutable snapshot | Clean data containers |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x | Unit/integration tests | All test files |
| pytest-qt | 4.x | PyQt6 widget testing | UI/controller tests |
| random (stdlib) | — | RandomAI move selection | RandomAI implementation |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| dataclass | NamedTuple | NamedTuple is immutable but less readable for complex types |
| QThread+moveToThread | QThreadPool | QThreadPool is for short tasks; persistent AI worker is simpler with dedicated thread |
| EngineSnapshot copy | Pass engine reference | Engine reference violates thread safety (see PITFALLS.md Pitfall 3) |

**Installation:**

```bash
# Already in pyproject.toml — no new dependencies needed
conda activate xqrl
```

---

## Architecture Patterns

### Recommended Project Structure

```
src/xiangqi/
├── engine/           # Phase 01-04 (complete, no changes)
│   ├── engine.py     # XiangqiEngine public API
│   ├── types.py      # Move encoding, Piece enum
│   └── ...
├── ui/               # Phase 05-06 (complete)
│   ├── board.py      # QXiangqiBoard + move_applied signal
│   ├── main.py       # MainWindow
│   └── ...
├── ai/               # Phase 07 NEW
│   ├── __init__.py
│   ├── base.py       # AIPlayer ABC, EngineSnapshot
│   └── random_ai.py  # RandomAI implementation
└── controller/       # Phase 07 NEW
    ├── __init__.py
    └── game_controller.py  # Orchestrator: engine + AI + UI signals
```

### Pattern 1: QThread Worker Object (D-04 to D-06)

**What:** Worker QObject moved to a QThread via `moveToThread()`. Thread runs event loop; worker slots execute in worker thread; signals cross thread boundary via queued connections.

**When to use:** All AI computation (RandomAI, future AlphaBeta, RL inference) must run off the main thread to prevent UI freezing.

**Example:**

```python
# src/xiangqi/controller/ai_worker.py
from PyQt6.QtCore import QObject, QThread, pyqtSignal

class AIWorker(QObject):
    """Worker object for AI computation in a background thread."""

    move_ready = pyqtSignal(int)  # Emits 16-bit move integer
    error = pyqtSignal(str)

    def __init__(self, ai_player, snapshot):
        super().__init__()
        self._ai = ai_player
        self._snapshot = snapshot

    def compute(self):
        """Slot called when thread starts. Runs in worker thread."""
        try:
            move = self._ai.suggest_move(self._snapshot)
            if move is not None:
                self.move_ready.emit(move)
        except Exception as e:
            self.error.emit(str(e))


# In GameController:
def _start_ai_turn(self):
    # 1. Create snapshot on main thread (thread-safe)
    snapshot = EngineSnapshot.from_engine(self._engine)

    # 2. Create worker + thread
    self._ai_thread = QThread()
    self._ai_worker = AIWorker(self._ai_player, snapshot)
    self._ai_worker.moveToThread(self._ai_thread)

    # 3. Wire signals
    self._ai_thread.started.connect(self._ai_worker.compute)
    self._ai_worker.move_ready.connect(self._on_ai_move_ready)
    self._ai_worker.error.connect(self._on_ai_error)

    # 4. Cleanup on finish
    self._ai_thread.finished.connect(self._ai_worker.deleteLater)
    self._ai_thread.finished.connect(self._ai_thread.deleteLater)

    # 5. Start
    self._ai_thread.start()
```

**Source:** Qt documentation, PITFALLS.md Pitfall 1

### Pattern 2: EngineSnapshot Immutable Copy

**What:** Dataclass holding a complete deep copy of engine state. Created on main thread, passed to AI worker, never mutated.

**When to use:** Every AI turn — snapshot before starting AI thread.

**Example:**

```python
# src/xiangqi/ai/base.py
from dataclasses import dataclass
from typing import List
import numpy as np

@dataclass(frozen=True)
class EngineSnapshot:
    """Immutable snapshot of engine state for thread-safe AI access."""
    board: np.ndarray       # Shape (10, 9), dtype=np.int8, DEEP COPY
    turn: int               # +1 = red, -1 = black
    legal_moves: List[int]  # Pre-computed legal move integers

    @classmethod
    def from_engine(cls, engine) -> "EngineSnapshot":
        """Create snapshot from engine. MUST be called on main thread."""
        return cls(
            board=engine.board.copy(),  # Deep copy!
            turn=engine.turn,
            legal_moves=engine.legal_moves(),
        )
```

**Source:** ARCHITECTURE.md EngineSnapshot pattern, PITFALLS.md Pitfall 3

### Pattern 3: GameController Orchestration

**What:** Single QObject that owns engine, AI player, and wires all signals. Central state machine for game flow.

**When to use:** This is the only place that imports both engine and AI.

**Example:**

```python
# src/xiangqi/controller/game_controller.py
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

class GameController(QObject):
    """Orchestrates engine, AI, and UI signals."""

    # Signals for UI to observe
    turn_changed = pyqtSignal(int)       # +1 red, -1 black
    game_over = pyqtSignal(str)          # result string
    ai_thinking_started = pyqtSignal()
    ai_thinking_finished = pyqtSignal()

    def __init__(self, engine, ai_player, board_widget, main_window):
        super().__init__()
        self._engine = engine
        self._ai_player = ai_player
        self._board = board_widget
        self._window = main_window
        self._ai_thread = None
        self._ai_worker = None

        # Wire board signal
        self._board.move_applied.connect(self._on_move_applied)

    @pyqtSlot(int, int, int)
    def _on_move_applied(self, from_sq: int, to_sq: int, captured: int):
        """User move completed. Check result, maybe start AI."""
        result = self._engine.result()
        if result != "IN_PROGRESS":
            self._handle_game_over(result)
            return

        # Switch turn indicator
        self.turn_changed.emit(self._engine.turn)

        # Start AI if black's turn
        if self._engine.turn == -1:
            self._start_ai_turn()

    def _start_ai_turn(self):
        """Launch AI computation in background thread."""
        self._board.set_interactive(False)  # D-18
        self.ai_thinking_started.emit()

        snapshot = EngineSnapshot.from_engine(self._engine)

        self._ai_thread = QThread()
        self._ai_worker = AIWorker(self._ai_player, snapshot)
        self._ai_worker.moveToThread(self._ai_thread)

        self._ai_thread.started.connect(self._ai_worker.compute)
        self._ai_worker.move_ready.connect(self._on_ai_move_ready)
        self._ai_thread.finished.connect(self._ai_worker.deleteLater)
        self._ai_thread.finished.connect(self._ai_thread.deleteLater)

        self._ai_thread.start()

    @pyqtSlot(int)
    def _on_ai_move_ready(self, move: int):
        """AI returned a move. Validate and apply."""
        # Clean up thread
        self._ai_thread.quit()
        self._ai_thread.wait(5000)
        self._ai_thread = None
        self._ai_worker = None

        self.ai_thinking_finished.emit()

        # D-11: is_legal guard
        if not self._engine.is_legal(move):
            raise ValueError(f"AI returned illegal move: {move}")

        # Apply via board (triggers move_applied signal)
        from_sq = move & 0x1FF
        to_sq = (move >> 9) & 0x7F
        self._board.apply_move(from_sq, to_sq)

        # Re-enable interaction
        self._board.set_interactive(True)

    def _handle_game_over(self, result: str):
        """Show game over popup."""
        self.game_over.emit(result)
```

**Source:** ARCHITECTURE.md GameController pattern

### Anti-Patterns to Avoid

- **QThread subclassing:** Override `run()` is error-prone. Use worker-object + `moveToThread()` instead. (PITFALLS.md Pitfall 1)
- **Passing engine reference to AI:** Creates shared mutable state across threads. Always use snapshot. (PITFALLS.md Pitfall 3)
- **Skipping is_legal() guard:** AI bugs corrupt game state. Always validate. (PITFALLS.md Pitfall 2)
- **UI calling engine directly:** Bypasses GameController, breaks signal flow. UI only emits signals.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Threading | Custom thread pool, QThread subclass | QThread + moveToThread() worker | Qt official pattern, avoids lifetime issues |
| State snapshot | Shallow copy, pickle | EngineSnapshot dataclass with np.copy() | Explicit thread-safety boundary |
| AI interface | Multiple AI classes with different signatures | AIPlayer ABC | Pluggable, testable, extensible |
| Game state machine | Scattered boolean flags | GameController with explicit flow | Single source of truth |

**Key insight:** The EngineSnapshot pattern is non-negotiable for thread safety. Never pass `engine.board` directly to the AI thread — always copy first.

---

## Common Pitfalls

### Pitfall 1: AI Returns Illegal Move

**What goes wrong:** AI (especially during development) returns a move that isn't in `engine.legal_moves()`. Applying it corrupts game state or raises ValueError.

**Why it happens:** AI computes from a snapshot; move encoding bugs; AI interface misunderstandings.

**How to avoid:** D-11 mandatory `is_legal()` guard before every `apply()`:

```python
if not self._engine.is_legal(move):
    raise ValueError(f"AI returned illegal move: {move}")
```

**Warning signs:** Game crashes after AI move; board shows illegal position.

### Pitfall 2: Race Condition — AI Reads Board While UI Mutates

**What goes wrong:** AI worker holds reference to `engine.board` (not a copy). Main thread applies user move. AI reads partially-updated board.

**Why it happens:** Forgetting to copy in `EngineSnapshot.from_engine()`.

**How to avoid:** Always use `engine.board.copy()` in snapshot creation. Verify with:

```python
# In tests:
snapshot = EngineSnapshot.from_engine(engine)
assert not np.shares_memory(snapshot.board, engine.board)
```

**Warning signs:** AI returns nonsensical moves; intermittent bugs.

### Pitfall 3: Thread Not Cleaned Up

**What goes wrong:** AI thread finishes but worker/thread objects not deleted. Memory leak; stale signals fire later.

**Why it happens:** Missing `deleteLater()` connections.

**How to avoid:** Always connect `thread.finished` to both `worker.deleteLater` and `thread.deleteLater`.

**Warning signs:** Increasing memory usage; signals firing unexpectedly.

### Pitfall 4: Status Bar Not Updating

**What goes wrong:** Turn indicator shows stale value after move.

**Why it happens:** Signal not connected; slot not called; wrong signal emission order.

**How to avoid:** Verify connection in `__init__`, emit signals after state change:

```python
# After applying move:
self.turn_changed.emit(self._engine.turn)  # Emit AFTER turn switches
```

**Warning signs:** Status bar text stuck on "红方回合" during black's turn.

---

## Code Examples

### AIPlayer ABC

```python
# src/xiangqi/ai/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import numpy as np

@dataclass(frozen=True)
class EngineSnapshot:
    """Thread-safe engine state snapshot."""
    board: np.ndarray       # (10, 9), int8, DEEP COPY
    turn: int               # +1 red, -1 black
    legal_moves: List[int]  # Pre-computed legal moves

    @classmethod
    def from_engine(cls, engine) -> "EngineSnapshot":
        return cls(
            board=engine.board.copy(),
            turn=engine.turn,
            legal_moves=list(engine.legal_moves()),
        )


class AIPlayer(ABC):
    """Abstract base for all AI implementations."""

    @abstractmethod
    def suggest_move(self, snapshot: EngineSnapshot) -> Optional[int]:
        """Select a move. Returns 16-bit move integer or None if no legal moves."""
        ...
```

**Source:** ARCHITECTURE.md AIPlayerBase pattern

### RandomAI Implementation

```python
# src/xiangqi/ai/random_ai.py
import random
from typing import Optional
from .base import AIPlayer, EngineSnapshot

class RandomAI(AIPlayer):
    """Random legal move selector."""

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def suggest_move(self, snapshot: EngineSnapshot) -> Optional[int]:
        if not snapshot.legal_moves:
            return None
        return self._rng.choice(snapshot.legal_moves)
```

**Source:** ARCHITECTURE.md RandomAI example, D-10 seed parameter

### Status Bar Turn Indicator

```python
# In GameController or MainWindow:
def _update_status_bar(self, turn: int, ai_thinking: bool = False):
    status = self._window.statusBar()
    if ai_thinking:
        status.showMessage("AI 思考中...")
    elif turn == 1:
        status.showMessage("红方回合")
    else:
        status.showMessage("黑方回合")

# Connect signals:
self.ai_thinking_started.connect(lambda: self._update_status_bar(-1, True))
self.ai_thinking_finished.connect(lambda: self._update_status_bar(self._engine.turn, False))
self.turn_changed.connect(lambda t: self._update_status_bar(t, False))
```

**Source:** D-01, D-02 status bar decisions

### Game Over Popup

```python
from PyQt6.QtWidgets import QMessageBox

def _show_game_over(self, result: str):
    """Show modal game over dialog."""
    result_text = {
        "RED_WINS": "红胜",
        "BLACK_WINS": "黑胜",
        "DRAW": "和棋",
    }.get(result, result)

    QMessageBox.information(
        self._window,
        "对局结束",
        result_text,
        QMessageBox.StandardButton.Ok,
    )
```

**Source:** D-03 QMessageBox decision

### AI Worker Thread Setup

```python
# src/xiangqi/controller/ai_worker.py
from PyQt6.QtCore import QObject, QThread, pyqtSignal

class AIWorker(QObject):
    move_ready = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, ai_player, snapshot):
        super().__init__()
        self._ai = ai_player
        self._snapshot = snapshot

    def compute(self):
        try:
            move = self._ai.suggest_move(self._snapshot)
            if move is not None:
                self.move_ready.emit(move)
        except Exception as e:
            self.error.emit(str(e))


# Usage in GameController:
def _start_ai_turn(self):
    snapshot = EngineSnapshot.from_engine(self._engine)

    self._ai_thread = QThread()
    self._ai_worker = AIWorker(self._ai_player, snapshot)
    self._ai_worker.moveToThread(self._ai_thread)

    # Wire: thread.start -> worker.compute -> move_ready -> on_ai_move_ready
    self._ai_thread.started.connect(self._ai_worker.compute)
    self._ai_worker.move_ready.connect(self._on_ai_move_ready)
    self._ai_worker.error.connect(self._on_ai_error)

    # Cleanup
    self._ai_thread.finished.connect(self._ai_worker.deleteLater)
    self._ai_thread.finished.connect(self._ai_thread.deleteLater)

    self._ai_thread.start()
```

**Source:** ARCHITECTURE.md QThread worker pattern, PITFALLS.md Pitfall 1

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| QThread subclass | Worker object + moveToThread | Qt 4.4+ | Proper thread affinity, safer lifetime |
| Pass engine to AI | EngineSnapshot copy | Phase 07 design | Thread safety guarantee |
| Boolean flags for state | GameController signal flow | Phase 07 design | Single source of truth |

**Deprecated/outdated:**
- `QThread.run()` override: Use worker object pattern instead
- Global engine singleton: Pass engine instance explicitly to GameController

---

## Open Questions

1. **GameController file location**
   - What we know: D-17 specifies AI in `src/xiangqi/ai/`
   - What's unclear: Should GameController be in `src/xiangqi/controller/` or `src/xiangqi/ui/`?
   - Recommendation: Create `src/xiangqi/controller/` per ARCHITECTURE.md, keeps UI layer clean

2. **MainWindow initialization order**
   - What we know: MainWindow currently creates engine + board in `__init__`
   - What's unclear: Does GameController own MainWindow or vice versa?
   - Recommendation: MainWindow owns GameController; GameController receives references to board and window

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PyQt6 | QThread, signals | Yes | 6.x | — |
| numpy | EngineSnapshot board | Yes | 2.x | — |
| pytest | AI unit tests | Yes | 8.x | — |
| pytest-qt | Controller integration tests | Yes | 4.x | — |

**Missing dependencies with no fallback:** None

**Missing dependencies with fallback:** None

---

## Sources

### Primary (HIGH confidence)

- `.planning/research/ARCHITECTURE.md` — QThread worker pattern, EngineSnapshot, GameController design
- `.planning/research/PITFALLS.md` — Threading pitfalls, is_legal guard, race conditions
- `src/xiangqi/engine/engine.py` — XiangqiEngine API: `apply()`, `legal_moves()`, `is_legal()`, `result()`, `turn`
- `src/xiangqi/ui/board.py` — `move_applied` signal, `set_interactive()`, `apply_move()`

### Secondary (MEDIUM confidence)

- `src/xiangqi/engine/types.py` — Move encoding: `encode_move()`, `rc_to_sq()`, `sq_to_rc()`
- `src/xiangqi/ui/main.py` — MainWindow structure, `statusBar()` access
- `tests/ui/conftest.py` — Existing pytest-qt fixtures pattern

### Tertiary (LOW confidence)

- None — all patterns verified from project files or prior research

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All dependencies already in project
- Architecture: HIGH — Patterns from verified ARCHITECTURE.md and PITFALLS.md
- Pitfalls: HIGH — Documented in PITFALLS.md with prevention strategies

**Research date:** 2026-03-25
**Valid until:** 30 days (stable PyQt6 patterns, project-specific decisions locked)
