---
phase: 03
slug: endgame-detection
status: draft
nyquist_compliant: false
wave_0_complete: false
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

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | END-01/02 | unit | `pytest tests/test_endgame.py -v` | ✅ | ⬜ pending |
| 03-01-02 | 01 | 1 | END-01/02 | unit | `pytest tests/test_endgame.py -v` | ✅ | ⬜ pending |
| 03-02-01 | 02 | 2 | END-03/04 | unit | `pytest tests/test_repetition.py -v` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_endgame.py` — stubs for END-01 (checkmate) and END-02 (stalemate) test fixtures
- [ ] `tests/test_repetition.py` — stubs for END-03 (long check) and END-04 (repetition draw) test fixtures
- [ ] `src/xiangqi/engine/endgame.py` — stub with `get_game_result()` that re-exports from `rules.py` (for Phase 2 test compat)

*Existing infrastructure: pytest, conftest.py, `make_state()` helper in test_rules.py.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stalemate = loss (困毙) in Xiangqi | END-02 | Confirmed by STATE.md and CONTEXT.md; covered by unit test `test_stalemate_also_loss` | See `tests/test_rules.py::TestGetGameResult::test_stalemate_also_loss` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
