---
phase: 02
slug: move-generation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 8.0 |
| **Config file** | `pyproject.toml` (existing from Phase 1) |
| **Quick run command** | `python -m pytest tests/test_moves.py tests/test_legal.py -v --tb=short` |
| **Full suite command** | `python -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_moves.py tests/test_legal.py -v --tb=short`
- **After every plan wave:** Run `python -m pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | MOVE-01 | unit | `pytest tests/test_moves.py::test_gen_general -x` | tests/test_moves.py (Wave 0) | ⬜ pending |
| 02-01-02 | 01 | 1 | MOVE-02 | unit | `pytest tests/test_moves.py::test_gen_chariot -x` | tests/test_moves.py (Wave 0) | ⬜ pending |
| 02-01-03 | 01 | 1 | MOVE-03 | unit | `pytest tests/test_moves.py::test_gen_horse -x` | tests/test_moves.py (Wave 0) | ⬜ pending |
| 02-01-04 | 01 | 1 | MOVE-04 | unit | `pytest tests/test_moves.py::test_gen_cannon -x` | tests/test_moves.py (Wave 0) | ⬜ pending |
| 02-01-05 | 01 | 1 | MOVE-05 | unit | `pytest tests/test_moves.py::test_gen_advisor -x` | tests/test_moves.py (Wave 0) | ⬜ pending |
| 02-01-06 | 01 | 1 | MOVE-06 | unit | `pytest tests/test_moves.py::test_gen_elephant -x` | tests/test_moves.py (Wave 0) | ⬜ pending |
| 02-01-07 | 01 | 1 | MOVE-07 | unit | `pytest tests/test_moves.py::test_gen_soldier -x` | tests/test_moves.py (Wave 0) | ⬜ pending |
| 02-02-01 | 02 | 1 | RULE-01 | unit | `pytest tests/test_legal.py::test_is_legal_move -x` | tests/test_legal.py (Wave 0) | ⬜ pending |
| 02-02-02 | 02 | 1 | RULE-02 | unit | `pytest tests/test_legal.py::test_generate_legal_moves_starting -x` | tests/test_legal.py (Wave 0) | ⬜ pending |
| 02-02-03 | 02 | 1 | RULE-03 | unit | `pytest tests/test_legal.py::test_is_in_check -x` | tests/test_legal.py (Wave 0) | ⬜ pending |
| 02-02-04 | 02 | 1 | RULE-04 | unit | `pytest tests/test_legal.py::test_no_self_check -x` | tests/test_legal.py (Wave 0) | ⬜ pending |
| 02-02-05 | 02 | 2 | RULE-05 | unit | `pytest tests/test_rules.py::test_face_to_face_rule -x` | tests/test_rules.py (Wave 0) | ⬜ pending |
| 02-02-06 | 02 | 2 | RULE-06 | unit | `pytest tests/test_rules.py::test_get_game_result -x` | tests/test_rules.py (Wave 0) | ⬜ pending |
| 02-03-01 | 03 | 2 | TEST-01 | perft | `pytest tests/test_perft.py -x` | tests/test_perft.py (Wave 0) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_moves.py` — stubs for MOVE-01..MOVE-07 (7 per-piece generator tests)
- [ ] `tests/test_legal.py` — stubs for RULE-01..RULE-04 (is_legal_move, generate_legal_moves, is_in_check, no-self-check)
- [ ] `tests/test_rules.py` — stubs for RULE-05 (face-to-face), RULE-06 (get_game_result)
- [ ] `tests/test_perft.py` — stub for TEST-01 (perft depth 1-3 vs CPW reference values)
- [ ] `tests/conftest.py` — extend with Phase 2 fixtures: `fen_state(fen)`, `blocked_horse_board`, `face_to_face_board`
- [ ] `src/xiangqi/engine/moves.py` — all 7 gen_* functions
- [ ] `src/xiangqi/engine/legal.py` — is_in_check, is_legal_move, generate_legal_moves, apply_move
- [ ] `src/xiangqi/engine/rules.py` — face-to-face rule, flying_general_violation

*(All Wave 0 files are new — no existing test infrastructure for move generation)*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None — all phase behaviors have automated verification | — | — | — |

---

## Important Note: Perft Reference Values

**REQUIREMENTS.md TEST-01 contains incorrect perft numbers.**
Use CPW-verified values instead:

| Depth | REQUIREMENTS.md | CPW Reference (correct) |
|-------|----------------|------------------------|
| 1 | 44 | 44 |
| 2 | 1,916 | **1,920** |
| 3 | 72,987 | **79,666** |

Tests must use CPW values (1,920 and 79,666) as assertions.

---

## Validation Sign-Off

- [ ] All tasks have automated verification
- [ ] Wave 0 stubs created before implementation tasks
- [ ] All 13 MOVE/RULE requirements covered
- [ ] Perft cross-validated against CPW reference (not REQUIREMENTS.md)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
