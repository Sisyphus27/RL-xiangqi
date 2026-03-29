---
phase: 11
slug: per-piece-type-action-masking
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml (tool.pytest) |
| **Quick run command** | `conda run -n xqrl --no-banner pytest tests/test_rl.py -x -q` |
| **Full suite command** | `conda run -n xqrl --no-banner pytest tests/test_rl.py -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `conda run -n xqrl --no-banner pytest tests/test_rl.py -x -q`
- **After every plan wave:** Run `conda run -n xqrl --no-banner pytest tests/test_rl.py -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | R4 | unit | `pytest tests/test_rl.py::test_get_legal_mask -v` | ✅ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | R4 | unit | `pytest tests/test_rl.py::test_get_piece_legal_mask -v` | ✅ W0 | ⬜ pending |
| 11-01-03 | 01 | 1 | R5 | unit | `pytest tests/test_rl.py::test_reward_sign -v` | ✅ W0 | ⬜ pending |
| 11-02-01 | 02 | 1 | R5 | unit | `pytest tests/test_rl.py::test_soldier_river_value -v` | ✅ W0 | ⬜ pending |
| 11-02-02 | 02 | 1 | R5 | unit | `pytest tests/test_rl.py::test_illegal_penalty -v` | ✅ W0 | ⬜ pending |
| 11-02-03 | 02 | 1 | R4+R5 | unit | `pytest tests/test_rl.py::test_non_current_player_mask -v` | ✅ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_rl.py` — existing file, add new test functions for R4/R5
- [ ] `src/xiangqi/rl/env.py` — existing file, modify public API and reward

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
