"""Tests for legal move filtering, check detection, and move application (RULE-01..06)."""
import numpy as np
import pytest

from src.xiangqi.engine.legal import (
    is_in_check, is_legal_move, generate_legal_moves,
    apply_move, flying_general_violation,
)
from src.xiangqi.engine.types import Piece, ROWS, COLS, rc_to_sq, encode_move, decode_move
from src.xiangqi.engine.state import XiangqiState, compute_hash


def make_state(turn: int, king_red_sq: int, king_black_sq: int,
               extra_pieces: dict[tuple[int, int], int] | None = None) -> XiangqiState:
    """Create a completely independent XiangqiState from scratch.

    kings are placed on DIFFERENT FILES by default to avoid accidental face-to-face.
    """
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


class TestIsInCheck:
    """RULE-01: is_in_check detects all attack types."""

    def test_not_in_check_starting(self, starting_state):
        assert is_in_check(starting_state, +1) is False
        assert is_in_check(starting_state, -1) is False

    def test_chariot_check(self):
        """Chariot delivering check along open file."""
        # Red king at (9,3), black king at (0,4) (different file), black chariot at (0,3)
        state = make_state(+1, rc_to_sq(9, 3), rc_to_sq(0, 4),
                           extra_pieces={(0, 3): Piece.B_CHE})
        assert is_in_check(state, +1) is True

    def test_cannon_check(self):
        """Cannon delivering check with exactly 1 screen."""
        state = make_state(+1, rc_to_sq(9, 3), rc_to_sq(0, 4),
                           extra_pieces={(5, 3): Piece.R_BING, (2, 3): Piece.B_PAO})
        assert is_in_check(state, +1) is True

    def test_horse_check(self):
        """Horse delivering L-shape check."""
        # Red king at (9,3), black king at (0,4) (different files).
        # Black horse at (7,4): leg at (8,4) empty, dest (9,3) = red king.
        # From (7,4): destinations (9,3) via leg (8,4), (9,5) via leg (8,4).
        state = make_state(+1, rc_to_sq(9, 3), rc_to_sq(0, 4),
                           extra_pieces={(7, 4): Piece.B_MA})
        assert is_in_check(state, +1) is True

    def test_horse_leg_blocked_no_check(self):
        """Horse with blocked leg does not give check."""
        # Horse at (7,4) attacks king (9,3) via leg (8,3). Block leg (8,3).
        # (8,3) is outside both palaces, so placing R_BING there creates no
        # advisor or chariot attack on the king.
        state = make_state(+1, rc_to_sq(9, 3), rc_to_sq(0, 4),
                           extra_pieces={(7, 4): Piece.B_MA, (8, 3): Piece.R_BING})
        assert is_in_check(state, +1) is False

    def test_soldier_check(self):
        """Soldier delivering check: forward square attack."""
        # Red king at (9,3), black king at (0,5) (different file, different col from soldier).
        # Black soldier (ZU) at (8,3): one square forward toward red king at (9,3).
        # No chariot or other piece on column 3 to override.
        state = make_state(+1, rc_to_sq(9, 3), rc_to_sq(0, 5),
                           extra_pieces={(8, 3): Piece.B_ZU})
        assert is_in_check(state, +1) is True

    def test_advisor_check(self):
        """Advisor delivering check via diagonal attack."""
        # Red king at (9,3), black advisor at (8,4) attacks diagonally
        state = make_state(+1, rc_to_sq(9, 3), rc_to_sq(0, 4),
                           extra_pieces={(8, 4): Piece.B_SHI})
        assert is_in_check(state, +1) is True

    def test_elephant_check(self):
        """Elephant delivering check via diagonal path."""
        # Black elephant at (7,5): eye at (8,4) empty, dest (9,3) = red king
        state = make_state(+1, rc_to_sq(9, 3), rc_to_sq(0, 4),
                           extra_pieces={(7, 5): Piece.B_XIANG})
        assert is_in_check(state, +1) is True

    def test_face_to_face_check(self):
        """Face-to-face rule: generals on same file with nothing between."""
        # Red king at (9,4), black king at (0,4) — same column, nothing between
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        assert is_in_check(state, +1) is True
        assert is_in_check(state, -1) is True

    def test_face_to_face_blocked_by_piece(self):
        """Piece between generals means no face-to-face check."""
        # Red king at (9,4), black king at (0,4) — same column.
        # R_MA at (5,4) is on column 4 between the kings -> blocks face-to-face.
        # No chariot on column 4; advisor at (8,4) does not attack the black king.
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4),
                           extra_pieces={(5, 4): Piece.R_MA})
        # Face-to-face blocked by horse at (5,4); no chariot -> no orthogonal check
        assert is_in_check(state, +1) is False
        assert is_in_check(state, -1) is False


class TestFlyingGeneralViolation:
    """RULE-04: flying_general_violation detects illegal face-to-face positions."""

    def test_violation_detected(self):
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        assert flying_general_violation(state, +1) is True

    def test_no_violation_different_file(self):
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 3))
        assert flying_general_violation(state, +1) is False

    def test_no_violation_piece_between(self):
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4),
                           extra_pieces={(5, 4): Piece.R_CHE})
        assert flying_general_violation(state, +1) is False


class TestApplyMove:
    """apply_move updates board, king_positions, turn, hash, history correctly."""

    def test_apply_move_captures(self):
        state = XiangqiState.starting()
        from_sq = rc_to_sq(9, 0)
        to_sq = rc_to_sq(0, 0)
        move = encode_move(from_sq, to_sq, is_capture=True)
        captured = apply_move(state, move)
        assert captured == Piece.B_CHE
        assert state.board[0, 0] == Piece.R_CHE
        assert state.board[9, 0] == 0
        assert state.turn == -1

    def test_apply_move_king_position_update(self):
        state = XiangqiState.starting()
        from_sq = rc_to_sq(9, 4)
        to_sq = rc_to_sq(8, 4)
        move = encode_move(from_sq, to_sq, is_capture=False)
        apply_move(state, move)
        assert state.king_positions[+1] == to_sq

    def test_apply_move_history_updated(self):
        state = XiangqiState.starting()
        from_sq = rc_to_sq(9, 0)
        to_sq = rc_to_sq(9, 1)
        move = encode_move(from_sq, to_sq, is_capture=False)
        apply_move(state, move)
        assert move in state.move_history
        assert len(state.zobrist_hash_history) == 2

    def test_apply_move_halfmove_clock(self):
        state = XiangqiState.starting()
        state.halfmove_clock = 5
        from_sq = rc_to_sq(6, 0)
        to_sq = rc_to_sq(7, 0)
        move = encode_move(from_sq, to_sq, is_capture=False)
        apply_move(state, move)
        assert state.halfmove_clock == 0


class TestIsLegalMove:
    """is_legal_move rejects moves that leave own king in check."""

    def test_own_king_left_in_check(self):
        """Moving piece that was blocking check is illegal."""
        state = make_state(+1, rc_to_sq(9, 3), rc_to_sq(0, 4),
                           extra_pieces={(5, 3): Piece.R_CHE, (0, 3): Piece.B_CHE})
        move = encode_move(rc_to_sq(5, 3), rc_to_sq(5, 4), is_capture=False)
        assert is_legal_move(state, move) is False

    def test_legal_move_no_check(self):
        """Move that does not leave king in check is legal."""
        state = make_state(+1, rc_to_sq(9, 3), rc_to_sq(0, 4))
        move = encode_move(rc_to_sq(9, 3), rc_to_sq(8, 3), is_capture=False)
        assert is_legal_move(state, move) is True

    def test_illegal_flying_general_violation(self):
        """Move that creates face-to-face generals is illegal."""
        # Red chariot at (1,3), red king at (9,4), black king at (0,4)
        # After chariot captures black king: kings face each other on col 4
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4),
                           extra_pieces={(1, 3): Piece.R_CHE})
        move = encode_move(rc_to_sq(1, 3), rc_to_sq(0, 4), is_capture=True)
        assert is_legal_move(state, move) is False


class TestGenerateLegalMoves:
    """generate_legal_moves returns all legal moves for current side."""

    def test_starting_position_legal_moves(self):
        """Starting position has 40+ legal moves for red (CPW=44)."""
        state = XiangqiState.starting()
        moves = generate_legal_moves(state)
        assert isinstance(moves, list)
        assert len(moves) >= 40

    def test_no_legal_moves_isolated_checkmate(self):
        """Isolated checkmate: double chariot mating net, no escape.

        Red king at (9,4), black chariot at (9,0) checks along row 9,
        black chariot at (0,4) controls column 4. All king escapes are covered:
        (9,3) and (9,5) attacked by row-9 chariot; (8,4) attacked by col-4 chariot.
        Own advisors at (8,3) and (8,5) block diagonal flight. No legal moves.
        """
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 3),
                           extra_pieces={
                               (9, 0): Piece.B_CHE,   # checking chariot (attacks row 9)
                               (0, 4): Piece.B_CHE,   # checking chariot (attacks col 4)
                               (8, 3): Piece.R_SHI,  # blocks (8,3) diagonal escape
                               (8, 5): Piece.R_SHI,  # blocks (8,5) diagonal escape
                           })
        moves = generate_legal_moves(state)
        assert len(moves) == 0

    def test_king_escape_moves_exist(self):
        """King in check has legal escape moves."""
        # Red king at (9,4) (palace center), black chariot at (0,4) checks col 4.
        # King can escape to (9,3) or (9,5); (8,4) still attacked by chariot.
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 3),
                           extra_pieces={(0, 4): Piece.B_CHE})
        moves = generate_legal_moves(state)
        general_moves = [m for m in moves
                         if decode_move(m)[0] == rc_to_sq(9, 4)]
        assert len(general_moves) > 0
        assert all(is_legal_move(state, m) for m in general_moves)
