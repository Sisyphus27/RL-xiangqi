"""Pure pseudo-legal move generators for all 7 Xiangqi piece types.

Each gen_* function returns list[int] of 16-bit encoded moves given a board
state. No king-safety filtering here -- that is done by generate_legal_moves()
in legal.py using a board-copy post-check.
"""
from __future__ import annotations

from typing import List

import numpy as np

from .types import Piece, ROWS, COLS, rc_to_sq, sq_to_rc, encode_move
from .constants import IN_PALACE

# ─── Direction tables ─────────────────────────────────────────────────────────

# 4 orthogonal directions for chariot, cannon, general
_ORTHOGONAL = [(-1, 0), (+1, 0), (0, -1), (0, +1)]

# 4 diagonal directions for advisor, elephant
_DIAGONAL = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]

# Horse: for each leg direction, the two leg destinations after the orthogonal step.
# Format: (leg_dr, leg_dc, (dest1_dr, dest1_dc), (dest2_dr, dest2_dc))
# Source: RULES.md §2.3, PITFALLS.md Pitfall 3
_HORSE_LEG_DEST = [
    (-1,  0, (-2, -1), (-2, +1)),   # leg at row-1: two destinations row-2
    (+1,  0, (+2, -1), (+2, +1)),   # leg at row+1
    ( 0, -1, (-1, -2), (+1, -2)),   # leg at col-1
    ( 0, +1, (-1, +2), (+1, +2)),   # leg at col+1
]

# Elephant: for each diagonal destination, the eye (midpoint) offset.
# Format: (dest_dr, dest_dc, eye_dr, eye_dc)
# Source: RULES.md §2.6, PITFALLS.md Pitfall 4
_ELEPHANT_EYE_DEST = [
    (-2, -2, -1, -1),
    (-2, +2, -1, +1),
    (+2, -2, +1, -1),
    (+2, +2, +1, +1),
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def belongs_to(piece: int, color: int) -> bool:
    """True if piece belongs to color (red: positive, black: negative, non-zero only)."""
    return piece != 0 and (piece > 0) == (color > 0)


def all_pieces_of_color(board: np.ndarray, color: int) -> List[int]:
    """Return list of flat square indices for all pieces of given color."""
    return [rc_to_sq(r, c) for r in range(ROWS) for c in range(COLS)
            if belongs_to(int(board[r, c]), color)]

# ─── Piece generators ──────────────────────────────────────────────────────────

def gen_general(board: np.ndarray, from_sq: int, color: int) -> List[int]:
    """Orthogonal 1-step, confined to palace. Returns list of encoded moves."""
    fr, fc = sq_to_rc(from_sq)
    moves: List[int] = []
    for dr, dc in _ORTHOGONAL:
        nr, nc = fr + dr, fc + dc
        if not (0 <= nr < ROWS and 0 <= nc < COLS):
            continue
        if not IN_PALACE[nr, nc]:
            continue
        target = int(board[nr, nc])
        if not belongs_to(target, color):
            moves.append(encode_move(from_sq, rc_to_sq(nr, nc), is_capture=target != 0))
    return moves


def gen_chariot(board: np.ndarray, from_sq: int, color: int) -> List[int]:
    """Orthogonal sliding, stop at any piece. Collect all reachable squares."""
    fr, fc = sq_to_rc(from_sq)
    moves: List[int] = []
    for dr, dc in _ORTHOGONAL:
        nr, nc = fr + dr, fc + dc
        while 0 <= nr < ROWS and 0 <= nc < COLS:
            target = int(board[nr, nc])
            if not belongs_to(target, color):
                moves.append(encode_move(from_sq, rc_to_sq(nr, nc), is_capture=target != 0))
            if target != 0:  # stop on any piece (own or enemy)
                break
            nr += dr
            nc += dc
    return moves


def gen_horse(board: np.ndarray, from_sq: int, color: int) -> List[int]:
    """L-shape: orthogonal 1-step (leg) then diagonal 1-step. Leg must be empty."""
    fr, fc = sq_to_rc(from_sq)
    moves: List[int] = []
    for leg_entry in _HORSE_LEG_DEST:
        leg_dr, leg_dc, d1, d2 = leg_entry
        leg_r, leg_c = fr + leg_dr, fc + leg_dc
        # Bounds check BEFORE array access to avoid Python negative-index wrapping
        if not (0 <= leg_r < ROWS and 0 <= leg_c < COLS):
            continue
        if board[leg_r, leg_c] != 0:
            continue  # leg is blocked -- skip both destinations
        d1r, d1c = d1
        d2r, d2c = d2
        for dest_dr, dest_dc in ((d1r, d1c), (d2r, d2c)):
            nr, nc = fr + dest_dr, fc + dest_dc
            if not (0 <= nr < ROWS and 0 <= nc < COLS):
                continue
            target = int(board[nr, nc])
            if not belongs_to(target, color):
                moves.append(encode_move(from_sq, rc_to_sq(nr, nc), is_capture=target != 0))
    return moves


def gen_cannon(board: np.ndarray, from_sq: int, color: int) -> List[int]:
    """Orthogonal sliding: non-capture slides, capture requires exactly 1 screen."""
    fr, fc = sq_to_rc(from_sq)
    moves: List[int] = []
    for dr, dc in _ORTHOGONAL:
        nr, nc = fr + dr, fc + dc
        screen_count = 0
        while 0 <= nr < ROWS and 0 <= nc < COLS:
            target = int(board[nr, nc])
            if screen_count == 0:
                # Sliding mode: collect empty squares, stop at first piece
                if target == 0:
                    moves.append(encode_move(from_sq, rc_to_sq(nr, nc), is_capture=False))
                else:
                    screen_count = 1  # first piece found -- switch to capture mode
            else:
                # Capture mode: screen_count == 1
                if target == 0:
                    # Empty square after screen -- keep searching
                    pass
                else:
                    # Second piece encountered -- if enemy, it is capturable
                    if not belongs_to(target, color):
                        moves.append(encode_move(from_sq, rc_to_sq(nr, nc), is_capture=True))
                    break  # stop after second piece (regardless of capture or not)
            nr += dr
            nc += dc
    return moves


def gen_advisor(board: np.ndarray, from_sq: int, color: int) -> List[int]:
    """Diagonal 1-step, confined to palace."""
    fr, fc = sq_to_rc(from_sq)
    moves: List[int] = []
    for dr, dc in _DIAGONAL:
        nr, nc = fr + dr, fc + dc
        if not (0 <= nr < ROWS and 0 <= nc < COLS):
            continue
        if not IN_PALACE[nr, nc]:
            continue
        target = int(board[nr, nc])
        if not belongs_to(target, color):
            moves.append(encode_move(from_sq, rc_to_sq(nr, nc), is_capture=target != 0))
    return moves


def gen_elephant(board: np.ndarray, from_sq: int, color: int) -> List[int]:
    """Diagonal 2-step: eye midpoint must be empty; cannot cross river."""
    fr, fc = sq_to_rc(from_sq)
    # Red elephant home half: rows 5-9; black elephant home half: rows 0-4
    home_rows = range(5, 10) if color == +1 else range(0, 5)
    moves: List[int] = []
    for dr, dc, er, ec in _ELEPHANT_EYE_DEST:
        nr, nc = fr + dr, fc + dc
        eye_r, eye_c = fr + er, fc + ec
        if not (0 <= nr < ROWS and 0 <= nc < COLS):
            continue
        if nr not in home_rows:
            continue  # river constraint: cannot cross
        if board[eye_r, eye_c] != 0:
            continue  # elephant eye blocked
        target = int(board[nr, nc])
        if not belongs_to(target, color):
            moves.append(encode_move(from_sq, rc_to_sq(nr, nc), is_capture=target != 0))
    return moves


def gen_soldier(board: np.ndarray, from_sq: int, color: int) -> List[int]:
    """Forward 1-step always; forward+sideways after crossing river."""
    fr, fc = sq_to_rc(from_sq)
    moves: List[int] = []
    forward_dr = -1 if color == +1 else +1
    # Forward move
    nr, nc = fr + forward_dr, fc
    if 0 <= nr < ROWS:
        target = int(board[nr, nc])
        if not belongs_to(target, color):
            moves.append(encode_move(from_sq, rc_to_sq(nr, nc), is_capture=target != 0))
    # Sideways moves only after crossing river
    # Red crosses into rows 0-4 (black's home); black crosses into rows 5-9 (red's home)
    crossed = (color == +1 and fr <= 4) or (color == -1 and fr >= 5)
    if crossed:
        for dc in (-1, +1):
            nc_s = fc + dc
            if 0 <= nc_s < COLS:
                target = int(board[fr, nc_s])
                if not belongs_to(target, color):
                    moves.append(encode_move(from_sq, rc_to_sq(fr, nc_s), is_capture=target != 0))
    return moves


__all__ = [
    'gen_general', 'gen_chariot', 'gen_horse', 'gen_cannon',
    'gen_advisor', 'gen_elephant', 'gen_soldier',
    'belongs_to', 'all_pieces_of_color',
]
