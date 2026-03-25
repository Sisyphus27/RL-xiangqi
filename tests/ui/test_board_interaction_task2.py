"""Tests for Task 2: click handling and move execution."""

import pytest
from PyQt6.QtCore import QPointF
from src.xiangqi.engine.engine import XiangqiEngine
from src.xiangqi.engine.state import XiangqiState
from src.xiangqi.engine.types import rc_to_sq, sq_to_rc
from src.xiangqi.ui.board import QXiangqiBoard
from src.xiangqi.ui.board_items import PieceItem


@pytest.fixture
def board_with_engine(qtbot):
    """QXiangqiBoard with XiangqiEngine for interaction tests."""
    state = XiangqiState.starting()
    engine = XiangqiEngine.starting()
    b = QXiangqiBoard(state=state, engine=engine)
    qtbot.addWidget(b)
    return b


def _click(board, row, col, qtbot):
    """Simulate a click at board (row, col).

    Uses viewport coordinates so mapToScene converts correctly.
    """
    from PyQt6.QtGui import QMouseEvent
    from PyQt6.QtCore import Qt
    vp = board.viewport()
    vp_w, vp_h = vp.width(), vp.height()

    # Scene is cell*10.2 wide x cell*11.2 tall, centered in viewport
    cell = board._cell
    scene_w = 10.2 * cell
    scene_h = 11.2 * cell

    # Scene origin in viewport: centered horizontally and vertically
    offset_x = (vp_w - scene_w) / 2.0
    offset_y = (vp_h - scene_h) / 2.0

    # Piece center in scene coords: (col+0.6)*cell, (row+0.6)*cell
    # Convert to viewport coords
    scene_x = (col + 0.6) * cell
    scene_y = (row + 0.6) * cell
    vp_x = scene_x + offset_x
    vp_y = scene_y + offset_y

    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(vp_x, vp_y),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    board.mousePressEvent(event)


class TestHandleBoardClick:
    """Tests for _handle_board_click behavior."""

    def test_click_red_piece_selects_it(self, board_with_engine, qtbot):
        """Clicking a red piece selects it (sets _selected)."""
        board = board_with_engine
        # Red pawn at row 6, col 0 (starting position)
        _click(board, 6, 0, qtbot)
        assert board._selected == (6, 0), "Clicking red pawn should select it"

    def test_click_red_piece_creates_selection_ring(self, board_with_engine, qtbot):
        """Clicking a red piece creates a gold selection ring."""
        board = board_with_engine
        _click(board, 6, 0, qtbot)
        assert board._selection_ring is not None, "Selection ring should be created"

    def test_click_red_piece_creates_legal_move_dots(self, board_with_engine, qtbot):
        """Clicking a red piece shows gold dots at legal move targets."""
        board = board_with_engine
        _click(board, 6, 0, qtbot)
        # Red pawn at row 6 has 1 legal forward move to row 5, col 0
        assert len(board._highlight_items) >= 1, "Legal move dots should appear"

    def test_click_empty_square_no_selection(self, board_with_engine, qtbot):
        """Clicking empty square with no selection does nothing."""
        board = board_with_engine
        # Empty square at row 4, col 4 (river area)
        _click(board, 4, 4, qtbot)
        assert board._selected is None, "Clicking empty square should not select"

    def test_click_black_piece_no_selection(self, board_with_engine, qtbot):
        """Clicking black piece with no selection does nothing."""
        board = board_with_engine
        # Black pawn at row 3, col 0 (starting position)
        _click(board, 3, 0, qtbot)
        assert board._selected is None, "Clicking black piece should not select"

    def test_click_illegal_target_deselects(self, board_with_engine, qtbot):
        """After selecting a piece, clicking an illegal target deselects."""
        board = board_with_engine
        _click(board, 6, 0, qtbot)  # Select red pawn
        assert board._selected == (6, 0)
        # Try clicking a square that's not a legal move for this pawn
        _click(board, 0, 0, qtbot)  # Empty square at top-left
        assert board._selected is None, "Clicking illegal target should deselect"

    def test_click_same_piece_deselects(self, board_with_engine, qtbot):
        """Clicking the selected piece again deselects it."""
        board = board_with_engine
        _click(board, 6, 0, qtbot)  # Select
        assert board._selected == (6, 0)
        _click(board, 6, 0, qtbot)  # Click same square again
        assert board._selected is None, "Clicking selected piece should deselect"

    def test_click_another_red_piece_switches_selection(self, board_with_engine, qtbot):
        """Clicking another red piece switches selection to the new piece."""
        board = board_with_engine
        _click(board, 6, 0, qtbot)  # Select first pawn
        first_selected = board._selected
        # Click another red piece (red chariot at row 9, col 0)
        _click(board, 9, 0, qtbot)
        assert board._selected == (9, 0), "Selection should switch to chariot"
        assert board._selected != first_selected


class TestIsLegalTarget:
    """Tests for _is_legal_target method."""

    def test_is_legal_target_method_exists(self, board_with_engine):
        """QXiangqiBoard has _is_legal_target method."""
        board = board_with_engine
        assert hasattr(board, '_is_legal_target'), "Must have _is_legal_target method"

    def test_is_legal_target_returns_true_for_legal_move(self, board_with_engine):
        """_is_legal_target returns True for a valid legal move."""
        board = board_with_engine
        # Red pawn at (6, 0) can move to (5, 0)
        assert board._is_legal_target(6, 0, 5, 0) is True

    def test_is_legal_target_returns_false_for_illegal_move(self, board_with_engine):
        """_is_legal_target returns False for an invalid move."""
        board = board_with_engine
        # Red pawn at (6, 0) cannot move to (0, 0)
        assert board._is_legal_target(6, 0, 0, 0) is False


class TestApplyMove:
    """Tests for apply_move method."""

    def test_apply_move_method_exists(self, board_with_engine):
        """QXiangqiBoard has apply_move method."""
        board = board_with_engine
        assert hasattr(board, 'apply_move'), "Must have apply_move method"

    def test_apply_move_updates_piece_position(self, board_with_engine):
        """apply_move moves the piece from one square to another."""
        board = board_with_engine
        from_sq = rc_to_sq(6, 0)  # Red pawn starting position
        to_sq = rc_to_sq(5, 0)    # One step forward
        board.apply_move(from_sq, to_sq)
        # Piece should now be at (5, 0)
        piece = board._piece_index.get((5, 0))
        assert piece is not None, "Piece should be at new position after move"

    def test_apply_move_removes_old_position(self, board_with_engine):
        """apply_move removes the piece from the old square."""
        board = board_with_engine
        from_sq = rc_to_sq(6, 0)
        to_sq = rc_to_sq(5, 0)
        board.apply_move(from_sq, to_sq)
        # Old position should be empty
        old_piece = board._piece_index.get((6, 0))
        assert old_piece is None, "Old position should be empty after move"

    def test_apply_move_clears_highlights(self, board_with_engine):
        """apply_move clears selection and all highlights."""
        board = board_with_engine
        from_sq = rc_to_sq(6, 0)
        to_sq = rc_to_sq(5, 0)
        board.apply_move(from_sq, to_sq)
        assert board._selected is None, "Selection should be cleared after move"
        assert len(board._highlight_items) == 0, "Highlights should be cleared after move"

    def test_apply_move_emits_signal(self, board_with_engine, qtbot):
        """apply_move emits move_applied signal with from_sq, to_sq, captured."""
        board = board_with_engine
        from_sq = rc_to_sq(6, 0)
        to_sq = rc_to_sq(5, 0)
        signals_received = []

        def record_signal(f, t, c):
            signals_received.append((f, t, c))

        board.move_applied.connect(record_signal)
        board.apply_move(from_sq, to_sq)
        assert len(signals_received) == 1, "move_applied should be emitted once"
        assert signals_received[0] == (from_sq, to_sq, 0), f"Signal args should be ({from_sq}, {to_sq}, 0), got {signals_received[0]}"


class TestClickAndMove:
    """End-to-end tests: click to select, click to move."""

    def test_full_move_sequence(self, board_with_engine, qtbot):
        """Click red pawn to select, then click legal target to move."""
        board = board_with_engine
        # Step 1: Click red pawn at (6, 0)
        _click(board, 6, 0, qtbot)
        assert board._selected == (6, 0), "Pawn should be selected"
        assert len(board._highlight_items) >= 1, "Legal moves should show"

        # Step 2: Click the legal target (5, 0)
        _click(board, 5, 0, qtbot)

        # Step 3: Verify move was applied
        assert board._piece_index.get((5, 0)) is not None, "Pawn should be at (5, 0)"
        assert board._piece_index.get((6, 0)) is None, "(6, 0) should be empty"
        assert board._selected is None, "Selection should be cleared"
        assert len(board._highlight_items) == 0, "Highlights should be cleared"


class TestPieceIndex:
    """Tests for _piece_index dictionary."""

    def test_piece_index_populated_on_init(self, board_with_engine):
        """_piece_index is populated with all 32 pieces after init."""
        board = board_with_engine
        assert len(board._piece_index) == 32, f"Should have 32 pieces, got {len(board._piece_index)}"

    def test_piece_index_lookup_red_pawn(self, board_with_engine):
        """_piece_index correctly maps (row, col) to PieceItem for red pawn."""
        board = board_with_engine
        piece = board._piece_index.get((6, 0))
        assert piece is not None, "Red pawn should be in piece index at (6, 0)"
        assert isinstance(piece, PieceItem)
        assert piece._piece_value > 0, "Red piece value should be positive"

    def test_piece_index_lookup_black_pawn(self, board_with_engine):
        """_piece_index correctly maps (row, col) to PieceItem for black pawn."""
        board = board_with_engine
        piece = board._piece_index.get((3, 0))
        assert piece is not None, "Black pawn should be in piece index at (3, 0)"
        assert isinstance(piece, PieceItem)
        assert piece._piece_value < 0, "Black piece value should be negative"
