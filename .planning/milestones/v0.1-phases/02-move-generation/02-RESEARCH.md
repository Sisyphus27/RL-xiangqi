# Phase 2: 棋子走法生成与规则校验 - Research

**Researched:** 2026-03-19
**Domain:** Xiangqi move generation, check detection, and rule enforcement
**Confidence:** HIGH (Xiangqi rules verified via RULES.md and PITFALLS.md; perft values verified via Chess Programming Wiki / Fairy-Stockfish community reference)

---

<user_constraints>
## User Constraints (from 02-CONTEXT.md)

### Locked Decisions
- Each `gen_*()` is **pure**: returns all pseudo-legal moves, NO king safety check inside generators
- `generate_legal_moves()` collects pseudo-legal moves, filters by simulating on board copy (via `XiangqiState.copy()`)
- Raw `list[int]` 16-bit move encoding returned (no Move dataclass)
- `king_positions` dict (Phase 1) used for O(1) king lookup during check detection
- Sliding pieces use direction scanning (not bitboard)
- Face-to-face rule as a post-filter on the resulting board state

### Claude's Discretion
- Internal organization of knee-position tables (list of tuples or dict)
- Whether to inline the face-to-face check in each generator or as a post-filter (POST-FILTER LOCKED)
- Horse knee-position exact offset pairs
- Whether to use `PIECE_ATTACKS` direction constant table or encode directions inline
- Test fixture naming and organization style

### Deferred Ideas (OUT OF SCOPE)
None.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MOVE-01 | 帅/将: 1-step orthogonal, palace-only | gen_general: orthogonal offsets + IN_PALACE mask |
| MOVE-02 | 车: orthogonal slide, stop at first blocker | gen_chariot: 4-direction scan, stop on any piece |
| MOVE-03 | 马: L-shape with leg-block check | gen_horse: 4 leg positions, 2 destinations each, leg must be empty |
| MOVE-04 | 炮: orthogonal slide non-capture, exactly-1-screen capture | gen_cannon: 4-dir scan with screen_count flag; two distinct path behaviors |
| MOVE-05 | 士: diagonal 1-step, palace-only | gen_advisor: 4 diagonal offsets + IN_PALACE mask |
| MOVE-06 | 象/相: diagonal 2-step, eye-block + river constraint | gen_elephant: 4 diagonal destinations, eye midpoint empty, row boundary check |
| MOVE-07 | 兵/卒: forward-only before river, forward+sideways after | gen_soldier: row threshold (5 for red, 4 for black) for sideways unlock |
| RULE-01 | is_legal_move: ownership + path + no-self-check | Simulate move on board copy; call is_in_check on resulting state |
| RULE-02 | generate_legal_moves: all legal moves | Collect all pseudo-legal from gen_* functions, filter via is_legal_move |
| RULE-03 | is_in_check: detect if general is capturable | Direct attack-scan per enemy piece type; use king_positions for O(1) lookup |
| RULE-04 | Cannot move general into check | is_legal_move already covers this (post-move check) |
| RULE-05 | Face-to-face rule: no column move when generals face | Post-filter after pseudo-legal generation: scan column between generals |
| RULE-06 | get_game_result: red/black win, draw, in-progress | Check legal move count; is_in_check for win/loss classification |
</phase_requirements>

---

## Summary

Phase 2 builds the move-generation and rule-validation core of the Xiangqi engine. Each piece type gets a pure generator function (`gen_*()`) that returns all pseudo-legal destinations given board geometry. Legal move filtering is deferred to `generate_legal_moves()`, which simulates each candidate on a board copy and discards moves that leave the mover's own General in check. This separation keeps generators independently testable and mirrors standard Western chess engine architecture.

The key technical decisions are: (1) pure generators with post-filter validation, (2) 16-bit integer move encoding already defined in Phase 1, (3) direction-scanning for sliding pieces (no bitboard), and (4) `king_positions` dict for O(1) king lookup in `is_in_check()`. The face-to-face rule is a lightweight post-filter that scans the file between the two generals after a candidate move is applied.

**Primary recommendation:** Implement three modules -- `moves.py` (piece generators), `legal.py` (check detection, legal-move filtering, apply/undo), `rules.py` (face-to-face and special rule helpers) -- with per-piece unit tests using minimal FEN boards, then validate the whole system against CPW Xiangqi perft reference values.

---

## Standard Stack

No additional external dependencies beyond Phase 1's `numpy`. All move generation is implemented in pure Python using NumPy array indexing.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `numpy` | >=2.0 | Board array (`np.int8`), boolean masks (`np.bool`), boundary constants | Already in project; fast O(1) square access |
| `pytest` | >=8.0 | Unit test runner | Already in project; Wave 0 infrastructure exists |

### Direction Constants (to add to `constants.py` or `moves.py`)

```python
# 4 orthogonal directions for chariot, cannon, general
_ORTHOGONAL = [(-1, 0), (+1, 0), (0, -1), (0, +1)]

# 4 diagonal directions for advisor, elephant
_DIAGONAL = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]

# Horse leg+destination pairs: each (leg_dr, leg_dc, [dest1], [dest2])
# Source: RULES.md §2.3, PITFALLS.md Pitfall 3
_HORSE_LEG_DEST = [
    (-1,  0, (-2, -1), (-2, +1)),  # leg up → two right-angle destinations
    (+1,  0, (+2, -1), (+2, +1)),  # leg down
    ( 0, -1, (-1, -2), (+1, -2)),  # leg left
    ( 0, +1, (-1, +2), (+1, +2)),  # leg right
]

# Elephant diagonal destinations with their eye midpoint offsets
# Source: RULES.md §2.6, PITFALLS.md Pitfall 4
_ELEPHANT_EYE_DEST = [
    (-2, -2, -1, -1),  # (dest_dr, dest_dc, eye_dr, eye_dc)
    (-2, +2, -1, +1),
    (+2, -2, +1, -1),
    (+2, +2, +1, +1),
]
```

---

## Architecture Patterns

### Module Structure

```
src/xiangqi/engine/
    moves.py    — gen_general, gen_chariot, gen_horse, gen_cannon,
                   gen_advisor, gen_elephant, gen_soldier (pseudo-legal only)
    legal.py    — is_in_check, is_legal_move, generate_legal_moves,
                   apply_move, undo_move
    rules.py    — flying_general_violation (post-filter),
                   _col_is_blocked_by_generals (helper)
```

Each `gen_*()` function:
- Takes `(board, from_sq)` and returns `list[int]` of encoded moves
- Checks board boundaries with `(0 <= nr < 10) and (0 <= nc < 9)`
- Checks own-piece occupancy before adding destination
- Does NOT check king safety (pure geometry only)

### Check-Detection Pattern (is_in_check)

Use `king_positions[color]` for O(1) king lookup. Scan for each attacker type:

```python
# Source: DATA_STRUCTURES.md §6, RULES.md §6
def is_in_check(state: XiangqiState, color: int) -> bool:
    ksq = state.king_positions[color]   # O(1) via Phase 1 king_positions dict
    kr, kc = divmod(ksq, 9)
    enemy = -color

    # 1. Orthogonal attackers: chariot, enemy general (face-to-face), cannon
    for dr, dc in _ORTHOGONAL:
        scan along this ray; track first_piece and screen_count
        if screen_count == 1 and second_piece == enemy*cannon_type → check
        if first_piece == enemy*chariot_type → check
        if first_piece == enemy*general and ray is open → check (face-to-face)

    # 2. Horse (L-shape, leg must be empty)
    for leg_dr, leg_dc, dest1, dest2 in _HORSE_LEG_DEST:
        leg_r, leg_c = kr + leg_dr, kc + leg_dc
        if board[leg_r, leg_c] != 0: continue  # blocked
        for dest_dr, dest_dc in [dest1, dest2]:
            nr, nc = kr + leg_dr + dest_dr, kc + leg_dc + dest_dc
            if board[nr, nc] == enemy * MA_TYPE: return True

    # 3. Soldier: forward square only (red: kr+1, black: kr-1)
    # Source: RULES.md §2.7 — soldiers attack orthogonally forward only, NOT diagonally
    srow = kr + (1 if color == +1 else -1)
    if 0 <= srow < 10 and state.board[srow, kc] == enemy * SOLDIER_TYPE: return True
    # Sideways attack (only if soldier is across the river)
    for dc in (-1, +1):
        sc = kc + dc
        if 0 <= sc < 9:
            # Soldier attacks sideways only if it is on the opponent's half
            soldier_row = srow  # row where soldier would be adjacent to king
            if 0 <= soldier_row < 10:
                p = state.board[soldier_row, sc]
                if p == enemy * SOLDIER_TYPE:
                    # Soldier is across river (row 5+ for red attacking, row 4- for black attacking)
                    if (enemy == +1 and soldier_row >= 5) or (enemy == -1 and soldier_row <= 4):
                        return True

    # 4. Advisor: adjacent diagonal within palace
    for dr, dc in _DIAGONAL:
        nr, nc = kr + dr, kc + dc
        if IN_PALACE[nr, nc] and state.board[nr, nc] == enemy * ADVISOR_TYPE: return True

    # 5. Elephant: adjacent diagonal on home half (eye empty)
    for dr, dc in _DIAGONAL:
        nr, nc = kr + dr, kc + dc
        if state.board[nr - dr, nc - dc] == 0:  # eye empty
            if state.board[nr, nc] == enemy * ELEPHANT_TYPE: return True

    return False
```

**Critical correction to DATA_STRUCTURES.md soldier attack section:** DATA_STRUCTURES.md §6 incorrectly discusses soldiers attacking diagonally. In Xiangqi, soldiers attack orthogonally forward only (RULES.md §2.7 confirms: "Soldiers always move forward only. Sideways is permitted only after crossing the river."). A soldier attacks the General only if directly in front (same column, adjacent row).

### Legal Move Filter Pattern

```python
# Source: 02-CONTEXT.md — pure generators + board copy post-filter
def is_legal_move(state: XiangqiState, move: int) -> bool:
    from_sq, to_sq, _ = decode_move(move)
    snap = state.copy()
    apply_move(snap, move)
    legal = not is_in_check(snap, state.turn)   # own king must be safe
    legal = legal and not flying_general_violation(snap, from_sq, to_sq)
    return legal

def generate_legal_moves(state: XiangqiState) -> list[int]:
    # Collect all pseudo-legal from each piece
    moves = []
    for piece_sq in all_pieces_of_color(state):
        piece = state.board.flat[piece_sq]
        pt = abs(piece)
        if pt == 1: moves += gen_general(state.board, piece_sq, state.turn)
        elif pt == 2: moves += gen_advisor(state.board, piece_sq, state.turn)
        # ... etc
    return [m for m in moves if is_legal_move(state, m)]
```

### Face-to-Face Post-Filter

```python
# Source: RULES.md §4.1, PITFALLS.md Pitfall 5
# Implemented as post-filter in generate_legal_moves (locked decision)
def _generals_face_each_other(state: XiangqiState) -> Tuple[int, int] | None:
    """Return (file_col,) if both generals face with nothing between, else None."""
    rk = state.king_positions.get(+1)
    bk = state.king_positions.get(-1)
    if rk is None or bk is None:
        return None
    rr, rc = divmod(rk, 9)
    br, bc = divmod(bk, 9)
    if rc != bc:
        return None  # different files
    lo, hi = min(rr, br), max(rr, br)
    for r in range(lo + 1, hi):
        if state.board[r, rc] != 0:
            return None  # something between them
    return rc  # they face each other on this file

def flying_general_violation(state_after_move: XiangqiState,
                             from_sq: int, to_sq: int) -> bool:
    """After a move, would both generals face each other with nothing between?"""
    rk = state_after_move.king_positions.get(+1)
    bk = state_after_move.king_positions.get(-1)
    if rk is None or bk is None:
        return False
    rr, rc = divmod(rk, 9)
    br, bc = divmod(bk, 9)
    if rc != bc:
        return False
    # Scan the file between the two generals
    lo, hi = min(rr, br), max(rr, br)
    for r in range(lo + 1, hi):
        if state_after_move.board[r, rc] != 0:
            return False
    # Generals face each other — this is a flying general violation
    return True
```

Note: `flying_general_violation` is called in `is_legal_move` on the board state AFTER the candidate move is applied. If `from_sq` and `to_sq` are on the same column as the enemy general and the move vacates that column with no other piece intervening, the move is illegal.

### Apply/Unmake Pattern

```python
# Source: DATA_STRUCTURES.md §4, PITFALLS.md Pitfall 9
# Use XiangqiState.copy() for Phase 2 — correct by construction (Phase 1)
def apply_move(state: XiangqiState, move: int) -> int:
    """Apply move to state. Returns captured piece (0 if none)."""
    from_sq, to_sq, _ = decode_move(move)
    fr, fc = divmod(from_sq, 9)
    tr, tc = divmod(to_sq, 9)
    piece = state.board[fr, fc]
    captured = int(state.board[tr, tc])

    # Update board
    state.board[tr, tc] = piece
    state.board[fr, fc] = 0

    # Update king_positions if general moved
    pt = abs(int(piece))
    if pt == 1:  # general
        state.king_positions[state.turn] = to_sq

    # Update turn
    state.turn *= -1

    # Update Zobrist hash
    from xiangqi.engine.state import update_hash
    new_hash = update_hash(
        state.zobrist_hash_history[-1],
        from_sq, to_sq, int(piece), captured, state.turn
    )
    state.zobrist_hash_history.append(new_hash)

    # Update history
    state.move_history.append(move)
    if pt == 7 or captured != 0:  # soldier move or capture
        state.halfmove_clock = 0
    else:
        state.halfmove_clock += 1

    return captured

def undo_move(state: XiangqiState) -> None:
    """Undo the last move in move_history. State must have at least one move."""
    move = state.move_history.pop()
    state.zobrist_hash_history.pop()
    state.turn *= -1
    state.halfmove_clock = max(0, state.halfmove_clock - 1)

    from_sq, to_sq, _ = decode_move(move)
    fr, fc = divmod(from_sq, 9)
    tr, tc = divmod(to_sq, 9)
    piece = state.board[tr, tc]

    # Restore captured piece (captured piece is in state.zobrist_hash_history diff)
    # The piece at to_sq after the move is the moved piece; restore from history
    # Use the hash diff: the captured piece is XORed out during update_hash
    # Simplest: restore board from zobrist would require full recompute
    # Use the undo_record pattern for correctness:
    # → For Phase 2, prefer XiangqiState.copy() in is_legal_move rather than undo
    pass
```

**Important:** The CONTEXT.md specifies `XiangqiState.copy()` for legal-move validation. For `undo_move` used in perft or search (Phase 3+), use the copy-state approach: instead of applying then undoing, simply use `state.copy()` and discard the copy after the check. This avoids undo complexity entirely for the Phase 2 scope. If undo is needed later (Phase 3 perft), implement a minimal `MoveUndo` record.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Horse blocking | Precomputed knight-style L-table | Per-leg occupancy check on orthogonal intermediate square | Knight table has no blocking concept; horse leg must be empty |
| Cannon capture | Rook sliding (one code path) | Two-phase scan: track screen_count flag (0 for slide, 1 for capture candidate) | Cannon has entirely different rules for slide vs capture; conflating is the most common Xiangqi bug |
| Elephant eye | Only diagonal midpoint check | Diagonal midpoint + river boundary (both independent constraints) | Missing river check allows elephant to attack across the board |
| Check detection | Generate all legal moves to see if king is attacked | Direct `is_in_check()` scanning only attacker types that could reach the king | O(1) per attack type vs O(n) move generation |
| Soldier attack | Diagonal attack (Western chess pawn) | Orthogonal forward only; sideways attack only if soldier is across the river | Xiangqi soldiers never attack diagonally |

**Key insight:** The Cannon is the single most buggy piece in open-source Xiangqi implementations. The screen-count state machine (zero screens → slide, one screen → capture candidate, two+ screens → stop) must be implemented with a per-direction `screen_count` variable that resets on each direction, not a global accumulator.

---

## Common Pitfalls

### Pitfall 1: Horse Leg Blocking (蹩马腿)
**What goes wrong:** Horse moves like a Western knight, leaping regardless of intermediate pieces.
**How to avoid:** For each of the 4 leg directions, the orthogonal adjacent square must be EMPTY before either of the two leg destinations is added. Block the entire leg (both destinations) if the knee square is occupied.
**Source:** PITFALLS.md Pitfall 3, RULES.md §2.3

### Pitfall 2: Cannon Capture Screen Counting
**What goes wrong:** Cannon can capture adjacent pieces (0 screens) or through 2+ screens.
**How to avoid:** Per-direction state machine: `screen_count=0` → add empty squares, stop at first occupied (set `screen_count=1`); `screen_count=1` → if enemy piece: add capture and break; if friendly: break; if empty: continue. Screen can be either color.
**Source:** PITFALLS.md Pitfall 6, RULES.md §2.4

### Pitfall 3: Elephant River Constraint (independent of eye)
**What goes wrong:** Elephant is coded with eye check but no river boundary, or vice versa.
**How to avoid:** Both constraints are independently checked. Red elephant destinations must have `row >= 5`; black elephant destinations must have `row <= 4`. This is checked in addition to the eye midpoint being empty.
**Source:** PITFALLS.md Pitfall 4, RULES.md §2.6

### Pitfall 4: Face-to-Face Missing from Check Detection
**What goes wrong:** The rule is treated as a move legality filter but omitted from `is_in_check()`.
**How to avoid:** `is_in_check()` must include a scan of the file between the two generals: if they share a column with no pieces between, each general is in check from the other. This check runs on every position, not just at move boundaries.
**Source:** PITFALLS.md Pitfall 5, RULES.md §4.1

### Pitfall 5: Soldier Sideways Before River
**What goes wrong:** Soldiers get sideways moves immediately, not only after crossing.
**How to avoid:** Red soldier sideways enabled when `row >= 5` (currently on or past the river row 4-5 boundary). Black soldier sideways enabled when `row <= 4`. Use `>= 5` for red (river is 4-5; row 5 is first black-side square) and `<= 4` for black.
**Source:** RULES.md §2.7, PITFALLS.md (soldier movement notes)

### Pitfall 6: Stalemate = Loss in Xiangqi (not Draw)
**What goes wrong:** `get_game_result()` returns draw when player has no legal moves and is not in check.
**How to avoid:** In Xiangqi, `困毙` (no legal moves, not in check) is a LOSS for the player who cannot move. Both checkmate and stalemate result in the same outcome: the player to move loses.
**Source:** PITFALLS.md Pitfall 7, RULES.md §7.2

---

## Code Examples

### Per-piece generator skeleton (verify each independently testable)

```python
# Source: DATA_STRUCTURES.md §5, adapted for Phase 1 types.py
from .types import Piece, ROWS, COLS, rc_to_sq, sq_to_rc, encode_move
from .constants import IN_PALACE

_ORTHOGONAL = [(-1, 0), (+1, 0), (0, -1), (0, +1)]
_DIAGONAL = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]

_HORSE_LEG_DEST = [
    (-1,  0, (-2, -1), (-2, +1)),
    (+1,  0, (+2, -1), (+2, +1)),
    ( 0, -1, (-1, -2), (+1, -2)),
    ( 0, +1, (-1, +2), (+1, +2)),
]

_ELEPHANT_EYE_DEST = [
    (-2, -2, -1, -1), (-2, +2, -1, +1),
    (+2, -2, +1, -1), (+2, +2, +1, +1),
]

def belongs_to(piece: int, color: int) -> bool:
    return piece != 0 and (piece > 0) == (color > 0)

def gen_general(board: np.ndarray, from_sq: int, color: int) -> list[int]:
    """Orthogonal 1-step, palace-only. Source: MOVE-01, RULES.md §2.1."""
    fr, fc = divmod(from_sq, 9)
    moves = []
    for dr, dc in _ORTHOGONAL:
        nr, nc = fr + dr, fc + dc
        if not (0 <= nr < ROWS and 0 <= nc < COLS):
            continue
        if not IN_PALACE[nr, nc]:
            continue
        target = int(board[nr, nc])
        if not belongs_to(target, color):
            moves.append(encode_move(from_sq, rc_to_sq(nr, nc), is_capture=target != 0))
    return moves

def gen_elephant(board: np.ndarray, from_sq: int, color: int) -> list[int]:
    """Diagonal 2-step, eye-blocked, river-confined. Source: MOVE-06, RULES.md §2.6."""
    fr, fc = divmod(from_sq, 9)
    home_rows = range(0, 5) if color == +1 else range(5, 10)  # red rows 0-4, black rows 5-9
    moves = []
    for dr, dc, er, ec in _ELEPHANT_EYE_DEST:
        nr, nc = fr + dr, fc + dc
        eye_r, eye_c = fr + er, fc + ec
        if not (0 <= nr < ROWS and 0 <= nc < COLS):
            continue
        if nr not in home_rows:
            continue  # cannot cross river
        if board[eye_r, eye_c] != 0:
            continue  # elephant eye blocked
        target = int(board[nr, nc])
        if not belongs_to(target, color):
            moves.append(encode_move(from_sq, rc_to_sq(nr, nc), is_capture=target != 0))
    return moves

def gen_soldier(board: np.ndarray, from_sq: int, color: int) -> list[int]:
    """Forward only; forward+sideways after crossing river.
    Source: MOVE-07, RULES.md §2.7."""
    fr, fc = divmod(from_sq, 9)
    moves = []
    forward_dr = +1 if color == +1 else -1
    nr, nc = fr + forward_dr, fc
    if 0 <= nr < ROWS:
        target = int(board[nr, nc])
        if not belongs_to(target, color):
            moves.append(encode_move(from_sq, rc_to_sq(nr, nc), is_capture=target != 0))
    # Sideways only after crossing river
    # Red across river: fr >= 5 (river is rows 4-5, red rows 5-9 are black's side)
    # Black across river: fr <= 4 (black rows 0-4 are red's side)
    crossed = (color == +1 and fr >= 5) or (color == -1 and fr <= 4)
    if crossed:
        for dc in (-1, +1):
            nc_s = fc + dc
            if 0 <= nc_s < COLS:
                target = int(board[fr, nc_s])
                if not belongs_to(target, color):
                    moves.append(encode_move(from_sq, rc_to_sq(fr, nc_s), is_capture=target != 0))
    return moves
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|-----------------|-------------|--------|
| Bitboard attack maps | Direction scanning with numpy | Phase 1 decision | 10x9 board is too small for bitboard advantage; direction scanning is simpler and testable |
| Inline king safety in each generator | Board-copy post-filter | 02-CONTEXT.md locked | Generators are pure geometry, independently testable |
| Western-chess knight L-table | Leg-destination pairs with blocking check | PITFALLS.md Pitfall 3 | Correct horse leg blocking rule |
| Single sliding function for cannon | Two-phase screen-count scan | PITFALLS.md Pitfall 6 | Correct cannon capture vs slide distinction |
| Stalemate = draw | Stalemate = loss | PITFALLS.md Pitfall 7 | Correct Xiangqi rule, no RL reward corruption |

**Perft reference values (Fairy-Stockfish / Chess Programming Wiki verified):**

| Depth | Nodes | Checks | Captures |
|-------|-------|--------|---------|
| 1 | 44 | 0 | 2 |
| 2 | 1,920 | 6 | 72 |
| 3 | 79,666 | 384 | 3,159 |
| 4 | 3,290,240 | 19,380 | 115,365 |

**WARNING: REQUIREMENTS.md TEST-01 contains incorrect perft numbers:**
- TEST-01 claims depth 2 = 1,916 and depth 3 = 72,987
- CPW-verified Fairy-Stockfish values are depth 2 = **1,920** and depth 3 = **79,666**
- Depth 1 (44) matches both sources
- The planner MUST use CPW values as the reference for test assertions; update TEST-01 requirement or flag the discrepancy for the user to correct

---

## Open Questions

1. **Perft discrepancy in REQUIREMENTS.md**
   - What we know: CPW and multiple WebSearch sources agree on 1,920 (depth 2) and 79,666 (depth 3)
   - What's unclear: Why REQUIREMENTS.md has 1,916 and 72,987 (off by 4 and 6,679)
   - Recommendation: Use CPW values (1,920 and 79,666) for test assertions; file an issue to correct TEST-01 in REQUIREMENTS.md

2. **Soldier sideways row threshold**
   - What we know: Red soldiers cross at river (rows 4-5), black soldiers cross at river
   - What's unclear: Is red "across river" when `row >= 5` or `row > 4`? Both are equivalent in Python
   - Recommendation: Use `fr >= 5` for red sideways, `fr <= 4` for black sideways (confirmed by RULES.md §9.5)

3. **Elephant eye check on pre-capture board**
   - What we know: Elephant eye check uses the board state before the move is applied
   - What's unclear: Is there any scenario where the destination piece being captured is itself the eye blocker?
   - Recommendation: Always check eye on pre-move board (confirmed by RULES.md §9.1); for `is_legal_move`, the copy is already made before checking

4. **Face-to-face as a source of check (not just legality filter)**
   - What we know: If generals face each other, each is giving check to the other
   - What's unclear: Should `is_in_check()` return True for the side NOT moving when they face each other?
   - Recommendation: Yes — `is_in_check()` must detect face-to-face as a check source (RULES.md §9.15)

---

## Validation Architecture

> Included per `workflow.nyquist_validation: true` in `.planning/config.json`.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >= 8.0 |
| Config file | `pyproject.toml` (existing from Phase 1) |
| Quick run command | `python -m pytest tests/test_moves.py tests/test_legal.py -v --tb=short` |
| Full suite command | `python -m pytest tests/ -v --tb=short` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| MOVE-01 | gen_general returns correct count from minimal FEN | unit | `pytest tests/test_moves.py::test_gen_general -x` | tests/test_moves.py (Wave 0) |
| MOVE-02 | gen_chariot slides and captures correctly | unit | `pytest tests/test_moves.py::test_gen_chariot -x` | tests/test_moves.py (Wave 0) |
| MOVE-03 | gen_horse blocked/unblocked counts | unit | `pytest tests/test_moves.py::test_gen_horse -x` | tests/test_moves.py (Wave 0) |
| MOVE-04 | gen_cannon slide vs capture (screen counting) | unit | `pytest tests/test_moves.py::test_gen_cannon -x` | tests/test_moves.py (Wave 0) |
| MOVE-05 | gen_advisor palace-constrained | unit | `pytest tests/test_moves.py::test_gen_advisor -x` | tests/test_moves.py (Wave 0) |
| MOVE-06 | gen_elephant eye-block and river constraint | unit | `pytest tests/test_moves.py::test_gen_elephant -x` | tests/test_moves.py (Wave 0) |
| MOVE-07 | gen_soldier pre/post-river movement | unit | `pytest tests/test_moves.py::test_gen_soldier -x` | tests/test_moves.py (Wave 0) |
| RULE-01 | is_legal_move rejects self-check moves | unit | `pytest tests/test_legal.py::test_is_legal_move -x` | tests/test_legal.py (Wave 0) |
| RULE-02 | generate_legal_moves returns correct count from starting position | unit | `pytest tests/test_legal.py::test_generate_legal_moves_starting -x` | tests/test_legal.py (Wave 0) |
| RULE-03 | is_in_check detects known checking pieces | unit | `pytest tests/test_legal.py::test_is_in_check -x` | tests/test_legal.py (Wave 0) |
| RULE-05 | face-to-face rule blocks column moves when generals face | unit | `pytest tests/test_rules.py::test_face_to_face_rule -x` | tests/test_rules.py (Wave 0) |
| RULE-06 | get_game_result correct for checkmate, stalemate | unit | `pytest tests/test_rules.py::test_get_game_result -x` | tests/test_rules.py (Wave 0) |
| TEST-01 | perft(1)=44, perft(2)=1,920, perft(3)=79,666 | perft | `pytest tests/test_perft.py -x` | tests/test_perft.py (Wave 0) |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_moves.py tests/test_legal.py -v --tb=short`
- **Per wave merge:** `python -m pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_moves.py` -- covers MOVE-01..MOVE-07 (7 per-piece generator tests)
- [ ] `tests/test_legal.py` -- covers RULE-01, RULE-02, RULE-03 (is_legal, generate_legal, is_in_check)
- [ ] `tests/test_rules.py` -- covers RULE-05 (face-to-face), RULE-06 (get_game_result)
- [ ] `tests/test_perft.py` -- covers TEST-01 (perft 1-3 cross-validation against CPW values)
- [ ] `tests/conftest.py` -- extend with Phase 2 fixtures: `fen_state(fen)`, `blocked_horse_board`, `face_to_face_board`
- [ ] `src/xiangqi/engine/moves.py` -- all 7 gen_* functions
- [ ] `src/xiangqi/engine/legal.py` -- is_in_check, is_legal_move, generate_legal_moves, apply_move
- [ ] `src/xiangqi/engine/rules.py` -- face-to-face rule, flying_general_violation

*(All Wave 0 files are new -- no existing test infrastructure for move generation)*

---

## Sources

### Primary (HIGH confidence)
- `.planning/research/RULES.md` -- Full Xiangqi rule specification including move offsets, check detection algorithm, face-to-face rule, elephant/river constraint, soldier forward-only movement
- `.planning/research/PITFALLS.md` -- Verified Xiangqi-specific pitfalls: horse leg blocking, cannon capture vs slide, elephant eye+river, face-to-face, stalemate-as-loss
- `.planning/research/DATA_STRUCTURES.md` -- Engine implementation patterns including per-piece generator code, is_in_check algorithm, Zobrist-based state, apply/undo pattern
- Chess Programming Wiki: Chinese Chess Perft Results (https://www.chessprogramming.org/Chinese_Chess_Perft_Results) -- Verified perft reference values for starting position at depths 1-4 (44, 1,920, 79,666, 3,290,240)
- Fairy-Stockfish perft.sh CI test (https://github.com/ianfab/Fairy-Stockfish) -- Confirms depth 4 = 3,290,240

### Secondary (MEDIUM confidence)
- WebSearch 2026-03-19: "Xiangqi Chinese chess perft numbers starting position depth 1 2 3 4" -- Confirms CPW values; notes Fairy-Stockfish verification

### Tertiary (LOW confidence)
- WebSearch: Fairy-Stockfish perft divide results -- divide output at depth 5 useful for bug isolation but not primary reference

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- pure Python + NumPy, no new dependencies, Phase 1 confirmed this stack works
- Architecture: HIGH -- generator + post-filter pattern is standard in Western chess engines; confirmed by DATA_STRUCTURES.md implementation code
- Pitfalls: HIGH -- all 6 critical Xiangqi pitfalls documented with precise prevention in PITFALLS.md
- Perft values: MEDIUM -- CPW/Fairy-Stockfish community values verified by multiple sources (depth 1, 4) but depth 2, 3 show discrepancy with REQUIREMENTS.md TEST-01

**Research date:** 2026-03-19
**Valid until:** 90 days (Xiangqi rules are stable; perft values are engine-independent)

**Flag for planner:**
- TEST-01 perft numbers in REQUIREMENTS.md (1,916, 72,987) differ from CPW reference (1,920, 79,666). Use CPW values in tests. The discrepancy is 4 and 6,679 nodes respectively, which is within the range of different engine implementations having slightly different move categorizations. CPW + Fairy-Stockfish CI confirmation is the more authoritative source.
