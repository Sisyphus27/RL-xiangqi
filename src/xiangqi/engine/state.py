"""Game state container and Zobrist hashing for Xiangqi."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict

import numpy as np

from .types import Piece, ROWS, COLS, NUM_SQUARES, rc_to_sq
from .constants import STARTING_FEN, from_fen

# ─── Zobrist hash tables ──────────────────────────────────────────────────────
# Shape (15, 90): index = piece_value + 7, mapping -7..+7 to 0..14
# Index 7 = EMPTY (= piece value 0), reserved but not hashed
_zobrist_piece: np.ndarray = np.zeros((15, NUM_SQUARES), dtype=np.uint64)

def _init_zobrist() -> None:
    """Eager Zobrist table initialization at module import time.

    Seed: 0x20240319 (fixed for reproducibility).
    """
    rng = random.Random(0x20240319)
    for piece_idx in range(15):
        for sq in range(NUM_SQUARES):
            _zobrist_piece[piece_idx, sq] = rng.getrandbits(64)

_init_zobrist()  # run at module import

# ─── Zobrist hash helpers ─────────────────────────────────────────────────────

def compute_hash(board: np.ndarray, turn: int) -> int:
    """Compute full Zobrist hash of a board position.

    O(90) — trivial for v0.1. Hashes each non-empty square piece,
    then XORs the turn bit if black to move.
    """
    h = 0
    for r in range(ROWS):
        for c in range(COLS):
            p = int(board[r, c])
            if p != 0:
                h ^= int(_zobrist_piece[p + 7, r * COLS + c])
    if turn == -1:
        h ^= _zobrist_piece[14, 0]  # XOR turn bit at a fixed square (index 14 unused piece slot)
    return h

def update_hash(
    old_hash: int,
    from_sq: int,
    to_sq: int,
    piece: int,
    captured: int,
    turn_after: int,
) -> int:
    """Incremental Zobrist hash update after a move.

    Removes old piece position, removes captured piece (if any),
    adds new piece position, flips turn bit.
    Returns new hash.
    """
    h = old_hash
    # Remove piece from source square
    h ^= int(_zobrist_piece[piece + 7, from_sq])
    # Remove captured piece from target square (if any)
    if captured != 0:
        h ^= int(_zobrist_piece[captured + 7, to_sq])
    # Add piece at target square
    h ^= int(_zobrist_piece[piece + 7, to_sq])
    # Flip turn bit (XOR with a fixed square in the unused index 14)
    h ^= int(_zobrist_piece[14, 0])
    return h

# ─── king position helper ─────────────────────────────────────────────────────

def _find_king_positions(board: np.ndarray) -> Dict[int, int]:
    """Scan board once and return {+1: red_king_sq, -1: black_king_sq}."""
    kings: Dict[int, int] = {}
    for r in range(ROWS):
        for c in range(COLS):
            p = board[r, c]
            if p == Piece.R_SHUAI:
                kings[+1] = rc_to_sq(r, c)
            elif p == Piece.B_JIANG:
                kings[-1] = rc_to_sq(r, c)
    return kings

# ─── XiangqiState dataclass ──────────────────────────────────────────────────

@dataclass
class XiangqiState:
    """Game state for a Xiangqi position.

    Fields (DATA-04):
      board: np.ndarray(10, 9, dtype=np.int8)
      turn: int  (+1=red, -1=black)
      move_history: list[int]  (encoded 16-bit moves)
      halfmove_clock: int  (plies since last pawn move or capture)
      zobrist_hash_history: list[int]  (running Zobrist hashes)

    Additional (researcher recommendation for Phase 2 performance):
      king_positions: dict[int, int]  (+1: red_sq, -1: black_sq)
    """
    board: np.ndarray
    turn: int
    move_history: list = field(default_factory=list)
    halfmove_clock: int = 0
    zobrist_hash_history: list = field(default_factory=list)
    king_positions: Dict[int, int] = field(default_factory=dict)

    @classmethod
    def from_fen(cls, fen: str) -> XiangqiState:
        """Parse a FEN string into a XiangqiState."""
        board, turn, halfmove_clock = from_fen(fen)
        king_positions = _find_king_positions(board)
        initial_hash = compute_hash(board, turn)
        return cls(
            board=board,
            turn=turn,
            move_history=[],
            halfmove_clock=halfmove_clock,
            zobrist_hash_history=[initial_hash],
            king_positions=king_positions,
        )

    @classmethod
    def starting(cls) -> XiangqiState:
        """Create initial Xiangqi position from STARTING_FEN."""
        return cls.from_fen(STARTING_FEN)

    def copy(self) -> XiangqiState:
        """Deep copy for copy-state move exploration (Phase 2)."""
        return XiangqiState(
            board=self.board.copy(),
            turn=self.turn,
            move_history=self.move_history.copy(),
            halfmove_clock=self.halfmove_clock,
            zobrist_hash_history=self.zobrist_hash_history.copy(),
            king_positions=dict(self.king_positions),
        )


__all__ = ['XiangqiState', 'compute_hash', 'update_hash', '_find_king_positions']
