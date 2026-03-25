---
phase: 6
slug: piece-interaction
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-qt 4.x |
| **Config file** | pyproject.toml (testpaths = ["tests"]) |
| **Quick run command** | `pytest tests/ui/test_board_interaction.py -x -q` |
| **Full suite command** | `pytest tests/ui/ -x` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ui/test_board_interaction.py -x -q`
- **After every plan wave:** Run `pytest tests/ui/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | UI-03 | unit | `pytest tests/ui/test_board_interaction.py::test_select_piece_shows_ring -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UI-03 | unit | `pytest tests/ui/test_board_interaction.py::test_select_piece_shows_legal_moves -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UI-04 | unit | `pytest tests/ui/test_board_interaction.py::test_click_legal_target_moves_piece -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UI-04 | unit | `pytest tests/ui/test_board_interaction.py::test_move_emits_signal -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UI-05 | unit | `pytest tests/ui/test_board_interaction.py::test_click_illegal_deselects -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UI-05 | unit | `pytest tests/ui/test_board_interaction.py::test_click_empty_deselects -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | D-24 | unit | `pytest tests/ui/test_board_interaction.py::test_black_turn_disabled -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | D-15 | unit | `pytest tests/ui/test_board_interaction.py::test_piece_index_lookup -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/ui/test_board_interaction.py` — stubs for UI-03, UI-04, UI-05
- [ ] `tests/ui/conftest.py` — add board_with_engine fixture if needed
- [ ] Verify `pytest-qt` installed (check pyproject.toml or run `pip list | grep pytest-qt`)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
