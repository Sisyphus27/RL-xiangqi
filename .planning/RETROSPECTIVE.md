# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v0.1 — Core Engine

**Shipped:** 2026-03-21
**Phases:** 7 | **Plans:** 11 | **Sessions:** ~8
**Commits:** 93 | **Files changed:** 93 | **Lines added:** 22,774
**Timeline:** 2026-03-19 → 2026-03-21 (2 days)

---

### What Was Built

- Full Xiangqi rule engine in pure Python: board representation, all 7 piece move generators, legal move validation with king-safety checks, FEN parsing/roundtrip
- CPW-verified perft numbers (depth 1-4): 44 / 1,920 / 79,666 / 3,290,240
- Endgame detection: checkmate, stalemate (kunbi=loss), threefold repetition, long-check draw, long-chase penalty
- XiangqiEngine facade: clean public API wrapping all internal modules, full undo/redo stack
- Performance: 58x speedup in `legal_moves()` via geometry pre-filter (29ms → 0.5ms)

### What Worked

- Phase-level execution with GSD: each phase was self-contained and independently verifiable
- CPW perft reference values caught 3 critical bugs (soldier direction, elephant home-half, general capture tracking)
- Bug isolation: Phase 04.1 fixed geometry validation and performance in one targeted plan without destabilizing other phases
- Test-first: 179 passing tests by end of milestone; boundary cases (stalemate geometry) forced deeper understanding of rules

### What Was Inefficient

- Phase 02.1 (stalemate test fix) and 02.2 (tech debt) were unplanned gap-closure phases — added 2 extra phases after initial scope
- VERIFICATION.md files went stale; perft bug shown as FAILED in docs while tests passed — documentation drift
- `02-03-SUMMARY.md` named incorrectly as `SUMmary.md` initially — minor friction in tool parsing
- pyffish cross-validation skipped entirely — platform dependency (stockfish) not addressed early

### Patterns Established

- Decimal phase numbering (02.1, 02.2, 04.1) for urgent post-scope insertions — proved effective for gap closure
- CPW perft verification as standard for any move-generation change
- Geometry pre-validation before board copy for O(1) rejection of obviously illegal moves
- WXO rules (long check = draw, long chase = chaser loses) confirmed as the rule standard

### Key Lessons

1. Perft numbers from CPW/Fairy-Stockfish are the single most reliable regression test — always verify against them early
2. Stalemate in Xiangqi (kunbi) means loss, not draw — this non-obvious rule must be verified per game, not per board state
3. Elephant/horse "blocking piece" geometry bugs are easy to introduce and hard to catch with unit tests alone — need integration-level perft checks
4. Phase summaries without one-liner fields make milestone completion backfill harder — add them during phase close

### Cost Observations

- Model mix: ~60% Sonnet 4, ~30% Opus 4, ~10% Haiku
- Sessions: ~8 (spanning 3 days across 2 calendar days)
- Notable: Most expensive session was Phase 02 (move generation) at ~480s due to perft bug investigation

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v0.1 | ~8 | 7 | Initial GSD workflow; decimal phases for gap closure; CPW perft as standard |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v0.1 | 179 | ~90% (estimated) | 0 (engine-only, no deps yet) |

### Top Lessons (Verified Across Milestones)

*(First milestone — no cross-milestone data yet)*
