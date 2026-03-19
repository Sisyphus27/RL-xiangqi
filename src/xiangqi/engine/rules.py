"""Xiangqi rule helpers: flying general detection, game result evaluation."""
from __future__ import annotations

import numpy as np

from .types import ROWS, COLS, rc_to_sq, sq_to_rc


def _generals_face_each_other(board: np.ndarray, king_positions: dict[int, int]) -> int | None:
    """Return the column index if both generals face each other (same col, nothing between), else None."""
    rk = king_positions.get(+1)
    bk = king_positions.get(-1)
    if rk is None or bk is None:
        return None
    rr, rc_col = sq_to_rc(rk)
    br, bc = sq_to_rc(bk)
    if rc_col != bc:
        return None
    lo, hi = min(rr, br), max(rr, br)
    for r in range(lo + 1, hi):
        if board[r, rc_col] != 0:
            return None
    return rc_col  # they face each other on this file


def flying_general_violation(state_after_move, turn_before_move: int) -> bool:
    """Return True if both generals would face each other after a move is applied.

    This is a violation: no piece may move to clear a file between the two generals.
    The turn_before_move parameter is accepted for API compatibility but the check
    is purely positional (board state after move is applied).
    """
    col = _generals_face_each_other(state_after_move.board, state_after_move.king_positions)
    return col is not None


def get_game_result(state) -> str:
    """Return game result: 'RED_WINS', 'BLACK_WINS', 'DRAW', or 'IN_PROGRESS'.

    Checks in order of priority:
    1. No legal moves + in check -> checkmate (current player loses)
    2. No legal moves + not in check -> stalemate (困毙) = loss in Xiangqi (current player loses)
    3. Otherwise -> IN_PROGRESS
    """
    from .legal import generate_legal_moves, is_in_check

    legal = generate_legal_moves(state)
    if len(legal) > 0:
        return 'IN_PROGRESS'

    # No legal moves -- check if in check
    in_check = is_in_check(state, state.turn)
    if in_check:
        # Checkmate: current player loses
        return 'BLACK_WINS' if state.turn == +1 else 'RED_WINS'
    else:
        # Stalemate (困毙) = loss in Xiangqi (not draw)
        return 'BLACK_WINS' if state.turn == +1 else 'RED_WINS'


__all__ = ['flying_general_violation', '_generals_face_each_other', 'get_game_result']
