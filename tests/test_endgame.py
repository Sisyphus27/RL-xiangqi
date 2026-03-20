"""Tests for endgame detection: checkmate, stalemate, draw conditions (END-01..END-04)."""
from __future__ import annotations

import numpy as np
import pytest

from src.xiangqi.engine.endgame import get_game_result
from src.xiangqi.engine.state import XiangqiState, compute_hash
from src.xiangqi.engine.types import Piece, ROWS, COLS, rc_to_sq


def make_state(turn: int, king_red_sq: int, king_black_sq: int,
               extra_pieces: dict[tuple[int, int], int] | None = None,
               zobrist_hash_history: list[int] | None = None,
               move_history: list[int] | None = None) -> XiangqiState:
    """Create a XiangqiState from scratch (mirrors test_rules.py make_state)."""
    board = np.zeros((ROWS, COLS), dtype=np.int8)
    kr, kc = divmod(king_red_sq, COLS)
    br, bc = divmod(king_black_sq, COLS)
    board[kr, kc] = Piece.R_SHUAI
    board[br, bc] = Piece.B_JIANG
    if extra_pieces:
        for (r, c), p in extra_pieces.items():
            board[r, c] = np.int8(p)
    if zobrist_hash_history is None:
        zobrist_hash_history = [compute_hash(board, turn)]
    return XiangqiState(
        board=board, turn=turn,
        king_positions={+1: king_red_sq, -1: king_black_sq},
        move_history=move_history or [],
        halfmove_clock=0,
        zobrist_hash_history=zobrist_hash_history,
    )


# ─── END-01: Checkmate ────────────────────────────────────────────────────────

class TestCheckmate:
    """END-01: No legal moves + in check -> opponent wins."""

    def test_checkmate_red_loses(self):
        """Classic double chariot checkmate: black to move is checkmated.

        Red king at (9,4), black chariots at (9,0) and (0,4) form mating net.
        All king squares are covered or blocked. King is in check.
        Red to move -> BLACK_WINS.
        """
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 3),
                           extra_pieces={
                               (9, 0): Piece.B_CHE,   # attacks row 9
                               (0, 4): Piece.B_CHE,   # attacks col 4 (checking)
                               (8, 3): Piece.R_SHI,  # blocks (7,3) diagonal
                               (8, 5): Piece.R_SHI,  # blocks (7,5) diagonal
                           })
        result = get_game_result(state)
        assert result == 'BLACK_WINS'

    def test_checkmate_black_loses(self):
        """Symmetric checkmate: red to move, black king at (0,4) is checkmated.

        Black king at (0,4), red chariots at (0,8) and (9,4) form mating net.
        Black has no legal moves, king is in check.
        Black to move -> RED_WINS.
        """
        state = make_state(-1, rc_to_sq(9, 3), rc_to_sq(0, 4),
                           extra_pieces={
                               (0, 8): Piece.R_CHE,   # attacks row 0
                               (9, 4): Piece.R_CHE,   # attacks col 4 (checking)
                               (1, 3): Piece.B_SHI,  # blocks (2,3) diagonal
                               (1, 5): Piece.B_SHI,  # blocks (2,5) diagonal
                           })
        result = get_game_result(state)
        assert result == 'RED_WINS'


# ─── END-02: Stalemate (困毙) = Loss in Xiangqi ──────────────────────────────

class TestStalemate:
    """END-02: No legal moves -> opponent wins (困毙 = loss in Xiangqi).

    In Xiangqi, a player with no legal moves always loses (no draw).
    This is called 困毙 (trapped/dead). Whether or not the king is directly
    in check, a player with zero legal moves loses immediately.
    """

    def test_stalemate_also_loss(self):
        """No legal moves -> opponent wins, regardless of whether king is in check.

        Same double-chariot checkmate position as test_checkmate_red_loses but with
        B_SHI at (8,4) as the forward blocker instead of R_SHI. The own red advisors
        at (8,3)/(8,5) block diagonal escapes; B_SHI at (8,4) is protected by
        B_CHE at (0,4) and blocks the forward diagonal; the chariot at (9,0) pins
        the king against its own pieces on row 9. Zero legal moves -> BLACK_WINS.
        """
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 3),
                           extra_pieces={
                               (9, 0): Piece.B_CHE,    # attacks row 9
                               (0, 4): Piece.B_CHE,    # attacks col 4
                               (8, 4): Piece.B_SHI,   # advisor blocks (8,4) escape
                               (8, 3): Piece.R_SHI,   # blocks diagonal (7,3)
                               (8, 5): Piece.R_SHI,   # blocks diagonal (7,5)
                           })
        result = get_game_result(state)
        assert result == 'BLACK_WINS'


# ─── IN_PROGRESS positions ───────────────────────────────────────────────────

class TestInProgress:
    """Positions with legal moves -> IN_PROGRESS."""

    def test_starting_position_in_progress(self, starting_state):
        """Starting position has 44 legal moves -> IN_PROGRESS."""
        assert get_game_result(starting_state) == 'IN_PROGRESS'

    def test_midgame_in_progress(self):
        """Any position with at least one legal move -> IN_PROGRESS."""
        state = XiangqiState.starting()
        state.board[0, 0] = 0  # remove black chariot
        result = get_game_result(state)
        assert result == 'IN_PROGRESS'


# ─── Priority order: repetition before check/stalemate ──────────────────────

class TestPriorityOrder:
    """Perpetual conditions must be checked BEFORE check/stalemate."""

    def test_repetition_draw_before_checkmate(self):
        """Position has 3x repetition AND no legal moves AND in check -> DRAW.

        The repetition draw must fire before the checkmate, per priority order.
        We construct a state where:
        1. zobrist_hash_history contains the same hash 3 times
        2. legal moves = 0 (checkmate position)
        3. is_in_check() = True
        Expected: DRAW (not BLACK_WINS).
        """
        # Use a checkmate position as base, then override the hash history
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 3),
                           extra_pieces={
                               (9, 0): Piece.B_CHE,
                               (0, 4): Piece.B_CHE,
                               (8, 3): Piece.R_SHI,
                               (8, 5): Piece.R_SHI,
                           })
        # Force repetition: all history entries are the same hash
        h = state.zobrist_hash_history[-1]
        state.zobrist_hash_history = [h, h, h]  # appears 3x -> DRAW
        result = get_game_result(state)
        assert result == 'DRAW'
