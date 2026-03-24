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
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPalette, QPainter, QPen, QBrush, QColor, QFont, QResizeEvent

from src.xiangqi.engine.state import XiangqiState
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
    parent : QWidget, optional
        Parent widget.

    Attributes
    ----------
    _state : XiangqiState
        Current game state (source of truth for piece positions).
    _cell : float
        Scene cell size in pixels. Updated on every resizeEvent.
        cell = min(viewport_width, viewport_height) / 11.2
    _scene : QGraphicsScene
        Holds all PieceItem instances.

    Coordinate system (scene coords):
      - Grid occupies x: [0.6, 9.6] * cell, y: [0.6, 10.6] * cell
      - 9 columns (0-8), 10 rows (0-9)
      - Engine row 0 = top (black home), row 9 = bottom (red home)
      - Piece center at (col + 0.6, row + 0.6) * cell
    """

    def __init__(self, state: XiangqiState | None = None, parent=None) -> None:
        super().__init__(parent)
        self._state = state or XiangqiState.starting()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setBackgroundRole(QPalette.ColorRole.NoRole)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._cell = 0.0
        # Trigger initial layout — resizeEvent(None) computes cell from viewport
        self.resizeEvent(None)

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
            p.drawLine(x, 0.6 * cell, x, 10.6 * cell)

        # 4. Horizontal lines (10 lines, but skip river gap between row 4 and 5)
        for row in range(ROWS):
            if row == 4:  # no line between river rows
                continue
            y = (row + 0.6) * cell
            p.drawLine(0.6 * cell, y, 9.6 * cell, y)

        # 5. Palace diagonals
        # Top palace (rows 0-2): left side (cols 0-2) and right side (cols 6-8)
        p.drawLine((0.6) * cell, (0.6) * cell, (2.6) * cell, (2.6) * cell)  # top-left \
        p.drawLine((2.6) * cell, (0.6) * cell, (0.6) * cell, (2.6) * cell)  # top-left /
        p.drawLine((6.6) * cell, (0.6) * cell, (8.6) * cell, (2.6) * cell)  # top-right \
        p.drawLine((8.6) * cell, (0.6) * cell, (6.6) * cell, (2.6) * cell)  # top-right /
        # Bottom palace (rows 7-9): left side (cols 0-2) and right side (cols 6-8)
        p.drawLine((0.6) * cell, (7.6) * cell, (2.6) * cell, (9.6) * cell)  # bottom-left \
        p.drawLine((2.6) * cell, (7.6) * cell, (0.6) * cell, (9.6) * cell)  # bottom-left /
        p.drawLine((6.6) * cell, (7.6) * cell, (8.6) * cell, (9.6) * cell)  # bottom-right \
        p.drawLine((8.6) * cell, (7.6) * cell, (6.6) * cell, (9.6) * cell)  # bottom-right /

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
