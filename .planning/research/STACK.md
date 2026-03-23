# Technology Stack: PyQt6 Game Board UI

**Project:** RL Xiangqi -- AI-powered Chinese Chess with PyQt6 desktop UI
**Researched:** 2026-03-23
**Confidence:** MEDIUM-HIGH (patterns verified across multiple open-source projects and documentation; some PyQt6-specific details require implementation validation)

---

## TL;DR -- The One-Line Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Board rendering | `QGraphicsView` + `QGraphicsScene` | Native drag-drop, selection, zoom, layering for highlights |
| Board drawing | Custom `QGraphicsRectItem` per square + `paint()` override | Clean hit-testing, per-item state, easy highlighting |
| Piece rendering | `QPixmap` on `QGraphicsPixmapItem` | Fast, scalable, anti-aliased via device pixel ratio |
| Drag-and-drop | Manual `mousePress`/`mouseMove`/`mouseRelease` on items | Qt's drag-drop system is for file/widget drops; not appropriate for board-piece moves |
| Architecture | MVP (Model-View-Presenter) | Qt combines View+Controller; MVP adds a clean Presenter that isolates the rule engine from the UI |
| Threading | `QThread` + `moveToThread()` + `pyqtSignal` | The canonical PyQt threading pattern; keeps AI off the GUI thread |
| AI interface | Abstract `GameAI` protocol + concrete `AIWorker(QObject)` | Future Alpha-Beta or MCTS plug-ins just implement `compute_best_move(state) -> Move` |
| Python version | Python 3.12 (or 3.13 with PyQt6 >= 6.8) | PyQt6 6.7.x had Python 3.13 breakage; 6.8+ is fixed |

---

## 1. Board Rendering: QGraphicsView vs QWidget

### Recommendation: QGraphicsView + QGraphicsScene

For a Xiangqi board (10 rows x 9 columns, with palace diagonals and a river), `QGraphicsView` is the correct choice over a raw `QWidget` with `paintEvent`.

| Criterion | QWidget + paintEvent | QGraphicsView + QGraphicsScene |
|-----------|---------------------|-------------------------------|
| Drag-and-drop | Manual implementation required | Built-in item selection, hover, drag tracking |
| Move highlights | Redraw entire board | Overlay highlight items on top of squares |
| Coordinate mapping | Manual math | `mapToScene()` / `itemAt()` handles it |
| Animation | Manual QTimer | `QGraphicsItemAnimation` or `setPos` anim |
| Layering | Manual z-order | Built-in: background squares < pieces < highlights < drag ghost |
| Zoom/pan | Manual | Built-in via `QGraphicsView` |
| Hit-testing | Manual `event.pos()` | `itemAt(pos)` returns the exact item |
| Performance for 90 squares | Fine | Fine (only 90 items) |

**When QWidget IS appropriate:** Static board display, no user interaction, pure image output.

**For Xiangqi specifically:** The board has cross-intersections (not full squares in the corners), palace diagonal marks, and a river. These are all cleanly drawn in a custom `QGraphicsItem.paint()` override. The layering model (board lines below, square fills, piece sprites, highlight overlays, drag shadow) is exactly what QGraphicsScene was designed for.

### Component Architecture

```
QGraphicsView (BoardView)
  └── QGraphicsScene (BoardScene)
        ├── QGraphicsRectItem[90]  (BoardSquare items -- colored fills, palace marks)
        ├── QGraphicsLineItem[...] (Grid lines -- drawn once, or baked into background)
        ├── QGraphicsPixmapItem[32] (Piece sprites -- front or back based on side)
        ├── QGraphicsRectItem[...]  (Highlight overlays -- legal move dots, last move)
        └── Custom drag-ghost item  (follows cursor during drag)
```

---

## 2. Drawing the Board with QPainter

### Background (drawn once, cached)

Draw the board grid and decorative elements (river, palace diagonals, file/rank labels) in a single `QPixmap` using `QPainter`, then set it as the `QGraphicsScene` background via `setBackgroundBrush()`. Alternatively, draw it in the `QGraphicsView.drawBackground()` override. Do NOT recreate this on every frame.

```python
def _build_board_pixmap(self, sq_size: int) -> QPixmap:
    pixmap = QPixmap(sq_size * 9, sq_size * 10)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Basic grid (vertical lines 9, horizontal lines 10)
    for col in range(9):
        x = col * sq_size + sq_size / 2
        painter.drawLine(int(x), int(sq_size / 2), int(x), int(sq_size * 9 + sq_size / 2))

    for row in range(10):
        y = row * sq_size + sq_size / 2
        x1 = sq_size / 2 if row in (0, 9) else sq_size / 2 + sq_size
        x2 = sq_size * 8 + sq_size / 2 if row in (0, 9) else sq_size * 8 + sq_size / 2
        painter.drawLine(int(x1), int(y), int(x2), int(y))

    # River (rows 4-5)
    font = QFont(" serif")
    font.setPixelSize(int(sq_size * 0.7))
    painter.setFont(font)
    painter.drawText(int(sq_size * 2.5), int(sq_size * 4.75), "楚 河")
    painter.drawText(int(sq_size * 5.5), int(sq_size * 4.75), "漢 界")

    # Palace diagonal marks
    for (r1, c1, r2, c2) in [(0, 3, 2, 5), (7, 3, 9, 5)]:
        x1, y1 = c1 * sq_size + sq_size / 2, r1 * sq_size + sq_size / 2
        x2, y2 = c2 * sq_size + sq_size / 2, r2 * sq_size + sq_size / 2
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        painter.drawLine(int(x2), int(y1), int(x1), int(y2))

    painter.end()
    return pixmap
```

### Per-Square Items (interactive, dynamic)

Each of the 90 squares is a `QGraphicsRectItem`. Store `(row, col)` as `setData(0, (row, col))` on each. This makes `itemAt(pos).data(0)` return the coordinates instantly.

States per square:
- **Normal**: light tan fill
- **Legal move target**: small dot overlay (semi-transparent circle drawn in `paint()`)
- **Last move** (from/to): soft yellow highlight
- **In check**: red glow on the General's square

### Piece Items

Each piece is a `QGraphicsPixmapItem` holding a `QPixmap` of the piece sprite. Load PNG sprites at 2x resolution for HiDPI (`devicePixelRatio()`).

```python
class PieceItem(QGraphicsPixmapItem):
    def __init__(self, piece_type: int, color: int, sq_size: int):
        super().__init__()
        self.piece_type = piece_type
        self.color = color
        self.sq_size = sq_size
        self.setPixmap(self._load_sprite())
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable)
        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.setOffset(-sq_size / 2, -sq_size / 2)

    def _load_sprite(self) -> QPixmap:
        # Return cached QPixmap for this piece type
        ...

    def itemChange(self, change, value):
        # Respond to position changes for legal-move validation
        ...
```

---

## 3. Drag-and-Drop: The Correct Approach for Board Games

**Critical finding:** Qt's built-in drag-and-drop system (`QDrag`, `QDropEvent`) is designed for dragging data between widgets or apps -- not for smooth in-board piece movement. Use direct mouse event handling on `QGraphicsItem` instead.

### The Three-Event Pattern

All three events are handled on the piece `QGraphicsItem` subclass:

```python
class PieceItem(QGraphicsPixmapItem):
    def __init__(self, ...):
        super().__init__()
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable)
        # DO NOT set ItemIsDragEnabled -- use manual drag

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            event.ignore()
            return
        self.scene().board_controller.start_drag(self, event.scenePos())
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        # Only enter drag mode if mouse has moved > QApplication.startDragDistance()
        if not self.scene().board_controller.is_dragging:
            return
        self.scene().board_controller.update_drag(event.scenePos())
        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if not self.scene().board_controller.is_dragging:
            super().mouseReleaseEvent(event)
            return
        target_square = self._snap_to_square(event.scenePos())
        self.scene().board_controller.end_drag(target_square)
        event.accept()

    def _snap_to_square(self, pos: QPointF) -> tuple[int, int]:
        col = int(pos.x() // self.sq_size)
        row = int(pos.y() // self.sq_size)
        return (max(0, min(row, 9)), max(0, min(col, 8)))
```

### Visual Feedback During Drag

During drag, the piece follows the cursor (set position in `mouseMove`). Use `setOpacity(0.7)` on the dragged piece. Show the original square with a ghost piece at `opacity=0.3` so the player knows where the piece came from. Draw legal-move squares as colored dots (via `QGraphicsEllipseItem` or painted on the square item).

### Snapping vs Free Positioning

Always snap to grid on release -- pieces snap to the center of the nearest valid square. Do not allow free-form piece placement. If the target is not a legal move, animate the piece back to its original square using `QPropertyAnimation` or `setPos` in a `QTimer.singleShot` loop.

---

## 4. MVP Architecture for Game Board UI

### Why Not MVC

Qt's own Model/View framework (e.g., `QAbstractTableModel`) combines View and Controller into the View widget. This is fine for lists and trees, but for a game board the input logic is complex enough to warrant a separate Presenter layer. Traditional MVC (where the Controller handles all input) also does not fit well with Qt's signal/slot architecture.

### MVP Structure

```
Presenter (BoardPresenter)
  - Owns: game state, AI worker, current turn
  - Receives: user move input, AI move results
  - Updates: Model (game state) and View (board display)
  - Signals: move_submitted, ai_thinking, ai_move_ready, game_over

Model (XiangqiGame -- from v0.1 rules engine)
  - Owns: board state, move history, check/checkmate state
  - Interface: apply_move(), legal_moves(), undo(), is_game_over()
  - Signals: state_changed (emitted on every move)

View (BoardView / QGraphicsView)
  - Owns: QGraphicsScene, piece items, highlight overlays
  - Receives: Presenter commands (show_board, highlight_moves, animate_ai_move)
  - Emits: piece_selected, piece_moved (Presenter decides if legal)
  - Never talks to the AI or the rules engine directly
```

### Key Signals on the Presenter

```python
class BoardPresenter(QObject):
    # Inputs (from View)
    piece_selected = pyqtSignal(int, int)       # row, col
    piece_moved = pyqtSignal(int, int, int, int)  # from_r, from_c, to_r, to_c

    # Outputs (to View)
    board_updated = pyqtSignal()                  # full board redraw
    highlights_updated = pyqtSignal(list)        # list of (row, col) to highlight
    ai_thinking = pyqtSignal(bool)               # True=thinking, False=done
    ai_move_ready = pyqtSignal(tuple)           # (from_r, from_c, to_r, to_c)
    game_over = pyqtSignal(str)                  # "RED_WINS", "BLACK_WINS", "DRAW"
```

### View Never Calls the Rules Engine

The View (`BoardScene`) knows only about `(row, col)` coordinates and piece sprites. It does NOT call `legal_moves()`, does NOT check for checkmate. The Presenter intercepts every user action, validates through the Model, and commands the View to update.

---

## 5. AI Interface Abstraction (Critical for Future Plug-in)

### The `GameAI` Protocol

Define an abstract base class (Python `abc.ABC`) that any AI algorithm implements:

```python
from abc import ABC, abstractmethod
from typing import Protocol
import numpy as np

class Move(NamedTuple):
    from_pos: tuple[int, int]   # (row, col)
    to_pos:   tuple[int, int]
    promotion: int | None = None

class GameAI(ABC):
    """Abstract interface for any Xiangqi AI engine."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name, e.g. 'Alpha-Beta Depth-4'."""
        ...

    @abstractmethod
    def compute_best_move(self, board: np.ndarray, color: int) -> Move | None:
        """
        Blocking call -- runs in the AI thread.
        board: np.ndarray shape (10, 9), dtype=np.int8
        color: +1 for RED, -1 for BLACK
        Returns the chosen Move, or None if no legal moves (game over).
        """
        ...

    @abstractmethod
    def abort(self) -> None:
        """Request abortion of current computation (called from GUI thread)."""
        ...

    def supports_analysis(self) -> bool:
        """Override to return True if compute_best_move supports a progress callback."""
        return False
```

### Concrete Implementations to Plug In

| AI Type | Implementation | Notes |
|---------|---------------|-------|
| **Random** | `RandomAI(GameAI)` | Uniform random over legal moves. Baseline. |
| **RL Policy** | `RLPolicyAI(GameAI)` | Your trained PPO policy network. Reads board, outputs action logits, samples. |
| **Alpha-Beta** | `AlphaBetaAI(GameAI)` | Classic depth-limited minimax with move ordering. ~300 lines. |
| **MCTS** | `MCTSai(GameAI)` | Monte Carlo Tree Search with UCB1 selection. |

### AI Worker Thread Pattern

The AI runs in a dedicated `QThread`. The Presenter does NOT block on AI computation. Communication is entirely via `pyqtSignal` / `pyqtSlot`:

```python
class AIWorker(QObject):
    """Runs in a QThread. Owns the GameAI instance. Non-blocking from GUI perspective."""

    thinking_started = pyqtSignal()
    move_ready = pyqtSignal(tuple)  # Move NamedTuple
    thinking_finished = pyqtSignal()

    def __init__(self, ai: GameAI):
        super().__init__()
        self._ai = ai
        self._abort_requested = False

    @pyqtSlot(np.ndarray, int)
    def compute(self, board: np.ndarray, color: int):
        """Called from Presenter via signal."""
        self.thinking_started.emit()
        best_move = self._ai.compute_best_move(board, color)
        self.thinking_finished.emit()
        self.move_ready.emit(best_move)

    def abort(self):
        self._abort_requested = True
        self._ai.abort()


# In Presenter.__init__:
self._ai_thread = QThread()
self._ai_worker = AIWorker(RandomAI())  # or AlphaBetaAI(), etc.
self._ai_worker.moveToThread(self._ai_thread)
self._ai_thread.start()

# Connect signals:
self._ai_worker.move_ready.connect(self._on_ai_move_ready)
self._ai_worker.thinking_started.connect(lambda: self.ai_thinking.emit(True))
self._ai_worker.thinking_finished.connect(lambda: self.ai_thinking.emit(False))

# To request an AI move (from Presenter.on_turn_changed or after human move):
@pyqtSlot()
def request_ai_move(self):
    board = self._model.get_board()   # np.ndarray
    color = self._model.current_color
    # request_ai_move signal is connected to AIWorker.compute slot
    self.request_ai_move_signal.emit(board, color)
```

### Hot-Swapping AI Engines

The Presenter holds a `GameAI` reference. To switch from `RandomAI` to `AlphaBetaAI`:

```python
def set_ai(self, ai: GameAI):
    self._ai_thread.quit()
    self._ai_thread.wait()
    old_worker = self._ai_worker
    self._ai_worker = AIWorker(ai)
    self._ai_worker.moveToThread(self._ai_thread)
    # Reconnect signals...
    self._ai_thread.start()
```

This hot-swap is possible because the `GameAI` protocol is the only interface the `AIWorker` depends on.

---

## 6. Threading: Keeping the UI Responsive

### The Canonical PyQt Threading Pattern

**Do NOT subclass `QThread` and override `run()`.** This pattern conflates the thread lifecycle with the worker logic and prevents the standard signal/slot thread-affinity mechanism from working correctly.

**Instead:** Subclass `QObject` as the worker, create a bare `QThread`, move the worker onto it with `moveToThread()`.

```python
# WRONG pattern (avoid):
class AIThread(QThread):
    def run(self):        # Logic lives in the thread subclass -- bad
        result = self._compute()
        self.result_ready.emit(result)

# RIGHT pattern (use):
class AIWorker(QObject):
    result_ready = pyqtSignal(object)
    def compute(self):    # Logic in a QObject -- good
        result = self._compute()
        self.result_ready.emit(result)

# In setup:
thread = QThread()
worker = AIWorker()
worker.moveToThread(thread)
worker.result_ready.connect(self._on_result)   # Slot runs in main thread (GUI thread)
thread.started.connect(worker.compute)          # worker.compute starts when thread starts
thread.start()
```

### Signals Cross Threads Automatically

`pyqtSignal` with default `Qt.ConnectionType.AutoConnection` routes slots to the receiver's thread automatically. The AI worker's `move_ready` signal will be delivered to the Presenter's slot in the main thread -- no explicit `QueuedConnection` needed when the receiver is a QObject living in the main thread.

### Thread Safety Rules

- **GUI thread owns all QGraphicsItems.** Never create or modify a `QGraphicsItem` from the AI thread.
- **Share NumPy arrays between threads safely.** `np.ndarray` with refcount=1 (not shared) is safe to pass across threads. Pass a **copy** (`board.copy()`) to the AI worker, not a reference into the scene's live board.
- **Use `QMetaObject.invokeMethod`** for thread-safe calls to QObject methods if needed.
- **`QApplication.processEvents()` in a worker is forbidden.** It will corrupt the event loop.

### Real-Time Considerations for Xiangqi

For RL-assisted play, the AI move computation could take seconds. Show a "thinking" indicator:
- `ai_thinking.emit(True)` → View shows a pulsing indicator on the AI side's pieces
- `ai_thinking.emit(False)` → indicator removed
- The AI worker can also emit periodic progress signals (e.g., every 1000 nodes) so the View can show a depth/evaluation bar without blocking.

---

## 7. Version Requirements

| Package | Minimum Version | Recommended | Python | Notes |
|---------|----------------|-------------|--------|-------|
| PyQt6 | 6.8.0 | 6.10.2 | 3.10 -- 3.13 | PyQt6 6.7.x had Python 3.13 breakage (missing sip module). 6.8+ fixed. |
| PyQt6-sip | 13.8 | latest | 3.10 -- 3.13 | Bundled with PyQt6 on pip install; separate package only needed for custom builds. |
| PySide6 | 6.8 | 6.9 | 3.10 -- 3.13 | Qt Company's official bindings. LGPL license. Use instead of PyQt6 if GPL is a concern. API is near-identical. |
| Python | 3.10 | 3.12 | -- | PyQt6 6.8+ fully supports 3.12 and 3.13. Use 3.12 for MPS/RLOPS stack compatibility (existing project constraint). |

### Compatibility Matrix

```
Python 3.10  -- PyQt6 6.4+  -- Works
Python 3.11  -- PyQt6 6.5+  -- Works
Python 3.12  -- PyQt6 6.7+  -- Works (MPS-compatible, project default)
Python 3.13  -- PyQt6 6.8+  -- Works (6.7.x had breakage, fixed in 6.8)
```

---

## 8. Supporting Libraries for the UI

| Library | Purpose | When to Use |
|---------|---------|-------------|
| **PyQtGraph 0.13.x** | Live training metric plots in-app | Show Elo/win-rate curves alongside the board during RL training |
| **matplotlib + FigureCanvasQTAgg** | Static/saved charts | For report generation, not live updates |
| **NumPy 2.x** | Board state as `np.ndarray` | All board data passed to the AI worker |

---

## 9. Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|------------------------|
| `QGraphicsView` + `QGraphicsScene` | Raw `QWidget` + `paintEvent` | Only for a static board with zero interactivity (e.g., a puzzle viewer with no drag) |
| Manual mouse events for drag | Qt `QDrag` system | Never for board-piece moves; QDrag is for inter-widget or inter-app data transfer |
| PyQt6 | **PySide6** | When LGPL licensing is required; otherwise PyQt6 has a richer ecosystem and more third-party examples |
| PyQt6 | **DearPyGui | Render-engine UI** | Demos then immediate-mode GUI style does not suit a board game; not suitable |
| `QGraphicsPixmapItem` for pieces | `QGraphicsSvgItem` for SVG pieces | SVG scales perfectly but adds a QtSvg6 dependency; PNG at 2x device pixel ratio is simpler |
| Worker QThread | `QThreadPool` + `QRunnable` | `QRunnable` cannot be stopped once started (no abort signal); use worker QThread for cancellable AI computations |
| PyQtGraph | Matplotlib live updates | Matplotlib is slow for real-time; use PyQtGraph for in-app live plots, matplotlib for export |

---

## 10. Recommended Project Structure

```
src/
  ui/
    board_view.py        # QGraphicsView + QGraphicsScene -- board rendering only
    piece_item.py        # QGraphicsPixmapItem subclass for pieces
    square_item.py       # QGraphicsRectItem subclass for squares
    board_presenter.py   # MVP Presenter -- orchestrates Model + View
  ai/
    base.py              # GameAI abstract protocol
    random_ai.py         # Random legal-move AI
    rl_policy_ai.py      # Trained PPO policy network AI
    alpha_beta_ai.py     # Depth-limited alpha-beta (future)
    mcts_ai.py           # MCTS (future)
    worker.py            # AIWorker -- QObject moved to QThread
  model/
    xiangqi_game.py      # XiangqiGame -- v0.1 rule engine, returns board np.ndarray
    move.py              # Move NamedTuple
  main.py                # QApplication, window creation, thread startup
```

The `board_presenter.py` is the only module that imports both the UI and the model. The AI modules (`ai/`) import only the model (board state). The UI (`ui/board_view.py`) imports only the presenter interface. The model has zero dependencies on either.

---

## 11. Gaps to Address in Later Research

- **QPropertyAnimation vs manual setPos in mouseMoveEvent** -- during drag, should the piece position follow the mouse exactly or use a spring/interpolation? Both are viable; implementer preference.
- **Sound effects** -- QSound or QSoundEffect for piece placement, check, game over. Not researched for this pass.
- **Game clock** -- `QTimer`-based clock widget with increment support. Not researched.
- **PGN/XQF file loading** -- out of scope for v0.2 but needed for replay feature.

---

## Sources

- PyQt6 QGraphicsView architecture and patterns -- pythonguis.com PyQt6 tutorial series -- HIGH confidence
- Manual drag-and-drop for QGraphicsView chess pieces -- gist.github.com/d23636898739dbc46db16be4e05a86f8 -- HIGH confidence (working code example)
- Sahinakkaya chess PyQt6 implementation -- github.com/sahinakkaya/chess -- MEDIUM confidence (open-source reference)
- ChessQ Chinese chess PyQt GUI -- github.com/walker8088/ChessQ -- MEDIUM confidence (xiangqi-specific PyQt reference)
- MVP pattern for PyQt -- medium.com/@mark_huber "A Clean Architecture for a PyQT GUI Using the MVP Pattern" -- MEDIUM confidence (design pattern article)
- PyQt6 threading best practices -- realpython.com/python-pyqt-qthread/ -- HIGH confidence (authoritative Python tutorial site)
- PyQt6 threading worker pattern -- pythonguis.com/tutorials/multithreading-pyqt6-applications-qthreadpool/ -- HIGH confidence
- Qt threading documentation -- doc.qt.io/qt-6/threads-qobject.html -- HIGH confidence (official docs)
- PyQt6 Python 3.13 compatibility -- Stack Overflow / forum.qt.io community reports -- MEDIUM confidence (user reports, 2024-2025)
- game-ai-client PyPI generic AI interface -- pypi.org/project/game-ai-client/0.1.2/ -- LOW-MEDIUM confidence (generic SDK, not xiangqi-specific)
- PhysicsKnight MCTS-Minimax hybrid -- github.com/physicsKnight/MCTS-Minimax -- LOW-MEDIUM confidence (reference for algorithm structure)
