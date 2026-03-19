"""Tests for face-to-face rule and game result evaluation (RULE-05, RULE-06)."""
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
        """Stalemate (困毙) = loss per RULE-06. No legal moves, not in check."""
        # Red king at (9,4), R_SHI at (9,3) and (9,5) block side escapes.
        # R_BING at (8,4) blocks forward escape; pawn cannot move (king in front).
        # No enemy piece attacks the king directly -> stalemate -> BLACK_WINS.
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 3),
                           extra_pieces={
                               (9, 3): Piece.R_SHI,
                               (9, 5): Piece.R_SHI,
                               (8, 4): Piece.R_BING,
                           })
        result = get_game_result(state)
        assert result == 'BLACK_WINS'

    def test_in_progress_mid_game(self):
        """Any position with legal moves is IN_PROGRESS."""
        state = XiangqiState.starting()
        state.board[0, 0] = 0  # remove black chariot
        result = get_game_result(state)
        assert result == 'IN_PROGRESS'
