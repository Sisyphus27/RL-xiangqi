# Phase 14: MARL Keyword Design - Research

**Researched:** 2026-03-30
**Domain:** DBLP literature search pipeline configuration for MARL domain
**Confidence:** HIGH

## Summary

Phase 14 modifies exactly one file (`paper_collect/dblp_config.json`) to replace hypergraph/traffic keywords with MARL-domain keywords. The existing two-stage pipeline scripts (`dblp_search.py` and `dblp_keywords_extract.py`) require zero code changes -- they are fully configuration-driven. The research confirms that the JSON config structure already supports the exact nesting pattern needed for the two-stage keyword design: flat lists for Stage 1 broad search, and Level 2 nested arrays (`[[OR-group1], [OR-group2]]`) for Stage 2 AND/OR extraction. DBLP API uses prefix matching by default (no wildcard syntax needed), and the venue substring matcher in `dblp_search.py` will correctly match "aamas" against both the AAMAS conference (DBLP key `conf/ifaamas`) and the JAAMAS journal (DBLP key `journals/aamas`).

The primary risk is keyword calibration: too-broad Stage 1 keywords combined with 20 venues could produce an unmanageable number of DBLP API queries (each keyword x venue pair is a separate API call), while too-narrow Stage 2 extraction groups could filter out relevant papers. The CONTEXT.md decisions mitigate this with 25 scoped Stage 1 keywords across 5 semantic groups and 6 well-defined Stage 2 AND/OR groups. A calibration test run is recommended after config updates to verify result volumes fall within the target range (~5000-10000 from broad search, ~100-300 after extraction).

**Primary recommendation:** Write the new keyword content directly into `dblp_config.json` following the exact structure prescribed in CONTEXT.md decisions D-01 through D-08, then run a calibration test with a single keyword-venue pair to validate DBLP connectivity and result volume before committing.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Scope is MARL core terminology anchored by the AIM paper (Wu et al., 2025) -- not the full breadth of MARL literature
- **D-02:** ~25 keywords organized into 5 semantic groups:
  - **MARL Core:** multi-agent reinforcement learning, multi-agent RL, MARL, cooperative multi-agent, decentralized execution, CTDE
  - **Heterogeneous & Roles (EXPANDED):** heterogeneous agent, heterogeneous multi-agent, agent diversity, asymmetric agents, type-aware, role-based, diverse agent
  - **Modeling & Inference:** teammate modeling, opponent modeling, active inference, Theory of Mind, belief tracking, agent modeling
  - **Value Decomposition & Policy:** value decomposition, credit assignment, MAPPO, QMIX
  - **Collaboration & Communication:** communication-free, ad-hoc teamwork, cooperative coordination
- **D-03:** Heterogeneous keywords expanded from 3 to 7 -- primary future innovation direction, needs maximum recall
- **D-04:** 6 AND/OR topic groups -- groups joined by AND, terms within each group joined by OR:
  - Group 1 (MARL Core), Group 2 (Cooperation), Group 3 (Heterogeneity -- richest synonyms), Group 4 (Modeling/Inference), Group 5 (Execution/Training), Group 6 (Application Scenario)
- **D-05:** Group 3 (Heterogeneity) has the richest synonym coverage to maximize recall
- **D-06:** Keep all 18 existing venues + add AAMAS + JAAMAS (total ~20 venues)
- **D-07:** Year range narrowed to 2024-2026 (from previous 2020-2026)
- **D-08:** Retain existing API, pagination, and termination settings unchanged

### Claude's Discretion
- Exact keyword ordering and deduplication within config
- Whether to use wildcard-style matching (e.g., "heterogeneous*") -- depends on DBLP API behavior
- Fine-tuning of sleep_time, jitter, and retry settings if needed for calibration test run
- Formatting of Stage 2 nested AND/OR structure in JSON

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LIT-01 | Redesign dblp_config.json keywords from hypergraph/traffic to MARL/heterogeneous agent/predictive collaboration domain | Config structure analysis confirms only `search.default_keywords`, `search.default_venues`, and `extract.default_keywords` content changes needed; JSON structure preserved exactly |
| LIT-02 | Two-stage keyword design: Stage 1 broad retrieval covers MARL core terms, Stage 2 uses nested AND/OR logic for refined extraction | `dblp_search.py` reads flat keyword list for Cartesian product queries; `dblp_keywords_extract.py` supports Level 2 nesting `[[OR-group1], [OR-group2]]` with group-inner OR and group-inter AND -- exact pattern needed |
| LIT-03 | Add AAMAS and other multi-agent conferences to search venues | Venue matcher in `dblp_search.py` uses substring matching (case-insensitive, spaces removed); "aamas" matches both AAMAS conference (`conf/ifaamas`) and JAAMAS journal (`journals/aamas`) |
</phase_requirements>

## Standard Stack

### Core
| Library/Tool | Version | Purpose | Why Standard |
|-------------|---------|---------|--------------|
| `dblp_search.py` | existing | Stage 1 broad search against DBLP API | Already built, handles pagination, rate limiting, retry, DOI dedup |
| `dblp_keywords_extract.py` | existing | Stage 2 refined AND/OR keyword extraction | Supports Level 2/3 nesting, case-insensitive substring matching on titles |
| `dblp_config.json` | existing structure | Configuration file driving both stages | Only content changes; structure unchanged |
| pandas | existing | CSV/Excel I/O for paper data | Used by both pipeline scripts |
| openpyxl | existing | Excel output format | Used by `extract_and_save_with_config()` |
| requests | existing | HTTP client for DBLP API | Used by `dblp_search.py` |
| tqdm | existing | Progress bars for long-running searches | Used by `dblp_search.py` |

### Supporting
| Library/Tool | Version | Purpose | When to Use |
|-------------|---------|---------|-------------|
| pytest | >=8.0 | Validation test runner | Calibration test run and config validation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual keyword design | Automated keyword expansion from AIM paper NLP | Over-engineering for a one-time config edit; manual design with synonym expansion is sufficient |
| DBLP API | Semantic Scholar API | CONTEXT.md locks in DBLP pipeline; Semantic Scholar has abstract search but DBLP has more comprehensive venue coverage |

**Installation:**
No new packages needed. The existing conda environment `xqrl` has all dependencies.

**Version verification:**
All dependencies are pre-existing and verified working from v0.3 milestone. No new packages introduced.

## Architecture Patterns

### Config File Structure (Target)
```
paper_collect/dblp_config.json
├── search
│   ├── default_keywords    # FLAT LIST — Stage 1 broad terms (~25 items)
│   ├── default_venues      # FLAT LIST — venue abbreviations (~20 items)
│   ├── start_year          # 2024 (changed from 2020)
│   ├── end_year            # 2026 (unchanged)
│   └── max_results         # 40000 (unchanged)
├── extract
│   └── default_keywords    # NESTED LIST — Stage 2 AND/OR groups (6 groups)
├── api                     # UNCHANGED — rate limiting, retry, timeout
├── pagination              # UNCHANGED — page size, sleep, jitter
├── termination             # UNCHANGED — dedup, stop conditions
└── abstract_apis           # UNCHANGED — Semantic Scholar (disabled)
```

### Pattern 1: Two-Stage Keyword Pipeline
**What:** Stage 1 casts a wide net (keyword x venue Cartesian product), Stage 2 filters precisely (AND/OR title matching)
**When to use:** Always -- this is the established pipeline pattern
**Data flow:**
```
dblp_config.json
    │
    ├── Stage 1: dblp_search.py
    │   reads search.default_keywords x search.default_venues
    │   produces: dblp_papers.csv (broad results)
    │
    └── Stage 2: dblp_keywords_extract.py
        reads extract.default_keywords (nested AND/OR)
        input: dblp_papers.csv
        produces: dblp_papers_matched_*.xlsx (filtered shortlist)
```

### Pattern 2: Level 2 Nested AND/OR Keyword Structure
**What:** `[[term1a, term1b], [term2a, term2b], [term3a]]` where inner lists are OR, outer list is AND
**When to use:** Stage 2 extraction -- always use this format
**Example:**
```json
// Source: dblp_keywords_extract.py _prepare_keywords() Level 2 handling
[
  ["multi-agent reinforcement learning", "multi-agent RL", "MARL"],
  ["heterogeneous", "diverse", "asymmetric", "type-aware"],
  ["teammate modeling", "agent modeling", "active inference"]
]
// Matches: papers whose title contains (MARL OR multi-agent RL OR ...)
//  AND (heterogeneous OR diverse OR ...)
//  AND (teammate modeling OR agent modeling OR ...)
```

### Pattern 3: Venue Abbreviation Matching
**What:** `dblp_search.py` `is_venue_match()` uses lowercase substring matching on venue string
**When to use:** Adding venues to `search.default_venues`
**Example:**
```python
# Source: dblp_search.py is_venue_match()
# "aamas" matches:
#   - conf/ifaamas (AAMAS conference)
#   - journals/aamas (JAAMAS journal)
# "kdd" matches:
#   - conf/kdd (KDD conference)
#   - journals/tkde (if "kdd" appears in venue string)
```

### Anti-Patterns to Avoid
- **Do NOT modify pipeline scripts:** The scripts are configuration-driven by design. All changes go into `dblp_config.json`.
- **Do NOT use Level 3 nesting for Stage 2 keywords:** Level 3 (`[[[group1]], [[group2]]]`) triggers `extract_keywords_multi_group()` which runs independent queries and merges results. The CONTEXT.md prescribes a single Level 2 structure with 6 AND groups -- use exactly that.
- **Do NOT add author names to Stage 1 keywords:** DBLP keyword search matches against title/author/venue. Author names as keywords would pollute Stage 1 results. Keep Stage 1 to domain terminology only.
- **Do NOT use wildcard syntax in keywords:** DBLP API uses prefix matching natively. "heterogeneous" already matches "heterogeneously". No `*` or `?` needed.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DBLP query construction | Custom API client | `dblp_search.py` `build_queries()` | Handles Cartesian product, pagination params, rate limiting |
| Keyword matching logic | Custom substring matcher | `dblp_keywords_extract.py` `extract_keywords()` | Supports Level 2/3 nesting, case folding, accent stripping, matched_terms output |
| DOI deduplication | Custom duplicate detector | Built into `dblp_search.py` | Pipeline is idempotent by design |
| Output file naming | Custom filename builder | `build_output_filename()` in extract script | Handles Windows path length, special chars, hash fallback |

**Key insight:** This entire phase is a configuration exercise. The only "code" written is JSON content in an existing file. Every runtime concern (pagination, rate limiting, dedup, output formatting) is handled by existing scripts.

## Common Pitfalls

### Pitfall 1: Keyword-venue query explosion
**What goes wrong:** 25 keywords x 20 venues = 500 API queries. With 2-second sleep between queries, this takes ~17 minutes minimum.
**Why it happens:** The Cartesian product in `build_queries()` creates one query per keyword-venue pair.
**How to avoid:** This is expected behavior. The pipeline handles it with `sleep_time`, `jitter`, and `retry_total` settings. The ~17-minute runtime is acceptable for a one-time search. Do NOT reduce sleep_time below 2.0 to avoid rate limiting.
**Warning signs:** If Stage 1 returns 0 results for many keyword-venue pairs, keywords may be too specific for broad search.

### Pitfall 2: Stage 2 over-filtering
**What goes wrong:** 6 AND groups means a paper must match at least one term from ALL 6 groups. This is very restrictive and may produce < 50 results.
**Why it happens:** Each AND group is a hard filter. If Group 6 (Application Scenario) only matches "game" or "StarCraft", papers about "heterogeneous MARL for scheduling" that don't mention "game" would be excluded.
**How to avoid:** Consider whether all 6 groups should be ANDed, or whether some should be optional. CONTEXT.md D-04 prescribes all 6 as AND, but the planner should flag this as a calibration concern. A test run with the prescribed 6 groups should be done first; if results are too few, relaxing to 5 groups (dropping Group 6) is a reasonable adjustment within Claude's discretion.
**Warning signs:** Extraction produces < 50 results for ~5000+ broad search papers.

### Pitfall 3: DBLP rate limiting or timeouts
**What goes wrong:** DBLP API returns 429 or 503 errors during long search sessions.
**Why it happens:** 500 queries in rapid succession can trigger rate limits.
**How to avoid:** Existing config already has `sleep_time: 2.0`, `jitter_min: 0.5`, `jitter_max: 1.5`, `retry_total: 5`, `retry_backoff: 2.0`. These are conservative and should handle rate limiting. D-08 locks these settings -- do not change them.
**Warning signs:** Frequent retry messages in logs; total runtime exceeding 30 minutes.

### Pitfall 4: Venue abbreviation collision
**What goes wrong:** Adding "aamas" to venues might match unintended venues beyond AAMAS/JAAMAS.
**Why it happens:** Substring matching means "aamas" could theoretically match any venue string containing "aamas".
**How to avoid:** In practice, "aamas" only appears in `conf/ifaamas` and `journals/aamas` in DBLP. This is not a real risk but worth verifying after the test run by checking unique venues in the results CSV.
**Warning signs:** Unexpected venues appearing in broad search results.

### Pitfall 5: Year range too narrow
**What goes wrong:** 2024-2026 range misses seminal papers from 2020-2023 that established the field.
**Why it happens:** CONTEXT.md D-07 locks the year range to 2024-2026.
**How to avoid:** This is an intentional tradeoff. The researcher chose to focus on cutting-edge work. Seminal papers will be discovered through cross-reference discovery in Phase 16 (ITER-02).
**Warning signs:** Very few results for established topics like "value decomposition" or "QMIX" which were hot 2020-2022.

## Code Examples

### Stage 1 keyword list (JSON format)
```json
// Source: CONTEXT.md D-02, verified against dblp_config.json structure
"search": {
  "default_keywords": [
    "multi-agent reinforcement learning",
    "multi-agent RL",
    "MARL",
    "cooperative multi-agent",
    "decentralized execution",
    "CTDE",
    "heterogeneous agent",
    "heterogeneous multi-agent",
    "agent diversity",
    "asymmetric agents",
    "type-aware",
    "role-based",
    "diverse agent",
    "teammate modeling",
    "opponent modeling",
    "active inference",
    "Theory of Mind",
    "belief tracking",
    "agent modeling",
    "value decomposition",
    "credit assignment",
    "MAPPO",
    "QMIX",
    "communication-free",
    "ad-hoc teamwork",
    "cooperative coordination"
  ]
}
```

### Stage 2 AND/OR groups (JSON format)
```json
// Source: CONTEXT.md D-04, verified against dblp_keywords_extract.py Level 2 handling
"extract": {
  "default_keywords": [
    ["multi-agent reinforcement learning", "multi-agent RL", "MARL"],
    ["cooperative", "collaborative", "coordination"],
    ["heterogeneous", "diverse", "asymmetric", "type-aware", "role-based", "different action space"],
    ["teammate modeling", "opponent modeling", "agent modeling", "active inference", "Theory of Mind", "belief"],
    ["decentralized", "CTDE", "value decomposition", "policy gradient", "credit assignment"],
    ["game", "board game", "StarCraft", "planning", "scheduling", "robot"]
  ]
}
```

### Venue list with AAMAS added
```json
// Source: CONTEXT.md D-06, verified against dblp_search.py is_venue_match()
"search": {
  "default_venues": [
    "kdd", "icml", "neurips", "aaai", "ijcai", "iclr",
    "icde", "sigmod", "vldb", "tkde", "tmc", "www",
    "cvpr", "acl", "iccv", "pami", "sigir", "tpami",
    "aamas"
  ]
}
```
Note: "aamas" covers both AAMAS conference and JAAMAS journal via substring matching.

### Calibration test command
```bash
# Quick test with a single keyword to validate config and connectivity
cd /Users/zy/.ssh/RL-xiangqi
conda activate xqrl
python paper_collect/dblp_search.py --keywords "heterogeneous agent" --venues "aamas" --start-year 2024 --end-year 2026
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual keyword brainstorming | AIM-paper-anchored keyword extraction with synonym expansion | Phase 14 design | Systematic coverage of domain terminology |
| Wide year range (2020-2026) | Narrow year range (2024-2026) | D-07 | Focuses on cutting-edge; seminal work discovered via cross-references |
| 3 heterogeneous keywords | 7 heterogeneous keywords with synonyms | D-03 | Maximum recall for the primary innovation area |

**Deprecated/outdated:**
- "conf/aamas" venue abbreviation: DBLP discontinued this in 2007; modern AAMAS uses "conf/ifaamas" -- but substring matching with "aamas" handles both correctly.

## Open Questions

1. **Stage 2 AND group count (6 groups) may over-filter**
   - What we know: CONTEXT.md prescribes 6 AND groups. Each group must match at least one term.
   - What's unclear: Whether 6 AND groups produces a usable result set (100-300 papers).
   - Recommendation: Run the prescribed 6 groups first. If results < 50, consider dropping Group 6 (Application Scenario) as it is the least domain-specific group. This falls within Claude's discretion per CONTEXT.md.

2. **Exact count of Stage 1 keywords**
   - What we know: CONTEXT.md says "~25 keywords" across 5 semantic groups. The actual count from D-02 is 26 keywords.
   - What's unclear: Whether 26 keywords x 20 venues (520 queries) is acceptable or if deduplication is needed.
   - Recommendation: 26 is close enough to "~25". No deduplication needed -- let the pipeline handle it.

3. **Additional MARL venues beyond AAMAS**
   - What we know: CONTEXT.md D-06 says "add AAMAS + JAAMAS" (both covered by "aamas"). The 18 existing venues include major ML/AI conferences.
   - What's unclear: Whether specialized MARL venues like IFAAMAS workshops or ALA (Adaptive Learning Agents) should be added.
   - Recommendation: Stay with "aamas" as specified. Specialized workshops are better discovered through cross-reference in Phase 16.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=8.0 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` testpaths=["tests"] |
| Quick run command | `conda run -n xqrl pytest tests/ -x -q --timeout=30` |
| Full suite command | `conda run -n xqrl pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LIT-01 | dblp_config.json contains MARL keywords, not hypergraph/traffic keywords | unit | `conda run -n xqrl pytest tests/test_config_validation.py::test_marl_keywords_present -x` | No -- Wave 0 |
| LIT-01 | dblp_config.json has correct year range (2024-2026) | unit | `conda run -n xqrl pytest tests/test_config_validation.py::test_year_range -x` | No -- Wave 0 |
| LIT-02 | extract.default_keywords has Level 2 nesting with 6 AND groups | unit | `conda run -n xqrl pytest tests/test_config_validation.py::test_stage2_structure -x` | No -- Wave 0 |
| LIT-03 | search.default_venues contains "aamas" | unit | `conda run -n xqrl pytest tests/test_config_validation.py::test_aamas_venue -x` | No -- Wave 0 |
| LIT-01/02 | Calibration test run produces non-zero results from DBLP API | smoke | `python paper_collect/dblp_search.py --keywords "MARL" --venues "neurips" --start-year 2024 --end-year 2026` (manual) | N/A -- manual smoke test |

### Sampling Rate
- **Per task commit:** `conda run -n xqrl pytest tests/test_config_validation.py -x -q`
- **Per wave merge:** `conda run -n xqrl pytest tests/ -v`
- **Phase gate:** Full suite green + manual calibration test returns results

### Wave 0 Gaps
- [ ] `tests/test_config_validation.py` -- covers LIT-01 (MARL keywords present, no hypergraph/traffic keywords), LIT-02 (Level 2 nesting with 6 groups), LIT-03 (aamas in venues, year range)
- [ ] Calibration smoke test: manual DBLP API call to verify connectivity and result volume (not automated -- requires network)

## Sources

### Primary (HIGH confidence)
- `paper_collect/dblp_config.json` -- direct code analysis of existing config structure and content
- `paper_collect/dblp_search.py` -- direct code analysis of `build_queries()`, `is_venue_match()`, `fetch_query_results()`
- `paper_collect/dblp_keywords_extract.py` -- direct code analysis of `_prepare_keywords()`, `extract_keywords()`, `_get_nesting_level()`
- `papers/Wu 等 - 2025 - Think How Your Teammates Think Active Inference Can Benefit Decentralized Execution.md` -- AIM paper terminology source

### Secondary (MEDIUM confidence)
- DBLP API documentation (https://dblp.org/faq/How+to+use+the+dblp+search+API) -- confirmed prefix matching behavior, pagination params, rate limit guidance
- DBLP venue listing -- confirmed AAMAS conference key `conf/ifaamas` and JAAMAS journal key `journals/aamas`
- MARL terminology survey papers -- validated synonym groups for heterogeneous agents, teammate modeling, and cooperative MARL

### Tertiary (LOW confidence)
- Calibration target volumes (~5000-10000 broad, ~100-300 refined) -- estimated from SUMMARY.md and previous pipeline experience with different keywords; actual volumes will vary with MARL-domain keywords

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all components are existing code, directly analyzed
- Architecture: HIGH -- JSON config structure verified, pipeline data flow confirmed
- Pitfalls: HIGH -- based on direct code analysis of rate limiting, nesting behavior, and venue matching
- Keyword content: MEDIUM -- specific keyword selections come from CONTEXT.md user decisions; effectiveness depends on calibration test
- Calibration targets: LOW -- volume estimates are approximate and domain-dependent

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (stable -- no external dependencies that change frequently)
