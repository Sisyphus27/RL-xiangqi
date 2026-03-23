"""
PieceItem — QGraphicsEllipseItem subclass rendering a single xiangqi piece.

Each piece renders as:
  - Filled circle (red for red pieces, black for black pieces)
  - White 2px stroke border
  - Centered Chinese character in white

Coordinate mapping (from 05-RESEARCH.md):
  - Scene size: (COLS + 1.2) * cell wide x (ROWS + 1.2) * cell tall
  - Piece ellipse rect: (col + 0.2, row + 0.2) * cell with diameter 0.8*cell
  - Piece center: (col + 0.6, row + 0.6) * cell
  - Engine row 0 = top (black home), row 9 = bottom (red home)
  - Red: piece_value > 0; Black: piece_value < 0
"""

from PyQt6.QtWidgets import QGraphicsEllipseItem
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont

from src.xiangqi.engine.types import Piece
from src.xiangqi.engine.constants import ROWS, COLS
from .constants import (
    RED_FILL,
    BLACK_FILL,
    PIECE_TEXT_COLOR,
    PIECE_STROKE_COLOR,
    CELL_RATIO,
    PIECE_FONT_RATIO,
)


class PieceItem(QGraphicsEllipseItem):
    """
    Renders a single xiangqi piece.

    Parameters
    ----------
    row : int
        Board row (0=top/black home, 9=bottom/red home).
    col : int
        Board column (0=left, 8=right).
    piece_value : int
        Signed integer from board array. Positive=red, negative=black.
        Must be non-zero.
    cell : float
        Scene cell size in pixels. Piece diameter = cell * CELL_RATIO (0.80).
    """

    __slots__ = ("_row", "_col", "_piece_value", "_cell", "_char")

    def __init__(self, row: int, col: int, piece_value: int, cell: float) -> None:
        if piece_value == 0:
            raise ValueError("PieceItem cannot represent an empty square (piece_value=0)")
        self._row = row
        self._col = col
        self._piece_value = piece_value
        self._cell = cell

        # Ellipse diameter = 80% of cell
        d = cell * CELL_RATIO

        # Local rect: origin at (0,0), size d x d
        super().__init__(0, 0, d, d)

        # Scene position: top-left of ellipse at (col+0.2, row+0.2) * cell
        # This centers the ellipse at (col+0.6, row+0.6) * cell
        self.setPos((col + 0.2) * cell, (row + 0.2) * cell)
        self.setZValue(1.0)

        # Fill color: red for positive value, black for negative
        fill_color = QColor(RED_FILL) if piece_value > 0 else QColor(BLACK_FILL)
        self.setBrush(QBrush(fill_color))

        # White 2px stroke border
        self.setPen(QPen(QColor(PIECE_STROKE_COLOR), 2.0))

        # Chinese character via Piece enum
        self._char = str(Piece(piece_value))

    # ─── paint ─────────────────────────────────────────────────────────────────

    def paint(
        self,
        painter: QPainter,
        option,
        widget=None,
    ) -> None:
        """
        Draw the piece ellipse and centered Chinese character.

        Overrides QGraphicsEllipseItem.paint().
        """
        # Draw the filled + stroked ellipse
        QGraphicsEllipseItem.paint(self, painter, option, widget)

        # Font size: cell * PIECE_FONT_RATIO (0.56), minimum 8px
        d = self._cell * CELL_RATIO
        font_size = max(int(d * PIECE_FONT_RATIO), 8)
        font = QFont("SimSun, Microsoft YaHei, Arial", font_size)
        font.setStyleStrategy(QFont.StyleStrategy.PreferMatch)

        painter.setFont(font)
        painter.setPen(QPen(QColor(PIECE_TEXT_COLOR)))

        # Draw character centered in the local ellipse rect
        painter.drawText(QRectF(0, 0, d, d), Qt.AlignmentFlag.AlignCenter, self._char)
