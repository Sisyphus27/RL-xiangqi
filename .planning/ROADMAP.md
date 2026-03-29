# Roadmap: RL-Xiangqi

## Milestones

- **v0.1** - Xiangqi Rule Engine (2026-03-19) [[archived]](milestones/v0.1-ROADMAP.md)
- **v0.2** - PyQt6 UI + RandomAI + AI Interface (2026-03-26) [[archived]](milestones/v0.2-ROADMAP.md)
- **v0.3** - Multi-Agent Gymnasium RL Environment (2026-03-29) [[archived]](milestones/v0.3-ROADMAP.md)
- **v1.0** - Heterogeneous Agent Predictive Collaboration Literature Pipeline (in progress)

## Phases

<details>
<summary>v0.1 Core Engine (Phases 01-04) — SHIPPED 2026-03-19</summary>

- [x] Phase 01: Board & State (4/4 plans)
- [x] Phase 02: Move Generation (4/4 plans)
- [x] Phase 03: Endgame Rules (4/4 plans)
- [x] Phase 04: Engine Public API (5/5 plans)

</details>

<details>
<summary>v0.2 PyQt6 UI + RandomAI (Phases 05-08) — SHIPPED 2026-03-26</summary>

- [x] Phase 05: Board Rendering (5/5 plans)
- [x] Phase 06: Piece Interaction (6/6 plans)
- [x] Phase 07: AI Interface (6/6 plans)
- [x] Phase 08: Game Control (5/5 plans)

</details>

<details>
<summary>v0.3 Gymnasium RL Environment (Phases 09-13) — SHIPPED 2026-03-29</summary>

- [x] Phase 09: XiangqiEnv Core (5/5 plans) — completed 2026-03-27
- [x] Phase 10: Observation Encoding (2/2 plans) — completed 2026-03-28
- [x] Phase 11: Per-Piece-Type Action Masking (2/2 plans) — completed 2026-03-28
- [x] Phase 12: Self-Play E2E Validation (1/1 plan) — completed 2026-03-28
- [x] Phase 13: Fix Test Suite (1/1 plan) — completed 2026-03-29

</details>

### v1.0 Literature Pipeline (In Progress)

**Phase Numbering:**
- Integer phases (14, 15, 16): Planned milestone work
- Decimal phases (14.1, 15.1): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 14: MARL Keyword Design** - Redesign dblp_config.json with two-stage MARL-domain keywords and AAMAS venue
- [ ] **Phase 15: Paper Collection** - Run broad search and refined extraction pipeline to generate shortlist
- [ ] **Phase 16: Manual Screening & Iteration** - Screen papers, collect full-text, iterate keywords, cross-reference discover

## Phase Details

### Phase 14: MARL Keyword Design
**Goal**: Researchers have a MARL-domain keyword configuration that produces targeted search results via the existing pipeline
**Depends on**: Nothing (first phase of v1.0)
**Requirements**: LIT-01, LIT-02, LIT-03
**Success Criteria** (what must be TRUE):
  1. Researcher can open dblp_config.json and see broad search keywords covering MARL core terminology (multi-agent RL, heterogeneous agents, teammate modeling, active inference, predictive collaboration)
  2. Researcher can identify the two-stage keyword structure: Stage 1 keywords for broad retrieval, Stage 2 nested AND/OR groups for refined extraction
  3. Researcher can confirm AAMAS is listed among the target venues in dblp_config.json
  4. A test run of dblp_search.py with the new config returns results (volume can be calibrated in Phase 15)
**Plans**: TBD

Plans:
- [ ] 14-01: TBD
- [ ] 14-02: TBD

### Phase 15: Paper Collection
**Goal**: Researchers have a filtered shortlist of candidate papers ready for manual review
**Depends on**: Phase 14
**Requirements**: LIT-04, LIT-05
**Success Criteria** (what must be TRUE):
  1. Researcher can run `python dblp_search.py` and it produces a CSV file with broad search results from DBLP
  2. Researcher can run `python dblp_keywords_extract.py` and it produces a shortlist Excel file with papers matching the refined AND/OR keyword criteria
  3. The shortlist contains a manageable number of papers (target: 100-300 after extraction) with title, authors, venue, year, and DOI columns
  4. DOI deduplication works correctly -- re-running the pipeline does not produce duplicate entries
**Plans**: TBD

Plans:
- [ ] 15-01: TBD
- [ ] 15-02: TBD

### Phase 16: Manual Screening & Iteration
**Goal**: Researchers have a curated set of included papers with full-text collected, and the keyword configuration has been refined based on screening feedback
**Depends on**: Phase 15
**Requirements**: LIT-06, LIT-07, ITER-01, ITER-02
**Success Criteria** (what must be TRUE):
  1. Researcher has reviewed every paper in the shortlist and recorded include/exclude decisions with reasons in a screening CSV
  2. Every included paper has its full text collected and saved as markdown in the papers/ directory
  3. Researcher can identify at least one keyword refinement made based on screening feedback (e.g., added synonym, narrowed scope, expanded term)
  4. Researcher has reviewed reference lists of included papers and added any missing relevant papers to the collection
  5. The final included paper set is documented with paper count and key coverage areas identified
**Plans**: TBD

Plans:
- [ ] 16-01: TBD
- [ ] 16-02: TBD
- [ ] 16-03: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 14 -> 15 -> 16

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 01-04 | v0.1 | 17/17 | Complete | 2026-03-19 |
| 05-08 | v0.2 | 22/22 | Complete | 2026-03-26 |
| 09 | v0.3 | 5/5 | Complete | 2026-03-27 |
| 10 | v0.3 | 2/2 | Complete | 2026-03-28 |
| 11 | v0.3 | 2/2 | Complete | 2026-03-28 |
| 12 | v0.3 | 1/1 | Complete | 2026-03-28 |
| 13 | v0.3 | 1/1 | Complete | 2026-03-29 |
| 14 | v1.0 | 0/2 | Not started | - |
| 15 | v1.0 | 0/2 | Not started | - |
| 16 | v1.0 | 0/3 | Not started | - |

---
*Roadmap updated: v1.0 milestone started 2026-03-29*
