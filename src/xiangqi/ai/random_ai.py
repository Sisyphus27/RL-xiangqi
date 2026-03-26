"""RandomAI - selects random legal moves."""
import random
from typing import Optional

from .base import AIPlayer, EngineSnapshot


class RandomAI(AIPlayer):
    """AI that selects uniformly random legal moves.

    Parameters
    ----------
    seed : int, optional
        Random seed for reproducibility. Default None (non-deterministic).

    Per D-10: RandomAI supports optional seed parameter for test reproducibility.
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def suggest_move(self, snapshot: EngineSnapshot) -> Optional[int]:
        """Select a random legal move.

        Returns
        -------
        int or None
            16-bit move integer, or None if no legal moves available.
        """
        if not snapshot.legal_moves:
            return None
        return self._rng.choice(snapshot.legal_moves)
