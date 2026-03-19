import numpy as np
from typing import Tuple

from .types import Piece  # noqa: F401 (re-export for consumers)

# ─── constants ────────────────────────────────────────────────────────────────
ROWS, COLS = 10, 9
NUM_SQUARES = ROWS * COLS  # 90

# ─── starting position (DATA-05) ─────────────────────────────────────────────
# WXF FEN — Xiangqi convention: red moves first (w), black back rank first
STARTING_FEN = (
    "rnbakabnr"  # rank 0: black back rank (row 0)
    "/9"         # rank 1: 9 empty squares (river + center)
    "/1c5c1"     # rank 2: black cannon, 5 empty, black cannon, 1 empty
    "/p1p1p1p1p" # rank 3: 5 black pawns separated by empties
    "/9"         # rank 4: 9 empty squares (river row 0)
    "/9"         # rank 5: 9 empty squares (river row 1)
    "/P1P1P1P1P" # rank 6: 5 red pawns
    "/1C5C1"     # rank 7: red cannon, 5 empty, red cannon, 1 empty
    "/9"         # rank 8: 9 empty squares
    "/RNBAKABNR" # rank 9: red back rank
    " w - 0 1"   # red to move, no castling, no en passant, halfmove 0, fullmove 1
)

# ─── boundary masks (DATA-05) ────────────────────────────────────────────────
# Palace: both 3x3 palaces (rows 0-2 cols 3-5 for black, rows 7-9 cols 3-5 for red)
IN_PALACE: np.ndarray = np.zeros((ROWS, COLS), dtype=bool)
IN_PALACE[0:3, 3:6] = True   # black palace
IN_PALACE[7:10, 3:6] = True  # red palace

# River boundary: rows 4 and 5 (between two sides)
IN_RIVER: np.ndarray = np.zeros((ROWS, COLS), dtype=bool)
IN_RIVER[4:6, :] = True

# Elephant home half (cannot cross the river)
IN_BLACK_HOME: np.ndarray = np.zeros((ROWS, COLS), dtype=bool)
IN_BLACK_HOME[0:5, :] = True   # black elephant home: rows 0-4

IN_RED_HOME: np.ndarray = np.zeros((ROWS, COLS), dtype=bool)
IN_RED_HOME[5:10, :] = True   # red elephant home: rows 5-9

# ─── FEN parser / serializer (DATA-05) ───────────────────────────────────────
# WXF piece map: uppercase=red, lowercase=black
_PIECE_MAP: dict[str, int] = {
    'K': +1, 'A': +2, 'B': +3, 'N': +4, 'R': +5, 'C': +6, 'P': +7,
    'k': -1, 'a': -2, 'b': -3, 'n': -4, 'r': -5, 'c': -6, 'p': -7,
}
_REV_PIECE_MAP: dict[int, str] = {v: k for k, v in _PIECE_MAP.items()}


def from_fen(fen: str) -> Tuple[np.ndarray, int]:
    """Parse WXF FEN string to (board, turn).

    Board rows 0-9 map to FEN ranks top-to-bottom (black back rank = row 0).
    Turn: +1=red to move, -1=black to move.
    """
    parts = fen.split()
    ranks_str = parts[0].split('/')
    board = np.zeros((ROWS, COLS), dtype=np.int8)

    for r_idx, rank in enumerate(ranks_str):
        c_idx = 0
        for ch in rank:
            if ch.isdigit():
                c_idx += int(ch)   # skip 'digit' empty squares
            else:
                board[r_idx, c_idx] = np.int8(_PIECE_MAP[ch])
                c_idx += 1

    turn = 1 if parts[1] == 'w' else -1
    return board, turn


def to_fen(board: np.ndarray, turn: int) -> str:
    """Serialize board + turn to WXF FEN string."""
    rank_strs = []
    for r in range(ROWS):
        rank = ''
        empty = 0
        for c in range(COLS):
            p = int(board[r, c])
            if p == 0:
                empty += 1
            else:
                if empty > 0:
                    rank += str(empty)
                    empty = 0
                rank += _REV_PIECE_MAP[p]
        if empty > 0:
            rank += str(empty)
        rank_strs.append(rank)

    color = 'w' if turn == 1 else 'b'
    return ' '.join(['/'.join(rank_strs), color, '-', '0', '1'])
