---
phase: 10
slug: observation-encoding-alpha-planes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing project) |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/test_rl.py -x -q` |
| **Full suite command** | `pytest tests/ -q --tb=short` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_rl.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | R3 (piece channels at start) | unit | `pytest tests/test_rl.py::test_observation_piece_channels_starting -x` | W0: test_rl.py exists | pending |
| 10-01-02 | 01 | 1 | R3 (canonical rotation fix) | unit | `pytest tests/test_rl.py::test_observation_canonical_rotation_black_to_move -x` | W0: test_rl.py exists | pending |
| 10-02-01 | 02 | 1 | R3 (repetition channel) | unit | `pytest tests/test_rl.py::test_observation_repetition_channel -x` | W0: test_rl.py exists | pending |
| 10-02-02 | 02 | 1 | R3 (halfmove channel) | unit | `pytest tests/test_rl.py::test_observation_halfmove_clock_channel -x` | W0: test_rl.py exists | pending |

*Status: pending · green · red · flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_rl.py` — 4 new test functions added for Phase 10 (D-10-10)
  - `test_observation_piece_channels_starting` — R3 piece channel encoding at start
  - `test_observation_canonical_rotation_black_to_move` — R3 canonical rotation
  - `test_observation_repetition_channel` — R3 repetition channel 14
  - `test_observation_halfmove_clock_channel` — R3 halfmove channel 15
- [ ] `tests/test_rl.py` — existing tests remain green (regression check)
- [ ] Framework install: gymnasium already added by Phase 09 — no new install needed

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | — | All phase behaviors have automated verification | — |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---
