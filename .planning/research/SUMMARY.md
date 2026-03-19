# Project Research Summary

**Project:** RL-Xiangqi — Heterogeneous Multi-Agent Reinforcement Learning for Chinese Chess
**Domain:** Desktop board game with online RL, Apple Silicon MPS, heterogeneous multi-agent architecture
**Researched:** 2026-03-19
**Confidence:** MEDIUM-HIGH

## Executive Summary

This project builds a desktop Xiangqi (Chinese Chess) application where a heterogeneous multi-agent RL system learns to play from scratch, updating its weights in real time during games against a human opponent on an Apple Silicon M1 Max. The defining architectural idea — that each piece type (General, Advisor, Elephant, Horse, Chariot, Cannon, Soldier) gets its own independent policy network, with proposals coordinated by an arbitration network — is a genuine research novelty. No existing framework or library handles this combination out of the box. The entire stack must be custom-built: a Xiangqi rules engine (no maintained Python library exists), a custom PPO/policy-gradient training loop (Stable-Baselines3 is MPS-incompatible), and a bespoke multi-agent coordination layer. Despite this custom requirement, all component patterns are well-understood and the implementation risk is manageable with careful build ordering.

The recommended approach is PyTorch 2.10 on native ARM64 Python 3.12 with the MPS backend, PyQt6 for the desktop UI, and a Centralized Training / Decentralized Execution (CTDE) multi-agent architecture. The rules engine must be built and exhaustively tested first — it is the root dependency for every other component. Piece-type agents with separate action spaces feed proposals to a centralized arbitrator, which selects the final move using full board state. Online learning runs in a QThread worker to keep the UI responsive, with a replay buffer spanning at least 5,000–10,000 transitions to prevent catastrophic forgetting. A self-play warm-up phase (200–500 games before human-facing deployment) is required to produce an initial gradient signal from the otherwise sparse terminal reward.

The three existential risks to this project are: (1) MPS-specific PyTorch bugs that silently freeze training weights (mitigated by pinning PyTorch >= 2.4 and verifying optimizer state in unit tests), (2) incorrect Xiangqi repetition rules producing corrupted reward signals (mitigated by implementing WXF perpetual-check/chase rules before any RL is connected), and (3) catastrophic forgetting during online learning wiping out accumulated skill (mitigated by a circular replay buffer and checkpoint rollback). Address all three before connecting the training loop to real gameplay.

## Key Findings

### Recommended Stack

The entire ML layer runs on PyTorch 2.10 with the MPS backend, requiring ARM64 native Python 3.12 (Rosetta-emulated Python silently disables MPS with no warning). Stable-Baselines3 is explicitly ruled out due to confirmed float64/MPS incompatibility — the training loop must be custom-built in plain PyTorch, approximately 300 lines for a thin PPO implementation with full MPS control. TorchRL's `MultiAgentMLP(share_params=False)` can provide scaffolding for the heterogeneous-agent bookkeeping without ceding control of the training loop. The UI is PyQt6 with QGraphicsScene/QGraphicsView for board rendering and PyQtGraph for live training metrics (faster than matplotlib for real-time Qt widget updates). All tensor operations must use float32 throughout — MPS does not support float64 or bfloat16 at all.

**Core technologies:**
- Python 3.12 (ARM64 native): Runtime — MPS requires native ARM64; Rosetta silently disables GPU
- PyTorch 2.10 + MPS: Deep learning + GPU backend — unified memory eliminates CPU-GPU copies on M1
- Custom PPO implementation: RL algorithm — only way to guarantee float32 and MPS control
- Custom Xiangqi rules engine: Game logic — no maintained pure-Python Xiangqi library exists
- PyQt6 6.10.2: Desktop UI — QGraphicsScene is the correct pattern for interactive board pieces
- TorchRL 0.7.x (optional): MARL scaffolding — `MultiAgentMLP(share_params=False)` maps to heterogeneous agents
- PyQtGraph 0.13.x: Live training plots — faster than matplotlib for real-time Qt updates
- NumPy 2.4.x: Array ops — required for PyTorch 2.10 compatibility (NumPy 1.x causes RuntimeError)
- gymnasium 1.0.x: Env interface — wraps the rules engine for RL tooling compatibility
- uv: Package management — reliable ARM64 package resolution on Apple Silicon

### Expected Features

**Must have (table stakes — v1 launch):**
- Complete Xiangqi rules engine (all 7 piece types, flying general, perpetual-check/chase, stalemate-as-loss)
- PyQt6 board UI with drag-and-drop, legal move highlighting, turn management
- Heterogeneous agent networks (7 piece-type policy networks + arbitration network)
- Proposal + arbitration mechanism selecting the AI's final move
- Shaped intermediate rewards (material capture delta + basic position score)
- Online learning loop: lightweight per-step update + deep end-of-game batch update
- MPS backend with float32 enforcement throughout
- Model save/load after each game (persistence is required for observable improvement)
- Observable metrics dashboard (win rate over last N games, episode reward trend)

**Should have (competitive differentiators — v1.x):**
- Move history display with Xiangqi-style notation
- Experience replay buffer (required to prevent catastrophic forgetting — treat as v1 requirement)
- Replay/game review using the trained model for intrinsic analysis
- Piece-level contribution visualization (which agent proposed the winning move)
- Loss/gradient norm display for developer insight

**Defer (v2+):**
- Self-play offline pre-training mode (AI vs. AI)
- Policy temperature / exploration scheduling
- Curriculum learning from simplified board configurations
- Export for benchmarking against pikafish/fairy-stockfish
- Opening book, PGN import, online multiplayer, MCTS at inference (all anti-features for v1)

### Architecture Approach

The system has four clearly separated layers: UI (PyQt6 widgets), Game Engine (XiangqiEnv with rules and reward logic), Agent Layer (7 PieceAgent networks + ArbitrationNetwork running CTDE), and Learning Layer (ReplayBuffer, TrainingCoordinator, CentralizedCritic). The GameController QThread is the sole bridge between the UI and the engine/agent layers — no ML code runs on the Qt main thread. Each PieceAgent operates over its own piece-type action space and proposes top-K candidate moves with confidence scores; the ArbitrationNetwork receives the full board state plus all proposals and selects the final action. The CentralizedCritic (used only during training) sees full joint state for stable credit assignment.

**Major components:**
1. XiangqiEnv — canonical board state, legal move generation, reward shaping, terminal detection; zero ML dependencies; must be tested in isolation first
2. PieceAgent x7 (Jiang, Shi, Xiang, Ju, Ma, Pao, Zu) — independent policy networks per piece type, each with its own action space and legal-move mask; shared CNN board encoder feeds separate MLP heads
3. ArbitrationNetwork — selects final action from all candidate proposals using full board state; trained via CTDE with centralized value signal
4. CentralizedCritic — value network seeing joint state; used for stable advantage estimation during training only
5. GameController (QThread) — bridges human input and AI move selection off the main thread; communicates via pyqtSignal/pyqtSlot
6. TrainingCoordinator — schedules per-step lightweight updates and end-of-game deep updates; manages checkpoints and metrics
7. ReplayBuffer — circular buffer spanning games; tagged with agent_id per transition; prevents catastrophic forgetting
8. BoardWidget + TrainingPanel — pure presentation layer; receives data only via Qt signals

### Critical Pitfalls

1. **MPS silent weight freeze (Adam non-contiguous tensor bug)** — PyTorch < 2.4 Adam optimizer silently freezes on MPS when tensors are non-contiguous. Pin PyTorch >= 2.4, call `.contiguous()` before optimizer steps, and write a unit test verifying `exp_avg_sq` is non-zero after 10 gradient steps.

2. **Incorrect Xiangqi repetition rules** — Perpetual check is a LOSS for the checking side (not a draw). Implementing Western chess 3-fold-repetition-as-draw corrupts all reward signals. Implement WXF rules with test cases for perpetual-check and perpetual-chase positions before connecting any RL training.

3. **GUI freeze during inline training** — Running gradient updates on the Qt main thread freezes the board. All training (per-step and end-of-game) must run in a QThread from day one, communicating results back via signals.

4. **Catastrophic forgetting during online learning** — Sequential training on correlated game data overwrites prior knowledge. A circular replay buffer of 5,000–10,000 transitions with 70% recent / 30% historical sampling mix is not optional — it must be in place before the first human-facing session.

5. **Cold-start: no learning signal for hundreds of games** — Random-policy agents playing from scratch rarely achieve checkmate, so terminal rewards never arrive. Implement a 200–500 game self-play warm-up phase with high initial epsilon before enabling human-vs-agent mode.

6. **Simultaneous heterogeneous agent gradient conflicts** — Updating all 7 piece agents simultaneously from the same trajectory violates MARL stationarity, causing oscillating loss and policy collapse. Use sequential update ordering (e.g., by piece value) with separate optimizers per agent type.

7. **Reward shaping overpowers terminal reward** — Material-capture shaping rewards can train agents to collect pieces without winning. Cap shaping at 10-20% of terminal reward magnitude and use potential-based shaping for provable policy-invariance.

8. **Arbitrator bottleneck** — If the arbitrator is too small or receives insufficient context, piece agents learn that their proposals are ignored and gradients collapse. Give the arbitrator the full board state, monitor selection entropy, and train it with centralized value signals.

## Implications for Roadmap

Based on combined research, the dependency graph mandates a strict build order. The rules engine is the root; agents cannot be wired until state representation is fixed; training cannot start until agents can produce legal moves; the UI can be connected after the game loop works with stub agents. This suggests 5 phases.

### Phase 1: Xiangqi Rules Engine + Environment Foundation

**Rationale:** Every other component depends on correct Xiangqi rules. Bugs here corrupt all downstream reward signals and require discarding trained models. The rules engine must be complete and exhaustively tested before any RL code is written. Two of the eight critical pitfalls (repetition rules, incorrect terminal detection) are rules-engine bugs that are catastrophically expensive to fix late.
**Delivers:** A standalone, fully tested XiangqiEnv with legal move generation for all 7 piece types, flying-general check detection, perpetual-check/chase resolution per WXF rules, stalemate-as-loss, board state tensor representation (14-channel 10x9), and per-piece-type legal move masks.
**Addresses:** Complete rules engine, legal move validation, board state representation (all foundational table-stakes from FEATURES.md)
**Avoids:** Pitfall 3 (incorrect repetition rules), Pitfall 1 (rules bugs discovered after training = retrain from scratch)
**Research flag:** Standard patterns apply. Xiangqi rules are fixed and well-documented; the WXF 2024 paper on repetition rules is the authoritative reference. No additional research phase needed.

### Phase 2: PyQt6 Board UI + Human Game Loop

**Rationale:** Wiring a human-playable board against random-policy stub agents validates the full game flow (turn management, drag-drop, win detection, board rerender) before any ML complexity is introduced. This also forces the QThread architecture into place early — the correct threading model must be established before the training loop exists, not retrofitted afterward.
**Delivers:** A playable human-vs-random-AI desktop application with drag-and-drop, legal move highlighting, turn indicator, game start/restart, and a GameController QThread bridge ready to receive real agent calls.
**Addresses:** Board UI, drag-and-drop interaction, turn management, legal move highlighting (all P1 table-stakes from FEATURES.md)
**Avoids:** Pitfall 2 (GUI freeze) — threading model established before training is connected
**Research flag:** Standard patterns apply. PyQt6 QGraphicsScene for board games is a documented, high-confidence pattern. No additional research needed.

### Phase 3: Heterogeneous Agent Architecture + Arbitration

**Rationale:** The 7 piece-type networks + arbitrator is the project's primary technical differentiator and the highest-risk ML design decision. The arbitrator architecture (attention vs. MLP), the shared-encoder vs. independent-encoder choice, and the sequential update ordering for MARL stability must all be decided and tested before training begins. Validating that the proposal + selection loop produces valid legal moves (even with random weights) is the gating condition.
**Delivers:** 7 PieceAgent policy networks with shared CNN board encoder and piece-specific MLP heads, ArbitrationNetwork receiving full board state + proposals, MultiAgentSystem orchestrating the proposal-select loop, CentralizedCritic for training, and stub training wiring that confirms legal moves are produced every turn.
**Addresses:** Heterogeneous agent networks, proposal + arbitration mechanism (core P1 differentiators from FEATURES.md)
**Avoids:** Pitfall 4 (arbitrator bottleneck), Pitfall 8 (simultaneous gradient conflicts) — sequential update ordering and per-agent optimizer separation designed in from the start
**Research flag:** Deeper research recommended. The proposal + arbitration pattern is novel (no exact published implementation found). The CTDE/HAPPO literature provides theoretical grounding but not a direct implementation reference. Research should focus on: arbitrator loss function design, sequential update ordering implementation, and attention-based vs. MLP arbitrator trade-offs.

### Phase 4: Training Infrastructure + Online Learning Loop

**Rationale:** With a working game loop and functional (random-policy) agents, the full learning infrastructure can be built and validated before human-facing deployment. This phase must include the replay buffer, TrainingCoordinator, self-play warm-up procedure, and MPS-specific hardening (contiguous tensor checks, float32 enforcement). The online learning loop cannot go live until all catastrophic-forgetting and cold-start mitigations are in place.
**Delivers:** Circular replay buffer (5,000–10,000 transitions, agent-tagged), TrainingCoordinator with per-step lightweight update + end-of-game deep update (both in QThread), PPO/policy-gradient training loop (custom, float32, MPS), self-play warm-up runner (200–500 games), checkpoint system with rollback, and MPS health checks (Adam contiguous tensor verification, exp_avg_sq unit test).
**Addresses:** Online learning loop, MPS backend, model save/load, shaped intermediate rewards (all P1 from FEATURES.md)
**Avoids:** Pitfall 1 (MPS silent weight freeze), Pitfall 5 (reward hacking), Pitfall 6 (catastrophic forgetting), Pitfall 7 (cold-start no learning signal)
**Research flag:** Standard patterns for PPO and replay buffers. MPS-specific hardening is well-documented in PyTorch issue tracker. Reward shaping calibration requires empirical tuning — plan for iteration. No formal research phase needed, but budget time for hyperparameter experimentation.

### Phase 5: Metrics, Observability + Polish

**Rationale:** The metrics dashboard is not cosmetic — it is the mechanism by which the core value proposition (observable AI improvement) becomes visible to users. Without it, the learning happening inside the system is invisible and the product's central promise is undemonstrable. This phase also includes UX hardening (thinking animation, illegal-move feedback, atomic checkpoint saves).
**Delivers:** Win rate trend panel (PyQtGraph, updates per game), episode reward trend, strength indicator, move history log, asynchronous model save (background thread), thinking animation during AI turn, illegal-move visual feedback, and piece-level contribution display (which agent's proposal was selected).
**Addresses:** Observable metrics dashboard, move history display, UX polish (P1 and P2 items from FEATURES.md)
**Avoids:** UX pitfalls (invisible learning, >2s AI response, silent illegal move failure)
**Research flag:** Standard patterns. PyQtGraph embedding in PyQt6 is well-documented. No additional research phase needed.

### Phase Ordering Rationale

- **Rules engine first** because it is the root dependency for every other component and rules bugs discovered after training begin require discarding all trained models.
- **UI second** (before agents) because a playable human-vs-random-stub game validates the full game flow and forces QThread architecture into place before training is connected.
- **Agent architecture third** because the proposal + arbitration design is the highest-risk ML decision and must be validated producing legal moves before training infrastructure is built on top of it.
- **Training infrastructure fourth** because it depends on working agents and must include all catastrophic-forgetting mitigations before the first human-facing game.
- **Observability last** because it enhances an already-working training loop rather than enabling it, and its complexity is lower.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Heterogeneous Agent Architecture):** The proposal + arbitration pattern is novel with no exact published implementation. Research should focus on arbitrator loss function, attention vs. MLP arbitrator architecture, and sequential update ordering per the HARL framework. The CTDE literature (HAPPO, MAPPO) provides theoretical grounding but not a Xiangqi-specific recipe.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Rules Engine):** Xiangqi rules are fixed; WXF 2024 paper is authoritative reference.
- **Phase 2 (PyQt6 UI):** QGraphicsScene board game pattern is well-documented with real-world codebases (PyQtChess, MzChess) as references.
- **Phase 4 (Training Infrastructure):** Custom PPO on MPS is well-understood; MPS pitfalls are documented in PyTorch issue tracker.
- **Phase 5 (Observability):** PyQtGraph + PyQt6 integration is standard.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core choices (PyTorch MPS, PyQt6, custom PPO, NumPy 2.x compatibility) verified across multiple sources. MPS float64/bfloat16 restrictions and SB3 incompatibility are confirmed facts, not speculation. |
| Features | MEDIUM-HIGH | Table-stakes and MVP scope are clear. Differentiator features (heterogeneous agents, proposal + arbitration) are well-motivated by research but have no directly comparable shipped product to validate against. |
| Architecture | MEDIUM | CTDE pattern and per-piece action space design are high-confidence. The specific proposal + arbitration mechanism is a novel combination — extrapolated from CTDE + MoE literature with no exact published precedent. Design may require iteration. |
| Pitfalls | MEDIUM-HIGH | MPS bugs (Adam non-contiguous, clip_grad_norm_ memory leak) are confirmed via PyTorch issue tracker. Xiangqi repetition rules are verified via 2024 academic paper. MARL stationarity issues are confirmed via HARL literature. Cold-start and reward hacking are well-documented RL failure modes. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Arbitrator loss function:** The correct loss for the arbitration network is underspecified. Options include TD error of game outcome assigned to selection decisions, maximize centralized value estimate of selected move, or REINFORCE with outcome as baseline. This requires empirical investigation during Phase 3.
- **Reward shaping calibration:** Specific coefficient values for material capture delta and position control rewards require empirical tuning. Budget time in Phase 4 for ablation experiments (shaped vs. unshaped agent over 200 games per the research recommendation).
- **Self-play warm-up convergence criteria:** The 200–500 game warm-up estimate is a heuristic. The actual criterion (average game length > 30 moves, shaping reward non-zero) should be used to gate transition to human-facing mode, not a fixed game count.
- **Shared vs. independent board encoder:** Research recommends a shared CNN encoder with piece-specific MLP heads, but the trade-off vs. fully independent networks has not been empirically validated for Xiangqi specifically. Start with shared encoder; benchmark independently if piece specialization fails to emerge.

## Sources

### Primary (HIGH confidence)
- PyTorch 2.10 release notes, pytorch.org — MPS backend capabilities and limitations
- PyTorch GitHub issues — Adam non-contiguous tensor bug on MPS (confirmed for < 2.4)
- PyTorch GitHub issues (March 2025) — `clip_grad_norm_` memory leak on MPS 2.7.0 / macOS 15.4
- docs.pytorch.org/rl — TorchRL `MultiAgentMLP(share_params=False)` heterogeneous agent support
- SB3 team acknowledgment + community reports — Stable-Baselines3 MPS incompatibility
- PyPI + community reports — NumPy 2.x / PyTorch 2.3.1+ compatibility requirement
- Qt official documentation — QGraphicsScene/QGraphicsView patterns, QThread signal/slot pattern
- riverbankcomputing.com — PyQt6 6.10.2 release

### Secondary (MEDIUM confidence)
- arXiv:2410.04865 — "Mastering Chinese Chess AI (Xiangqi) Without Search" — architecture and training approach
- arXiv:2304.09870 — Heterogeneous-Agent Reinforcement Learning (HARL framework, sequential update ordering)
- IJCAI 2024 M2RL Framework — multi-agent cooperative coordination
- HAPPO/HATRPO (Kuba et al.), MAPPO papers — CTDE pattern for cooperative MARL
- "A Complete Algorithm for Ruling the WXF Repetition Rules" (2024) — Xiangqi perpetual-check/chase implementation
- PyQtChess, MzChess, CARA projects — real-world PyQt desktop chess UI patterns
- AlphaZero (PNAS), IEEE CoG 2019 — shared encoder + policy/value head architecture

### Tertiary (LOW confidence)
- ANNSIM 2024 "Markov Games with Chess" — per-piece agent structure (paper not fully accessible)
- M2CTS (MoE + MCTS for chess) — researchgate.net (webSearch only, not directly accessed)
- Proposal + arbitration as novel pattern — extrapolated from CTDE + MoE literature; no exact published implementation

---
*Research completed: 2026-03-19*
*Ready for roadmap: yes*
