# Feature Research

**Domain:** Heterogeneous Multi-Agent RL Chess System (Xiangqi / Chinese Chess)
**Researched:** 2026-03-19
**Confidence:** MEDIUM-HIGH

---

## Feature Landscape

### Table Stakes (Users Expect These)

These are the minimum required features. Missing any of them makes the product broken or unacceptable.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Complete Xiangqi rules engine | Any chess program must enforce legal moves; Xiangqi has unique rules (flying general, cannon capture, no jumping for horses/elephants, river restrictions, stalemate is a loss, no perpetual check) | HIGH | 7 piece types with distinct movement logic; flying general check and no-perpetual-check rules are non-trivial edge cases to detect |
| Check detection and checkmate/stalemate judgment | Game cannot proceed without win/loss/draw detection | HIGH | Flying general rule adds a dimension not present in Western chess; stalemate is a loss (not draw) in Xiangqi — different from Western chess |
| Legal move validation (UI side) | Users expect the board to reject illegal drags silently, not crash | MEDIUM | python-chess has no Xiangqi support; must implement from scratch or use pikafish/fairy-stockfish bindings |
| Drag-and-drop piece interaction | Standard expectation for any desktop board game UI | MEDIUM | PyQt6 mouse event handling; need to highlight valid drop targets to guide players |
| Visual board rendering with correct piece icons | The 9x10 intersection-based board (not squares) is visually distinct from Western chess | MEDIUM | Pieces sit on intersections, not inside squares; need custom SVG or image assets for Chinese piece characters |
| AI responds with a move | Core product: the AI must move | HIGH | Entire RL pipeline must be functional before this works |
| Game start / restart flow | Users expect a "new game" button | LOW | Simple state reset |
| Turn management | Alternating red/black turns, with turn indicator | LOW | Must prevent user from moving opponent's pieces |
| Move history display | Users need to review what happened; common in all chess UIs | MEDIUM | Can use a scrollable text log with algebraic-style notation for Xiangqi |
| Model persistence (save/load) | Progress must survive app restarts; critical for online learning value prop | MEDIUM | Save after each game; PyTorch `torch.save` / `torch.load` with versioning |

### Differentiators (Competitive Advantage)

These map directly to the core value proposition: observable AI improvement through online learning with a heterogeneous multi-agent architecture.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Heterogeneous agent architecture (per-piece-type networks) | The project's primary research differentiator; each piece type (General, Advisor, Elephant, Horse, Chariot, Cannon, Soldier) maintains its own policy network, exploiting the radically different move semantics per piece type | HIGH | 7 distinct network types; Chariot/Cannon/Soldier have very different action spaces; requires careful state representation per agent type |
| Proposal + arbitration coordination mechanism | Candidate moves from all piece-type agents are scored and arbitrated by a global network, enabling emergent cooperative strategy beyond greedy per-piece decisions | HIGH | Arbitrator architecture choice is critical: attention-based (treating proposals as tokens) or a simple scoring network; needs careful design to avoid the arbitrator dominating learning |
| Online learning during human play (real-time weight updates) | AI visibly improves across games played by the same user — the defining user experience | HIGH | Step-level lightweight updates (avoid freezing the UI) + end-of-game deep update batch; must run training in a background thread to keep UI responsive |
| Mixed update strategy (per-step + end-of-game) | Per-step shaping rewards accelerate learning; end-of-game batch update provides stable gradient signal | HIGH | Balance is tricky: too much per-step updating causes instability; too little makes online learning imperceptible |
| Shaped intermediate rewards (material capture, board control) | Sparse terminal rewards (win/loss only) make learning extremely slow; shaped rewards guide the agent toward meaningful positions faster | HIGH | Common shapes: piece-value delta on capture, center/river-crossing bonuses for soldiers, mobility (number of available moves). Must be calibrated to avoid reward hacking |
| Observable AI skill progression (metrics dashboard) | Users must be able to see the AI getting stronger — this is the core experiential promise | MEDIUM | Show win rate over last N games, average game length trend, episode loss curve. A simple matplotlib panel embedded in PyQt6 or a separate TensorBoard view |
| Apple Silicon MPS backend optimization | Enables the online training loop to be fast enough to run between/during moves on consumer hardware with no GPU | MEDIUM | PyTorch MPS backend; some ops fall back to CPU — identify and handle gracefully; MPS memory management differs from CUDA |
| Zero prior knowledge (learns from scratch) | Validates that the RL system works without human-game datasets or opening books — a cleaner scientific demonstration | MEDIUM | No corpus needed; random initialization; implies the early games will be very weak (this should be communicated to users as "watching the AI learn") |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Opening book / endgame tablebase | "The AI plays randomly in the opening" complaints | Contradicts the from-scratch learning premise; injecting hand-crafted knowledge pollutes the online learning experiment; creates complex initialization dependencies | Let the agent develop its own opening tendencies through repeated play; shape the experience narrative ("it's learning, not pre-programmed") |
| PGN / game record import | Users want to feed the AI human games for faster learning | Breaks the zero-prior-knowledge constraint; introduces distribution shift between human-game data and self-play data; scope creep | Train purely from human vs. AI games; the AI's experience is the data |
| Online multiplayer | Obvious extension request | Requires server infrastructure, authentication, matchmaking — an entirely different product; human vs. AI is the validated use case | Explicitly out of scope per PROJECT.md |
| Stockfish / external engine integration for analysis | "Tell me if my move was good" coaching feature | Requires pikafish (Xiangqi UCI engine); adds a large dependency; shifts focus from RL learning to analysis tool; competing product | Offer a simple "replay this game" view showing what the AI would do now vs. what it did then — intrinsic analysis using the trained model itself |
| Full MCTS search at inference time | "Make the AI stronger" | At online-learning scale on MPS hardware, adding MCTS at inference time makes the AI too slow to respond interactively; AlphaZero MCTS is designed for distributed training clusters | The heterogeneous proposal + arbitration mechanism IS the multi-agent equivalent of candidate selection; depth-1 look-ahead is acceptable for v1 |
| Real-time visualization updating every step | Cool-looking training graphs updating live | Per-step UI refresh causes heavy thread contention between training loop and Qt event loop; small updates are not meaningful noise-to-signal | Update metrics at end-of-game (or every N games); use a background queue to pass metrics to the UI thread |
| Mobile / web version | Broader reach | PyQt6 is desktop-only; MPS training requires macOS; porting is a full re-architecture | Explicitly out of scope per PROJECT.md |
| Adjustable AI difficulty slider | Common in chess apps | Requires either multiple trained models or policy temperature tuning; interferes with a single online-learning model that is continuously improving | Communicate strength via the metrics dashboard; the "difficulty" is organic and observable |
| Multi-game parallel self-play training | Faster learning | Requires parallel game environments and synchronous gradient accumulation; significant complexity for a single-machine MPS setup | Sequential games with experience replay buffer for replay diversity |

---

## Feature Dependencies

```
[Xiangqi Rules Engine]
    └──requires──> [Legal move generation per piece type]
                       └──requires──> [Board state representation (9x10 intersection model)]
                                          └──requires──> [Flying general detection]
                                          └──requires──> [No-perpetual-check detection]

[Heterogeneous Agent Networks]
    └──requires──> [Board state representation]
    └──requires──> [Per-piece-type action space definition]
                       └──requires──> [Legal move generation per piece type]

[Proposal + Arbitration Mechanism]
    └──requires──> [Heterogeneous Agent Networks]
    └──requires──> [Legal move generation per piece type]  (arbitrator must only select legal moves)

[Online Learning Loop]
    └──requires──> [Proposal + Arbitration Mechanism]
    └──requires──> [Shaped Intermediate Rewards]
                       └──requires──> [Board state representation]
    └──requires──> [Model Persistence]

[PyQt6 UI — Board + Interaction]
    └──requires──> [Board state representation]
    └──requires──> [Legal move validation]

[Drag-and-Drop + Legal Move Highlighting]
    └──requires──> [PyQt6 UI — Board + Interaction]
    └──requires──> [Legal move generation per piece type]

[Observable Metrics Dashboard]
    └──requires──> [Online Learning Loop]  (needs metrics to display)
    └──enhances──> [Online Learning Loop]  (makes the value prop visible)

[MPS Backend Optimization]
    └──enhances──> [Online Learning Loop]  (makes per-step training feasible on Apple Silicon)

[Model Persistence]
    └──requires──> [Online Learning Loop]  (nothing to save without training)
```

### Dependency Notes

- **Xiangqi Rules Engine is the root dependency**: everything — UI, RL, agents — depends on a correct rule implementation. It must be built and fully tested before any other work begins.
- **Board state representation blocks heterogeneous agents**: the representation must encode piece positions in a form each agent network can consume (likely a multi-channel 9x10 tensor, one channel per piece type per side).
- **Legal move generation per piece type is shared**: both the UI (for drag validation and highlighting) and the arbitration mechanism (to constrain legal proposals) depend on the same move generator. Build it once as a shared service.
- **Online Learning Loop requires background threading**: the Qt event loop and the PyTorch training loop must not share the main thread. This is an architectural constraint, not just a feature dependency.
- **Observable Metrics enhances the core value prop**: technically optional for v1 functionality, but critical for demonstrating the learning narrative to users. Treat as required for MVP.

---

## MVP Definition

### Launch With (v1)

Minimum viable product to validate the core thesis: heterogeneous multi-agent online RL learns Xiangqi from scratch while playing against a human.

- [ ] Complete Xiangqi rules engine with all 7 piece types — game cannot function without it
- [ ] PyQt6 board UI with drag-and-drop, turn management, legal move highlighting — human interaction layer
- [ ] Heterogeneous agent networks (7 piece-type networks + arbitrator) producing a move — the differentiating architecture
- [ ] Proposal + arbitration mechanism selecting the AI's move — must work before any training can happen
- [ ] Shaped intermediate rewards (capture delta + basic position score) — required for online learning to converge in reasonable time
- [ ] Online learning loop: per-step lightweight update + end-of-game batch update — the core value proposition
- [ ] MPS backend — the only GPU-like hardware available; CPU training will be too slow for per-step updates
- [ ] Model save/load on game end — persistence required for observable improvement across sessions
- [ ] Basic metrics panel (win rate over last N games, episode reward trend) — makes the learning observable; without this the core value prop is invisible to the user

### Add After Validation (v1.x)

- [ ] Move history display — add once gameplay loop is stable; users will ask for it
- [ ] Replay / game review using trained model — provides intrinsic analysis without needing Stockfish
- [ ] Experience replay buffer for training stability — add when catastrophic forgetting becomes observable (it will)
- [ ] Loss curve / gradient norm display — add when users or developers want deeper training insight
- [ ] Piece-level contribution visualization (which agent proposed the winning move) — showcases the heterogeneous architecture to curious users

### Future Consideration (v2+)

- [ ] Self-play mode (AI vs. AI) for accelerated offline pre-training — defer until online learning convergence is validated
- [ ] Policy temperature / exploration scheduling — defer until training stability is established
- [ ] Curriculum learning (start with simplified board configurations) — defer; adds complexity before baselines are measured
- [ ] Export trained model for benchmarking against pikafish/fairy-stockfish — defer until model is strong enough to be meaningful

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Xiangqi rules engine (full) | HIGH | HIGH | P1 |
| PyQt6 board UI + drag-and-drop | HIGH | MEDIUM | P1 |
| Heterogeneous agent networks (7 types) | HIGH | HIGH | P1 |
| Proposal + arbitration mechanism | HIGH | HIGH | P1 |
| Online learning loop (per-step + end-of-game) | HIGH | HIGH | P1 |
| MPS backend | HIGH | MEDIUM | P1 |
| Model save/load | HIGH | LOW | P1 |
| Shaped intermediate rewards | HIGH | MEDIUM | P1 |
| Observable metrics dashboard | HIGH | MEDIUM | P1 |
| Turn management + legal move highlighting | MEDIUM | LOW | P1 |
| Move history display | MEDIUM | LOW | P2 |
| Experience replay buffer | MEDIUM | MEDIUM | P2 |
| Replay / game review | MEDIUM | MEDIUM | P2 |
| Piece-level contribution visualization | MEDIUM | MEDIUM | P2 |
| Self-play offline pre-training | LOW | HIGH | P3 |
| Curriculum learning | LOW | HIGH | P3 |
| Stockfish integration for analysis | LOW | MEDIUM | P3 (anti-feature risk) |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | AlphaZero-style systems (e.g., Leela, pikafish) | Maia Chess (human-like) | This System |
|---------|------------------------------------------------|------------------------|-------------|
| Architecture | Single monolithic policy-value network | Single transformer network | 7 heterogeneous piece-type networks + arbitrator |
| Training data source | Large-scale self-play (distributed) | 91M human games (Lichess) | Zero prior data; online human vs. AI games only |
| Inference-time search | MCTS (required for strength) | None (network only) | None at v1; proposal + arbitration as substitute |
| Online/incremental learning | No (offline batch training) | No (static trained model) | Yes — updates during each game |
| Observable learning progression | No (static strength) | No (static model) | Yes — metrics dashboard tracks improvement |
| Target hardware | TPU/GPU clusters | GPU server | MacBook Pro M1 Max MPS |
| Xiangqi-specific | pikafish: yes. Most others: no | No | Yes |

---

## Sources

- arXiv:2509.19512 — Heterogeneous Multi-Agent Challenge (HeMARL)
- arXiv:2304.09870 — Heterogeneous-Agent Reinforcement Learning
- arXiv:2410.04865 — Mastering Chinese Chess AI (Xiangqi) Without Search
- arXiv:2501.11818 — Group-Agent Reinforcement Learning with Heterogeneous Agents
- IJCAI 2024 M2RL Framework: https://www.ijcai.org/proceedings/2024/1046
- Chessformer (OpenReview 2025) — attention-based board token model
- Xiangqi rules reference: standard rule documentation (HIGH confidence, stable)
- MIT 2025 study: RL minimizes catastrophic forgetting vs. supervised fine-tuning
- PyQt chess desktop patterns: PyQtChess, MzChess, CARA projects (HIGH confidence — directly observed codebases)
- Dense reward signals for chess RL (arXiv 2025) — Stockfish-distilled dense rewards outperform sparse binary rewards
- NeurIPS 2024 — Successor Features and representation collapse in RL

---

*Feature research for: Heterogeneous Multi-Agent RL Xiangqi System*
*Researched: 2026-03-19*
