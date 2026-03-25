"""Tests for Task 3: resizeEvent highlight preservation."""

import pytest
from PyQt6.QtCore import Qt
from src.xiangqi.engine.engine import XiangqiEngine
from src.xiangqi.engine.state import XiangqiState
from src.xiangqi.ui.board import QXiangqiBoard


@pytest.fixture
def board_with_engine(qtbot):
    """QXiangqiBoard with XiangqiEngine for interaction tests."""
    state = XiangqiState.starting()
    engine = XiangqiEngine.starting()
    b = QXiangqiBoard(state=state, engine=engine)
    qtbot.addWidget(b)
    return b


def _click(board, row, col):
    """Simulate a click at board (row, col) in viewport coordinates."""
    from PyQt6.QtGui import QMouseEvent
    from PyQt6.QtCore import QPointF
    cell = board._cell
    # Convert board (row, col) to VIEWPORT coordinates
    # viewport = board + (103.5, 2.0) offset for center-aligned scene
    vp_x = (col + 0.6) * cell + 103.5
    vp_y = (row + 0.6) * cell + 2.0
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(vp_x, vp_y),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    board.mousePressEvent(event)


class TestResizeHighlightPreservation:
    """Tests for resizeEvent preserving highlights and selection."""

    def test_resize_preserves_selection(self, board_with_engine, qtbot):
        """Window resize preserves the selected piece selection."""
        board = board_with_engine
        # Select a red pawn at (6, 0)
        _click(board, 6, 0)
        assert board._selected == (6, 0), "Piece should be selected"

        # Resize the window to a new size
        board.resize(600, 700)
        board.resizeEvent(None)  # Force resize event handling

        assert board._selected == (6, 0), "Selection should be preserved after resize"

    def test_resize_recreates_selection_ring(self, board_with_engine, qtbot):
        """Window resize recreates the selection ring at the new scale."""
        board = board_with_engine
        # Select a red pawn
        _click(board, 6, 0)
        ring_before = board._selection_ring
        assert ring_before is not None

        old_cell = board._cell
        # Resize to a larger window
        board.resize(720, 800)
        board.resizeEvent(None)

        ring_after = board._selection_ring
        assert ring_after is not None, "Selection ring should be recreated after resize"
        # Ring should be at the new cell size (larger)
        assert ring_after is not ring_before, "A new ring item should be created"

    def test_resize_recreates_legal_move_dots(self, board_with_engine, qtbot):
        """Window resize recreates legal move dots at the new positions."""
        board = board_with_engine
        # Select a red pawn (which has a legal forward move)
        _click(board, 6, 0)
        dots_before = len(board._highlight_items)
        assert dots_before >= 1, "Should have legal move dots after selection"

        old_cell = board._cell
        # Resize to a different size
        board.resize(300, 400)
        board.resizeEvent(None)

        dots_after = len(board._highlight_items)
        assert dots_after >= 1, "Legal move dots should be recreated after resize"
        # Dots should be at the new cell size
        assert dots_after == dots_before, "Same number of dots should be recreated"

    def test_resize_no_selection_no_highlights(self, board_with_engine, qtbot):
        """Window resize with no selection produces no highlights."""
        board = board_with_engine
        assert board._selected is None, "No selection initially"

        # Resize without selection
        board.resize(720, 800)
        board.resizeEvent(None)

        assert board._selected is None, "Still no selection after resize"
        assert board._selection_ring is None, "No selection ring after resize"
        assert len(board._highlight_items) == 0, "No highlight items after resize"
