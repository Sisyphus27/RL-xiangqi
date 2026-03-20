"""Repetition detection, perpetual check/chase tracking (END-03, END-04)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from .types import ROWS, COLS, sq_to_rc, rc_to_sq, Piece
from .state import XiangqiState
from .legal import is_in_check
from .moves import gen_chariot, gen_cannon, gen_general, gen_soldier


# ─── RepetitionState dataclass ───────────────────────────────────────────────

@dataclass
class RepetitionState:
    """Tracks state needed for perpetual-rule detection across a game.

    Lives in engine.py (Phase 4), not in XiangqiState. Passed as argument
    to get_game_result(). Zero-initialized at game start.
    """
    consecutive_check_count: int = 0
    chase_seq: List[tuple[int, int]] = field(default_factory=list)  # [(att_sq, tgt_sq), ...]
    last_chasing_color: int = 0  # +1 red, -1 black, 0 = none

    def reset(self) -> None:
        """Reset all counters (for game restart)."""
        self.consecutive_check_count = 0
        self.chase_seq = []
        self.last_chasing_color = 0


# ─── Repetition draw ─────────────────────────────────────────────────────────

def check_repetition(state: XiangqiState) -> Optional[str]:
    """Return 'DRAW' if any position appears 3+ times in zobrist_hash_history, else None.

    END-04: any 3 occurrences (not required to be consecutive).
    O(n) scan where n = len(zobrist_hash_history) <= ~500.
    """
    seen: dict[int, int] = {}
    for h in state.zobrist_hash_history:
        seen[h] = seen.get(h, 0) + 1
        if seen[h] >= 3:
            return 'DRAW'
    return None


# ─── Long check draw ─────────────────────────────────────────────────────────

def check_long_check(state: XiangqiState,
                     rep_state: RepetitionState) -> Optional[str]:
    """Return 'DRAW' if 4+ consecutive checking moves, else None.

    END-03 (long check): continuous check for 4+ moves by the same side
    without resolution -> draw (not loss).
    """
    if rep_state.consecutive_check_count >= 4:
        return 'DRAW'
    return None


# ─── Long chase detection ───────────────────────────────────────────────────

def _detect_chase(prev_state: XiangqiState, move: int,
                  new_state: XiangqiState, mover: int) -> Optional[tuple[int, int]]:
    """Return (attacking_sq, target_sq) if this move is a chase, else None.

    A chase = the moving piece attacks a non-king enemy piece.
    The chasing piece is at to_sq on the post-move board.
    Only general, chariot, cannon, and soldier can chase (per WXO rules).
    """
    from_sq = move & 0x1FF
    to_sq = (move >> 9) & 0x7F

    # Build post-move board from prev_state (pre-move state)
    board = prev_state.board.copy()
    fr, fc = divmod(from_sq, 9)
    tr, tc = divmod(to_sq, 9)
    piece = int(board[fr, fc])
    board[tr, tc] = piece
    board[fr, fc] = np.int8(0)

    pt = abs(piece)
    if pt == 1:
        moves = gen_general(board, to_sq, mover)
    elif pt == 5:
        moves = gen_chariot(board, to_sq, mover)
    elif pt == 6:
        moves = gen_cannon(board, to_sq, mover)
    elif pt == 7:
        moves = gen_soldier(board, to_sq, mover)
    else:
        return None  # advisor, elephant, horse cannot chase

    # Extract all attacked squares from the move list
    attacked_sqs: set[int] = set()
    for m in moves:
        attacked_sqs.add((m >> 9) & 0x7F)

    enemy = -mover
    for sq in attacked_sqs:
        r, c = divmod(sq, 9)
        p = int(board[r, c])
        if p == 0:
            continue
        # Enemy piece?
        if (p > 0) != (enemy > 0) and abs(p) != 1:
            # Attacks a non-king enemy piece -> this is a chase
            return (to_sq, sq)
    return None


def check_long_chase(state: XiangqiState,
                     rep_state: RepetitionState) -> Optional[str]:
    """Return winner if chaser loses after 4+ consecutive chases of same target, else None.

    END-03 (long chase): same (attacking_sq, target_sq) x4 consecutive by same side
    -> chaser LOSES (not draw). Per CONTEXT.md: chaser loses because they are
    deliberately creating the loop.
    """
    if len(rep_state.chase_seq) >= 4 and rep_state.last_chasing_color != 0:
        chaser = rep_state.last_chasing_color
        # chaser == +1 (red): chaser loses -> BLACK_WINS
        # chaser == -1 (black): chaser loses -> RED_WINS
        return 'RED_WINS' if chaser == -1 else 'BLACK_WINS'
    return None


__all__ = [
    'RepetitionState',
    'check_repetition',
    'check_long_check',
    'check_long_chase',
]
