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

### Xiangqi Rules Engine

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Custom Python rules engine | — | Legal move generation, check detection, win condition | No mature, maintained pure-Python Xiangqi library exists comparable to python-chess for standard chess. `cotuong.py` exists but is niche and unmaintained. Write your own: ~400–600 lines covering piece movement rules, check/checkmate/stalemate, palace constraint, flying generals rule. Gives full control over state representation needed for RL observation tensors. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tensorboard | 2.x | Training visualization: loss curves, reward curves, Elo-equivalent metrics | Embed in training loop via `SummaryWriter`. Renders in browser; no notebook required. Use for all per-step and per-episode scalar logging. |
| matplotlib | 3.9.x | Static plots, episode reward distributions, policy entropy charts | Use for post-hoc analysis and in-app training visualization widgets embedded in PyQt6 via `FigureCanvasQTAgg`. |
| PyQtGraph | 0.13.x | Live in-app metric plots (loss curves, win rate) during training | PyQtGraph is faster than matplotlib for real-time PyQt6 widget updates. Use for the live training visualization panel inside the desktop app. NumPy 2 compatible as of 0.13.5. |
| gymnasium | 1.0.x | Standard `Env` interface wrapper around Xiangqi rules engine | Wrapping the game in a `gymnasium.Env` gives compatibility with standard RL tooling and makes the environment testable independently. Required if using TorchRL collectors. |
| numpy | 2.4.x | Board state arrays, action masking, reward computation | Use `uint8` arrays for board state (avoids float64 MPS errors downstream). |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Python package management and virtual environments | Faster than pip, handles Apple Silicon ARM64 package resolution reliably. `uv venv --python 3.12 && uv pip install ...` |
| pytest | Unit testing rules engine and RL components | Test move generation exhaustively before training — bugs in the rules engine cause silent training divergence. |
| black + ruff | Code formatting and linting | Ruff replaces flake8/isort. Keep AI/RL code readable; training loops get complex fast. |

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

# Dev dependencies
uv pip install pytest black ruff

# MPS fallback (add to shell profile or .env)
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Custom PPO | Stable-Baselines3 | Never on this project — SB3 has confirmed float64/MPS incompatibility. Would require forking SB3 internals. |
| Custom PPO | RLlib (Ray) | If the project scales to distributed training or self-play tournaments needing many parallel workers. Overkill for single-machine human-vs-AI with online learning. |
| Custom rules engine | cotuong.py / xiangqigame | If you need a fast, battle-tested engine immediately. xiangqigame uses C++/Pybind11 and is fast but couples you to its state representation, making RL observation tensors awkward. |
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

**For board state representation:**
- Use a flat integer array of shape `(90,)` (10×9 board, one int per cell encoding piece type + color) as the canonical state
- Expand to `(14, 10, 9)` channel tensor for network input: one binary channel per piece type per color (7 types × 2 colors)
- This representation is MPS-friendly (float32 after cast, no float64 needed)

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
| macOS requirement | MPS backend | macOS 12.3 minimum. M1 Max (macOS 15.x as of 2026) is fully supported. |

---

## Sources

- PyTorch MPS status and limitations — WebSearch, multiple sources corroborate (HIGH confidence on float64/BFloat16 restrictions, MEDIUM on specific op coverage)
- PyTorch 2.10.0 release date — WebSearch, pytorch.org release history (HIGH confidence)
- PyQt6 6.10.2 — PyPI/riverbankcomputing.com (HIGH confidence)
- TorchRL `MultiAgentMLP(share_params=False)` heterogeneous support — docs.pytorch.org/rl (HIGH confidence)
- Stable-Baselines3 MPS incompatibility — multiple community reports + SB3 team acknowledgment (HIGH confidence)
- NumPy 2.x / PyTorch compatibility matrix — PyPI + community reports (HIGH confidence)
- Xiangqi Python library landscape — GitHub search (MEDIUM confidence; no library is clearly dominant/maintained)
- PPO for board game online learning — multiple tutorials and community examples (HIGH confidence on algorithm suitability)
- PyQt6 `QGraphicsScene` for board rendering pattern — official Qt docs + StackOverflow corroboration (HIGH confidence)

---

*Stack research for: Heterogeneous multi-agent RL Xiangqi system on Apple Silicon M1 Max*
*Researched: 2026-03-19*
