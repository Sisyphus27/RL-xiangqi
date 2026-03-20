# SUMMARY — Plan 02-03: Soldier Forward Direction Bug Fix

**Plan:** 02-03 | **Phase:** 02-move-generation | **Gap Closure:** TEST-01

## What was built

Single-line fix to `gen_soldier` forward direction + 5 updated test assertions in `TestGenSoldier`.

## Bug Root Cause

`gen_soldier` had inverted `forward_dr` values:
```python
# BEFORE (buggy):
forward_dr = +1 if color == +1 else -1  # red→row+1 (toward own home!), black→row-1

# AFTER (correct):
forward_dr = -1 if color == +1 else +1  # red→row-1 (toward enemy home ✓), black→row+1 ✓
```

Red soldiers at row 6 were moving toward row 7 (backward) instead of row 5 (forward). Black soldiers at row 3 were moving toward row 2 instead of row 4.

## Changes

| File | Change |
|------|--------|
| `src/xiangqi/engine/moves.py` | One-line fix: invert `forward_dr` ternary |
| `tests/test_moves.py` | 5 soldier test assertions corrected |
| `tests/test_rules.py` | Stalemate test comment updated (pre-existing design flaw documented) |

### Test Assertion Updates (test_moves.py)

| Test | Old Value | New Value |
|------|-----------|-----------|
| `test_red_soldier_pre_river` | `rc_to_sq(7, 3)` | `rc_to_sq(5, 3)` |
| `test_red_soldier_crossed_river` | `rc_to_sq(4, 3)` | `rc_to_sq(2, 3)` |
| `test_black_soldier_pre_river` | `rc_to_sq(2, 3)` | `rc_to_sq(4, 3)` |
| `test_black_soldier_crossed_river` | `rc_to_sq(5, 3)` | `rc_to_sq(7, 3)` |
| `test_soldier_captures_enemy` | enemy at row 7 | enemy at row 5 |

## Verification

```
perft(1) = 44        ✓ (CPW-verified)
perft(2) = 1,920    ✓ (CPW-verified)
perft(3) = 79,666   ✓ (CPW-verified)
perft(4) = 3,290,240 ✓ (CPW-verified)
TestGenSoldier: 5/5 PASS
Full suite: 101/102 PASS
```

## Known Issue

`test_stalemate_also_loss` (test_rules.py) has a pre-existing position design flaw. With correct SHI movement, the R_SHI pieces at (9,3) and (9,5) can move to (8,2) and (8,4) respectively, giving red legal moves. The test was only passing before due to a **compensating bug** in `gen_soldier` (the R_BING at (8,4) could not move forward with buggy direction). With the fix, the BING moves forward from (8,4) to (7,4), exposing that the position is not stalemate. Test position redesign needed as a follow-up.

**Result:** 101/102 tests pass. Gap TEST-01 closed.

## Self-Check

- [x] `forward_dr = -1 if color == +1 else +1` in gen_soldier (one-line fix)
- [x] perft(1)=44, perft(2)=1,920, perft(3)=79,666, perft(4)=3,290,240 (all CPW-verified)
- [x] 5 soldier test assertions updated
- [x] `test_soldier_captures_enemy` enemy position corrected (row 7 → row 5)
- [x] Stalemate test position flaw documented
- [x] Committed
