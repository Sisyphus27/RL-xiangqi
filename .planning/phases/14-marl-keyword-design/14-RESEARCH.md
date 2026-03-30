---
phase: 14
name: marl-keyword-design
created: 2026-03-29
status: complete
---

## RESEARCH COMPLETE

### 1. Current State of dblp_config.json and dblp_search.py

#### 1.1 dblp_config.json Structure (Current: Hypergraph/Traffic Domain)

The config file at `paper_collect/dblp_config.json` has six top-level sections. Only two sections contain domain-specific keyword content that must change:

| Section | Purpose | Changes Needed |
|---------|---------|----------------|
| `search.default_keywords` | Stage 1 broad search terms | **REPLACE** hypergraph/traffic terms with MARL terms |
| `search.default_venues` | Target venues list | **ADD** aamas, jaamas |
| `search.start_year` | Year filter start | **CHANGE** 2020 -> 2024 |
| `search.end_year` | Year filter end | Keep 2026 |
| `extract.default_keywords` | Stage 2 nested AND/OR groups | **REPLACE** with MARL AND/OR groups |
| `api`, `pagination`, `termination`, `abstract_apis` | Pipeline infrastructure | **NO CHANGE** |

Current keyword counts:
- Stage 1: 35 keywords (all hypergraph/traffic domain)
- Stage 2: 14 AND/OR groups (each is a 2D array: `[group1_OR, group2_OR, ...]`)
- Venues: 18 venues (kdd, icml, neurips, aaai, ijcai, iclr, icde, sigmod, vldb, tkde, tmc, www, cvpr, acl, iccv, pami, sigir, tpami)

Existing CSV cache: `paper_collect/dblp_papers.csv` has 5,597 rows of hypergraph/traffic domain papers. This must be archived before re-running with MARL keywords.

#### 1.2 dblp_search.py Mechanics (READ ONLY -- No Modifications)

Key behaviors relevant to keyword design:

1. **Cartesian product queries**: For each `(keyword, venue)` pair, the script issues a DBLP API query formatted as `"{keyword} {venue}"` (see `build_queries()` at line 549-550). This means each keyword is searched independently against each venue.

2. **Title + venue matching**: DBLP's search API performs full-text matching on publication metadata. The venue name appended to the query narrows results to that venue's proceedings.

3. **Year filtering**: Applied client-side in `process_hits()` (lines 447-448) -- papers outside `[start_year, end_year]` are discarded. This means the API may return older papers that get filtered out.

4. **DOI deduplication**: Uses composite key `doi if doi else f"{title}_{year}"` (line 448-449). Re-running with different keywords merges results without duplication. This makes iteration safe.

5. **Rate limiting**: Built-in sleep with jitter between pages. Config controls: `sleep_time=2.0`, `jitter_min=0.5`, `jitter_max=1.5`, `max_workers=2`. These are conservative enough for MARL-scale queries.

6. **Termination conditions**: Stops on consecutive duplicate pages (`duplicate_pages_limit=2`), same-paper threshold (`same_paper_threshold=2`), or reaching `max_pages=50`. These prevent infinite loops on high-volume queries.

**Implication for keyword design**: Since each keyword generates `len(venues)` API queries, the total query count is `keywords * venues`. With ~25 keywords and ~20 venues, that is ~500 queries. At ~2s per query with 2 workers, estimated runtime is ~8-10 minutes. This is acceptable.

#### 1.3 dblp_keywords_extract.py Mechanics (READ ONLY -- No Modifications)

Key behaviors relevant to keyword design:

1. **Title-only matching**: Keywords are matched against the `title` column of the CSV (not abstracts). This limits precision but is fast. The `case_insensitive: true` setting means matching is case-insensitive.

2. **Nesting levels**: The script handles three nesting levels (see `_get_nesting_level()`):
   - **Level 1** (flat): `["kw1", "kw2"]` -- all keywords in one group, controlled by `match_all` (AND/OR)
   - **Level 2** (2D): `[["a", "b"], ["c"]]` -- group-inner OR, group-inter AND. This is the standard Stage 2 structure.
   - **Level 3** (3D): `[[["a","b"],["c"]], [["d","e"],["f"]]]` -- multiple Level 2 queries executed independently, then merged with deduplication.

3. **Current Level 2 structure**: The existing config uses Level 2 exclusively -- each element of `extract.default_keywords` is a 2D array where:
   - Each inner array is a synonym group (OR logic): any term in the group matches
   - All groups must match (AND logic): the paper title must hit at least one term from every group

4. **Level 3 for MARL**: The 14-CONTEXT.md decisions specify 6 AND/OR topic groups for Stage 2. Since the script processes the entire `extract.default_keywords` as a single Level 2 structure (all groups AND'd together), using 6 groups would mean a paper must match ALL 6 groups simultaneously -- this is extremely restrictive and would yield very few results.

   **The correct approach is Level 3**: Each of the 6 AND/OR groups should be a separate Level 2 query wrapped in a Level 3 outer array. This way, a paper matches if it satisfies ANY of the 6 topic groups (group-inter OR at Level 3), while within each group, the AND/OR logic applies. The script's `extract_keywords_multi_group()` function handles this by executing each Level 2 query independently and merging results.

   Structure:
   ```json
   [
     [[MARL_Core_OR], [Cooperation_OR], [Heterogeneity_OR], ...],
     [[MARL_Core_OR], [Cooperation_OR], [Modeling_OR], ...],
     ...
   ]
   ```
   Each outer element is one AND/OR topic group (Level 2). The script runs each independently and merges.

5. **Substring matching**: The matching is plain substring containment (`token in text` after normalization, line 290). This means "agent" matches "agent", "agents", "multi-agent", "agent-based", etc. No wildcards needed -- the substring behavior already provides broad matching.

   **Caution**: "RL" would match URLs containing "url" after case-insensitive normalization. Use more specific terms like "reinforcement learning" or check for false positives during calibration.

---

### 2. Two-Stage Keyword Structure Design

#### 2.1 Stage 1: Broad Search (search.default_keywords)

**Purpose**: Cast a wide net to capture all potentially relevant papers from DBLP. Keywords are combined with venues in a Cartesian product.

**Design principles**:
- Terms should be broad enough to catch relevant work even if the paper's title doesn't use our exact domain vocabulary
- ~25 keywords organized into 5 semantic groups per D-02 decision
- Each keyword is a standalone search term -- no AND logic at this stage
- Substring matching by DBLP API means shorter terms cast wider nets

**Keyword groups** (from D-02, D-03):

| Group | Keywords | Count | Rationale |
|-------|----------|-------|-----------|
| MARL Core | multi-agent reinforcement learning, multi-agent RL, MARL, cooperative multi-agent, decentralized execution, CTDE | 6 | Foundation terms that identify the domain |
| Heterogeneous & Roles | heterogeneous agent, heterogeneous multi-agent, agent diversity, asymmetric agents, type-aware, role-based, diverse agent | 7 | Primary innovation area, expanded per D-03 for maximum recall |
| Modeling & Inference | teammate modeling, opponent modeling, active inference, Theory of Mind, belief tracking, agent modeling | 6 | Core technical approach from AIM paper |
| Value Decomposition & Policy | value decomposition, credit assignment, MAPPO, QMIX | 4 | CTDE training methods that capture related algorithmic work |
| Collaboration & Communication | communication-free, ad-hoc teamwork, cooperative coordination | 3 | Collaboration paradigms relevant to non-communication setting |

**Total: ~26 keywords**

**Query volume estimation**: 26 keywords x 20 venues = 520 queries. With `max_workers=2` and ~2s average per query, estimated runtime: ~9 minutes. Acceptable.

**Expected result volume**: Based on SUMMARY.md calibration target, aiming for ~5,000-10,000 papers after deduplication. If volume is too high, the Stage 2 extraction will filter down to ~100-300. If too low, keywords can be expanded.

#### 2.2 Stage 2: Refined Extraction (extract.default_keywords)

**Purpose**: Use nested AND/OR logic to filter the broad CSV into a manageable shortlist. Each topic group represents a distinct "relevance profile" -- a paper matches if it satisfies ANY topic group.

**Structure**: Level 3 nesting (3D array). Each outer element is a Level 2 AND/OR query.

**Topic groups** (from D-04, D-05):

```
Group 1 — MARL Core + Heterogeneity:
  AND: [multi-agent reinforcement learning | multi-agent RL | MARL]
  AND: [heterogeneous | diverse | asymmetric | type-aware | role-based | different action space]
  → Captures papers explicitly about heterogeneous MARL

Group 2 — MARL Core + Cooperation:
  AND: [multi-agent reinforcement learning | multi-agent RL | MARL]
  AND: [cooperative | collaborative | coordination]
  → Captures cooperative MARL papers (may include homogeneous work)

Group 3 — Modeling + Inference + Cooperation:
  AND: [teammate modeling | opponent modeling | agent modeling | active inference | Theory of Mind | belief]
  AND: [cooperative | collaborative | coordination | multi-agent]
  → Captures agent modeling work in multi-agent settings

Group 4 — Heterogeneity + Training:
  AND: [heterogeneous | diverse | asymmetric | type-aware | role-based | different action space]
  AND: [decentralized | CTDE | value decomposition | policy gradient | credit assignment]
  → Captures training/method papers for heterogeneous agents

Group 5 — Collaboration + No Communication:
  AND: [communication-free | ad-hoc teamwork | non-communication]
  AND: [multi-agent | cooperative | collaboration | coordination]
  → Captures communication-free collaboration work

Group 6 — Application Scenario + MARL:
  AND: [game | board game | StarCraft | planning | scheduling | robot]
  AND: [multi-agent reinforcement learning | multi-agent RL | MARL | cooperative]
  → Captures MARL papers in application domains relevant to our setting
```

**Why Level 3 (6 independent queries) instead of Level 2 (6 AND'd groups)**: If we used Level 2 with all 6 groups AND'd together, a paper would need to match terms from ALL 6 groups -- extremely restrictive, likely yielding zero results. Level 3 allows a paper to match ANY single topic group, which is the correct semantics for "papers relevant to our research in different ways."

**Implementation detail**: The `extract_keywords_multi_group()` function handles Level 3 by executing each Level 2 query independently, adding a `matched_keyword_group` column (e.g., "group_1", "group_1;group_3"), and deduplicating by title+year. This gives us both the shortlist and visibility into which topic profiles each paper matched.

#### 2.3 Mapping Between Stages

| Stage 1 Keyword | Stage 2 Groups Where It Appears |
|-----------------|-------------------------------|
| multi-agent reinforcement learning | Groups 1, 2, 6 |
| heterogeneous agent | Groups 1, 4 |
| teammate modeling | Group 3 |
| active inference | Group 3 |
| MAPPO | Group 4 (via "policy gradient") |
| ad-hoc teamwork | Group 5 |
| ... | ... |

The mapping is not 1:1 -- Stage 1 keywords are designed for broad DBLP retrieval, while Stage 2 groups encode specific relevance profiles. Some Stage 2 terms (like "different action space") may not appear in Stage 1 but serve as additional matching signals during extraction.

---

### 3. MARL Domain Terminology Mapping

#### 3.1 Source: AIM Paper (Wu et al., 2025)

The AIM paper provides the primary terminology anchor. Key terms extracted:

| Term | Context | Keyword Usage |
|------|---------|---------------|
| Active inference | Core framework concept | Direct keyword |
| Perception/Belief/Action portrait | AIM's three-portrait model | "belief tracking" as proxy |
| Teammate modeling | Core problem | Direct keyword |
| Non-communication | AIM's constraint | Direct keyword + "communication-free" |
| Decentralized execution | Target execution mode | Direct keyword |
| CTDE | Training paradigm | Direct keyword (acronym) |
| Dual filter | AIM's selection mechanism | Not a keyword (too specific) |
| Dec-POMDP | Formal framework | Not a keyword (too formal) |

#### 3.2 Source: AIM Paper Related Works

The Related Works and References sections provide verified terminology from the broader field:

| Category | Terms from References | Keyword Coverage |
|----------|-----------------------|-----------------|
| Agent modeling | "opponent modeling", "agent modelling", "Theory of Mind", "Bayesian reasoning" | opponent modeling, Theory of Mind, belief tracking |
| Value decomposition | "QMIX", "VDN", "QPLEX" | QMIX (direct), value decomposition |
| Role-based MARL | "RODE", "role decomposition" | role-based (in heterogeneous group) |
| Communication | "multi-agent communication", "targeted communication" | communication-free (antonym approach) |
| Policy methods | "MAPPO", "MADDPG" | MAPPO (direct) |

#### 3.3 Synonym Expansion

Critical for Stage 2 recall. Terms that authors use interchangeably:

| Concept | Synonym Group (Stage 2 OR) |
|---------|---------------------------|
| Heterogeneous agents | heterogeneous, diverse, asymmetric, type-aware, role-based, different action space |
| Teammate modeling | teammate modeling, opponent modeling, agent modeling |
| Active inference | active inference, Theory of Mind, belief, belief tracking |
| Cooperation | cooperative, collaborative, coordination |
| MARL | multi-agent reinforcement learning, multi-agent RL, MARL |
| Decentralized training | decentralized, CTDE, value decomposition, policy gradient, credit assignment |

**Heterogeneity group** (Group 3 in Stage 2) has the richest synonym coverage per D-05, because this is the primary innovation direction and needs maximum recall.

---

### 4. DBLP API Query Structure and Constraints

#### 4.1 Query Format

The DBLP search API endpoint is `https://dblp.org/search/publ/api`. Queries are formed as:

```
GET https://dblp.org/search/publ/api?q={keyword}+{venue}&format=json&h=100&f=0
```

The script constructs queries in `build_queries()` as `f"{keyword} {venue}"` -- DBLP interprets the space-separated terms as a combined search.

**Important**: DBLP's search is a full-text metadata search, not just title search. It matches against titles, authors, venues, and abstracts. However, Stage 2 extraction filters by title only. This means:
- Stage 1 may return papers where the keyword appears in the abstract but not the title
- Stage 2 will filter these out if the title doesn't contain the extract keywords
- This is acceptable -- it's better to over-retrieve at Stage 1 and filter at Stage 2

#### 4.2 Pagination and Rate Limits

- `max_per_page=100`: Maximum results per API call
- `max_pages=50`: Maximum pagination depth per query
- `sleep_time=2.0` + jitter `[0.5, 1.5]`: 1.0-3.0 seconds between pages
- `max_workers=2`: Concurrent query threads
- DBLP has no official rate limit but aggressive crawling triggers 429 responses

**For MARL queries**: Some keywords like "MARL" may return very large result sets. The `stop_on_duplicate_page` and `same_paper_threshold` settings will terminate early once all relevant results are captured. Year filtering (2024-2026) further limits the volume.

#### 4.3 Venue Matching

The `is_venue_match()` function (line 176-179) does case-insensitive substring matching on the venue string. This means:
- Querying "aamas" will match venue strings containing "aamas" (e.g., "International Conference on Autonomous Agents and Multi-Agent Systems")
- The venue parameter in the query narrows DBLP results, but client-side filtering also applies

---

### 5. Venue Selection Strategy

#### 5.1 Current Venues (18)

All are top-tier venues in ML/AI/DM:

| Venue | Full Name | MARL Relevance |
|-------|-----------|----------------|
| kdd | Knowledge Discovery and Data Mining | Medium |
| icml | International Conference on Machine Learning | High |
| neurips | Neural Information Processing Systems | High |
| aaai | AAAI Conference on Artificial Intelligence | High |
| ijcai | International Joint Conference on AI | High |
| iclr | International Conference on Learning Representations | High |
| icde | International Conference on Data Engineering | Low |
| sigmod | ACM SIGMOD Conference | Low |
| vldb | Very Large Data Bases | Low |
| tkde | IEEE Trans. Knowledge and Data Engineering | Low |
| tmc | IEEE Trans. Mobile Computing | Low |
| www | The Web Conference | Low |
| cvpr | Computer Vision and Pattern Recognition | Low |
| acl | Association for Computational Linguistics | Low |
| iccv | International Conference on Computer Vision | Low |
| pami | IEEE Trans. Pattern Analysis and Machine Intelligence | Low |
| sigir | ACM SIGIR Conference | Low |
| tpami | IEEE Trans. Pattern Analysis and Machine Intelligence | Low |

#### 5.2 Venues to Add (per D-06)

| Venue | Full Name | MARL Relevance | Justification |
|-------|-----------|----------------|---------------|
| aamas | International Conference on Autonomous Agents and Multi-Agent Systems | **Critical** | Primary multi-agent systems conference; most MARL work appears here |
| jaamas | Journal of Autonomous Agents and Multi-Agent Systems | High | Journal companion to AAMAS; archival MARL publications |

**Total venues: 20** (18 existing + 2 new)

#### 5.3 Venues NOT to Add

The following were considered but excluded:
- `ec` (Economics and Computation) -- more game-theory than RL
- `corl` (Conference on Robot Learning) -- too narrow for our domain
- `aaai FALL symposia` -- not well-indexed in DBLP
- `alta` (Australasian Language Technology) -- irrelevant

The guideline from ARCHITECTURE.md: keep under 22 venues. At 20 venues, we are within budget.

#### 5.4 Year Range Change (per D-07)

| Setting | Current | New | Rationale |
|---------|---------|-----|-----------|
| `start_year` | 2020 | 2024 | Focus on cutting-edge work; active inference + heterogeneous MARL is a very recent research direction |
| `end_year` | 2026 | 2026 | No change; 2026 captures current year publications |

Narrowing from 7 years (2020-2026) to 3 years (2024-2026) significantly reduces result volume, which aligns with the calibration target of ~5,000-10,000 papers.

---

### 6. Dependencies, Risks, and Technical Considerations

#### 6.1 Dependencies

| Dependency | Status | Impact if Missing |
|------------|--------|-------------------|
| AIM paper in papers/ | Present | Domain anchor; all terminology derived from it |
| dblp_search.py | Present, unchanged | Stage 1 search engine |
| dblp_keywords_extract.py | Present, unchanged | Stage 2 extraction engine |
| Existing dblp_papers.csv | Present but stale | Must archive before re-run to avoid domain mixing |
| pandas, openpyxl, tqdm, requests | Installed | Required for pipeline scripts |
| DBLP API availability | External | API downtime blocks execution (mitigated by retry logic) |

#### 6.2 Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Keyword too broad** -- "MARL" returns 10,000+ papers, overwhelming Stage 2 | Medium | Long runtime, but Stage 2 filters handle it | Year narrowing (2024-2026) reduces volume; Stage 2 AND logic further filters |
| **Keyword too narrow** -- Miss relevant work that uses different terminology | Medium | False negatives; incomplete literature coverage | Rich synonym expansion in Stage 2; iteration loop in Phase 16 adds missed terms |
| **Stage 2 returns 0 results** -- AND logic too restrictive | Low | No shortlist for screening | Level 3 structure (6 independent topic groups) provides multiple match pathways; any single group match suffices |
| **Stage 2 returns too many results (>500)** -- Too many false positives | Low | Screening burden increases | Tighten Stage 2 AND groups; add more required dimensions; calibrate in Phase 15 |
| **DBLP API 429 rate limiting** | Low-Medium | Queries fail temporarily | Built-in retry with backoff (`retry_total=5`, `retry_backoff=2.0`); `max_workers=2` is conservative |
| **"RL" matches URLs in titles** | Low | False positives in Stage 2 | Avoid bare "RL" in Stage 2; use "reinforcement learning" instead; Stage 1 can use "RL" since DBLP metadata matching is less prone to this |
| **Level 3 vs Level 2 confusion** | Medium | Wrong JSON structure breaks extraction | Must wrap the 6 topic groups in an outer array (Level 3); verify by checking `_get_nesting_level()` returns 3 |

#### 6.3 Technical Considerations

1. **JSON structure precision**: The `extract.default_keywords` must be a 3D array. Each of the 6 topic groups is a 2D array. The outer array wraps all 6. Example:
   ```json
   [
     [["multi-agent reinforcement learning", "multi-agent RL", "MARL"], ["heterogeneous", "diverse", "asymmetric"]],
     [["multi-agent reinforcement learning", "multi-agent RL", "MARL"], ["cooperative", "collaborative", "coordination"]],
     ...5 more groups...
   ]
   ```

2. **Archiving existing CSV**: Before running with new keywords, archive `paper_collect/dblp_papers.csv` (currently 5,597 hypergraph/traffic rows) to prevent domain mixing. Suggested name: `dblp_papers_hypergraph_archive.csv`.

3. **Deduplication across groups**: The `extract_keywords_multi_group()` function deduplicates by `title + year` as unique key. Papers matching multiple topic groups get a combined `matched_keyword_group` label (e.g., "group_1;group_3"). This is informative for screening.

4. **Substring matching caveat**: Stage 2 uses substring containment (`token in text`). This means:
   - "MARL" matches "MARL", "MARL-based", etc. -- good
   - "belief" matches "belief", "beliefs", "belief-based" -- good
   - "CTDE" matches "CTDE" but may miss "centralized training decentralized execution" if abbreviated -- include both forms
   - "game" matches "game", "games", "game-theoretic", but also "frame", "gameplay" -- monitor for false positives

5. **No abstract matching**: Stage 2 only matches against titles. Papers whose relevance is expressed in the abstract but not the title will be missed. This is an accepted trade-off -- the `abstract_apis.semantic_scholar.enable: false` setting confirms this. Can be enabled in a future iteration if needed.

6. **Calibration test run**: Per 14-CONTEXT.md success criterion 4, a test run of `dblp_search.py` should return results. This is a sanity check, not a full calibration. Full volume calibration happens in Phase 15.

#### 6.4 Out of Scope

The following are explicitly out of scope for Phase 14 (handled in later phases):

- Running the full pipeline (Phase 15)
- Keyword iteration based on screening feedback (Phase 16)
- Modifying `dblp_search.py` or `dblp_keywords_extract.py` (never -- they are configuration-driven)
- Fetching abstracts from Semantic Scholar (config already has `enable: false`)
- Building screening tools or UI (CSV-based workflow in Phase 16)
- Any code changes to `src/xiangqi/` (v1.0 is research-only)

---

### 7. Implementation Checklist for Phase 14 Plan

When writing the plan, ensure:

1. **Stage 1 keywords** (~26 terms) replace `search.default_keywords` content
2. **Stage 2 keywords** (6 Level 3 topic groups) replace `extract.default_keywords` content
3. **Venues** add "aamas" and "jaamas" to `search.default_venues`
4. **Year range** change `start_year` from 2020 to 2024
5. **Archive** existing `dblp_papers.csv` before any test run
6. **Test run** of `dblp_search.py` with new config returns non-zero results
7. **Verify** JSON structure is valid (Level 3 nesting for extract keywords)
8. **No other files** are modified

---

### Sources

- `paper_collect/dblp_config.json` -- current configuration (direct analysis)
- `paper_collect/dblp_search.py` -- search pipeline mechanics (direct code analysis)
- `paper_collect/dblp_keywords_extract.py` -- extraction pipeline mechanics, nesting levels, `extract_keywords_multi_group()` (direct code analysis)
- `papers/Wu 等 - 2025 - Think How Your Teammates Think Active Inference Can Benefit Decentralized Execution.md` -- AIM paper providing domain terminology anchor
- `.planning/phases/14-marl-keyword-design/14-CONTEXT.md` -- user decisions (D-01 through D-08)
- `.planning/research/SUMMARY.md` -- project research summary, calibration targets
- `.planning/research/FEATURES.md` -- feature analysis, synonym groups
- `.planning/research/ARCHITECTURE.md` -- two-stage keyword pipeline pattern, venue strategy
- `.planning/REQUIREMENTS.md` -- LIT-01, LIT-02, LIT-03 requirements
- `.planning/ROADMAP.md` -- Phase 14 success criteria

---
*Research completed: 2026-03-29*
