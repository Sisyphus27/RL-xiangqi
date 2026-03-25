"""Clean public API facade for the Xiangqi engine.

Wraps all internal modules (state, legal, endgame, repetition) behind a single
XiangqiEngine class. External callers use this class exclusively.

Design decisions (per 04-CONTEXT.md):
  - Engine holds and owns XiangqiState and RepetitionState
  - FEN on Engine class: from_fen() classmethod, to_fen() instance method
  - 7 public methods: reset, apply, undo, is_legal, legal_moves, is_check, result
  - 3 read-only properties: board, turn, move_history
  - Exceptions: illegal move/FEN -> ValueError; empty undo stack -> IndexError("nothing to undo")
  - apply/undo jointly maintain RepetitionState (apply snapshots before, undo restores)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

from .state import XiangqiState
from .legal import (
    apply_move as _apply_move,
    is_legal_move,
    generate_legal_moves,
    is_in_check,
)
from .endgame import get_game_result
from .repetition import RepetitionState
from .constants import to_fen
from .types import encode_move


# ─── Undo entry ─────────────────────────────────────────────────────────────

@dataclass
class UndoEntry:
    """Everything needed to reverse one applied move."""
    from_sq: int
    to_sq: int
    captured: int          # 0 = no capture
    piece: int             # the moving piece
    prev_hash: int         # zobrist_hash_history entry before this move
    prev_halfmove: int
    prev_king_positions: dict[int, int]
    rep_snapshot: RepetitionState  # full RepetitionState snapshot


# ─── Engine facade ──────────────────────────────────────────────────────────

class XiangqiEngine:
    """Clean public API wrapping all internal Xiangqi engine modules.

    The engine owns a private XiangqiState and RepetitionState.
    All public methods delegate to one of the four internal modules.

    API-01 methods:
      reset()       -> None
      apply(move)  -> captured: int
      undo()       -> None
      is_legal(move) -> bool
      legal_moves() -> list[int]
      is_check()    -> bool
      result()      -> str  ('RED_WINS'|'BLACK_WINS'|'DRAW'|'IN_PROGRESS')

    Factory constructors:
      starting()           -> XiangqiEngine  (class method)
      from_fen(fen: str)   -> XiangqiEngine  (class method, raises ValueError)

    Read-only properties:
      board: np.ndarray  (shape (10, 9))
      turn: int          (+1=red, -1=black)
      move_history: list[int]
    """

    def __init__(self) -> None:
        object.__setattr__(self, '_state', None)
        object.__setattr__(self, '_rep_state', RepetitionState())
        object.__setattr__(self, '_undo_stack', [])

    # ── Factory constructors ─────────────────────────────────────────────────

    @classmethod
    def starting(cls) -> XiangqiEngine:
        """Create engine at standard starting position (red to move)."""
        eng = cls()
        object.__setattr__(eng, '_state', XiangqiState.starting())
        return eng

    @classmethod
    def from_fen(cls, fen: str) -> XiangqiEngine:
        """Create engine from FEN string. Raises ValueError on parse error."""
        try:
            eng = cls()
            object.__setattr__(eng, '_state', XiangqiState.from_fen(fen))
            return eng
        except Exception as exc:
            raise ValueError(f"Invalid FEN: {fen}") from exc

    # ── Public API ──────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset to starting position. Clears undo stack and RepetitionState."""
        object.__setattr__(self, '_state', XiangqiState.starting())
        object.__setattr__(self, '_rep_state', RepetitionState())
        object.__setattr__(self, '_undo_stack', [])

    def apply(self, move: int) -> int:
        """Apply a move. Returns captured piece (0 if none). Raises ValueError if illegal."""
        # Validate move encoding: source square must contain a piece of the current player
        from_sq = move & 0x1FF
        to_sq   = (move >> 9) & 0x7F
        fr, fc  = divmod(from_sq, 9)
        tr, tc  = divmod(to_sq, 9)
        if not (0 <= fr < 10 and 0 <= fc < 9):
            raise ValueError(f"Illegal move: {move}")
        piece = self._state.board[fr, fc]
        if piece == 0:
            raise ValueError(f"Illegal move: {move}")
        if (piece > 0) != (self._state.turn > 0):
            raise ValueError(f"Illegal move: {move}")

        if not is_legal_move(self._state, move):
            raise ValueError(f"Illegal move: {move}")

        # Snapshot state fields BEFORE mutation
        captured = int(self._state.board[tr, tc])
        prev_hash = self._state.zobrist_hash_history[-1]
        prev_halfmove = self._state.halfmove_clock
        prev_king_positions = dict(self._state.king_positions)
        prev_turn = self._state.turn

        # Snapshot RepetitionState BEFORE mutation
        rep_snapshot = self._rep_state.copy()

        # Snapshot full state for RepetitionState.update() (pre-move position)
        pre_state = self._state.copy()
        # Rebuild pre-move board: move piece back
        pre_state.board[tr, tc] = pre_state.board[fr, fc]
        pre_state.board[fr, fc] = np.int8(0)
        pre_state.turn = prev_turn
        pre_state.king_positions = prev_king_positions
        # Remove the post-apply hash entry from the snapshot's history
        # (pre_state hash_history has the post-apply hash appended by .copy();
        #  we need the pre-apply hash entry, which is at [-2])
        if len(pre_state.zobrist_hash_history) >= 2:
            pre_state.zobrist_hash_history.pop()  # remove post-apply hash

        # Apply the move (mutates self._state in place)
        _apply_move(self._state, move)

        # Update RepetitionState with pre-move state snapshot
        self._rep_state.update(pre_state, move, self._state)

        # Push undo entry
        undo_stack = list(self._undo_stack)
        undo_stack.append(UndoEntry(
            from_sq=from_sq, to_sq=to_sq,
            captured=captured, piece=int(piece),
            prev_hash=prev_hash,
            prev_halfmove=prev_halfmove,
            prev_king_positions=prev_king_positions,
            rep_snapshot=rep_snapshot,
        ))
        object.__setattr__(self, '_undo_stack', undo_stack)

        return captured

    def undo(self) -> None:
        """Undo the last move. Raises IndexError if stack is empty."""
        if not self._undo_stack:
            raise IndexError("nothing to undo")
        entry: UndoEntry = self._undo_stack.pop()
        fr, fc = divmod(entry.from_sq, 9)
        tr, tc = divmod(entry.to_sq, 9)
        # Restore board
        self._state.board[fr, fc] = np.int8(entry.piece)
        self._state.board[tr, tc] = np.int8(entry.captured)
        # Restore state fields
        self._state.turn = -self._state.turn
        self._state.zobrist_hash_history.append(entry.prev_hash)
        self._state.halfmove_clock = entry.prev_halfmove
        self._state.king_positions = entry.prev_king_positions
        self._state.move_history.pop()
        # Restore RepetitionState from snapshot
        object.__setattr__(self, '_rep_state', entry.rep_snapshot)

    def is_legal(self, move: int) -> bool:
        """Return True if the given move is legal for the side to move."""
        return is_legal_move(self._state, move)

    def legal_moves(self) -> List[int]:
        """Return all legal moves for the side to move."""
        return list(generate_legal_moves(self._state))

    def is_check(self) -> bool:
        """Return True if the side to move is currently in check."""
        return is_in_check(self._state, self._state.turn)

    def result(self) -> str:
        """Return game result: 'RED_WINS', 'BLACK_WINS', 'DRAW', or 'IN_PROGRESS'."""
        return get_game_result(self._state, self._rep_state)

    # ── FEN ─────────────────────────────────────────────────────────────────

    def to_fen(self) -> str:
        """Serialize current position to WXF FEN string."""
        return to_fen(self._state.board, self._state.turn)

    # ── Read-only properties ────────────────────────────────────────────────

    @property
    def board(self) -> np.ndarray:
        """The current 10x9 board array (np.int8). Read-only."""
        return self._state.board

    @property
    def state(self) -> XiangqiState:
        """The current XiangqiState. Read-only."""
        return self._state

    @property
    def turn(self) -> int:
        """+1 if red to move, -1 if black to move. Read-only."""
        return self._state.turn

    @property
    def move_history(self) -> list:
        """List of applied 16-bit move integers. Read-only."""
        return self._state.move_history
