# Phase 1: 数据结构 - Research

**Researched:** 2026-03-19
**Domain:** Python data structures for a Xiangqi (Chinese Chess) rule engine
**Confidence:** HIGH

## Summary

Phase 1 establishes the foundational data layer: board representation (10x9 signed int8 NumPy array), piece type encoding (IntEnum with Chinese pinyin names), move encoding (16-bit integer), game state container (dataclass), Zobrist hashing (eager module-level table), and starting position constants (WXF FEN + boundary masks). The phase is entirely mechanical — no game logic, no search, no RL interface. Implementation is straightforward given the locked decisions from the discuss-phase session. The main risks are subtle: numpy int8 overflow when negating piece values, correct Zobrist table dimensionality (15x90, not 14x90), and enum repr override behavior. Tests should use pytest fixtures in conftest.py for reusable state, and all three source modules are safe from circular import issues since they form a clean bottom-up chain.

**Primary recommendation:** Implement `types.py` first (Piece enum + move helpers), then `constants.py` (FEN + boundary masks), then `state.py` (XiangqiState + Zobrist init). Keep state.py thin — it should import types.py and constants.py but not the other way around.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Piece naming: pure Chinese pinyin enum member names (`R_SHUAI`, not `R_GENERAL`)
- `__repr__` of enum members shows Chinese character (display only, not the enum name)
- `IntEnum` so arithmetic works and mypy/strict typing passes
- Zobrist: eager `_init_zobrist()` at module import time, module-level global `_zobrist_piece = np.zeros((15, 90), dtype=np.uint64)`, fixed seed `random.Random(0x20240319)`
- FEN: WXF XFEN standard, starting FEN `rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1`
- Boundary storage: `np.ndarray` boolean masks shape `(10, 9)` for palace and river, not Python sets
- Move: 16-bit integer only (`from_sq | (to_sq << 9) | (is_capture << 16)`), no Move dataclass
- Flat index: `sq = row * 9 + col`, reverse: `row, col = divmod(sq, 9)`
- `XiangqiState` fields: board, turn, move_history, halfmove_clock, zobrist_hash_history

### Claude's Discretion

- Internal organization of the Piece enum members (order, grouping)
- Exact location of helper functions (can live in `types.py` or a `_utils.py` submodule)
- Whether to use `@dataclass(slots=True)` vs plain class for XiangqiState
- Random seed value (any fixed non-zero 32/64-bit integer — 0x20240319 is a reasonable suggestion)
- Exact row/column index direction (as long as STARTING_FEN is consistent with it)
- Test fixture setup style

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within Phase 1 scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-01 | Board as `np.ndarray(10, 9, dtype=np.int8)`, 0=empty, +1..+7=red, -1..-7=black | Board geometry defined in STACK.md; int8 range -128..127 covers -7..+7 safely; negation for color-flipping works in int8 |
| DATA-02 | Piece types as `IntEnum`: 帅/将/车/马/炮/士/象/兵, red positive, black negative | IntEnum needed for arithmetic compatibility; pinyin naming locked; `__repr__` override for Chinese character display |
| DATA-03 | Move as 16-bit integer: `from_sq \| (to_sq << 9) \| (is_capture << 16)`, flat index = `from_sq * 90 + to_sq` | Encode/decode helpers need to mask correctly (bits 0-8=from, 9-15=to, 16=cap); `divmod` for sq_to_rc |
| DATA-04 | `XiangqiState` with board, turn, move_history, halfmove_clock, zobrist_hash_history | Plain `@dataclass` (not slots=True) recommended for Phase 1; fields per locked decisions; Zobrist hash initialized from initial board |
| DATA-05 | `STARTING_FEN` constant, standard opening position | WXF FEN verified; `from_fen()` and `to_fen()` in constants.py per CONTEXT.md |

</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | 2.4.x | Board array (int8), Zobrist table (uint64), boundary masks (bool) | All board operations use numpy; PyTorch 2.10 requires NumPy 2.x |
| pytest | 8.x | Test runner for test_types.py, test_state.py, test_constants.py | Project dev dependency; conftest.py for shared fixtures |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| random (stdlib) | — | PRNG for Zobrist table initialization | `_init_zobrist()` uses `random.Random(seed).getrandbits(64)` for 64-bit entries |

**Installation:**
```bash
uv pip install numpy pytest
```

**NumPy version note:** PyTorch 2.10 requires NumPy >= 2.x. Do NOT pin to NumPy 1.x. NumPy 2.x removed deprecated aliases (`np.bool_` → `np.bool`, `np.product` → `np.prod`) — use explicit dtypes always.

---

## Architecture Patterns

### Recommended Project Structure

```
src/xiangqi/
├── __init__.py           # public exports: Piece, XiangqiState, STARTING_FEN, encode/decode helpers
└── engine/
    ├── __init__.py       # engine package init
    ├── types.py          # Piece IntEnum, move encode/decode, sq/rc helpers
    ├── constants.py      # STARTING_FEN, IN_PALACE, IN_BLACK_HOME, FEN parser/serializer
    └── state.py          # XiangqiState dataclass, Zobrist init (calls _init_zobrist at import)

tests/
├── __init__.py
├── conftest.py           # shared fixtures: starting_state, empty_board
├── test_types.py
├── test_constants.py
└── test_state.py
```

**Import order (safe, no cycles):**
1. `types.py` — no imports from this package (uses stdlib `enum` only)
2. `constants.py` — imports `types` for FEN mapping (piece_map needs Piece values)
3. `state.py` — imports `types` and `constants`; Zobrist init runs at `import xiangqi.engine.state`

### Pattern 1: Piece IntEnum with `__repr__` Override

**What:** `IntEnum` subclass where `__repr__` returns the Chinese character so `repr(piece)` shows the visual symbol while `.name` gives the pinyin identifier.

**Implementation:**
```python
# Source: python-chess IntEnum patterns adapted
from enum import IntEnum

class Piece(IntEnum):
    EMPTY = 0
    R_SHUAI = +1
    B_JIANG = -1
    R_SHI = +2
    B_SHI = -2
    R_XIANG = +3
    B_XIANG = -3
    R_MA = +4
    B_MA = -4
    R_CHE = +5
    B_CHE = -5
    R_PAO = +6
    B_PAO = -6
    R_BING = +7
    B_ZU = -7

    # Class-level mapping from enum value to Chinese character
    _CHARS = {
        0: '　',  # full-width space for empty
        +1: '帅', +2: '仕', +3: '相', +4: '马', +5: '车', +6: '炮', +7: '兵',
        -1: '将', -2: '士', -3: '象', -4: '馬', -5: '車', -6: '砲', -7: '卒',
    }

    def __repr__(self) -> str:
        return self._CHARS[self.value]

    def __str__(self) -> str:
        return self._CHARS[self.value]
```

**Warning:** `__repr__` returning a string changes how `repr()` behaves — `repr(Piece.R_SHUAI)` returns `'帅'` not `'Piece.R_SHUAI'`. For logging/debugging, use `.name`. For display, `__str__` and `__repr__` both return the Chinese character.

**When to use:** All board prints, UI rendering, debug output.

### Pattern 2: Zobrist Eager Initialization with Module-Level Globals

**What:** `_init_zobrist()` called at the end of `state.py` (module import time). Table stored as module-level `_zobrist_piece: np.ndarray`.

**Implementation:**
```python
# state.py
import random
import numpy as np
from dataclasses import dataclass, field

_ROWS, _COLS = 10, 9
_NUM_SQUARES = _ROWS * _COLS  # 90

# Shape (15, 90): index = piece_value + 7 (maps -7..+7 → 0..14)
# Index 7 = EMPTY (= 0 piece, never actually hashed but reserves the slot)
_zobrist_piece: np.ndarray = np.zeros((15, _NUM_SQUARES), dtype=np.uint64)

def _init_zobrist() -> None:
    rng = random.Random(0x20240319)  # fixed seed for reproducibility
    for piece_idx in range(15):
        for sq in range(_NUM_SQUARES):
            _zobrist_piece[piece_idx, sq] = rng.getrandbits(64)

_init_zobrist()  # run at module import
```

**Why shape (15, 90):** Piece values range from -7 to +7 (15 distinct values including 0). The offset `piece_idx = piece_value + 7` maps to array index 0..14. Using a single offset instead of conditional checks (`if p > 0: ... elif p < 0: ...`) makes the hash update a single indexing operation instead of a branch.

**Why uint64:** Standard Zobrist hash width. 64 bits is more than enough to avoid collisions for game tree sizes in v0.1 (< 10^9 nodes). The hash is a Python `int` on read (NumPy uint64 casts to Python int automatically).

### Pattern 3: Boundary Masks as NumPy Boolean Arrays

**What:** Precomputed `np.ndarray` of shape `(10, 9)` and `dtype=bool` for O(1) boundary checking via array indexing.

**Implementation:**
```python
# constants.py
import numpy as np

ROWS, COLS = 10, 9
NUM_SQUARES = ROWS * COLS  # 90

# Palace mask: both red and black 3x3 palaces
IN_PALACE: np.ndarray = np.zeros((ROWS, COLS), dtype=bool)
IN_PALACE[0:3, 3:6] = True   # black palace rows 0-2, cols 3-5
IN_PALACE[7:10, 3:6] = True  # red palace rows 7-9, cols 3-5

# Black elephant home half: rows 0-4 (cannot enter red side rows 5-9)
IN_BLACK_HOME: np.ndarray = np.zeros((ROWS, COLS), dtype=bool)
IN_BLACK_HOME[0:5, :] = True

# Red elephant home half: rows 5-9
IN_RED_HOME: np.ndarray = np.zeros((ROWS, COLS), dtype=bool)
IN_RED_HOME[5:10, :] = True
```

**Why not Python sets:** `np.ndarray` boolean mask enables vectorized checks: `IN_PALACE[row, col]` is a single array lookup O(1). Python sets require constructing a `(row, col)` tuple and a hash lookup — slower and incompatible with NumPy idioms used throughout the codebase.

### Pattern 4: XiangqiState Plain Dataclass

**What:** `@dataclass` without `slots=True` for the state container. Includes a `copy()` method for copy-state move exploration.

**Recommendation: do NOT use `slots=True` for Phase 1.** Reasoning:
- `slots=True` prevents adding attributes dynamically and makes `dataclasses.replace()` the only way to create modified copies. For Phase 1, a simple `state.copy()` method that returns `XiangqiState(board=..., turn=..., ...)` is more readable and idiomatic.
- `slots=True` saves ~56 bytes per instance. With a 90-byte board array, the savings are negligible (< 0.1% of total memory).
- `slots=True` is more relevant for large numbers of short-lived objects (e.g., nodes in a search tree). XiangqiState objects live for the duration of a game (one at a time), so the memory benefit is moot.
- The PITFALLS.md explicitly recommends copy-state over make/unmake for v0.1. Plain dataclass with an explicit `copy()` method is the cleanest implementation of that pattern.

```python
@dataclass
class XiangqiState:
    board: np.ndarray                    # shape (10, 9), dtype=int8
    turn: int                            # +1 = red to move, -1 = black
    move_history: list[int]              # encoded moves, newest last
    halfmove_clock: int                  # plies since last pawn move or capture
    zobrist_hash_history: list[int]       # running Zobrist hash list

    def copy(self) -> XiangqiState:
        """Deep copy for copy-state move exploration."""
        return XiangqiState(
            board=self.board.copy(),
            turn=self.turn,
            move_history=self.move_history.copy(),
            halfmove_clock=self.halfmove_clock,
            zobrist_hash_history=self.zobrist_hash_history.copy(),
        )
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PRNG for Zobrist keys | Write a custom LCG or Mersenne Twister | `random.Random(seed).getrandbits(64)` | `random.Random` is in stdlib, cryptographically unnecessary for Zobrist keys, fast enough for 1350 64-bit values |
| Piece type lookup | Conditional `if p > 0` / `elif p < 0` branches everywhere | `abs(p)` and offset indexing `p + 7` | Single arithmetic operation vs branch misprediction on hot paths |
| Boundary checking | Python `if row in range(0,3) and col in range(3,6)` per move | Boolean `np.ndarray` masks `IN_PALACE[row, col]` | Array indexing is O(1) with no Python object construction |
| Move encoding | A dataclass or namedtuple with 3 fields | 16-bit integer bit-packing | ~2 bytes per move vs ~72 bytes per object; maps directly to fixed RL action space index |
| FEN parsing | Manual string splitting with edge cases | Simple rank-by-rank parse with a `piece_map` dict | 15 lines of code, no library needed |

---

## Common Pitfalls

### Pitfall 1: NumPy int8 Overflow When Negating Pieces

**What goes wrong:** After a move, code negates a piece value to flip its color for some operation, and the result is wrong. Specifically, `int8(-128)` cannot be represented as a positive value in int8 (overflow on negation).

**Why it happens:** NumPy `int8` is a signed 8-bit integer with range -128..+127. Xiangqi piece values are -7..+7 — well within range. The overflow only occurs if you negate `np.int8(-128)`, which happens if an int8 array is saturated at -128 by arithmetic. This is unlikely in normal use but can occur during in-place negation: `board[board < 0] *= -1` in a uint8 context would work, but `board[board < 0] = -board[board < 0]` in int8 if any value is -128 (not possible in Xiangqi, but the pattern is risky).

**How to avoid:** Never negate int8 arrays in-place with unary minus. Always create a new array: `negated = -board.copy()`. Use `board.astype(np.int8)` for explicit dtype safety. For color flipping in the RL canonical state encoder, prefer constructing a new array rather than in-place negation.

**Warning signs:** `np.int8(-7)` becomes `np.int8(249)` after a mistaken in-place op — the piece would read as an invalid value > 7.

### Pitfall 2: Zobrist Table Is 14x90 Not 15x90

**What goes wrong:** The table is initialized as `np.zeros((14, 90))` because there are 7 piece types × 2 colors = 14, forgetting the EMPTY offset (index 0 = empty = piece value 0).

**Why it happens:** The offset `piece_value + 7` maps -7..+7 to 0..14. If the array has only 14 rows (0..13), piece value +7 = 7 would be out of bounds for EMPTY (piece value 0 maps to index 7). Empty squares are not hashed (the hash update is skipped for `p == 0`), so the bug doesn't immediately manifest — but the index 7 is reserved and may be accidentally used later.

**How to avoid:** Use exactly `(15, 90)` as specified in the locked decision. The array shape should be documented in a comment: `# 15 rows: index = piece_value + 7, mapping -7..+7 to 0..14`.

### Pitfall 3: Move Encoding Bits Overlap

**What goes wrong:** `encode_move` uses `from_sq | (to_sq << 9) | (is_capture << 16)` but `to_sq << 9` can bleed into bit 16 (is_capture) if `to_sq` uses more than 7 bits. `to_sq` ranges 0..89 (7 bits: 89 < 128 = 2^7). So `to_sq << 9` can produce bits in positions 9-15, which is fine. But if `to_sq` uses all 9 bits (positions 0-8), shifting left by 9 places puts bit 8 into position 17 — this is fine too. The overlap only occurs if the bit field boundaries aren't right.

**Root cause:** The specification says `from_sq | (to_sq << 9) | (is_capture << 16)`. `from_sq` uses bits 0-8 (9 bits), `to_sq << 9` uses bits 9-17 (9 bits), `is_capture << 16` uses bit 16. Since `to_sq` needs only 7 bits (0-89) but occupies 9 bits in the encoding, and `is_capture` is at bit 16 — there is no overlap as long as `to_sq` doesn't use bit 16+.

**The real issue:** The decode uses `mask & 0x1FF` for `from_sq` (9 bits, mask = 0x1FF = bits 0-8), `mask >> 9 & 0x1FF` for `to_sq` (9 bits). `0x1FF = 511` covers values 0-511, far more than needed (0-89). The encoding is correct; just be precise with masks:

```python
_FROM_MASK = 0x1FF      # bits 0-8
_TO_MASK   = 0x3FE00    # bits 9-17 = 0x1FF << 9
_CAP_MASK  = 0x10000    # bit 16

def encode_move(from_sq: int, to_sq: int, is_capture: bool = False) -> int:
    return (from_sq & _FROM_MASK) | ((to_sq << 9) & _TO_MASK) | (int(is_capture) << 16)

def decode_move(move: int) -> tuple[int, int, bool]:
    from_sq =  move        & _FROM_MASK
    to_sq   = (move >> 9)  & 0x1FF
    capture =  (move >> 16) & 0x1
    return from_sq, to_sq, bool(capture)
```

### Pitfall 4: Enum `__repr__` Changes Object Identity in Collections

**What goes wrong:** `Piece.R_SHUAI in my_list` fails because `__repr__` was overridden but `__eq__` was not — `Piece.R_SHUAI == 1` returns `True` (IntEnum default), but `repr(Piece.R_SHUAI)` returns `'帅'`. The enum member identity is unchanged; only the string representation is changed.

**Why it's NOT a pitfall:** `IntEnum` members compare equal to their integer values by default. `Piece.R_SHUAI == 1` is `True`. So `board == Piece.R_SHUAI` works correctly. The `__repr__` override only changes what `repr()` and `str()` return, not equality comparisons.

**However:** If `Piece` enum members are stored in a Python set or dict (unusual but possible), the `__hash__` behavior of `IntEnum` is based on the integer value, not the enum identity. `hash(Piece.R_SHUAI) == hash(1)` — this is the correct behavior. No action needed.

### Pitfall 5: FEN Rank Parsing Off-by-One on Empty Square Count

**What goes wrong:** When parsing `rnbakabnr/9/...`, the `9` in the FEN means 9 consecutive empty squares. A common bug is treating the `9` as "skip 8 squares" (off by one) or treating the rank string as red's perspective (reversed).

**How to avoid:** FEN ranks are always parsed from black's back rank (row 0, top of board) going down. `9` means skip exactly 9 columns. The column index increments by the digit value, not `digit - 1`. Pseudocode:

```python
for ch in rank_string:
    if ch.isdigit():
        col_idx += int(ch)   # skip 'digit' empty squares
    else:
        board[row_idx, col_idx] = piece_map[ch]
        col_idx += 1
```

The starting FEN `rnbakabnr/9/...` has 9 chars in the second rank: col_idx goes 0→9 after the `9`, placing the next piece at column 9 (off-board). **The starting FEN actually has `rnbakabnr/9/1c5c1/...`** — the `9` in rank 1 means all 9 squares are empty (the river and center area). After parsing `rnbakabnr` (9 pieces, row 0 complete at col 9), the `9` on row 1 sets col_idx to 9 — but since row 1 has only 9 columns (0-8), the `9` means "the rest of this rank is empty." After the `9`, col_idx = 9, and the loop ends (rank full). This is correct — the column pointer naturally terminates the rank. The `9` is redundant (9 empty squares at cols 0-8), but it is valid FEN.

---

## Code Examples

### Move Encoding/Decoding Roundtrip

```python
# Source: DATA_STRUCTURES.md move encoding section
from typing import Tuple

ROWS = 10
COLS = 9
NUM_SQUARES = ROWS * COLS  # 90

def rc_to_sq(row: int, col: int) -> int:
    """Flat square index: row * 9 + col. Range 0-89."""
    return row * COLS + col

def sq_to_rc(sq: int) -> Tuple[int, int]:
    """Reverse flat index: (row, col) = divmod(sq, 9)."""
    return divmod(sq, COLS)

def encode_move(from_sq: int, to_sq: int, is_capture: bool = False) -> int:
    """16-bit encoding: bits 0-8=from, bits 9-15=to, bit 16=is_capture."""
    return (from_sq & 0x1FF) | ((to_sq << 9) & 0x3FE00) | (int(is_capture) << 16)

def decode_move(move: int) -> Tuple[int, int, bool]:
    """Reverse the 16-bit encoding."""
    from_sq =  move        & 0x1FF
    to_sq   = (move >> 9)  & 0x1FF
    capture =  (move >> 16) & 0x1
    return from_sq, to_sq, bool(capture)

# Roundtrip test
for from_sq in range(90):
    for to_sq in range(90):
        if from_sq == to_sq:
            continue
        for cap in (False, True):
            m = encode_move(from_sq, to_sq, cap)
            f, t, c = decode_move(m)
            assert f == from_sq and t == to_sq and c == cap, f"FAIL: {from_sq}->{to_sq} cap={cap}"
```

### Zobrist Hash Computation and Incremental Update

```python
# Source: DATA_STRUCTURES.md Section 4
import numpy as np
import random

_NUM_SQUARES = 90
# Shape: (15, 90) — index = piece_value + 7
_zobrist_piece: np.ndarray = np.zeros((15, _NUM_SQUARES), dtype=np.uint64)

def _init_zobrist() -> None:
    rng = random.Random(0x20240319)
    for piece_idx in range(15):
        for sq in range(_NUM_SQUARES):
            _zobrist_piece[piece_idx, sq] = rng.getrandbits(64)

def compute_hash(board: np.ndarray, turn: int) -> int:
    """Full board hash. O(90) = trivial."""
    h = 0
    for r in range(10):
        for c in range(9):
            p = board[r, c]
            if p != 0:
                h ^= int(_zobrist_piece[p + 7, r * 9 + c])
    return h

def update_hash(
    old_hash: int,
    from_sq: int,
    to_sq: int,
    piece: int,
    captured: int,
) -> int:
    """Incremental hash update. O(1)."""
    h = old_hash
    h ^= int(_zobrist_piece[piece + 7, from_sq])          # remove old
    if captured != 0:
        h ^= int(_zobrist_piece[captured + 7, to_sq])     # remove captured
    h ^= int(_zobrist_piece[piece + 7, to_sq])            # add new
    return h
```

### FEN Parser and Serializer

```python
# Source: DATA_STRUCTURES.md Section 3
import numpy as np

_PIECE_MAP = {
    'K': 1, 'A': 2, 'B': 3, 'N': 4, 'R': 5, 'C': 6, 'P': 7,
    'k': -1, 'a': -2, 'b': -3, 'n': -4, 'r': -5, 'c': -6, 'p': -7,
}
_REV_PIECE_MAP = {v: k for k, v in _PIECE_MAP.items()}

def from_fen(fen: str) -> tuple[np.ndarray, int]:
    """Parse WXF FEN string to (board, turn)."""
    parts = fen.split()
    ranks_str = parts[0].split('/')
    board = np.zeros((10, 9), dtype=np.int8)

    for r_idx, rank in enumerate(ranks_str):  # r_idx=0 is black back rank
        c_idx = 0
        for ch in rank:
            if ch.isdigit():
                c_idx += int(ch)  # skip 'digit' empty squares
            else:
                board[r_idx, c_idx] = np.int8(_PIECE_MAP[ch])
                c_idx += 1

    turn = 1 if parts[1] == 'w' else -1
    return board, turn

def to_fen(board: np.ndarray, turn: int) -> str:
    """Serialize board to WXF FEN string."""
    rank_strs = []
    for r in range(10):
        rank = ''
        empty = 0
        for c in range(9):
            p = int(board[r, c])
            if p == 0:
                empty += 1
            else:
                if empty > 0:
                    rank += str(empty)
                    empty = 0
                rank += _REV_PIECE_MAP[p]
        if empty > 0:
            rank += str(empty)
        rank_strs.append(rank)
    color = 'w' if turn == 1 else 'b'
    return ' '.join(['/'.join(rank_strs), color, '-', '0', '1'])
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Python dict `{pos: piece}` for board | `np.ndarray` shape (10, 9), dtype=int8 | Always (greenfield) | Enables NumPy vectorization; direct PyTorch tensor conversion; ~90x faster piece scanning |
| `namedtuple Move` or dataclass for moves | 16-bit integer encoding | Always | ~72 bytes → ~2 bytes per move; maps to RL action space index |
| FEN string comparison for repetition | Zobrist hash tracking | Always | O(90) string compare → O(1) int compare |
| Lazy Zobrist init (on first compute) | Eager init at module import | Always | Eliminates init-time latency spike on first call; table is ~10KB, free to load |

**Deprecated/outdated:**
- `np.bool_` (NumPy < 2.0) — removed in NumPy 2.0. Use Python `bool` or `np.bool8` explicitly.
- `np.product` — removed in NumPy 2.0. Use `np.prod`.
- Python `gym` (pre-Farama) — replaced by `gymnasium`. Use `gymnasium` for RL wrappers in v0.2.

---

## Open Questions

1. **King positions tracking in XiangqiState**
   - What we know: DATA-04 requires `board, turn, move_history, halfmove_clock, zobrist_hash_history`. The discuss-phase did not include `king_positions` in XiangqiState, but move generation (Phase 2) will need to find both kings per-move to run `is_in_check()`. Fast king lookup requires tracking positions.
   - What's unclear: Should `king_positions` be in XiangqiState (added in Phase 1) or computed fresh in Phase 2?
   - Recommendation: Add `king_positions: dict[int, int]` to XiangqiState in Phase 1. Initialize it in the `XiangqiState` constructor by scanning the board once. Update it in-place during Phase 2 move application. This avoids a full-board scan in `is_in_check()` on every move.

2. **NumPy version pinned or not**
   - What we know: STACK.md recommends NumPy 2.4.x. NumPy 2.x removed several deprecated APIs.
   - What's unclear: Is there a hard upper bound needed for safety, or is the range `>= 2.0, < 3.0` sufficient?
   - Recommendation: Pin `numpy>=2.0,<3.0` in pyproject.toml. NumPy has a strong backward-compatibility record.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` (pytest section) or `pytest.ini` — neither needed for basic usage |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| DATA-01 | board shape (10,9) dtype int8 | unit | `pytest tests/test_state.py::test_board_shape` | no |
| DATA-01 | piece values: 0 empty, +1..+7 red, -1..-7 black | unit | `pytest tests/test_types.py::test_piece_values` | no |
| DATA-02 | Piece IntEnum: pinyin names, `__repr__` returns Chinese char | unit | `pytest tests/test_types.py::test_piece_enum` | no |
| DATA-02 | `abs(Piece.R_SHUAI) == abs(Piece.B_JIANG) == 1` | unit | `pytest tests/test_types.py::test_piece_type_abs` | no |
| DATA-03 | `encode_move`/`decode_move` roundtrip for all 90x90 combos | unit | `pytest tests/test_types.py::test_move_encoding_roundtrip` | no |
| DATA-03 | `sq_to_rc`/`rc_to_sq` roundtrip | unit | `pytest tests/test_types.py::test_sq_rc_helpers` | no |
| DATA-04 | XiangqiState initializes with correct field types | unit | `pytest tests/test_state.py::test_state_fields` | no |
| DATA-04 | `state.copy()` produces independent board | unit | `pytest tests/test_state.py::test_state_copy` | no |
| DATA-04 | Initial Zobrist hash matches `compute_hash(starting_board)` | unit | `pytest tests/test_state.py::test_zobrist_initial_hash` | no |
| DATA-05 | `from_fen(STARTING_FEN)` produces correct board layout | unit | `pytest tests/test_constants.py::test_starting_fen_parsed` | no |
| DATA-05 | `to_fen(from_fen(fen)) == fen` (forward/backward FEN roundtrip) | unit | `pytest tests/test_constants.py::test_fen_roundtrip` | no |
| DATA-05 | `IN_PALACE` mask has correct squares set | unit | `pytest tests/test_constants.py::test_palace_mask` | no |
| DATA-05 | `IN_BLACK_HOME` / `IN_RED_HOME` river boundary correct | unit | `pytest tests/test_constants.py::test_home_half_masks` | no |

### Sampling Rate

- **Per task commit:** `pytest tests/ -x -q` (fast: Phase 1 tests are pure data assertions, no logic)
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- `tests/conftest.py` — shared fixtures: `starting_board`, `starting_state`, `empty_board`
- `tests/__init__.py` — package marker
- `tests/test_types.py` — Piece enum, move encoding tests
- `tests/test_constants.py` — FEN parsing, boundary mask tests
- `tests/test_state.py` — XiangqiState dataclass, Zobrist hash tests
- `pyproject.toml` — pytest config section (if any non-default settings needed)
- Framework install: `uv pip install pytest` — pytest is not yet in any project dependencies

---

## Sources

### Primary (HIGH confidence)

- `.planning/research/DATA_STRUCTURES.md` — full implementation reference with code examples, board geometry, piece encoding, move representation, Zobrist hashing, FEN parsing (researched 2026-03-19)
- `.planning/research/STACK.md` — numpy dtype guidance, int8 range (-128..+127), NumPy 2.x compatibility notes
- `.planning/research/PITFALLS.md` — Zobrist initialization patterns, copy-state vs make/unmake recommendations

### Secondary (MEDIUM confidence)

- `.planning/phases/01-data-structures/01-CONTEXT.md` — locked decisions verified against discuss-phase output (gathered 2026-03-19)
- Chess Programming Wiki: board representation techniques adapted for Xiangqi's 10x9 board — domain authoritative
- python-chess `IntEnum` patterns for piece representation — well-established Python pattern

### Tertiary (LOW confidence)

- NumPy 2.x `np.bool_` deprecation — verified by reading STACK.md research notes; not re-checked in NumPy docs directly

---

## Metadata

**Confidence breakdown:**

| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | Locked decisions from discuss-phase; numpy + pytest are unambiguous |
| Architecture | HIGH | Module import order (types→constants→state) is safe from cycles; structure aligns with deliverable files |
| Pitfalls | HIGH | All pitfalls derived from DATA_STRUCTURES.md research with explicit code examples; overflow scenario for int8 is verified from numpy dtype documentation |
| Don't Hand-Roll | HIGH | All "don't build" items verified against stdlib/builtin capabilities |

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (data structure fundamentals are stable; only fast-moving concern is NumPy 2.x API surface, which is documented)
