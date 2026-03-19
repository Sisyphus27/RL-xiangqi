# Stack Research

**Domain:** Heterogeneous multi-agent RL board game (Xiangqi / Chinese Chess) with online learning on Apple Silicon
**Researched:** 2026-03-19
**Confidence:** MEDIUM-HIGH (core choices verified via multiple sources; some library-specific MPS behavior is still experimental)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12 | Runtime | Officially recommended for PyTorch MPS on Apple Silicon. ARM64 native build required — Rosetta-emulated x86 Python causes MPS to silently report unavailable. |
| PyTorch | 2.10.0 | Deep learning backend + MPS GPU | Latest stable (Jan 2026). MPS support for all standard NN ops (matmul, conv, activations, softmax). Unified memory on M1 Max eliminates CPU-GPU copies. Set `PYTORCH_ENABLE_MPS_FALLBACK=1` for ops not yet Metal-kernelized. |
| PyQt6 | 6.10.2 | Desktop UI: board rendering, drag-drop interaction | Latest stable (Jan 2026). `QGraphicsScene` + `QGraphicsView` + `QGraphicsPixmapItem` is the correct pattern for interactive board pieces. Superior to Tkinter for game UIs; pure Qt bindings give full access to Qt6 widgets. |
| NumPy | 2.4.x | Array ops, board state representations | PyTorch 2.10 is NumPy 2.x-compatible. Do NOT pin to NumPy 1.x unless forced by another dependency. |

### RL Algorithm Layer

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Custom PPO implementation | — | On-policy online learning | **Do not use Stable-Baselines3** — it has confirmed MPS incompatibility (float64 errors, no auto-detection of MPS device). Build a thin PPO from scratch with PyTorch: policy network, value network, clipped surrogate loss, GAE advantage estimation. ~300 lines, full MPS control. |
| TorchRL (optional scaffold) | 0.7.x (matches PyTorch 2.10) | Provides `MultiAgentMLP`, replay buffers, rollout collectors | TorchRL's `MultiAgentMLP(share_params=False)` directly maps to the heterogeneous-agent requirement (each piece type gets independent parameters). Use for structural scaffolding; keep custom training loop for MPS control. |

### Xiangqi Rule Engine (v0.1 Milestone)

**Verdict: Write a custom pure-Python engine. Do not adopt an external library as the primary rule source.**

No mature, well-maintained pure-Python Xiangqi library comparable to `python-chess` for standard chess exists on PyPI as of March 2026. The alternatives are either abandoned, have wrong abstraction boundaries for RL (C-backed opaque state), or cover Western chess only. The rule engine for this project is ~500–700 lines of well-tested Python — not a large investment, and full ownership is required for RL observation tensor generation anyway.

| Component | Approach | Notes |
|-----------|----------|-------|
| Board state | `np.ndarray` shape `(10, 9)`, `dtype=np.int8` | Integer encoding: 0=empty, 1–7=red pieces, -1 to -7=black pieces (per piece type constants). 10 rows (rank 0=black back rank, rank 9=red back rank), 9 columns. |
| Move history | Python `list` of `(from_pos, to_pos, captured_piece)` tuples | Enables O(1) undo for check validation and perpetual-check detection. Do NOT copy the full board per move — store deltas. |
| Legal move generation | Precomputed attack tables + constraint validation | Per-piece lookup tables for static movers (Advisor, Elephant, Soldier), ray tracing for sliders (Chariot), jump+block for Horse and Cannon. Check validation via make-move / in-check / unmove. |
| Check detection | Scan from General position outward using per-piece attack patterns | Scan for each threat type independently: Chariot/Cannon rays, Horse L-moves, flying General (same-file scan). O(1) with precomputed tables. |
| Win/draw detection | After legal move generation returns empty set | Checkmate = no legal moves AND in check; Stalemate = no legal moves AND not in check. Both lose for the side with no moves under standard Xiangqi rules. |
| Repetition / perpetual | Move history + position hash cache | Track FEN-equivalent hashes in a `collections.Counter`. Three-fold repetition with perpetual check = loss for checking side. Full WXF perpetual-chase rules are complex — implement basic perpetual check first, defer full chase detection to v2. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tensorboard | 2.x | Training visualization: loss curves, reward curves, Elo-equivalent metrics | Embed in training loop via `SummaryWriter`. Renders in browser; no notebook required. Use for all per-step and per-episode scalar logging. |
| matplotlib | 3.9.x | Static plots, episode reward distributions, policy entropy charts | Use for post-hoc analysis and in-app training visualization widgets embedded in PyQt6 via `FigureCanvasQTAgg`. |
| PyQtGraph | 0.13.x | Live in-app metric plots (loss curves, win rate) during training | PyQtGraph is faster than matplotlib for real-time PyQt6 widget updates. Use for the live training visualization panel inside the desktop app. NumPy 2 compatible as of 0.13.5. |
| gymnasium | 1.0.x | Standard `Env` interface wrapper around Xiangqi rules engine | Wrapping the game in a `gymnasium.Env` gives compatibility with standard RL tooling and makes the environment testable independently. Required if using TorchRL collectors. |
| numpy | 2.4.x | Board state arrays, action masking, reward computation | Use `uint8` arrays for board state (avoids float64 MPS errors downstream). |
| pyffish | 0.0.88 | **Reference oracle for rule engine testing only** — NOT for training env | C++ Fairy-Stockfish Python binding. Supports Xiangqi natively (`sf.legal_moves("xiangqi", fen, moves)`). Use it in pytest fixtures to cross-validate your custom engine's legal move output. Do NOT use as the training environment — its opaque state representation breaks RL observation generation. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Python package management and virtual environments | Faster than pip, handles Apple Silicon ARM64 package resolution reliably. `uv venv --python 3.12 && uv pip install ...` |
| pytest | Unit testing rules engine and RL components | Test move generation exhaustively before training — bugs in the rules engine cause silent training divergence. Cross-validate against pyffish for all 7 piece types from all positions. |
| black + ruff | Code formatting and linting | Ruff replaces flake8/isort. Keep AI/RL code readable; training loops get complex fast. |

---

## Xiangqi Rule Engine: Piece Implementation Guide

This section documents Xiangqi-specific rules that are easy to get wrong. These are not obvious from Western chess knowledge.

### Board Geometry

```
Rows:  0 = black's back rank (top of board)
       9 = red's back rank (bottom of board)
Cols:  0–8 (a–i in coordinate notation)

River: between rows 4 and 5
Black palace: rows 0–2, cols 3–5
Red palace:   rows 7–9, cols 3–5
```

### Piece Movement Rules (all 7 types)

| Piece | Red / Black | Movement | Special Constraints |
|-------|-------------|----------|---------------------|
| 帅/将 General | King | 1 step orthogonal | Must stay inside own palace (3×3). Flying General: cannot leave file open to opposing General with no piece between. |
| 仕/士 Advisor | Guard | 1 step diagonal | Must stay inside own palace. Only 4 valid squares + center. |
| 相/象 Elephant | Bishop | 2 steps diagonal ("elephant leg") | Cannot cross river. Blocked if the intervening diagonal square ("elephant eye") is occupied. |
| 马 Horse | Knight | 1 orthogonal + 1 diagonal | Blocked if the orthogonal step square is occupied ("hobbled horse"). Order matters: orthogonal first, then diagonal. |
| 车 Chariot | Rook | Any number of steps orthogonal | Blocked by intervening pieces. Standard sliding move. |
| 炮 Cannon | Cannon | Moves like Chariot; captures by jumping exactly one piece | For quiet moves: no pieces between source and target. For captures: exactly one piece (the "screen") between source and target. Two different move types for the same piece. |
| 兵/卒 Soldier | Pawn | 1 step forward before crossing river; 1 forward or 1 sideways after crossing river | Cannot move backward ever. Promotion-free. |

### Flying General Rule (Critical)

After every move, verify that the two Generals do not face each other on the same file with no pieces between them. This is an illegal position. It applies to BOTH sides — a move that exposes your own General to the flying General check is illegal.

```python
def flying_general_check(board, red_gen_pos, black_gen_pos):
    if red_gen_pos[1] != black_gen_pos[1]:
        return False  # different files, no flying general threat
    col = red_gen_pos[1]
    min_row, max_row = min(red_gen_pos[0], black_gen_pos[0]), max(red_gen_pos[0], black_gen_pos[0])
    for row in range(min_row + 1, max_row):
        if board[row, col] != 0:
            return False  # piece blocking line of sight
    return True  # generals face each other — illegal
```

### Check Detection Algorithm

To check whether the side-to-move's General is in check:

1. **Chariot threat**: scan all 4 orthogonal rays from General; any Chariot or enemy General on first unobstructed square is a threat.
2. **Cannon threat**: scan all 4 orthogonal rays; skip first piece encountered (the screen); if second piece encountered is enemy Cannon, it's a threat.
3. **Horse threat**: for each of 8 L-move destinations, verify the hobbling square is empty, and the destination holds an enemy Horse.
4. **Soldier/Advisor/Elephant**: check the specific squares each can reach from the General position (very limited set — precompute as static lookup tables indexed by position and color).
5. **Flying General**: check as above.

### Performance Target

The <100ms per move requirement (from PROJECT.md) is trivially achievable with pure Python + NumPy for a single-step legal move generation. A typical position has 30–50 legal moves. Full legal move generation (all pieces, all moves, check-filtering) in Python takes 0.1–2ms per position. No Cython or C extension is needed for v0.1.

If self-play warm-up generates positions at high throughput (SP-01: 200 games), batching calls to the rule engine and keeping board state in NumPy arrays (not Python dicts or objects) will keep it fast enough. Profile before optimizing.

---

## Installation

```bash
# Create ARM64 native Python 3.12 venv (CRITICAL: must be native ARM64, not Rosetta)
uv venv .venv --python 3.12
source .venv/bin/activate

# Verify ARM64 (must print arm64, not x86_64)
python -c "import platform; print(platform.machine())"

# Core stack
uv pip install torch==2.10.0 torchvision torchaudio

# Verify MPS is available
python -c "import torch; print(torch.backends.mps.is_available())"

# UI and visualization
uv pip install PyQt6==6.10.2 pyqtgraph==0.13.7 matplotlib tensorboard

# RL tooling (optional)
uv pip install torchrl gymnasium

# Utilities
uv pip install numpy

# Rule engine testing oracle (dev only)
uv pip install pyffish

# Dev dependencies
uv pip install pytest black ruff

# MPS fallback (add to shell profile or .env)
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Custom rules engine | **pyffish** (Fairy-Stockfish bindings) | As a testing oracle only. pyffish 0.0.88 supports Xiangqi via `sf.legal_moves("xiangqi", fen, moves)` — use in pytest fixtures to cross-validate custom engine output. Never use as training env: opaque C++ state prevents RL observation tensor access. |
| Custom rules engine | **cotuong.py** (github.com/Ihsara/cotuong.py) | If you want a reference implementation to read. Covers move generation, check/checkmate/draw detection via `GameState` class. Targets Python 3.7, appears unmaintained, no PyPI package. Read the code as a design reference, do not depend on it. |
| Custom rules engine | **gym-xiangqi** (PyPI) | If you want an OpenAI Gym wrapper and don't need control over internals. Observation space uses integer encoding -16 to +16 per cell, which differs from the (14, 10, 9) channel tensor needed for CNN-based RL. Marked inactive on PyPI (no releases in 12+ months). |
| Custom PPO | Stable-Baselines3 | Never on this project — SB3 has confirmed float64/MPS incompatibility. Would require forking SB3 internals. |
| Custom PPO | RLlib (Ray) | If the project scales to distributed training or self-play tournaments needing many parallel workers. Overkill for single-machine human-vs-AI with online learning. |
| Custom rules engine | Fairy-Stockfish via UCCI | For evaluating AI strength via ELO benchmarking, not for training environment. Fairy-Stockfish is a useful strength reference but not suitable as an RL training environment. |
| PyQt6 | PySide6 | PySide6 is Qt's official Python binding (LGPL, vs PyQt6's GPL). API is near-identical. Use PySide6 if GPL licensing is a concern for commercial distribution. |
| PyQt6 | Tkinter | Tkinter cannot handle 90fps board redraw, SVG piece rendering, or embedded matplotlib/PyQtGraph plots cleanly. Inappropriate for this use case. |
| TorchRL scaffold | Pure custom MARL | Pure custom is fine if TorchRL's `MultiAgentMLP` and collector abstractions are not wanted. TorchRL adds dependencies but reduces boilerplate for heterogeneous multi-agent bookkeeping. |
| PyQtGraph (live plots) | Matplotlib in PyQt6 | Matplotlib via `FigureCanvasQTAgg` is simpler but slower for live updates. Use matplotlib for static/saved charts, PyQtGraph for in-app live training metrics. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Stable-Baselines3 | MPS incompatible: float64 tensors not supported by Metal; MPS device not auto-detected; team confirmed no full MPS support | Custom PPO implementation in plain PyTorch |
| MLX (Apple's framework) | 2–3x faster for LLM inference but NOT PyTorch — would require rewriting all RL logic, losing the PyTorch ecosystem (TorchRL, autograd, standard PPO implementations) | PyTorch 2.10 with MPS backend |
| torch.compile on MPS | Mature compiler stack (Triton) doesn't target Metal. Complex fusions fall back to CPU or run as unfused Metal kernels. Performance often worse than eager mode on MPS. | Eager mode with `PYTORCH_ENABLE_MPS_FALLBACK=1` |
| float64 tensors anywhere in RL pipeline | Metal/MPS framework does not support float64 at all — will crash or silently fall to CPU. RL algorithms must use float32 throughout. | Explicitly use `dtype=torch.float32` on all tensor creation; set `torch.set_default_dtype(torch.float32)` at startup |
| BFloat16 on MPS | Not supported by Metal API (unlike NVIDIA GPUs where it's native). Will error or silently misbehave. | float32 only |
| Python x86 (Rosetta-emulated) | MPS reports as unavailable under Rosetta; training falls back to CPU with no warning. Common trap on M1 Macs. | ARM64 native Python 3.12 via uv or conda-miniforge |
| CUDA-specific code paths | No CUDA on M1 Max. Any `torch.cuda.*` call will fail or return False. Use `device = "mps" if torch.backends.mps.is_available() else "cpu"`. | MPS device string with CPU fallback |
| NumPy < 2.0 with PyTorch 2.10 | Binary incompatibility: PyTorch 2.3.1+ requires NumPy 2.x. Mixing causes `RuntimeError: compiled using NumPy 1.x`. | NumPy 2.4.x |
| Bitboard representation for Xiangqi rule engine | Xiangqi board is 10×9 = 90 squares; does not fit in a single 64-bit integer. Two-integer bitboard schemes are complex to implement and maintain. Benchmarks show mailbox arrays are competitive with bitboards for this board size, and the mailbox representation maps directly to RL tensors. | `np.ndarray` shape `(10, 9)` mailbox representation |
| Full WXF perpetual-chase detection in v0.1 | The complete WXF repetition rules (perpetual check + perpetual chase distinction) are notoriously complex — even major commercial apps implement them incorrectly. A Dec 2024 academic paper introduced the first correct implementation for all 110 WXF test cases. This complexity is out of scope for v0.1. | Implement basic three-fold repetition as draw, perpetual check as loss. Defer full WXF chase rules to v2. |
| cotuong.py as a dependency | Unmaintained (targets Python 3.7), no PyPI package, no recent commits. | Read as reference; write your own. |
| gym-xiangqi as primary environment | Marked inactive on PyPI, observation space encoding (-16 to +16 integer per cell) is suboptimal for CNN feature extraction, does not produce the (14, 10, 9) channel tensor format needed for the agent architecture. | Custom `gymnasium.Env` wrapper around your own rule engine. |

---

## Stack Patterns by Variant

**For the heterogeneous multi-agent architecture (each piece type = independent agent):**
- Use `MultiAgentMLP(share_params=False)` from TorchRL, OR manually instantiate one `nn.Module` per piece type (7 types: General, Advisor, Elephant, Horse, Chariot, Cannon, Soldier)
- Each piece-type network outputs action proposals (logits over legal moves for that piece type)
- A separate arbiter network (or value-weighted max) selects the final action from all proposals
- Keep each network small: 3–4 layer MLP with 128–256 hidden units — sufficient for a 10×9 board state

**For online learning (update during human gameplay):**
- Use a lightweight per-step policy gradient update (REINFORCE with baseline) during the game for immediate responsiveness
- Use full PPO update (mini-batch gradient steps over the completed episode) at game-end for stable learning
- Buffer episode trajectory in CPU RAM (not on MPS device) to avoid MPS memory pressure during play

**For board state representation (rule engine → RL pipeline):**
- Canonical state: `np.ndarray` shape `(10, 9)`, `dtype=np.int8`. Integer per cell: 0=empty, positive=red piece by type ID, negative=black piece by type ID.
- RL observation tensor: expand to `(14, 10, 9)` float32: one binary channel per piece type per color (7 types × 2 colors). This is the standard AlphaZero-style feature plane format.
- Conversion: `(board == piece_id).astype(np.float32)` for each of 14 channels. Cast to `torch.tensor` for MPS.
- This representation is MPS-friendly (float32 after cast, no float64 needed).

**For move representation in RL action space:**
- Action = `(from_row, from_col, to_row, to_col)` tuple, or equivalently flat index `from_pos * 90 + to_pos` (max 90×90 = 8100 possible actions, most illegal)
- Use action masking: compute legal moves as a boolean mask over the action space; apply before softmax in policy network
- Legal move count per position: typically 30–50. Masking keeps the action space tractable.

**If MPS fallback causes training slowdown:**
- Profile with `PYTORCH_ENABLE_MPS_FALLBACK=1` and `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0`
- For ops hitting CPU fallback frequently, consider reimplementing those ops to stay on-device (e.g., replace `torch.multinomial` if it falls back with custom categorical sampling)

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| PyTorch 2.10.0 | NumPy 2.4.x | PyTorch >= 2.3.1 required for NumPy 2.x. Earlier PyTorch needs `numpy<2`. |
| PyTorch 2.10.0 | Python 3.12 | Officially supported. Requires ARM64 native Python on Apple Silicon. |
| PyQt6 6.10.2 | Python >= 3.9 | No direct NumPy dependency. Compatible with Python 3.12. |
| PyQtGraph 0.13.x | NumPy 2.x | NumPy 2 compatibility patches merged in 0.13.5+. |
| TorchRL 0.7.x | PyTorch 2.10.0 | TorchRL versions track PyTorch minor releases. Verify with `pip install torchrl` — it pins to matching PyTorch version. |
| gymnasium 1.0.x | Python 3.12, NumPy 2.x | Farama Foundation's Gymnasium 1.0 dropped legacy Gym compatibility. Use `gymnasium` not `gym`. |
| pyffish 0.0.88 | Python 3.11–3.13, macOS/Linux/Windows | Pre-built wheels on PyPI. No Fairy-Stockfish installation required — engine bundled in wheel. |
| macOS requirement | MPS backend | macOS 12.3 minimum. M1 Max (macOS 15.x as of 2026) is fully supported. |

---

## Sources

- Xiangqi board geometry, piece rules, flying general rule — Chess Programming Wiki (chessprogramming.org/Chinese_Chess_Board_Representation) — MEDIUM confidence (domain authoritative but site was not fetchable; content verified via web search summaries)
- pyffish 0.0.88 Xiangqi support, API functions — PyPI + Fairy-Stockfish GitHub + pychess.org production usage — HIGH confidence
- WXF perpetual check/chase complexity and Dec 2024 academic paper — arxiv.org/html/2412.17334v1 (Daniel Tan, UC Riverside) — MEDIUM confidence (paper exists, content verified via web search summaries)
- gym-xiangqi observation space and inactive status — PyPI (inactive label) and GitHub — MEDIUM confidence
- Bitboard vs mailbox performance parity for Xiangqi — community reports, TalkChess forum discussions — LOW-MEDIUM confidence (empirical, hardware-dependent)
- Mailbox array → RL tensor mapping approach — AlphaZero paper, community Xiangqi RL implementations — HIGH confidence (widely established pattern)
- PyTorch MPS status and limitations — WebSearch, multiple sources corroborate — HIGH confidence on float64/BFloat16 restrictions
- PyTorch 2.10.0 release date — pytorch.org release history — HIGH confidence
- PyQt6 6.10.2 — PyPI/riverbankcomputing.com — HIGH confidence
- TorchRL `MultiAgentMLP(share_params=False)` heterogeneous support — docs.pytorch.org/rl — HIGH confidence
- Stable-Baselines3 MPS incompatibility — multiple community reports + SB3 team acknowledgment — HIGH confidence
- NumPy 2.x / PyTorch compatibility matrix — PyPI + community reports — HIGH confidence
- cotuong.py Python 3.7 requirement, unmaintained status — GitHub (Ihsara/cotuong.py) — MEDIUM confidence

---

*Stack research for: Heterogeneous multi-agent RL Xiangqi system on Apple Silicon M1 Max*
*Updated: 2026-03-19 — v0.1 rule engine detail pass added*
