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

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QFrame
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF, pyqtSignal
from PyQt6.QtGui import QPalette, QPainter, QPen, QBrush, QColor, QFont, QResizeEvent, QMouseEvent

from src.xiangqi.engine.state import XiangqiState
from src.xiangqi.engine.engine import XiangqiEngine
from src.xiangqi.engine.types import Piece, ROWS, COLS
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
        scene_pos = self.mapToScene(event.position())
        board_pos = self._scene_to_board(scene_pos)
        if board_pos is None:
            return
        row, col = board_pos
        self._handle_board_click(row, col)

    # ─── click handling stubs (implemented in Task 2) ─────────────────────────

    def _handle_board_click(self, row: int, col: int) -> None:
        """Handle a click at board position (row, col).

        Subclass or extend this method to implement selection/move logic.
        Default: no-op (requires engine to be set).
        """
        pass

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
        self.viewport().update()

    # ─── piece loading ────────────────────────────────────────────────────────

    def _load_pieces(self) -> None:
        """Add PieceItem for every non-zero square in the current state."""
        board = self._state.board
        for row in range(ROWS):
            for col in range(COLS):
                val = int(board[row, col])
                if val == 0:
                    continue
                piece_item = PieceItem(row, col, val, self._cell)
                self._scene.addItem(piece_item)

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
