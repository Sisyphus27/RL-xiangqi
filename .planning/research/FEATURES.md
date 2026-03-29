# Feature Analysis

**Domain:** Heterogeneous multi-agent RL predictive collaboration
**Researched:** 2026-03-29
**Confidence:** HIGH (based on AIM paper analysis and MARL literature survey; algorithm-specific details at MEDIUM confidence where noted)

---

## Feature Categories

### Category 1: Literature Collection Pipeline

#### Table Stakes

| Feature | Description | Complexity | Depends On |
|---------|-------------|------------|------------|
| Two-stage keyword design | Broad search (Stage 1) + refined extraction (Stage 2) for MARL domain | LOW | Understanding of MARL terminology |
| MARL-focused search keywords | Replace hypergraph/traffic keywords with multi-agent RL keywords | LOW | AIM paper domain analysis |
| Heterogeneous agent keyword coverage | Keywords that capture heterogeneity, diversity, role-based MARL | LOW | Domain knowledge of terminology variants |
| Predictive collaboration keyword coverage | Keywords for teammate modeling, active inference, belief tracking | LOW | AIM paper technical terms |
| Venue selection | ML/AI venues (existing) + AAMAS for multi-agent work | LOW | None |

#### Differentiators

| Feature | Description | Complexity | Depends On |
|---------|-------------|------------|------------|
| Keyword iteration loop | Systematic refinement based on screening feedback | MEDIUM | Initial screening results |
| Cross-reference discovery | Finding related papers via citation chains | LOW | Included papers' reference lists |

#### Research Notes
- The existing pipeline (dblp_search.py + dblp_keywords_extract.py) is domain-agnostic and works via configuration
- Only `dblp_config.json` keyword content needs changing
- The AIM paper provides the anchor: terms like "active inference", "teammate portrait", "perception-belief-action" define the core vocabulary
- Key synonym groups: {cooperative, collaborative}, {heterogeneous, diverse, diverse agents}, {teammate modeling, agent modeling, opponent modeling}

---

### Category 2: Active Inference for Teammate Modeling

#### Table Stakes

| Feature | Description | Complexity | Depends On |
|---------|-------------|------------|------------|
| Perception portrait | Model what teammates observe from own perspective | HIGH | Viewpoint transformation |
| Belief portrait | Model teammates' higher-level understanding | HIGH | Variational inference, latent space |
| Action portrait | Predict teammates' actions as posterior validation | MEDIUM | Belief + perception portraits |
| Dual filter mechanism | Select accurate and relevant teammates for collaboration | MEDIUM | Accuracy scoring, attention mechanism |

#### Differentiators

| Feature | Description | Complexity | Depends On |
|---------|-------------|------------|------------|
| Perspective transformation | Recalculate positions relative to each teammate's viewpoint | HIGH | Existing board state representation |
| Mutual evaluation consistency | Symmetric accuracy scores between agent pairs | MEDIUM | Perception portrait quality |
| Dynamic teammate selection | Choose top-k collaborators based on context | MEDIUM | Accuracy + relevance filters |

#### Research Notes
- AIM paper tested on SMAC, SMACv2, MPE, GRF — all homogeneous agents
- **Key challenge for our domain:** Chinese chess has 7 heterogeneous piece types with fundamentally different action spaces
- Perception portrait relies on observation overlap — in chess, all agents share the same board state but may have different "relevant" subsets
- The belief portrait uses reparameterized Gaussian — stability is critical (cosine similarity loss L_cn)
- AIM's limitation: fixed top-k teammate selection; dynamic selection is open problem

---

### Category 3: Heterogeneous Agent Collaboration

#### Table Stakes

| Feature | Description | Complexity | Depends On |
|---------|-------------|------------|------------|
| Different action spaces per agent | 7 piece types with different legal move sets | DONE (v0.3) | XiangqiEnv |
| Per-piece-type action masking | Filter illegal moves per agent type | DONE (v0.3) | XiangqiEnv |
| Heterogeneous parameter handling | Different network architectures or shared networks with type indication | HIGH | Parameter sharing strategy |
| Credit assignment | Attribute team reward to individual heterogeneous agents | HIGH | Value decomposition method |

#### Differentiators

| Feature | Description | Complexity | Depends On |
|---------|-------------|------------|------------|
| Type-aware parameter sharing | Share parameters within same piece type, separate across types | MEDIUM | Agent grouping strategy |
| Agent indication encoding | Concatenate agent type/ID to observation | LOW | Observation space design |
| Role-based decomposition | Automatically discover roles (attack/defense/support) from piece types | HIGH | RODE-style decomposition |
| Kaleidoscope networks | Symmetric weight sharing for equivalent agent types | MEDIUM | Network architecture |

#### Research Notes
- Our 7 piece types naturally provide heterogeneous groups: King (1), Advisor (2), Elephant (2), Horse (2), Chariot (2), Cannon (2), Soldier (5)
- Parameter sharing strategies: (1) No sharing — 16 separate networks; (2) Type-based sharing — 7 networks; (3) Full sharing with type indication — 1 network; (4) Hybrid — group by similarity
- QMIX monotonicity constraint may limit heterogeneous expressiveness — QTypeMix addresses this
- Flat Discrete(8100) action space with masking (v0.3 approach) is compatible with most value decomposition methods

---

### Category 4: Non-Communication Teammate Prediction

#### Table Stakes

| Feature | Description | Complexity | Depends On |
|---------|-------------|------------|------------|
| Local observation-based modeling | Infer teammate behavior from own observations only | HIGH | Observation design |
| Policy prediction | Predict teammate's action distribution | HIGH | Opponent/teammate modeling |
| Belief tracking | Maintain belief state about teammates over time | HIGH | RNN/GRU for temporal modeling |

#### Differentiators

| Feature | Description | Complexity | Depends On |
|---------|-------------|------------|------------|
| Theory of Mind reasoning | Higher-order belief tracking (what A thinks B thinks) | VERY HIGH | Recursive reasoning depth |
| Recursive reasoning (PR2) | Probabilistic recursive reasoning about others' policies | HIGH | PR2 framework adaptation |
| Ad-hoc teamwork | Collaborate with previously unseen teammates | VERY HIGH | Zero-shot coordination |
| Active inference integration | Combine perception-belief-action with heterogeneous agents | VERY HIGH | AIM + heterogeneous adaptation |

#### Research Notes
- Communication-free is critical for our domain: chess pieces don't "communicate" during play
- AIM framework is the primary reference but assumes homogeneous agents
- PR2 framework provides recursive reasoning but also tested on homogeneous agents
- Ad-hoc teamwork literature may provide insights for handling diverse piece types
- The key open question: how to extend active inference portraits to agents with fundamentally different action spaces

---

### Category 5: Algorithm Design Methodology

#### Table Stakes

| Feature | Description | Complexity | Depends On |
|---------|-------------|------------|------------|
| CTDE framework | Centralized training with decentralized execution | MEDIUM | QMIX/MAPPO backbone |
| Value decomposition | Factor joint Q-value into per-agent contributions | MEDIUM | Base algorithm selection |
| Reward shaping | Design reward signal for cooperative play | MEDIUM | Existing material + outcome rewards |

#### Differentiators

| Feature | Description | Complexity | Depends On |
|---------|-------------|------------|------------|
| Heterogeneous-aware mixing | Type-conditioned mixing network instead of uniform | HIGH | QTypeMix pattern |
| Cooperative reward bonus | Additional reward for successful collaboration patterns | MEDIUM | Team coordination metrics |
| Curriculum learning | Progressive difficulty from simple to complex collaboration | HIGH | Training schedule design |

#### Research Notes
- v0.3 already has material + outcome reward shaping
- The algorithm design depends entirely on what the literature analysis reveals
- Must wait for user's paper screening before proposing specific algorithm

---

## Feature Prioritization for v1.0

This is a **research milestone** — no code implementation. Features are research deliverables:

1. **Keyword design** (Phase 1) — Config-only, immediate
2. **Paper collection** (Phase 2) — Run existing scripts with new config
3. **Manual screening** (Phase 3) — Human workflow, user-driven
4. **Technical analysis** (Phase 4) — Per-paper analysis + synthesis
5. **Algorithm design** (Phase 5) — Final deliverable: algorithm specification document

---

*Feature analysis for: RL-Xiangqi v1.0 research pipeline — heterogeneous multi-agent RL predictive collaboration*
*Researched: 2026-03-29*
