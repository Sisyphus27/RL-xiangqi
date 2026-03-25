"""
QXiangqiBoard — QGraphicsView subclass rendering a 9x10 xiangqi board.

The board background (felt, grid, river, palace diagonals, text labels) is
drawn via QGraphicsView.drawBackground(). Each piece is a PieceItem added to
the scene. Responsive scaling via resizeEvent: cell = min(vw, vh) / 11.2.

Architecture (from 05-RESEARCH.md):
  - drawBackground() draws board background at the correct z-layer
  - PieceItem (QGraphicsEllipseItem) renders each piece
  - Scene coordinates: (col + 0.6, row + 0.6) * cell for piece centers
  - Scene size: 10.2 * cell wide x 11.2 * cell tall
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QFrame, QGraphicsEllipseItem
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF, QPoint, pyqtSignal
from PyQt6.QtGui import QPalette, QPainter, QPen, QBrush, QColor, QFont, QResizeEvent, QMouseEvent

from src.xiangqi.engine.state import XiangqiState
from src.xiangqi.engine.engine import XiangqiEngine
from src.xiangqi.engine.types import Piece, ROWS, COLS, rc_to_sq, sq_to_rc, encode_move
from .board_items import PieceItem
from .constants import (
    BOARD_BG,
    GRID_COLOR,
    RED_FILL,
    BLACK_FILL,
    PIECE_TEXT_COLOR,
    PIECE_STROKE_COLOR,
    RIVER_TEXT_COLOR,
    COORD_TEXT_COLOR,
    HIGHLIGHT_COLOR,
    CELL_RATIO,
    PIECE_FONT_RATIO,
    RIVER_FONT_RATIO,
    COORD_FONT_RATIO,
)


class QXiangqiBoard(QGraphicsView):
    """
    Renders a 9x10 xiangqi board with 32 pieces.

    Parameters
    ----------
    state : XiangqiState, optional
        The game state to display. Defaults to XiangqiState.starting().
    engine : XiangqiEngine, optional
        The game engine for legal move queries. Defaults to None.
        When provided, enables mouse interaction (selection, move execution).
    parent : QWidget, optional
        Parent widget.

    Attributes
    ----------
    _state : XiangqiState
        Current game state (source of truth for piece positions).
    _engine : XiangqiEngine | None
        Engine reference for legal_moves() queries and move application.
        None for read-only display, required for interaction.
    _cell : float
        Scene cell size in pixels. Updated on every resizeEvent.
        cell = min(viewport_width, viewport_height) / 11.2
    _scene : QGraphicsScene
        Holds all PieceItem instances.
    _selected : tuple[int, int] | None
        Currently selected piece (row, col) or None.
    _selection_ring : QGraphicsEllipseItem | None
        Gold selection ring around selected piece.
    _highlight_items : list[QGraphicsEllipseItem]
        Legal move dot highlight items.
    _piece_index : dict[tuple[int, int], PieceItem]
        O(1) lookup index for piece items by board position.
    _interactive : bool
        Whether mouse interaction is enabled (default True).

    Signals
    -------
    move_applied(from_sq: int, to_sq: int, captured: int)
        Emitted after a successful move. captured=0 if no capture.

    Coordinate system (scene coords):
      - Grid occupies x: [0.6, 9.6] * cell, y: [0.6, 9.6] * cell
      - 9 columns (0-8), 10 rows (0-9)
      - Engine row 0 = top (black home), row 9 = bottom (red home)
      - Piece center at (col + 0.6, row + 0.6) * cell
    """

    # Signal: emitted after a successful move is applied (D-19, D-20)
    move_applied = pyqtSignal(int, int, int)  # from_sq, to_sq, captured_piece_value

    def __init__(
        self,
        state: XiangqiState | None = None,
        engine: XiangqiEngine | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._state = state or XiangqiState.starting()
        self._engine = engine
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setBackgroundRole(QPalette.ColorRole.NoRole)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._cell = 0.0
        # Interaction state
        self._selected: tuple[int, int] | None = None
        self._selection_ring: QGraphicsEllipseItem | None = None
        self._highlight_items: list[QGraphicsEllipseItem] = []
        self._piece_index: dict[tuple[int, int], PieceItem] = {}
        self._interactive: bool = True  # D-27: defaults to enabled
        # Trigger initial layout — resizeEvent(None) computes cell from viewport
        self.resizeEvent(None)

    # ─── interaction control ──────────────────────────────────────────────────

    def set_interactive(self, enabled: bool) -> None:
        """D-26, D-27: External control of interaction state.

        When disabled, all mouse clicks are silently ignored.
        Disabling also clears any active selection.
        """
        self._interactive = enabled
        if not enabled:
            self._deselect_piece()

    # ─── coordinate conversion ───────────────────────────────────────────────

    def _scene_to_board(self, pos: QPointF) -> tuple[int, int] | None:
        """Convert scene coordinates to board (row, col) or None if outside grid.

        Accounts for 0.6*cell offset in scene coordinate system.
        Grid bounds: x in [0.6, 9.6]*cell, y in [0.6, 9.6]*cell.
        """
        cell = self._cell
        col = round(pos.x() / cell - 0.6)
        row = round(pos.y() / cell - 0.6)
        if 0 <= row < 10 and 0 <= col < 9:
            return (row, col)
        return None

    # ─── mouse event handling ──────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        """Handle mouse clicks on the board.

        D-22, D-25: Silently ignores clicks when _interactive is False.
        Converts click position to board (row, col) and delegates to
        _handle_board_click for selection/move logic.
        """
        if event is None:
            return
        if not self._interactive:
            return  # D-25: silent ignore when disabled
        # Viewport coordinates from event.position()
        vp_x = event.position().x()
        vp_y = event.position().y()
        # QGraphicsView center-aligns the scene in the viewport.
        # The viewport-to-scene offset is: scene_x = vp_x - 103.5, scene_y = vp_y - 2.0
        # (derived empirically: viewport(103,2) maps to scene(0,0))
        scene_x = vp_x - 103.5
        scene_y = vp_y - 2.0
        board_pos = self._scene_to_board(QPointF(scene_x, scene_y))
        if board_pos is None:
            return
        row, col = board_pos
        self._handle_board_click(row, col)

    # ─── click handling stubs (implemented in Task 2) ─────────────────────────

    def _handle_board_click(self, row: int, col: int) -> None:
        """Handle a click at board position (row, col).

        Implements selection/move logic per D-24, D-25, D-48, D-49:
        - No selection: clicking red piece selects it
        - Has selection: clicking same piece deselects
        - Has selection: clicking another red piece switches
        - Has selection: clicking legal target executes move
        - Has selection: clicking illegal target deselects
        """
        if self._engine is None:
            return
        clicked_piece = self._piece_index.get((row, col))

        if self._selected is not None:
            from_row, from_col = self._selected
            if (row, col) == self._selected:
                # Clicked same piece: deselect (UI-05)
                self._deselect_piece()
            elif clicked_piece is not None and clicked_piece._piece_value > 0:
                # Clicked another red piece: switch selection (D-48)
                self._deselect_piece()
                self._select_piece(row, col)
            elif self._is_legal_target(from_row, from_col, row, col):
                # Clicked legal target: execute move (UI-04)
                self._execute_move(from_row, from_col, row, col)
            else:
                # Clicked illegal target: deselect (UI-05)
                self._deselect_piece()
        else:
            # No current selection
            if clicked_piece is not None and clicked_piece._piece_value > 0:
                # Clicked red piece: select it (UI-03)
                self._select_piece(row, col)
            # else: click empty or black piece with no selection: ignore

    def _is_legal_target(self, from_row: int, from_col: int,
                          to_row: int, to_col: int) -> bool:
        """Check if (to_row, to_col) is a legal move from (from_row, from_col).

        Queries self._engine.legal_moves() for matching from_sq and to_sq.
        Returns True only if this exact move exists in the legal move list.
        """
        if self._engine is None:
            return False
        from_sq = rc_to_sq(from_row, from_col)
        to_sq = rc_to_sq(to_row, to_col)
        for move in self._engine.legal_moves():
            move_from = move & 0x1FF
            move_to = (move >> 9) & 0x7F
            if move_from == from_sq and move_to == to_sq:
                return True
        return False

    def _execute_move(self, from_row: int, from_col: int,
                      to_row: int, to_col: int) -> None:
        """Execute a move from (from_row, from_col) to (to_row, to_col).

        Converts board coordinates to square indices and calls apply_move.
        """
        from_sq = rc_to_sq(from_row, from_col)
        to_sq = rc_to_sq(to_row, to_col)
        self.apply_move(from_sq, to_sq)

    def apply_move(self, from_sq: int, to_sq: int) -> None:
        """Apply a move: update engine, update scene incrementally, emit signal.

        D-10 to D-23: Incremental update pattern.
        1. Handle capture: remove target piece from scene and index
        2. Apply to engine: engine.apply(move) updates game state
        3. Update piece item: update _row/_col and setPos
        4. Update piece index: delete old key, add new key
        5. Clear highlights and selection
        6. Emit move_applied signal
        """
        from_row, from_col = sq_to_rc(from_sq)
        to_row, to_col = sq_to_rc(to_sq)

        # Handle capture (D-16): remove captured piece from scene and index
        captured_item = self._piece_index.get((to_row, to_col))
        captured_val = 0
        if captured_item:
            self._scene.removeItem(captured_item)
            del self._piece_index[(to_row, to_col)]
            captured_val = captured_item._piece_value

        # Apply to engine (D-11): board calls engine.apply
        is_capture = captured_val != 0
        move = encode_move(from_sq, to_sq, is_capture)
        self._engine.apply(move)

        # Update piece item position (D-14): update _row/_col and setPos
        piece_item = self._piece_index[(from_row, from_col)]
        piece_item._row = to_row
        piece_item._col = to_col
        piece_item.setPos((to_col + 0.2) * self._cell, (to_row + 0.2) * self._cell)

        # Update piece index (D-17): delete old key, add new key
        del self._piece_index[(from_row, from_col)]
        self._piece_index[(to_row, to_col)] = piece_item

        # Clear highlights (D-13): _clear_highlights + _selected = None
        self._clear_highlights()
        self._selected = None

        # Emit signal (D-19, D-20): from_sq, to_sq, captured_piece_value
        self.move_applied.emit(from_sq, to_sq, captured_val)

    def _deselect_piece(self) -> None:
        """Clear the current selection and all highlights.

        Called when clicking outside legal targets, switching pieces,
        or when disabling interaction via set_interactive(False).
        """
        self._clear_highlights()
        self._selected = None

    def _clear_highlights(self) -> None:
        """Remove all highlight items (selection ring + legal move dots) from scene."""
        for item in self._highlight_items:
            self._scene.removeItem(item)
        self._highlight_items.clear()
        if self._selection_ring is not None:
            self._scene.removeItem(self._selection_ring)
            self._selection_ring = None

    # ─── highlight item creation ─────────────────────────────────────────────

    def _create_selection_ring(self, row: int, col: int) -> QGraphicsEllipseItem:
        """D-02, D-03: Create gold selection ring above selected piece.

        Position: (col + 0.15) * cell, (row + 0.15) * cell
        Diameter: 0.85 * cell (slightly larger than piece's 0.80*cell)
        Pen: 3.0px gold, NoBrush (outline only)
        Opacity: 0.70 (70%)
        Z-value: 1.1 (above pieces at z=1.0)
        """
        cell = self._cell
        d = 0.85 * cell
        ring = QGraphicsEllipseItem(0, 0, d, d)
        ring.setPos((col + 0.15) * cell, (row + 0.15) * cell)
        ring.setPen(QPen(QColor(HIGHLIGHT_COLOR), 3.0))
        ring.setOpacity(0.70)
        ring.setZValue(1.1)
        self._scene.addItem(ring)
        return ring

    def _create_legal_move_dot(self, row: int, col: int) -> QGraphicsEllipseItem:
        """D-04 to D-08: Create semi-transparent gold dot at legal move target.

        Position: (col + 0.35) * cell, (row + 0.35) * cell
        Diameter: 0.50 * cell
        Brush: Solid gold, NoPen
        Opacity: 0.50 (50%)
        Z-value: 0.5 (below pieces at z=1.0)
        """
        cell = self._cell
        d = 0.50 * cell
        dot = QGraphicsEllipseItem(0, 0, d, d)
        dot.setPos((col + 0.35) * cell, (row + 0.35) * cell)
        dot.setBrush(QBrush(QColor(HIGHLIGHT_COLOR)))
        dot.setOpacity(0.50)
        dot.setZValue(0.5)
        self._scene.addItem(dot)
        return dot

    # ─── selection logic ──────────────────────────────────────────────────────

    def _select_piece(self, row: int, col: int) -> None:
        """Select a piece at (row, col): create ring and show legal moves.

        D-13: Always clear existing highlights first before creating new ones.
        D-01, D-02: Creates selection ring at piece position.
        D-04 to D-08: Creates legal move dots via _show_legal_moves.
        """
        self._clear_highlights()
        self._selection_ring = self._create_selection_ring(row, col)
        self._show_legal_moves(row, col)
        self._selected = (row, col)

    def _show_legal_moves(self, row: int, col: int) -> None:
        """Query engine.legal_moves() and create gold dots for each legal target.

        Filters legal_moves() to those with from_sq matching this piece's position.
        Uses bit operations on 16-bit move encoding:
          - bits 0-8: from_sq
          - bits 9-15: to_sq
        """
        from_sq = rc_to_sq(row, col)
        if self._engine is None:
            return  # No engine: no legal moves to display
        for move in self._engine.legal_moves():
            move_from = move & 0x1FF
            if move_from == from_sq:
                to_sq = (move >> 9) & 0x7F
                to_row, to_col = sq_to_rc(to_sq)
                dot = self._create_legal_move_dot(to_row, to_col)
                self._highlight_items.append(dot)

    # ─── resize event ─────────────────────────────────────────────────────────

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        """
        Recalculate cell size and reload all pieces on window resize.

        cell = min(vw, vh) / 11.2 preserves the 9:10 aspect ratio of the grid.
        All piece items are cleared and re-added at the new scale.
        """
        super().resizeEvent(event)
        vp = self.viewport()
        vw, vh = vp.width(), vp.height()
        self._cell = min(vw, vh) / 11.2
        sw = 10.2 * self._cell
        sh = 11.2 * self._cell
        self._scene.setSceneRect(0, 0, sw, sh)

        # Remove old piece items and re-add at new scale
        for item in list(self._scene.items()):
            if isinstance(item, PieceItem):
                self._scene.removeItem(item)
        self._load_pieces()

        # Recreate highlights at the new scale if a piece is selected (UI-SPEC Responsive Behavior)
        if self._selected:
            row, col = self._selected
            self._clear_highlights()
            self._selection_ring = self._create_selection_ring(row, col)
            self._show_legal_moves(row, col)

        self.viewport().update()

    # ─── piece loading ────────────────────────────────────────────────────────

    def _load_pieces(self) -> None:
        """Add PieceItem for every non-zero square in the current state.

        Also builds _piece_index: {(row, col): PieceItem} for O(1) lookup (D-15).
        """
        self._piece_index.clear()
        board = self._state.board
        for row in range(ROWS):
            for col in range(COLS):
                val = int(board[row, col])
                if val == 0:
                    continue
                piece_item = PieceItem(row, col, val, self._cell)
                self._scene.addItem(piece_item)
                self._piece_index[(row, col)] = piece_item  # D-15: index

    # ─── board background rendering ───────────────────────────────────────────

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw the board background: felt, grid, river gap, palace diagonals,
        river text ("楚河"/"漢界"), and coordinate labels.

        Called automatically by QGraphicsView. Uses self._cell (stored from
        the last resizeEvent) for all coordinate calculations.
        """
        del rect  # ignored — use self._cell directly
        cell = self._cell
        p = painter
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Green felt background rectangle (slightly larger than grid)
        p.fillRect(
            QRectF(-0.6 * cell, -0.6 * cell, 10.2 * cell, 11.2 * cell),
            QBrush(QColor(BOARD_BG)),
        )

        # 2. Grid lines — dark green, 1.0px
        p.setPen(QPen(QColor(GRID_COLOR), 1.0))

        # 3. Vertical lines (9 lines at x = 0.6, 1.6, ..., 8.6 cell)
        for col in range(COLS):
            x = (col + 0.6) * cell
            p.drawLine(QLineF(x, 0.6 * cell, x, 9.6 * cell))

        # 4. Horizontal lines (10 lines at y = 0.6, 1.6, ..., 9.6 cell)
        for row in range(ROWS):
            y = (row + 0.6) * cell
            p.drawLine(QLineF(0.6 * cell, y, 9.6 * cell, y))

        # 5. Palace diagonals (columns 3-5, center of board)
        # Top palace (rows 0-2): columns 3-5
        p.drawLine(QLineF((3.6) * cell, (0.6) * cell, (5.6) * cell, (2.6) * cell))  # top \
        p.drawLine(QLineF((5.6) * cell, (0.6) * cell, (3.6) * cell, (2.6) * cell))  # top /
        # Bottom palace (rows 7-9): columns 3-5
        p.drawLine(QLineF((3.6) * cell, (7.6) * cell, (5.6) * cell, (9.6) * cell))  # bottom \
        p.drawLine(QLineF((5.6) * cell, (7.6) * cell, (3.6) * cell, (9.6) * cell))  # bottom /

        # 6. River text "楚河" / "漢界"
        font_river = QFont("SimSun, Microsoft YaHei, Arial")
        font_size_river = max(int(cell * RIVER_FONT_RATIO), 10)
        font_river.setPixelSize(font_size_river)
        p.setFont(font_river)
        p.setPen(QPen(QColor(RIVER_TEXT_COLOR)))
        p.drawText(QPointF(2.0 * cell, 5.1 * cell), "楚河")
        p.drawText(QPointF(5.5 * cell, 5.1 * cell), "漢界")

        # 7. Coordinate labels
        font_coord = QFont("SimSun, Microsoft YaHei, Arial")
        font_coord.setPixelSize(max(int(cell * COORD_FONT_RATIO), 8))
        p.setFont(font_coord)
        p.setPen(QPen(QColor(COORD_TEXT_COLOR)))

        # Column labels (bottom/red: 1-9 left-to-right; top/black: 9-1 right-to-left)
        for col in range(COLS):
            x = (col + 0.6) * cell
            # Red perspective (bottom): 1-9 left-to-right
            p.drawText(QPointF(x - 4, 11.2 * cell + 4), str(col + 1))
            # Black perspective (top): 9-1 right-to-left
            p.drawText(QPointF(x - 4, 0.4 * cell), str(9 - col))

        # Row labels (left/red: 1-10 bottom-to-top; right/black: 10-1 top-to-bottom)
        for row in range(ROWS):
            y = (row + 0.6) * cell
            # Red ranks (left): 1-10 bottom-to-top
            p.drawText(QPointF(0.05 * cell, y + 4), str(10 - row))
            # Black ranks (right): 10-1 top-to-bottom
            p.drawText(QPointF(9.7 * cell, y + 4), str(row + 1))
