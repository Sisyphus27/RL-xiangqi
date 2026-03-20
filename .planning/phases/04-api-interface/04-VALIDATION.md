---
phase: 4
slug: api-interface
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml (pytest section) |
| **Quick run command** | `pytest tests/test_api.py -v` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_api.py -v`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | API-01 | unit | `pytest tests/test_api.py -v -k "test_reset or test_apply"` | ✅ | ⬜ pending |
| 04-01-02 | 01 | 1 | API-01 | unit | `pytest tests/test_api.py -v -k "test_undo"` | ✅ | ⬜ pending |
| 04-01-03 | 01 | 1 | API-01 | unit | `pytest tests/test_api.py -v -k "test_legal_moves or test_is_legal"` | ✅ | ⬜ pending |
| 04-01-04 | 01 | 1 | API-01 | unit | `pytest tests/test_api.py -v -k "test_is_check"` | ✅ | ⬜ pending |
| 04-01-05 | 01 | 1 | API-01 | unit | `pytest tests/test_api.py -v -k "test_result"` | ✅ | ⬜ pending |
| 04-02-01 | 01 | 1 | API-02 | unit | `pytest tests/test_api.py -v -k "test_state_update"` | ✅ | ⬜ pending |
| 04-02-02 | 01 | 1 | API-03 | unit | `pytest tests/test_api.py -v -k "test_fen"` | ✅ | ⬜ pending |
| 04-03-01 | 01 | 2 | API-04 | perf | `pytest tests/test_perft.py -v` | ✅ | ⬜ pending |
| 04-04-01 | 01 | 2 | TEST-02 | integration | `pytest tests/test_pyffish.py -v` | ✅ (new) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_api.py` — stubs for all API-01..03 tests
- [ ] `tests/test_pyffish.py` — stubs for pyffish cross-validation (importorskip)
- [ ] `src/xiangqi/engine/engine.py` — stub class with all API methods (NotImplemented)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None — all phase behaviors have automated verification | API-04 | N/A | Run `pytest tests/test_perft.py --durations=5` and check durations |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
