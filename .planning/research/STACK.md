# Stack Analysis

**Domain:** Heterogeneous multi-agent RL predictive collaboration research pipeline
**Researched:** 2026-03-29
**Confidence:** HIGH (library versions verified via web search; integration points verified against existing codebase)

---

## Recommended Stack

### Category 1: Literature Collection Pipeline (EXISTING — no changes needed)

| Component | Version | Purpose | Status |
|-----------|---------|---------|--------|
| `dblp_search.py` | Existing | Broad DBLP API search (keyword x venue cartesian product) | **KEEP** — works for any keywords |
| `dblp_keywords_extract.py` | Existing | Fine-grained title filtering (nested AND/OR logic) | **KEEP** — flexible enough |
| `dblp_config.json` | Existing | Keywords, venues, API configuration | **MODIFY** — keyword content only |
| Python `requests` | Existing | HTTP client for DBLP/Semantic Scholar APIs | **KEEP** |
| Python `pandas` | Existing | CSV/Excel data manipulation | **KEEP** |
| Python `openpyxl` | Existing | Excel output for screening | **KEEP** |
| Python `tqdm` | Existing | Progress bars for long searches | **KEEP** |

**Rationale:** The existing pipeline is configuration-driven and domain-agnostic. Only keyword content changes. No new dependencies needed.

### Category 2: RL Training Frameworks (RESEARCH REFERENCE — for algorithm design)

| Framework | Version | Heterogeneous Support | Notes |
|-----------|---------|----------------------|-------|
| PettingZoo | 1.25.0 | Native: different obs/action spaces per agent | Best fit: already Gymnasium-compatible, parallel API supports heterogeneous agents |
| Ray RLlib | 2.40+ | Yes via multi-agent config | Heavy dependency, better for production scaling than research prototyping |
| PyMARL2 | Latest | QMIX-based, homogeneous by default | Reference implementation for value decomposition methods |
| EPyMARL | Latest | Supports QMIX, MAPPO, MADDPG | Lightweight PyTorch MARL framework, good for research |
| MAPPO implementation | Various | Policy-based CTDE | Simple, effective baseline for cooperative MARL |

**Recommendation:** For v1.0 research milestone, use existing XiangqiEnv (already Gymnasium-compatible). No new framework dependencies until algorithm design is finalized. Reference these frameworks for architectural patterns during analysis.

**What NOT to add:** Ray RLlib (too heavy for research phase), Stable-Baselines3 (homogeneous agent focus, no native multi-agent heterogeneous support).

### Category 3: Experiment Tracking (RESEARCH REFERENCE)

| Tool | Best For | Notes |
|------|----------|-------|
| TensorBoard | Local, lightweight | Already common in PyTorch ecosystem; zero setup |
| MLflow | Model registry + experiment tracking | Better for comparing hyperparameter sweeps |
| W&B (Weights & Biases) | Collaborative, cloud-based | Overkill for single researcher; good for sharing results |

**Recommendation:** Defer to implementation milestone. For research phase, markdown documents and CSV analysis are sufficient.

### Category 4: Key RL Algorithm References (for algorithm design phase)

| Algorithm | Type | Heterogeneous? | Key Feature |
|-----------|------|---------------|-------------|
| QMIX | Value-based CTDE | Limited (monotonicity constraint) | Mixing network for centralized training |
| QPLEX | Value-based CTDE | Better than QMIX | Duplex dueling, full IGM expressiveness |
| QTypeMix | Value-based CTDE | **Yes** — type-based decomposition | Handles different action spaces per agent type |
| MAPPO | Policy-based CTDE | Yes | Simple, effective, PPO-based |
| MADDPG | Actor-critic CTDE | Yes (continuous actions) | Centralized critic, decentralized actors |
| RODE | Role-based | **Yes** — role decomposition | Learns roles from action space structure |
| AIM | Agent modeling + QMIX | Partial — homogeneous teammates tested | Active inference portraits (perception-belief-action) |
| PR2 | Recursive reasoning | Homogeneous | Probabilistic recursive reasoning for opponent modeling |
| TARMAC | Attention + communication | Homogeneous | Targeted multi-agent communication |

**What NOT to use:** Vanilla QMIX as final algorithm (monotonicity constraint limits heterogeneous expressiveness). Instead, QTypeMix or QPLEX for value-based, MAPPO for policy-based.

### Category 5: Literature Management (optional, for future)

| Tool | Purpose | Notes |
|------|---------|-------|
| Zotero + pyzotero | Paper management, tagging, annotation | API-based; useful if collection grows beyond 200 papers |
| Semantic Scholar API | Abstracts, citations, recommendations | Already partially integrated in dblp_search.py |
| Google Scholar alerts | Ongoing monitoring for new papers | Complementary to DBLP search |

**Recommendation:** Not needed in v1.0 milestone. CSV-based screening is sufficient. Consider if collection grows beyond 200 papers.

---

## Integration Points

| New Component | Integrates With | How |
|---------------|----------------|-----|
| `dblp_config.json` (modified) | `dblp_search.py`, `dblp_keywords_extract.py` | JSON config read by both scripts |
| Future: algorithm prototype | `src/xiangqi/rl/env.py` | XiangqiEnv provides gym interface for training |
| Future: policy network | `src/xiangqi/ai/` | Replaces RandomAI with learned agent |

---

## What NOT to Add

| Component | Why Not |
|-----------|---------|
| Ray RLlib | Over-engineering for research phase; heavy dependency |
| Stable-Baselines3 | Homogeneous agent focus, no multi-agent heterogeneous support |
| Streamlit/Flask for screening | Over-engineering; CSV + Excel is sufficient |
| Zotero/pyzotero | Only useful for 200+ papers; current collection is smaller |
| Any new pip dependencies for v1.0 | The milestone is research-only; no code implementation |

---

*Stack analysis for: RL-Xiangqi v1.0 research pipeline — heterogeneous multi-agent RL predictive collaboration*
*Researched: 2026-03-29*
