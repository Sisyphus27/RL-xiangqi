"""XiangqiEnv: Gymnasium-compatible RL environment wrapping XiangqiEngine."""
from __future__ import annotations

from typing import Dict

import gymnasium as gym
import numpy as np


# Lazy import to avoid circular deps
def _get_engine_class():
    from xiangqi.engine.engine import XiangqiEngine
    return XiangqiEngine


class XiangqiEnv(gym.Env):
    """Gymnasium Env subclass for Xiangqi (Chinese Chess).

    Wraps XiangqiEngine internally. Provides:
    - observation_space: Box(0.0, 1.0, (16, 10, 9), float32)
    - action_space: Discrete(8100)  -- flat index = from_sq * 90 + to_sq
    - reset(seed, options) -> (obs, info)
    - step(action) -> (obs, reward, terminated, truncated, info)

    Info dict contains:
    - legal_mask: np.ndarray (8100,) float32 -- 1.0 for legal actions
    - piece_masks: dict[int, np.ndarray] -- per-piece-type legal move masks (keys 0-6)
    - piece_type_to_move: int -- which piece type is proposing (0-6)
    - player_to_move: int -- +1=red, -1=black
    """

    metadata = {"render_modes": []}

    # PIECE VALUES for reward computation (used in Phase 11, pre-declare here)
    PIECE_VALUES = {0: 0, 1: 0, 2: 2, 3: 2, 4: 4, 5: 9, 6: 4.5, 7: 1}

    action_space: gym.spaces.Discrete
    observation_space: gym.spaces.Box

    def __init__(self):
        super().__init__()
        self.action_space = gym.spaces.Discrete(8100)  # D-03
        self.observation_space = gym.spaces.Box(
            low=0.0, high=1.0, shape=(16, 10, 9), dtype=np.float32
        )  # D-09
        self._engine = None
        self._np_random = None

    def reset(self, seed=None, options=None):
        # D-09: Initialize engine
        if seed is not None:
            self._np_random = np.random.default_rng(seed)
        else:
            self._np_random = np.random.default_rng()

        EngineCls = _get_engine_class()
        if options and options.get("fen"):
            self._engine = EngineCls.from_fen(options["fen"])
        else:
            self._engine = EngineCls.starting()

        obs = self._get_observation()
        info = self._get_info()
        return obs, info

    def step(self, action):
        """Execute one half-move.

        Args:
            action: int in [0, 8099] -- flat index = from_sq * 90 + to_sq

        Returns:
            (obs, reward, terminated, truncated, info)
        """
        # Decode flat action -> from_sq, to_sq
        from_sq = action // 90
        to_sq = action % 90

        # Bounds check: from_sq and to_sq must be in [0, 89]
        if from_sq >= 90 or to_sq >= 90:
            return (
                self._get_observation(),
                -2.0,
                False,
                False,
                {**self._get_info(), "illegal_move": True},
            )

        # Convert to engine's 16-bit encoding
        from xiangqi.engine.types import encode_move
        move = encode_move(from_sq, to_sq)

        # Illegal move: penalty, no state change (D-06)
        if not self._engine.is_legal(move):
            return (
                self._get_observation(),
                -2.0,
                False,
                False,
                {**self._get_info(), "illegal_move": True},
            )

        # Apply move
        captured = self._engine.apply(move)

        # Compute reward (D-07 terminal detection delegates to engine.result())
        result = self._engine.result()
        if result == "IN_PROGRESS":
            terminated = False
            reward = self._compute_reward(captured, to_sq)
        else:
            terminated = True
            if result == "RED_WINS":
                reward = 1.0
            elif result == "BLACK_WINS":
                reward = -1.0
            else:  # DRAW
                reward = 0.0

        obs = self._get_observation()
        info = self._get_info()
        return obs, reward, terminated, False, info

    def _get_observation(self):
        """Return (16, 10, 9) float32 raw board planes."""
        # Build 16 planes: 7 red (0-6), 7 black (7-13), repetition (14), halfmove (15)
        board = self._canonical_board()
        planes = np.zeros((16, 10, 9), dtype=np.float32)

        # Piece planes (0-13)
        for r in range(10):
            for c in range(9):
                piece = int(board[r, c])
                if piece == 0:
                    continue
                is_red = piece > 0
                pt = abs(piece) - 1  # 0-6 (D-04, D-05)
                channel = pt if is_red else (pt + 7)
                planes[channel, r, c] = 1.0

        # Channel 14: repetition count (normalized 0-3)
        state = self._engine.state
        current_hash = state.zobrist_hash_history[-1]
        rep_count = state.zobrist_hash_history.count(current_hash)
        planes[14] = np.clip(rep_count, 0, 3) / 3.0

        # Channel 15: halfmove clock (normalized 0-100)
        planes[15] = np.clip(state.halfmove_clock, 0, 100) / 100.0

        return planes

    def _canonical_board(self):
        """Return board with canonical rotation (D-10)."""
        board = self._engine.board.copy()  # (10, 9)
        if self._engine.turn == -1:  # black to move
            board = -np.rot90(board, k=2)  # 180 deg + negate piece values (D-10-07 fix)
        return board

    def _get_info(self):
        """Return info dict with legal_mask, piece_masks, piece_type_to_move, player_to_move."""
        legal_mask = self._build_legal_mask()
        piece_masks = self._build_piece_masks()
        board = self._canonical_board()

        # Determine piece_type_to_move (D-05): scan board for first piece of current player
        piece_type_to_move = 6  # default to soldier (last type)
        for r in range(10):
            for c in range(9):
                piece = int(board[r, c])
                if piece != 0 and (piece > 0) == (self._engine.turn == 1):
                    piece_type_to_move = abs(piece) - 1
                    break
            else:
                continue
            break

        return {
            "legal_mask": legal_mask,
            "piece_masks": piece_masks,
            "piece_type_to_move": piece_type_to_move,
            "player_to_move": self._engine.turn,
        }

    def _build_legal_mask(self):
        """Build full 8100-element legal move mask."""
        from xiangqi.engine.types import decode_move
        mask = np.zeros(8100, dtype=np.float32)
        for move in self._engine.legal_moves():
            from_sq, to_sq, _ = decode_move(move)
            mask[from_sq * 90 + to_sq] = 1.0
        return mask

    def _build_piece_masks(self):
        """Build per-piece-type legal move masks (D-04)."""
        from xiangqi.engine.types import decode_move
        masks = {pt: np.zeros(8100, dtype=np.float32) for pt in range(7)}
        board = self._canonical_board()

        # Map raw engine moves to canonical board coordinates
        engine_turn = self._engine.turn  # +1=red, -1=black
        for move in self._engine.legal_moves():
            from_sq, to_sq, _ = decode_move(move)
            # Decode raw engine coordinates
            er, ec = divmod(from_sq, 9)
            et, ec_to = divmod(to_sq, 9)

            # Apply canonical rotation to get coordinates in canonical board
            if engine_turn == -1:  # black to move: board was rotated 180
                cr, cc = 9 - er, 8 - ec
                ct, cc_to = 9 - et, 8 - ec_to
            else:
                cr, cc = er, ec
                ct, cc_to = et, ec_to

            canonical_from_sq = cr * 9 + cc
            canonical_to_sq = ct * 9 + cc_to
            action_idx = canonical_from_sq * 90 + canonical_to_sq

            # Determine piece type in canonical board
            canonical_piece = board[cr, cc]
            pt_idx = abs(int(canonical_piece)) - 1
            masks[pt_idx][action_idx] = 1.0

        return masks

    def get_legal_mask(self, player: int = 1) -> np.ndarray:
        """Public API (R4): full 8100-element legal move mask.

        Args:
            player: +1 for red, -1 for black. Only current turn player
                    returns non-zero mask.

        Returns:
            np.ndarray (8100,) float32 -- 1.0 for legal actions, 0.0 otherwise.
            Returns all-zero mask if player != current turn player.
        """
        if self._engine is None or player != self._engine.turn:
            return np.zeros(8100, dtype=np.float32)
        return self._build_legal_mask()

    def get_piece_legal_mask(self, piece_type: int, player: int) -> np.ndarray:
        """Public API (R4): per-piece-type legal move mask.

        Args:
            piece_type: int in [0, 6] (0=General, 1=Advisor, ..., 6=Soldier)
            player: +1 for red, -1 for black. Only current turn player
                    returns non-zero mask.

        Returns:
            np.ndarray (8100,) float32 -- 1.0 for legal actions of that piece type.
            Returns all-zero mask if player != current turn player or invalid piece_type.
        """
        if self._engine is None or player != self._engine.turn:
            return np.zeros(8100, dtype=np.float32)
        if not (0 <= piece_type <= 6):
            return np.zeros(8100, dtype=np.float32)
        masks = self._build_piece_masks()
        return masks[piece_type]

    def _compute_reward(self, captured: int, to_sq: int = -1) -> float:
        """Compute shaping reward for captured piece (red perspective).

        Args:
            captured: piece value on target square (0=none, >0=red piece, <0=black piece)
            to_sq: flat square index of target (needed for soldier river-crossing check)
        """
        if captured == 0:
            return 0.0

        piece_type = abs(captured)

        # Dynamic soldier value based on river crossing (D-01)
        if piece_type == 7 and to_sq >= 0:
            to_row = to_sq // 9
            if captured > 0:   # Red soldier captured by Black
                piece_value = 2.0 if to_row <= 4 else 1.0
            else:               # Black soldier captured by Red
                piece_value = 2.0 if to_row >= 5 else 1.0
        else:
            piece_value = self.PIECE_VALUES.get(piece_type, 0)

        # Red perspective: capturing enemy (captured < 0 = black piece) = positive reward
        sign = -1 if captured > 0 else 1
        return sign * piece_value / 100.0


# Gymnasium registration (D-01, enables gymnasium.make("Xiangqi-v0"))
gym.register(id="Xiangqi-v0", entry_point="xiangqi.rl.env:XiangqiEnv")
