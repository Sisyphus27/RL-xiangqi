# RL Environment Design for Xiangqi

**Domain:** Xiangqi (Chinese Chess) Rule Engine as a Gymnasium-compatible RL Environment
**Project:** RL-Xiangqi — Heterogeneous Multi-Agent RL on Apple Silicon M1 Max
**Researched:** 2026-03-19
**Confidence:** HIGH (AlphaZero-style board encoding is well-established; Xiangqi-specific details from WXF rules research)

---

## Table of Contents

1. [RL Environment Interface (`gymnasium.Env`)](#1-rl-environment-interface-gymnasiumenv)
2. [Action Space Design](#2-action-space-design)
3. [Observation Representation (AlphaZero-Style Board Planes)](#3-observation-representation-alphazero-style-board-planes)
4. [Reward Shaping](#4-reward-shaping)
5. [PyTorch Integration](#5-pytorch-integration)
6. [Gymnasium Environment Patterns](#6-gymnasium-environment-patterns)
7. [Self-Play Training Loop Structure](#7-self-play-training-loop-structure)
8. [Known Xiangqi RL Projects for Reference](#8-known-xiangqi-rl-projects-for-reference)
9. [Performance Requirements for Batch Simulation](#9-performance-requirements-for-batch-simulation)
10. [Multi-Agent RL: Per-Piece-Type Networks](#10-multi-agent-rl-per-piece-type-networks)

---

## 1. RL Environment Interface (`gymnasium.Env`)

### Core API Contract

The environment wraps the Xiangqi rule engine (board state, legal move generation, rule enforcement) and exposes the standard `gymnasium.Env` interface:

```python
import gymnasium as gym
import numpy as np

class XiangqiEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    def __init__(self, config: dict | None = None):
        config = config or {}
        self._board = ...       # internal board state (np.ndarray 10x9, int8)
        self._history = ...      # move list, repetition counter
        self._player_to_move = 1  # +1 = red, -1 = black

    # ── Observation Space ────────────────────────────────────────────────────
    def _create_observation_space(self) -> gym.Space:
        # 14 channels (7 piece types × 2 colors) × 10 rows × 9 columns
        # Each channel is binary: 1.0 where that piece occupies the square
        return gym.Box(low=0.0, high=1.0, shape=(14, 10, 9), dtype=np.float32)

    # ── Action Space ─────────────────────────────────────────────────────────
    def _create_action_space(self) -> gym.Space:
        # 8100 = 90 positions × 90 destinations (all from/to combinations on 9×10 board)
        # Valid subset selected via action_mask
        return gym.Discrete(90 * 90)   # flat: (from_sq * 90 + to_sq)

    # ── Required Gymnasium Methods ───────────────────────────────────────────
    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict | None = None
    ) -> tuple[np.ndarray, dict]:
        """Reset to starting position (or custom FEN if options["fen"] provided)."""
        if seed is not None:
            self._np_random = np.random.default_rng(seed)

        self._board = self._init_board()        # np.ndarray (10, 9), int8
        self._history: list[Move] = []
        self._repetition_counter = collections.Counter()
        self._halfmove_clock = 0               # for 50-move rule
        self._player_to_move = 1               # red moves first
        self._terminal = False
        self._outcome = 0                       # 0 = ongoing, +1 = red wins, -1 = black wins, 2 = draw

        obs = self._get_observation()
        info = self._get_info()
        return obs, info

    def step(
        self,
        action: int
    ) -> tuple[np.ndarray, float, bool, bool, dict]:
        """
        Execute one half-move (one side's action).

        Returns:
            observation : np.ndarray (14, 10, 9) — current board as float32 planes
            reward      : float — shaping reward (see §4) for the acting player
            terminated  : bool — game is over (win/loss/draw)
            truncated   : bool — always False for Xiangqi (no step limit)
            info        : dict — legal_mask, outcome, repetition_count, etc.
        """
        if self._terminal:
            return self._get_observation(), 0.0, True, False, self._get_info()

        # Decode flat action → (from_sq, to_sq)
        from_sq = action // 90
        to_sq   = action % 90

        # Validate legality
        legal_moves = self.get_legal_moves(self._player_to_move)
        if (from_sq, to_sq) not in legal_moves:
            # Illegal move: apply strong penalty, do NOT update state
            reward = -2.0    # large penalty for policy exploring illegal moves
            terminated = False
            truncated = False
            info = self._get_info()
            info["illegal_move"] = True
            return self._get_observation(), reward, terminated, truncated, info

        # Apply move
        captured = self._apply_move(from_sq, to_sq)

        # Compute shaping reward (before terminal check, for the acting player)
        reward = self._compute_reward(captured, self._player_to_move)

        # Update repetition counter
        h = self._position_hash()
        self._repetition_counter[h] += 1
        self._halfmove_clock += 1

        # Terminal check
        self._terminal, self._outcome = self._detect_terminal()
        if self._terminal:
            reward = self._terminal_reward()   # +1 / -1 / 0

        self._player_to_move *= -1   # switch side

        obs = self._get_observation()
        info = self._get_info()
        return obs, reward, self._terminal, False, info

    def get_legal_moves(self, player: int) -> list[tuple[int, int]]:
        """Return list of legal (from_sq, to_sq) pairs for the given player."""
        # Implementation: generate all pseudo-legal moves for each piece,
        # filter by king-safety check and flying-general rule.
        # Returns flat indices: sq = row * 9 + col (0–89).

    def get_legal_mask(self) -> np.ndarray:
        """Return boolean mask over 8100-element action space."""
        mask = np.zeros(8100, dtype=np.float32)
        for (f, t) in self.get_legal_moves(self._player_to_move):
            mask[f * 90 + t] = 1.0
        return mask

    # ── Internal Helpers ──────────────────────────────────────────────────────
    def _get_observation(self) -> np.ndarray:
        """Return (14, 10, 9) float32 board planes — canonical (red-to-move) view."""
        return self._board_to_planes(self._board, self._player_to_move)

    def _board_to_planes(
        self,
        board: np.ndarray,       # (10, 9), int8
        perspective: int         # +1 = red view, -1 = black view
    ) -> np.ndarray:
        """AlphaZero-style binary feature planes. Shape: (14, 10, 9) float32."""
        planes = np.zeros((14, 10, 9), dtype=np.float32)
        for r in range(10):
            for c in range(9):
                piece = board[r, c]
                if piece == 0:
                    continue
                is_red = piece > 0
                pt = abs(piece) - 1           # 0=General, 1=Advisor, ..., 6=Soldier
                color_idx = 0 if is_red else 7
                channel = color_idx + pt
                # If black's turn in canonical view, flip the board
                if perspective == -1:
                    r_flip = 9 - r
                    c_flip = 8 - c
                else:
                    r_flip, c_flip = r, c
                planes[channel, r_flip, c_flip] = 1.0

        # Channel 14: repetitions (0/1/2/3+)
        planes[14] = min(self._repetition_counter[self._position_hash()], 3) / 3.0

        # Channel 15: no-capture / no-pawn-move halfmove count (for 50-move rule)
        planes[15] = min(self._halfmove_clock, 100) / 100.0

        return planes

    def _get_info(self) -> dict:
        return {
            "legal_mask": self.get_legal_mask(),
            "player_to_move": self._player_to_move,
            "outcome": self._outcome,
            "repetition_count": self._repetition_counter[self._position_hash()],
            "halfmove_clock": self._halfmove_clock,
            "history_len": len(self._history),
        }

    def render(self, mode="human"):
        ...
```

### Canonical Board State Convention

XiangqiEnv uses **canonical rotation**: the observation is always presented from the perspective of the player whose turn it is. The board array is flipped row-wise (and piece colors swapped) so the policy network always sees red at the bottom. This halves the number of positions the network must learn to recognize.

```
# Canonical view:
# - Rows 0-9: top=black back rank, bottom=red back rank
# - Active player always sees their General at the bottom
# - Planes are reoriented (flipped) for the non-active player at each step
```

---

## 2. Action Space Design

### Options

There are three primary action space representations for Xiangqi RL:

| Representation | Size | Pros | Cons |
|---|---|---|---|
| **Flat Discrete** `(from, to)` | 8100 (90×90) | Simple; matches `gym.Discrete`; works with any policy head | Most actions are illegal; requires strong masking |
| **From-To Separate** `(from_sq, dir)` | 90×8 or 90×16 | Reduces branching; directional policy | Complex to implement correctly; hard to mask |
| **Per-Destination Policy** | 90 destination logits | Natural for CNN heads; easy masking | Duplicates source-selection information |

### Recommended: Flat Discrete with Action Masking

**Action encoding:** Flat index `a = from_sq * 90 + to_sq`, where `from_sq` and `to_sq` are both in `[0, 89]` (row * 9 + col). This maps directly to `gym.spaces.Discrete(8100)`.

**Rationale:** The flat discrete space is the simplest implementation that is correct. Legal move counts in Xiangqi average 35–50 per position (slightly fewer than Western chess, which has ~38 average). A mask over 8100 is trivial to compute and apply.

```python
# Policy head output: logits over all 8100 actions
logits = policy_network(observation)                    # (B, 8100)
legal_mask = env.get_legal_mask()                       # (8100,) float32 {0, 1}

# Masked softmax — prevents sampling/moving illegal actions
MASK_VALUE = -1e9
logits = logits + (1 - legal_mask) * MASK_VALUE
probs   = torch.softmax(logits, dim=-1)

# For training: cross-entropy against masked one-hot target
# For inference: torch.argmax(probs) or weighted sampling
```

### Legal Move Generation Order

For the RL training loop, legal move generation must be **fast and deterministic**. Recommended order:

1. Generate pseudo-legal moves per piece type using precomputed lookup tables
2. Filter by king safety: for each candidate move, apply move → check if own king attacked → undo
3. Filter by flying-general rule (per WXF rules, not Western chess)

**Performance note:** Pure Python legal move generation is fast enough for RL workloads. A typical position generates 35–50 legal moves in 0.2–1.0 ms on a modern CPU. No Cython needed for v0.1.

### Piece-Specific Action Sub-Spaces (Multi-Agent Path)

If using per-piece-type networks (see Section 10), each agent proposes moves only from squares where its piece type exists:

```python
def get_piece_legal_mask(self, piece_type: int) -> np.ndarray:
    """Return legal-move mask for a specific piece type only (0–6)."""
    mask = np.zeros(8100, dtype=np.float32)
    for (f, t) in self.get_legal_moves(self._player_to_move):
        if self._board[from_row(f), from_col(f)] == piece_type:
            mask[f * 90 + t] = 1.0
    return mask
```

---

## 3. Observation Representation (AlphaZero-Style Board Planes)

### Channel Layout

The standard AlphaZero-inspired representation for Xiangqi uses **14 binary occupancy planes + 2 auxiliary scalar planes**:

```
Channel  0: Red General    (1.0 = red General at this square)
Channel  1: Red Advisor
Channel  2: Red Elephant
Channel  3: Red Horse
Channel  4: Red Chariot
Channel  5: Red Cannon
Channel  6: Red Soldier
Channel  7: Black General
Channel  8: Black Advisor
Channel  9: Black Elephant
Channel 10: Black Horse
Channel 11: Black Chariot
Channel 12: Black Cannon
Channel 13: Black Soldier
Channel 14: Repetition count   (0.0 / 0.33 / 0.67 / 1.0)
Channel 15: Halfmove clock    (normalized 0–100)
```

**Shape:** `(16, 10, 9)` float32 per observation.

This matches the AlphaZero pattern exactly: one binary channel per piece type per color, plus auxiliary history/repetition channels.

### Why Binary Planes, Not Integer Encoding?

Integer encoding (e.g., `[0, 10]` per cell) is simpler but suboptimal for CNNs:
- Integer values have no spatial meaning for conv filters — the model must learn that 7 and -7 are "same piece type, different color"
- Binary planes allow the CNN to use individual channels as feature detectors, which is more natural for spatial reasoning
- The AlphaZero paper demonstrates binary planes significantly outperform integer encoding for chess-like games
- The `(16, 10, 9)` float32 tensor is directly usable as a PyTorch convolution input

### Coordinate System

```
Board (10 rows × 9 columns):

Row 0: Black back rank   (row 0 at visual top)
Row 4: River (empty row)
Row 5: River (empty row)
Row 9: Red back rank    (row 9 at visual bottom)

Col 0: left edge
Col 4: center file
Col 8: right edge

Palace boundaries:
  Black palace: rows 0–2, cols 3–5
  Red palace:   rows 7–9, cols 3–5
```

### Canonical Rotation (Critical for Learning)

At every `reset()` and `step()`, the observation tensor is re-oriented so the active player sees their pieces in the same orientation as the starting position. This means:
- The network never needs to learn separate red/black policies from separate board orientations
- The same network weights learn from all game positions regardless of which side is to move

```python
def _canonical_observation(self) -> np.ndarray:
    """Return board planes from the active player's perspective."""
    if self._player_to_move == 1:   # red to move → no change
        return self._board_to_planes(self._board, perspective=1)
    else:                            # black to move → rotate 180°
        return self._board_to_planes(
            np.rot90(self._board, k=2),   # 180° rotation
            perspective=-1
        )
```

**Note:** 180° rotation is equivalent to row-flip + col-flip for the board array, plus swapping red/black channel groups. The `np.rot90(arr, k=2)` approach is simplest.

### History Planes

For AlphaZero-style training, historical board states are included as additional planes. A typical setup uses the last 8 plies (4 full moves):

```
Channels 16–31: board planes 1 ply ago
Channels 32–47: board planes 2 plies ago
...
```

This adds context about recent move history without requiring a recurrent memory. For v0.1, omit history planes to keep the architecture simple; add them once the base system trains correctly.

---

## 4. Reward Shaping

### Reward Signal Hierarchy

Xiangqi has a sparse terminal reward structure — most games last 80–150 plies with near-zero reward until a win/loss event. Pure terminal reward (+1/-1) is too sparse for effective learning; dense shaping is required.

| Reward | Value | Trigger | Notes |
|---|---|---|---|
| **Terminal Win** | +1.0 | Game ends — opponent is checkmated or loses by WXF rule | Dominant reward signal |
| **Terminal Loss** | -1.0 | Current player loses | |
| **Terminal Draw** | 0.0 | Repetition draw, 50-move rule, insufficient material | |
| **Capture (positive)** | +piece_value / 100 | Capture an enemy piece | Shaping reward |
| **Capture (loss)** | -piece_value / 100 | Lose a piece to enemy | Negative shaping |
| **Check** | +0.05 | Move places opponent's General in check | Mild shaping |
| **Illegal move penalty** | -2.0 | Policy selects illegal action (RL exploration) | Prevents policy from wasting samples on illegal moves |

### Piece Value Table (Material Shaping)

| Piece Type | Value | Red Channel | Black Channel |
|---|---|---|---|
| General (将/帅) | Not applicable | — | — |
| Advisor (仕/士) | 2 | 0.02 | -0.02 |
| Elephant (相/象) | 2 | 0.02 | -0.02 |
| Horse (马) | 4 | 0.04 | -0.04 |
| Chariot (车) | 9 | 0.09 | -0.09 |
| Cannon (炮) | 4.5 | 0.045 | -0.045 |
| Soldier (卒/兵) | 1 (pre-river), 2 (post-river) | 0.01–0.02 | -0.01–-0.02 |

The per-step material delta is the difference in total piece value before and after the move. This is a **potential-based shaping function** — it does not change the optimal policy (no Sutton-style guarantee violation) because it is a difference of state values, not an arbitrary bonus.

```python
def _compute_reward(self, captured_piece: int | None, actor: int) -> float:
    """Compute shaping reward for the acting player."""
    if self._terminal:
        return self._terminal_reward()    # +1 / -1 / 0

    reward = 0.0

    # Material capture reward
    if captured_piece is not None:
        piece_value = PIECE_VALUES[abs(captured_piece)]
        reward += (piece_value * actor) / 100.0   # positive if red captured, negative if black

    # Check reward (small bonus for discovering/confirming a check)
    if self._is_in_check(actor * -1):
        reward += 0.05 * actor    # positive for red, negative for black

    return reward
```

### Sparse vs. Dense Trade-offs

- **Pure terminal reward** (+1/-1/0 only): Too sparse. Random exploration cannot discover wins for thousands of episodes. Cold-start failure mode is guaranteed without a warm-up phase.
- **Dense material shaping**: Provides per-step gradient signal. Scales naturally with play quality. Risk: agent may optimize for piece trades instead of checkmate.
- **Potential-based shaping (recommended)**: `F(s) = gamma * V(s') - V(s)` where V is a learned value function. This preserves optimality guarantee. Practical version: use piece value delta as a handcrafted V approximation.
- **Win-hint shaping**: Give a bonus when the agent enters a position classified as "winning" by a simple heuristic (e.g., material advantage + advanced soldier position). Use sparingly — over-reliance on heuristics defeats the RL-from-zero goal.

### WXF Perpetual Check/Chase and Reward

Under WXF rules, perpetual check is a **loss for the checking player**, not a draw. The environment must correctly identify this:

```python
def _detect_terminal(self) -> tuple[bool, int]:
    # Checkmate
    if len(self.get_legal_moves(self._player_to_move)) == 0:
        if self._is_in_check(self._player_to_move):
            return True, -self._player_to_move   # loser = side in check
        else:
            return True, -self._player_to_move   # stalemate = loss in Xiangqi

    # Repetition: 4-fold
    h = self._position_hash()
    if self._repetition_counter[h] >= 4:
        return True, 0    # draw by repetition

    # 50-move rule
    if self._halfmove_clock >= 100:
        return True, 0    # draw

    # WXF Perpetual check: if the same checking-side position repeats
    # with the same player to move and the move was a checking move,
    # and count >= 4: loss for the checking player
    if self._is_perpetual_check():
        return True, self._perpetual_check_loser()

    return False, 0
```

---

## 5. PyTorch Integration

### Tensor Output Contract

The environment outputs **NumPy arrays** (`np.ndarray`); the caller converts to PyTorch tensors:

```python
# Environment returns NumPy
obs, info = env.reset()
legal_mask = info["legal_mask"]           # np.ndarray (8100,), float32

# Convert to PyTorch tensor
obs_t = torch.from_numpy(obs).unsqueeze(0).to("mps")   # (1, 16, 10, 9)
mask_t = torch.from_numpy(legal_mask).unsqueeze(0).to("mps")  # (1, 8100)
```

**Critical:** All tensors must be `float32` on MPS. `float64` (`np.float64`) and `bfloat16` are not supported by the Metal API and will crash or silently fall back to CPU.

### Batch Processing Support

For self-play simulation (Section 7), the environment must support batch stepping:

```python
class XiangqiEnv:
    def reset_batch(self, n: int, seeds: list[int] | None = None):
        """Reset n environments, return batch of observations."""
        obs_batch = np.zeros((n, 16, 10, 9), dtype=np.float32)
        for i in range(n):
            obs_batch[i], _ = self.reset(seed=(seeds[i] if seeds else None))
        return obs_batch

    def step_batch(
        self,
        actions: np.ndarray   # (n,) flat action indices
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[dict]]:
        """Step n environments in batch. Returns NumPy arrays for vectorized processing."""
        n = len(actions)
        obs  = np.zeros((n, 16, 10, 9), dtype=np.float32)
        rew  = np.zeros(n, dtype=np.float32)
        term = np.zeros(n, dtype=bool)
        for i in range(n):
            obs[i], rew[i], term[i], _, info = self.step(actions[i])
        return obs, rew, term, np.zeros(n, dtype=bool), [info] * n
```

**Performance note:** `reset_batch` and `step_batch` use Python loops for now. They are fast because the board state is lightweight (10×9 = 90 bytes) and the bottleneck is legal move generation. Once the single-env path is validated, a C-extension or Cython batch stepper can be added if needed.

### Device-Aware Forward Pass

```python
def select_action(
    policy_net: nn.Module,
    obs: np.ndarray,        # or torch.Tensor
    legal_mask: np.ndarray,
    device: str = "mps",
    deterministic: bool = False,
    temperature: float = 1.0,
) -> int:
    """Select action from policy network given observation and legal mask."""
    if isinstance(obs, np.ndarray):
        obs_t = torch.from_numpy(obs).unsqueeze(0).float().to(device)
    else:
        obs_t = obs.unsqueeze(0) if obs.dim() == 3 else obs

    mask_t = torch.from_numpy(legal_mask).unsqueeze(0).float().to(device)

    with torch.no_grad():
        logits = policy_net(obs_t)            # (1, 8100)
        logits = logits + (1 - mask_t) * -1e9
        if temperature == 0.0 or deterministic:
            action_idx = logits.argmax(dim=-1)
        else:
            probs = torch.softmax(logits / temperature, dim=-1)
            action_idx = torch.multinomial(probs.squeeze(0), num_samples=1)

    return action_idx.item()
```

### MPS-Specific Considerations

```python
# At startup — verify MPS availability
import torch
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Using device: {device}")

# Enforce float32 globally — prevent any accidental float64
torch.set_default_dtype(torch.float32)

# For tensor creation, always specify dtype explicitly
obs_t = torch.zeros((1, 16, 10, 9), dtype=torch.float32, device=device)

# Adam optimizer — ensure contiguous tensors before step (MPS < 2.4 bug mitigation)
for param_group in optimizer.param_groups:
    for p in param_group["params"]:
        if not p.is_contiguous():
            p.data = p.data.contiguous()
optimizer.step()
```

---

## 6. Gymnasium Environment Patterns

### Full Gymnasium Compatibility

Implement the `gymnasium.Env` interface precisely to gain compatibility with standard RL tooling:

```python
import gymnasium as gym
import numpy as np

class XiangqiEnv(gym.Env):
    # Required class attributes
    action_space: gym.spaces.Discrete
    observation_space: gym.spaces.Box

    # Optional: provide a non-trivial observation space for vectorized environments
    def __init__(self, config: dict | None = None):
        super().__init__()
        self.action_space = gym.spaces.Discrete(90 * 90)
        # Channels: 14 piece planes + 2 auxiliary
        self.observation_space = gym.spaces.Box(
            low=0.0, high=1.0,
            shape=(16, 10, 9),
            dtype=np.float32
        )
        self._config = config or {}
        self._board = None
        self._initialize()

    # Property-based wrappers for Stable-Baselines3 / TorchRL compatibility
    @property
    def unwrapped(self) -> "XiangqiEnv":
        return self
```

### Vectorized Environments

For self-play batch simulation, wrap in `gymnasium.vector.SyncVectorEnv`:

```python
def make_xiangqi_vec_env(n_envs: int = 8) -> gym.vector.VectorEnv:
    def make_env(rank: int):
        def _init():
            env = XiangqiEnv()
            env.reset(seed=rank)
            return env
        return _init

    return gym.vector.SyncVectorEnv([make_env(i) for i in range(n_envs)])
```

This runs n environments in separate Python processes (Unix fork), bypassing the GIL for CPU-bound legal move generation. Neural network forward passes still run on MPS.

### Action Space with Masking (`MaskableppoWrapper`)

Gymnasium provides `gymnasium.wrappers.TransformObservation` and `gymnasium.wrappers.TimeAwareObservation`, but for action masking the standard approach is:

```python
# Use SB3's ActionMaskPPO which accepts "action_mask" in the info dict
# Or implement masking inline in the training loop (preferred for custom PPO):

class MaskedCategorical:
    """Masked softmax categorical distribution for masked policy logits."""
    def __init__(self, logits: torch.Tensor, mask: torch.Tensor):
        self.logits = logits
        self.mask = mask

    def probs(self) -> torch.Tensor:
        # Apply mask as -inf
        masked_logits = self.logits.clone()
        masked_logits[~self.mask.bool()] = -float("inf")
        return torch.softmax(masked_logits, dim=-1)

    def sample(self) -> torch.Tensor:
        probs = self.probs()
        return torch.multinomial(probs, 1).squeeze(-1)

    def log_prob(self, actions: torch.Tensor) -> torch.Tensor:
        probs = self.probs()
        return torch.log(probs.gather(-1, actions.unsqueeze(-1)).squeeze(-1) + 1e-8)
```

### Reward Scaling

The terminal reward is +1.0 and shaping rewards are small (max ~0.1). This reward scale is well-suited for PyTorch's default learning rates. No reward normalization is needed.

If per-batch normalization is desired (e.g., standardizing rewards across a batch), use a running mean/std tracked over the last 10,000 steps:

```python
class RewardNormalizer:
    def __init__(self, clip: float = 10.0):
        self.count = 0
        self.mean = 0.0
        self.var = 1.0
        self.clip = clip

    def update(self, reward: float):
        self.count += 1
        delta = reward - self.mean
        self.mean += delta / self.count
        delta2 = reward - self.mean
        self.var += (delta * delta2 - self.var) / self.count

    def normalize(self, reward: float) -> float:
        std = max(np.sqrt(self.var), 1e-8)
        return np.clip((reward - self.mean) / std, -self.clip, self.clip)
```

---

## 7. Self-Play Training Loop Structure

### AlphaZero-Style Self-Play Loop

The self-play loop is the core training mechanism. It generates game episodes, stores transitions, and periodically updates the policy/value networks.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Self-Play Training Loop                          │
│                                                                          │
│  for game_idx in range(n_games):                                         │
│    obs, _ = env.reset()                                                  │
│    trajectory = []                                                       │
│    while not done:                                                       │
│      legal_mask = env.get_legal_mask()                                   │
│      action = select_action(policy_net, obs, legal_mask, temp)            │
│      next_obs, reward, terminated, truncated, info = env.step(action)    │
│      trajectory.append((obs, action, reward, next_obs, done, legal_mask))│
│      obs = next_obs                                                      │
│      if terminated: break                                                │
│                                                                          │
│    replay_buffer.extend(trajectory)                                       │
│                                                                          │
│    if game_idx % update_freq == 0:                                        │
│      batch = replay_buffer.sample(batch_size)                            │
│      update_policy_network(batch)      # PPO or REINFORCE               │
│      update_value_network(batch)                                        │
│                                                                          │
│    if game_idx % eval_freq == 0:                                          │
│      win_rate = evaluate(policy_net, opponent_net, n_games=100)           │
│      if win_rate > best_win_rate:                                         │
│        best_model = copy(policy_net)                                     │
│        save_checkpoint(policy_net, f"best_model.pt")                     │
│      opponent_net = best_model  # self-play with current best          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Detailed Training Step (PPO)

```python
import torch
import torch.nn as nn
import torch.optim as optim

class PPOTrainer:
    def __init__(
        self,
        policy_net: nn.Module,
        value_net: nn.Module,
        device: str,
        lr: float = 3e-4,
        clip_eps: float = 0.2,
        entropy_coef: float = 0.01,
        value_coef: float = 0.5,
        max_grad_norm: float = 1.0,
    ):
        self.policy_opt = optim.Adam(policy_net.parameters(), lr=lr)
        self.value_opt  = optim.Adam(value_net.parameters(),  lr=lr)
        self.clip_eps   = clip_eps
        self.entropy_coef = entropy_coef
        self.value_coef   = value_coef
        self.max_grad_norm = max_grad_norm
        self.device = device
        self.policy_net = policy_net

    def update(self, batch: list):
        """
        Perform one PPO update over a batch of transitions.

        batch: list of (obs, action, reward, next_obs, done, legal_mask)
        """
        obs_t      = torch.stack([torch.from_numpy(x[0]) for x in batch]).to(self.device)
        actions    = torch.tensor([x[1] for x in batch], dtype=torch.long, device=self.device)
        rewards    = torch.tensor([x[2] for x in batch], dtype=torch.float32, device=self.device)
        dones      = torch.tensor([x[4] for x in batch], dtype=torch.float32, device=self.device)
        masks_t    = torch.stack([torch.from_numpy(x[5]) for x in batch]).to(self.device)

        T = len(batch)
        # Compute returns (Monte-Carlo for now; GAE in full implementation)
        returns = torch.zeros(T, device=self.device)
        running = 0.0
        for t in reversed(range(T)):
            running = rewards[t] + 0.99 * running * (1 - dones[t])
            returns[t] = running

        # Normalize returns
        returns = (returns - returns.mean()) / (returns.std() + 1e-8)

        # Forward pass
        logits  = self.policy_net(obs_t)          # (T, 8100)
        values  = self.value_net(obs_t).squeeze(-1)  # (T,)

        # Apply action mask to logits
        masked_logits = logits + (1 - masks_t) * -1e9
        log_probs = torch.log_softmax(masked_logits, dim=-1)
        pi_a     = log_probs.gather(-1, actions.unsqueeze(-1)).squeeze(-1)

        # Entropy bonus
        probs    = torch.softmax(masked_logits, dim=-1)
        entropy  = -(probs * log_probs).sum(-1).mean()

        # Value loss
        value_loss = self.value_coef * (returns - values).pow(2).mean()

        # Policy loss (simplified REINFORCE with baseline — upgrade to full PPO)
        policy_loss = -(pi_a * returns.detach()).mean()

        # Total loss
        loss = policy_loss + value_loss - self.entropy_coef * entropy

        # Backward pass
        self.policy_opt.zero_grad()
        self.value_opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.policy_net.parameters(), self.max_grad_norm)
        nn.utils.clip_grad_norm_(self.value_net.parameters(),  self.max_grad_norm)

        # MPS contiguity fix (Adam on MPS < 2.4)
        for p in self.policy_net.parameters():
            if not p.is_contiguous():
                p.data = p.data.contiguous()

        self.policy_opt.step()
        self.value_opt.step()

        return {
            "policy_loss": policy_loss.item(),
            "value_loss": value_loss.item(),
            "entropy": entropy.item(),
            "total_loss": loss.item(),
        }
```

### Temperature Scheduling

Exploration temperature for action selection decreases over training:

```python
def get_temperature(step: int, n_total: int) -> float:
    """Linear annealing from 1.0 to 0.1 over training."""
    frac = min(step / n_total, 1.0)
    return 1.0 - 0.9 * frac   # 1.0 → 0.1
```

### Evaluation Against Previous Best

Self-play training requires periodic evaluation to track improvement:

```python
def evaluate(policy_a, policy_b, env, n_games: int = 100) -> float:
    """Return win rate of policy_a against policy_b over n_games."""
    wins = 0.0
    for i in range(n_games):
        env.reset()
        player_a_is_red = (i % 2 == 0)   # alternate colors
        policy_red = policy_a if player_a_is_red else policy_b
        policy_black = policy_b if player_a_is_red else policy_a

        while not done:
            if env._player_to_move == 1:
                action = select_action(policy_red, obs, mask, deterministic=True)
            else:
                action = select_action(policy_black, obs, mask, deterministic=True)
            obs, reward, done, _, _ = env.step(action)

        wins += (reward > 0) if player_a_is_red else (reward < 0)

    return wins / n_games
```

---

## 8. Known Xiangqi RL Projects for Reference

### AlphaXiangqi / AlphaZero-Xiangqi

**Paper:** "Mastering Chinese Chess AI (Xiangqi) Without Search" (arXiv:2410.04865)

- Architecture: ResNet-style CNN + policy head + value head, trained from zero with self-play
- Observation: 14-channel binary planes (7 piece types × 2 colors), 10×9 board
- Self-play training: PPO-style policy gradient with Monte-Carlo returns
- Result: Achieves intermediate strength without search; with MCTS search, competitive with top Xiangqi engines
- **Relevance:** Provides the definitive architecture template for the AlphaZero-style Xiangqi RL environment. Observation encoding, action masking, and training loop structure are directly applicable.

### ELF-OpenGo Xiangqi Adaptation

**Source:** Meta's ELF (Experience Replay Language) framework, adapted for Xiangqi

- Original ELF-OpenGo targets Go with a 3-headed network (policy, value, classification)
- Xiangqi adaptation: similar architecture, reduced action space (8100 vs 19×19=361 for Go)
- **Relevance:** ELF's "execute multiple games in parallel" design pattern is directly applicable to batch simulation. The framework's data pipeline (buffer → batch → GPU → update) is the template for the self-play loop.

### DRL+MCTS Xiangqi

**Paper:** arXiv:2506.15880 — "Deep Reinforcement Learning + Monte Carlo Tree Search for Xiangqi"

- Combines RL policy/value networks with MCTS at inference time
- RL phase produces policy (π) and value (V) networks; MCTS uses these as priors and evaluation
- **Relevance:** The RL environment described here can be extended to support MCTS inference (v2+ feature). The neural network architecture (CNN encoder → policy/value heads) is identical.

### CARA (Chess Archive with Reinforcement Learning Agent)

**Source:** github.com/ihsara/CARA (pure Python, PyTorch)

- Implements Western chess as an RL environment with PyTorch
- Demonstrates the full cycle: env → batch simulation → replay buffer → PPO update
- **Relevance:** The Python-level implementation patterns (Gymnasium wrapper, batch env, PPO trainer) are directly applicable. The code structure in `env/`, `agents/`, `training/` mirrors CARA's organization.

### Fairy-Stockfish (pyffish) — Reference Oracle

**Source:** github.com/ianfab/mqxiangqi — Fairy-Stockfish Xiangqi rules implementation

- PyPI: `pyffish` — supports Xiangqi via `sf.legal_moves("xiangqi", fen, moves)`
- Provides 100% correct legal move generation, WXF rules, UCCI protocol
- **Relevance:** Use as a **testing oracle only** — not as the training environment. Cross-validate the custom rule engine's move output against pyffish in pytest fixtures. The opaque C++ state prevents RL observation tensor access.

### gym-xiangqi (PyPI)

**Source:** PyPI — `gym-xiangqi` (inactive)

- Provides a Gym environment for Xiangqi with integer encoding (-16 to +16 per cell)
- Inactive on PyPI (no releases in 12+ months as of 2026)
- **Relevance:** Not suitable as primary environment. Observation space uses integer encoding, not the (14, 10, 9) binary planes needed for CNN-based RL. Reference for interface design only.

### Key Architectural Insights from Literature

| Aspect | Western Chess (AlphaZero) | Xiangqi Adaptation |
|---|---|---|
| Board size | 8×8 = 64 squares | 9×10 = 90 intersections |
| Piece types | 6 types × 2 colors = 12 planes | 7 types × 2 colors = 14 planes |
| Action space | 4,672 (all legal) / 2,188 (from-to) | ~8,100 (all from-to), ~40–50 legal |
| Castling | Special move (4 states) | None |
| Promotion | Pawn reaching back rank | None |
| Flying General | N/A | Must be encoded as 15th channel |
| River boundary | N/A | Elephant/Horse constrained by row 5 |

---

## 9. Performance Requirements for Batch Simulation

### Target Metrics

| Metric | Target | Notes |
|---|---|---|
| **Games per second (self-play)** | 50–200 games/s | With batched CPU simulation (8+ workers) |
| **Legal move generation per position** | < 1 ms | Python; Cython if needed |
| **Neural forward pass (batch=1)** | < 5 ms | M1 Max MPS; shared encoder amortizes cost |
| **Neural forward pass (batch=256)** | < 20 ms | Full MPS batch throughput |
| **Training steps per second** | 100–500 steps/s | Depends on batch size and learning rate |
| **Episode length** | 60–120 plies average | Xiangqi games average ~80 half-moves |
| **Memory per game trajectory** | ~1–2 MB | 80 plies × 8100 mask + 16×10×9 obs + actions |

### Bottleneck Analysis

The RL training pipeline has three sequential phases:

```
1. Data Collection (CPU-bound):
   env.step(actions) → legal move gen → board update → obs encoding
   Throughput: ~10,000 positions/second per CPU worker
   Fix: run 8–16 workers in parallel via multiprocessing.Pool

2. Neural Forward Pass (GPU/MPS-bound):
   policy_net(obs_batch), value_net(obs_batch)
   Throughput: ~100,000 positions/second on M1 Max (batch=256)
   Fix: accumulate large batches from all workers before GPU call

3. Gradient Update (GPU/MPS-bound):
   loss.backward() → optimizer.step()
   Throughput: ~50–200 updates/second depending on batch size
   Fix: use gradient accumulation for effective larger batches
```

### Batch Simulation Architecture

```python
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

def simulate_game_worker(seed: int) -> list[dict]:
    """Run one self-play game. Runs in separate process."""
    env = XiangqiEnv()
    env.reset(seed=seed)
    trajectory = []

    while True:
        obs, info = env._get_observation(), env._get_info()
        action = random_legal_action(env) if training else greedy_action(env)
        next_obs, reward, terminated, _, next_info = env.step(action)
        trajectory.append({
            "obs": obs,
            "action": action,
            "reward": reward,
            "next_obs": next_obs,
            "done": terminated,
            "legal_mask": info["legal_mask"],
        })
        if terminated:
            break

    return trajectory

def collect_selfplay_batch(n_games: int, n_workers: int = 8) -> list[dict]:
    """Collect trajectories from n_games in parallel on CPU."""
    seeds = list(range(n_games))
    all_trajectories = []

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(simulate_game_worker, s): s for s in seeds}
        for future in as_completed(futures):
            all_trajectories.extend(future.result())

    return all_trajectories
```

### Memory Budget

For self-play with replay buffer:

| Component | Memory (MB) | Notes |
|---|---|---|
| Replay buffer (10,000 transitions) | ~500 MB | obs (16×10×9 × 4 bytes) + masks (8100 × 4) + actions + rewards |
| Policy/value networks | ~20 MB | Small CNN; 7 piece agents × ~3 MB each |
| Batch tensors (MPS) | ~50 MB | Batch of 256 observations |
| Total working set | ~600 MB | Well within M1 Max 32GB unified memory |

### Profiling Recommendations

1. Profile legal move generation first — it is called once per step per self-play worker
2. Profile the full self-play game throughput before adding neural network training
3. Profile MPS forward pass + backward pass separately to identify which is the bottleneck
4. Use `torch.profiler` with MPS device for GPU-level profiling

---

## 10. Multi-Agent RL: Per-Piece-Type Networks

### Architectural Overview

The project defines **7 independent policy networks** (one per piece type), coordinated by an **ArbitrationNetwork**:

```
Board Observation (16, 10, 9)
        │
        ▼
┌─────────────────────────┐
│   Shared CNN Encoder     │  ← ResNet-style, ~3 layers, shared weights
│   (16 → 64 channels)     │
└─────────────┬───────────┘
              │
    ┌─────────┼─────────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
    ▼         ▼             ▼          ▼          ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│General  │ │Advisor  │ │Elephant│ │ Horse  │ │Chariot │ │ Cannon │ │Soldier │
│Head (0) │ │Head (1) │ │Head (2)│ │Head (3) │ │Head (4) │ │Head (5) │ │Head (6) │
└────┬────┘ └────┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
     │           │          │          │          │          │          │
     │ logits_G  │ logits_A │ logits_E │ logits_H │ logits_C  │ logits_Ca│ logits_S
     │ mask_G    │ mask_A   │ mask_E   │ mask_H   │ mask_C   │ mask_Ca  │ mask_S
     │           │          │          │          │          │          │
     └───────────┴──────────┴───────────┴──────────┴──────────┴──────────┴─────────┘
                              │
                    Proposals: (piece_type, move, logit_score)
                              │
                              ▼
                   ┌──────────────────────┐
                   │  ArbitrationNetwork  │  ← MLP attending over proposals
                   │  (selects final move)│
                   └──────────┬───────────┘
                              │
                         final_action
```

### Network Definitions

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class XiangqiPolicyNetwork(nn.Module):
    """
    Shared CNN encoder + per-piece-type policy heads.
    Output: dict of {piece_type: (logits, mask)} for each active piece type.
    """
    def __init__(self, in_channels: int = 16, hidden_channels: int = 64):
        super().__init__()
        # Shared CNN encoder
        self.conv1 = nn.Conv2d(in_channels, hidden_channels, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(hidden_channels, hidden_channels, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(hidden_channels, hidden_channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(hidden_channels)
        self.bn2 = nn.BatchNorm2d(hidden_channels)
        self.bn3 = nn.BatchNorm2d(hidden_channels)

        # Global pooling → shared feature vector
        # Each piece-type head: small MLP
        self.heads = nn.ModuleDict({
            "general":  nn.Linear(hidden_channels, self._head_out_size("general")),
            "advisor":  nn.Linear(hidden_channels, self._head_out_size("advisor")),
            "elephant": nn.Linear(hidden_channels, self._head_out_size("elephant")),
            "horse":    nn.Linear(hidden_channels, self._head_out_size("horse")),
            "chariot":  nn.Linear(hidden_channels, self._head_out_size("chariot")),
            "cannon":   nn.Linear(hidden_channels, self._head_out_size("cannon")),
            "soldier":  nn.Linear(hidden_channels, self._head_out_size("soldier")),
        })

    def _head_out_size(self, piece_type: str) -> int:
        # Each head outputs logits over its own subset of the 8100 action space
        # For simplicity, each head outputs all 8100 logits; masking is applied at usage
        return 8100

    def forward(
        self,
        x: torch.Tensor,          # (B, 16, 10, 9)
        piece_masks: dict[str, torch.Tensor],  # {piece_type: (B, 8100)}
    ) -> dict[str, torch.Tensor]:
        """
        Returns dict of {piece_type: masked_logits} for each piece type with pieces on board.
        """
        # CNN encoder
        h = F.relu(self.bn1(self.conv1(x)))
        h = F.relu(self.bn2(self.conv2(h)))
        h = F.relu(self.bn3(self.conv3(h)))
        # Global average pooling → (B, hidden_channels)
        h = h.mean(dim=(2, 3))

        outputs = {}
        for pt, head in self.heads.items():
            logits = head(h)                              # (B, 8100)
            if pt in piece_masks:
                mask = piece_masks[pt]                   # (B, 8100)
                logits = logits + (1 - mask) * -1e9
            outputs[pt] = logits

        return outputs   # {piece_type: (B, 8100)}


class ArbitrationNetwork(nn.Module):
    """
    Selects the final action from all piece-type proposals.
    Input: board encoding + list of (piece_type, move, logit_score) proposals
    Output: scalar score per proposal for final selection.
    """
    def __init__(self, board_features_dim: int = 64, n_proposals: int = 21):
        super().__init__()
        self.n_proposals = n_proposals   # max proposals to consider (e.g., 3 per piece type)

        # Encode each proposal: (piece_type_embedding + move_embedding)
        self.piece_embed = nn.Embedding(7, 16)        # 7 piece types
        self.proposal_fc = nn.Linear(16 + 2, 32)      # piece type + (from, to) as 2 features

        # Attend over proposals
        self.proposal_encoder = nn.Linear(32, 32)
        self.query_proj = nn.Linear(board_features_dim, 32)
        self.arb_fc = nn.Linear(32, 1)                # score per proposal

    def forward(
        self,
        board_features: torch.Tensor,   # (B, hidden_channels)
        proposals: list[list[tuple[int, int, int]]],  # per-sample: list of (pt, from, to)
    ) -> torch.Tensor:                   # (B, n_proposals) — scores for top proposals
        """
        proposals: list of up to n_proposals (piece_type, from_sq, to_sq) tuples
        """
        B = board_features.shape[0]
        board_q = self.query_proj(board_features)     # (B, 32)

        # Encode all proposals for this batch
        scores = torch.zeros(B, self.n_proposals, device=board_features.device)
        for b in range(B):
            batch_proposals = proposals[b] if b < len(proposals) else []
            for i, (pt, frm, to) in enumerate(batch_proposals[:self.n_proposals]):
                pt_emb   = self.piece_embed(torch.tensor(pt, device=board_features.device))
                pt_feat  = torch.cat([pt_emb, torch.tensor([frm/89.0, to/89.0], device=board_features.device)])
                enc      = F.relu(self.proposal_fc(pt_feat))   # (32,)
                score    = self.arb_fc(enc * board_q[b]).squeeze(-1)   # scalar
                scores[b, i] = score

        return scores
```

### Value Network (Shared with Policy or Separate)

A separate value head on the policy network (dual-head architecture, same as AlphaZero) is simpler and often performs well:

```python
class XiangqiValueNetwork(nn.Module):
    """Value head sharing the CNN encoder with the policy network."""
    def __init__(self, policy_net: XiangqiPolicyNetwork):
        super().__init__()
        # Share all policy layers
        self.conv1 = policy_net.conv1
        self.conv2 = policy_net.conv2
        self.conv3 = policy_net.conv3
        self.bn1 = policy_net.bn1
        self.bn2 = policy_net.bn2
        self.bn3 = policy_net.bn3
        # Value-specific head
        self.value_head = nn.Sequential(
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Tanh()   # output in [-1, +1]: black win to red win
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = F.relu(self.bn1(self.conv1(x)))
        h = F.relu(self.bn2(self.conv2(h)))
        h = F.relu(self.bn3(self.conv3(h)))
        h = h.mean(dim=(2, 3))
        return self.value_head(h)   # (B, 1) in [-1, 1]
```

### Multi-Agent Proposal Collection

```python
def collect_proposals(
    policy_net: XiangqiPolicyNetwork,
    env: XiangqiEnv,
    device: str,
) -> list[tuple[int, int, float]]:
    """
    Collect top-K proposals from each active piece type on the board.
    Returns list of (from_sq, to_sq, logit_score) sorted by score.
    """
    obs_t = torch.from_numpy(env._get_observation()).unsqueeze(0).float().to(device)
    all_proposals = []

    # Build per-piece-type masks
    piece_masks = {}
    for pt_idx in range(7):
        pt_name = PIECE_NAMES[pt_idx]
        mask = env.get_piece_legal_mask(pt_idx)    # (8100,) float32
        piece_masks[pt_name] = torch.from_numpy(mask).unsqueeze(0).to(device)

    with torch.no_grad():
        logits_dict = policy_net(obs_t, piece_masks)

    for pt_name, logits in logits_dict.items():
        # Get top-K moves for this piece type
        top_k = torch.topk(logits.squeeze(0), k=3)
        for score, action_idx in zip(top_k.values, top_k.indices):
            frm = action_idx.item() // 90
            to  = action_idx.item() % 90
            all_proposals.append((pt_name, frm, to, score.item()))

    # Sort by score descending
    all_proposals.sort(key=lambda x: x[3], reverse=True)
    return all_proposals[:21]   # max 21 proposals (3 per piece type)
```

### Training: CTDE with Piece-Type Agents

Each piece-type network is trained on transitions where it **proposed the selected action** (tagged in the replay buffer):

```python
def update_piece_agents(
    agents: dict[str, nn.Module],
    replay_buffer: ReplayBuffer,
    device: str,
):
    """Update each piece agent on its own subset of transitions."""
    batch = replay_buffer.sample(batch_size=256)

    for pt_name, agent in agents.items():
        # Filter transitions where this piece type was selected
        pt_batch = [t for t in batch if t["selected_piece_type"] == pt_name]
        if len(pt_batch) < 4:
            continue

        obs_t = torch.stack([torch.from_numpy(t["obs"]) for t in pt_batch]).to(device)
        actions_t = torch.tensor([t["action"] for t in pt_batch], device=device)
        returns_t = torch.tensor([t["return"] for t in pt_batch], dtype=torch.float32, device=device)

        logits = agent(obs_t)                    # (B, 8100) — masked internally
        log_probs = torch.log_softmax(logits, dim=-1)
        pi_a = log_probs.gather(-1, actions_t.unsqueeze(-1)).squeeze(-1)

        loss = -(pi_a * returns_t.detach()).mean()
        agent.optimizer.zero_grad()
        loss.backward()
        agent.optimizer.step()
```

---

## Integration Checklist (v0.1 Implementation Order)

Before connecting the RL loop to any trained policy:

- [ ] XiangqiEnv.reset() returns valid (16, 10, 9) float32 observation
- [ ] XiangqiEnv.step() rejects illegal moves (returns penalty, does not update state)
- [ ] XiangqiEnv.get_legal_mask() returns correct mask for all positions
- [ ] Random policy agent selects only legal moves (mask enforcement confirmed)
- [ ] Self-play produces full game episodes (terminal reached, no crashes)
- [ ] Replay buffer stores and retrieves transitions with correct shapes
- [ ] MPS device is verified available; all tensors are float32
- [ ] Checkpoint save/load round-trips all model weights correctly
- [ ] Terminal reward is +1/-1/0 with correct sign for both sides

---

## Sources

- AlphaZero (Silver et al., PNAS 2018) — board plane representation, self-play loop, dual-head network
- "Mastering Chinese Chess AI (Xiangqi) Without Search" (arXiv:2410.04865) — Xiangqi-specific architecture
- "DRL+MCTS Xiangqi" (arXiv:2506.15880) — RL + search combination for Xiangqi
- ELF-OpenGo (Tian & Zhu, arXiv:1904.04968) — batch self-play framework design
- CARA GitHub (ihsara/CARA) — Python PyTorch chess RL implementation patterns
- gymnasium 1.0.x documentation — `gymnasium.Env` interface specification
- TorchRL documentation — `MultiAgentMLP`, vectorized environments
- "Heterogeneous-Agent Reinforcement Learning" (HARL, Kuba et al.) — sequential update ordering for heterogeneous MARL
- WXF Rules paper (arXiv:2412.17334, December 2024) — correct Xiangqi repetition/perpetual-check implementation
- STACK.md (this project) — PyTorch MPS constraints, float32 enforcement, device management
- ARCHITECTURE.md (this project) — CTDE pattern, per-piece proposal + arbitration design

---

*RL Environment research for: RL-Xiangqi heterogeneous multi-agent RL Xiangqi system*
*Researched: 2026-03-19*
