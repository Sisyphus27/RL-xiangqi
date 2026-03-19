# Architecture Research

**Domain:** Heterogeneous Multi-Agent RL — Xiangqi (Chinese Chess)
**Researched:** 2026-03-19
**Confidence:** MEDIUM (proposal+arbitration pattern is novel; CTDE and piece-level decomposition are verified patterns)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         UI Layer (PyQt6)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  BoardWidget  │  │ TrainingPanel│  │  GameControlWidget       │   │
│  │ (QGraphicsView│  │ (loss/elo)   │  │  (new game, save, load)  │   │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘   │
│         │                 │                        │                 │
│         └─────────────────┴───────────┬────────────┘                 │
│                                       │ signals/slots                │
│                                       ▼                              │
│                              GameController (QThread)                │
└───────────────────────────────────────┬────────────────────────────-─┘
                                        │ Python objects / queues
┌───────────────────────────────────────▼──────────────────────────────┐
│                         Game Engine Layer                             │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                     XiangqiEnv                               │    │
│  │  board state · legal move generation · rule enforcement      │    │
│  │  reward shaping · terminal detection · history encoding      │    │
│  └──────────────────────────────┬───────────────────────────────┘    │
└──────────────────────────────────┼───────────────────────────────────┘
                                   │ observations / actions
┌──────────────────────────────────▼───────────────────────────────────┐
│                      Agent Layer (CTDE)                               │
│                                                                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │  Jiang  │ │  Shi    │ │  Xiang  │ │  Ju     │ │  Ma     │        │
│  │  Agent  │ │  Agent  │ │  Agent  │ │  Agent  │ │  Agent  │        │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘        │
│       │           │           │            │           │             │
│  ┌────┴───────────┴───────────┴────────────┴───────────┴──────────┐  │
│  │  (also Pao Agent, Zu Agent — 7 piece types total)              │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                              │ candidate proposals                    │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                    Arbitration Network                        │    │
│  │  receives candidate (piece_type, move, score) tuples         │    │
│  │  outputs final action using global board state               │    │
│  └──────────────────────────────┬───────────────────────────────┘    │
└──────────────────────────────────┼───────────────────────────────────┘
                                   │ selected action
┌──────────────────────────────────▼───────────────────────────────────┐
│                      Learning Layer                                   │
│  ┌────────────────────────┐  ┌────────────────────────────────────┐  │
│  │  Per-Agent Replay      │  │  Centralized Critic (value net)    │  │
│  │  Buffers + Optimizers  │  │  shared global state input         │  │
│  └────────────────────────┘  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  TrainingCoordinator                                           │  │
│  │  per-step lightweight update + end-of-game deep update        │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| BoardWidget | Render board, handle drag/drop, display legal move hints | PyQt6 QGraphicsView + QGraphicsScene |
| TrainingPanel | Show loss curves, Elo/win-rate over time | pyqtgraph or matplotlib embedded in QWidget |
| GameController | Bridge UI and engine; runs AI move computation off the main thread | QThread + pyqtSignal/pyqtSlot |
| XiangqiEnv | Canonical game state; legal move generation; reward computation; step/reset API | Python class with numpy board array; python-chess-like move representation |
| PieceAgent (x7) | Policy network for one piece type; given board obs + mask of legal moves for its pieces, outputs ranked candidate moves with scores | Small MLP or CNN head; one per piece type (Jiang, Shi, Xiang, Ju, Ma, Pao, Zu) |
| Arbitration Network | Select the final move from all candidates; has access to full board state and all proposals | Attention or MLP over (board_state, candidates) |
| Centralized Critic | Estimate V(s) for the joint state during training only; not used at inference | Shared network updated by all agents; classic CTDE critic |
| ReplayBuffer | Store (state, action, reward, next_state, done) for each agent | Circular deque per agent, or shared with agent_id tag |
| TrainingCoordinator | Schedule per-step and per-game training; write model checkpoints; log metrics | Python class orchestrating optimizer steps |

## Recommended Project Structure

```
rl_xiangqi/
├── env/                     # Game engine — no ML dependencies
│   ├── board.py             # Board state, move representation, legal move gen
│   ├── rules.py             # Xiangqi-specific rules (check, checkmate, draw)
│   ├── rewards.py           # Shaping reward definitions
│   └── xiangqi_env.py       # OpenAI Gym-compatible Env wrapper
│
├── agents/                  # RL agents — depends on env, not on UI
│   ├── base_agent.py        # Abstract PieceAgent interface
│   ├── piece_agents.py      # Concrete agents (Ju, Ma, Pao, etc.)
│   ├── arbitrator.py        # Arbitration network
│   ├── critic.py            # Centralized value network
│   └── multi_agent.py       # MultiAgentSystem: orchestrates proposal+select
│
├── training/                # Training infrastructure
│   ├── replay_buffer.py     # Circular buffer with optional PER
│   ├── coordinator.py       # TrainingCoordinator (step update + game update)
│   ├── checkpointer.py      # Save/load model weights
│   └── metrics.py           # Win rate, Elo estimation, loss tracking
│
├── ui/                      # PyQt6 front-end — depends on agents, env
│   ├── main_window.py       # App entry point, layout
│   ├── board_widget.py      # QGraphicsView chess board
│   ├── game_controller.py   # QThread bridging UI ↔ engine
│   ├── training_panel.py    # Training metrics visualization
│   └── assets/              # Piece images, board graphics
│
├── config/
│   └── default.yaml         # Hyperparameters, device, buffer sizes
│
└── main.py                  # Entry point
```

### Structure Rationale

- **env/:** Zero ML dependencies. Can be unit-tested and profiled in isolation. Legal move generation and reward shaping are the hardest-to-debug components; isolation ensures correctness before adding RL.
- **agents/:** Decoupled from UI. The multi_agent.py module is the only place that understands how proposals from all seven piece agents combine into one final action.
- **training/:** Separated from inference path. The coordinator can be disabled or replaced (e.g., batch-only mode) without touching agents.
- **ui/:** Pure presentation. GameController is the only bridge; UI never directly calls env or agents.

## Architectural Patterns

### Pattern 1: Centralized Training, Decentralized Execution (CTDE)

**What:** Each piece agent acts using only its own observations and legal-move mask at inference time. During training, a centralized critic sees the full board state and can assign credit across all agents.

**When to use:** Always — this is the standard for cooperative heterogeneous MARL. HAPPO and MAPPO are the canonical algorithms.

**Trade-offs:** Training is more expensive (centralized critic sees joint state). Inference is fast (agents are independent). Credit assignment is much more stable than purely independent learners.

**Example:**
```python
# Decentralized inference
for agent in piece_agents:
    legal_mask = env.get_legal_mask(agent.piece_type)
    proposal = agent.propose(board_obs, legal_mask)   # (move, score) tuple

# Centralized arbitration — selects among proposals using global state
final_action = arbitrator.select(board_obs, proposals)
env.step(final_action)

# Centralized critic update (training only)
value = critic(board_obs_full)  # sees full state
```

### Pattern 2: Independent Proposal + Arbitration

**What:** Each piece agent outputs a ranked list of its best candidate moves with confidence scores. The arbitrator is a separate network that takes (board_state, all_candidate_moves) and selects one final action.

**When to use:** This pattern fits the project requirement exactly. It differs from standard CTDE in that the arbitrator is trained and acts as an explicit bottleneck — it can learn meta-strategies (e.g., prefer a Ju sacrifice if Pao has a winning follow-up).

**Trade-offs:** Two-stage inference adds latency (~1ms). The arbitrator's loss must be carefully defined (it needs a signal about whether the chosen move was "right"). The simplest signal is the TD error of the game outcome. More complex: train arbitrator to maximize centralized value estimate.

**Example:**
```python
# Proposal stage
proposals = []
for agent in active_agents:      # only agents with pieces on board
    top_k = agent.top_k_moves(board_obs, legal_mask, k=3)
    proposals.extend(top_k)      # list of (piece_type, move, logit)

# Arbitration stage
final_action = arbitrator(board_obs_encoded, proposals)
# arbitrator can be: attention over proposals, MLP, or simple argmax on joint value
```

### Pattern 3: Separate Piece-Type Action Spaces

**What:** Each piece type has a fundamentally different move structure (Ju slides along ranks/files; Ma hops in L-shape; Pao needs a screen). Rather than projecting all moves into a single flat action space, each agent owns its own action encoding.

**When to use:** Always in heterogeneous piece-agent design. Forcing a single unified action space wastes capacity on impossible moves and makes the policy harder to learn.

**Trade-offs:** 7 separate networks vs 1 network with 7 heads. Separate networks: cleaner, easier to inspect per-piece behavior, easy to add/remove piece types. Heads on one network: parameter sharing may help early training if the board encoding is shared. Recommendation: separate networks with a shared board encoder (CNN backbone shared; piece-specific MLP heads).

**Example:**
```python
# Shared board encoder (ResNet-style conv)
board_features = shared_encoder(board_tensor)   # (B, D)

# Piece-specific policy heads
ju_logits  = ju_head(board_features, ju_legal_mask)
ma_logits  = ma_head(board_features, ma_legal_mask)
# ...
```

## Data Flow

### Turn Flow (AI side)

```
Human plays move
    ↓
XiangqiEnv.step(human_action)
    → board state updated, reward=0 for AI
    ↓
GameController (QThread)
    → calls MultiAgentSystem.select_action(board_obs)
         ↓
         for each PieceAgent:
             legal_mask = env.get_legal_mask(piece_type)
             proposals = agent.propose(obs, legal_mask)   # forward pass
         ↓
         Arbitrator.select(board_obs, all_proposals)      # forward pass
         → final_action returned
    ↓
XiangqiEnv.step(final_action)
    → board state updated
    → reward computed (shaping + terminal check)
    ↓
GameController emits signal → BoardWidget.update()
```

### Training Flow (per-step)

```
(state, action, reward, next_state, done)
    ↓
ReplayBuffer.push(transition)
    ↓ (if buffer has enough samples)
TrainingCoordinator.step_update()
    → sample mini-batch
    → compute TD targets using Centralized Critic
    → update per-agent policy networks (actor loss)
    → update Arbitrator (selection quality loss)
    → update Centralized Critic (value loss)
    → log metrics
```

### End-of-Game Deep Update

```
Episode ends (win/loss/draw)
    ↓
XiangqiEnv returns terminal reward (+1 / -1 / 0)
    ↓
TrainingCoordinator.game_update()
    → compute Monte-Carlo returns over full game trajectory
    → perform multiple update passes (larger batch, more epochs)
    → update Elo estimate
    → checkpoint models
    ↓
MetricsLogger → TrainingPanel emits updated plots
```

### Key Data Flows

1. **Board observation encoding:** Board state is a 3D tensor (channels × 10 × 9) with one channel per piece type per color + auxiliary channels (turn, repetition count). All agents share this encoding as input.
2. **Legal move mask:** The Env provides per-piece-type boolean masks over possible moves. Agents apply softmax only over legal moves, preventing illegal action selection before arbitration.
3. **Reward shaping signal:** XiangqiEnv computes a composite reward: terminal outcome (dominant) + capture delta (piece values) + position control (optional). All agents share the same scalar reward per step.
4. **Model persistence:** After each game, TrainingCoordinator writes versioned `.pt` files for all 7 piece agents + arbitrator + critic. Best model (by Elo) is separately tracked.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Single machine (M1 Max 32GB) | All components in one process; QThread for UI separation; MPS for neural forward/backward passes; CPU workers for env stepping |
| If training speed becomes bottleneck | Decouple data collection (CPU, env-heavy) from gradient updates (MPS, net-heavy) using a queue; async actor-learner pattern |
| If model grows large | Share CNN board encoder weights across all piece agents; only piece-specific heads are independent |

### Scaling Priorities

1. **First bottleneck:** Neural network forward passes during AI turn selection. Fix: batch all 7 piece-agent forward passes together; use shared encoder to reduce repeated computation.
2. **Second bottleneck:** UI freezing during training epochs. Fix: all training happens in QThread; never block the Qt main thread.

## Anti-Patterns

### Anti-Pattern 1: Monolithic Policy Network

**What people do:** Use a single policy network that takes board state and outputs one move over all possible moves (e.g., 10×9×possible_destinations flat space).

**Why it's wrong:** For heterogeneous piece agents, this ignores the per-piece structural prior. The network must learn to zero out impossible moves for each piece type independently — wasted capacity. More critically, it destroys the independent-proposal architecture entirely: there is no meaningful arbitration step if there is only one policy.

**Do this instead:** Separate policy head per piece type, each operating over its own legal move set. A shared CNN board encoder feeds all heads.

### Anti-Pattern 2: Blocking UI Thread for AI Computation

**What people do:** Call `agent.select_action()` directly in a Qt event handler (button click, drag release).

**Why it's wrong:** Neural forward passes on even a small network take 10–100ms. On MPS, the first call includes kernel compilation overhead (seconds). The UI freezes and Qt event queue backs up.

**Do this instead:** Use `QThread` (or `QRunnable` + `QThreadPool`) for all AI computation. Communicate results back to the main thread via `pyqtSignal`.

### Anti-Pattern 3: Training on Every Single Step Synchronously

**What people do:** After each env step, immediately run a gradient update before the UI updates.

**Why it's wrong:** Gradient updates are 10–100x slower than env steps. The UI will feel sluggish. The training signal per step is also very noisy — minibatch updates from a replay buffer are far more stable.

**Do this instead:** Push transitions to a replay buffer every step. Run lightweight gradient updates asynchronously on a fixed schedule (e.g., every N steps). Run a deeper multi-epoch update at game end.

### Anti-Pattern 4: Shared Replay Buffer Confusion Without Agent Tags

**What people do:** Store all transitions in one replay buffer without tagging which piece agent took the action.

**Why it's wrong:** Each piece agent must only receive gradient updates from transitions where *it* proposed the action. Untagged buffers cause all agents to train on all transitions, corrupting per-piece specialization.

**Do this instead:** Tag each transition with `agent_id` and `piece_type`. During training, sample per-agent sub-batches, or maintain separate per-agent buffers.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| PyTorch MPS | `.to('mps')` device placement; `PYTORCH_ENABLE_MPS_FALLBACK=1` env var | Only one MPS device; no distributed training. Unified memory means no explicit CPU↔GPU copies. |
| pyqtgraph / matplotlib | Embedded in QWidget for training visualization | pyqtgraph is faster for live updating; matplotlib is more familiar. Recommend pyqtgraph for real-time loss curves. |
| Model checkpoints (filesystem) | `torch.save` / `torch.load`; versioned filenames | Save after each game. Keep last N + best-ever checkpoint. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| UI ↔ GameController | `pyqtSignal` / `pyqtSlot` (Qt signal/slot across threads) | Only way to safely update UI from QThread |
| GameController ↔ XiangqiEnv | Direct Python method calls (same thread as GameController) | Env is pure Python, safe to call synchronously |
| MultiAgentSystem ↔ PieceAgents | Direct method calls (same process/thread) | Piece agents are stateless at inference; thread safety only matters during training |
| TrainingCoordinator ↔ ReplayBuffer | Direct Python (same thread) | If async training is added later, protect with a threading.Lock |
| XiangqiEnv ↔ ReplayBuffer | TrainingCoordinator collects transitions from Env and pushes to buffer | Env does not know about the buffer; coordinator decouples them |

## Build Order Implications

The component dependency graph implies this build order:

1. **XiangqiEnv** — foundational; no RL dependencies. Build and test game rules fully before writing any agent code.
2. **Board observation encoding + legal move masks** — part of env; needed by all agents. Define the tensor format early; changing it later breaks all agent input shapes.
3. **PieceAgent shells** (random policy) — stub agents that can propose legal random moves. Enables end-to-end wiring before any real learning.
4. **Arbitration + MultiAgentSystem** — once agents can propose moves, the arbitration loop can be wired and tested for correctness.
5. **PyQt6 UI + GameController** — wire human play against random-policy agents. Validates the full game loop before training is integrated.
6. **ReplayBuffer + TrainingCoordinator + Centralized Critic** — learning infrastructure. After this, agents start actually learning.
7. **Shaping rewards** — tune after basic learning works. Getting sign and scale right requires seeing initial training curves.
8. **MPS optimization + checkpointing + training visualization** — final hardening once learning is confirmed functional.

## Sources

- CTDE paradigm: HAPPO/HATRPO (Kuba et al.), MAPPO — confirmed patterns for heterogeneous cooperative MARL [MEDIUM confidence — papers confirmed via web search, not Context7]
- Proposal + Arbitration pattern: inspired by CTDE centralized critic pattern; no exact published "proposal+arbitration for chess pieces" system found — this is a novel combination [LOW confidence — design extrapolated from CTDE + MoE literature]
- AlphaZero architecture (shared encoder, policy head + value head): IEEE CoG 2019 paper, PNAS AlphaZero paper [HIGH confidence — well-documented]
- M2CTS (MoE + MCTS for chess): https://www.researchgate.net/publication/400492537 [MEDIUM confidence — webSearch only]
- PyTorch MPS architecture: official PyTorch docs + webSearch [HIGH confidence] — single MPS device, no distributed, CPU workers for async collection
- PyQt6 threading pattern: established Qt pattern (QThread + signals) [HIGH confidence — standard practice]
- Xiangqi RL: DRL+MCTS Xiangqi (arXiv 2506.15880), Mastering Xiangqi Without Search (arXiv 2410.04865) [MEDIUM confidence — papers surfaced via webSearch]
- ANNSIM 2024 Markov Games with Chess (per-piece agent structure): https://annsim.org/wp-content/uploads/2024/08/ANNSIM2024_86_Paper.pdf [LOW confidence — could not fetch full paper]
- Per-piece action space design: logical derivation from Xiangqi rules; each piece type has structurally distinct move generation [HIGH confidence — game rules are fixed]

---
*Architecture research for: RL-Xiangqi heterogeneous multi-agent chess system*
*Researched: 2026-03-19*
