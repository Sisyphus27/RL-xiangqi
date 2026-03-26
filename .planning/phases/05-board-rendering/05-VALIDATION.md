---
phase: 05
slug: board-rendering
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (Python) |
| **Config file** | none — Wave 0 creates test structure |
| **Quick run command** | `python -m pytest tests/ui/ -v` |
| **Full suite command** | `python -m pytest tests/ui/ -v --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ui/ -v`
- **After every plan wave:** Run `python -m pytest tests/ui/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | UI-01 | unit | `python -c "from src.xiangqi.ui.constants import ..."` | — | pending |
| 05-01-02 | 01 | 1 | UI-01 | unit | `python -c "from src.xiangqi.ui.constants import ..."` | — | pending |
| 05-02-01 | 02 | 1 | UI-01, UI-02 | unit | `pytest tests/ui/test_board.py -v` | W0 | pending |
| 05-03-01 | 03 | 2 | UI-01, UI-02 | unit | `pytest tests/ui/test_main.py -v` | W0 | pending |
| 05-03-02 | 03 | 2 | UI-01, UI-02 | unit | `pytest tests/ui/test_constants.py -v` | W2 | pending |
| 05-03-03 | 03 | 2 | UI-01, UI-02 | unit | `pytest tests/ui/test_piece_item.py -v` | W2 | pending |

*Status: pending · green · red · flaky*

---

## Wave 0 Requirements

- [ ] `tests/ui/__init__.py` — package marker
- [ ] `tests/ui/conftest.py` — shared fixtures (QApplication, XiangqiState.starting())
- [ ] `tests/ui/test_constants.py` — color/font/size constant tests
- [ ] `tests/ui/test_piece_item.py` — PieceItem and BoardBackgroundItem tests
- [ ] `tests/ui/test_board.py` — QXiangqiBoard initialization and resize tests
- [ ] `tests/ui/test_main.py` — MainWindow title and central widget tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Green felt board background visible | UI-01 | Visual confirmation requires human eye | Run app, screenshot board, verify `#7BA05B` green felt background |
| Red pieces (#CC2200) vs black pieces (#1A1A1A) | UI-02 | Color accuracy requires visual inspection | Run app, verify red pieces appear red, black pieces appear black |
| River gap (no line between rows 4-5) | UI-01 | Visual inspection of grid break | Run app, confirm horizontal line breaks at river |
| Palace diagonals drawn correctly | UI-01 | Visual inspection of diagonal lines | Run app, verify 4 palace diagonal lines present |
| Window title "RL-Xiangqi v0.2" | UI-01 | String matching from window | Run app, check window title bar |
| Aspect ratio preserved on resize | UI-01 | Visual inspection | Resize window, verify board stays 9:10 ratio |

*Automated tests cover unit-level correctness; manual verification covers visual output.*

---

## Validation Sign-Off

- [ ] All tasks have automated or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all test file stubs
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---

*Generated from: 05-RESEARCH.md Validation Architecture section*
