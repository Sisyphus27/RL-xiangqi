# Pitfalls Research

**Domain:** Heterogeneous multi-agent RL — Chinese Chess (Xiangqi) with online learning, MPS backend, PyQt6 desktop UI
**Researched:** 2026-03-19
**Confidence:** MEDIUM-HIGH (MPS bugs verified via official PyTorch issues; MARL pitfalls verified via HARL/MAPPO literature; Xiangqi rules confirmed via 2024 academic paper)

---

## Critical Pitfalls

### Pitfall 1: MPS Silent Weight Freeze (Adam Non-Contiguous Tensor Bug)

**What goes wrong:**
On PyTorch < 2.4 with MPS backend, the Adam optimizer's `addcmul_` and `addcdiv_` in-place operations silently fail when operating on non-contiguous output tensors. The second moment (`exp_avg_sq`) never updates — it stays at its zero initialization — and weight updates silently stop. The network appears to be training (loss is logged, GPU is busy) but parameters are frozen. This is extremely hard to notice because `exp_avg_sq` initializes to zero and "stays at zero" looks identical to "never updated."

**Why it happens:**
The MPS Metal kernel for fused in-place operations has a correctness bug for non-contiguous memory layouts. Non-contiguous tensors arise naturally from `view()`, `permute()`, `transpose()`, or slicing operations, which are common in attention layers and in multi-agent systems where agent observation tensors are sliced from a shared game state.

**How to avoid:**
- Pin PyTorch >= 2.4 and macOS >= 15 in the project's requirements from day one
- Explicitly call `.contiguous()` before any optimizer step on parameters that might be non-contiguous: `param.data = param.data.contiguous()`
- Write a training sanity check that verifies `exp_avg_sq` is non-zero after the first 10 steps

**Warning signs:**
- Loss drops initially then plateaus completely and never improves, even with high learning rate
- `torch.norm(param.grad)` shows non-zero gradients but weights are not changing
- All agents converge to identical, degenerate policies early in training

**Phase to address:** Foundation phase (MPS setup and training harness). Verify fix before any RL logic is written.

---

### Pitfall 2: PyQt6 GUI Freezing During Inline Training Step

**What goes wrong:**
If the online training step (gradient update after each move) runs on the main Qt event loop thread, the GUI freezes for the duration of that update. Even a 100ms training step creates a visibly sluggish experience. A "deep update" at game end (multiple gradient steps) will freeze the UI for seconds — the "worst UX zone" per interaction latency research.

**Why it happens:**
Qt is single-threaded by design. Calling any blocking Python code from the main thread prevents event processing, which blocks repaints, mouse events, and drag-drop handling for the chess board.

**How to avoid:**
- Architect the training loop as a `QThread` worker from the start, never inline in event handlers
- Use Qt signals/slots to pass training metrics (loss, win rate) back to the UI thread for display
- The per-move "lightweight update" should be debounced or queued; the end-of-game "deep update" must always run in a worker thread
- Never call `waitForDone()` on the training thread from the main thread — it re-introduces the freeze

**Warning signs:**
- Board drag-drop becomes sluggish or unresponsive during AI thinking
- OS reports the application as "Not Responding" briefly after moves
- `QTimer` callbacks are delayed or bunched

**Phase to address:** UI + game loop integration phase. Thread separation must be designed before connecting training to game events.

---

### Pitfall 3: Xiangqi Repetition Rules Are Not "Drawn by 3-fold Repetition"

**What goes wrong:**
Western chess (and most games) treat repeated positions as draws. Xiangqi does not. In Xiangqi, perpetual check is a *loss* for the checking side, perpetual chase is a *loss* for the chasing side, and mutual perpetual check/chase is a draw. An RL agent trained with a naive "third repetition = draw" rule will exploit this to avoid losing — particularly by perpetually checking when ahead, leading to incorrect game outcomes and corrupted reward signals during online learning.

**Why it happens:**
This rule is unique to Xiangqi and counter-intuitive. Most Xiangqi applications get it wrong (Tiantian Xiangqi's repetition handling is documented as "completely broken"). Developers familiar with chess assume repetition = draw.

**How to avoid:**
- Implement the WXF repetition rules from a verified reference (the 2024 academic paper covering all 110 WXF example cases is the authoritative source)
- At minimum: detect check-loops and award a loss to the perpetual checker; detect chase-loops and award a loss to the chaser; draw only for mutual-perpetual or non-check/non-chase loops
- Add test cases for at least 5 perpetual-check positions and 5 perpetual-chase positions before connecting RL training

**Warning signs:**
- Agent develops a policy of repeated checking sequences in won positions
- Games never terminate despite both sides having made 50+ moves
- Win/loss statistics look skewed (fewer losses than expected for a random agent)

**Phase to address:** Xiangqi rules engine phase, before any RL training begins.

---

### Pitfall 4: Arbitrator Network Becomes a Learning Bottleneck

**What goes wrong:**
In the "piece agents propose, arbitrator selects" architecture, the arbitrator network sits on the critical path of every action selection. If the arbitrator is too weak (too small, wrong input representation), the piece agents learn to propose reasonable moves but the arbitrator selects poorly — the system's ceiling is limited by the arbitrator, not the piece agents. Conversely, if the arbitrator is too dominant, piece agents become lazy proposers.

**Why it happens:**
Research on multi-agent coordinator systems shows that sub-agent capability matters more than orchestrator capability in terms of raw output quality, but a weak orchestrator becomes a routing bottleneck. The arbitrator here is the orchestrator. In training, the arbitrator receives a multi-hot input (which pieces proposed which moves) and must learn a value function over joint actions — a harder learning problem than individual piece policies.

**How to avoid:**
- Give the arbitrator the full board state as input, not just the proposed moves — it needs context to evaluate proposals
- Train the arbitrator with its own value head using centralized training (CTDE pattern): the arbitrator can see global state during training even if piece agents cannot
- Monitor arbitrator confidence distribution during training; if it always selects the first proposal, it has not learned

**Warning signs:**
- Arbitrator selection entropy collapses to near-zero early in training (always picking the same agent's proposal)
- Removing the arbitrator and using random selection among proposals yields similar performance
- Piece agent gradients become zero (they learn that their proposals are ignored)

**Phase to address:** Multi-agent architecture phase — design and validate before full RL training.

---

### Pitfall 5: Reward Shaping Overpowers Terminal Reward (Reward Hacking)

**What goes wrong:**
Shaping rewards for material gain (capturing pieces), board control, and position cause the agent to optimize those signals instead of winning. Common failure modes: the agent repeatedly captures low-value pieces to maximize material rewards without ever checkmating; the agent develops a "piece-collecting" strategy that sacrifices king safety; shaped reward for board control causes the agent to spread pieces widely without tactical purpose.

**Why it happens:**
Goodhart's Law — when a proxy metric becomes the target, it stops being a reliable measure of the true objective. Piece capture rewards are particularly dangerous because Xiangqi has high-value pieces (Rook, Cannon) that are easy to overweight. Shaping rewards also interact across agents: the piece agent that captures a piece gets a direct reward but the arbitrator that selected its proposal does not — causing a credit mismatch.

**How to avoid:**
- Scale all shaping rewards to at most 10-20% of the terminal win/loss reward magnitude
- Use potential-based shaping (reward = gamma * Phi(s') - Phi(s)) which is provably policy-invariant
- Run ablation: train one agent with shaping, one without — if the shaped agent is not outperforming after 500 games, the shaping is miscalibrated
- Assign shaping rewards to the arbitrator (the decision-maker) not to individual piece agents

**Warning signs:**
- Win rate does not improve beyond 30% despite loss decreasing
- Agent captures many pieces but consistently loses on checkmate
- Agent never develops multi-move tactical sequences

**Phase to address:** Reward design phase, before full online training. Re-verify after adding each new shaping signal.

---

### Pitfall 6: Catastrophic Forgetting During Online Learning Against Human

**What goes wrong:**
Online learning without a replay buffer causes the agent to catastrophically overfit to recent human play patterns. If the human plays a particular opening ten games in a row, the agent learns to counter it — and loses the ability to play all other openings. This violates the core value proposition: the agent should get broadly stronger, not narrowly adapted.

**Why it happens:**
Online RL with sequential mini-batches from correlated data (consecutive moves of the same game, consecutive games against the same human) violates the i.i.d. assumption. Neural network SGD aggressively overwrites old knowledge when data distribution shifts.

**How to avoid:**
- Maintain a circular replay buffer of at least 5,000–10,000 (state, action, reward) transitions across all games
- Each training step should sample a mix of recent transitions (70%) and random historical transitions (30%)
- Periodically snapshot model weights; if win rate against a fixed reference opponent drops >15% between snapshots, roll back to the snapshot and diagnose
- The "deep update" at game end should train on a sampled batch from the full replay buffer, not just the current game

**Warning signs:**
- Agent plays well against human's current style but poorly against novel openings
- Win rate oscillates game-to-game rather than trending upward
- Loss on validation set (fixed position evaluations) increases while training loss decreases

**Phase to address:** Online learning architecture phase — replay buffer must be in place before the first human-facing training session.

---

### Pitfall 7: Training from Scratch Produces No Learning Signal for Hundreds of Games

**What goes wrong:**
Starting from random weights with no pretraining, the agent plays random-like moves for many games. Terminal rewards (win/loss) are never received because neither side can achieve checkmate from pure random play — games terminate on move-count limits or draw conditions. The shaping rewards are the only signal, and early on those are also near-zero. Effectively there is no gradient signal, and training makes no progress.

**Why it happens:**
Xiangqi's large action space (~40-100 legal moves per position) combined with no prior knowledge means the probability of stumbling onto a checkmate sequence from random play is astronomically low. This is the sparse-reward cold-start problem. AlphaZero solved this with MCTS; pure online policy gradient from random play does not have this luxury.

**How to avoid:**
- Implement a self-play warm-up phase: run 200-500 games of agent-vs-self before enabling human-vs-agent mode, to build a minimal replay buffer with non-trivial game progressions
- Use epsilon-greedy exploration with a high initial epsilon (0.5+) during warm-up, decaying to 0.1 during human play
- Add a simple material-advantage heuristic as an auxiliary value target during early training (not as policy signal — only to bootstrap value estimates)
- Consider starting from a small random opening curriculum (fixed first 4 moves) to generate more varied game states early

**Warning signs:**
- Average game length is under 20 moves for the first 100 games (agent is playing suicide moves)
- All piece agents propose the same move type regardless of board state
- Shaping reward per game stays near zero after 50 games

**Phase to address:** Initial training phase — warm-up procedure must precede human-facing deployment.

---

### Pitfall 8: Simultaneous Heterogeneous Agent Updates Cause Conflicting Gradients

**What goes wrong:**
When all piece agents (Rook, Cannon, Knight, etc.) are updated simultaneously from the same game trajectory, their gradient directions can conflict: the Rook agent pushes the shared board representation one way while the Cannon agent pushes it another. This leads to training instability, oscillating loss, and agents that never converge to cooperative strategies.

**Why it happens:**
Simultaneous policy gradient updates in cooperative multi-agent settings violate the stationarity assumption — each agent's update changes the environment seen by all other agents. The HARL framework (Heterogeneous-Agent RL) was specifically created to address this with sequential update ordering, providing theoretical convergence guarantees that simultaneous updates lack.

**How to avoid:**
- Use sequential update ordering: update agents in a fixed order (e.g., by piece value: King, Rook, Cannon, Knight, Horse, Elephant, Advisor, Pawn) rather than simultaneously
- Give each agent a fixed number of gradient steps before moving to the next agent
- Use separate optimizers per agent type — do not share optimizer state
- Monitor per-agent loss independently; if one agent's loss increases while others decrease, the update order needs adjustment

**Warning signs:**
- Total loss oscillates with period equal to number of agent types
- One agent type dominates action proposals (others effectively become no-ops)
- Per-agent loss curves are anti-correlated (when one improves, another degrades)

**Phase to address:** Multi-agent architecture phase — update scheme must be designed before training begins.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Single shared network for all piece types (parameter sharing) | Faster to implement | Prevents piece-specific specialization; homogenizes policies | Never — defeats purpose of heterogeneous architecture |
| Run training in main Qt thread | No threading complexity | GUI freezes, user experience destroyed | Never |
| Skip replay buffer for MVP | Simpler code | Catastrophic forgetting, no improvement trajectory visible | Never — online learning requires it |
| Hard-code draw on position repetition | Simpler rule engine | Incorrect Xiangqi rules, corrupted reward signal | Never |
| Use float64 for numerical stability | Avoids precision bugs | MPS does not support float64 — runtime crash on Apple Silicon | Never |
| Global learning rate for all agents | Fewer hyperparameters | Different piece types have different learning dynamics; one rate fits none | Acceptable only in earliest prototype |
| PYTORCH_ENABLE_MPS_FALLBACK=1 for unsupported ops | Unblocks development | Silent CPU fallback; training is slower than expected, hard to detect | Acceptable temporarily during development |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| PyTorch MPS | Using default PyTorch install without version pinning | Pin `torch>=2.4.0`, require macOS >= 15; verify with `torch.backends.mps.is_available()` at startup |
| PyQt6 + PyTorch | Passing tensors directly across thread boundary via signals | Pass Python primitives (float, int, list) via signals; tensors are not thread-safe across Qt signal/slot |
| Adam optimizer on MPS | Using Adam with default settings | Verify optimizer state tensors are contiguous; consider using `adamw` with `foreach=False` as safer alternative |
| Xiangqi move generation | Generating legal moves without checking for king-in-check after move | Always validate that the moving side's king is not in check after applying the move |
| Replay buffer sampling | Storing raw tensors in replay buffer on MPS device | Store experiences as CPU tensors (or numpy arrays) in the buffer; move to MPS only at training time |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `clip_grad_norm_()` MPS memory leak | Memory grows from 1GB to 7GB+ over 8 epochs; training slows dramatically | Monitor memory with Activity Monitor; detach losses (`float(loss)`); consider gradient clipping via `torch.nn.utils.clip_grad_value_` as fallback | After ~5–10 training epochs |
| Per-step training on every move | AI move latency > 500ms; GUI stutter | Batch lightweight updates every N moves; only run deep update at game end in worker thread | At game move 1 if training is not threaded |
| Attention with long sequences on MPS | OOM crash when board history > ~500 tokens | Cap board state history window; use fixed-size board representation rather than sequence model | Sequence length > 12,000 tokens (less relevant for board states) |
| Full game history in replay buffer (raw tensors) | RAM exhaustion after 1,000+ games | Store board state as compact integer array (numpy uint8); reconstruct tensor at sample time | After ~500 games if storing float32 tensors |
| Synchronous model save after every game | 2–5 second freeze at game end | Save model asynchronously in background thread or on QThread; notify UI when complete | Immediate — file I/O blocks main thread |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No visible indication that AI is learning | User cannot tell if the AI is getting stronger; the core value prop is invisible | Show a "strength meter" or ELO-like indicator that updates after each game; display win/loss trend |
| AI move takes >2 seconds | Game feels broken; user thinks application crashed | Show a "thinking" animation; cap AI inference to 500ms by limiting proposal generation |
| Catastrophic forgetting makes AI regress | User sees the AI get weaker after many games; deeply frustrating | Checkpoint system + rollback mechanism; never allow live weights to degrade below last checkpoint |
| Training visualization (loss curves) shown raw | Loss numbers are meaningless to non-ML users | Show win rate % trend instead of loss; optionally show piece strength as a radar chart |
| Drag-drop fails silently on illegal moves | User drops piece, nothing happens, no feedback | Show visual illegal-move flash (red highlight) and reset piece to origin with animation |

---

## "Looks Done But Isn't" Checklist

- [ ] **Xiangqi rules engine:** Often missing perpetual-check loss assignment — verify against at least 5 canonical perpetual-check positions from WXF manual
- [ ] **MPS training:** Often missing contiguous tensor check — verify `exp_avg_sq` is non-zero after step 10 in a unit test
- [ ] **Online learning:** Often missing replay buffer — verify that games from 50+ games ago still appear in training batches
- [ ] **Multi-agent update:** Often missing per-agent loss monitoring — verify each agent type's loss trends independently
- [ ] **Threading:** Often missing error propagation from worker thread — verify exceptions in training thread surface to UI rather than silently dying
- [ ] **Model save:** Often missing atomic write — verify save uses temp file + rename to prevent corrupted checkpoints on crash
- [ ] **Reward shaping:** Often missing ablation — verify shaped-reward agent outperforms no-shaping agent after 200 games
- [ ] **Arbitrator:** Often missing input validation — verify arbitrator receives full board state, not just proposal indices

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| MPS silent weight freeze discovered late | HIGH | Verify PyTorch version; add `.contiguous()` calls; reset optimizer state; restart training from last checkpoint |
| Xiangqi rules bug discovered after training | HIGH | Fix rule engine; invalidate all trained models (rules were wrong = reward was wrong); retrain from scratch |
| Catastrophic forgetting — agent regressed | MEDIUM | Roll back to last checkpoint where win rate was acceptable; check replay buffer ratio; reduce online learning rate |
| Reward hacking (piece-farming) | MEDIUM | Scale down shaping rewards by 10x; retrain from last checkpoint before hacking emerged |
| GUI freeze on training | LOW | Move training call to QThread; no retraining needed |
| Training cold-start (no learning signal) | LOW | Add self-play warm-up; increase epsilon; add auxiliary value target |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| MPS silent weight freeze | Phase 1: Environment & Hardware Setup | Unit test: verify optimizer state updates after 10 gradient steps |
| GUI freeze during training | Phase 2: UI + Game Loop | Integration test: board remains responsive during 50-step training loop |
| Xiangqi repetition rules bug | Phase 1: Rules Engine | Test suite: 10+ canonical perpetual-check/chase positions with correct outcomes |
| Arbitrator bottleneck | Phase 3: Multi-Agent Architecture | Ablation: arbitrator entropy must be > 0.5 after 100 games |
| Reward hacking | Phase 4: Reward Design | Comparison test: shaped vs unshaped agent after 200 games |
| Catastrophic forgetting | Phase 4: Online Learning Architecture | Long-run test: win rate against fixed opponent must be non-decreasing over 50 games |
| Cold-start no learning signal | Phase 4: Training Bootstrap | Warm-up check: average game length must exceed 30 moves after 100 self-play games |
| Simultaneous gradient conflicts | Phase 3: Multi-Agent Architecture | Monitor per-agent loss curves — must not be anti-correlated |

---

## Sources

- HARL framework paper: Heterogeneous-Agent Reinforcement Learning (sequential update ordering, theoretical grounding)
- PyTorch MPS non-contiguous tensor bug: PyTorch GitHub issues, PyTorch >= 2.4 release notes; confirmed for Adam `addcmul_`/`addcdiv_` on MPS < macOS 15
- MPS memory leak with `clip_grad_norm_`: PyTorch 2.7.0 on macOS 15.4 confirmed issue (community bug reports, March 2025)
- Xiangqi WXF repetition rules: "A Complete Algorithm for Ruling the WXF Repetition Rules" (2024 academic paper; +10 Elo from correct implementation)
- MAPPO/IPPO non-stationarity: Multi-Agent RL survey literature, CTDE pattern
- Reward hacking: Lilian Weng, "Reward Hacking in Reinforcement Learning" (2024); Fu et al., arXiv:2502.18770 (ICML 2025)
- Catastrophic forgetting in online RL: Replay buffer research, EWC, CLEAR framework
- PyQt6 threading: Qt documentation, Real Python QThread guide
- Self-play sparse reward: AlphaZero literature, policy collapse in REINFORCE with sparse rewards

---
*Pitfalls research for: Heterogeneous multi-agent RL Xiangqi platform (MPS, online learning, PyQt6)*
*Researched: 2026-03-19*
