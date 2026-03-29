# Phase 14: MARL Keyword Design - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Redesign `dblp_config.json` content with MARL-domain keywords, replacing the current hypergraph/traffic keywords. The existing scripts (`dblp_search.py`, `dblp_keywords_extract.py`) are untouched — only the JSON config file content changes. This phase delivers a ready-to-run keyword configuration that produces targeted search results via the existing two-stage pipeline.

</domain>

<decisions>
## Implementation Decisions

### Stage 1: Broad Search Keywords
- **D-01:** Scope is MARL core terminology anchored by the AIM paper (Wu et al., 2025) — not the full breadth of MARL literature
- **D-02:** ~25 keywords organized into 5 semantic groups:
  - **MARL Core:** multi-agent reinforcement learning, multi-agent RL, MARL, cooperative multi-agent, decentralized execution, CTDE
  - **Heterogeneous & Roles (EXPANDED — main innovation point):** heterogeneous agent, heterogeneous multi-agent, agent diversity, asymmetric agents, type-aware, role-based, diverse agent
  - **Modeling & Inference:** teammate modeling, opponent modeling, active inference, Theory of Mind, belief tracking, agent modeling
  - **Value Decomposition & Policy:** value decomposition, credit assignment, MAPPO, QMIX
  - **Collaboration & Communication:** communication-free, ad-hoc teamwork, cooperative coordination
- **D-03:** Heterogeneous keywords expanded from 3 to 7 — this is the primary future innovation direction and needs maximum recall

### Stage 2: Refined Extraction Keywords
- **D-04:** 6 AND/OR topic groups — groups joined by AND (paper must hit multiple groups), terms within each group joined by OR (synonym variants)
  - **Group 1 — MARL Core:** multi-agent reinforcement learning | multi-agent RL | MARL
  - **Group 2 — Cooperation/Coordination:** cooperative | collaborative | coordination
  - **Group 3 — Heterogeneity/Diversity:** heterogeneous | diverse | asymmetric | type-aware | role-based | different action space
  - **Group 4 — Modeling/Inference:** teammate modeling | opponent modeling | agent modeling | active inference | Theory of Mind | belief
  - **Group 5 — Execution/Training:** decentralized | CTDE | value decomposition | policy gradient | credit assignment
  - **Group 6 — Application Scenario:** game | board game | StarCraft | planning | scheduling | robot
- **D-05:** Group 3 (Heterogeneity) has the richest synonym coverage to maximize recall for the innovation area

### Venue & Year Configuration
- **D-06:** Keep all 18 existing venues + add AAMAS + JAAMAS (total ~20 venues)
- **D-07:** Year range narrowed to 2024-2026 (from previous 2020-2026)
- **D-08:** Retain existing API, pagination, and termination settings unchanged

### Claude's Discretion
- Exact keyword ordering and deduplication within config
- Whether to use wildcard-style matching (e.g., "heterogeneous*" — depends on DBLP API behavior)
- Fine-tuning of sleep_time, jitter, and retry settings if needed for calibration test run
- Formatting of Stage 2 nested AND/OR structure in JSON

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Core Domain Anchor
- `papers/Wu 等 - 2025 - Think How Your Teammates Think Active Inference Can Benefit Decentralized Execution.md` — The AIM paper; anchors all terminology and defines the research scope

### Configuration Target
- `paper_collect/dblp_config.json` — The single file being modified; current hypergraph/traffic keywords serve as structural reference

### Pipeline Scripts (READ ONLY — do not modify)
- `paper_collect/dblp_search.py` — Stage 1 broad search; keyword x venue Cartesian product search against DBLP API
- `paper_collect/dblp_keywords_extract.py` — Stage 2 refined extraction; nested AND/OR keyword matching on paper titles

### Research Context
- `.planning/research/SUMMARY.md` — Full research summary including keyword calibration targets (~5000-10000 broad, ~100-300 refined)
- `.planning/research/FEATURES.md` — Feature analysis with synonym groups and keyword design guidance
- `.planning/REQUIREMENTS.md` — LIT-01, LIT-02, LIT-03 requirements for this phase
- `.planning/ROADMAP.md` — Phase 14 success criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `dblp_config.json`: Already has the exact JSON structure needed — `search.default_keywords`, `search.default_venues`, `extract.default_keywords` sections. Only content values change.
- `dblp_search.py`: Reads `search.default_keywords` and `search.default_venues` for Cartesian product queries. Handles pagination, rate limiting, retry, DOI deduplication automatically.
- `dblp_keywords_extract.py`: Reads `extract.default_keywords` for nested AND/OR extraction. Supports Level 2 (2D) nesting: `[[group1_synonyms], [group2_synonyms]]` where group-inner is OR, group-inter is AND.

### Established Patterns
- Keywords are matched against paper **titles** (not abstracts) in Stage 2 — this limits precision but is fast
- Stage 1 searches DBLP by keyword + venue combination — broader terms produce more results
- The pipeline is idempotent — DOI deduplication means re-running doesn't create duplicates
- Config has `abstract_apis.semantic_scholar.enable: false` — abstracts not fetched (can be enabled for future phases)

### Integration Points
- New keywords go into `search.default_keywords` (Stage 1) and `extract.default_keywords` (Stage 2)
- New venues go into `search.default_venues`
- Year range via `search.start_year` and `search.end_year`
- No other files need modification

</code_context>

<specifics>
## Specific Ideas

- User emphasized heterogeneous agents as the **primary future innovation point** — keyword design should prioritize maximum recall in this area
- AIM paper's Related Works section provides a rich source of verified terminology and author names that could be used as additional keyword signals
- The year range 2024-2026 targets very recent work — this is intentional to capture the cutting edge of active inference + heterogeneous MARL research

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---
*Phase: 14-marl-keyword-design*
*Context gathered: 2026-03-29*
