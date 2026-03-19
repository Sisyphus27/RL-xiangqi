---
phase: 01-data-structures
plan: 02
status: complete
---

## Summary

**What was built:** XiangqiState dataclass with Zobrist hashing (DATA-04), pyproject.toml with numpy/pytest, and shared pytest fixtures in conftest.py

**Tasks:** 3/3 complete
**Files:**
- `src/xiangqi/engine/state.py` (140 lines) — XiangqiState, compute_hash, update_hash, _find_king_positions
- `pyproject.toml` (18 lines) — numpy>=2.0,<3.0, pytest>=8.0, hatchling build backend
- `tests/conftest.py` (32 lines) — empty_board, starting_board, starting_state fixtures
- `tests/test_state.py` (145 lines) — 13 tests covering all DATA-04 requirements

## Completed Tasks

- Task 1: Create src/xiangqi/engine/state.py (DATA-04 + king_positions) -- 186ea97
- Task 2: Create pyproject.toml and tests/conftest.py -- 6df38b6
- Task 3: Create tests/test_state.py (DATA-04) -- 97cb7d6

## Verification

All 28 tests pass (13 new + 15 existing). Run: `python3.11 -m pytest tests/ -v --tb=short`

```
tests/test_constants.py .........  [32%]
tests/test_state.py .............  [78%]
tests/test_types.py ......        [100%]
28 passed in 0.06s
```

## Issues

None -- plan executed exactly as written. No deviations.

## Key Implementation Notes

- `_zobrist_piece` shape `(15, 90)`: index `piece_value + 7` maps -7..+7 to 0..14; index 7 = EMPTY (not hashed)
- `_init_zobrist()` called eagerly at module import with seed `0x20240319`
- Turn bit XORed at `_zobrist_piece[14, 0]` (unused slot)
- `king_positions` dict initialized by `_find_king_positions()` O(90) scan at state creation
- `XiangqiState.from_fen()` and `starting()` class methods; `copy()` deep-copies all mutable fields

## Commits

| Hash | Message |
|------|---------|
| 186ea97 | feat(01-02): create src/xiangqi/engine/state.py with XiangqiState dataclass |
| 6df38b6 | feat(01-02): add pyproject.toml and tests/conftest.py fixtures |
| 97cb7d6 | test(01-02): add tests/test_state.py covering DATA-04 |

**Duration:** 120s
**Completed:** 2026-03-19
