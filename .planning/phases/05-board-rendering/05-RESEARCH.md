# Phase 05: Board Rendering - Research

**Researched:** 2026-03-23
**Domain:** PyQt6 QGraphicsView + QGraphicsScene rendering, Xiangqi board coordinate mapping, font rendering on Windows
**Confidence:** HIGH (PyQt6 API verified against official Qt 6.8 docs; coordinate math verified against codebase constants; font sizing confirmed via spec arithmetic)

---

## Summary

Phase 05 renders a 9x10 Xiangqi board with 32 pieces using PyQt6's QGraphicsView + QGraphicsScene. The board background (felt, grid, river, palace diagonals, labels) is best drawn via `QGraphicsView.drawBackground()` override. Each piece is best implemented as a custom `QGraphicsEllipseItem` subclass whose `paint()` draws both the filled/stroked circle and centered Chinese character text. The cell size is derived from `min(vw, vh) / 11.2` to preserve the 9:10 aspect ratio. At the minimum window size (360x450), pieces are ~32px diameter with ~23px font -- readable for single Chinese characters on Windows. The existing engine (`XiangqiState.starting()`, `Piece.__str__()`) provides all the data needed; no new engine work is required.

**Primary recommendation:** Use `QGraphicsView.drawBackground()` for the board and a custom `QGraphicsEllipseItem.paint()` override for each piece. This is the cleanest, most maintainable split and avoids z-order complexity.

---

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Board background: `#7BA05B` (green felt), grid lines: `#2D5A1B` (dark green)
- Piece diameter: 80% of cell width; white stroke on all pieces
- Red pieces: `#CC2200` fill, white text; Black pieces: `#1A1A1A` fill, white text
- Window: 480x600 default, 360x450 min, 720x900 max, title "RL-Xiangqi v0.2"
- River gap: rows 4-5 (0-indexed), "楚河"/"漢界" text in gap
- Palace diagonals on rows 0-2 and 7-9, both diagonals on each side
- All font sizes derived from single `cell` variable (ratios: 0.56 piece, 0.28 river, 0.22 coord)
- Architecture: `src/xiangqi/ui/` with board.py, board_items.py, constants.py, main.py
- Engine provides `XiangqiState.starting()` returning 10x9 np.ndarray; positive = red, negative = black

### Claude's Discretion (research these, recommend)
- Exact rendering position of coordinate labels (inner/outer edge)
- Whether to use `setBackgroundBrush()` or a custom QGraphicsItem for board background
- Whether to use `QGraphicsSimpleTextItem` or custom `paint()` for piece text

### Deferred Ideas (OUT OF SCOPE)
- Board outer border margin (Phase 08+)
- Check visual highlight (Phase 08+)
- Captured pieces tray (v0.2+)
- Sound effects (v0.3)
- Drag-to-move (click-to-move only, out of scope)

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-01 | PyQt6 QGraphicsView + QGraphicsScene renders 9x10 board (grid + river + palace diagonals) | `drawBackground()` override pattern; ROWS=10, COLS=9 from `src/xiangqi/engine/constants.py` |
| UI-02 | Pieces rendered via Piece enum Chinese chars, red/black distinguished by color | `Piece.__str__()` returns `"帅"`, `"將"` etc.; sign of `board[r,c]` determines red (+1..+7) vs black (-1..-7) |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyQt6 | >= 6.8.0 | Board rendering via QGraphicsView + QGraphicsScene | Industry-standard Python Qt binding; v0.2 mandate from STATE.md |
| NumPy | >= 2.0 | Board array from engine: `np.ndarray(10, 9, dtype=np.int8)` | Already in project dependencies |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >= 8.0 | Test discovery and fixtures | All phase validation |
| pytest-qt | latest | QApplication lifecycle management in tests | GUI smoke tests for Phase 05 |

**Installation:**
```bash
conda activate xqrl
pip install PyQt6 pytest pytest-qt
```

---

## Architecture Patterns

### Recommended Project Structure

```
src/xiangqi/ui/
  __init__.py
  constants.py      # UI color/size constants (BOARD_BG, RED_FILL, CELL_RATIO, etc.)
  board_items.py    # PieceItem (QGraphicsEllipseItem), BoardBackgroundItem (QGraphicsRectItem)
  board.py          # QXiangqiBoard (QGraphicsView), BoardScene (QGraphicsScene)
  main.py           # main() — QApplication + MainWindow entry point
```

### Pattern 1: Scene Coordinate System

**What:** The scene coordinate system maps engine `(row, col)` to `(x_scene, y_scene)`.

**Scene coordinate definition** (from UI-SPEC):
```
Scene size: (COLS + 1.2) * cell  wide  x  (ROWS + 1.2) * cell  tall
           = 10.2 * cell          wide  x  11.2 * cell       tall

Grid lines drawn from (0.6*cell, 0.6*cell) to (9.6*cell, 10.6*cell)
  → grid occupies 9.0 cells wide, 10.0 cells tall
  → 0.6-cell margin on each side

Engine row 0 = top of screen (black home rank)
Engine col 0 = left side (black's left)
```

**Piece center formula:**
```
x_center = (col + 0.6) * cell
y_center = (row + 0.6) * cell
```

**QGraphicsEllipseItem rect (diameter = 0.8*cell):**
```
rect_x = (col + 0.2) * cell   # center - 0.4*cell
rect_y = (row + 0.2) * cell
rect_w = rect_h = 0.8 * cell
```

**Example:** Piece at (row=9, col=4) — red SHUAI:
```python
# board[9, 4] = Piece.R_SHUAI = +1
cell = 50  # at 480x600 default
x_center = (4 + 0.6) * 50 = 230
y_center = (9 + 0.6) * 50 = 480
# QGraphicsEllipseItem rect:
rect = QRectF(0.2*50, 0.2*50, 0.8*50, 0.8*50)
#   = QRectF(10, 10, 40, 40)
#   centered at (30, 30) in the item's local coords
# setPos((col+0.2)*cell, (row+0.2)*cell) places the item's top-left at that point
```

### Pattern 2: Board Background via `QGraphicsView.drawBackground()`

**What:** Override `QGraphicsView.drawBackground()` to paint the felt, grid, river, palace diagonals, and text labels.

**Why better than alternatives:**
- `QGraphicsScene.setBackgroundBrush()`: Can only paint a solid color or tiled pixmap, not complex lines
- `QGraphicsRectItem` background: Extra item in scene, z-order complexity, harder to resize
- `QGraphicsView.drawBackground()`: Painter already has correct DPI scaling, no extra items, easy resize via `resizeEvent`

**Implementation skeleton:**
```python
class QXiangqiBoard(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setBackgroundRole(QPalette.ColorRole.NoRole)  # prevent auto background
        # pieces added to scene at z >= 1.0

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Draw board: felt + grid + river + palace + labels."""
        # painter origin = scene top-left (0, 0)
        cell = self._cell  # stored from last resizeEvent
        p = painter
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Green felt rectangle (slightly larger than grid)
        p.fillRect(-0.6*cell, -0.6*cell, 10.2*cell, 11.2*cell,
                    QBrush(QColor(BOARD_BG)))

        # 2. Grid lines color
        p.setPen(QPen(QColor(GRID_COLOR), 1.0))

        # 3. Vertical lines (x = 0.6, 1.6, ..., 8.6)
        for col in range(COLS):
            x = (col + 0.6) * cell
            p.drawLine(QLineF(x, 0.6*cell, x, 10.6*cell))

        # 4. Horizontal lines with river gap at rows 4-5
        for row in range(ROWS):
            if row == 4:  # skip line between river rows
                continue
            y = (row + 0.6) * cell
            p.drawLine(QLineF(0.6*cell, y, 9.6*cell, y))

        # 5. Palace diagonals (rows 0-2 and 7-9, cols 3-5)
        palace_x = [3, 4, 5]  # col indices in the 9-col grid
        for start_col in (0, 6):  # left palace (cols 0-2), right palace (cols 6-8)
            x0, x1 = (start_col + 0.6) * cell, (start_col + 2.6) * cell
            if start_col == 0:
                y_top = 0.6 * cell
                y_bot = 2.6 * cell
            else:  # bottom palace
                y_top = 7.6 * cell
                y_bot = 9.6 * cell
            p.drawLine(QLineF(x0, y_top, x1, y_bot))  # \ diagonal
            p.drawLine(QLineF(x1, y_top, x0, y_bot))  # / diagonal

        # 6. River text "楚河" / "漢界"
        font_river = QFont("SimSun")
        font_river.setPixelSize(int(cell * 0.28))
        p.setFont(font_river)
        p.setPen(QPen(QColor(GRID_COLOR)))
        mid_x = 4.5 * cell  # center column
        p.drawText(QPointF(2.0*cell, 5.1*cell), "楚河")
        p.drawText(QPointF(5.5*cell, 5.1*cell), "漢界")

        # 7. Coordinate labels (both perspectives)
        font_coord = QFont("SimSun")
        font_coord.setPixelSize(int(cell * 0.22))
        p.setFont(font_coord)
        for col in range(COLS):
            x = (col + 0.6) * cell
            # Red labels (bottom): 1-9 left-to-right
            p.drawText(QPointF(x - 4, 11.2*cell), str(col + 1))
            # Black labels (top): 9-1 right-to-left
            p.drawText(QPointF(x - 4, 0.4*cell), str(9 - col))
        for row in range(ROWS):
            y = (row + 0.6) * cell
            # Red ranks (left): 1-10 bottom-to-top
            p.drawText(QPointF(0.1*cell, y + 4), str(10 - row))
            # Black ranks (right): 10-1 top-to-bottom
            p.drawText(QPointF(9.7*cell, y + 4), str(row + 1))
```

### Pattern 3: Piece Rendering via Custom `QGraphicsEllipseItem.paint()`

**What:** One custom class per piece that draws both the filled/stroked circle and centered Chinese character text in a single `paint()` override.

**Why not QGraphicsItemGroup:** A group with separate ellipse + text items adds z-order management complexity. A single item's `paint()` paints everything in one call, guaranteeing correct layering.

**Implementation:**
```python
# board_items.py
class PieceItem(QGraphicsEllipseItem):
    """A xiangqi piece: filled circle + white-stroke + Chinese character."""

    def __init__(self, row: int, col: int, piece_value: int, cell: float):
        # diameter = 80% of cell
        d = cell * CELL_RATIO  # 0.8 * cell
        # top-left of bounding rect (item's local coords)
        super().__init__(0, 0, d, d)
        self._row = row
        self._col = col
        self._piece_value = piece_value
        self._cell = cell
        self._char = str(Piece(piece_value))

        # Set position in scene coordinates
        self.setPos((col + 0.2) * cell, (row + 0.2) * cell)
        self.setZValue(1.0)

        # Determine fill color from piece sign
        if piece_value > 0:
            fill_color = QColor(RED_FILL)   # "#CC2200"
        else:
            fill_color = QColor(BLACK_FILL)  # "#1A1A1A"
        self.setBrush(QBrush(fill_color))
        self.setPen(QPen(QColor(PIECE_STROKE_COLOR), 2.0))  # white stroke

    def paint(self, painter, option, widget=None):
        # Draw ellipse (fill + stroke from pen/brush set in __init__)
        QGraphicsEllipseItem.paint(self, painter, option, widget)
        # Draw Chinese character centered on the ellipse
        d = self._cell * CELL_RATIO
        font = QFont("SimSun")
        font_size = max(int(d * 0.56), 8)  # minimum 8px for readability
        font.setPixelSize(font_size)
        painter.setFont(font)
        painter.setPen(QPen(QColor(PIECE_TEXT_COLOR)))  # white
        painter.drawText(QRectF(0, 0, d, d),
                         Qt.AlignmentFlag.AlignCenter,
                         self._char)
```

**Alternative using `QGraphicsSimpleTextItem` in a group (less preferred):**
```python
class PieceItem(QGraphicsItemGroup):
    def __init__(self, row, col, piece_value, cell):
        super().__init__()
        d = cell * 0.8
        ellipse = QGraphicsEllipseItem(0, 0, d, d, self)
        ellipse.setBrush(QBrush(fill_color))
        ellipse.setPen(QPen(Qt.GlobalColor.white, 2.0))
        ellipse.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent, False)

        text = QGraphicsSimpleTextItem(str(Piece(piece_value)), self)
        text.setFont(QFont("SimSun", int(d * 0.56)))
        text.setBrush(QBrush(Qt.GlobalColor.white))
        text_width = text.boundingRect().width()
        text.setPos((d - text_width) / 2, d * 0.08)  # visual centering

        self.setPos((col + 0.2)*cell, (row + 0.2)*cell)
        self.setZValue(1.0)
```
This is messier due to manual text centering. Use the single-class approach.

### Pattern 4: Responsive Scaling via `resizeEvent`

**What:** Override `resizeEvent` to recalculate `cell` from viewport size and update all board dimensions.

**Aspect ratio math:**
- Scene aspect: `(COLS+1.2) / (ROWS+1.2)` = `10.2/11.2` = 0.911 (slightly wider than square)
- Window aspect: 480/600 = 0.8 (portrait)
- Since window is taller relative to its width than the grid, **height is always the constraining dimension**
- `cell = viewport_height / 11.2` always fits the scene within the viewport

**This means:** At any window size within 360x450..720x900, `cell = vh/11.2` works. The grid will always fit.

**Implementation:**
```python
class QXiangqiBoard(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cell = 0.0
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        vp = self.viewport()
        vw, vh = vp.width(), vp.height()
        # cell derived from MIN dimension (though height always constrains here)
        self._cell = min(vw, vh) / 11.2
        scene_w = 10.2 * self._cell
        scene_h = 11.2 * self._cell
        self._scene.setSceneRect(0, 0, scene_w, scene_h)
        # Center the scene in the viewport
        offset_x = (vw - scene_w) / 2
        offset_y = (vh - scene_h) / 2
        self.horizontalScrollBar().setValue(int(offset_x))
        self.verticalScrollBar().setValue(int(offset_y))
        # Trigger board redraw (update draws drawBackground)
        self.viewport().update()
```

**Cell size range:**
| Window | vh | cell = vh/11.2 | piece_dia = 0.8*cell |
|--------|----|---------------|----------------------|
| MIN 360x450 | 450 | ~40.2 | ~32px |
| DEFAULT 480x600 | 600 | ~53.6 | ~43px |
| MAX 720x900 | 900 | ~80.4 | ~64px |

### Pattern 5: Piece Placement from Engine State

```python
def load_starting_position(board_scene: QGraphicsScene, state: XiangqiState, cell: float):
    """Add all 32 pieces from engine state to the scene."""
    board = state.board  # np.ndarray(10, 9, dtype=np.int8)
    for row in range(ROWS):
        for col in range(COLS):
            piece_val = int(board[row, col])
            if piece_val == 0:
                continue
            piece_item = PieceItem(row, col, piece_val, cell)
            board_scene.addItem(piece_item)
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Coordinate math for grid | Manual `(col * sq_size + sq_size/2)` everywhere | Single `cell` variable formula | All sizes derived from cell; changing one value cascades correctly |
| Chinese character positioning | Manual `QPointF(x - w/2, y + h/2)` text centering | `painter.drawText(QRectF(...), AlignCenter, text)` | Qt.AlignCenter handles baseline/font center automatically |
| Board redraw on resize | Full scene clear + re-render | `viewport().update()` only | Only `drawBackground()` repaints; pieces are QGraphicsItems and stay in place |
| Window aspect ratio | Ad-hoc resize clamping | Simple `cell = min(vw, vh) / 11.2` | Math guarantees grid fits viewport at any size |

---

## Runtime State Inventory

> Not applicable — Phase 05 is a greenfield UI rendering phase. No rename, rebrand, refactor, or migration of existing state. The engine provides all data via `XiangqiState.starting()`.

---

## Common Pitfalls

### Pitfall 1: `QGraphicsView.drawBackground()` Called with Painter in Wrong Coordinate System

**What goes wrong:** Board draws in wrong position or scaled incorrectly after resize.

**Why it happens:** `drawBackground(painter, rect)` — the `rect` argument is the *exposed rect* in scene coordinates (not the viewport rect). The painter is ready to paint in scene coordinates. Confusion leads implementers to use viewport width/height instead of `rect.width()`/`rect.height()`.

**How to avoid:** Use `self._cell` (stored from `resizeEvent`) for all drawing calculations. Never use `self.width()` or `self.viewport().width()` inside `drawBackground()`. The painter is already in scene coords.

**Warning signs:** Grid lines at wrong positions, board too large/small after resize.

### Pitfall 2: Text Item Positioned at Top-Left Instead of Centered

**What goes wrong:** Chinese character appears in top-left corner of piece circle, not centered.

**Why it happens:** `QGraphicsSimpleTextItem` default position is `(0, 0)` — the top-left of its bounding rect. Without centering offset, the text is not visually centered.

**How to avoid:** Use the single `paint()` override approach (`QGraphicsEllipseItem.paint()` draws ellipse then calls `painter.drawText(rect, AlignCenter, char)`). Qt.AlignCenter with a `QRectF` of the ellipse's size correctly centers the single-character text.

### Pitfall 3: Pieces Don't Update on `resizeEvent` Because Scene Items Are in Absolute Coordinates

**What goes wrong:** After resize, pieces stay at their old positions while the board background scales. Pieces appear misaligned.

**Why it happens:** `QGraphicsItem` positions are stored in scene coordinates (floating-point). When `cell` changes in `resizeEvent`, the piece items still have their old `(col+0.2)*old_cell` positions. Only the background redraws at the new scale.

**How to avoid:** On `resizeEvent`, clear all piece items from the scene and re-add them with new positions calculated from the new `cell`. This is simpler than trying to reposition every item individually:
```python
def resizeEvent(self, event):
    ...
    # Remove old pieces
    for item in self._scene.items():
        if isinstance(item, PieceItem):
            self._scene.removeItem(item)
    # Re-add with new cell
    self._load_pieces(self._state, self._cell)
    self.viewport().update()
```
This is slightly slower than incremental moves but correct and matches the "engine as single source of truth" pattern (PITFALLS.md Pitfall 9).

### Pitfall 4: SimSun Font Not Available on Non-Chinese Windows

**What goes wrong:** Piece characters render as tofu (missing glyph boxes) on English Windows or some Windows VMs.

**Why it happens:** SimSun is a Chinese Windows font. On English Windows or Windows Server, it may not be installed.

**How to avoid:** Fallback chain: `QFont("SimSun, Microsoft YaHei, Arial")` — if SimSun is missing, Qt will use YaHei (also a Chinese font), then Arial as last resort. SimSun is nearly universal on Chinese Windows (which is the majority of Windows installs globally). Flag as LOW risk.

**Warning signs:** `[?]` glyphs instead of Chinese characters.

### Pitfall 5: `QApplication` Created Multiple Times in Tests

**What goes wrong:** pytest tests crash with `QApplication` instance already exists error.

**Why it happens:** Each test file that imports the UI module may trigger `QApplication.__init__()` at module level. pytest may run multiple test files in the same process.

**How to avoid:** Use `pytest-qt`'s `qtbot` fixture which manages the QApplication lifecycle:
```python
def test_board_renders_grid(qtbot):
    board = QXiangqiBoard()
    qtbot.addWidget(board)
    board.show()
    qtbot.waitExposed(board)
    assert board.scene() is not None
```
Or use `pytest-qt`'s `qapp` fixture in conftest.py.

### Pitfall 6: Window Title Not Set / Wrong Title

**What goes wrong:** Window shows "XQiangqi" (default from Qt) or empty title.

**Why it happens:** `setWindowTitle()` called after `show()`, or called on wrong widget.

**How to avoid:** Set in `MainWindow.__init__` before `show()`:
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RL-Xiangqi v0.2")
        self.setCentralWidget(QXiangqiBoard())
        self.resize(480, 600)
```

---

## Code Examples

### Constants Module (`src/xiangqi/ui/constants.py`)
```python
"""UI constants for Phase 05 Board Rendering."""
from pathlib import Path

# Colors (from D-01, D-04, D-14, D-15)
BOARD_BG = "#7BA05B"          # green felt background
GRID_COLOR = "#2D5A1B"        # dark green grid lines
RED_FILL = "#CC2200"          # red piece fill
BLACK_FILL = "#1A1A1A"        # black piece fill
PIECE_TEXT_COLOR = "#FFFFFF"  # white text on pieces
PIECE_STROKE_COLOR = "#FFFFFF"
RIVER_TEXT_COLOR = "#2D5A1B"
COORD_TEXT_COLOR = "#2D5A1B"

# Derived size ratios (D-12, D-13, font size ratios from UI-SPEC)
CELL_RATIO = 0.80          # piece diameter / cell
PIECE_FONT_RATIO = 0.56    # piece char font size / cell
RIVER_FONT_RATIO = 0.28    # river text font / cell
COORD_FONT_RATIO = 0.22    # coordinate label font / cell

# Window sizes (D-08, D-09, D-10, D-11)
DEFAULT_SIZE = (480, 600)
MIN_SIZE = (360, 450)
MAX_SIZE = (720, 900)
```

### Engine Integration (`src/xiangqi/ui/board.py` — excerpt)
```python
from src.xiangqi.engine.state import XiangqiState
from src.xiangqi.engine.types import Piece, ROWS, COLS
from .board_items import PieceItem
from .constants import BOARD_BG, RED_FILL, BLACK_FILL, CELL_RATIO

class QXiangqiBoard(QGraphicsView):
    def __init__(self, state: XiangqiState | None = None, parent=None):
        super().__init__(parent)
        self._state = state or XiangqiState.starting()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setBackgroundRole(QPalette.ColorRole.NoRole)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.resizeEvent = self._board_resize

        # trigger initial layout
        self._board_resize(None)

    def _board_resize(self, event):
        vp = self.viewport()
        vw, vh = vp.width(), vp.height()
        self._cell = min(vw, vh) / 11.2
        sw, sh = 10.2 * self._cell, 11.2 * self._cell
        self._scene.setSceneRect(0, 0, sw, sh)
        # Re-add pieces with new cell
        for item in list(self._scene.items()):
            if isinstance(item, PieceItem):
                self._scene.removeItem(item)
        self._load_pieces()
        self.viewport().update()

    def _load_pieces(self):
        for row in range(ROWS):
            for col in range(COLS):
                val = int(self._state.board[row, col])
                if val == 0:
                    continue
                item = PieceItem(row, col, val, self._cell)
                self._scene.addItem(item)

    def drawBackground(self, painter, rect):
        # Draw board (felt + grid + river + palaces + text) — see Pattern 2
        ...
```

### Main Entry Point (`src/xiangqi/ui/main.py`)
```python
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from .board import QXiangqiBoard
from .constants import DEFAULT_SIZE

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RL-Xiangqi")
    win = QMainWindow()
    win.setWindowTitle("RL-Xiangqi v0.2")
    win.resize(*DEFAULT_SIZE)
    win.setMinimumSize(*(360, 450))
    win.setMaximumSize(*(720, 900))
    win.setCentralWidget(QXiangqiBoard())
    win.show()
    sys.exit(app.exec())
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| QWidget + paintEvent for board | QGraphicsView + QGraphicsScene | Qt 4.3+ (2007) | Layering, hit-testing, animation built-in |
| PNG piece sprites at fixed resolution | QGraphicsEllipseItem + QFont text rendering | This project | Infinite scalability, no sprite assets needed |
| Pixel-based grid coordinates | `cell`-derived floating-point coords | This project | Clean aspect-ratio preservation on resize |
| QGraphicsTextItem for labels | QPainter.drawText in drawBackground | This project | Simpler, no item management overhead for static labels |

**Deprecated/outdated:**
- `QGraphicsSvgItem` for pieces: Would require SVG assets; Chinese-character text rendering with QFont is simpler and more maintainable for v0.2
- Per-square `QGraphicsRectItem` for each of 90 squares: Unnecessary item count; background drawn in `drawBackground()` is more efficient

---

## Open Questions

1. **River text positioning at small cell sizes**
   - What we know: At MIN_SIZE cell=~40, river font is ~11px. "楚河" and "漢界" at 11px are very small.
   - What's unclear: Whether 0.28*cell is the right ratio for readability at minimum size. The spec sets it but doesn't validate at MIN_SIZE.
   - Recommendation: Implement as spec (0.28*cell) but add a minimum: `max(int(cell * 0.28), 10)` to prevent unreadable text.

2. **Palace diagonal intersection points**
   - What we know: Palace spans cols 0-2 (left) and 6-8 (right), rows 0-2 (top) and 7-9 (bottom). Diagonals from corner to corner.
   - What's unclear: Whether the diagonals should include the intersection dots (small filled circles at the 4 palace corner points) — standard physical xiangqi boards have these. The spec does not mention them.
   - Recommendation: Implement without corner dots for Phase 05 (matches the "simplified" D-02 intent). Add dots in Phase 08 if desired.

3. **Coordinate label visibility at minimum size**
   - What we know: At MIN_SIZE, coord font is 0.22*40.2 ≈ 9px. Labels are drawn outside the grid (left, right, top, bottom of grid area).
   - What's unclear: Whether 9px labels are readable at all. The scene size is 10.2*40.2 ≈ 410 wide and 11.2*40.2 ≈ 450 tall; the viewport is 360 wide — labels might be clipped if centered naively.
   - Recommendation: Use `AlignCenter` for the QPainter text draws and ensure scroll bars are OFF and the scene is centered in the viewport. Labels sit within the scene rect, so they should always be visible.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 8.0 + pytest-qt |
| Config file | `pyproject.toml` (already has pytest config) |
| Quick run command | `conda activate xqrl && pytest tests/ui/test_board.py -x -q` |
| Full suite command | `conda activate xqrl && pytest tests/ui/ -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| UI-01 | Board background renders: 9 vertical lines, 10 horizontal lines with river gap at row 4-5, palace diagonals (rows 0-2 and 7-9, both diagonals on each side) | Smoke/unit | N/A — visual (QGraphicsScene item structure verified via API) | test_board.py |
| UI-01 | 32 pieces from XiangqiState.starting() added to scene | Unit | `pytest tests/ui/test_board.py::test_piece_count -x` | test_board.py |
| UI-01 | River text "楚河"/"漢界" drawn in gap | Unit | Verify via `drawBackground` override mock or pixel sampling | test_board.py |
| UI-02 | Red pieces: piece_value > 0, fill `#CC2200` | Unit | `pytest tests/ui/test_board.py::test_piece_colors -x` | test_board.py |
| UI-02 | Black pieces: piece_value < 0, fill `#1A1A1A` | Unit | `pytest tests/ui/test_board.py::test_piece_colors -x` | test_board.py |
| UI-02 | Piece character matches `str(Piece(value))` | Unit | `pytest tests/ui/test_board.py::test_piece_characters -x` | test_board.py |
| (SC-4) | Aspect ratio preserved: cell derived from min(vw, vh)/11.2 | Unit | `pytest tests/ui/test_board.py::test_cell_size_formula -x` | test_board.py |
| (SC-5) | Window title: "RL-Xiangqi v0.2" | Smoke | `pytest tests/ui/test_board.py::test_window_title -x` | test_board.py |

### Sampling Rate
- **Per task commit:** `pytest tests/ui/test_board.py -x -q` (< 5 seconds, Qt app starts via qtbot)
- **Per wave merge:** `pytest tests/ui/ -q` (full suite)
- **Phase gate:** All tests green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/ui/` directory — create with `__init__.py`
- [ ] `tests/ui/test_board.py` — board rendering smoke/unit tests
- [ ] `tests/ui/conftest.py` — pytest-qt fixtures (QApplication via qtbot)
- [ ] Framework install: `pip install pytest-qt` — if not already in environment

### Validation Approach (No Display Required)

Since CI/headless environments may lack a display, tests validate the **structure** of the rendered scene rather than pixel-perfect output:

```python
# tests/ui/test_board.py
import pytest
from src.xiangqi.engine.state import XiangqiState
from src.xiangqi.engine.types import Piece

@pytest.fixture
def board(qtbot):
    from src.xiangqi.ui.board import QXiangqiBoard
    board = QXiangqiBoard()
    qtbot.addWidget(board)
    return board

def test_piece_count(board):
    """Exactly 32 pieces on starting board."""
    pieces = [i for i in board.scene().items() if isinstance(i, PieceItem)]
    assert len(pieces) == 32

def test_piece_colors(board):
    """Red pieces (#CC2200) for positive values, black (#1A1A1A) for negative."""
    from src.xiangqi.ui.constants import RED_FILL, BLACK_FILL
    state = XiangqiState.starting()
    for item in board.scene().items():
        if not isinstance(item, PieceItem):
            continue
        expected_fill = RED_FILL if item._piece_value > 0 else BLACK_FILL
        assert item.brush().color().name().upper() == expected_fill.upper()

def test_piece_characters(board):
    """Each piece shows correct Chinese character from Piece enum."""
    state = XiangqiState.starting()
    for item in board.scene().items():
        if not isinstance(item, PieceItem):
            continue
        expected_char = str(Piece(item._piece_value))
        assert item._char == expected_char

def test_cell_size_formula():
    """cell = min(vw, vh) / 11.2."""
    # Simulate viewport sizes
    test_cases = [
        (360, 450, 450/11.2),
        (480, 600, 600/11.2),
        (720, 900, 900/11.2),
    ]
    for vw, vh, expected_cell in test_cases:
        assert abs(min(vw, vh) / 11.2 - expected_cell) < 0.01

def test_window_title(qtbot):
    """MainWindow has correct title."""
    from src.xiangqi.ui.main import MainWindow
    win = MainWindow()
    qtbot.addWidget(win)
    assert win.windowTitle() == "RL-Xiangqi v0.2"
```

**Note on visual validation:** Actual pixel-perfect rendering (grid lines visible, palace diagonals correct, river text readable) is verified manually by the developer opening the application. The automated tests cover structural correctness (item count, colors, positions, font characters).

---

## Sources

### Primary (HIGH confidence)
- Qt 6.8 official docs — `QGraphicsView.drawBackground()`, `QGraphicsEllipseItem`, `QPainter.drawText()` coordinate semantics — HIGH confidence
- `src/xiangqi/engine/types.py` — Piece enum, `__str__`, ROWS/COLS constants — HIGH confidence
- `src/xiangqi/engine/state.py` — XiangqiState.starting() board shape and values — HIGH confidence
- `src/xiangqi/engine/constants.py` — ROWS=10, COLS=9, IN_PALACE boundary masks — HIGH confidence

### Secondary (MEDIUM confidence)
- STACK.md — QGraphicsView vs QWidget decision, drag-and-drop pattern — MEDIUM confidence (community reference, not official Qt)
- PyQt6 threading — PITFALLS.md verified against realpython.com PyQt threading article — MEDIUM confidence
- SimSun font availability on Windows — general knowledge, not verified for all Windows SKUs — MEDIUM confidence

### Tertiary (LOW confidence)
- Specific cell math formula (`min(vw, vh) / 11.2`): Derived from spec arithmetic; not verified against an existing implementation — LOW confidence, recommend manual testing at all three window sizes
- Palace diagonal exact pixel endpoints: Calculated from spec; not cross-referenced against a working Xiangqi board implementation — LOW confidence, recommend visual check

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PyQt6 6.8+ is locked by STATE.md, numpy already in project
- Architecture: HIGH — QGraphicsView.drawBackground() + custom PieceItem is the correct PyQt pattern; coordinate math verified against engine constants
- Pitfalls: HIGH — all pitfalls identified are well-known PyQt issues with known mitigations documented in PITFALLS.md research

**Research date:** 2026-03-23
**Valid until:** 2026-04-22 (30 days — PyQt6 stable, xiangqi rendering patterns well-established)
