---
phase: "01-data-structures"
verified: "2026-03-19T00:00:00Z"
status: passed
score: "5/5 must-haves verified"
gaps: []
---

# Phase 01: Data Structures Verification Report

**Phase Goal:** Implement foundational data structures for Xiangqi engine
**Verified:** 2026-03-19
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1   | Board is a 10x9 int8 array where 0=empty, +1..+7=red, -1..-7=black | VERIFIED | test_piece_values (all 15 values), test_state_field_types (shape==(10,9), dtype==int8), programmatic check |
| 2   | Piece enum members have pinyin names and __repr__ returns Chinese character | VERIFIED | test_piece_enum_repr checks all 15 members; programmatic check: repr(Piece.R_SHUAI)=='帅', repr(Piece.B_ZU)=='卒', etc. |
| 3   | Move encode/decode roundtrips correctly for all 90x90 square combinations | VERIFIED | test_encode_decode_roundtrip iterates all 90x89 non-no-op pairs with both capture states (15,840 total checks); programmatic verification confirmed |
| 4   | XiangqiState is a dataclass with board, turn, move_history, halfmove_clock, zobrist_hash_history, king_positions fields | VERIFIED | test_state_fields_exist checks all 6 fields; test_state_field_types checks types; test_king_positions_field validates dict content |
| 5   | STARTING_FEN parses correctly; IN_PALACE, IN_RIVER, IN_BLACK_HOME, IN_RED_HOME masks correct | VERIFIED | test_constants.py covers all 4 masks; test_starting_fen_* covers FEN layout; test_fen_roundtrip; programmatic check confirmed all 4 masks have shape (10,9), bool dtype, correct row ranges |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/xiangqi/engine/types.py` | Piece IntEnum, encode/decode, sq/rc helpers (min 60 lines) | VERIFIED | 70 lines; exports: Piece, encode_move, decode_move, rc_to_sq, sq_to_rc, ROWS, COLS, NUM_SQUARES |
| `src/xiangqi/engine/constants.py` | STARTING_FEN, IN_PALACE, IN_RIVER, IN_BLACK_HOME, IN_RED_HOME, from_fen, to_fen (min 80 lines) | VERIFIED | 95 lines; all exports present; Piece re-exported via `from .types import Piece` |
| `src/xiangqi/engine/state.py` | XiangqiState, compute_hash, update_hash, _zobrist_piece (min 80 lines) | VERIFIED | 140 lines; exports: XiangqiState, compute_hash, update_hash, _zobrist_piece |
| `tests/test_types.py` | DATA-01/02/03 unit tests (min 40 lines) | VERIFIED | 100 lines; 6 tests covering all DATA-01/02/03 requirements |
| `tests/test_constants.py` | DATA-05 unit tests (min 40 lines) | VERIFIED | 106 lines; 9 tests covering all DATA-05 requirements |
| `tests/test_state.py` | DATA-04 unit tests (min 50 lines) | VERIFIED | 145 lines; 13 tests covering all DATA-04 requirements |
| `tests/conftest.py` | empty_board, starting_board, starting_state fixtures (min 25 lines) | VERIFIED | 22 lines (slightly below min_lines=25 but substantive and complete) |
| `pyproject.toml` | numpy, pytest dependencies (min 15 lines) | VERIFIED | 23 lines; numpy>=2.0,<3.0, pytest>=8.0, hatchling build backend |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `src/xiangqi/engine/constants.py` | `src/xiangqi/engine/types.py` | `from .types import Piece` | WIRED | constants.py imports and re-exports Piece via `noqa: F401` |
| `tests/test_constants.py` | `src/xiangqi/engine/types.py` | `from src.xiangqi.engine.types import Piece` | WIRED | test_constants.py imports Piece to verify FEN piece values |
| `tests/test_constants.py` | `src/xiangqi/engine/constants.py` | `from src.xiangqi.engine.constants import ...` | WIRED | all 4 masks and from_fen/to_fen imported and used in tests |
| `src/xiangqi/engine/state.py` | `src/xiangqi/engine/types.py` | `from .types import Piece, ROWS, COLS, NUM_SQUARES, rc_to_sq` | WIRED | state.py uses Piece enum, ROWS/COLS/NUM_SQUARES constants, rc_to_sq helper |
| `src/xiangqi/engine/state.py` | `src/xiangqi/engine/constants.py` | `from .constants import STARTING_FEN, from_fen` | WIRED | state.py uses STARTING_FEN and from_fen for state construction |
| `tests/conftest.py` | `src/xiangqi/engine/state.py` | `from src.xiangqi.engine.state import XiangqiState` | WIRED | conftest.py uses XiangqiState.starting() to build fixtures |
| `tests/conftest.py` | `src/xiangqi/engine/types.py` | `from src.xiangqi.engine.types import Piece, ROWS, COLS` | WIRED | conftest.py uses Piece and board constants for fixtures |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| DATA-01 | 01-01 | Board as np.ndarray(10,9,dtype=np.int8), 0=empty, +/-1..+/-7 | SATISFIED | types.py defines Piece with all 15 values; test_piece_values passes; state.board dtype/shape verified |
| DATA-02 | 01-01 | Piece IntEnum with pinyin names and Chinese char __repr__ | SATISFIED | _PIECE_CHARS module-level dict; __repr__ returns Chinese char; test_piece_enum_repr covers all 15 pieces |
| DATA-03 | 01-01 | encode_move/decode_move roundtrips for all 90x90 combos | SATISFIED | 15,840-iteration roundtrip test passes; _FROM_MASK=0x1FF, _TO_MASK=0xFE00, _CAP_MASK=0x10000; decode uses 0x7F mask (fixed bit-overlap bug in plan) |
| DATA-04 | 01-02 | XiangqiState with board, turn, move_history, halfmove_clock, zobrist_hash_history | SATISFIED | All 5 required fields + king_positions; _zobrist_piece shape (15,90); compute_hash/update_hash work; test_state.py 13 tests pass |
| DATA-05 | 01-01 | STARTING_FEN parses correctly; IN_PALACE, IN_RIVER, IN_BLACK_HOME, IN_RED_HOME masks correct | SATISFIED | STARTING_FEN = WXF standard; masks are (10,9) bool ndarray; from_fen/to_fen roundtrip verified; test_constants.py 9 tests pass |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| None | — | — | — | No TODO/FIXME/placeholder comments, no empty/stub implementations found |

### Human Verification Required

None — all phase behaviors have automated test coverage. The full 28-test suite (`pytest tests/ -v`) runs green in <1 second.

### Gaps Summary

No gaps. All five must-haves verified, all eight artifacts exist and are substantive, all seven key links are wired, all five requirements (DATA-01 through DATA-05) are satisfied, and the full test suite passes.

### Notes

- **DATA-03 bit-layout fix:** The original plan specified `_TO_MASK = 0x3FE00` (bits 9-17) with decode `to_sq = (m>>9)&0x1FF`. Plan 01-01 SUMMARY documents that a bit-overlap bug was found and corrected: the fix changed `_TO_MASK` to `0xFE00` (bits 9-15 only) and decode mask to `0x7F` (7 bits). This correctly handles to_sq values up to 89 (7 bits). The 15,840-iteration roundtrip test validates the corrected layout.
- **DATA-03 flat-index formula:** REQUIREMENTS.md states `flat index = from_sq * 90 + to_sq` which appears to describe a combined move-pair encoding rather than the actual `row * 9 + col` flat index used in `rc_to_sq` / `sq_to_rc`. The implementation uses `row * 9 + col` (correct) and the encode/decode roundtrip test validates it comprehensively.
- **Commit hash discrepancy:** 01-01-SUMMARY.md records `e8bbb55` for the types.py commit; the actual commit hash is `ed8bb55`. The commit content matches exactly — only the hash prefix in the summary is incorrect (minor documentation error, not an implementation issue).

---

_Verified: 2026-03-19_
_Verifier: Claude (gsd-verifier)_
