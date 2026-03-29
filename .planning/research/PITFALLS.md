# Pitfalls Analysis

**Domain:** Heterogeneous multi-agent RL predictive collaboration research pipeline
**Researched:** 2026-03-29
**Confidence:** HIGH (based on MARL literature survey and AIM paper analysis)

---

## Pitfall Categories

### Category 1: Heterogeneous MARL Pitfalls

#### Pitfall 1.1: QMIX Monotonicity Limiting Heterogeneous Expressiveness

**Warning sign:** Using vanilla QMIX for agents with fundamentally different capabilities
**Impact:** The monotonicity constraint prevents the mixing network from learning that some agents' actions should be negatively valued (e.g., a defensive piece making an aggressive move)
**Prevention:** Use QTypeMix (type-based mixing) or QPLEX (full IGM expressiveness) that can represent negative individual contributions
**Phase to address:** Phase 5 (algorithm design) — select base algorithm that supports heterogeneous agents

#### Pitfall 1.2: Action Space Mismatch Between Agent Types

**Warning sign:** Treating all agents as having the same action space despite different capabilities
**Impact:** Agents waste capacity learning to ignore illegal actions; parameter sharing across types becomes harmful
**Prevention:** Our v0.3 already handles this with flat Discrete(8100) + per-piece-type masking. For algorithm design, consider type-specific output heads or separate policy networks per type group
**Phase to address:** Phase 5 — algorithm architecture design

#### Pitfall 1.3: Credit Assignment with Heterogeneous Contributions

**Warning sign:** Equal credit distribution when agent contributions are inherently unequal (e.g., Chariot vs Soldier)
**Impact:** Under-performing agents receive same reward signal, no incentive for specialized role learning
**Prevention:** Use value decomposition methods that compute individual Q-values; consider importance weighting based on piece value or role
**Phase to address:** Phase 5 — reward and value decomposition design

#### Pitfall 1.4: Parameter Sharing Failures Across Different Agent Types

**Warning sign:** Full parameter sharing between King and Chariot networks
**Impact:** Network capacity wasted on reconciling fundamentally different action patterns; degraded performance for all agent types
**Prevention:** Type-based parameter sharing (7 networks for 7 piece types) or agent indication encoding (concatenate piece type ID to observation). Research Kaleidoscope networks for structurally similar types
**Phase to address:** Phase 5 — network architecture design

---

### Category 2: Teammate Modeling Pitfalls

#### Pitfall 2.1: Modeling Errors Propagating Through Belief Updates

**Warning sign:** Noisy belief portraits degrading decision quality over multiple steps
**Impact:** Accumulated errors in teammate belief state lead to increasingly poor collaboration decisions
**Prevention:** AIM uses cosine similarity loss (L_cn) to enforce belief stability across time steps. Include explicit belief regularization. Monitor belief drift during training
**Phase to address:** Phase 5 — belief portrait training stability design

#### Pitfall 2.2: Fixed Teammate Parameters Limiting Team Optimization

**Warning sign:** Freezing modeled teammate policies during training (OMG-style)
**Impact:** Upper bound on collaboration efficiency; team cannot discover more optimal joint policies
**Prevention:** All agents should be trainable simultaneously. AIM models teammates' inference process, not fixed policies. This is a key design choice
**Phase to address:** Phase 5 — training procedure design

#### Pitfall 2.3: Partial Observability Cascading Into Modeling Inaccuracy

**Warning sign:** Perception portrait based on incomplete observation overlap
**Impact:** Agent models teammate based on wrong observation, leading to incorrect belief and action predictions
**Prevention:** AIM's accuracy filter (dual filter mechanism) addresses this. In chess, all agents share full board state (fully observable), so this is less of a concern
**Phase to address:** Phase 5 — may be less relevant for fully observable chess domain

#### Pitfall 2.4: Over-Reliance on Modeled Teammates

**Warning sign:** Agent follows modeled teammate belief even when own observation contradicts it
**Impact:** Blind spots where agent's own superior information is ignored in favor of potentially stale teammate model
**Prevention:** Belief fusion should be weighted by accuracy scores; own observation should always have highest weight. AIM's self-evaluation-is-highest property (diagonal loss L_se) enforces this
**Phase to address:** Phase 5 — attention/fusion mechanism design

---

### Category 3: Active Inference MARL Pitfalls

#### Pitfall 3.1: Belief Instability in Sequential Decision-Making

**Warning sign:** Belief portrait oscillating wildly between time steps
**Impact:** Unstable beliefs provide no useful signal for decision-making; training diverges
**Prevention:** AIM uses temporal consistency loss (cosine similarity between consecutive beliefs). Monitor belief variance during training. Consider KL divergence regularization for belief distribution
**Phase to address:** Phase 5 — training loss design

#### Pitfall 3.2: Scaling to Many Heterogeneous Agent Types

**Warning sign:** NxN perception evaluation matrix becomes computationally expensive for 16 agents
**Impact:** Training slowdown; memory bottleneck for large agent counts
**Prevention:** In chess, we have 16 pieces per side but only 7 types. Use type-based grouping to reduce NxN to 7x7 evaluation. Dual filter's top-k selection also limits computational cost
**Phase to address:** Phase 5 — computational efficiency design

#### Pitfall 3.3: Observation Representation Mismatch

**Warning sign:** Using AIM's viewpoint transformation directly on 16-channel AlphaZero board planes
**Impact:** Viewpoint transformation designed for relative-position features (SMAC/MPE); may not make sense for full board state where all agents see the same board
**Prevention:** In chess, the board is fully observable — all agents see the same state. The "perception portrait" for our domain may be simpler: instead of viewpoint transformation, use attention over which board regions are relevant to which piece type. This is a key adaptation needed
**Phase to address:** Phase 5 — observation/perspective adaptation design

---

### Category 4: Literature Search Keyword Pitfalls

#### Pitfall 4.1: Too Broad Keywords Returning Noise

**Warning sign:** "multi-agent" alone returns 50,000+ papers across all domains
**Impact:** Screening burden becomes overwhelming; relevant papers buried in noise
**Prevention:** Stage 1 keywords should be broad but domain-scoped (e.g., "multi-agent reinforcement learning" not just "multi-agent"). Stage 2 extract keywords use AND logic to narrow. Target: Stage 1 produces ~5000-10000 papers; Stage 2 filters to ~100-300 for manual screening
**Phase to address:** Phase 1 — keyword design

#### Pitfall 4.2: Too Narrow Keywords Missing Relevant Work

**Warning sign:** Only searching for exact term "active inference" in MARL context
**Impact:** Missing related work in "teammate modeling", "opponent modeling", "Theory of Mind", "recursive reasoning" that uses different terminology for similar concepts
**Prevention:** Use synonym groups in extract keywords. Check reference lists of included papers for missed work
**Phase to address:** Phase 1 — keyword design; iterate in Phase 3

#### Pitfall 4.3: Missing Domain-Specific Terminology Variants

**Warning sign:** Only using "cooperative" but not "collaborative", "collaboration", "coordination"
**Impact:** Missing papers that use different terminology for the same concept
**Prevention:** Exhaustive synonym expansion in Stage 2 extract keywords. Key synonym groups:
- {cooperative, collaborative, collaboration, coordination, teamwork}
- {heterogeneous, diverse, diverse agents, agent diversity, multi-type}
- {teammate modeling, agent modeling, opponent modeling, partner modeling}
- {prediction, inference, forecasting, anticipation}
- {communication-free, non-communication, no communication, silent}
**Phase to address:** Phase 1 — keyword design

#### Pitfall 4.4: Stale or Incorrect Venue Selection

**Warning sign:** Missing AAMAS (primary multi-agent conference) from venue list
**Impact:** Missing the most relevant venue for multi-agent RL research
**Prevention:** Add `aamas` to venue list. Consider adding `ec` (Economics and Computation) for specialized multi-agent work
**Phase to address:** Phase 1 — keyword/venue design

---

### Category 5: Algorithm Design Pitfalls for Chess Heterogeneous MARL

#### Pitfall 5.1: Sparse Reward in Chess-Like Games

**Warning sign:** Only using win/loss/draw as reward signal
**Impact:** Very sparse signal for learning collaborative patterns; training requires millions of games
**Prevention:** v0.3 already has material reward shaping. For collaboration, consider additional shaping: reward for piece coordination (e.g., pieces covering each other), strategic positioning bonuses
**Phase to address:** Phase 5 — reward design

#### Pitfall 5.2: Exploration Challenges with Heterogeneous Agents

**Warning sign:** King explores the same way as Chariot; Soldier explores the same as Cannon
**Impact:** Inefficient exploration — some pieces need conservative exploration (King), others aggressive (Chariot)
**Prevention:** Consider type-specific exploration parameters or intrinsic motivation bonuses scaled by piece type. Use entropy regularization with type-dependent coefficients
**Phase to address:** Phase 5 — exploration strategy design

#### Pitfall 5.3: Multiple Loss Terms Causing Training Instability

**Warning sign:** AIM has 6+ loss terms (L_TD + L_mi + L_cn + L_ce + L_sy + L_se) that may conflict
**Impact:** Loss balancing is critical; wrong weights cause training collapse or suboptimal convergence
**Prevention:** Start with simplest loss configuration; add complexity incrementally. Use careful hyperparameter search for loss weights. Monitor individual loss curves
**Phase to address:** Phase 5 — training procedure design

#### Pitfall 5.4: Premature Algorithm Commitment

**Warning sign:** Designing the full algorithm before completing literature analysis
**Impact:** Locking into a suboptimal approach; missing better techniques discovered during analysis
**Prevention:** This is exactly why v1.0 is research-first. The algorithm design (Phase 5) must wait until paper screening (Phase 3) and analysis (Phase 4) are complete. Do not skip ahead
**Phase to address:** Enforce phase ordering — Phase 5 strictly depends on Phase 4 output

---

## Prevention Priority Matrix

| Pitfall | Likelihood | Impact | Prevention Effort | Priority |
|---------|-----------|--------|-------------------|----------|
| 1.1 QMIX monotonicity | HIGH | HIGH | LOW (choose different base) | **Critical** |
| 4.1 Too broad keywords | HIGH | MEDIUM | LOW (careful keyword design) | **High** |
| 4.3 Missing terminology | MEDIUM | MEDIUM | LOW (synonym expansion) | **High** |
| 3.3 Observation mismatch | HIGH | HIGH | MEDIUM (adapt perception portrait) | **Critical** |
| 2.1 Belief error propagation | MEDIUM | HIGH | MEDIUM (regularization) | **High** |
| 5.3 Training instability | MEDIUM | HIGH | MEDIUM (incremental loss) | **High** |
| 5.4 Premature commitment | MEDIUM | HIGH | LOW (enforce phase ordering) | **High** |
| 1.4 Parameter sharing | LOW | MEDIUM | LOW (type-based sharing) | Medium |
| 5.1 Sparse reward | LOW | MEDIUM | LOW (already addressed) | Low |

---

*Pitfalls analysis for: RL-Xiangqi v1.0 research pipeline — heterogeneous multi-agent RL predictive collaboration*
*Researched: 2026-03-29*
