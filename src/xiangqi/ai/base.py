"""AI player abstract base class and engine snapshot dataclass.

This module defines the contract between the game engine and AI implementations.
EngineSnapshot provides thread-safe state capture for AI computation off the main thread.

Design decisions (per 07-CONTEXT.md D-07 to D-09):
  - AIPlayer is abstract base class defining suggest_move(snapshot: EngineSnapshot) -> int | None
  - EngineSnapshot holds immutable copy of board, turn, legal_moves
  - EngineSnapshot.from_engine() creates deep copy (thread-safe)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

import numpy as np


@dataclass(frozen=True)
class EngineSnapshot:
    """Immutable snapshot of engine state for thread-safe AI computation.

    Holds a deep copy of the board array and pre-computed legal moves.
    This allows AI to safely analyze the position without holding the GIL
    or blocking the main UI thread.

    Attributes:
        board: Deep copy of the 10x9 board array (np.int8)
        turn: +1 for red to move, -1 for black to move
        legal_moves: Pre-computed list of legal 16-bit move integers
    """
    board: np.ndarray  # shape (10, 9), dtype np.int8
    turn: int  # +1 red, -1 black
    legal_moves: List[int]  # pre-computed legal move integers

    @classmethod
    def from_engine(cls, engine) -> EngineSnapshot:
        """Create a snapshot from a XiangqiEngine instance.

        Creates deep copies of all mutable data for thread safety.
        The AI can safely analyze this snapshot without affecting the engine.

        Args:
            engine: A XiangqiEngine instance

        Returns:
            An immutable EngineSnapshot with deep-copied state
        """
        return cls(
            board=engine.board.copy(),  # DEEP COPY - critical for thread safety
            turn=engine.turn,
            legal_moves=list(engine.legal_moves()),  # list copy, not reference
        )


class AIPlayer(ABC):
    """Abstract base class for AI players.

    Subclasses must implement suggest_move() to select a move from the
    given game state snapshot. This interface is designed to be future-proof
    for various AI implementations (RandomAI, AlphaBetaAI, MCTSAI, etc.).

    Thread Safety:
        AIPlayer implementations receive an immutable EngineSnapshot and
        should not hold references to the engine or modify any state.
    """

    @abstractmethod
    def suggest_move(self, snapshot: EngineSnapshot) -> Optional[int]:
        """Select a move from the current position.

        Args:
            snapshot: Immutable snapshot of the current game state

        Returns:
            16-bit move integer, or None if no legal moves available
        """
        ...
