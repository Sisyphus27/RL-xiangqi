# Project Research Summary

**Project:** RL-Xiangqi v1.0 -- Heterogeneous Multi-Agent RL Predictive Collaboration
**Domain:** Academic research pipeline (literature survey + algorithm design)
**Researched:** 2026-03-29
**Confidence:** HIGH

---

## Executive Summary

RL-Xiangqi v1.0 is a research-only milestone that extends an existing Chinese chess (Xiangqi) multi-agent RL environment into the domain of heterogeneous agent predictive collaboration. The project sits at the intersection of multi-agent reinforcement learning, active inference for teammate modeling, and heterogeneous agent coordination. Experts approach this kind of research through a disciplined literature pipeline: systematic keyword-driven search, manual screening, deep technical analysis, and then algorithm synthesis. The existing codebase already provides a mature Gymnasium environment (XiangqiEnv) with 7 heterogeneous piece-type agents, flat Discrete(8100) action space with per-piece-type masking, and material-plus-outcome reward shaping -- all from the v0.3 milestone. The research phase builds on top of a working DBLP search pipeline (`dblp_search.py` + `dblp_keywords_extract.py`) that is configuration-driven and domain-agnostic, meaning only keyword content needs to change.

The recommended approach is a five-phase sequential pipeline where only the first phase involves any code change (a single JSON config file), and the remaining four phases are human-driven research work. The AIM paper (Wu et al., 2025) anchors the domain: its active inference portraits (perception-belief-action) provide the conceptual framework, but critically, AIM was tested only on homogeneous agents. The central research challenge is adapting active inference teammate modeling to agents with fundamentally different action spaces -- a King moves one step, a Chariot moves across the board. Algorithm options include QTypeMix (type-based value decomposition), MAPPO (policy-based CTDE), or a novel hybrid that incorporates AIM's belief portraits into a heterogeneous-aware architecture.

The key risks are: (1) keyword design that is too broad or too narrow, either overwhelming screening or missing relevant work -- mitigated by a two-stage broad-then-fine keyword pipeline with synonym expansion and iterative refinement; (2) premature algorithm commitment before literature analysis is complete -- mitigated by strict phase ordering where algorithm design is the final phase; and (3) the observation representation mismatch -- AIM's viewpoint transformation was designed for partially observable domains with relative-position features, but chess is fully observable with all agents seeing the same board, so the "perception portrait" concept needs fundamental adaptation.

---

## Key Findings

### Recommended Stack

The v1.0 milestone requires no new software dependencies. The existing Python stack (requests, pandas, openpyxl, tqdm) powers a configuration-driven DBLP search pipeline that is already built and tested. Only `dblp_config.json` content changes. RL frameworks (PyMARL2, EPyMARL, PettingZoo) and algorithm references (QTypeMix, MAPPO, RODE) are research references for the algorithm design document, not implementation targets. No code is written against these frameworks in v1.0.

**Core technologies:**
- `dblp_search.py` + `dblp_keywords_extract.py`: existing two-stage search pipeline -- domain-agnostic, handles pagination, rate limiting, DOI dedup, Excel output
- `dblp_config.json`: keyword configuration -- the single file that changes; drives both search breadth and extraction precision
- `XiangqiEnv` (Gymnasium): existing multi-agent environment -- provides 16-channel observation, per-piece-type action masking, material+outcome rewards (from v0.3)
- CSV/Markdown: screening and analysis artifacts -- no database, no web app, just version-controlled text files

**What NOT to add:** Ray RLlib (too heavy for research), Stable-Baselines3 (homogeneous agent focus), Streamlit/Flask screening UI (over-engineering), Zotero (collection will stay under 200 papers).

### Expected Features

This is a research milestone. "Features" are research deliverables, not shipped code.

**Must have (table stakes):**
- MARL-focused keyword design in `dblp_config.json` -- broad search keywords (multi-agent RL, heterogeneous, teammate modeling, active inference) plus fine-grained AND/OR extract keywords
- AAMAS venue added to search list -- the primary multi-agent systems conference
- Systematic screening workflow with CSV artifacts (shortlist, included, excluded)
- Per-paper technical analysis with consistent template (contribution, relevance, method, strengths, limitations, applicable ideas)
- Cross-paper synthesis document identifying patterns, gaps, and algorithmic opportunities
- Algorithm specification document (`prototypes/algorithm_v1.md`) -- the final deliverable

**Should have (differentiators):**
- Keyword iteration loop -- refine keywords based on screening feedback, re-run pipeline cheaply (DOI dedup handles incremental updates)
- Cross-reference discovery -- follow citation chains from included papers
- Observation/perspective adaptation design -- how to adapt AIM's perception portrait to fully observable chess (attention over board regions rather than viewpoint transformation)

**Defer (future milestones):**
- Algorithm implementation in `src/xiangqi/`
- Training loop and experiment tracking
- Policy network replacing RandomAI
- Curriculum learning and heterogeneous-aware mixing networks

### Architecture Approach

The architecture extends the existing `paper_collect/` directory with three new subdirectories (`screening/`, `analysis/`, `prototypes/`) while leaving `src/xiangqi/` entirely untouched. Data flows in one direction: keywords drive search, search produces a shortlist, screening produces included papers, analysis produces summaries and synthesis, synthesis produces algorithm design. The pipeline is iterative -- if analysis reveals gaps, keywords update and the cycle repeats. The entire `src/xiangqi/` codebase (engine, UI, controller, AI interface, RL environment) is stable and unchanged.

**Major components:**
1. `dblp_config.json` (MODIFY) -- keyword content redesigned for MARL domain; broad search terms plus nested AND/OR extract groups
2. `screening/` (NEW) -- manual paper screening artifacts; CSV-based in/exclude decisions with reasons
3. `analysis/` (NEW) -- per-paper markdown summaries plus cross-paper synthesis and algorithm ideas
4. `prototypes/` (NEW) -- algorithm specification document; the culminating deliverable of the milestone
5. `papers/` (EXISTING, grows) -- full-text markdown of collected papers

### Critical Pitfalls

1. **QMIX monotonicity limits heterogeneous expressiveness** -- Vanilla QMIX cannot represent negative individual contributions; a defensive piece making an aggressive move gets the wrong gradient. Use QTypeMix or QPLEX instead. Addressed in Phase 5 algorithm design.

2. **Observation representation mismatch** -- AIM's viewpoint transformation assumes partially observable domains with relative-position features. Chess is fully observable; all agents see the same board. The perception portrait must be fundamentally rethought (attention over relevant board regions per piece type, not viewpoint transformation). This is the hardest conceptual adaptation. Addressed in Phase 5.

3. **Too-broad or too-narrow keywords** -- "multi-agent" alone returns 50,000+ papers; "active inference" alone misses teammate modeling and Theory of Mind work. Use broad-but-domain-scoped Stage 1 keywords, then AND-logic Stage 2 extract groups with exhaustive synonym expansion. Addressed in Phase 1, iterated in Phase 3.

4. **Premature algorithm commitment** -- Designing the algorithm before completing literature analysis locks in a suboptimal approach. v1.0 exists precisely to prevent this. Enforce strict phase ordering: algorithm design is the final phase. Addressed by workflow discipline.

5. **Multiple loss terms causing training instability** -- AIM has 6+ loss terms that may conflict. If we adopt AIM's framework, loss balancing becomes a critical hyperparameter concern. Addressed in Phase 5 -- start simple, add complexity incrementally.

---

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Keyword Redesign
**Rationale:** This is the only phase involving code changes (a single JSON config file). It is the fastest to complete and unblocks all downstream phases. The existing pipeline scripts require zero modification.
**Delivers:** Updated `dblp_config.json` with MARL-domain keywords and AAMAS venue
**Addresses:** Literature pipeline table stakes; Category 1 features from FEATURES.md
**Avoids:** Pitfalls 4.1 (too broad), 4.2 (too narrow), 4.3 (missing terminology variants), 4.4 (missing venues)

### Phase 2: Paper Collection
**Rationale:** Pure execution of existing scripts with new config. No development risk. The scripts handle pagination, rate limiting, retry, and DOI deduplication automatically.
**Delivers:** `screening/shortlist.csv` with filtered paper candidates
**Uses:** `dblp_search.py`, `dblp_keywords_extract.py` (unchanged)
**Implements:** Two-stage keyword pipeline pattern from ARCHITECTURE.md

### Phase 3: Manual Screening
**Rationale:** Human judgment phase. Researcher reads titles/abstracts, makes in/exclude decisions, collects full-text papers. This is where keyword quality is validated and iteration may be triggered.
**Delivers:** `screening/included.csv`, `screening/excluded.csv`, new papers in `papers/`
**Addresses:** Systematic screening workflow from FEATURES.md
**Avoids:** Pitfall 4.1 (iterates keywords if too many false positives/negatives)

### Phase 4: Technical Analysis
**Rationale:** Deep reading and structured analysis of included papers. Produces the cross-paper synthesis that identifies algorithmic opportunities and gaps. This is the most intellectually demanding phase.
**Delivers:** `analysis/summaries/*.md`, `analysis/synthesis.md`, `analysis/algorithm_ideas.md`
**Addresses:** Category 2-5 feature research from FEATURES.md
**Avoids:** Pitfall 5.4 (premature algorithm commitment) by completing analysis before design

### Phase 5: Algorithm Design
**Rationale:** The culminating phase. Only begins after literature analysis is complete. Synthesizes findings into a concrete algorithm specification for heterogeneous agent predictive collaboration on the Xiangqi domain.
**Delivers:** `prototypes/algorithm_v1.md` -- architecture, training procedure, evaluation metrics, loss design
**Addresses:** Algorithm design methodology from FEATURES.md
**Avoids:** Pitfalls 1.1 (QMIX monotonicity), 3.3 (observation mismatch), 5.3 (training instability) through informed design choices

### Phase Ordering Rationale

- Phase 1 is configuration-only and takes minutes to hours; it unblocks everything with zero risk.
- Phase 2 uses battle-tested scripts that require no modification; it is pure execution.
- Phases 3-5 are human-driven research with no code to write and no bugs to fix.
- Strict sequential ordering (1 then 2 then 3 then 4 then 5) prevents premature algorithm commitment.
- Iteration is cheap: the pipeline supports incremental re-runs via DOI deduplication, so keyword refinement after Phase 3 does not waste prior work.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Keyword calibration may require a preliminary test run to gauge result volume (aim for ~5000-10000 from search, ~100-300 after extraction). Not a technical risk but a tuning step.
- **Phase 5:** This is the most intellectually complex phase. The observation adaptation problem (how to do perception portraits in fully observable chess) has no established answer in the literature. May warrant a focused `/gsd:research-phase` call during planning to investigate attention-based alternatives to viewpoint transformation.

Phases with standard patterns (skip research-phase):
- **Phase 2:** Well-documented scripts, no development needed.
- **Phase 3:** Standard systematic review methodology, no technical risk.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Existing pipeline verified via direct code analysis; no new dependencies needed |
| Features | HIGH | Feature categories well-defined from AIM paper analysis and MARL literature survey |
| Architecture | HIGH | Directory structure and data flow derived from direct codebase analysis; patterns are standard research methodology |
| Pitfalls | HIGH | Pitfalls identified from MARL literature and AIM paper limitations; prevention strategies are concrete |
| Algorithm design | MEDIUM | Algorithm is the research output, not the input; specific architecture depends on literature analysis results |

**Overall confidence:** HIGH

### Gaps to Address

- **Perception portrait adaptation for fully observable domains:** AIM's viewpoint transformation assumes partial observability. Chess is fully observable with a shared board. The perception portrait concept needs fundamental rethinking -- possibly attention over board regions relevant to each piece type rather than viewpoint transformation. This gap cannot be resolved until Phase 4 analysis identifies which existing work (if any) addresses this.
- **Optimal parameter sharing strategy:** 7 piece types with counts 1/2/2/2/2/2/5 creates an imbalance. Type-based sharing (7 networks) is the most natural choice, but whether to further group similar types (e.g., Chariot + Cannon as "long-range") is an open question that depends on literature findings.
- **Keyword recall validation:** There is no automated way to measure recall (fraction of relevant papers found). The iteration loop and cross-reference discovery mitigate this, but completeness cannot be guaranteed. Acceptable for a research milestone.

## Sources

### Primary (HIGH confidence)
- Existing codebase analysis: `paper_collect/dblp_search.py`, `paper_collect/dblp_keywords_extract.py`, `paper_collect/dblp_config.json`, `src/xiangqi/rl/env.py` -- direct code reading verified all integration points and capabilities
- AIM paper (Wu et al. 2025): `papers/` directory -- anchors the domain, provides the active inference portrait framework, identifies the homogeneous-agent limitation
- DBLP API documentation: https://dblp.org/faq/How+to+use+the+dblp+search+API -- official reference for search capabilities

### Secondary (MEDIUM confidence)
- MARL agent modeling literature: ScienceDirect, OpenReview, AAAI, NeurIPS proceedings -- identified QTypeMix, RODE, PR2 as key algorithmic references
- MARL heterogeneous agent literature: identified parameter sharing strategies, credit assignment methods, and role decomposition approaches
- Systematic review methodology: standard academic practice for literature screening

### Tertiary (LOW confidence)
- Specific algorithm performance comparisons: benchmark results from MARL papers are domain-specific and may not transfer to the chess domain
- Observation adaptation alternatives (attention over board regions): inferred from gap analysis, not found in existing literature

---
*Research completed: 2026-03-29*
*Ready for roadmap: yes*
