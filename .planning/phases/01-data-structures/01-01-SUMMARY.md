---
phase: 01-data-structures
plan: 01
status: complete
---

## Summary

**What was built:** Piece IntEnum with pinyin names and Chinese character repr, 16-bit move encoding/decoding with correct bit layout (bits 0-8=from_sq, bits 9-15=to_sq, bit 16=is_capture), WXF FEN parser/serializer, and boolean ndarray boundary masks for palace/river/elephant-home zones.

**Tasks:** 4/4 complete

**Files:**
- `src/xiangqi/engine/__init__.py` — empty package marker
- `src/xiangqi/engine/types.py` — Piece IntEnum, encode_move, decode_move, rc_to_sq, sq_to_rc
- `src/xiangqi/engine/constants.py` — STARTING_FEN, IN_PALACE, IN_RIVER, IN_BLACK_HOME, IN_RED_HOME, from_fen, to_fen
- `tests/__init__.py` — empty package marker
- `tests/test_types.py` — 6 tests covering DATA-01/02/03
- `tests/test_constants.py` — 9 tests covering DATA-05

## Completed Tasks

- Task 1: `src/xiangqi/engine/types.py` — Piece IntEnum with pinyin names and Chinese __repr__, move encoding/decoding, sq/rc helpers — commit ed8bb55
- Task 2: `tests/test_types.py` — 6 tests: piece values, repr Chinese chars, IntEnum arithmetic, 90x90 encode/decode roundtrip, rc/sq helpers, capture bit isolation — commit e387bc9
- Task 3: `src/xiangqi/engine/constants.py` — STARTING_FEN, IN_PALACE, IN_RIVER, IN_BLACK_HOME, IN_RED_HOME, from_fen, to_fen — commit 1d93424
- Task 4: `tests/test_constants.py` — 9 tests: palace/river/home-half masks, red/black back ranks, pawn rows, FEN roundtrip — commit e85a8d9

## Verification

All 15 automated tests pass:
```
pytest tests/test_types.py tests/test_constants.py -v --tb=short
========================= 15 passed in 0.06s =========================
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] IntEnum `_CHARS` dict conflict**
- **Found during:** Task 1
- **Issue:** Defining `_CHARS` as a class attribute inside `class Piece(IntEnum)` caused Python to treat it as an enum member, raising `TypeError: int() argument must be a string, a bytes-like object or a number, not 'dict'`.
- **Fix:** Moved `_PIECE_CHARS` to module-level before the class definition; `__repr__` accesses it via closure.
- **Files modified:** `src/xiangqi/engine/types.py`
- **Commit:** ed8bb55

**2. [Rule 1 - Bug] Move encoding masks corrected (bit overlap)**
- **Found during:** Task 1
- **Issue:** The plan's stated masks (`_TO_MASK = 0x3FE00`, decode `to_sq = (m>>9)&0x1FF`) had a bit overlap bug: bit 16 was simultaneously part of `to_sq` (bits 9-17 = 9 bits) AND the capture flag. When both `to_sq=81` and `is_capture=True`, the encode produced `to_sq` with bit 16 set, and decode extracted it via `(m>>9)&0x1FF` (which includes bit 16 in positions 0-8).
- **Fix:** Reorganized bit layout to: bits 0-8=from_sq (9 bits), bits 9-15=to_sq (7 bits, range 0-89), bit 16=is_capture. Updated `_TO_MASK = 0xFE00` and decode `to_sq` mask to `0x7F`. Full 90x90 roundtrip verified.
- **Files modified:** `src/xiangqi/engine/types.py`
- **Commit:** ed8bb55

## Requirements Covered

| Req ID | Description | Verified |
|--------|-------------|----------|
| DATA-01 | Board as np.ndarray(10,9,dtype=np.int8), 0=empty, +/-1..+/-7 | Via test_types.py::test_piece_values |
| DATA-02 | Piece IntEnum, pinyin names, Chinese char __repr__ | Via test_types.py::test_piece_enum_repr |
| DATA-03 | Move encoding 16-bit, encode/decode roundtrip, sq/rc helpers | Via test_types.py::test_encode_decode_roundtrip, test_sq_rc_helpers |
| DATA-05 | STARTING_FEN, boundary masks, from_fen/to_fen | Via test_constants.py (all 9 tests) |

## Self-Check

```
[ -f "src/xiangqi/engine/__init__.py" ]          FOUND
[ -f "src/xiangqi/engine/types.py" ]             FOUND
[ -f "src/xiangqi/engine/constants.py" ]          FOUND
[ -f "tests/__init__.py" ]                        FOUND
[ -f "tests/test_types.py" ]                      FOUND
[ -f "tests/test_constants.py" ]                  FOUND
git log --oneline | grep -q "e8bb55"             FOUND
git log --oneline | grep -q "e387bc9"           FOUND
git log --oneline | grep -q "1d93424"            FOUND
git log --oneline | grep -q "e85a8d9"            FOUND
pytest tests/test_types.py tests/test_constants.py # 15 passed
```
## Self-Check: PASSED
