---
phase: 03
slug: endgame-detection
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-20
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` (existing) |
| **Quick run command** | `pytest tests/test_endgame.py tests/test_repetition.py -v` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_endgame.py tests/test_repetition.py -v`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Automated Command | Status |
|---------|------|------|-------------|-------------------|--------|
| 03-01-01 | 01 | 1 | END-01/02 | `pytest tests/test_endgame.py::TestCheckmate -v` | pending |
| 03-01-02 | 01 | 1 | END-01/02 | `pytest tests/test_endgame.py::TestStalemate -v` | pending |
| 03-01-03 | 01 | 1 | END-03/04 | `python -c "from src.xiangqi.engine.repetition import RepetitionState; ..."` | pending |
| 03-01-04 | 01 | 1 | Phase 2 compat | `pytest tests/test_rules.py -v` | pending |
| 03-01-05 | 01 | 1 | API hygiene | `python -c "from src.xiangqi.engine.legal import *"` | pending |
| 03-01-06 | 01 | 1 | END-01/02 | `pytest tests/test_endgame.py -v` | pending |
| 03-01-07 | 01 | 2 | END-03/04 | `pytest tests/test_repetition.py -v` | pending |

*Status: pending · green · red · flaky*

---

## Wave 0 Status

Wave 0 is complete (the plan itself documents all wave 0 requirements as preconditions).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stalemate = loss (困毙) in Xiangqi | END-02 | Confirmed by STATE.md and CONTEXT.md; covered by unit test `test_stalemate_also_loss` | See `tests/test_endgame.py::TestStalemate::test_stalemate_also_loss` |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
