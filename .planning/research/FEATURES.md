# Feature Research: Xiangqi PyQt6 UI

**Domain:** PyQt6 Desktop UI for Human-vs-AI Xiangqi
**Context:** v0.3 milestone — working board that validates engine integration and exposes a clean AI plugin interface
**Researched:** 2026-03-23
**Confidence:** HIGH (PyQt6 QGraphicsView board pattern is well-established; engine API confirmed from existing codebase)

---

## Scope Note

The existing `.planning/research/FEATURES.md` covers the **rule engine** (v0.1). This document covers **UI features only** (v0.3 milestone). The two are complementary: the UI consumes the engine's `XiangqiEngine` API.

**Engine API already built (v0.1):**

```python
engine = XiangqiEngine.starting()     # classmethod
engine.board       # np.ndarray(10, 9) — piece integers
engine.turn        # +1 (red) / -1 (black)
engine.legal_moves()    # list[int] — 16-bit encoded moves
engine.is_legal(move)  # bool
engine.is_check()       # bool
engine.result()        # 'RED_WINS'|'BLACK_WINS'|'DRAW'|'IN_PROGRESS'
engine.apply(move)     # returns captured piece int
engine.undo()          # reverse last move
engine.move_history    # list[int]
engine.to_fen()        # str serialization
engine.reset()         # restart from starting position
```

The UI's job is to **visualize** this state, **translate** mouse interactions into encoded moves, and **bridge** to an AI plugin. Not a polished commercial product.

---

## Feature Landscape

### Table Stakes (Working Human-vs-AI Board)

These features make the board playable at all. Missing any of these means the board is broken.

| Feature | Why Required | Complexity | Notes |
|---------|--------------|------------|-------|
| **Board geometry** | The 9x10 intersection grid is the core visual primitive | LOW | Vertical lines x9, horizontal lines x10; river gap at rows 4-5; palace diagonal boxes at rows 0-2 and 7-9 |
| **Piece placement from engine state** | UI must reflect current board array | LOW | Iterate `engine.board`, place piece widgets at each non-empty intersection |
| **Click-to-select piece** | Only one interaction mode needed for minimum viable product | LOW | Click a piece of the side-to-move → highlight it |
| **Click-to-move** | Complete the move by clicking destination | LOW | After selecting a piece, click a legal destination to apply the move |
| **Move application via engine** | The engine owns all rule validation | LOW | `engine.apply(encoded_move)` — if illegal, engine raises `ValueError`; UI shows feedback |
| **Turn management** | Alternating play is fundamental | LOW | Toggle on every applied move; disable human interaction during AI turn |
| **Board re-render on state change** | Visual board must track engine state | LOW | After `apply()`, re-render all pieces from `engine.board` |
| **New Game / Reset** | Basic replayability | LOW | `engine.reset()` + clear move history display + clear captured pieces |
| **Game over display** | User needs to know when the game ends | LOW | Read `engine.result()` after each move; show modal or status text |
| **AI move execution** | Human-vs-AI requires AI to respond | MEDIUM | `GameController` QThread calls AI plugin, applies move to engine, signals UI update |

### Nice-to-Have (UX Quality)

These do not block the board from working but significantly improve usability.

| Feature | Value | Complexity | Notes |
|---------|-------|------------|-------|
| **Legal move highlighting** | Prevents users from making illegal moves by accident | LOW | On piece selection, highlight legal-destination intersections via `engine.legal_moves()` |
| **Drag-and-drop** | Faster play for experienced users | MEDIUM | Override `mouseMoveEvent` on `QGraphicsView`; snap piece to nearest intersection on release |
| **Captured pieces display** | Shows game progress and material balance | LOW | Maintain two lists (red captured, black captured); update on each `apply()` return value |
| **Current turn indicator** | Shows whose move it is at a glance | LOW | Colored label or piece count in sidebar: "Red to move" / "Black to move" |
| **In-check visual warning** | Critical game state signal | LOW | If `engine.is_check()` is True, flash the king's square or show a status banner |
| **Move history log** | Reference during and after play | MEDIUM | List widget showing WXF or ICCS notation per move; decoded from `engine.move_history` |
| **Board flip** | Black-side perspective for review | LOW | Rotate `QGraphicsView` 180 degrees via `QTransform.rotate(180)` |

### Anti-Features

Features to explicitly NOT build for v0.3. Adding them wastes time and adds scope risk.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|--------------------|
| **Time controls / clocks** | Not needed for AI-vs-human validation; belongs to competitive play | Defer to v1.0+ |
| **PGN/WXF game save/load** | Nice but not required to validate engine integration | Implement only if time remains |
| **Multiple game tabs** | Over-architecture for a single-board AI validator | One board, one game at a time |
| **Sound effects** | Distracting for RL development workflow | Never |
| **Settings dialogs** | Config that the engine/AI should own | Keep hardcoded defaults |
| **Hint / undo AI moves** | Confuses the AI-vs-human validation model | Defer to v1.0+ |
| **Network / online play** | Anti-feature for a local AI training tool | Never |

---

## Feature Details

### 1. Board Geometry

The xiangqi board is a 9-column by 10-row grid of **intersection points**, not grid cells.

**Coordinate system (from existing engine):**
```
Rows: 0 = black's back rank (top of display)
      9 = red's back rank (bottom of display)
Cols: 0–8 (left to right from red's perspective)
```

**Drawing elements:**
- 9 vertical lines, 10 horizontal lines → 90 intersection points
- River band between rows 4 and 5 (horizontal gap with "楚河汉界" text)
- Palace box: rows 0–2, cols 3–5 (black's palace, top)
- Palace box: rows 7–9, cols 3–5 (red's palace, bottom)
- Palace diagonal lines: connect (row,3)↔(row+2,5) and (row+2,3)↔(row,5) for both palaces
- Optional: small tick marks at the 5 palace intersection points

**Recommended rendering approach:**
Override `QGraphicsView.drawBackground()` or paint on a dedicated `QGraphicsPixmapItem` background. Use `QPainter` to draw all lines, the river band, and palace diagonals once. Cache the result as a `QPixmap` so the board background does not need to be repainted on every interaction.

```python
def _paint_board_background(self, painter: QPainter, rect: QRectF):
    """Paint all static board elements: grid, river, palace diagonals."""
    pen = QPen(QColor("#8B4513"), 2)
    painter.setPen(pen)

    # Vertical lines (9 columns)
    for col in range(9):
        x = self._col_to_x(col)
        painter.drawLine(x, self._row_to_y(0), x, self._row_to_y(9))

    # Horizontal lines (10 rows) — broken at cols 3 and 6 in rows 3 and 6 (palace top/bottom)
    for row in range(10):
        y = self._row_to_y(row)
        start_col = 0
        end_col = 9
        # Palace: rows 0-2 (black palace) and 7-9 (red palace) break at cols 3 and 6
        if row in (0, 2, 7, 9):
            painter.drawLine(self._col_to_x(0), y, self._col_to_x(3), y)
            painter.drawLine(self._col_to_x(5), y, self._col_to_x(8), y)
        elif row == 1 or row == 8:
            # Palace corners connect diagonally
            pass
        else:
            painter.drawLine(self._col_to_x(start_col), y, self._col_to_x(end_col - 1), y)

    # Palace diagonals
    # Black palace (rows 0-2): (0,3)-(2,5) and (0,5)-(2,3)
    painter.drawLine(self._col_to_x(3), self._row_to_y(0), self._col_to_x(5), self._row_to_y(2))
    painter.drawLine(self._col_to_x(5), self._row_to_y(0), self._col_to_x(3), self._row_to_y(2))
    # Red palace (rows 7-9): same diagonals at rows 7-9
    painter.drawLine(self._col_to_x(3), self._row_to_y(7), self._col_to_x(5), self._row_to_y(9))
    painter.drawLine(self._col_to_x(5), self._row_to_y(7), self._col_to_x(3), self._row_to_y(9))

    # River text
    font = QFont("Serif", 14, QFont.Bold)
    painter.setFont(font)
    painter.drawText(self._board_rect, Qt.AlignmentFlag.AlignCenter, "楚河汉界")
```

**Coordinate mapping:**
```python
def _row_to_y(self, row: int) -> float:
    return self._top_margin + row * self._cell_size

def _col_to_x(self, col: int) -> float:
    return self._left_margin + col * self._cell_size

def _xy_to_rc(self, x: float, y: float) -> Tuple[int, int] | None:
    """Convert pixel coordinates to (row, col) or None if outside tolerance."""
    col = round((x - self._left_margin) / self._cell_size)
    row = round((y - self._top_margin) / self._cell_size)
    if 0 <= row < 10 and 0 <= col < 9:
        return row, col
    return None
```

### 2. Piece Representation

Two viable approaches, ranked by recommendation:

**Approach A: Unicode Chess Symbols (Recommended for MVP)**

Unicode 11.0 (2018) added xiangqi pieces in the Chess Symbols block U+1FA60–U+1FA6D:

| Piece | Red Unicode | Black Unicode |
|-------|------------|--------------|
| General | U+1FA60 (🩠) | U+1FA67 (🩧) |
| Advisor | U+1FA61 (🩡) | U+1FA68 (🩨) |
| Elephant | U+1FA62 (🩢) | U+1FA69 (🩩) |
| Horse | U+1FA63 (🩣) | U+1FA6A (🩪) |
| Chariot | U+1FA64 (🩤) | U+1FA6B (🩫) |
| Cannon | U+1FA65 (🩥) | U+1FA6C (🩬) |
| Soldier | U+1FA66 (🩦) | U+1FA6D (🩭) |

**Implementation:** `QGraphicsSimpleTextItem` with a font that supports the Chess Symbols block. The [BabelStone Xiangqi font](https://www.babelstone.co.uk/Fonts/Xiangqi.html) covers the full block and is free. Fall back to traditional Chinese characters (帥仕相馬車炮兵 / 将士象马车炮卒) rendered via `QGraphicsTextItem` with a CJK font — these are already defined in the existing engine's `Piece.__str__` method.

**Font stack for broad compatibility:**
```python
# Primary: Unicode chess symbols with BabelStone Xiangqi
# Fallback: Chinese characters with system CJK font
font = QFont("BabelStone Xiangqi", size)
if not QFontInfo(font).exactMatch():
    font = QFont("Noto Sans CJK SC", size)   # or "Microsoft YaHei" on Windows
piece_item.setFont(font)
piece_item.setText("\U0001fa60")   # Red General
```

**Approach B: SVG Piece Graphics**

Higher visual quality but adds asset management. See the [xiangqi-setup](https://github.com/hartwork/xiangqi-setup) project for SVG piece sets. Use `QGraphicsSvgItem` wrapped in a `QGraphicsItemGroup` for centering. SVG pieces are the approach taken by [ChessQ](https://github.com/walker8088/ChessQ) (a production PyQt Xiangqi app). For v0.3 MVP, Approach A is faster to implement.

**Piece rendering from engine board:**
```python
_PIECE_TO_UNICODE = {
    Piece.R_SHUAI: "\U0001fa60", Piece.R_SHI: "\U0001fa61",
    Piece.R_XIANG: "\U0001fa62", Piece.R_MA: "\U0001fa63",
    Piece.R_CHE: "\U0001fa64",  Piece.R_PAO: "\U0001fa65",
    Piece.R_BING: "\U0001fa66",
    Piece.B_JIANG: "\U0001fa67", Piece.B_SHI: "\U0001fa68",
    Piece.B_XIANG: "\U0001fa69", Piece.B_MA: "\U0001fa6a",
    Piece.B_CHE: "\U0001fa6b",   Piece.B_PAO: "\U0001fa6c",
    Piece.B_ZU: "\U0001fa6d",
}

def render_board(self, board: np.ndarray):
    """Remove all piece items, then place a piece at each non-empty square."""
    for item in self._scene.items():
        if isinstance(item, PieceGraphicsItem):
            self._scene.removeItem(item)
    for row in range(ROWS):
        for col in range(COLS):
            piece_val = board[row, col]
            if piece_val != 0:
                item = PieceGraphicsItem(piece_val, row, col)
                self._scene.addItem(item)
```

### 3. Captured Pieces Display

Maintain two `QGridLayout` or `QVBoxLayout` panels — one per side — showing captured pieces grouped by type. Update whenever `engine.apply()` returns a non-zero captured value.

**Recommended layout:**
```
┌─────────────────────────────┐
│  Captured by Red  [兵 兵 炮] │
│  Captured by Black [車 馬]   │
└─────────────────────────────┘
```

**Implementation:** Use `QListWidget` with one item per captured piece, or a `QHBoxLayout` of small `QLabel` widgets. When a piece is captured, append it to the appropriate panel. Sort captured pieces by value (Chariot first, Soldier last) for quick material assessment.

```python
def on_move_applied(self, captured_piece: int):
    """Update captured pieces panel after engine.apply()."""
    if captured_piece == 0:
        return
    color = "Red" if captured_piece > 0 else "Black"
    panel = self._captured_by_red if captured_piece > 0 else self._captured_by_black
    unicode_char = _PIECE_TO_UNICODE.get(captured_piece, "?")
    panel.addWidget(QLabel(unicode_char))   # styled to match piece color
```

### 4. Turn Indicator

Simple text label in the sidebar or status bar. State derives entirely from `engine.turn`.

```python
def update_turn_indicator(self):
    color = "Red" if self._engine.turn == +1 else "Black"
    self._turn_label.setText(f"{color} to move")
    # Style the label: red text for red turn, dark for black
    palette = self._turn_label.palette()
    palette.setColor(QPalette.WindowText,
                     QColor("#c41e3a") if self._engine.turn == +1 else QColor("#1a1a1a"))
    self._turn_label.setPalette(palette)
```

### 5. Legal Move Highlighting

On piece selection, call `engine.legal_moves()`, decode each move to `to_sq`, and overlay highlights on destination intersections. This is the single highest-value UX feature for a working board — it eliminates guesswork about legal moves.

**Cache at turn start, not per-click:**
```python
def on_piece_selected(self, row: int, col: int):
    # Only compute highlights when a piece is clicked
    all_legal = self._engine.legal_moves()
    from_sq = row * 9 + col
    destinations = set()
    for move in all_legal:
        if (move & 0x1FF) == from_sq:
            to_sq = (move >> 9) & 0x7F
            tr, tc = divmod(to_sq, 9)
            destinations.add((tr, tc))
    self._show_highlights(destinations)
```

**Highlight rendering:** `QGraphicsEllipseItem` at each destination, filled with semi-transparent green (`rgba(0, 200, 0, 80)`). Clear highlights on any subsequent click.

### 6. Game State Display

**In-check warning:** If `engine.is_check()` returns True after a move, display a status banner or flash the king's square in red. This is the most important game-state signal.

**Game over:** After each `engine.apply()`, check `engine.result()`. If not `'IN_PROGRESS'`:

```python
def on_engine_updated(self):
    result = self._engine.result()
    if result != 'IN_PROGRESS':
        self._show_game_over_dialog(result)
```

**Game over dialog:** `QMessageBox` or a styled `QDialog` showing the result ("Red Wins", "Black Wins", "Draw") and a "New Game" button. Disable board interaction.

### 7. Clean Reset / New Game Flow

One button that resets everything to initial state:

```python
def new_game(self):
    self._engine.reset()
    self._captured_by_red.clear()
    self._captured_by_black.clear()
    self._move_history.clear()
    self._render_board()
    self._update_turn_indicator()
    self._clear_highlights()
    self._status_label.setText("New game — Red to move")
    # Re-enable board interaction
    self._set_interaction_enabled(True)
```

### 8. AI Plugin Interface

The board must expose a clean interface for plugging in any AI agent. The existing architecture defines this as a `GameController` QThread.

**Interface contract:**
```python
class AIAgent(ABC):
    """Abstract interface that any AI plugin must implement."""

    @abstractmethod
    def select_move(self, engine: XiangqiEngine) -> int:
        """Given the current engine state, return an encoded move (int).
        Must return a legal move. Raises if no legal moves exist."""
        ...
```

**QThread integration pattern:**
```python
class GameController(QThread):
    move_ready = pyqtSignal(int)          # AI has chosen a move
    thinking_started = pyqtSignal()
    thinking_finished = pyqtSignal()

    def __init__(self, engine: XiangqiEngine, agent: AIAgent):
        super().__init__()
        self._engine = engine
        self._agent = agent

    def request_move(self):
        """Called by UI when it's the AI's turn."""
        self.start()   # runs self.run() in a QThread

    def run(self):
        self.thinking_started.emit()
        move = self._agent.select_move(self._engine)
        self.move_ready.emit(move)    # emitted in the QThread
        self.thinking_finished.emit()
```

**UI slot:**
```python
class BoardWidget:
    def _on_ai_move_ready(self, move: int):
        try:
            captured = self._engine.apply(move)
            self._render_board()
            self._update_turn_indicator()
            self._update_captured(captured)
            self._check_game_over()
            self._set_interaction_enabled(True)
        except ValueError:
            # AI returned an illegal move — log and retry
            logging.error(f"AI returned illegal move {move}")
```

---

## Feature Dependencies

```
Board Rendering
    |--requires--> Board geometry (grid, river, palace)
    |--requires--> Piece placement from engine.board
    |--requires--> Coordinate mapping (px <-> rc)

Piece Selection
    |--requires--> Click-to-select handler (mousePressEvent)
    |--requires--> Turn-aware: only select current player's pieces
    |--requires--> Legal move highlighting (on selection)

Move Application
    |--requires--> Click-to-move handler (mousePressEvent on highlighted square)
    |--requires--> Move encoding: (row, col) -> 16-bit engine move
    |--requires--> engine.apply(move) — raises on illegal
    |--requires--> Board re-render after apply()

AI Integration
    |--requires--> GameController QThread (never block UI thread)
    |--requires--> AIAgent plugin interface
    |--requires--> pyqtSignal/pyqtSlot bridge (QThread -> UI thread)
    |--requires--> Turn management (disable human input during AI thinking)

Game State
    |--requires--> engine.is_check() — in-check warning
    |--requires--> engine.result() — game over detection
    |--requires--> engine.reset() — new game

Captured Pieces
    |--requires--> engine.apply() return value (captured piece int)
    |--requires--> Two-panel layout (one per side)
```

---

## MVP Recommendation

**Build in this order for v0.3:**

1. **Board geometry only** — static background rendering. Verify it looks correct before adding pieces.
2. **Static piece placement** — read `engine.board`, place all pieces. No interaction yet.
3. **Click-to-select + legal move highlighting** — wire `engine.legal_moves()` to highlight overlays.
4. **Click-to-move + engine.apply()** — complete the human move loop.
5. **Turn management** — toggle on each apply, disable input during AI turn.
6. **AI plugin interface + GameController QThread** — stub agent returning a random legal move.
7. **New Game / Reset** — one-button restart.
8. **Captured pieces display** — update on each apply.
9. **In-check + game over** — `engine.is_check()` and `engine.result()` wired to UI.
10. **Human-vs-stub-AI end-to-end test** — play 5 full games, verify no crashes or illegal state.

**Defer:** Drag-and-drop (click-to-move is sufficient for v0.3), board flip, move history log.

---

## Architecture Integration Points

The UI layer sits above the v0.1 `XiangqiEngine`. Key integration points:

| UI Component | Engine Method | Notes |
|-------------|--------------|-------|
| `BoardWidget._render_board()` | `engine.board` property | Read-only; triggers scene rebuild |
| `BoardWidget._on_square_clicked()` | `engine.legal_moves()`, `engine.is_legal()` | Filter to selected piece's moves |
| `BoardWidget._on_destination_clicked()` | `engine.apply(move)` | Raises `ValueError` on illegal; UI shows feedback |
| `GameController` | `engine.legal_moves()` inside agent | AI must call this to pick legal moves only |
| `CapturedPanel` | `engine.apply()` return value | Captured piece int, 0 if none |
| `StatusBar` | `engine.is_check()`, `engine.turn` | Re-evaluate after every apply |
| `GameOverDialog` | `engine.result()` | Check after every apply |
| `NewGameButton` | `engine.reset()` | Clears all UI state too |

---

## Sources

- [ChessQ — PyQt Xiangqi GUI](https://github.com/walker8088/ChessQ) — active PyQt Xiangqi project, last updated Feb 2025 — MEDIUM confidence
- [xiangqi-setup — FEN to SVG rendering](https://github.com/hartwork/xiangqi-setup) — SVG rendering approach for xiangqi boards — MEDIUM confidence
- [Xiangqi Unicode Characters — Compart](https://www.compart.com/en/unicode/U+1FA62) — Unicode U+1FA60–U+1FA6D range confirmed — HIGH confidence
- [BabelStone Xiangqi Font](https://www.babelstone.co.uk/Fonts/Xiangqi.html) — free font covering full Unicode chess symbols block — HIGH confidence
- [QGraphicsView Qt6 Documentation](https://doc.qt.io/qt-6/qgraphicsview.html) — official Qt docs — HIGH confidence
- [PyQt6 QGraphicsView Tutorial — SteamXO](https://steam.oxxostudio.tw/category/python/pyqt6/qgraphicsview.html) — tutorial — MEDIUM confidence
- [Chinese Chess Board Design — CSDN](https://blog.csdn.net/weixin_43401773/article/details/147174764) — board drawing patterns in Python — MEDIUM confidence
- [Qt C++ Chinese Chess Implementation — CSDN](https://blog.csdn.net/u011463646/article/details/145601419) — QGraphicsView/Scene architecture for xiangqi — MEDIUM confidence
- [python-chess SVG rendering](https://python-chess.readthedocs.io/en/latest/svg.html) — SVG rendering pattern reference for chess boards — HIGH confidence

---

*Feature research for: RL-Xiangqi v0.3 PyQt6 UI*
*Researched: 2026-03-23*
