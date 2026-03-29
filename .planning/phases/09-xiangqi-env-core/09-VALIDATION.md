---
phase: 09
slug: xiangqi-env-core
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-26
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing project) |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/test_rl.py -x -q` |
| **Full suite command** | `pytest tests/ -q --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_rl.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | R1 (reset obs shape) | unit | `pytest tests/test_rl.py::test_reset_returns_correct_shapes -x` | ✅ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | R1 (action space) | unit | `pytest tests/test_rl.py::test_action_space_discrete_8100 -x` | ✅ W0 | ⬜ pending |
| 09-01-03 | 01 | 1 | R2 (piece_masks dict) | unit | `pytest tests/test_rl.py::test_piece_masks_shape -x` | ✅ W0 | ⬜ pending |
| 09-01-04 | 01 | 1 | R8 (env independence) | unit | `pytest tests/test_rl.py::test_env_instances_independent -x` | ✅ W0 | ⬜ pending |
| 09-02-01 | 02 | 1 | R1 (step legal move) | unit | `pytest tests/test_rl.py::test_step_accepts_valid_action -x` | ✅ W0 | ⬜ pending |
| 09-02-02 | 02 | 1 | R6 (checkmate detection) | unit | `pytest tests/test_rl.py::test_checkmate_detection -x` | ✅ W0 | ⬜ pending |
| 09-02-03 | 02 | 1 | R6 (repetition draw) | unit | `pytest tests/test_rl.py::test_repetition_draw -x` | ✅ W0 | ⬜ pending |
| 09-02-04 | 02 | 1 | R6 (illegal move penalty) | unit | `pytest tests/test_rl.py::test_illegal_move_penalty -x` | ✅ W0 | ⬜ pending |
| 09-03-01 | 03 | 2 | R8 (SyncVectorEnv) | integration | `pytest tests/test_rl.py::test_sync_vector_env -x` | ✅ W0 | ⬜ pending |
| 09-03-02 | 03 | 2 | R6 (50-move rule) | unit | `pytest tests/test_rl.py::test_50_move_rule -x` | ✅ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_rl.py` — stubs for all R1/R2/R6/R8 tests
- [ ] `tests/conftest.py` — shared fixtures if needed
- [ ] Add `gymnasium` to `pyproject.toml` dependencies

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SyncVectorEnv n_envs=2 completes games without crash | R8 | Requires multi-process; can be flaky on CI | `pytest tests/test_rl.py::test_sync_vector_env -x -s` — watch for deadlocks |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
