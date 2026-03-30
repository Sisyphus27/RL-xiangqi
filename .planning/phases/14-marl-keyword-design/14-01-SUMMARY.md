---
phase: 14-marl-keyword-design
plan: 01
subsystem: literature-search
tags: [dblp, marl, keyword-design, config, two-stage-pipeline]

# Dependency graph
requires:
  - phase: none
    provides: "No prior phase dependency — standalone config redesign"
provides:
  - "MARL-domain keyword configuration in dblp_config.json ready for two-stage pipeline execution"
  - "26 Stage 1 broad search keywords across 5 semantic groups"
  - "6 Stage 2 AND/OR extraction groups with Level 2 nesting"
  - "19 venues including AAMAS (covers both AAMAS conf and JAAMAS journal)"
  - "Year range 2024-2026"
affects: [15-paper-collection, 16-manual-screening]

# Tech tracking
tech-stack:
  added: [requests, pandas, tqdm, openpyxl]
  patterns: [two-stage-keyword-pipeline, level2-nested-and-or-arrays]

key-files:
  created: []
  modified:
    - "paper_collect/dblp_config.json"

key-decisions:
  - "26 MARL keywords organized into 5 semantic groups per CONTEXT.md D-01 through D-03"
  - "6 AND/OR extraction groups with Level 2 nesting per CONTEXT.md D-04, D-05"
  - "AAMAS added as single venue covering both conference and journal via substring matching"
  - "Year range narrowed to 2024-2026 per CONTEXT.md D-07"

patterns-established:
  - "Two-stage keyword design: flat list for broad search (Stage 1), nested AND/OR for refined extraction (Stage 2)"
  - "Level 2 nested arrays [[OR-group1], [OR-group2], ...] where inner lists are OR synonyms and outer list is AND"

requirements-completed: [LIT-01, LIT-02, LIT-03]

# Metrics
duration: 3min
completed: 2026-03-30
---

# Phase 14 Plan 01: MARL Keyword Configuration Summary

**Two-stage MARL keyword pipeline configuration with 26 broad search terms across 5 semantic groups and 6 AND/OR extraction groups, validated against live DBLP API**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-30T02:25:48Z
- **Completed:** 2026-03-30T02:29:32Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Replaced all 34 hypergraph/traffic keywords with 26 MARL-domain keywords across 5 semantic groups (MARL Core, Heterogeneous & Roles, Modeling & Inference, Value Decomposition, Collaboration & Communication)
- Configured 6 Level 2 nested AND/OR extraction groups for Stage 2 refined filtering
- Added AAMAS venue (19 total), narrowed year range to 2024-2026, preserved all infrastructure settings
- Validated configuration with live DBLP API query ("MARL neurips" returned 5 results in under 3 seconds)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write MARL keyword configuration into dblp_config.json** - `dd736a7` (feat)

**Plan metadata:** pending (docs commit below)

## Files Created/Modified
- `paper_collect/dblp_config.json` - Complete two-stage MARL keyword configuration (26 Stage 1 keywords, 6 Stage 2 AND/OR groups, 19 venues, year range 2024-2026)

## Decisions Made
- Installed requests, pandas, tqdm, openpyxl into xqrl conda environment (needed for calibration test; environment was minimal with only core packages)
- No keyword deduplication needed -- 26 keywords is close enough to the ~25 target per D-02

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing Python dependencies in xqrl conda environment**
- **Found during:** Task 2 (DBLP API calibration test)
- **Issue:** xqrl environment was missing requests, pandas, tqdm, openpyxl -- required by dblp_search.py for the calibration test
- **Fix:** Ran `conda run -n xqrl pip install requests pandas tqdm openpyxl`
- **Files modified:** None (conda environment packages, not repo files)
- **Verification:** Calibration test ran successfully, returned 5 results from DBLP API
- **Committed in:** N/A (environment change, not repo commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential for completing calibration test. No scope creep.

## Issues Encounted
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- dblp_config.json is ready for Phase 15 paper collection -- run `dblp_search.py` with default config for full Stage 1 broad search (26 keywords x 19 venues = 494 API queries, estimated ~17 minutes)
- After Stage 1 completes, run `dblp_keywords_extract.py` for Stage 2 refined extraction (6 AND/OR groups filtering on paper titles)
- Target volumes: ~5000-10000 from broad search, ~100-300 after extraction. If Stage 2 produces fewer than 50 results, consider relaxing Group 6 (Application Scenario) as noted in RESEARCH.md open questions.

## Self-Check: PASSED

- FOUND: paper_collect/dblp_config.json
- FOUND: .planning/phases/14-marl-keyword-design/14-01-SUMMARY.md
- FOUND: commit dd736a7

---
*Phase: 14-marl-keyword-design*
*Completed: 2026-03-30*
