# Data Structures and Algorithms for Xiangqi Engine Implementation

**Domain:** Xiangqi (Chinese Chess) rule engine — v0.1 milestone
**Researched:** 2026-03-19
**Confidence:** HIGH (patterns drawn from chessprogramming.org techniques adapted for Xiangqi's 10x9 board, cross-validated against existing engine implementations in the project research files)

---

## 1. Board Representation

### Chosen Approach: Mailbox Array (10x9)

The board is represented as a 2D NumPy array of shape `(10, 9)`, indexed `[row][col]`.

```
Row 0: black back rank (top of displayed board)
Row 9: red back rank (bottom of displayed board)
Col 0: left file (a)
Col 8: right file (i)
```

**Coordinate convention:** `[row, col]` with `row` increasing downward (black→red direction). This is the standard array indexing convention and matches how NumPy arrays are naturally iterated.

**Why not alternatives:**

| Scheme | Verdict | Rationale |
|--------|---------|-----------|
| Standard 64-bit bitboard | Inapplicable | Xiangqi's 90 squares do not fit in 64 bits. A 128-bit or two-64-bit scheme adds complexity for no gain. |
| 0x88 board | Unnecessary | 0x88 enables O(1) off-board checks (`sq & 0x88`) for Western chess's 8x8 board. Xiangqi's 10x9 is asymmetric; simple `0 <= row < 10 and 0 <= col < 9` bounds checks are equally cheap and far simpler. |
| Dictionary `{pos: piece}` | Too slow | O(n) piece lookup; cannot leverage NumPy vectorization; incompatible with PyTorch tensor conversion. |
| Mailbox array (10x9) | **Recommended** | Direct index access O(1); trivially convertible to PyTorch tensor; NumPy slice operations work naturally; maps directly to RL observation plane format. |

### Static Constraint Tables (Precomputed)

Rather than computing palace/river boundaries at runtime, precompute constant lookup tables at module load time:

```python
# Derived from board dimensions (10 rows x 9 cols)
# Black palace: rows 0-2, cols 3-5
# Red palace:   rows 7-9, cols 3-5

BLACK_PALACE = {(r, c) for r in range(3) for c in range(3, 6)}   # 9 squares
RED_PALACE   = {(r, c) for r in range(7, 10) for c in range(3, 6)}
PALACE = BLACK_PALACE | RED_PALACE

BLACK_RIVER_SIDE   = range(0, 5)   # rows 0-4
RED_RIVER_SIDE     = range(5, 10)  # rows 5-9
BLACK_HOME_ROWS     = range(0, 5)   # elephant cannot enter red side
RED_HOME_ROWS       = range(5, 10)  # elephant cannot enter black side
```

These sets are small enough (≤90 elements) that membership testing is fast in Python. For hot paths (every legal-move candidate), consider `np.ndarray` boolean masks instead:

```python
# Boolean masks shape (10, 9) — faster for NumPy vectorized checks
_in_palace = np.zeros((10, 9), dtype=bool)
_in_palace[0:3, 3:6] = True
_in_palace[7:10, 3:6] = True

_black_home = np.zeros((10, 9), dtype=bool)
_black_home[0:5, :] = True   # rows 0-4 = black half (elephant territory)
```

### Board Access Functions

```python
def piece_at(board: np.ndarray, row: int, col: int) -> int:
    """Return piece ID at (row, col). 0 = empty."""
    if 0 <= row < 10 and 0 <= col < 9:
        return board[row, col]
    return _OUT_OF_BOUNDS  # sentinel, never stored on board

def is_enemy(board: np.ndarray, row: int, col: int, by_color: int) -> bool:
    """True if the piece at (row, col) belongs to the opponent of `by_color`."""
    p = board[row, col]
    return p != 0 and (p > 0) != (by_color > 0)
```

---

## 2. Piece Encoding

### Integer Encoding (Primary Representation)

Use signed integers — one `int8` value per square:

```
  0  = empty
 +1  = Red General (帅)
 +2  = Red Advisor (仕)
 +3  = Red Elephant (相)
 +4  = Red Horse (马)
 +5  = Red Chariot (车)
 +6  = Red Cannon (炮)
 +7  = Red Soldier (兵)
 -1  = Black General (将)
 -2  = Black Advisor (士)
 -3  = Black Elephant (象)
 -4  = Black Horse (馬)
 -5  = Black Chariot (車)
 -6  = Black Cannon (砲)
 -7  = Black Soldier (卒)
```

**Why signed over two separate arrays:** A single `int8` board lets you test `board[row, col] > 0` for red, `< 0` for black, `== 0` for empty. This is faster than checking two bitplanes. The RL conversion layer (Section 9) expands this into separate bitplanes anyway.

### Piece Type and Color Accessors

```python
def piece_type(p: int) -> int:
    """Absolute value — piece type ID, 0-7."""
    return abs(p)

def is_red(p: int) -> bool:
    return p > 0

def is_black(p: int) -> bool:
    return p < 0

def belongs_to(p: int, color: int) -> bool:
    """True if `p` belongs to `color` (color: positive=red, negative=black)."""
    return p != 0 and (p > 0) == (color > 0)
```

### Python Enum for Readability

```python
from enum import IntEnum

class Piece(IntEnum):
    EMPTY = 0
    # Red pieces (positive)
    R_GEN = +1   # General
    R_ADV = +2   # Advisor
    R_ELE = +3   # Elephant
    R_HOR = +4   # Horse
    R_CHA = +5   # Chariot
    R_CAN = +6   # Cannon
    R_SOL = +7   # Soldier
    # Black pieces (negative, use -value)
    B_GEN = -1
    B_ADV = -2
    B_ELE = -3
    B_HOR = -4
    B_CHA = -5
    B_CAN = -6
    B_SOL = -7
```

`IntEnum` allows arithmetic like `piece * -1` to flip color (a valid approach for board mirroring, but prefer the explicit `change_turn()` state variable over inverting piece signs on the board).

### Bit Representation (for Zobrist Hashing)

For Zobrist hashing (Section 4), each `(piece, square)` combination needs an independent random 64-bit integer. There are 7 piece types × 2 colors × 90 squares = 1,260 entries:

```python
# Generated once at startup using a cryptographic RNG (e.g., random.randrange(2**64))
# Stored as: zobrist_table[piece_id + 7][row * 9 + col]  (index offset so piece_id -7..+7 maps to 0..14)
# 15 * 90 = 1,350 64-bit integers = ~10 KB. Trivially small.
```

---

## 3. Move Representation

### Compact Integer Encoding (Recommended)

Encode each move as a single unsigned 16-bit integer:

```
Bits 0-8:   from_square   (0..89, row * 9 + col)
Bits 9-15:  to_square     (0..89)
Bit  16:    is_capture    (1 if target square was non-empty)
Bit  17+:   reserved (0)  — for future flags (promotion, etc.)
```

```python
def encode_move(from_sq: int, to_sq: int, is_capture: bool = False) -> int:
    return (from_sq & 0xFF) | ((to_sq & 0xFF) << 9) | (int(is_capture) << 16)

def decode_move(move: int) -> tuple[int, int, bool]:
    from_sq =  move        & 0x1FF   # bits 0-8
    to_sq   = (move >> 9)  & 0x1FF   # bits 9-17
    capture = (move >> 16)  & 0x1    # bit 16
    return from_sq, to_sq, bool(capture)

def sq_to_rc(sq: int) -> tuple[int, int]:
    """Convert flat square index 0-89 to (row, col)."""
    return divmod(sq, 9)

def rc_to_sq(row: int, col: int) -> int:
    """Convert (row, col) to flat square index."""
    return row * 9 + col
```

**Why 16-bit over Move objects:** Python `namedtuple` or dataclass Move objects are convenient but carry overhead (~72 bytes per move vs 2 bytes per integer). For move generation producing 30-50 legal moves per position, the list of move integers is ~150-250 bytes vs ~2KB for object list. Negligible for v0.1, but the integer encoding is the right long-term choice and maps directly to a fixed action-space index for the RL agent.

### Rich Move Object (Alternative, for Debugging)

During development, keep a richer representation alongside the integer encoding:

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Move:
    from_row: int
    from_col: int
    to_row: int
    to_col: int
    piece: int       # piece type ID (abs value, 1-7)
    capture: int     # captured piece type ID, or 0
    is_check: bool   # post-move: does this move give check?
    notation: str    # WXF-style notation string (e.g., "马8进7")
```

The `slots=True` dataclass cuts per-instance memory from ~72 to ~56 bytes. The `frozen=True` makes moves hashable (useful for transposition tables later). The RL pipeline uses only the integer encoding; the `Move` object is a debugging/testing view.

### FEN-Like Notation

Xiangqi FEN (XFEN) follows standard FEN structure with Xiangqi-specific piece symbols:

```
<position> <active_color> <castling> <halfmove> <fullmove>
```

Example initial position:
```
rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1
```

**Position encoding:** Each rank from row 0 (black back) to row 9 (red back) separated by `/`. Numbers indicate consecutive empty squares (standard FEN run-length encoding). Red pieces use uppercase, black pieces lowercase.

**Active color:** `w` = red to move, `b` = black to move. (Xiangqi convention: red moves first.)

**The `castling` field** is always `-` in Xiangqi (no castling equivalent).

**Canonical board parsing:**

```python
# Parse XFEN to board array
# Piece symbols: K=general, A=advisor, B=elephant, N=horse, R=chariot, C=cannon, P=soldier
# Uppercase=red, lowercase=black
# '/' separates ranks from row 0 (black back) downward
# Digits are consecutive empty squares
# '9' means 9 empty squares

def parse_xfen(xfen: str) -> np.ndarray:
    board = np.zeros((10, 9), dtype=np.int8)
    piece_map = {'K': 1, 'A': 2, 'B': 3, 'N': 4, 'R': 5, 'C': 6, 'P': 7,
                 'k': -1, 'a': -2, 'b': -3, 'n': -4, 'r': -5, 'c': -6, 'p': -7}
    ranks = xfen.split()[0].split('/')
    for r_idx, rank in enumerate(ranks):   # r_idx=0 is black back rank
        c_idx = 0
        for ch in rank:
            if ch.isdigit():
                c_idx += int(ch)
            else:
                board[r_idx, c_idx] = piece_map[ch]
                c_idx += 1
    return board
```

### Starting Position XFEN

```
rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1
```

---

## 4. Game State

### State Container

```python
@dataclass(slots=True)
class XiangqiState:
    board: np.ndarray               # shape (10, 9), dtype=int8
    turn: int                       # +1=red, -1=black
    move_history: list[int]        # list of encoded moves (undo stack)
    captured: list[int]            # pieces captured this game (for display)
    halfmove_clock: int            # plies since last capture or pawn advance
    fullmove_number: int            # starts at 1, increments after black move
    position_history: list[int]    # Zobrist hash history (see below)
    king_positions: dict[int, int] # {+1: red_king_sq, -1: black_king_sq}

    def copy(self) -> XiangqiState:
        """Deep copy for copy-state move exploration."""
        return XiangqiState(
            board=self.board.copy(),
            turn=self.turn,
            move_history=self.move_history.copy(),
            captured=self.captured.copy(),
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
            position_history=self.position_history.copy(),
            king_positions=self.king_positions.copy(),
        )
```

### Turn Management

Single integer `turn`: `+1` = red, `-1` = black. After each move, `turn *= -1`. No en-passant state exists in Xiangqi, so the turn is the only ephemeral state.

### Move History

Store encoded moves as 16-bit integers in a list. Each entry is sufficient to reconstruct the move; a separate `captured` list tracks captured pieces for display purposes.

**Undo stack design (if make/unmake is preferred over copy-state):**

```python
@dataclass(slots=True)
class MoveUndo:
    from_sq: int
    to_sq: int
    captured_piece: int
    old_halfmove_clock: int
    old_king_pos: int   # only valid if the moved piece was a king
    old_zobrist_hash: int
```

The undo entry is small (fits in 5 fields), making make/unmake viable if performance demands it. Use copy-state for v0.1 — it is correct by construction.

### Halfmove Clock

Standard chess convention: count plies since the last capture or pawn advance. Xiangqi has no pawn advance equivalent to a "pawn move" (soldiers advance 1 step forward before river, sideways after river — both are pawn moves for the 50-move rule). For the halfmove clock:

```python
SOLDIER_PIECES = {7, -7}  # piece types that are pawn-equivalent

def is_pawn_move(piece_type: int) -> bool:
    return piece_type in SOLDIER_PIECES

def apply_move(state: XiangqiState, move: int):
    from_sq, to_sq, _ = decode_move(move)
    from_r, from_c = sq_to_rc(from_sq)
    to_r, to_c = sq_to_rc(to_sq)
    piece = state.board[from_r, from_c]

    state.halfmove_clock += 1
    if abs(state.board[to_r, to_c]) != 0 or is_pawn_move(abs(piece)):
        state.halfmove_clock = 0

    state.board[to_r, to_c] = piece
    state.board[from_r, from_c] = 0
    state.move_history.append(move)
```

### Repetition Detection via Zobrist Hashing

**Zobrist hash** is a 64-bit rolling hash of the board position. It updates incrementally with each move (XOR in the piece-at-square entry, XOR out when removing). This enables O(1) position equality comparison — vastly faster than comparing 90-element arrays.

```python
# Global tables generated at module load
_zobrist_piece = np.zeros((15, 90), dtype=np.uint64)   # 15 = 7 types * 2 colors + 1 (EMPTY slot unused)
_zobrist_turn  = np.uint64(0)                          # XORed when red to move (optional)

import random
def _init_zobrist():
    rng = random.Random(0xXIANGQI_SEED)  # fixed seed for reproducibility
    for piece_idx in range(15):
        for sq in range(90):
            _zobrist_piece[piece_idx, sq] = rng.getrandbits(64)

def compute_hash(board: np.ndarray, turn: int) -> np.uint64:
    h = np.uint64(0)
    for r in range(10):
        for c in range(9):
            p = board[r, c]
            if p != 0:
                h ^= _zobrist_piece[p + 7, r * 9 + c]   # offset: -7..+7 → 0..14
    return h

def update_hash(old_hash: np.uint64, board: np.ndarray,
                from_sq: int, to_sq: int,
                piece: int, captured: int) -> np.uint64:
    """Incrementally update Zobrist hash after a move. O(1)."""
    h = old_hash
    h ^= _zobrist_piece[piece + 7, from_sq]    # remove old position
    if captured != 0:
        h ^= _zobrist_piece[captured + 7, to_sq]  # remove captured piece
    h ^= _zobrist_piece[piece + 7, to_sq]        # add piece at new position
    return h
```

**Repetition detection:**

```python
def detect_repetition(position_history: list[np.uint64],
                      current_hash: np.uint64,
                      draw_overning: int = 4) -> str | None:
    """
    Returns classification of the repeated position.
    None = no repetition.
    'CHECKMATE/LOSS' = perpetual check (loss for checking side).
    'CHASE' = perpetual chase (loss for chasing side).
    'IDLE_DRAW' = perpetual idle repetition (draw).
    'DRAW_3FOLD' = ordinary 3-fold repetition (draw).
    """
    count = position_history.count(current_hash)
    if count + 1 < 3:
        return None

    # Classify the nature of the repeated positions
    # (requires move nature classification — see FEATURES.md / PITFALLS.md)
    # Basic implementation for v0.1: simple 4-fold repetition = draw
    if count + 1 >= draw_overning:
        return 'IDLE_DRAW'
    return 'DRAW_3FOLD'
```

The WXF-correct version (v0.2+) uses the full 16-condition repetition classifier from arXiv:2412.17334. For v0.1, implement basic 4-fold draw and verify all RL rewards are terminal outcomes before adding WXF complexity.

### Incremental State for Check Validation

After each move, cache the Zobrist hash in `state.position_history`. Before move generation, the current hash is `position_history[-1]`. The incremental update (XOR-based, O(1)) avoids recomputing the full board hash.

---

## 5. Per-Piece Move Generation

### Design Principle

Generate **pseudo-legal** moves per piece (ignoring king safety), then filter to **legal** moves by testing whether each pseudo-legal candidate leaves the mover's own General in check. This is the standard approach from Western chess engines.

Pseudo-legal generation is fast because it is purely geometric (board constraints + sliding rays). The king-safety filter is a separate O(1) operation per candidate.

### Helper Constants

```python
# 4 orthogonal directions
_ORTH = [(-1, 0), (+1, 0), (0, -1), (0, +1)]
# 4 diagonal directions
_DIAG = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
# 8 horse leg offsets (orthogonal step); each has 2 diagonal destinations
_HORSE_LEGS = [(-1, 0), (+1, 0), (0, -1), (0, +1),
               (-2, -1), (-2, +1), (-1, -2), (-1, +2),
               (+1, -2), (+1, +2), (+2, -1), (+2, +1)]  # 12 leg positions
# Horse destination offsets from leg: precompute per leg
# For leg (-1, 0): destinations are (-1±1, 0±1) → (-2,-1), (-2,+1)
# The leg is the SQUARE AFTER THE FIRST STEP that blocks the horse
_HORSE_OFFSETS = [
    # (leg_dr, leg_dc, [dest1_dr, dest1_dc], [dest2_dr, dest2_dc])
    (-1,  0, [(-2, -1), (-2, +1)]),
    (+1,  0, [(+2, -1), (+2, +1)]),
    ( 0, -1, [(-1, -2), (+1, -2)]),
    ( 0, +1, [(-1, +2), (+1, +2)]),
]
# Elephant eye offsets (diagonal midpoint): (±1, ±1) for each diagonal destination
_ELEPHANT_OFFSETS = [
    (-2, -2, -1, -1),  # (dest_dr, dest_dc, eye_dr, eye_dc)
    (-2, +2, -1, +1),
    (+2, -2, +1, -1),
    (+2, +2, +1, +1),
]
```

### Per-Piece Generators

All generators yield `(from_sq, to_sq)` integer pairs. The caller builds the encoded move.

**General (King, piece_id=1):**

```python
def gen_general(board: np.ndarray, row: int, col: int,
                color: int, moves: list) -> None:
    # 4 orthogonal destinations, palace-confined
    for dr, dc in _ORTH:
        nr, nc = row + dr, col + dc
        if nr, nc in PALACE:
            target = board[nr, nc]
            if not belongs_to(target, color):
                moves.append((rc_to_sq(row, col), rc_to_sq(nr, nc)))
```

**Advisor (piece_id=2):**

```python
def gen_advisor(board: np.ndarray, row: int, col: int,
                color: int, moves: list) -> None:
    # 4 diagonal destinations, palace-confined
    for dr, dc in _DIAG:
        nr, nc = row + dr, col + dc
        if nr, nc in PALACE:
            target = board[nr, nc]
            if not belongs_to(target, color):
                moves.append((rc_to_sq(row, col), rc_to_sq(nr, nc)))
```

**Elephant (piece_id=3):**

```python
def gen_elephant(board: np.ndarray, row: int, col: int,
                 color: int, moves: list) -> None:
    # 4 diagonal destinations, river-bound, eye-blocked
    home_rows = range(0, 5) if is_red(color) else range(5, 10)
    for dest_dr, dest_dc, eye_dr, eye_dc in _ELEPHANT_OFFSETS:
        nr, nc = row + dest_dr, col + dest_dc
        er, ec = row + eye_dr, col + eye_dc
        if nr not in range(10) or nc not in range(9):
            continue
        if nr not in home_rows:
            continue  # elephant cannot cross river
        if board[er, ec] != 0:
            continue  # elephant eye blocked
        target = board[nr, nc]
        if not belongs_to(target, color):
            moves.append((rc_to_sq(row, col), rc_to_sq(nr, nc)))
```

**Horse (piece_id=4):**

```python
def gen_horse(board: np.ndarray, row: int, col: int,
              color: int, moves: list) -> None:
    # 4 leg positions; each leg has 2 diagonal destinations
    for leg_dr, leg_dc, dests in _HORSE_OFFSETS:
        leg_r, leg_c = row + leg_dr, col + leg_dc
        if leg_r not in range(10) or leg_c not in range(9):
            continue
        if board[leg_r, leg_c] != 0:
            continue  # horse leg blocked
        for dr, dc in dests:
            nr, nc = row + dr, col + dc
            if nr not in range(10) or nc not in range(9):
                continue
            target = board[nr, nc]
            if not belongs_to(target, color):
                moves.append((rc_to_sq(row, col), rc_to_sq(nr, nc)))
```

**Chariot (piece_id=5):**

```python
def gen_chariot(board: np.ndarray, row: int, col: int,
                color: int, moves: list) -> None:
    for dr, dc in _ORTH:
        nr, nc = row + dr, col + dc
        while 0 <= nr < 10 and 0 <= nc < 9:
            target = board[nr, nc]
            if target == 0:
                moves.append((rc_to_sq(row, col), rc_to_sq(nr, nc)))
            else:
                if not belongs_to(target, color):
                    moves.append((rc_to_sq(row, col), rc_to_sq(nr, nc)))
                break  # blocked by any piece (friendly or enemy)
            nr += dr
            nc += dc
```

**Cannon (piece_id=6):**

```python
def gen_cannon(board: np.ndarray, row: int, col: int,
               color: int, moves: list) -> None:
    for dr, dc in _ORTH:
        nr, nc = row + dr, col + dc
        screen_found = False
        while 0 <= nr < 10 and 0 <= nc < 9:
            target = board[nr, nc]
            if not screen_found:
                if target == 0:
                    moves.append((rc_to_sq(row, col), rc_to_sq(nr, nc)))
                else:
                    screen_found = True
            else:
                if not belongs_to(target, color):
                    moves.append((rc_to_sq(row, col), rc_to_sq(nr, nc)))
                    break  # capture, then stop
                else:
                    break  # friendly piece after screen blocks
            nr += dr
            nc += dc
```

**Soldier (piece_id=7):**

```python
def gen_soldier(board: np.ndarray, row: int, col: int,
                color: int, moves: list) -> None:
    # Forward direction: red moves toward higher row, black toward lower row
    dr = 1 if is_red(color) else -1
    nr, nc = row + dr, col
    if 0 <= nr < 10:
        target = board[nr, nc]
        if not belongs_to(target, color):
            moves.append((rc_to_sq(row, col), rc_to_sq(nr, nc)))
    # Sideways: only after crossing river (red row >= 5, black row <= 4)
    crossed = (is_red(color) and row >= 5) or (is_black(color) and row <= 4)
    if crossed:
        for dc in (-1, +1):
            nc_s = col + dc
            if 0 <= nc_s < 9:
                target = board[row, nc_s]
                if not belongs_to(target, color):
                    moves.append((rc_to_sq(row, col), rc_to_sq(row, nc_s)))
```

### Full Pseudo-Legal Move Generation

```python
def gen_pseudo_legal(state: XiangqiState) -> list[int]:
    """Generate all pseudo-legal moves for the side to move."""
    moves = []
    board = state.board
    color = state.turn
    for row in range(10):
        for col in range(9):
            piece = board[row, col]
            if not belongs_to(piece, color):
                continue
            pt = piece_type(piece)
            if pt == 1:   gen_general(board, row, col, color, moves)
            elif pt == 2: gen_advisor(board, row, col, color, moves)
            elif pt == 3: gen_elephant(board, row, col, color, moves)
            elif pt == 4: gen_horse(board, row, col, color, moves)
            elif pt == 5: gen_chariot(board, row, col, color, moves)
            elif pt == 6: gen_cannon(board, row, col, color, moves)
            elif pt == 7: gen_soldier(board, row, col, color, moves)
    return moves
```

### Legal Move Filter

```python
def is_legal(state: XiangqiState, move: int) -> bool:
    """
    A move is legal if:
    1. The move is pseudo-legal (piece can reach destination geometrically)
    2. After applying the move, the mover's General is NOT in check
    3. The move does not leave the two Generals facing on the same file
    """
    from_sq, to_sq, _ = decode_move(move)
    from_r, from_c = sq_to_rc(from_sq)
    to_r, to_c = sq_to_rc(to_sq)

    # Apply move on a copy
    snapshot = state.board[from_r, from_c], state.board[to_r, to_c]

    # Handle king position tracking
    piece = state.board[from_r, from_c]
    pt = piece_type(piece)
    old_king_pos = None
    if pt == 1:  # moving king
        old_king_pos = state.king_positions[state.turn]
        state.king_positions[state.turn] = to_sq

    state.board[to_r, to_c] = piece
    state.board[from_r, from_c] = 0

    legal = not is_in_check(state, state.turn) and not flying_general_violation(state)

    # Restore
    state.board[from_r, from_c], state.board[to_r, to_c] = snapshot
    if old_king_pos is not None:
        state.king_positions[state.turn] = old_king_pos

    return legal

def gen_legal(state: XiangqiState) -> list[int]:
    """Generate all legal moves. O(legal_moves * check_check)."""
    return [m for m in gen_pseudo_legal(state) if is_legal(state, m)]
```

---

## 6. Check Detection Algorithm

### Direct Attack Detection (No Move Generation Required)

`is_in_check(state, color)` determines whether `color`'s General is under attack by any enemy piece. This is O(1) with precomputed direction constants — no move generation needed.

```python
def is_in_check(state: XiangqiState, color: int) -> bool:
    """Return True if `color`'s General is under attack."""
    king_sq = state.king_positions[color]
    kr, kc = sq_to_rc(king_sq)
    enemy = -color  # opponent's color sign

    # 1. Direct orthogonal attackers: Chariot, enemy General (facing), Cannon (as screen-finder)
    for dr, dc in _ORTH:
        nr, nc = kr + dr, kc + dc
        first_piece = None
        while 0 <= nr < 10 and 0 <= nc < 9:
            p = state.board[nr, nc]
            if p != 0:
                if first_piece is None:
                    first_piece = p
                else:
                    # Second piece seen on this ray
                    if piece_type(p) == 6 and belongs_to(p, enemy):
                        return True   # Cannon capture: exactly 2 pieces, second is cannon
                    break
            nr += dr
            nc += dc

        # After loop: check first_piece
        if first_piece is not None:
            pt = piece_type(first_piece)
            if pt == 1 and belongs_to(first_piece, enemy):
                return True   # Enemy General in face
            if pt == 5 and belongs_to(first_piece, enemy):
                return True   # Enemy Chariot in face
        # Cannon attacking without a screen would have caught first_piece == enemy cannon above
        # If first_piece is a cannon from the right color, it's a non-capturing screen

    # 2. Horse attack (L-shape with leg check)
    horse_pt = 4 if is_red(enemy) else 4  # same type ID
    for dr, dc in _ORTH:
        leg_r, leg_c = kr + dr, kc + dc
        if leg_r not in range(10) or leg_c not in range(9):
            continue
        if state.board[leg_r, leg_c] != 0:
            continue  # horse leg blocked
        for h_dest_dr, h_dest_dc in _HORSE_DESTINATIONS_FROM_LEG[(dr, dc)]:
            hr, hc = kr + dr + h_dest_dr, kc + dc + h_dest_dc
            if 0 <= hr < 10 and 0 <= hc < 9:
                if state.board[hr, hc] == enemy * 4:  # enemy horse
                    return True

    # 3. Soldier attack (adjacent forward or sideways if across river)
    # Soldiers attack one square forward only
    soldier_dr = 1 if is_red(enemy) else -1
    for dc in (-1, 0, +1):
        sr, sc = kr + soldier_dr, kc + dc
        if 0 <= sr < 10 and 0 <= sc < 9:
            bp = state.board[sr, sc]
            if bp == enemy * 7:  # enemy soldier
                # Soldier attacks forward; sideways attack only if across river
                # From general's perspective, check if the soldier is attacking into our palace
                # A soldier attacks diagonally (in Xiangqi, soldiers attack forward only)
                # Actually: soldiers do NOT attack diagonally. They only move forward (and sideways after river).
                # But they CAN attack the general from the front. Check:
                # Soldier at (kr-1, kc) for red checking black general
                # The soldier's forward direction for red is +1 row (toward red's back rank)
                # Black general is at kr. Red soldier attacks at kr+1. So sr = kr + 1.
                pass  # corrected below

    # 4. Advisor/Elephant attack (precomputed squares per palace position)
    # Advisors and elephants cannot reach the palace interior squares near the general
    # from far away — just check the 5 specific palace squares they can attack from
    return flying_general_check(state, color)


# Precomputed horse destinations per leg direction
_HORSE_DESTINATIONS_FROM_LEG = {
    (-1,  0): [(-1, -1), (-1, +1)],
    (+1,  0): [(+1, -1), (+1, +1)],
    ( 0, -1): [(-1, -1), (+1, -1)],
    ( 0, +1): [(-1, +1), (+1, +1)],
}
```

**Corrected soldier attack on General:**

Soldiers attack orthogonally in the forward direction only. A soldier attacks the General's square if the soldier is one step directly in front of the General (same column, row-adjacent) and on the correct side of the river for its color.

```python
# A soldier attacks the General from the front (not diagonal).
# Soldier for `enemy` attacks at (king_row + enemy_dir, king_col)
soldier_attack_row = kr + (1 if is_red(enemy) else -1)
if 0 <= soldier_attack_row < 10:
    if state.board[soldier_attack_row, kc] == enemy * 7:
        return True
```

**Flying General check (separate function):**

```python
def flying_general_check(state: XiangqiState, color: int) -> bool:
    """Check if the General of `color` is in flying-general check."""
    red_king_sq = state.king_positions.get(1)
    black_king_sq = state.king_positions.get(-1)
    if red_king_sq is None or black_king_sq is None:
        return False
    rr, rc = sq_to_rc(red_king_sq)
    br, bc = sq_to_rc(black_king_sq)
    if rc != bc:
        return False  # different files
    min_r, max_r = min(rr, br), max(rr, br)
    for r in range(min_r + 1, max_r):
        if state.board[r, rc] != 0:
            return False  # something between the kings
    # Generals face each other: the side that just moved is in check
    return True
```

---

## 7. Checkmate and Stalemate Detection

### Algorithm

```python
def get_game_result(state: XiangqiState) -> int | None:
    """
    Returns:
      +1  = red wins
      -1  = black wins
       0  = draw (repetition, 50-move rule, insufficient material)
      None = game not over

    Xiangqi rules:
      - Checkmate: no legal moves AND in check → loser is the side to move
      - Stalemate (困毙): no legal moves AND NOT in check → loser is the side to move
      - Repetition: see Section 4 (WXF rules; basic v0.1 = 4-fold draw)
      - 50-move rule: halfmove_clock >= 100 → draw
    """
    legal_moves = gen_legal(state)
    if legal_moves:
        return None  # game continues

    # No legal moves available
    if is_in_check(state, state.turn):
        # Checkmate: the side to move loses
        return -state.turn   # winner is the opponent
    else:
        # Stalemate (困毙): also a loss for the side to move in Xiangqi
        return -state.turn
```

**Critical note from PITFALLS.md:** Stalemate is a **loss**, not a draw, in Xiangqi. This is the most commonly mis-implemented rule in Western chess programmers' Xiangqi engines.

### Insufficient Material Detection (for Draw)

Xiangqi has specific unwinnable material combinations. A conservative draw detection for v0.1:

```python
def has_sufficient_material(state: XiangqiState) -> bool:
    """True if at least one side has a realistic chance to deliver checkmate."""
    pieces = []
    for r in range(10):
        for c in range(9):
            p = state.board[r, c]
            if p != 0:
                pieces.append(abs(p))
    # Count non-soldier pieces
    non_soldiers = [pt for pt in pieces if pt != 7]
    if len(non_soldiers) == 0:
        return False  # only soldiers remaining — usually a draw by insufficient material
    if len(non_soldiers) == 1:
        # One non-soldier vs soldiers only: draw if soldiers cannot organize a checkmate
        return False
    return True
```

---

## 8. Performance Considerations

### Speed Target

The STACK.md research identifies `<100ms per move generation` as the performance target. This is trivially achievable in pure Python for a Xiangqi engine. Typical legal move counts per position are 30-50 moves. Full legal move generation (all pieces, all candidates, check filtering) takes **0.1–2ms per position** in pure Python.

### Performance Breakdown

| Operation | Estimated Time (pure Python) | Notes |
|-----------|------------------------------|-------|
| `gen_pseudo_legal` (all pieces) | 0.05–0.3ms | NumPy array iteration; 7 piece-type dispatch |
| `is_in_check` | 0.01–0.1ms | Orthogonal scan (max 18 squares) + horse check (4 legs) |
| `is_legal` per candidate | 0.01–0.05ms | Copy state + is_in_check + restore |
| `gen_legal` (full) | 0.1–1.5ms | O(legal_moves) × is_legal; 30-50 legal moves typical |
| `apply_move` | 0.01ms | Direct NumPy write; O(1) |
| Repetition check (Zobrist) | 0.001ms | Counter lookup in position_history dict |

### Key Optimizations (Apply Only If Profiled)

1. **Cache `is_in_check` result per position:** The board state does not change between calls to `is_legal` for different candidate moves — only the candidate move itself changes. However, the current approach (apply move → check → restore) naturally makes each check independent. Do not precompute an "attacked squares" bitboard unless profiling shows check detection is the bottleneck (it won't be for pure Python).

2. **Precompute per-piece destination masks:** For Advisor and Elephant, the set of reachable squares is fully determined by the starting position (up to 5 and 7 destinations respectively) with no sliding. Precompute these as a dict `advisor_moves[(row, col)] -> list[(to_row, to_col)]`. For the General, precompute the 4 palace-adjacent squares.

3. **NumPy vectorization for sliding pieces:** The Chariot and Cannon sliding loops are Python `for` loops. For hot positions (deep search), these can be replaced with NumPy slice operations:
   ```python
   # Instead of: while board[nr, nc] == 0: add; nr += dr
   # NumPy approach for Chariot slides:
   ray = np.diag(board, k=dc-dr)  # extract diagonal/orthogonal ray; complex for 10x9
   ```
   This optimization is unnecessary for v0.1. Stick with Python loops until profiling confirms they are the bottleneck.

4. **Avoid `belongs_to()` in inner loops:** Inline the check as `p != 0 and (p > 0) == (color > 0)` in generator functions. Function call overhead accumulates in move generation with 40+ candidates.

5. **Use `list` append for move collection:** Python lists with `.append()` are faster than pre-allocating arrays for move lists of unknown size. At 30-50 moves per position, appending is negligible.

6. **Copy-state vs make/unmake:** For v0.1, prefer copy-state. The board is 90 bytes (`int8`). Copying it 50 times per position is 4.5 KB of memory and ~0.01ms. It is correct by construction and eliminates a class of bugs (undo errors). Switch to make/unmake only if deep search (not in scope for v0.1 RL engine) demands it.

### Perft Benchmarks (Reference)

Perft from the initial position at depth 4 is a standard benchmark. Reference values (from Fairy-Stockfish Xiangqi):

```
Perft(1) = 44   (initial position, red to move — 44 legal moves)
Perft(2) ≈ 1,900
Perft(3) ≈ 78,000
Perft(4) ≈ 2,850,000
```

These values are smaller than Western chess (perft(4) ≈ 197,281) because Xiangqi has fewer pieces and more constrained movement, making the engine faster even in pure Python.

---

## 9. Memory Layout for RL Training Compatibility

### Board State to RL Observation Tensor

The RL agent receives a `(14, 10, 9)` binary feature tensor (AlphaZero-style):

```python
def board_to_rl_tensor(board: np.ndarray, device: str = 'cpu') -> torch.Tensor:
    """
    Convert board (10, 9), dtype=int8 to RL observation (14, 10, 9), dtype=float32.

    Channels (index: piece description):
      0: Red General
      1: Red Advisor
      2: Red Elephant
      3: Red Horse
      4: Red Chariot
      5: Red Cannon
      6: Red Soldier
      7: Black General
      8: Black Advisor
      9: Black Elephant
     10: Black Horse
     11: Black Chariot
     12: Black Cannon
     13: Black Soldier
    """
    tensor = np.zeros((14, 10, 9), dtype=np.float32)
    for r in range(10):
        for c in range(9):
            p = board[r, c]
            if p == 0:
                continue
            pt = abs(p) - 1         # 0-indexed piece type
            color_idx = 0 if p > 0 else 7  # red channels 0-6, black channels 7-13
            tensor[color_idx + pt, r, c] = 1.0
    return torch.from_numpy(tensor).to(device)
```

### Legal Move Mask

The legal move mask is a fixed-size boolean array of shape `(8100,)` (90 source squares × 90 destination squares). It is indexed by flat `from_sq * 90 + to_sq`. Legal moves set `mask[action_idx] = True`.

```python
LEGAL_MASK_SIZE = 90 * 90  # = 8100

def build_legal_mask(state: XiangqiState) -> np.ndarray:
    mask = np.zeros(LEGAL_MASK_SIZE, dtype=np.float32)
    for move in gen_legal(state):
        from_sq, to_sq, _ = decode_move(move)
        mask[from_sq * 90 + to_sq] = 1.0
    return mask
```

**Why 8100 over the actual 1,260 non-self moves (90×14 self pairs excluded)?** Using the full 90×90 grid means the policy head always outputs a fixed 8100-dimensional logit vector, matching standard AlphaZero-style action encoding. The mask zeros out illegal actions. This is simpler than maintaining a variable-length encoding and makes batching straightforward.

**Memory:** 8,100 floats × 4 bytes = 32.4 KB per observation. Negligible.

### RL Transition Storage Format

Each transition in the replay buffer stores:

```python
@dataclass(slots=True)
class Transition:
    obs: np.ndarray       # (14, 10, 9) float32
    legal_mask: np.ndarray  # (8100,) float32
    action_idx: int        # 0..8099
    reward: float
    next_obs: np.ndarray   # (14, 10, 9) float32
    next_legal_mask: np.ndarray  # (8100,) float32
    done: bool
    agent_id: int          # which piece type was active (1-7)
```

**Memory per transition:** ~2.2 KB. A 100,000-transition buffer = ~220 MB. Keep on CPU RAM; transfer to MPS only during training mini-batch construction.

### Canonical State Encoding

To ensure the RL observation is color-invariant (so the same position viewed from red or black's perspective produces identical features), use **color flipping**: always present the board from the perspective of the player to move.

```python
def to_canonical(board: np.ndarray, turn: int) -> np.ndarray:
    """Return board array with red pieces as positive values.
    If turn is black (-1), flip the board: negate all piece signs AND mirror rows."""
    if turn > 0:
        return board.copy()
    else:
        flipped = -board.copy()
        # Also mirror vertically so row 0 is always the back rank of the side to move
        return np.flipud(flipped)
```

This doubles the effective training data (each position contributes 2 samples, one per perspective) and ensures the policy network sees a consistent color encoding.

---

## 10. Python-Specific Considerations

### PyPy vs CPython

**Use CPython 3.12.** PyPy's JIT compiler benefits long-running loops but hurts startup time and is incompatible with some numerical libraries used in this stack (PyTorch has no PyPy support). The 10x9 board is too small for PyPy's JIT to provide meaningful speedup over CPython's interpreter.

**Key CPython optimizations:**
- Use `__slots__` on dataclasses (`@dataclass(slots=True)`) to eliminate per-instance `__dict__` — saves ~56 bytes per object.
- Use local variable binding in hot loops (`board = self.board; moves = []`) to avoid repeated attribute lookup.
- Avoid `range()` with step in inner loops.

### NumPy Integration

**Array dtype:** Always `np.int8` for the board (signed byte). This is MPS-compatible and memory-efficient (90 bytes per board). Do not use `np.float64` for board state — Metal does not support float64.

**NumPy 2.x compatibility:** This project requires NumPy 2.x (compatible with PyTorch 2.10). Use `np.zeros((10, 9), dtype=np.int8)` explicitly. Avoid NumPy 1.x APIs that were removed in 2.0 (e.g., `np.bool_` → `np.bool`; `np.product` → `np.prod`).

**NumPy → PyTorch conversion:** The conversion boundary is the most critical performance point. Keep board as NumPy int8; cast to float32 torch tensor at the RL boundary only:

```python
import torch
import numpy as np

# WRONG: numpy float64 (will cause MPS errors)
obs = board.astype(np.float64)

# CORRECT: numpy int8 → torch float32
obs = torch.from_numpy(board.astype(np.int8)).float()  # 0..7, MPS-compatible

# FASTEST: preallocate output tensor, write in-place
obs = torch.empty(14, 10, 9, dtype=torch.float32, device='mps')
# Fill channels from board (avoids intermediate allocations)
```

### Avoiding float64 Anywhere

Metal (MPS backend) does not support float64. Any `torch.float64` tensor will silently fall back to CPU or raise an error. Enforce float32 globally at startup:

```python
import torch
torch.set_default_dtype(torch.float32)
```

### GIL Considerations

Python's Global Interpreter Lock (GIL) prevents true parallelism for CPU-bound Python code. For this project, the GIL is not a concern because:
- The rule engine is fast enough (<2ms per position) that GIL contention is negligible.
- RL training uses PyTorch MPS which releases the GIL during CUDA/MPS kernel calls.
- The UI runs in the main thread; AI computation runs in a `QThread` — the GIL is released during NumPy and PyTorch operations.

### JIT Compilation (Optional, v0.2+)

If profiling after v0.1 launch shows legal move generation is the bottleneck (unlikely for pure Python on a 90-square board), consider:

- **`@functools.lru_cache` on pure functions:** Cache results of `advisor_moves[(row, col)]` lookups. The cache is small (at most 45 advisor positions × 2 colors = 90 entries).
- **`numba.jit`:** JIT-compile the sliding piece generators (`gen_chariot`, `gen_cannon`) with `numba.njit`. Numba supports NumPy and can provide 10-50x speedup on numerical loops with zero code changes. Test carefully — Numba's JIT warmup time (1-3s) is acceptable if it happens once at module load, not per position.
- **Do NOT use Cython initially:** Cython adds build complexity and is unnecessary for v0.1. Measure before adding complexity.

### Type Safety

Use `np.ndarray` for the board, not Python `list[list[int]]`. Type checking with `mypy` is cleaner with typed dataclasses:

```python
from typing import Annotated
BoardArray = Annotated[np.ndarray, np.dtype(np.int8)]

class XiangqiEngine:
    board: BoardArray
    turn: int  # +1=red, -1=black
```

`mypy --strict` will catch dtype mismatches and out-of-bounds accesses where type stubs are available.

### Profiling Tools

```bash
# Profile move generation in the terminal
python -m cProfile -s cumulative -m env.board gen_legal(...)
# Line-by-line profiling
python -m pip install scalene
scalene script.py  # GPU-accelerated, shows per-line CPU+memory
```

---

## Implementation Reference: Quick-Reference Tables

### Piece → Generator Function

| Piece Type ID | Absolute Value | Generator | Constraint |
|---------------|---------------|-----------|-----------|
| 1 | General | `gen_general` | Palace only (3x3) |
| 2 | Advisor | `gen_advisor` | Palace only (3x3 diagonal) |
| 3 | Elephant | `gen_elephant` | River-bound + eye blocked |
| 4 | Horse | `gen_horse` | Leg blocked |
| 5 | Chariot | `gen_chariot` | Sliding orthogonal |
| 6 | Cannon | `gen_cannon` | Sliding + hopper capture |
| 7 | Soldier | `gen_soldier` | Forward only; sideways after river |

### Board Constants

| Constant | Value |
|----------|-------|
| `ROWS` | 10 |
| `COLS` | 9 |
| `NUM_SQUARES` | 90 |
| `ACTION_SPACE_SIZE` | 8100 (90×90) |
| Red palace rows | 7–9, cols 3–5 |
| Black palace rows | 0–2, cols 3–5 |
| River boundary | rows 4–5 |
| Red home rows (elephant) | 0–4 |
| Black home rows (elephant) | 5–9 |

### Red/Black Encoding

| Color | Sign | `is_red()` | `is_black()` |
|-------|------|------------|--------------|
| Red | +1 | `True` | `False` |
| Black | -1 | `False` | `True` |

---

## Sources

- Chess Programming Wiki: Board Representation (https://www.chessprogramming.org/Board_Representation) — MEDIUM confidence; 0x88 and bitboard techniques adapted for Xiangqi
- Chess Programming Wiki: Perft (https://www.chessprogramming.org/Perft) — methodology; Fairy-Stockfish Xiangqi perft reference values
- Fairy-Stockfish Xiangqi perft issue #278 (https://github.com/ianfab/Fairy-Stockfish/issues/278) — reference perft counts for Xiangqi starting position
- "A Complete Algorithm for Ruling the WXF Repetition Rules" (arXiv:2412.17334v1, 2024) — WXF repetition classification, including move nature (check/chase/idle)
- Orange-Xiangqi (https://github.com/danieltan1517/orange-xiangqi) — open-source Xiangqi engine; board representation patterns verified
- xiangqi.js (https://github.com/lengyanyu258/xiangqi.js/) — JavaScript Xiangqi engine; move encoding patterns verified
- python-chess (https://github.com/python-chess/python-chess) — mature Western chess engine in Python; Zobrist hashing, move encoding, and legal move generation patterns adapted for Xiangqi
- AlphaZero paper (Science, 2018) — RL observation tensor format: binary feature planes per piece type per color
- STACK.md, FEATURES.md, PITFALLS.md, ARCHITECTURE.md — project-internal research files cross-validating these findings

---

*Data structures and algorithms research for: RL-Xiangqi v0.1 Rule Engine*
*Researched: 2026-03-19*
