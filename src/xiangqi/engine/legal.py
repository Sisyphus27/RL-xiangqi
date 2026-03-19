"""Check detection, legal-move filtering, and apply/undo move for Xiangqi.

This module provides the core rule-validation layer on top of the pure
pseudo-legal generators in moves.py. Legal move filtering uses board-copy
post-check: each candidate move is simulated on a state copy, then we verify
(1) the moving player's own general is not left in check, and (2) no flying
general violation results.
"""
from __future__ import annotations

from typing import List

import numpy as np

from .types import Piece, ROWS, COLS, rc_to_sq, sq_to_rc, encode_move, decode_move
from .moves import (
    gen_general, gen_chariot, gen_horse, gen_cannon,
    gen_advisor, gen_elephant, gen_soldier, all_pieces_of_color,
)
from .constants import IN_PALACE
from .state import XiangqiState, update_hash

# ─── Direction tables (same as moves.py, needed here for is_in_check) ─────────

_ORTHOGONAL = [(-1, 0), (+1, 0), (0, -1), (0, +1)]
_DIAGONAL = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
_HORSE_LEG_DEST = [
    (-1,  0, (-2, -1), (-2, +1)),
    (+1,  0, (+2, -1), (+2, +1)),
    ( 0, -1, (-1, -2), (+1, -2)),
    ( 0, +1, (-1, +2), (+1, +2)),
]

# ─── Check detection ──────────────────────────────────────────────────────────

def is_in_check(state: XiangqiState, color: int) -> bool:
    """Return True if the general of given color is under attack.

    Scans all enemy piece types that can attack the king. Includes the
    face-to-face rule: if both generals share a column with no pieces
    between, each is giving check to the other. (RULES.md §9.15)
    """
    ksq = state.king_positions.get(color)
    if ksq is None:
        return False
    kr, kc = divmod(ksq, 9)
    enemy = -color

    # 1. Orthogonal attackers: chariot, face-to-face general, cannon
    for dr, dc in _ORTHOGONAL:
        nr, nc = kr + dr, kc + dc
        first_piece_sq = None
        first_piece_val = 0
        screen_count = 0
        second_piece_sq = None
        second_piece_val = 0
        while 0 <= nr < ROWS and 0 <= nc < COLS:
            p = int(state.board[nr, nc])
            if p != 0:
                if screen_count == 0:
                    first_piece_sq = rc_to_sq(nr, nc)
                    first_piece_val = p
                    screen_count = 1
                else:
                    second_piece_sq = rc_to_sq(nr, nc)
                    second_piece_val = p
                    break
            nr += dr
            nc += dc
        if first_piece_sq is not None:
            if first_piece_val == enemy * 5:   # chariot attacks on same line
                return True
            if screen_count == 1 and second_piece_sq is not None:
                if second_piece_val == enemy * 6:   # cannon with exactly 1 screen
                    return True
                if first_piece_val == enemy * 1:    # face-to-face general (no screen)
                    return True

    # 2. Horse (L-shape, leg must be empty)
    for leg_entry in _HORSE_LEG_DEST:
        leg_dr, leg_dc, d1, d2 = leg_entry
        leg_r, leg_c = kr + leg_dr, kc + leg_dc
        # Bounds check BEFORE array access to avoid Python negative-index wrapping
        if not (0 <= leg_r < ROWS and 0 <= leg_c < COLS):
            continue
        if state.board[leg_r, leg_c] != 0:
            continue
        d1r, d1c = d1
        d2r, d2c = d2
        for dest_dr, dest_dc in ((d1r, d1c), (d2r, d2c)):
            nr, nc = kr + dest_dr, kc + dest_dc
            if not (0 <= nr < ROWS and 0 <= nc < COLS):
                continue
            if int(state.board[nr, nc]) == enemy * 4:  # horse
                return True

    # 3. Soldier: forward square only (adjacent row, same col)
    srow = kr + (1 if color == +1 else -1)
    if 0 <= srow < ROWS:
        if int(state.board[srow, kc]) == enemy * 7:  # soldier forward
            return True
    # Sideways: only if soldier is across the river
    for dc in (-1, +1):
        sc = kc + dc
        if 0 <= sc < COLS:
            soldier_row = srow
            if 0 <= soldier_row < ROWS:
                p = int(state.board[soldier_row, sc])
                if p == enemy * 7:
                    # Soldier attacks sideways only if it is across the river
                    if (enemy == +1 and soldier_row >= 5) or (enemy == -1 and soldier_row <= 4):
                        return True

    # 4. Advisor: adjacent diagonal within palace
    for dr, dc in _DIAGONAL:
        nr, nc = kr + dr, kc + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS:
            if IN_PALACE[nr, nc] and int(state.board[nr, nc]) == enemy * 2:
                return True

    # 5. Elephant: adjacent diagonal on own half (eye must be empty)
    for dr, dc in _DIAGONAL:
        nr, nc = kr + dr, kc + dc
        er, ec = kr + 2 * dr, kc + 2 * dc
        if 0 <= nr < ROWS and 0 <= nc < COLS and 0 <= er < ROWS and 0 <= ec < COLS:
            if int(state.board[nr, nc]) == 0:  # eye empty
                if int(state.board[er, ec]) == enemy * 3:
                    return True

    return False

# ─── Flying general detection ────────────────────────────────────────────────

def flying_general_violation(state: XiangqiState, turn_before_move: int) -> bool:
    """Return True if both generals face each other (same column, no pieces between).

    This is a violation: no piece may move to clear a file between the two generals.
    The turn_before_move parameter is accepted for API compatibility but the check
    is purely positional (board state after move is applied).
    """
    rk = state.king_positions.get(+1)
    bk = state.king_positions.get(-1)
    if rk is None or bk is None:
        return False
    rr, rc = divmod(rk, 9)
    br, bc = divmod(bk, 9)
    if rc != bc:
        return False
    lo, hi = min(rr, br), max(rr, br)
    for r in range(lo + 1, hi):
        if state.board[r, rc] != 0:
            return False
    return True  # generals face each other with nothing between

# ─── Move application ─────────────────────────────────────────────────────────

def apply_move(state: XiangqiState, move: int) -> int:
    """Apply move to state. Returns captured piece (0 if none).

    Updates board, king_positions, turn, Zobrist hash, halfmove_clock,
    and move_history.
    """
    from_sq, to_sq, _ = decode_move(move)
    fr, fc = sq_to_rc(from_sq)
    tr, tc = sq_to_rc(to_sq)
    piece = int(state.board[fr, fc])
    captured = int(state.board[tr, tc])

    # Update board
    state.board[tr, tc] = np.int8(piece)
    state.board[fr, fc] = np.int8(0)

    # Update king_positions if general moved
    pt = abs(piece)
    if pt == 1:  # general
        state.king_positions[state.turn] = to_sq

    # Update turn
    state.turn *= -1

    # Update Zobrist hash
    new_hash = update_hash(
        state.zobrist_hash_history[-1],
        from_sq, to_sq, piece, captured, state.turn
    )
    state.zobrist_hash_history.append(new_hash)

    # Update history and halfmove_clock
    state.move_history.append(move)
    if pt == 7 or captured != 0:
        state.halfmove_clock = 0
    else:
        state.halfmove_clock += 1

    return captured

# ─── Legal move filtering ─────────────────────────────────────────────────────

def is_legal_move(state: XiangqiState, move: int) -> bool:
    """Return True if move is legal for the side to move.

    Legality = pseudo-legal + own general not left in check + no flying general violation.
    """
    moving_color = state.turn  # color BEFORE turn flip
    snap = state.copy()
    apply_move(snap, move)
    # After apply_move, snap.turn is the OPPONENT's color.
    # Check that the MOVING PLAYER's general is NOT in check.
    if is_in_check(snap, moving_color):
        return False
    # No flying general violation
    if flying_general_violation(snap, moving_color):
        return False
    return True


def generate_legal_moves(state: XiangqiState) -> List[int]:
    """Return all legal moves for the side to move."""
    moves: List[int] = []
    for piece_sq in all_pieces_of_color(state.board, state.turn):
        fr, fc = sq_to_rc(piece_sq)
        piece = int(state.board[fr, fc])
        pt = abs(piece)
        if pt == 1:
            moves += gen_general(state.board, piece_sq, state.turn)
        elif pt == 2:
            moves += gen_advisor(state.board, piece_sq, state.turn)
        elif pt == 3:
            moves += gen_elephant(state.board, piece_sq, state.turn)
        elif pt == 4:
            moves += gen_horse(state.board, piece_sq, state.turn)
        elif pt == 5:
            moves += gen_chariot(state.board, piece_sq, state.turn)
        elif pt == 6:
            moves += gen_cannon(state.board, piece_sq, state.turn)
        elif pt == 7:
            moves += gen_soldier(state.board, piece_sq, state.turn)
    return [m for m in moves if is_legal_move(state, m)]


__all__ = ['is_in_check', 'is_legal_move', 'generate_legal_moves', 'apply_move', 'flying_general_violation']
