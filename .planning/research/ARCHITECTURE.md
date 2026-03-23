# Architecture Research: UI / Engine / AI Integration

**Project:** RL-Xiangqi — PyQt6 Desktop Board + Pluggable AI
**Domain:** Desktop board game UI integration with pure-Python game engine and AI player component
**Researched:** 2026-03-23
**Confidence:** HIGH (all patterns are well-established Qt/software engineering practices; grounded in actual engine API)

---

## Recommended Architecture

### System Overview

```
Human player (drag-drop)                          AI player (background thread)
        │                                                      │
        ▼                                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            UI Layer (PyQt6)                                   │
│  ┌────────────────────┐  ┌───────────────────┐  ┌──────────────────────────┐  │
│  │   BoardWidget      │  │  GameStatusBar    │  │  ControlPanel            │  │
│  │  QGraphicsView     │  │  (turn, result)   │  │  (new, undo, redo)       │  │
│  └─────────┬──────────┘  └───────────────────┘  └──────────────────────────┘  │
│            │                                                                │
│            │              QSignal-based Observer Pattern                     │
│            │  (EngineObserver)          (EngineController)                   │
│            │◄───────────────────────────────┬─────────────────────────────►│
└────────────┼────────────────────────────────┼────────────────────────────────┘
             │                                │
             ▼                                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         Engine Layer                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        XiangqiEngine                                 │    │
│  │  apply(move)  legal_moves()  is_check()  result  undo()  redo()  │    │
│  │  board (np.ndarray)  turn (int)  move_history (list)              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                          AI Layer                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   AIPlayerBase  (abstract)                          │    │
│  │   async suggest_move(engine_state) -> Move                          │    │
│  └──────────────────────────┬──────────────────────────────────────────┘    │
│                             │                                                │
│         ┌───────────────────┼───────────────────────┐                       │
│         ▼                   ▼                       ▼                       │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────────┐             │
│  │ RandomAI    │   │ HeuristicAI  │   │ RLAgent (future)     │             │
│  └─────────────┘   └──────────────┘   └──────────────────────┘             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Owns | Communicates With |
|-----------|---------------|------|-------------------|
| `BoardWidget` | Render board, capture drag-drop, emit `square_clicked(from, to)` | Qt graphics items | `GameController` via signals only |
| `ControlPanel` | Buttons: new game, undo, redo, flip board, AI difficulty | Pushbuttons | `GameController` via signals only |
| `GameStatusBar` | Display: "Red to move", "Black wins", etc. | QLabel | `GameController` via signal |
| `GameController` | Orchestrate game state machine, own engine instance, route moves | `XiangqiEngine` instance, `AIPlayerBase` instance, `GameStateMachine` | UI via pyqtSignal; AI via async method call |
| `XiangqiEngine` | Rule enforcement, move application, board state, terminal detection | Board state, undo stack, repetition state | GameController via direct method calls |
| `AIPlayerBase` | Abstract interface: `suggest_move(engine) -> Move` | Nothing | GameController via method call + QThread |
| `GameStateMachine` | Manage WAITING_INPUT / AI_THINKING / ANIMATING transitions | Current state enum | GameController |

---

## Layer Separation

### The Three-Layer Contract

```
Layer 1: UI (PyQt6)
  - Owns ONLY Qt widgets
  - NEVER calls XiangqiEngine directly
  - NEVER creates AI instances
  - Reacts ONLY to pyqtSignal emissions from GameController
  - Sends user input ONLY as signals to GameController

Layer 2: Engine (XiangqiEngine)
  - Pure Python, zero UI dependencies
  - No signals, no threading, no GUI awareness
  - Driven entirely by GameController
  - Fully unit-testable without any Qt or AI imports

Layer 3: AI (AIPlayerBase + implementations)
  - Driven by GameController
  - Receives engine state via a clean snapshot (board copy + metadata dict)
  - NEVER mutates engine state directly
  - Returns a Move object to GameController, which applies it
```

**Why this contract matters for this project:** The engine already exists (`src/xiangqi/engine/engine.py`) with a clean API. Wrapping it in `GameController` is the only integration work needed. The engine's existing `apply(from_sq, to_sq)` signature maps directly to the `Move` abstraction needed by both UI and AI.

### Clean Imports

```
src/xiangqi/            # Engine layer — zero dependencies outside this tree
  engine/
    engine.py           # XiangqiEngine

src/ui/                 # UI layer
  main.py               # QApplication entry point
  board_widget.py       # QGraphicsView board
  control_panel.py      # Buttons
  status_bar.py         # Status display

src/ai/                 # AI layer
  base.py               # AIPlayerBase abstract class
  random_ai.py          # Random legal move
  heuristic_ai.py       # Material + positional scoring
  rl_agent.py           # Future: PyTorch policy network

src/controller/         # Bridge layer — the only place that imports all three
  game_controller.py    # GameController, GameStateMachine
  signals.py            # Shared pyqtSignal definitions
```

---

## AI Abstraction Interface

### `AIPlayerBase` Abstract Class

The AI layer is pluggable. Any AI implementation — random, heuristic, RL, or external engine — must conform to this interface:

```python
# src/ai/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
import numpy as np

@dataclass(frozen=True)
class Move:
    """Immutable move representation shared by UI, engine, and AI."""
    from_sq: int   # 0-89 flat square index
    to_sq: int     # 0-89 flat square index

    def encode(self) -> int:
        """Encode to the 16-bit integer used by XiangqiEngine."""
        return (self.from_sq & 0x1FF) | ((self.to_sq << 9) & 0xFE00)

    @classmethod
    def from_int(cls, encoded: int) -> "Move":
        from_sq =  encoded        & 0x1FF
        to_sq   = (encoded >> 9)  & 0x7F
        return cls(from_sq=from_sq, to_sq=to_sq)


@dataclass(frozen=True)
class EngineSnapshot:
    """Read-only snapshot of engine state for the AI.

    GameController copies these fields from XiangqiEngine before passing
    to the AI. The AI must NEVER mutate this snapshot or the engine.
    """
    board: np.ndarray          # shape (10, 9), dtype=int8, read-only view
    turn: int                  # +1 = red to move, -1 = black to move
    legal_moves: List[int]     # pre-computed legal move integers
    is_in_check: bool          # side to move is in check
    move_history: List[int]    # list of applied move integers
    result: str                # 'IN_PROGRESS' | 'RED_WINS' | 'BLACK_WINS' | 'DRAW'
    fen: str                   # WXF FEN string

    @classmethod
    def from_engine(cls, engine: XiangqiEngine) -> "EngineSnapshot":
        """Capture current engine state as an immutable snapshot."""
        return cls(
            board=np.array(engine.board, copy=True),
            turn=engine.turn,
            legal_moves=engine.legal_moves(),
            is_in_check=engine.is_check(),
            move_history=list(engine.move_history),
            result=engine.result(),
            fen=engine.to_fen(),
        )


class AIPlayerBase(ABC):
    """Abstract interface for all AI players.

    Concrete implementations:
      - RandomAI      (testing, baseline)
      - HeuristicAI   (material + positional scoring, human-readable)
      - RLAgent       (future: PyTorch policy network)

    The suggest_move() method is synchronous. For real AI implementations
    that take time to compute, GameController calls it in a QThread worker.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name shown in UI, e.g. 'Random AI' or 'RL Agent'."""
        ...

    @abstractmethod
    def suggest_move(self, snapshot: EngineSnapshot) -> Move | None:
        """Select a move from the given engine snapshot.

        Args:
            snapshot: Read-only state snapshot. The AI must NOT mutate it.

        Returns:
            Move chosen by the AI, or None if no legal moves (game over).

        Raises:
            No valid move in snapshot.legal_moves is an internal error —
            the AI should only be called when the game is ongoing.
        """
        ...

    def legal_moves_from_snapshot(self, snapshot: EngineSnapshot) -> List[Move]:
        """Utility: convert encoded ints to Move objects."""
        return [Move.from_int(m) for m in snapshot.legal_moves]
```

### Why `EngineSnapshot` instead of passing `XiangqiEngine`?

1. **AI must never hold a reference to the engine** — if an AI implementation accidentally calls `engine.apply()`, it corrupts game state outside GameController's management.
2. **Thread safety** — the AI runs in a QThread. The engine lives in the main thread. Passing a snapshot (plain dataclass) is inherently thread-safe; passing a live engine object invites race conditions.
3. **Reproducibility** — `EngineSnapshot.fen` and `move_history` are sufficient to reconstruct the exact position for logging, replay, or debugging.

### `suggest_move` Implementation Example: RandomAI

```python
# src/ai/random_ai.py
import random
from .base import AIPlayerBase, EngineSnapshot, Move

class RandomAI(AIPlayerBase):
    @property
    def name(self) -> str:
        return "Random AI"

    def suggest_move(self, snapshot: EngineSnapshot) -> Move | None:
        if not snapshot.legal_moves:
            return None
        chosen = random.choice(snapshot.legal_moves)
        return Move.from_int(chosen)
```

### `suggest_move` Implementation Example: HeuristicAI

```python
# src/ai/heuristic_ai.py
import random
from .base import AIPlayerBase, EngineSnapshot, Move

# Piece values (centipawns, Xiangqi scale)
_PIECE_VALUES = {0: 0, 1: 15000, 2: 200, 3: 200, 4: 400, 5: 900, 6: 450, 7: 100,
                 -1: 15000, -2: 200, -3: 200, -4: 400, -5: 900, -6: 450, -7: 100}

class HeuristicAI(AIPlayerBase):
    """Material + capture scoring. Good enough to beat a random player."""

    @property
    def name(self) -> str:
        return "Heuristic AI"

    def suggest_move(self, snapshot: EngineSnapshot) -> Move | None:
        if not snapshot.legal_moves:
            return None

        best_score = -1
        best_moves = []

        for encoded in snapshot.legal_moves:
            score = self._score_move(encoded, snapshot)
            if score > best_score:
                best_score = score
                best_moves = [encoded]
            elif score == best_score:
                best_moves.append(encoded)

        return Move.from_int(random.choice(best_moves))

    def _score_move(self, encoded: int, snapshot: EngineSnapshot) -> int:
        """Score a move: captures > checks > center control > random."""
        from_sq =  encoded        & 0x1FF
        to_sq   = (encoded >> 9)  & 0x7F
        fr, fc  = divmod(from_sq, 9)
        tr, tc  = divmod(to_sq, 9)
        captured = snapshot.board[tr, tc]

        # Capture value: prefer taking high-value pieces
        capture_score = _PIECE_VALUES[abs(captured)] * 1000 if captured != 0 else 0

        # Check bonus: moves that deliver check
        # (requires simulating the move — see Pitfall 1 below)
        check_bonus = 50 if snapshot.is_in_check else 0

        # Center/river control bonus
        center_bonus = 10 if 3 <= tr <= 6 and 2 <= tc <= 6 else 0

        return capture_score + check_bonus + center_bonus
```

---

## Observer Pattern for UI Reacting to Engine State

### Pattern: Qt Signal Observer (GameController = Subject)

The classic GoF Observer pattern implemented with Qt's signal/slot mechanism. `GameController` is the single source of truth; all UI widgets are observers.

**Rule:** UI widgets never poll engine state. They only update when GameController emits a signal.

```python
# src/controller/signals.py
from PyQt6.QtCore import QObject, pyqtSignal

class GameSignals(QObject):
    """pyqtSignal definitions for the GameController → UI communication channel.

    Defined as a standalone QObject so GameController can own one instance,
    and widgets can connect to it without importing GameController directly.
    """

    board_changed = pyqtSignal()          # Board needs full redraw
    move_applied = pyqtSignal(int, int)   # (from_sq, to_sq) for animation
    turn_changed = pyqtSignal(int)        # +1 = red, -1 = black
    check_changed = pyqtSignal(bool)      # is the side-to-move in check?
    result_changed = pyqtSignal(str)      # 'IN_PROGRESS' | 'RED_WINS' | etc.
    ai_thinking_started = pyqtSignal()    # AI started computing
    ai_thinking_finished = pyqtSignal()    # AI finished (emit even on cancel)
    move_hint_requested = pyqtSignal(int) # from_sq: highlight legal moves
```

### Signal Emission Contract

**Every public method on GameController that mutates engine state emits signals immediately:**

```python
# Pseudocode for the contract
def apply_user_move(self, from_sq: int, to_sq: int):
    move = encode_move(from_sq, to_sq)
    self._engine.apply(move)
    self._state_machine.transition("MOVE_APPLIED")
    self.signals.move_applied.emit(from_sq, to_sq)   # Trigger piece animation
    self.signals.board_changed.emit()                 # Trigger square highlights
    self.signals.turn_changed.emit(self._engine.turn)
    self.signals.check_changed.emit(self._engine.is_check())
    self.signals.result_changed.emit(self._engine.result())
    self._check_game_over()

def undo(self):
    self._engine.undo()
    self.signals.board_changed.emit()
    self.signals.turn_changed.emit(self._engine.turn)
    self.signals.result_changed.emit(self._engine.result())
```

### Why NOT use Qt's Model/View Architecture

Qt's Model/View (QAbstractItemModel, QTableView) is designed for tabular data with selection semantics. For a board game, it adds complexity without benefit:
- Piece positions are not rows/columns of a table
- Drag-and-drop in QTableView requires extensive custom event handling
- Custom widgets (QGraphicsView) are the correct tool for interactive board rendering

BoardWidget should subclass `QGraphicsView`, not `QAbstractItemModel`.

---

## Qt Signal/Slot for Decoupled Component Communication

### Connection Pattern

Widgets connect to `GameSignals` in their `__init__` (or via a `setup_connections(controller_signals)` helper):

```python
# Inside BoardWidget.__init__
def setup_connections(self, signals: GameSignals):
    signals.board_changed.connect(self._on_board_changed)
    signals.move_applied.connect(self._on_move_applied)
    signals.turn_changed.connect(self._on_turn_changed)
    signals.check_changed.connect(self._on_check_changed)
    signals.move_hint_requested.connect(self._on_hint_requested)
    signals.ai_thinking_started.connect(self._on_ai_thinking)
    signals.ai_thinking_finished.connect(self._on_ai_finished)

# Inside ControlPanel.__init__
def setup_connections(self, signals: GameSignals):
    signals.result_changed.connect(self._on_result_changed)
    signals.ai_thinking_finished.connect(self._on_ai_finished)
```

### Control Signal (UI → Controller)

User actions are emitted as signals from widgets and routed to GameController via a single slot:

```python
# src/controller/game_controller.py
class GameController(QObject):
    """Sole bridge between UI and engine/AI. Lives on the main Qt thread."""

    # Control signals from UI
    user_move_requested = pyqtSignal(int, int)  # (from_sq, to_sq)
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()
    new_game_requested = pyqtSignal()
    ai_toggle_requested = pyqtSignal(bool)      # enable/disable AI opponent
    ai_level_changed = pyqtSignal(str)          # 'random' | 'heuristic' | 'rl'

    # External signal bus (owned)
    signals: GameSignals

    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = GameSignals()
        self._engine = XiangqiEngine.starting()
        self._ai: AIPlayerBase | None = None
        self._state_machine = GameStateMachine()

        # Connect own control signals
        self.user_move_requested.connect(self._on_user_move)
        self.undo_requested.connect(self._on_undo)
        self.redo_requested.connect(self._on_redo)
        self.new_game_requested.connect(self._on_new_game)
        self.ai_toggle_requested.connect(self._on_ai_toggle)
        self.ai_level_changed.connect(self._on_ai_level_changed)
```

This pattern keeps UI code completely unaware of the engine and AI:
- `BoardWidget` only knows it emits `user_move_requested(from_sq, to_sq)`
- `BoardWidget` has no idea what happens next
- `GameController` decides whether to apply the move, reject it as illegal, or forward it to the AI

### Slot Decorator for Control Signal Handlers

```python
from PyQt6.QtCore import pyqtSlot

class GameController(QObject):
    @pyqtSlot(int, int)
    def _on_user_move(self, from_sq: int, to_sq: int):
        if self._state_machine.state != GameState.WAITING_INPUT:
            return  # Ignore clicks while AI is thinking or animating
        # Validate + apply + emit signals
        ...

    @pyqtSlot()
    def _on_undo(self):
        # Can be called anytime; guard in apply()
        ...
```

---

## Background AI Thread (QThread + Signals)

### Anti-Pattern to Avoid

Calling `ai.suggest_move(snapshot)` synchronously in an event handler blocks the Qt event loop. With a slow AI (RL inference: 50-500ms), the UI freezes.

### Correct Pattern: Dedicated AI Worker QThread

```
Main Thread (Qt event loop)          AI Thread (QThread)
─────────────────────────            ──────────────────────
GameController                         AIWorker
  │                                       │
  │  request_ai_move(snapshot) ──────────►│
  │                                       │  [run suggest_move()]
  │                                       │  [may take 50-500ms]
  │  ◄────────────── ai_move_ready(move) ─│
  │                                       │
  │  apply_move(move)                     │
  │  emit signals ──────────────────────────► [idle]
```

### Implementation

```python
# src/controller/ai_worker.py
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from .base import AIPlayerBase, EngineSnapshot, Move

class AIWorker(QObject):
    """QThread worker for running AI computation off the main thread.

    Lifetime: created when AI turn starts, destroyed when move is ready.
    Not reused across moves (avoids stale state issues).
    """

    move_ready = pyqtSignal(object)   # Move or None
    error = pyqtSignal(str)           # Exception message

    def __init__(self, ai: AIPlayerBase, snapshot: EngineSnapshot, parent=None):
        super().__init__(parent)
        self._ai = ai
        self._snapshot = snapshot

    def run(self):
        """Executed in the AI QThread when started via moveToThread()."""
        try:
            move = self._ai.suggest_move(self._snapshot)
            self.move_ready.emit(move)
        except Exception as exc:
            self.error.emit(str(exc))


# src/controller/game_controller.py
class GameController(QObject):
    signals: GameSignals

    def __init__(self, ...):
        ...
        self._ai_thread: QThread | None = None
        self._ai_worker: AIWorker | None = None

    def _start_ai_turn(self):
        """Launch AI computation in a background thread."""
        if self._state_machine.state != GameState.WAITING_INPUT:
            return

        if self._ai is None:
            return  # No AI enabled

        self._state_machine.transition("AI_START_THINKING")
        self.signals.ai_thinking_started.emit()

        # Build snapshot while still on main thread
        snapshot = EngineSnapshot.from_engine(self._engine)

        # Create worker + thread
        self._ai_thread = QThread()
        self._ai_worker = AIWorker(self._ai, snapshot)
        self._ai_worker.moveToThread(self._ai_thread)

        # Wire: thread starts → worker runs → move_ready signal
        self._ai_thread.started.connect(self._ai_worker.run)
        self._ai_worker.move_ready.connect(self._on_ai_move_ready)
        self._ai_worker.error.connect(self._on_ai_error)

        # Auto-cleanup when thread finishes
        self._ai_thread.finished.connect(self._ai_worker.deleteLater)
        self._ai_thread.finished.connect(self._ai_thread.deleteLater)

        self._ai_thread.start()

    @pyqtSlot(object)
    def _on_ai_move_ready(self, move: Move | None):
        """Called on main thread when AI has computed its move."""
        if self._ai_thread is not None:
            self._ai_thread.quit()
            self._ai_thread.wait(5000)  # 5s timeout
            self._ai_thread = None
            self._ai_worker = None

        self.signals.ai_thinking_finished.emit()

        if move is None:
            # Game over — no move returned
            return

        # Apply the AI move (same path as user move)
        self._apply_move(move.from_sq, move.to_sq)

    def _apply_move(self, from_sq: int, to_sq: int):
        """Internal: apply a move and emit all relevant signals."""
        encoded = encode_move(from_sq, to_sq)
        try:
            self._engine.apply(encoded)
        except ValueError:
            return  # Illegal — guard should have filtered this

        self._state_machine.transition("MOVE_APPLIED")
        self.signals.move_applied.emit(from_sq, to_sq)
        self.signals.board_changed.emit()
        self.signals.turn_changed.emit(self._engine.turn)
        self.signals.check_changed.emit(self._engine.is_check())
        self.signals.result_changed.emit(self._engine.result())
        self._check_game_over()
```

### Why Create a New Thread Per Move

Reusing a persistent QThread for AI computation introduces state-management complexity (the worker must reset its state between moves, and any exception in one move poisons the worker). For this project, creating a fresh thread per move is the correct tradeoff: the overhead of thread creation (~1ms) is negligible compared to AI computation time (50ms+), and the simplicity gain (each move = fresh state) is significant.

If AI computation is very fast (RandomAI: <1ms), skip the thread entirely and call it synchronously:

```python
def _start_ai_turn(self):
    if isinstance(self._ai, RandomAI):
        move = self._ai.suggest_move(EngineSnapshot.from_engine(self._engine))
        self._on_ai_move_ready(move)
    else:
        self._start_ai_background()
```

---

## Game State Machine

### States

```
                    ┌──────────────────────────┐
                    │      WAITING_INPUT        │◄─────────────────┐
                    │  (human to move or AI     │                  │
                    │   to move if AI enabled)  │                  │
                    └──────────────┬─────────────┘                  │
                                   │ user clicks / AI move ready    │
                    ┌──────────────▼─────────────┐                  │
                    │       AI_THINKING          │                  │
                    │  (AI computing in          │                  │
                    │   QThread)                 │                  │
                    └──────────────┬─────────────┘                  │
                                   │ AI returns move                 │
                    ┌──────────────▼─────────────┐                  │
                    │        ANIMATING           │                  │
                    │  (piece moving across      │                  │
                    │   board — 200-500ms)       │                  │
                    └──────────────┬─────────────┘                  │
                                   │ animation done                 │
                    ┌──────────────▼─────────────┐                  │
                    │       GAME_OVER            │                  │
                    │  (checkmate / draw /       │──────────────────┘
                    │   resignation)             │  new game
                    └─────────────────────────────┘
```

### State Definitions

| State | Entry Condition | Valid Transitions | UI Behavior |
|-------|----------------|-------------------|-------------|
| `WAITING_INPUT` | Game start, after animation, after undo | `→ AI_THINKING` (if AI turn and enabled), `→ ANIMATING` (user clicks) | Board accepts clicks; cursor shows selectable pieces |
| `AI_THINKING` | AI turn starts | `→ ANIMATING` (AI move returned) | "AI is thinking..." indicator; board non-interactive |
| `ANIMATING` | Move applied, animation queued | `→ WAITING_INPUT` (animation done), `→ GAME_OVER` (move ends game) | Piece animates; no input accepted |
| `GAME_OVER` | Terminal result detected | `→ WAITING_INPUT` (new game) | Result displayed; "New Game" highlighted |

### Implementation

```python
# src/controller/state_machine.py
from enum import Enum, auto

class GameState(Enum):
    WAITING_INPUT = auto()
    AI_THINKING  = auto()
    ANIMATING    = auto()
    GAME_OVER    = auto()

# Valid transitions: state -> set of valid next states
_VALID_TRANSITIONS: dict[GameState, set[GameState]] = {
    GameState.WAITING_INPUT: {GameState.AI_THINKING, GameState.ANIMATING, GameState.GAME_OVER},
    GameState.AI_THINKING:  {GameState.ANIMATING,   GameState.GAME_OVER, GameState.WAITING_INPUT},
    GameState.ANIMATING:    {GameState.WAITING_INPUT, GameState.GAME_OVER},
    GameState.GAME_OVER:    {GameState.WAITING_INPUT},
}

class GameStateMachine:
    def __init__(self):
        self._state = GameState.WAITING_INPUT

    @property
    def state(self) -> GameState:
        return self._state

    def transition(self, event: str):
        """Advance state machine based on an event string.

        Raises:
            ValueError: if the transition is not valid from the current state.
        """
        next_state = self._next_state(event)
        if next_state not in _VALID_TRANSITIONS.get(self._state, set()):
            raise ValueError(
                f"Invalid transition: {self._state.name} + {event} -> "
                f"{next_state.name} (valid: {self._valid_events(self._state)})"
            )
        self._state = next_state

    def _next_state(self, event: str) -> GameState:
        """Deterministic next state from current state + event."""
        table = {
            (GameState.WAITING_INPUT, "AI_START_THINKING"): GameState.AI_THINKING,
            (GameState.WAITING_INPUT, "USER_MOVE"):         GameState.ANIMATING,
            (GameState.AI_THINKING,   "MOVE_APPLIED"):       GameState.ANIMATING,
            (GameState.AI_THINKING,   "GAME_OVER"):          GameState.GAME_OVER,
            (GameState.ANIMATING,     "ANIMATION_DONE"):     GameState.WAITING_INPUT,
            (GameState.ANIMATING,     "GAME_OVER"):          GameState.GAME_OVER,
            (GameState.GAME_OVER,      "NEW_GAME"):           GameState.WAITING_INPUT,
        }
        return table.get((self._state, event), self._state)

    def _valid_events(self, state: GameState) -> list[str]:
        return [e for (s, e), n in table.items() if s == state]

    def can_accept_input(self) -> bool:
        """Convenience: is the board interactive in the current state?"""
        return self._state == GameState.WAITING_INPUT
```

### Why a Dedicated State Machine

Without it, guards against out-of-order actions are scattered across multiple methods as boolean flags:

```python
# Anti-pattern: scattered boolean flags
def _on_square_clicked(self, sq):
    if self._ai_thinking:  # scattered flag
        return
    if self._animating:    # another scattered flag
        return
    ...

# Correct: single source of truth
def _on_square_clicked(self, sq):
    if not self._state_machine.can_accept_input():
        return
    ...
```

A `GameStateMachine` class consolidates all state-related guards into one place, making it impossible to enter an illegal UI state.

---

## Recommended Directory Structure

```
D:/WorkSpace/RL-xiangqi/
├── src/
│   └── xiangqi/
│       ├── engine/              # v0.1 completed — no changes needed
│       │   ├── engine.py        # XiangqiEngine (already exists)
│       │   ├── state.py
│       │   ├── legal.py
│       │   ├── moves.py
│       │   ├── rules.py
│       │   ├── repetition.py
│       │   ├── endgame.py
│       │   ├── constants.py
│       │   ├── types.py
│       │   └── __init__.py
│       │
│       ├── ui/                  # NEW — PyQt6 presentation layer
│       │   ├── __init__.py
│       │   ├── main_window.py   # QMainWindow, layout assembly
│       │   ├── board_widget.py  # QGraphicsView board rendering
│       │   ├── piece_item.py    # QGraphicsPixmapItem for pieces
│       │   ├── control_panel.py # New Game, Undo, Redo, AI toggle
│       │   ├── status_bar.py    # Turn indicator, result display
│       │   └── assets/          # PNG piece images (64x64 recommended)
│       │       ├── red_king.png
│       │       ├── red_advisor.png
│       │       └── ...           # 14 piece images total
│       │
│       ├── ai/                   # NEW — Pluggable AI layer
│       │   ├── __init__.py
│       │   ├── base.py           # AIPlayerBase, EngineSnapshot, Move
│       │   ├── random_ai.py      # RandomAI
│       │   ├── heuristic_ai.py    # HeuristicAI
│       │   └── rl_agent.py        # Future: RLAgent (PyTorch)
│       │
│       └── controller/           # NEW — Bridge layer (only layer that
│           ├── __init__.py        # imports from engine + ai + ui)
│           ├── signals.py         # GameSignals (pyqtSignal definitions)
│           ├── state_machine.py   # GameStateMachine, GameState enum
│           ├── game_controller.py # GameController (QObject, owns engine + AI)
│           └── ai_worker.py        # AIWorker (QThread runner for slow AIs)
│
├── .planning/
│   └── research/
│       └── ARCHITECTURE.md        # This file
│
├── tests/
│   └── (existing test suite — no changes to engine tests)
│
├── pyproject.toml
└── uv.lock
```

### Structure Rationale

| Directory | Why | Dependencies |
|-----------|-----|-------------|
| `src/xiangqi/engine/` | Already exists; pure rules engine | Zero external dependencies |
| `src/xiangqi/ui/` | PyQt6 widgets only | PyQt6 only; no engine or AI imports |
| `src/xiangqi/ai/` | AI implementations only | numpy only (for board analysis) |
| `src/xiangqi/controller/` | Bridge: the only layer that imports engine + ai + ui | PyQt6, engine, ai |

The `controller/` package is intentionally thin (~300 lines total). It holds no game state of its own — only the `XiangqiEngine` instance and the `AIPlayerBase` reference.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: UI Calling Engine Directly

```python
# BAD — UI imports and calls engine directly
class BoardWidget(QGraphicsView):
    def mouseReleaseEvent(self, event):
        engine.apply(self._selected_move)  # WRONG

# GOOD — UI emits signal, controller applies
class BoardWidget(QGraphicsView):
    def mouseReleaseEvent(self, event):
        self.game_controller.user_move_requested.emit(from_sq, to_sq)
```

### Anti-Pattern 2: AI Mutating Engine State

```python
# BAD — AI holds engine reference and applies move itself
class BadAIAgent:
    def __init__(self, engine):
        self.engine = engine   # WRONG: AI now owns engine mutation

    def suggest_move(self):
        move = self._compute()
        self.engine.apply(move)  # Side effect! Controller doesn't know
        return move

# GOOD — AI returns Move; controller applies it
class GoodAIAgent:
    def suggest_move(self, snapshot):
        move = self._compute(snapshot)
        return move  # No side effects
```

### Anti-Pattern 3: QThread Subclassing

```python
# BAD — subclassing QThread is error-prone (override run(), start() semantics)
class AThread(QThread):
    def run(self):
        self._ai.suggest_move(...)

# GOOD — worker QObject moved to a QThread
class AIWorker(QObject):
    def run(self):
        self._ai.suggest_move(...)

worker = AIWorker(ai, snapshot)
thread = QThread()
worker.moveToThread(thread)
thread.started.connect(worker.run)
```

PyQt documentation explicitly warns against subclassing `QThread`. Use `QObject.moveToThread()` instead.

### Anti-Pattern 4: Missing Signal Cleanup on Controller Reset

```python
# BAD — signals not disconnected when AI is swapped
def set_ai(self, ai: AIPlayerBase):
    self._ai = ai   # Old worker thread still running, memory leak

# GOOD — terminate + wait old thread before setting new AI
def set_ai(self, ai: AIPlayerBase):
    if self._ai_thread is not None:
        self._ai_thread.quit()
        self._ai_thread.wait(5000)
    self._ai = ai
```

---

## Scalability Considerations

| Concern | At Human vs AI (v1) | At AI vs AI Self-Play | At RL Training Loop |
|---------|---------------------|----------------------|---------------------|
| AI thread | 1 QThread per move, destroy after use | Same | All AI calls are synchronous (no thread needed) |
| Engine instance | 1 shared instance in GameController | 1 per game | 1 per environment step (CPU workers) |
| UI updates | Every move, every signal emission | Same | Not applicable (no UI) |
| Memory | ~10MB for UI + engine | ~10MB per game instance | ~1MB per env instance, 100s of envs |
| Bottleneck | AI computation (>100ms = noticeable lag) | AI computation | Env stepping throughput |

For v1 human-vs-AI, the AI QThread pattern is sufficient. For future AI-vs-AI self-play, batch AI computation across a `QThreadPool` of workers with a shared engine queue.

---

## Phase-Specific Architecture Notes

### Phase: PyQt6 Board UI + GameController

The core wiring challenge is ensuring all UI state originates from `GameSignals` emissions. The first working version should:
1. `GameController` owns `XiangqiEngine.starting()`
2. `BoardWidget` displays `engine.board` via `board_changed` signal
3. User clicks a piece → `user_move_requested(from_sq, to_sq)` signal
4. `GameController` validates and applies; emits `move_applied` for animation
5. After animation, `state_machine.transition("ANIMATION_DONE")` → `WAITING_INPUT`

### Phase: AI Integration

The pluggable AI interface is designed to be trivial to test:

```python
def test_heuristic_ai_always_captures_when_possible():
    snapshot = make_snapshot_with_capturable_enemy_piece()
    ai = HeuristicAI()
    move = ai.suggest_move(snapshot)
    assert snapshot.board[move.to_sq] != 0  # Captured something
```

Every AI implementation is unit-testable with no Qt dependency — pure Python with `EngineSnapshot`.

---

## Sources

- Qt documentation: QThread + signals/slot pattern — HIGH confidence (official Qt docs)
- PyQt6 signal/slot threading: riverbankcomputing.com/pyqt/signalsandslots — HIGH confidence
- QThread subclassing warning: doc.qt.io/qt-6/qthread.html#subclassing-qthread — HIGH confidence (explicit warning in Qt docs)
- Observer pattern in Qt: standard software engineering practice — HIGH confidence
- Game state machine for board games: standard pattern used in chess.com, lichess, Stockfish UI — HIGH confidence
- AI abstraction interface design: python-chess library API design (abstraction over engine), stockfish Python bindings — HIGH confidence
- EngineSnapshot pattern: derived from the GoF Memento pattern for encapsulating internal state — HIGH confidence (standard design pattern)
- Move encoding: confirmed from existing `src/xiangqi/engine/engine.py` and `types.py` — HIGH confidence

---
*Architecture research for: RL-Xiangqi PyQt6 + AI integration layer*
*Researched: 2026-03-23*
