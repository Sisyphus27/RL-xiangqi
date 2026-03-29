# Architecture Patterns

**Domain:** Research pipeline for heterogeneous multi-agent RL predictive collaboration
**Researched:** 2026-03-29
**Confidence:** HIGH (based on direct analysis of existing codebase and scripts; domain literature patterns from web search at MEDIUM confidence where noted)

---

## Recommended Architecture

The v1.0 milestone is research-focused, not production. The architecture extends the existing `paper_collect/` scripts into a structured literature pipeline while keeping integration with `src/xiangqi/` minimal. The key principle: research artifacts (papers, analysis, algorithm designs) live in `paper_collect/` and `papers/`; code artifacts (algorithm prototypes, training loops) will eventually live in `src/xiangqi/` but that is future work.

```
paper_collect/                     # Existing, needs keyword redesign
  dblp_config.json                   # MODIFIED: new keywords for MARL domain
  dblp_search.py                     # UNCHANGED: search engine works as-is
  dblp_keywords_extract.py           # UNCHANGED: extraction engine works as-is
  screening/                         # NEW: manual screening artifacts
    shortlist.csv                     # Papers passing keyword filter
    included.csv                      # Papers passing manual screening
    excluded.csv                      # Papers rejected with reasons
    screening_log.md                  # Screening notes per paper
  analysis/                          # NEW: per-paper technical analysis
    summaries/                        # One .md per analyzed paper
    synthesis.md                      # Cross-paper synthesis document
    algorithm_ideas.md                # Algorithm concepts derived from analysis
  prototypes/                        # NEW: algorithm design documents
    algorithm_v1.md                   # Algorithm specification for v1.0 approach

papers/                            # Existing, grows with screening
  <author> - <year> - <title>.md   # Full paper markdown (current format)

src/xiangqi/                       # UNCHANGED in this milestone
  (existing codebase unchanged)
```

### Component Boundaries

| Component | Responsibility | Communicates With | Status |
|-----------|---------------|-------------------|--------|
| `dblp_config.json` | Keywords, venues, API config for both search and extract | Read by `dblp_search.py`, `dblp_keywords_extract.py` | **MODIFY**: keywords redesigned for MARL domain |
| `dblp_search.py` | Broad DBLP search (keyword x venue cartesian product) | Writes `dblp_papers.csv` | **UNCHANGED**: engine works for any keywords |
| `dblp_keywords_extract.py` | Fine keyword filtering on CSV (nested AND/OR logic) | Reads `dblp_papers.csv`, writes matched Excel | **UNCHANGED**: flexible enough for new keywords |
| `screening/` | Manual paper screening workflow (in/exclude decisions) | Receives output from extract; feeds papers/ and analysis/ | **NEW** |
| `analysis/` | Technical analysis of screened papers | Reads from papers/; feeds prototypes/ | **NEW** |
| `prototypes/` | Algorithm design documents | Reads from analysis/; feeds future src/xiangqi/ training code | **NEW** |
| `papers/` | Full-text markdown of collected papers | Populated manually during screening | **EXISTING**: grows |
| `src/xiangqi/rl/` | Gymnasium environment (XiangqiEnv) | No changes this milestone | **UNCHANGED** |
| `src/xiangqi/ai/` | AI interface (AIPlayer ABC) | No changes this milestone | **UNCHANGED** |

### Data Flow

```
Stage 1: Broad Search
  dblp_config.json (search keywords)
    --> dblp_search.py
    --> dblp_papers.csv (~5000+ rows)

Stage 2: Fine Filtering
  dblp_config.json (extract keywords, nested AND/OR)
    --> dblp_keywords_extract.py
    --> screening/shortlist.csv (~50-200 rows)

Stage 3: Manual Screening
  researcher reads titles/abstracts from shortlist.csv
    --> screening/included.csv (relevant papers)
    --> screening/excluded.csv (rejected with reason)
    --> papers/*.md (full text of included papers, collected manually)

Stage 4: Technical Analysis
  researcher reads papers/*.md
    --> analysis/summaries/<paper>.md (per-paper analysis)
    --> analysis/synthesis.md (cross-paper patterns)

Stage 5: Algorithm Design
  researcher synthesizes findings
    --> analysis/algorithm_ideas.md (candidate approaches)
    --> prototypes/algorithm_v1.md (selected approach specification)

Iteration Loop:
  If analysis reveals gaps:
    --> update dblp_config.json keywords
    --> re-run Stage 1-2 (incremental, appends to existing CSV)
    --> re-screen new results
```

---

## Patterns to Follow

### Pattern 1: Two-Stage Keyword Pipeline (Existing, Reuse As-Is)

**What:** The existing `dblp_search.py` does broad retrieval (single keywords x venues), then `dblp_keywords_extract.py` does fine filtering with nested AND/OR logic. This is already well-designed.

**When:** This is the core search-filter pattern. No code changes needed -- only the keyword content in `dblp_config.json` changes.

**Why it works for the new domain:** The MARL/heterogeneous agent domain has the same structure as the previous hypergraph/traffic domain: broad keywords catch a wide net, then precise compound queries narrow to the intersection of relevant concepts.

**Keyword redesign approach for MARL domain:**

Stage 1 (search keywords in `dblp_config.json`):
```json
{
  "search": {
    "default_keywords": [
      "multi-agent reinforcement learning",
      "MARL",
      "heterogeneous",
      "agent modeling",
      "teammate modeling",
      "opponent modeling",
      "theory of mind",
      "active inference",
      "decentralized execution",
      "cooperative multi-agent",
      "collaborative",
      "predictive collaboration",
      "ad-hoc teamwork",
      "agent heterogeneity",
      "policy prediction",
      "opponent learning",
      "centralized training decentralized execution",
      "CTDE",
      "communication-free",
      "non-communication",
      "multi-agent cooperation",
      "role-based multi-agent",
      "agent diversity"
    ]
  }
}
```

Stage 2 (extract keywords in `dblp_config.json`):
```json
{
  "extract": {
    "default_keywords": [
      [["multi-agent", "MARL"], ["heterogeneous", "diverse", "diversity"], ["reinforcement learning", "RL"]],
      [["agent modeling", "teammate modeling", "opponent modeling"], ["prediction", "inference", "predict"], ["decentralized"]],
      [["cooperative", "collaborative"], ["multi-agent", "MARL"], ["no communication", "communication-free", "non-communication"]],
      [["active inference"], ["multi-agent", "MARL"], ["decentralized", "cooperative"]],
      [["theory of mind", "mental model"], ["multi-agent"], ["reinforcement learning"]],
      [["ad-hoc teamwork", "ad hoc"], ["multi-agent", "agent"], ["cooperation", "collaboration"]],
      [["role-based", "heterogeneous"], ["multi-agent", "MARL"], ["reinforcement learning", "RL", "cooperative"]],
      [["centralized training", "CTDE"], ["decentralized execution"], ["multi-agent", "MARL"]],
      [["predictive", "prediction"], ["teammate", "agent"], ["cooperation", "collaboration", "coordination"]],
      [["policy", "strategy"], ["prediction", "modeling", "inference"], ["multi-agent", "MARL"]]
    ]
  }
}
```

Add relevant venues: Keep existing ML/AI venues, add `aamas` (International Conference on Autonomous Agents and Multi-Agent Systems).

**Source confidence:** HIGH for existing script capabilities (direct code analysis). MEDIUM for keyword design (based on domain knowledge and AIM paper analysis, not yet validated by running the pipeline).

### Pattern 2: CSV-Based Screening Workflow

**What:** Use simple CSV files for screening decisions. No database, no web app. The shortlist CSV from extraction becomes the input; screening decisions are recorded in `included.csv` and `excluded.csv`.

**When:** Manual literature screening. This is the standard systematic review pattern adapted for a single researcher.

**Example schema:**
```csv
title,year,venue,doi,url,abstract,matched_terms,decision,reason,notes
```

The `decision` field is one of: `include`, `exclude`, `maybe`. The `reason` field documents why. This enables iteration: if keywords change, you can re-screen only the new additions by checking what is already in included/excluded.

**Why simple CSV:** The existing pipeline already outputs CSV. Adding a SQLite database or web app for screening would be over-engineering for a single researcher doing one-time screening of ~200 papers. CSV is diff-friendly, version-controllable, and directly consumable by pandas.

**Source confidence:** HIGH (standard research methodology, no technology risk).

### Pattern 3: Per-Paper Analysis Markdown

**What:** One markdown file per paper in `analysis/summaries/`, following a consistent template.

**When:** During deep reading and technical analysis of included papers.

**Example template:**
```markdown
# [Paper Title]
- **Venue:** [venue]
- **Year:** [year]
- **Key Contribution:** [1-2 sentences]
- **Relevance to v1.0:** [Why this paper matters for heterogeneous agent predictive collaboration]
- **Method:** [Technical approach summary]
- **Strengths:** [What is good about this approach]
- **Limitations:** [What is missing or weak]
- **Applicable Ideas:** [Specific techniques we could adopt]
- **Related Papers:** [Links to related papers in our collection]
```

**Why markdown:** Consistent with the existing `papers/` format. No special tooling needed. Git-friendly for tracking evolution of understanding.

**Source confidence:** HIGH (formatting convention, no technology risk).

### Pattern 4: Keyword Iteration Loop

**What:** After initial screening and analysis, update keywords in `dblp_config.json` based on discovered gaps, then re-run the pipeline.

**When:** When analysis reveals that the initial keyword set missed relevant papers or captured too many irrelevant ones.

**How:**
1. Run initial search + extract with best-guess keywords
2. Screen results, identify false negatives (relevant papers missed) and false positives
3. Add new keywords for false negatives (e.g., discovered "ad-hoc teamwork" is relevant but was not in keywords)
4. Tighten extract groups to reduce false positives
5. Re-run `dblp_search.py` (results merge into existing CSV by DOI)
6. Re-run `dblp_keywords_extract.py` with updated config
7. Screen only new additions

**Critical detail:** The existing `dblp_search.py` uses DOI-based deduplication (composite key from DOI or title+year, line 448-449 of the script), so re-running with new keywords safely adds to the existing CSV without full duplication. This makes iteration cheap.

**Source confidence:** HIGH (verified directly from code analysis of `process_hits()` function).

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Building a Web UI for Screening

**What:** Creating a Flask/Django/Streamlit app to manage paper screening.
**Why bad:** Massive over-engineering for a single researcher doing one-time screening. Adds framework dependencies, deployment complexity, and maintenance burden. The milestone is about research output, not tool building.
**Instead:** Use CSV files opened in Excel/LibreOffice for screening. Filter, sort, add columns manually. The existing `dblp_keywords_extract.py` already outputs Excel (`.xlsx`).

### Anti-Pattern 2: Modifying Existing Pipeline Code

**What:** Refactoring `dblp_search.py` or `dblp_keywords_extract.py` to "better fit" the new domain.
**Why bad:** These scripts are already well-tested and domain-agnostic. The search script takes any keywords from config; the extract script handles arbitrary nested AND/OR logic. Changing working code introduces risk with no benefit.
**Instead:** Only change `dblp_config.json` keyword content. The code is configuration-driven by design.

### Anti-Pattern 3: Premature Algorithm Implementation

**What:** Writing training code in `src/xiangqi/` during this research milestone.
**Why bad:** v1.0 is explicitly a research milestone -- the goal is to explore, screen, and analyze. Implementing before the algorithm design is finalized leads to throwaway code and wasted effort. The algorithm specification in `prototypes/algorithm_v1.md` should be complete before any implementation begins (that is a future milestone).
**Instead:** Keep all algorithm work as design documents in `paper_collect/prototypes/`. Implementation belongs in a future milestone after the research is settled.

### Anti-Pattern 4: Expanding Venues Too Broadly

**What:** Adding 30+ venues to catch every possible paper.
**Why bad:** DBLP search does keyword x venue cartesian product. More venues = more API calls = longer runtime. The existing 18 venues already cover the top-tier ML/AI/DM conferences and journals.
**Instead:** Keep existing venue list, add `aamas` and perhaps `ec` (Economics and Computation) for multi-agent work. Total should stay under 22 venues.

---

## Scalability Considerations

| Concern | At 50 papers | At 200 papers | At 500+ papers |
|---------|--------------|---------------|----------------|
| Screening time | Few hours | 1-2 days | 3-5 days (acceptable for research) |
| Analysis depth | Full read of all | Full read of top 50, skim rest | Prioritize by relevance, sample rest |
| Keyword iterations | 1-2 cycles | 2-3 cycles | 3-5 cycles (diminishing returns) |
| Storage | Negligible | Negligible | Still negligible (markdown + CSV) |

The scale here is inherently bounded: this is academic literature review, not production data. Expect 50-200 included papers maximum. No scalability engineering needed.

---

## Integration Points with Existing Codebase

### What Stays Unchanged

The entire `src/xiangqi/` codebase is unchanged in this milestone:
- `src/xiangqi/engine/` -- Pure rules engine, no research dependency
- `src/xiangqi/ui/` -- PyQt6 UI, no research dependency
- `src/xiangqi/controller/` -- Game orchestration, no research dependency
- `src/xiangqi/ai/` -- AI interface (AIPlayer ABC, RandomAI), no research dependency
- `src/xiangqi/rl/` -- Gymnasium environment (XiangqiEnv with 16-channel observation, per-piece-type masking, reward shaping), no research dependency

### Future Integration (Post v1.0)

The research pipeline's output (`prototypes/algorithm_v1.md`) will inform:
1. New policy network architecture in `src/xiangqi/ai/` (replacing RandomAI with learned agents)
2. New reward shaping in `src/xiangqi/rl/env.py` (team cooperation bonuses, heterogeneous agent coordination rewards)
3. New training loop (new module, e.g., `src/xiangqi/training/`)
4. Arbitration network for heterogeneous agent move selection

These are all future milestones. This milestone produces the design document that enables those.

### Existing `dblp_papers.csv` Data

The existing CSV contains ~5,596 papers from the previous domain (hypergraph/traffic forecasting). This data is stale for the new domain but the file is a cache, not a source of truth. Options:
- **Recommended:** Archive the existing CSV (`mv dblp_papers.csv dblp_papers_hypergraph_archive.csv`), then run fresh search with new MARL keywords. This gives a clean dataset.
- **Alternative:** Keep the existing CSV and re-run search. New results merge in by DOI deduplication. Then use extract keywords to filter only MARL-relevant papers. Risk: larger file, noise from old domain.

---

## Build Order

The build order respects dependencies: each step depends on the previous step's output.

```
Phase 1: Keyword Design (no code changes)
  - Redesign dblp_config.json keywords for MARL domain
  - Depends on: reading AIM paper (already in papers/) to understand domain
  - Output: updated dblp_config.json

Phase 2: Paper Collection (existing scripts)
  - Run dblp_search.py with new keywords
  - Run dblp_keywords_extract.py with new extract config
  - Depends on: Phase 1
  - Output: screening/shortlist.csv

Phase 3: Manual Screening (human workflow)
  - Create screening/ directory structure
  - Screen shortlist into included/excluded
  - Collect full-text PDFs/markdown for included papers
  - Depends on: Phase 2
  - Output: screening/included.csv, screening/excluded.csv, papers/*.md additions

Phase 4: Technical Analysis (human + markdown)
  - Create analysis/ directory structure
  - Analyze each included paper using template
  - Write cross-paper synthesis
  - Depends on: Phase 3
  - Output: analysis/summaries/*.md, analysis/synthesis.md

Phase 5: Algorithm Design (human + markdown)
  - Create prototypes/ directory
  - Design algorithm based on analysis
  - Specify architecture, training procedure, evaluation metrics
  - Depends on: Phase 4
  - Output: prototypes/algorithm_v1.md

Iteration (any time after Phase 2):
  - If gaps found, update keywords, re-run Phases 1-3
  - Iterate until coverage is satisfactory
```

**Phase ordering rationale:**
- Phase 1 is pure configuration -- fastest to complete, unblocks everything.
- Phase 2 uses existing scripts unchanged -- no development risk.
- Phase 3-5 are human-driven research work -- no code to write, no bugs to fix.
- Iteration is cheap because the existing pipeline supports incremental re-runs with DOI deduplication.

**Research flags for phases:**
- Phase 1: Needs domain knowledge from AIM paper + preliminary search to calibrate keyword breadth. Standard research work, unlikely to need technical investigation.
- Phase 2: Pure execution. The scripts handle pagination, rate limiting, retry, and deduplication. No risk.
- Phase 3-5: Human judgment. No technical risk. The main risk is scope creep in paper collection -- mitigate by setting a target (e.g., 50-100 included papers).

---

## Sources

- DBLP API documentation: https://dblp.org/faq/How+to+use+the+dblp+search+API (HIGH confidence -- official API reference)
- Existing codebase analysis: `paper_collect/dblp_search.py`, `paper_collect/dblp_keywords_extract.py`, `paper_collect/dblp_config.json` (HIGH confidence -- direct code reading)
- AIM paper (Wu et al. 2025) in `papers/` directory -- anchors the domain and keyword design (HIGH confidence)
- MARL agent modeling literature: ScienceDirect, OpenReview, AAAI, NeurIPS proceedings (MEDIUM confidence -- web search results identifying key research directions)
- Systematic review methodology: standard academic practice for literature screening (HIGH confidence)

---
*Architecture research for: RL-Xiangqi v1.0 research pipeline -- heterogeneous multi-agent RL predictive collaboration*
*Researched: 2026-03-29*
