# Phase 06: Piece Interaction - Research

**Researched:** 2026-03-25
**Domain:** PyQt6 QGraphicsView mouse interaction, piece selection highlighting, legal move visualization
**Confidence:** HIGH (existing codebase patterns, established Qt APIs, CONTEXT.md decisions locked)

## Summary

Phase 06 adds interactive piece selection and move execution to the static board rendering from Phase 05. Users click red pieces to select them, see legal move destinations highlighted, click a highlighted square to move, and can only interact during red's turn. The implementation builds directly on QXiangqiBoard and PieceItem classes, adding mouse event handling, dynamic highlight items, and signal emission for move notification.

**Primary recommendation:** Implement mouse interaction in QXiangqiBoard via mousePressEvent override, use mapToScene() for coordinate conversion, create/destroy QGraphicsEllipseItem highlights dynamically, and emit a pyqtSignal when moves are applied. All decisions are locked in CONTEXT.md - no architectural exploration needed.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Selection Visual Feedback
- **D-01:** Selected piece shows gold outer ring highlight (#FFD700), keep original white stroke
- **D-02:** Outer ring item dynamically created/deleted: create QGraphicsEllipseItem on selection, delete on deselection
- **D-03:** Outer ring above piece (z-value > 1.0), semi-transparent not fully occluding piece

#### Legal Move Highlighting
- **D-04:** Legal move targets show semi-transparent dots (QGraphicsEllipseItem)
- **D-05:** Dot color gold #FFD700, unified with selection ring color
- **D-06:** Dots implemented as QGraphicsEllipseItem, created on piece selection, deleted on deselection
- **D-07:** Dot transparency 50%, semi-transparent not occluding board grid
- **D-08:** Dot size 0.5*cell diameter (medium dots)

#### Move Execution UX
- **D-09:** Immediate move on drop, no animation (simplified implementation)
- **D-10:** Incremental board update: only update moved piece and captured piece (if any), rest unchanged
- **D-11:** State update order: call engine.apply(move) -> update self._state -> refresh board
- **D-12:** Incremental update logic encapsulated in QXiangqiBoard.apply_move() method
- **D-13:** Clear all highlights after move (selection ring + legal move dots)
- **D-14:** Update existing item's pos and internal _row/_col attributes when moving, reuse item
- **D-15:** QXiangqiBoard maintains {(row, col): PieceItem} dictionary index, O(1) piece item lookup
- **D-16:** Captured piece removed from scene and deleted from dictionary
- **D-17:** Dictionary index updated immediately: update dict right after move/capture, maintain consistency
- **D-18:** No exception handling needed: UI layer ensures only legal moves called (from legal_moves selection)
- **D-19:** Emit signal after move to notify external state changed
- **D-20:** Custom pyqtSignal carrying move info (from_sq, to_sq, captured)
- **D-21:** Temporarily disable interaction during move execution, prevent duplicate operations
- **D-22:** Interaction disable via boolean property _interactive: bool, mousePressEvent checks flag
- **D-23:** UI builds move (16-bit int): from selected piece position + target position, using rc_to_sq and bit operations

#### Turn Interaction Control
- **D-24:** Black turn disables interaction via _interactive=False flag
- **D-25:** Disabled state silently ignores clicks, no visual feedback (mousePressEvent returns directly)
- **D-26:** External Controller (Phase 07) sets _interactive flag: True for red turn, False for black turn
- **D-27:** _interactive default True (enabled), set False before black turn, restore True after move

### Claude's Discretion
- Outer ring highlight specific opacity (suggest 50-70%)
- Outer ring specific thickness (suggest 2-3px)
- Dot z-value (should be below pieces, z < 1.0)
- Dictionary index initialization timing (build synchronously in _load_pieces)
- Signal naming style (e.g., moveApplied or on_move_applied)

### Deferred Ideas (OUT OF SCOPE)
- Drag-and-drop move (drag-drop) — MVP click-to-move sufficient, drag adds complexity
- Check visual highlight (king highlighted when in check) — Phase 08 UI enhancement
- Move animation (sliding effect) — MVP immediate move, animation in v0.3
- Sound effects (move sound) — v0.3
- Captured piece display area — post v0.2

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-03 | Click own piece to select, legal move targets highlighted | D-01 to D-08: selection ring + legal move dots via QGraphicsEllipseItem |
| UI-04 | Click legal move target to execute move, call engine.apply() | D-09 to D-23: mousePressEvent -> apply_move() -> signal emission |
| UI-05 | Click illegal target/empty square deselects, invalid interaction | D-13: clear highlights on invalid click; click handling logic |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyQt6 | 6.x | UI framework | Already used in Phase 05, project standard |
| pytest-qt | 4.x | UI testing | Standard for PyQt testing, already in test suite |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x | Test runner | All test execution |
| numpy | 2.x | Board array | Engine state access |

### Existing Code Assets (No New Libraries)
| Asset | Location | Purpose |
|-------|----------|---------|
| QXiangqiBoard | src/xiangqi/ui/board.py | Base class for interaction |
| PieceItem | src/xiangqi/ui/board_items.py | Piece rendering, has _row/_col/_piece_value |
| XiangqiEngine | src/xiangqi/engine/engine.py | legal_moves(), apply(), is_legal() |
| rc_to_sq / sq_to_rc | src/xiangqi/engine/types.py | Coordinate conversion |

## Architecture Patterns

### Recommended Class Extensions

```
QXiangqiBoard (existing)
├── New instance variables:
│   ├── _selected: tuple[int, int] | None  # (row, col) of selected piece
│   ├── _highlight_items: list[QGraphicsEllipseItem]  # legal move dots
│   ├── _selection_ring: QGraphicsEllipseItem | None  # selection highlight
│   ├── _piece_index: dict[tuple[int, int], PieceItem]  # O(1) lookup
│   └── _interactive: bool  # interaction enabled flag
├── New signals:
│   └── move_applied = pyqtSignal(int, int, int)  # from_sq, to_sq, captured
├── New methods:
│   ├── mousePressEvent(event)  # click handling
│   ├── _scene_to_board(pos: QPointF) -> tuple[int, int] | None
│   ├── _select_piece(row: int, col: int) -> None
│   ├── _deselect_piece() -> None
│   ├── _show_legal_moves(row: int, col: int) -> None
│   ├── _clear_highlights() -> None
│   ├── _try_move(from_row, from_col, to_row, to_col) -> bool
│   ├── apply_move(from_sq: int, to_sq: int) -> None
│   └── set_interactive(enabled: bool) -> None
└── Modified methods:
    └── _load_pieces()  # also build _piece_index
```

### Pattern 1: Mouse Event Handling

**What:** Override mousePressEvent to capture clicks and map to board coordinates.

**When to use:** All user piece selection and move execution.

**Example:**
```python
# Source: PyQt6 documentation + established patterns
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QMouseEvent

class QXiangqiBoard(QGraphicsView):
    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        if not self._interactive:
            return  # D-25: silently ignore when disabled

        # Convert view coordinates to scene coordinates
        scene_pos: QPointF = self.mapToScene(event.position())
        board_pos = self._scene_to_board(scene_pos)

        if board_pos is None:
            return  # Click outside board

        row, col = board_pos
        self._handle_board_click(row, col)

    def _scene_to_board(self, pos: QPointF) -> tuple[int, int] | None:
        """Convert scene coordinates to board (row, col) or None if outside grid."""
        cell = self._cell
        # Grid bounds: x in [0.6, 9.6]*cell, y in [0.6, 9.6]*cell
        col = round(pos.x() / cell - 0.6)
        row = round(pos.y() / cell - 0.6)
        if 0 <= row < 10 and 0 <= col < 9:
            return (row, col)
        return None
```

### Pattern 2: Dynamic Highlight Items

**What:** Create QGraphicsEllipseItem highlights on selection, destroy on deselection.

**When to use:** Selection ring (D-02) and legal move dots (D-06).

**Example:**
```python
# Source: Qt documentation QGraphicsItem.setOpacity()
from PyQt6.QtWidgets import QGraphicsEllipseItem
from PyQt6.QtGui import QPen, QBrush, QColor

HIGHLIGHT_COLOR = "#FFD700"  # D-05: gold color

def _create_selection_ring(self, row: int, col: int) -> QGraphicsEllipseItem:
    """D-02, D-03: Create selection highlight ring above piece."""
    cell = self._cell
    d = cell * 0.85  # Slightly larger than piece (0.8*cell)

    ring = QGraphicsEllipseItem(0, 0, d, d)
    ring.setPos((col + 0.15) * cell, (row + 0.15) * cell)  # Center on piece
    ring.setPen(QPen(QColor(HIGHLIGHT_COLOR), 3.0))  # D: 2-3px thickness
    ring.setBrush(Qt.BrushStyle.NoBrush)  # No fill, just outline
    ring.setOpacity(0.7)  # D: 50-70% opacity
    ring.setZValue(1.1)  # D-03: above piece (z=1.0)
    self._scene.addItem(ring)
    return ring

def _create_legal_move_dot(self, row: int, col: int) -> QGraphicsEllipseItem:
    """D-04 to D-08: Create semi-transparent dot at legal move target."""
    cell = self._cell
    d = cell * 0.5  # D-08: 0.5*cell diameter

    dot = QGraphicsEllipseItem(0, 0, d, d)
    dot.setPos((col + 0.35) * cell, (row + 0.35) * cell)  # Center on square
    dot.setPen(Qt.PenStyle.NoPen)
    dot.setBrush(QBrush(QColor(HIGHLIGHT_COLOR)))
    dot.setOpacity(0.5)  # D-07: 50% transparency
    dot.setZValue(0.5)  # D: below pieces (z=1.0)
    self._scene.addItem(dot)
    return dot

def _clear_highlights(self) -> None:
    """D-13: Remove all highlight items from scene."""
    for item in self._highlight_items:
        self._scene.removeItem(item)
    self._highlight_items.clear()
    if self._selection_ring:
        self._scene.removeItem(self._selection_ring)
        self._selection_ring = None
```

### Pattern 3: Piece Index Dictionary

**What:** Maintain {(row, col): PieceItem} for O(1) lookup instead of O(n) scene scan.

**When to use:** Finding piece at click position, updating piece positions after move.

**Example:**
```python
# D-15: Dictionary index for O(1) lookup
def _load_pieces(self) -> None:
    """Load pieces and build index dictionary."""
    self._piece_index: dict[tuple[int, int], PieceItem] = {}
    board = self._state.board
    for row in range(ROWS):
        for col in range(COLS):
            val = int(board[row, col])
            if val == 0:
                continue
            piece_item = PieceItem(row, col, val, self._cell)
            self._scene.addItem(piece_item)
            self._piece_index[(row, col)] = piece_item  # D-15: index

def _get_piece_at(self, row: int, col: int) -> PieceItem | None:
    """O(1) lookup via dictionary index."""
    return self._piece_index.get((row, col))
```

### Pattern 4: Incremental Move Application

**What:** Update only moved piece and captured piece, not full board reload.

**When to use:** After legal move confirmed (D-10).

**Example:**
```python
# D-10 to D-17: Incremental update
from src.xiangqi.engine.types import rc_to_sq, encode_move

def apply_move(self, from_sq: int, to_sq: int) -> None:
    """Apply move to board state and update scene incrementally."""
    from_row, from_col = divmod(from_sq, 9)
    to_row, to_col = divmod(to_sq, 9)

    # Get piece item being moved
    piece_item = self._piece_index.get((from_row, from_col))
    if piece_item is None:
        return  # Should not happen if called correctly

    # Check for capture (D-16)
    captured_item = self._piece_index.get((to_row, to_col))
    captured_val = 0
    if captured_item:
        self._scene.removeItem(captured_item)
        del self._piece_index[(to_row, to_col)]
        captured_val = captured_item._piece_value

    # Apply to engine (D-11)
    move = encode_move(from_sq, to_sq, captured_val != 0)
    self._state = self._state.apply(move)  # or however state is updated

    # Update piece item position (D-14)
    piece_item._row = to_row
    piece_item._col = to_col
    piece_item.setPos((to_col + 0.2) * self._cell, (to_row + 0.2) * self._cell)

    # Update index (D-17)
    del self._piece_index[(from_row, from_col)]
    self._piece_index[(to_row, to_col)] = piece_item

    # Clear highlights (D-13)
    self._clear_highlights()
    self._selected = None

    # Emit signal (D-19, D-20)
    self.move_applied.emit(from_sq, to_sq, captured_val)
```

### Pattern 5: Custom pyqtSignal

**What:** Define signal to notify external listeners (Phase 07 Controller) of move completion.

**When to use:** After successful move application (D-19).

**Example:**
```python
# Source: PyQt6 pyqtSignal documentation
from PyQt6.QtCore import pyqtSignal

class QXiangqiBoard(QGraphicsView):
    # D-20: Signal carrying move info
    move_applied = pyqtSignal(int, int, int)  # from_sq, to_sq, captured

    def _on_move_complete(self, from_sq: int, to_sq: int, captured: int):
        """Called after move applied."""
        self.move_applied.emit(from_sq, to_sq, captured)
```

### Anti-Patterns to Avoid

- **Anti-pattern 1: Engine mutation in mousePressEvent** — Call apply_move() which handles engine update; don't call engine.apply() directly in event handler
- **Anti-pattern 2: Recreating all pieces on every move** — Use incremental update (D-10), only update moved/captured pieces
- **Anti-pattern 3: Scene scan for piece lookup** — Use _piece_index dictionary (D-15) for O(1) lookup
- **Anti-pattern 4: Ignoring resize** — Highlight items must be repositioned in resizeEvent along with pieces

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Click to board coordinate | Manual math from viewport | mapToScene() + rounding | Qt handles transforms, margins |
| Piece selection state | Custom state machine | Simple _selected: tuple \| None | Only one piece selected at a time |
| Legal move filtering | Custom move generation | engine.legal_moves() + filter by from_sq | Engine is source of truth |
| Semi-transparent items | RGBA color math | QGraphicsItem.setOpacity() | Qt compositing handles this |

**Key insight:** Qt provides all needed primitives. The complexity is in state management (_selected, _interactive, _piece_index), not graphics operations.

## Common Pitfalls

### Pitfall 1: Scene Coordinate Conversion Off By Half Cell

**What goes wrong:** Clicks register one square off because piece center offset (0.6*cell) not accounted for.

**Why it happens:** Scene origin is at (-0.6*cell, -0.6*cell) to center grid. Raw scene coordinates need adjustment.

**How to avoid:**
```python
def _scene_to_board(self, pos: QPointF) -> tuple[int, int] | None:
    cell = self._cell
    col = round(pos.x() / cell - 0.6)  # Account for 0.6*cell offset
    row = round(pos.y() / cell - 0.6)
    if 0 <= row < 10 and 0 <= col < 9:
        return (row, col)
    return None
```

**Warning signs:** Clicks on piece A select piece B consistently.

### Pitfall 2: Highlight Items Not Cleared on Deselect

**What goes wrong:** Legal move dots persist after clicking another piece or empty square.

**Why it happens:** _clear_highlights() not called in all deselection paths.

**How to avoid:** Always call _clear_highlights() at the start of _select_piece() and on any click that doesn't result in a move.

**Warning signs:** Multiple sets of dots visible simultaneously.

### Pitfall 3: Piece Index Out of Sync After Move

**What goes wrong:** After a move, clicking the destination square doesn't find the piece.

**Why it happens:** _piece_index updated before or after scene item update, creating temporary inconsistency.

**How to avoid:** Follow strict order (D-17): update piece item attributes -> update _piece_index -> clear highlights.

**Warning signs:** "Piece not found" errors after first move.

### Pitfall 4: ResizeEvent Doesn't Update Highlights

**What goes wrong:** After window resize, highlights are at wrong positions or wrong sizes.

**Why it happens:** resizeEvent reloads pieces but doesn't reposition highlight items.

**How to avoid:** In resizeEvent, also clear and recreate highlights if a piece is selected:
```python
def resizeEvent(self, event):
    # ... existing piece reload logic ...
    # Recreate highlights if piece selected
    if self._selected:
        row, col = self._selected
        self._clear_highlights()
        self._selection_ring = self._create_selection_ring(row, col)
        self._show_legal_moves(row, col)
```

**Warning signs:** Highlights misaligned after window resize.

### Pitfall 5: Signal Not Connected During Testing

**What goes wrong:** Tests pass but move_applied signal never fires in actual app.

**Why it happens:** Signal defined but never connected to anything in test setup.

**How to avoid:** In tests, explicitly connect signal and use qtbot.waitSignal():
```python
def test_move_emits_signal(board, qtbot):
    with qtbot.waitSignal(board.move_applied, timeout=1000) as blocker:
        # Simulate click sequence
        ...
    assert blocker.args == [from_sq, to_sq, 0]  # no capture
```

**Warning signs:** Tests don't verify signal emission.

## Code Examples

### Complete mousePressEvent Implementation

```python
# Source: Derived from CONTEXT.md decisions and PyQt6 patterns
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QGraphicsView, QGraphicsEllipseItem

class QXiangqiBoard(QGraphicsView):
    move_applied = pyqtSignal(int, int, int)  # D-20

    def __init__(self, state=None, parent=None):
        super().__init__(parent)
        # ... existing init ...
        self._selected: tuple[int, int] | None = None
        self._selection_ring: QGraphicsEllipseItem | None = None
        self._highlight_items: list[QGraphicsEllipseItem] = []
        self._piece_index: dict[tuple[int, int], PieceItem] = {}
        self._interactive: bool = True  # D-27

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        if not self._interactive:  # D-22, D-24
            return  # D-25: silent ignore

        scene_pos = self.mapToScene(event.position())
        board_pos = self._scene_to_board(scene_pos)

        if board_pos is None:
            return

        row, col = board_pos
        clicked_piece = self._piece_index.get((row, col))

        if self._selected:
            # Already have selection
            from_row, from_col = self._selected
            if (row, col) == self._selected:
                # Clicked same piece - deselect (UI-05)
                self._deselect_piece()
            elif clicked_piece and clicked_piece._piece_value > 0:
                # Clicked another red piece - switch selection
                self._deselect_piece()
                self._select_piece(row, col)
            elif self._is_legal_target(from_row, from_col, row, col):
                # Clicked legal move target - execute move (UI-04)
                self._execute_move(from_row, from_col, row, col)
            else:
                # Clicked illegal target - deselect (UI-05)
                self._deselect_piece()
        else:
            # No current selection
            if clicked_piece and clicked_piece._piece_value > 0:
                # Clicked red piece - select it (UI-03)
                self._select_piece(row, col)
            # else: clicked empty or black piece with no selection - ignore

    def _is_legal_target(self, from_row: int, from_col: int,
                          to_row: int, to_col: int) -> bool:
        """Check if (to_row, to_col) is a legal move from (from_row, from_col)."""
        from_sq = rc_to_sq(from_row, from_col)
        to_sq = rc_to_sq(to_row, to_col)

        # Get legal moves from engine and filter by from_sq
        legal = self._engine.legal_moves()  # or however engine is accessed
        for move in legal:
            move_from = move & 0x1FF
            move_to = (move >> 9) & 0x7F
            if move_from == from_sq and move_to == to_sq:
                return True
        return False

    def set_interactive(self, enabled: bool) -> None:
        """D-26: External control of interaction state."""
        self._interactive = enabled
        if not enabled:
            self._deselect_piece()  # Clear any selection when disabling
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Full board reload on move | Incremental update | Phase 06 D-10 | Better performance, smoother UX |
| Scan scene for piece at position | Dictionary index | Phase 06 D-15 | O(1) vs O(n) lookup |
| Static rendering only | Interactive selection | Phase 06 | Enables human play |

**Deprecated/outdated:**
- None for this phase (building on Phase 05 patterns)

## Open Questions

1. **Engine Reference in QXiangqiBoard**
   - What we know: Board currently holds XiangqiState (_state), not XiangqiEngine
   - What's unclear: How to access legal_moves() - need engine reference or pass moves from outside
   - Recommendation: Add engine parameter to __init__ or pass legal moves as needed. CONTEXT.md references "engine.apply()" suggesting engine reference expected.

2. **Move Application State Update**
   - What we know: D-11 says call engine.apply() then update self._state
   - What's unclear: If _state is separate from engine's internal state, they may diverge
   - Recommendation: Either _state should be engine's board property, or QXiangqiBoard holds engine reference and reads board from it after apply().

3. **Signal Connection for Phase 07**
   - What we know: move_applied signal defined (D-19, D-20)
   - What's unclear: Who connects to it in Phase 06 testing
   - Recommendation: Tests connect directly. Phase 07 Controller connects for turn management.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-qt 4.x |
| Config file | pyproject.toml (testpaths = ["tests"]) |
| Quick run command | `pytest tests/ui/test_board_interaction.py -x -q` |
| Full suite command | `pytest tests/ui/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-03 | Click red piece shows selection ring | unit | `pytest tests/ui/test_board_interaction.py::test_select_piece_shows_ring -x` | Wave 0 |
| UI-03 | Click red piece shows legal move dots | unit | `pytest tests/ui/test_board_interaction.py::test_select_piece_shows_legal_moves -x` | Wave 0 |
| UI-04 | Click legal target executes move | unit | `pytest tests/ui/test_board_interaction.py::test_click_legal_target_moves_piece -x` | Wave 0 |
| UI-04 | Move emits move_applied signal | unit | `pytest tests/ui/test_board_interaction.py::test_move_emits_signal -x` | Wave 0 |
| UI-05 | Click illegal target deselects | unit | `pytest tests/ui/test_board_interaction.py::test_click_illegal_deselects -x` | Wave 0 |
| UI-05 | Click empty square deselects | unit | `pytest tests/ui/test_board_interaction.py::test_click_empty_deselects -x` | Wave 0 |
| D-24 | Black turn disables interaction | unit | `pytest tests/ui/test_board_interaction.py::test_black_turn_disabled -x` | Wave 0 |
| D-15 | Piece index O(1) lookup works | unit | `pytest tests/ui/test_board_interaction.py::test_piece_index_lookup -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ui/test_board_interaction.py -x -q`
- **Per wave merge:** `pytest tests/ui/ -x`
- **Phase gate:** Full suite green before /gsd:verify-work

### Wave 0 Gaps
- [ ] `tests/ui/test_board_interaction.py` - covers UI-03, UI-04, UI-05, D-24, D-15
- [ ] `tests/ui/conftest.py` - add board_with_engine fixture if needed
- Framework install: `pip install pytest-qt` - check if already installed

*(If no gaps: "None - existing test infrastructure covers all phase requirements")*

## Sources

### Primary (HIGH confidence)
- [CONTEXT.md](./06-CONTEXT.md) - Locked decisions D-01 to D-27
- [Phase 05 board.py](../../src/xiangqi/ui/board.py) - Existing QXiangqiBoard implementation
- [Phase 05 board_items.py](../../src/xiangqi/ui/board_items.py) - PieceItem class with _row/_col/_piece_value
- [engine.py](../../src/xiangqi/engine/engine.py) - XiangqiEngine API: apply(), legal_moves(), is_legal()
- [types.py](../../src/xiangqi/engine/types.py) - rc_to_sq(), sq_to_rc(), encode_move()

### Secondary (MEDIUM confidence)
- [PyQt6 QGraphicsView.mapToScene()](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGraphicsView.html#mapToScene) - Coordinate conversion
- [PyQt6 QGraphicsItem.setOpacity()](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGraphicsItem.html#setOpacity) - Transparency control
- [pytest-qt documentation](https://pytest-qt.readthedocs.io/en/latest/reference.html) - qtbot.mouseClick and waitSignal

### Tertiary (LOW confidence)
- [PythonGUIs QGraphics tutorial](https://www.pythonguis.com/tutorials/pyside6-qgraphics-vector-graphics/) - Selection highlight patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using existing PyQt6, no new libraries needed
- Architecture: HIGH - All decisions locked in CONTEXT.md
- Pitfalls: HIGH - Based on established Qt patterns and project-specific coordinate system

**Research date:** 2026-03-25
**Valid until:** 30 days (stable Qt API, locked decisions)
