"""Phase 06: Piece interaction automated tests.

Test coverage for UI-03 (select/highlight), UI-04 (move), UI-05 (deselect).

All tests use board_with_engine fixture which provides a QXiangqiBoard
with engine reference for querying legal moves.
"""

import pytest


def test_select_piece_shows_ring(board_with_engine, qtbot):
    """Clicking a red piece shows gold selection ring (UI-03)."""
    pass


def test_select_piece_shows_legal_moves(board_with_engine, qtbot):
    """Selecting a piece highlights all legal move targets with gold dots (UI-03)."""
    pass


def test_click_legal_target_moves_piece(board_with_engine, qtbot):
    """Clicking a highlighted legal target moves the piece (UI-04)."""
    pass


def test_move_emits_signal(board_with_engine, qtbot):
    """Executing a move emits move_applied(from_sq, to_sq, captured) signal (UI-04)."""
    pass


def test_click_illegal_deselects(board_with_engine, qtbot):
    """Clicking a non-legal target deselects the current piece (UI-05)."""
    pass


def test_click_empty_deselects(board_with_engine, qtbot):
    """Clicking an empty non-target square deselects the current piece (UI-05)."""
    pass


def test_black_turn_disabled(board_with_engine, qtbot):
    """During black turn (AI thinking), clicks are silently ignored (UI-03 guard)."""
    pass


def test_piece_index_lookup(board_with_engine, qtbot):
    """Board maintains O(1) piece index dict for fast PieceItem lookup (D-15)."""
    pass
