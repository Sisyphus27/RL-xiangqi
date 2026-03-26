"""Tests for QXiangqiBoard selection and highlight infrastructure — Phase 06-01.

Covers:
  - HIGHLIGHT_COLOR constant value
  - State variables: _engine, _selected, _selection_ring, _highlight_items, _piece_index
  - Highlight creation: _create_selection_ring, _create_legal_move_dot, _clear_highlights
  - Selection methods: _select_piece, _deselect_piece, _show_legal_moves
  - Piece index: _piece_index dictionary built during _load_pieces
"""

import pytest
from PyQt6.QtWidgets import QGraphicsEllipseItem

from src.xiangqi.engine.engine import XiangqiEngine
from src.xiangqi.engine.state import XiangqiState
from src.xiangqi.ui.board import QXiangqiBoard
from src.xiangqi.ui.board_items import PieceItem


@pytest.fixture
def board_with_engine(qtbot):
    """QXiangqiBoard with XiangqiEngine for interaction tests (red to move)."""
    state = XiangqiState.starting()
    engine = XiangqiEngine.starting()
    b = QXiangqiBoard(state=state, engine=engine)
    qtbot.addWidget(b)
    return b


class TestHighlightColor:
    """HIGHLIGHT_COLOR constant value (UI-03 selection ring and dots)."""

    def test_highlight_color_value(self):
        """HIGHLIGHT_COLOR is gold #FFD700."""
        from src.xiangqi.ui.constants import HIGHLIGHT_COLOR
        assert HIGHLIGHT_COLOR == "#FFD700"


class TestBoardStateVariables:
    """QXiangqiBoard instance variables for selection infrastructure."""

    def test_board_has_engine_attribute(self, board_with_engine):
        """Board holds a reference to XiangqiEngine."""
        assert hasattr(board_with_engine, "_engine")
        assert board_with_engine._engine is not None

    def test_board_has_selected_attribute(self, board_with_engine):
        """Board has _selected attribute (None when nothing selected)."""
        assert hasattr(board_with_engine, "_selected")
        assert board_with_engine._selected is None

    def test_board_has_selection_ring_attribute(self, board_with_engine):
        """Board has _selection_ring attribute (None when nothing selected)."""
        assert hasattr(board_with_engine, "_selection_ring")
        assert board_with_engine._selection_ring is None

    def test_board_has_highlight_items_attribute(self, board_with_engine):
        """Board has _highlight_items attribute (empty list)."""
        assert hasattr(board_with_engine, "_highlight_items")
        assert board_with_engine._highlight_items == []

    def test_board_has_piece_index_attribute(self, board_with_engine):
        """Board has _piece_index dictionary for O(1) piece lookup."""
        assert hasattr(board_with_engine, "_piece_index")
        assert isinstance(board_with_engine._piece_index, dict)
        assert len(board_with_engine._piece_index) == 32  # 32 pieces on starting board


class TestHighlightCreationMethods:
    """Helper methods for creating/clearing highlight items."""

    def test_create_selection_ring_returns_ellipse(self, board_with_engine):
        """_create_selection_ring returns a QGraphicsEllipseItem."""
        ring = board_with_engine._create_selection_ring(row=6, col=4)
        assert isinstance(ring, QGraphicsEllipseItem)
        board_with_engine._scene.removeItem(ring)

    def test_create_selection_ring_has_gold_pen(self, board_with_engine):
        """Selection ring pen color is HIGHLIGHT_COLOR gold."""
        from src.xiangqi.ui.constants import HIGHLIGHT_COLOR
        ring = board_with_engine._create_selection_ring(row=6, col=4)
        pen_color = ring.pen().color().name().upper()
        assert pen_color == HIGHLIGHT_COLOR.upper()
        board_with_engine._scene.removeItem(ring)

    def test_create_selection_ring_z_value_above_pieces(self, board_with_engine):
        """Selection ring z-value is 1.1 (above pieces at z=1.0)."""
        ring = board_with_engine._create_selection_ring(row=6, col=4)
        assert ring.zValue() == 1.1
        board_with_engine._scene.removeItem(ring)

    def test_create_legal_move_dot_returns_ellipse(self, board_with_engine):
        """_create_legal_move_dot returns a QGraphicsEllipseItem."""
        dot = board_with_engine._create_legal_move_dot(row=6, col=4)
        assert isinstance(dot, QGraphicsEllipseItem)
        board_with_engine._scene.removeItem(dot)

    def test_create_legal_move_dot_z_value_below_pieces(self, board_with_engine):
        """Legal move dot z-value is 0.5 (below pieces at z=1.0)."""
        dot = board_with_engine._create_legal_move_dot(row=6, col=4)
        assert dot.zValue() == 0.5
        board_with_engine._scene.removeItem(dot)

    def test_clear_highlights_removes_all_items(self, board_with_engine):
        """_clear_highlights removes all highlight items from scene and resets state."""
        ring = board_with_engine._create_selection_ring(row=6, col=4)
        dot = board_with_engine._create_legal_move_dot(row=5, col=4)
        board_with_engine._highlight_items.append(dot)
        board_with_engine._selection_ring = ring

        board_with_engine._clear_highlights()

        assert len(board_with_engine._highlight_items) == 0
        assert board_with_engine._selection_ring is None
        assert ring not in board_with_engine._scene.items()
        assert dot not in board_with_engine._scene.items()


class TestSelectionMethods:
    """_select_piece, _deselect_piece, _show_legal_moves implementation."""

    def test_select_piece_creates_ring(self, board_with_engine):
        """_select_piece creates a selection ring and sets _selected."""
        board_with_engine._select_piece(row=6, col=4)
        assert board_with_engine._selection_ring is not None
        assert isinstance(board_with_engine._selection_ring, QGraphicsEllipseItem)
        assert board_with_engine._selected == (6, 4)
        board_with_engine._clear_highlights()

    def test_deselect_piece_clears_selection(self, board_with_engine):
        """_deselect_piece clears _selected and removes all highlights."""
        board_with_engine._select_piece(row=6, col=4)
        board_with_engine._deselect_piece()
        assert board_with_engine._selected is None
        assert board_with_engine._selection_ring is None
        assert len(board_with_engine._highlight_items) == 0

    def test_show_legal_moves_creates_dots(self, board_with_engine):
        """_show_legal_moves creates a dot for each legal move target from selected piece."""
        board_with_engine._select_piece(row=6, col=4)  # Red chariot has several legal moves
        assert len(board_with_engine._highlight_items) > 0
        for item in board_with_engine._highlight_items:
            assert isinstance(item, QGraphicsEllipseItem)
        board_with_engine._clear_highlights()


class TestPieceIndex:
    """_piece_index dictionary built during _load_pieces."""

    def test_piece_index_contains_32_pieces(self, board_with_engine):
        """_piece_index maps all 32 starting positions to PieceItems."""
        idx = board_with_engine._piece_index
        assert len(idx) == 32

    def test_piece_index_key_integrity(self, board_with_engine):
        """Every key in _piece_index matches its PieceItem's _row/_col."""
        for pos, item in board_with_engine._piece_index.items():
            assert isinstance(pos, tuple)
            assert isinstance(item, PieceItem)
            assert pos == (item._row, item._col)

    def test_piece_index_red_chariot_lookup(self, board_with_engine):
        """_piece_index.get((row, col)) returns the correct PieceItem."""
        piece = board_with_engine._piece_index.get((9, 0))  # Red chariot at col 0, row 9
        assert piece is not None
        assert piece._piece_value == 5  # Red chariot = +5

    def test_piece_index_empty_square_returns_none(self, board_with_engine):
        """_piece_index.get((row, col)) returns None for empty squares."""
        piece = board_with_engine._piece_index.get((5, 4))  # empty on starting board
        assert piece is None

    def test_piece_index_board_alignment(self, board_with_engine):
        """Every indexed piece's value matches the board array at that position."""
        board = board_with_engine._state.board
        for (row, col), piece_item in board_with_engine._piece_index.items():
            assert int(board[row, col]) == piece_item._piece_value
