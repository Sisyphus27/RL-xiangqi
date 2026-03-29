---
phase: 07
slug: ai-interface
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-qt (already in pyproject.toml) |
| **Config file** | None — see Wave 0 |
| **Quick run command** | `conda activate xqrl && pytest tests/ai/ tests/controller/ -v -x` |
| **Full suite command** | `conda activate xqrl && pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `conda activate xqrl && pytest tests/ai/ tests/controller/ -v -x`
- **After every plan wave:** Run `conda activate xqrl && pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | AI-01 | unit | `pytest tests/ai/test_base.py -x` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | AI-02 | unit | `pytest tests/ai/test_snapshot.py -x` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 1 | AI-03 | unit | `pytest tests/ai/test_random_ai.py -x` | ❌ W0 | ⬜ pending |
| 07-03-01 | 03 | 2 | AI-04, UI-06 | integration | `pytest tests/controller/test_game_controller.py -x` | ❌ W0 | ⬜ pending |
| 07-03-02 | 03 | 2 | UI-07 | integration | `pytest tests/controller/test_game_controller.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/ai/__init__.py` — package init
- [ ] `tests/ai/test_base.py` — AIPlayer ABC contract tests
- [ ] `tests/ai/test_snapshot.py` — EngineSnapshot immutability/copy tests
- [ ] `tests/ai/test_random_ai.py` — RandomAI with seed reproducibility
- [ ] `tests/ai/conftest.py` — shared AI test fixtures
- [ ] `tests/controller/__init__.py` — package init
- [ ] `tests/controller/test_game_controller.py` — GameController integration tests
- [ ] `tests/controller/conftest.py` — shared controller test fixtures

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | — | All phase behaviors have automated verification via pytest-qt | — |

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
