# Pitfalls Research: PyQt6 UI + Engine + AI Integration

**Domain:** Xiangqi game engine with PyQt6 GUI and pluggable AI
**Researched:** 2026-03-23
**Confidence:** MEDIUM (PyQt6 patterns verified via established community resources; AI/engine integration patterns are well-established from chess programming community; RL-specific concerns verified from literature)

---

## Critical Pitfalls

### Pitfall 1: QThread Subclass Anti-Pattern — Slots Live in the Wrong Thread

**What goes wrong:**
A `QThread` subclass defines `pyqtSlot`-decorated methods. These slots live in the main thread (where the `QThread` object lives by default in Python), not in the worker thread. Calling them from the worker thread via `emit()` queues the signal to the main thread's event loop, which is correct for some patterns but incorrect for worker-side logic that must run in the background.

The result: a signal emitted from the worker thread triggers a slot running in the main thread — which is fine for results — but any logic that should happen *inside* the worker (e.g., `self._engine.legal_moves()`) is called in the main thread instead, defeating the entire purpose of threading.

**Why it happens:**
Qt documentation for `QThread` is confusing. The canonical Python pattern (worker object + `moveToThread`) is not obvious from the C++ docs. The natural subclass `QThread` and override `run()` pattern is subtly wrong for Python object lifetime management.

**Prevention:**
Use the **worker-object pattern**:

```python
# WRONG — slots defined on QThread live in main thread
class MyThread(QThread):
    @pyqtSlot()
    def do_work(self):          # runs in main thread!
        ...

# CORRECT — worker object moves to thread
class Worker(QObject):
    finished = pyqtSignal()
    move_ready = pyqtSignal(int)   # move encoding

    def __init__(self, engine):
        super().__init__()
        self._engine = engine       # passed in, shared reference

    @pyqtSlot()
    def compute_move(self):
        moves = self._engine.legal_moves()
        best = random.choice(moves)  # or alpha_beta_search
        self.move_ready.emit(best)
        self.finished.emit()

# Wiring:
thread = QThread()
worker = Worker(engine)
worker.moveToThread(thread)
thread.started.connect(worker.compute_move)  # NOT worker.do_work() called directly
worker.finished.connect(thread.quit)
```

The worker object lives in the worker thread. Slots on the worker run in the worker thread. Signals *from* the worker (like `move_ready`) cross the thread boundary to the main thread's slots (like UI update methods).

**Detection:**
- Add a `thread=QThread.currentThread()` log in every slot and verify the thread identity
- If a "slow" slot runs in the main thread, the UI will freeze even though it's inside a `QThread`

**Phase to address:** v0.3 PyQt6 UI — first time any threading is introduced.

---

### Pitfall 2: AI Returns Illegal Move — The Engine Must Always Validate

**What goes wrong:**
An AI (RandomAI, AlphaBetaAI, MCTS) computes a move and returns it to the UI, which applies it directly to the engine. The AI returns `(7, 42)` (from row 7 to square 42) but the Horse on square 7 is actually blocked — the move is illegal. The UI applies the illegal move and the game state diverges from the engine's record. In the worst case, the UI reflects a piece in a position the engine would never allow, and subsequent legal-move highlighting is wrong.

**Why it happens:**
The AI computes moves from a board state snapshot. Between the moment the AI samples a move and the moment the UI calls `engine.apply(move)`, the position has not changed (human hasn't played). But the AI might still generate an illegal move due to a bug, or return a move that was legal in a slightly different position, or (more commonly) the AI interface encodes moves differently from the engine's `encode_move()` format.

**Prevention — mandatory two-layer validation:**

```python
class BaseAI(ABC):
    @abstractmethod
    def select_move(self, board: np.ndarray, turn: int) -> int:
        """Returns a 16-bit move integer. MUST be engine.is_legal() before apply()."""
        raise NotImplementedError

# In the UI controller:
class GameController:
    def _on_ai_move_ready(self, move: int):
        # Layer 1: format validation (encoding sanity check)
        if not self._is_well_formed(move):
            return  # drop illegal encoding

        # Layer 2: legal move validation (authoritative)
        if not self._engine.is_legal(move):
            # CRITICAL: log and fallback to random legal move
            legal = self._engine.legal_moves()
            move = random.choice(legal) if legal else None
            log.error(f"AI returned illegal move {move}, fell back to {legal}")
        if move is not None:
            self._engine.apply(move)       # only now is it safe
            self._update_ui()
```

The fallback to a random legal move is essential: crashing the UI is worse than silently correcting a bad AI move during development.

**Detection:**
- Unit test every AI implementation: generate 1000 random positions, call `ai.select_move()`, assert `engine.is_legal(move)` for every result
- Add a runtime guard: if `engine.is_legal(move)` is False, log at ERROR level and fall back

**Phase to address:** v0.3 PyQt6 UI — define the AI interface protocol before any AI implementation.

---

### Pitfall 3: Race Condition — AI Thread Reads Engine State While UI Is Mutating It

**What goes wrong:**
Human clicks a square to move a piece. The UI calls `engine.apply(move)` in the main thread. The AI worker thread is already running `alpha_beta_search(engine)` and has captured a reference to `engine` (or `engine.board`). The AI's search function reads `engine.board` at the same time the main thread is mutating it. Python's GIL provides some protection but does not guarantee atomicity for compound operations — the AI may read a partially-updated board state (e.g., piece moved from source but not yet cleared from destination).

In practice this manifests as: AI searches a position that never existed in the game tree, returns a move based on corrupted state, and either the move is illegal (caught by Pitfall 2) or it is legal but semantically wrong (AI thought a piece was somewhere it wasn't).

**Why it happens:**
The engine holds mutable state (`XiangqiState.board`) shared between threads. The worker thread holds a direct Python object reference. Even with the GIL, a thread switch between `board[fr, fc] = 0` and `board[tr, tc] = piece` causes the reading thread to see half-written state.

**Prevention — three options, in order of preference:**

**Option A: Snapshot pass (simplest, recommended for v0.3):**
Before starting the AI worker, copy the engine state. Pass the *snapshot* to the AI. The AI never touches the live engine.

```python
class GameController:
    def start_ai_turn(self):
        # Snapshot BEFORE handing to worker
        snapshot = {
            'board': self._engine.board.copy(),
            'turn': self._engine.turn,
        }
        self._worker.compute_move(snapshot)   # AI gets snapshot, not live engine
```

The UI still calls `self._engine.apply(move)` on the live engine after the AI returns. The AI never modifies state.

**Option B: Read lock on engine (if AI must read live state):**
Use `threading.Lock` around all engine reads and writes. The AI acquires a read lock; the UI acquires a write lock. This requires careful lock management and is prone to deadlocks if slots call engine methods while holding locks.

**Option C: Immutable game state object (best for long-term):**
The engine exposes only immutable snapshots. Every turn, the UI copies the current position into an immutable `XiangqiPosition` dataclass. The AI receives and operates on this immutable object. Applying moves always creates a new engine instance rather than mutating the existing one.

**Recommendation for v0.3:** Use Option A. The AI receives a `board: np.ndarray` snapshot and `turn: int`. It returns a move integer. The UI validates and applies to the live engine. This keeps the AI stateless (easy to test) and avoids all shared-mutability issues.

**Detection:**
- Race conditions are intermittent and hard to reproduce deterministically
- Add `threading.current_thread().ident` logs on all engine method calls
- If the same `engine.board` is passed to both AI and UI without a snapshot boundary, flag as high risk

**Phase to address:** v0.3 PyQt6 UI — the threading model must be designed before the AI controller is wired.

---

### Pitfall 4: Event Loop Blocking — Neural Network or Search Freezes the UI

**What goes wrong:**
The user clicks "New Game" or the AI begins thinking. The UI freezes — the board does not render, buttons do not respond, the window cannot be moved. In severe cases (first PyTorch MPS call), the freeze lasts 5-10 seconds while the GPU kernel compiles.

**Why it happens:**
Any long-running Python computation on the main thread blocks the Qt event loop. The Qt event loop processes UI events (paint, mouse, keyboard) and signal/slot deliveries. When it is blocked, the GUI becomes unresponsive. PyTorch MPS has significant startup overhead for the first kernel compilation.

**Prevention:**
Never run AI computation on the main thread. Use `QThread` + `worker.moveToThread()` (see Pitfall 1). The AI computation runs in the worker thread; the main thread event loop stays responsive. Connect worker signals to UI update slots:

```python
# Worker emits result
self.move_ready.connect(self._on_ai_move_ready)  # _on_ai_move_ready runs in main thread (safe for UI)

# Worker signals it is done
self.finished.connect(self._on_ai_computation_done)
```

For PyTorch MPS specifically, warm up the device at startup:
```python
# At application startup (once, before any game):
dummy = torch.zeros(1, device='mps')
# First real call now takes milliseconds, not seconds
```

**Detection:**
- If the UI is unresponsive for >200ms during normal play, a computation is blocking the main thread
- Watch for: clicking a piece causes a 1+ second freeze (legal move generation on main thread), clicking "AI vs AI" causes a freeze (search on main thread)

**Phase to address:** v0.3 PyQt6 UI — all AI computation must be off the main thread from day one.

---

### Pitfall 5: Garbage Collection of Widgets While They Are Referenced

**What goes wrong:**
A `BoardWidget` holds a reference to the engine via `self._engine`. The main window creates a `BoardWidget`, then later replaces it with a different widget. Python's garbage collector runs and, because no other reference exists to the old `BoardWidget`, it is collected — which triggers `deleteLater()` on the Qt widget. This is correct behavior. But if the AI worker thread holds a callback reference to the old `BoardWidget`, or if the old `BoardWidget`'s `paintEvent` is still scheduled in the event loop, behavior is undefined. In practice: the new board renders but occasionally "flickers" back to the old board state for one frame.

**Why it happens:**
Qt's parent-child ownership model and Python's reference counting interact in subtle ways. Python's `gc` may run at unpredictable times. A Qt widget that is still referenced by a Python object but has been `deleteLater()`'d by Qt enters a half-dead state.

**Prevention:**
- Never store a direct reference to a UI widget in a worker thread. Pass only serializable data (move integers, board snapshots) via signals.
- Explicitly call `widget.deleteLater()` before replacing a widget in a layout. This schedules deletion in the event loop after all pending events for that widget are processed.
- Keep strong references to widgets that are actively displayed; only release them explicitly when replaced.

**Detection:**
- Occasional visual artifacts after switching views or resetting the game
- `RuntimeError: wrapped C/C++ object has been deleted` — indicates a Python reference to a deleted Qt object was used

**Phase to address:** v0.3 PyQt6 UI — architecture review when implementing game reset and view switching.

---

### Pitfall 6: Tight Coupling — AI Directly Instantiated Inside UI

**What goes wrong:**
The `GameController` class contains:
```python
self._ai = RandomAI(self._engine)
```
The `RandomAI` constructor takes the live `XiangqiEngine` instance. Replacing `RandomAI` with `AlphaBetaAI` requires editing `GameController`. Worse, `AlphaBetaAI` might have different constructor arguments (search depth, evaluation function), so every AI swap requires code changes in multiple places.

**Why it happens:**
Without a defined AI interface, each AI is a special case. The UI controller becomes a switch statement for AI types, and every new AI requires editing the controller.

**Prevention — define a strict AI protocol:**
```python
from abc import ABC, abstractmethod
import numpy as np

class AIPlayer(ABC):
    """Pluggable AI interface. All AI implementations inherit from this."""

    @abstractmethod
    def compute_move(self, board: np.ndarray, turn: int) -> int:
        """
        Compute and return the best move.

        Args:
            board: 10x9 numpy array (np.int8), current position snapshot.
                   NEVER modify this array.
            turn:  +1 for red to move, -1 for black to move.

        Returns:
            A 16-bit move integer (from_sq | (to_sq << 9)).
            The returned move is NOT guaranteed legal.
            The caller MUST validate with engine.is_legal() before apply().

        Threading: This method runs in the worker thread.
        It must not mutate any shared state.
        """
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        """Reset internal state (e.g., transposition table, move counter)."""
        raise NotImplementedError
```

Every AI implementation (RandomAI, AlphaBetaAI, MCTSAI, RLAgent) satisfies this interface. The `GameController` holds `self._ai: AIPlayer` and never needs to know which subclass it is.

**Detection:**
- If `isinstance(self._ai, XxxAI)` appears in the controller, the coupling is too tight
- If changing the AI requires editing the controller's `__init__`, the interface is insufficient

**Phase to address:** v0.3 PyQt6 UI — define `AIPlayer` protocol before writing any concrete AI class.

---

### Pitfall 7: AI Interface Returns Mutable Board Reference (Snapshot Violation)

**What goes wrong:**
The engine's `board` property returns the live `np.ndarray`:
```python
@property
def board(self) -> np.ndarray:
    return self._state.board   # returns the LIVE array, not a copy
```
The AI receives this reference. The UI thread mutates the board via `apply()`. The AI thread reads from the same array simultaneously. Result: corrupt state reads (Pitfall 3).

**Why it happens:**
For performance, the engine returns the raw array rather than a copy. This is a deliberate optimization for internal use — but it makes the board unsafe to share across threads.

**Prevention:**
The `XiangqiEngine.board` property already returns the raw array. The `GameController` must call `.copy()` before passing to the AI worker:

```python
# In GameController.start_ai_turn():
snapshot = self._engine.board.copy()   # immutable snapshot
turn = self._engine.turn
self._worker.compute_move(snapshot, turn)
```

Document this requirement in the `AIPlayer` protocol docstring. Consider adding a `.snapshot()` method to the engine that returns a fully-isolated copy (board + turn + move_history) to make the boundary explicit.

**Detection:**
- Search for all call sites of `engine.board` — any that pass it to another thread without `.copy()` are bugs
- Add a runtime assertion: if `np.shares_memory(board_snapshot, engine.board)`, raise a `RuntimeError`

**Phase to address:** v0.3 PyQt6 UI — audit all engine.board consumers for thread safety.

---

## Moderate Pitfalls

### Pitfall 8: Human Move Applied Without Pre-Validation, UI and Engine Desync

**What goes wrong:**
The user drags a piece from A3 to A5. The UI immediately updates the piece position on screen. Then the UI calls `engine.apply(move)`. If the move is illegal, `apply()` raises `ValueError`. The UI has already rendered the illegal move and must roll back. Rollback logic is missing or buggy — the UI shows an illegal position.

**Why it happens:**
UI optimism: render first, validate second. Fine for a responsive UI, but rollback is an afterthought.

**Prevention:**
Always validate before rendering:

```python
def on_piece_dropped(self, from_sq: int, to_sq: int):
    move = encode_move(from_sq, to_sq)
    if not self._engine.is_legal(move):
        self._reject_move_animation(from_sq)   # snap back
        self._highlight_legal_moves(from_sq)  # show why it failed
        return
    # Legal: animate and apply
    self._animate_move(from_sq, to_sq)
    self._engine.apply(move)
    self._advance_turn()
```

**Phase to address:** v0.3 PyQt6 UI — implement legal-move pre-validation before drag-and-drop rendering.

---

### Pitfall 9: Engine State Embedded in QGraphicsItems

**What goes wrong:**
A `PieceItem` (a `QGraphicsPolygonItem` subclass) stores the piece position as its own `self._row` and `self._col`. The board state lives in two places: `XiangqiEngine.board` and the visual `PieceItem` objects. When the engine advances a turn, the UI must synchronize all piece items. If synchronization is incomplete, the visual state diverges from the engine state — the most dangerous kind of bug because it is invisible to the engine's own validation.

**Why it happens:**
Natural OO design: each piece item knows where it is. The problem is that there are now two sources of truth for piece positions.

**Prevention:**
Treat the engine as the single source of truth. The UI renders *from* the engine state:

```python
def render_board(self):
    """Re-render entire board from engine state. Called after every move."""
    # Remove all existing piece items
    for item in self._scene.items():
        self._scene.removeItem(item)
    # Re-add from engine
    for sq in range(90):
        r, c = divmod(sq, 9)
        piece = self._engine.board[r, c]
        if piece != 0:
            self._add_piece_item(r, c, piece)
```

This is slightly slower than incremental updates but eliminates all synchronization bugs. Profile it; for a 90-square board, full re-render is fast enough.

**Phase to address:** v0.3 PyQt6 UI — design the board rendering as a pure function of engine state.

---

### Pitfall 10: Testing Engine Only Through the UI (No Isolation)

**What goes wrong:**
The project has 179 tests for the rule engine. Adding the PyQt6 UI, all subsequent tests go through the UI: click here, verify board updates there. The engine's 179 passing tests provide no coverage for the UI-integrated path because the UI tests exercise the UI, not the engine's internal API. A regression in `XiangqiEngine.apply()` is not caught because the UI tests use `GameController._engine`, which is a different code path than the unit tests.

**Why it happens:**
As the UI is built, developers naturally add integration tests that exercise the full stack. The engine's unit tests are written once and never touched. But integration tests are slower and less targeted — they cannot cover edge cases the way unit tests do.

**Prevention:**
Maintain two separate test suites:

| Suite | Scope | Engine Coverage | Speed |
|-------|-------|-----------------|-------|
| `tests/test_engine.py` | Engine in isolation | 100% — 179 tests | <1s |
| `tests/test_ui.py` | UI widget in isolation (mock engine) | 0% engine | <100ms |
| `tests/test_integration.py` | Full stack (real engine + real UI) | partial | >1s |

The `tests/test_ui.py` suite uses a `MockEngine` that implements the same interface as `XiangqiEngine`:

```python
class MockEngine:
    """Implements the XiangqiEngine interface for UI testing without engine dependencies."""
    def __init__(self):
        self.board = np.zeros((10, 9), dtype=np.int8)
        self.turn = 1

    def apply(self, move: int) -> int: ...
    def is_legal(self, move: int) -> bool: ...
    def legal_moves(self) -> List[int]: ...
    def is_check(self) -> bool: ...
    def result(self) -> str: ...
```

The UI is instantiated with `BoardWidget(engine=MockEngine())`. This allows testing UI behavior (animations, highlighting, signal emission) without the engine. The integration test suite uses real `XiangqiEngine` instances to catch wiring bugs between UI and engine.

**Phase to address:** v0.3 PyQt6 UI — set up the test architecture before writing the first UI test.

---

### Pitfall 11: AI Computes on Stale Position (No Turn Barrier)

**What goes wrong:**
Human plays a move. AI worker starts computing. Before the AI finishes, the human clicks "Undo" or "Reset". The AI worker is still running against the old position snapshot. When it finally returns a move, it is a move for the wrong position. The UI may apply it to the new (reset) position, corrupting state.

**Why it happens:**
The AI worker runs asynchronously. There is no mechanism to tell a running worker "this result is no longer needed."

**Prevention:**
Use a **generation counter** (also called a version number):

```python
class GameController:
    def __init__(self):
        self._generation = 0      # increments on every game reset or undo

    def start_ai_turn(self):
        gen = self._generation
        board = self._engine.board.copy()
        turn = self._engine.turn
        self._worker.compute_move(gen, board, turn)

    def on_human_move(self):
        self._generation += 1     # invalidate all in-flight AI computations
        self._engine.apply(self._current_move)
        self._update_ui()

    @pyqtSlot(int, int)
    def _on_ai_move_ready(self, gen: int, move: int):
        if gen != self._generation:
            return   # stale result — discard silently
        # Apply move...
```

The worker's result carries the generation number. If the generation has changed, the result is discarded.

**Phase to address:** v0.3 PyQt6 UI — implement generation counter before AI vs human gameplay is tested.

---

## Minor Pitfalls

### Pitfall 12: Legal Move Cache Not Invalidated on Engine State Change

**What goes wrong:**
The UI caches `legal_moves()` at the start of a turn for highlight rendering. On a human move, the UI calls `engine.apply(move)` which changes the engine state. The UI continues to show highlights from the previous position because the cache was never invalidated.

**Prevention:**
The cache should be a method, not a stored value:

```python
def legal_moves_for(self, from_sq: int) -> List[int]:
    """Legal moves from a specific square. Always computed fresh from current engine state."""
    all_moves = self._engine.legal_moves()
    return [m for m in all_moves if (m & 0x1FF) == from_sq]
```

If performance demands caching, invalidate explicitly:
```python
def on_engine_changed(self):
    self._legal_move_cache = None
```

**Phase to address:** v0.3 PyQt6 UI — first time legal move highlighting is implemented.

---

### Pitfall 13: PyQt Signal/Slot Type Mismatches Cause Silent Failures

**What goes wrong:**
A signal is emitted with an `int` argument but the slot expects a `str`. PyQt6 may silently fail to connect, or coerce the type incorrectly, or raise a `TypeError` at runtime. In Python's dynamic type system, these mismatches are not caught at definition time.

**Prevention:**
Use `pyqtSignal` type annotations explicitly:
```python
class Worker(QObject):
    move_ready = pyqtSignal(int)        # explicitly typed
    search_progress = pyqtSignal(int)  # percentage complete
```

Use `Qt.ConnectionType.UniqueConnection` to detect duplicate connections:
```python
self.worker.move_ready.connect(
    self._on_move_ready,
    type=Qt.ConnectionType.UniqueConnection
)
```

**Phase to address:** v0.3 PyQt6 UI — code review checklist item for all signal/slot connections.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| First QThread wiring | Pitfall 1 (QThread subclass anti-pattern) + Pitfall 4 (event loop blocking) | Use worker-object + moveToThread from the start; never subclass QThread |
| First AI integration | Pitfall 2 (illegal moves from AI) + Pitfall 7 (mutable board reference) | Define AIPlayer protocol with explicit snapshot semantics; always validate before apply |
| First async gameplay | Pitfall 3 (race condition) + Pitfall 11 (stale position) | Use snapshot pass (not shared references); add generation counter |
| First UI test suite | Pitfall 10 (no engine isolation) | MockEngine interface; unit tests for engine remain authoritative |
| First view switching/reset | Pitfall 5 (GC of live widgets) + Pitfall 9 (dual state) | Explicit deleteLater(); treat engine as single source of truth |

---

## Anti-Features — Things to Explicitly NOT Build

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|---------------------|
| AI holds a direct reference to `XiangqiEngine` | Creates shared mutability across threads; makes AI stateful and hard to test | AI receives immutable board snapshots |
| Engine stores UI widget references | Tight coupling; engine cannot be used headlessly | Engine is UI-agnostic; UI observes engine state |
| Human move rendered before engine validation | Rollback complexity; desync risk | Validate-then-render pattern |
| Global mutable game state singleton | Race conditions; hard to test multiple games | Pass engine instance explicitly |
| AI search runs to completion with no abort mechanism | User clicks "New Game" but must wait for search to finish | Check generation counter inside search loop; yield to event loop periodically |

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| AI returns illegal move (not validated) | MEDIUM | Add `engine.is_legal()` guard; log all occurrences; run 1000-move regression test |
| Race condition in engine access | HIGH | Audit all engine consumers for thread boundaries; introduce snapshot pass; add threading tests |
| Event loop blocking | LOW | Move computation to QThread; add startup GPU warmup |
| GC of referenced widget | MEDIUM | Audit all cross-thread references; use deleteLater(); add "widget deleted" assertion |
| Engine state in UI items | HIGH | Refactor rendering to be pure function of engine state; add integration test with undo/redo |
| Stale AI result applied to wrong position | MEDIUM | Add generation counter; add integration test: "undo during AI thinking" |

---

## Sources

- KDAB: "The Eight Rules of Multithreaded Qt" (https://www.kdab.com/the-eight-rules-of-multithreaded-qt/) — canonical Qt threading rules [HIGH confidence]
- Real Python: "Use PyQt's QThread to Prevent Freezing GUIs" (https://realpython.com/python-pyqt-qthread/) — worker object pattern [HIGH confidence]
- PythonGUIs: "Multithreading PyQt6 applications with QThreadPool" (https://www.pythonguis.com/tutorials/multithreading-pyqt6-applications-qthreadpool/) [HIGH confidence]
- Stack Overflow: "Python PyQt6 deleteLater() and child widgets" (https://stackoverflow.com/questions/73258934/python-pyqt6-deletelater-and-child-widgets) [MEDIUM confidence]
- Qt Forum: "PySide6 memory model and QObject lifetime management" (https://forum.qt.io/topic/154590/pyside6-memory-model-and-qobject-lifetime-management) [MEDIUM confidence]
- ChessProgramming Wiki: UCI protocol for engine/AI interface (https://www.chessprogramming.org/UCI) — inspiration for pluggable AI protocol [HIGH confidence]
- python-chess architecture: abstract MoveGen and Board separation (https://python-chess.readthedocs.io/) — inspiration for clean interface design [HIGH confidence]
- AlphaZero (Science, 2018) — legal move masking pattern; illegal moves handled via policy softmax masking [HIGH confidence]

---

*Pitfalls research for: v0.3 PyQt6 UI + AI integration — RL-Xiangqi*
*Researched: 2026-03-23*
