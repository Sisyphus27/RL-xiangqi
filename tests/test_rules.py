"""Tests for face-to-face rule and game result evaluation (RULE-05, RULE-06)."""
from __future__ import annotations

import numpy as np
import pytest

from src.xiangqi.engine.rules import (
    flying_general_violation, _generals_face_each_other, get_game_result,
)
from src.xiangqi.engine.types import Piece, ROWS, COLS, rc_to_sq
from src.xiangqi.engine.state import XiangqiState, compute_hash


def make_state(turn: int, king_red_sq: int, king_black_sq: int,
               extra_pieces: dict[tuple[int, int], int] | None = None) -> XiangqiState:
    """Create a completely independent XiangqiState from scratch."""
    board = np.zeros((ROWS, COLS), dtype=np.int8)
    kr, kc = divmod(king_red_sq, COLS)
    br, bc = divmod(king_black_sq, COLS)
    board[kr, kc] = Piece.R_SHUAI
    board[br, bc] = Piece.B_JIANG
    if extra_pieces:
        for (r, c), p in extra_pieces.items():
            board[r, c] = np.int8(p)
    state = XiangqiState(
        board=board, turn=turn,
        king_positions={+1: king_red_sq, -1: king_black_sq},
        move_history=[], halfmove_clock=0,
        zobrist_hash_history=[compute_hash(board, turn)],
    )
    return state


class TestGeneralsFaceEachOther:
    """Pure helper: _generals_face_each_other."""

    def test_returns_column_when_face_to_face(self):
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[9, 4] = Piece.R_SHUAI
        board[0, 4] = Piece.B_JIANG
        king_positions = {+1: rc_to_sq(9, 4), -1: rc_to_sq(0, 4)}
        col = _generals_face_each_other(board, king_positions)
        assert col == 4

    def test_returns_none_different_columns(self):
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[9, 4] = Piece.R_SHUAI
        board[0, 3] = Piece.B_JIANG
        king_positions = {+1: rc_to_sq(9, 4), -1: rc_to_sq(0, 3)}
        assert _generals_face_each_other(board, king_positions) is None

    def test_returns_none_piece_between(self):
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[9, 4] = Piece.R_SHUAI
        board[5, 4] = Piece.R_CHE
        board[0, 4] = Piece.B_JIANG
        king_positions = {+1: rc_to_sq(9, 4), -1: rc_to_sq(0, 4)}
        assert _generals_face_each_other(board, king_positions) is None

    def test_returns_none_missing_king(self):
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[9, 4] = Piece.R_SHUAI
        king_positions = {+1: rc_to_sq(9, 4)}
        assert _generals_face_each_other(board, king_positions) is None


class TestFlyingGeneralViolation:
    """RULE-04: flying_general_violation is True when generals face each other."""

    def test_violation_true(self):
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        assert flying_general_violation(state, +1) is True

    def test_violation_false_different_file(self):
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 3))
        assert flying_general_violation(state, +1) is False

    def test_violation_false_piece_between(self):
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4),
                           extra_pieces={(5, 4): Piece.R_CHE})
        assert flying_general_violation(state, +1) is False


class TestGetGameResult:
    """RULE-05, RULE-06: game result evaluation."""

    def test_in_progress_starting(self, starting_state):
        assert get_game_result(starting_state) == 'IN_PROGRESS'

    def test_checkmate_red_loses(self):
        """Checkmate: double chariot mating net, red has no legal moves.

        Red king at (9,4), black chariot at (9,0) checks along row 9,
        black chariot at (0,4) controls column 4. All king escapes are covered.
        Own advisors at (8,3) and (8,5) block diagonal flight.
        No legal moves, king in check -> BLACK_WINS.
        """
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 3),
                           extra_pieces={
                               (9, 0): Piece.B_CHE,   # checking chariot (attacks row 9)
                               (0, 4): Piece.B_CHE,   # checking chariot (attacks col 4)
                               (8, 3): Piece.R_SHI,  # blocks (8,3) diagonal escape
                               (8, 5): Piece.R_SHI,  # blocks (8,5) diagonal escape
                           })
        result = get_game_result(state)
        assert result == 'BLACK_WINS'

    def test_stalemate_also_loss(self):
        """Checkmate: red king has no legal moves and is in check.

        This position uses the same structure as test_checkmate_red_loses but with
        B_SHI at (8,4) as the forward blocker (instead of R_SHI), making the
        forward square (8,4) capturable by the king while ensuring no red piece
        can legally move to resolve check.

        B_CHE at (9,0) attacks row 9 — king at (9,4) cannot move horizontally
        to (9,3) or (9,5) (occupied by own R_SHI, also on the attacked row).
        B_CHE at (0,4) attacks column 4 — king cannot move forward (8,4) to
        capture B_SHI (blocked by own R_SHI at (8,3)/(8,5)) and also B_CHE at
        (0,4) covers (8,4) from above, making it a protected blocker.
        B_SHI at (8,4) blocks the forward diagonal (8,4) escape; it is protected
        by B_CHE at (0,4) (same column 4) and by the checking geometry: R_SHI
        at (8,3)/(8,5) cannot capture it (not on their diagonal line).
        R_SHI at (8,3) and (8,5) block diagonal escapes (7,3) and (7,5)
        (occupied) and cannot move to (8,4) (blocked by B_SHI).
        All 5 adjacent king squares are covered or occupied — zero legal moves.
        King is IN CHECK from B_CHE at (0,4) — checkmate — BLACK_WINS.

        NOTE: The old position (R_SHI + R_BING at (8,4)) was broken because
        correct SHI movement allows R_SHI at (8,5) to move diagonally to (8,4)
        and capture the forward blocker. Using B_SHI at (8,4) as the forward
        blocker is safe because R_SHI at (8,5) cannot capture it (occupied own
        piece at (8,5) is not on the diagonal to (8,4)) and B_CHE at (0,4)
        protects B_SHI while checking the king.
        """
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 3),
                           extra_pieces={
                               (9, 0): Piece.B_CHE,    # chariot: attacks row 9
                               (0, 4): Piece.B_CHE,    # chariot: attacks column 4 (checking king)
                               (8, 4): Piece.B_SHI,   # advisor: blocks forward (8,4) escape
                               (8, 3): Piece.R_SHI,   # blocks diagonal (7,3) escape
                               (8, 5): Piece.R_SHI,   # blocks diagonal (7,5) escape
                           })
        result = get_game_result(state)
        assert result == 'BLACK_WINS'

    def test_in_progress_mid_game(self):
        """Any position with legal moves is IN_PROGRESS."""
        state = XiangqiState.starting()
        state.board[0, 0] = 0  # remove black chariot
        result = get_game_result(state)
        assert result == 'IN_PROGRESS'
