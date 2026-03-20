"""Endgame detection: checkmate, stalemate, and draw conditions (END-01..END-04)."""
from __future__ import annotations

from .types import ROWS, COLS
from .state import XiangqiState
from .legal import generate_legal_moves, is_in_check

# Lazy import to avoid circular dependency at module load time
_REPETITION_IMPORTED = False
_RepetitionState = None
_check_repetition = None
_check_long_check = None
_check_long_chase = None

def _ensure_repetition():
    global _REPETITION_IMPORTED, _RepetitionState, _check_repetition, _check_long_check, _check_long_chase
    if not _REPETITION_IMPORTED:
        from .repetition import (
            RepetitionState,
            check_repetition,
            check_long_check,
            check_long_chase,
        )
        _RepetitionState = RepetitionState
        _check_repetition = check_repetition
        _check_long_check = check_long_check
        _check_long_chase = check_long_chase
        _REPETITION_IMPORTED = True


def get_game_result(state: XiangqiState,
                    rep_state: object = None) -> str:
    """Return game result: 'RED_WINS', 'BLACK_WINS', 'DRAW', or 'IN_PROGRESS'.

    Priority order (per CONTEXT.md):
    1. Threefold repetition (any hash appears 3x in zobrist_hash_history) -> DRAW
    2. Long check (4+ consecutive checking moves) -> DRAW
    3. Long chase (4+ consecutive chases of same target by same side) -> chaser loses
    4. No legal moves + in check -> checkmate -> opponent wins
    5. No legal moves + not in check -> stalemate (困毙) -> opponent wins
    6. Otherwise -> IN_PROGRESS
    """
    _ensure_repetition()

    if rep_state is None:
        rep_state = _RepetitionState()

    # 1. Repetition draw
    d = _check_repetition(state)
    if d is not None:
        return d

    # 2. Long check draw
    d = _check_long_check(state, rep_state)
    if d is not None:
        return d

    # 3. Long chase -> chaser loses
    d = _check_long_chase(state, rep_state)
    if d is not None:
        return d

    # 4. Checkmate / Stalemate
    legal = generate_legal_moves(state)
    if len(legal) == 0:
        # Both checkmate and stalemate are losses for the player to move in Xiangqi
        return 'BLACK_WINS' if state.turn == +1 else 'RED_WINS'

    return 'IN_PROGRESS'


__all__ = ['get_game_result']
