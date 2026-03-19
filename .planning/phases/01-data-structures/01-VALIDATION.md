---
phase: 01
slug: data-structures
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | none — wave 0 creates `pyproject.toml` pytest section if needed |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01 | 01 | 1 | DATA-01, DATA-02, DATA-03 | unit | `pytest tests/test_types.py -v` | W0 | ⬜ pending |
| 01-02 | 01 | 1 | DATA-05 | unit | `pytest tests/test_constants.py -v` | W0 | ⬜ pending |
| 01-03 | 01 | 1 | DATA-04 | unit | `pytest tests/test_state.py -v` | W0 | ⬜ pending |
| 01-04 | 01 | 1 | TEST-01 | setup | fixtures + pytest install | W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — package marker
- [ ] `tests/conftest.py` — shared fixtures: `empty_board`, `starting_board`, `starting_state`
- [ ] `tests/test_types.py` — stubs for DATA-01/02/03 tests
- [ ] `tests/test_constants.py` — stubs for DATA-05 tests
- [ ] `tests/test_state.py` — stubs for DATA-04 tests
- [ ] `pyproject.toml` — add pytest dependency section if non-default settings needed
- [ ] `uv pip install pytest` — pytest not yet in project dependencies

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | — | — | — |

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
