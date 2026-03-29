---
phase: 12
slug: environment-validation-self-play-e2e
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `/c/software/miniconda/envs/xqrl/python.exe -m pytest tests/test_selfplay.py -s --timeout=300 -x` |
| **Full suite command** | `/c/software/miniconda/envs/xqrl/python.exe -m pytest tests/ -s --timeout=300 -x` |
| **Estimated runtime** | ~90 seconds (74s self-play + test overhead) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_selfplay.py -s --timeout=300 -x`
- **After every plan wave:** Run `pytest tests/ -s --timeout=300 -x`
- **Before `/gsd:verify-work`:** Full suite must be green (29 existing + new self-play tests)
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | R7 | integration | `pytest tests/test_selfplay.py -s --timeout=300` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_selfplay.py` — self-play E2E validation test (R7)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | -- | -- | -- |

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
