# Phase 3: Endgame Detection - Research

**Researched:** 2026-03-20
**Domain:** Terminal game-state detection for Xiangqi (checkmate, stalemate, perpetual check/chase, repetition draw)
**Confidence:** HIGH (source-aligned with existing code, RULES.md, and CONTEXT.md decisions)

---

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Two files only**: `endgame.py` (checkmate/stalemate + main `get_game_result()`) and `repetition.py` (repetition + perpetual tracking)
- **END-04**: any 3 occurrences of a hash anywhere in history (not consecutive) → draw
- **END-03 long check**: 4 consecutive moves where opponent is in check → draw (not loss)
- **END-03 long chase**: same `(attacking_sq, target_sq)` x4 consecutive by same color → chaser loses
- **END-01/END-02**: checkmate + stalemate behavior unchanged from current `get_game_result()`
- **Priority order**: repetition → long check → long chase → checkmate → stalemate → IN_PROGRESS
- **Module-level tracking state** in `repetition.py` (chase_seq, consecutive_check_count, last_chasing_color), passed as arguments to `get_game_result()`
- **END-05**: SKIP (optional)

### Claude's Discretion
- Exact threshold for "meaningful progress" (capture/check/new square)
- Internal organization of check/chase detection functions
- Whether to inline perpetual detection in `get_game_result()` or call a helper
- How `chase_seq` resets when opponent makes a non-chase move (decision: sequence is per-side, per-target)

### Deferred Ideas
- END-05 60-move rule
- Perpetual siege (长围)

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| END-01 | Checkmate: no legal moves + in check → opponent wins | Algorithm in §END-01, test fixtures in §Test Fixtures |
| END-02 | Stalemate (困毙): no legal moves + not in check → opponent wins | Same code path, same test fixtures |
| END-03 | Long check: 4 consecutive checking moves → draw | Algorithm in §END-03-long-check, state in §RepetitionState |
| END-03 | Long chase: same (attacker, target) x4 → chaser loses | Algorithm in §END-03-long-chase, chase_seq tracking |
| END-04 | Repetition: any hash appears 3x → draw | Simple `history.count(h) >= 3` on existing `zobrist_hash_history` |
| END-05 | 60-move rule | SKIPPED |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | >=2.0,<3.0 | board storage | Phase 1 foundation |
| pytest | >=8.0 | test framework | Phase 1 foundation |

No new third-party libraries are required. All detection is implemented in pure Python on top of existing Phase 1/2 infrastructure.

---

## Architecture Decisions

### Module Layout (CONTEXT Override of ROADMAP)

**ROADMAP.md** lists 3 files (endgame.py + repetition.py + perpetual.py).
**CONTEXT.md** overrides with 2 files. The two-file layout is the constraint to honor.

```
src/xiangqi/engine/
├── endgame.py        # get_game_result(), checkmate/stalemate helpers
├── repetition.py     # RepetitionState, repetition detection, perpetual tracking
├── legal.py          # existing: is_in_check, generate_legal_moves, apply_move
├── rules.py          # existing: keep for Phase 4; get_game_result MOVED to endgame.py
├── state.py          # existing: XiangqiState, compute_hash, update_hash
├── moves.py          # existing: gen_* piece generators
├── types.py          # existing: Piece enum, encode/decode_move
└── constants.py      # existing: IN_PALACE, STARTING_FEN
```

**Critical note on existing duplication:** Both `legal.py` and `rules.py` define `is_in_check()` and `flying_general_violation()`. `rules.py`'s `get_game_result()` imports `generate_legal_moves` and `is_in_check` from `legal.py`. After the refactor:
- `endgame.py` imports from `legal.py` (not `rules.py`)
- `rules.py` becomes a thin re-export shim for Phase 4 backwards compat (or is absorbed into `legal.py`)
- Phase 4 `engine.py` imports from `endgame.py` and `legal.py`

### RepetitionState Design

CONTEXT says: tracking state lives in `repetition.py` as module-level state, passed as arguments.

**Recommended design:** `RepetitionState` dataclass (not module-level globals — see §Why Not Module Globals).

```python
# src/xiangqi/engine/repetition.py
from dataclasses import dataclass, field

@dataclass
class RepetitionState:
    """Mutable tracker for perpetual-rule state across a game."""
    consecutive_check_count: int = 0       # consecutive checking moves
    chase_seq: list[tuple[int, int]] = field(default_factory=list)  # [(att_sq, tgt_sq), ...]
    last_chasing_color: int = 0            # +1 red, -1 black, 0 = none

    def reset_check(self) -> None: ...
    def reset_chase(self) -> None: ...
    def update(self, prev_state: XiangqiState, move: int, new_state: XiangqiState) -> None: ...
```

**Why a dataclass and not module-level globals:**
1. **Test isolation**: pytest runs tests in the same process; module-level globals persist across test cases unless explicitly reset, causing cross-test contamination.
2. **Thread safety**: N/A for v0.1, but good practice.
3. **Undo friendliness**: Phase 4 `engine.py` will need `undo_move()` — a `RepetitionState` object is easy to `.copy()` and restore.

**Initialization:** `RepetitionState()` (zero-initialized) at game start.

### State Persistence for Perpetual Tracking

**Option A (chosen):** `RepetitionState` lives in `engine.py` (Phase 4), not in `XiangqiState`.
- `apply_move()` does NOT update `RepetitionState` (it only updates `XiangqiState` fields).
- After each `apply_move()`, Phase 4 `engine.py` calls `rep_state.update(prev_state, move, new_state)`.
- `get_game_result(state, rep_state)` reads from `rep_state`.

**Option B:** `RepetitionState` fields embedded in `XiangqiState`.
- Rejected: XiangqiState tracks game tree state (board, history); perpetual tracking is an engine-level concern, not a game-state concern. Mixing concerns makes `copy()` and `undo` more complex.

**Key insight:** `apply_move()` in `legal.py` already appends to `zobrist_hash_history`. Perpetual tracking uses `is_in_check()` on the post-move state (available after `apply_move`). The update flow for Phase 4 engine:

```python
# Phase 4 engine pseudo-code
rep_state = RepetitionState()
while not (result := get_game_result(state, rep_state)).ends:
    move = select_move(state)
    snap = state.copy()
    apply_move(state, move)
    rep_state.update(snap, move, state)  # updates counters based on prev→new transition
    history.push(snap)
```

### Import Chain (no circular deps)

```
repetition.py   — no imports from endgame.py
endgame.py      — imports from legal.py (is_in_check, generate_legal_moves)
                  — imports from repetition.py (RepetitionState, check_* functions)
legal.py        — no imports from endgame.py or repetition.py
rules.py        — re-exports get_game_result from endgame.py (Phase 4 compat)
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Position equality | Custom board-comparison loops | Zobrist hash comparison | O(90) scan per comparison; hash is O(1) |
| Attack-set for chase | Reimplement piece attack logic | `is_in_check`-style scan reusing existing `moves.py` gen_* | Same piece-move computation; avoids duplicating blocking/ray logic |
| Perpetual state | Multiple independent int/counter variables | `RepetitionState` dataclass | Single object to copy/restore on undo, clear reset semantics |

---

## Common Pitfalls

### Pitfall 1: Priority Order Inversion
**What goes wrong:** `get_game_result()` checks checkmate/stalemate before checking perpetuals, so a perpetual-draw position is incorrectly reported as `IN_PROGRESS`.
**How to avoid:** Enforce the CONTEXT priority order literally in the function body. The checkmate/stalemate path must be reached only if repetition, long-check, and long-chase all return `None`.
**Code structure:**
```python
def get_game_result(state, rep_state=None) -> str:
    if (d := check_repetition(state, rep_state)) is not None: return d
    if (d := check_long_check(state, rep_state)) is not None: return d
    if (d := check_long_chase(state, rep_state)) is not None: return d
    # Only now check terminal positions
    legal = generate_legal_moves(state)
    if len(legal) == 0:
        return 'BLACK_WINS' if state.turn == +1 else 'RED_WINS'
    return 'IN_PROGRESS'
```

### Pitfall 2: Testing with Stale Perpetual State
**What goes wrong:** A test for long-check sets up a specific position but `rep_state.consecutive_check_count` is non-zero from a previous test (module global), causing the test to pass for the wrong reason or fail inconsistently.
**How to avoid:** Each test that uses perpetual state must construct its own `RepetitionState()` and pass it explicitly. Never rely on implicit reset.
**Code:**
```python
def test_long_check_draw():
    rep_state = RepetitionState()  # fresh, zero-initialized
    state = make_long_check_state()  # sets up position mid-chase
    result = get_game_result(state, rep_state)
    assert result == 'DRAW'
```

### Pitfall 3: Confusing "in check" with "giving check"
**What goes wrong:** `consecutive_check_count` increments on the position where the CURRENT player is in check. But "long check" means the checking side (opponent) has been giving check for 4 consecutive moves.
**Root cause:** The check is detected AFTER `apply_move()`, when the board state has already flipped turns.
**Correct logic:**
```python
# After apply_move(), state.turn is the NEXT player to move
# If opponent (state.turn * -1) is in check → the move just played gave check
opponent = state.turn * -1  # who just moved
if is_in_check(state, opponent):
    rep_state.consecutive_check_count += 1
else:
    rep_state.consecutive_check_count = 0
```
**Warning sign:** Counter incrementing on the wrong player's moves, or off-by-one on the 4-move threshold.

### Pitfall 4: Chase Definition Too Broad
**What goes wrong:** Every move that attacks any enemy piece counts as a chase, even if the piece being attacked can easily escape or the attack is incidental.
**What to do instead:** The WXO definition requires attacking the SAME enemy piece (same square) repeatedly. The `(attacking_sq, target_sq)` pair must match. A move that attacks a different enemy piece breaks the chase sequence.
**Algorithm:** See §END-03-long-chase.

### Pitfall 5: Rules.py vs Legal.py Confusion After Refactor
**What goes wrong:** After moving `get_game_result()` to `endgame.py`, existing imports in `test_rules.py` break.
**How to avoid:** Keep `rules.py` as a re-export shim after the move:
```python
# rules.py — after Phase 3
from .endgame import get_game_result
__all__ = ['get_game_result']
```
Then update `test_rules.py` imports in the same commit. Test fixtures (`make_state` helper) stay in `test_rules.py`.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_endgame.py tests/test_repetition.py -x` |
| Full suite command | `pytest tests/ -q` |
| Existing test infra | `tests/conftest.py` (`starting_state` fixture), `make_state` helper in `test_rules.py`, `test_legal.py` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| END-01 | Checkmate: 0 legal moves + in check → BLACK_WINS | unit | `pytest tests/test_endgame.py::TestCheckmate -x` | NEW |
| END-02 | Stalemate: 0 legal moves + not in check → opponent wins | unit | `pytest tests/test_endgame.py::TestStalemate -x` | NEW |
| END-03 | Long check: 4 consecutive checking moves → DRAW | unit | `pytest tests/test_repetition.py::TestLongCheck -x` | NEW |
| END-03 | Long chase: same (att, tgt) x4 → chaser loses | unit | `pytest tests/test_repetition.py::TestLongChase -x` | NEW |
| END-04 | Repetition: hash appears 3x → DRAW | unit | `pytest tests/test_repetition.py::TestRepetition -x` | NEW |

### Sampling Rate
- **Per task commit:** `pytest tests/test_endgame.py tests/test_repetition.py -x`
- **Per wave merge:** `pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_endgame.py` — covers END-01, END-02, moved from `test_rules.py::TestGetGameResult`
- [ ] `tests/test_repetition.py` — covers END-03, END-04
- [ ] `tests/conftest.py` — add `make_state` fixture (shared across endgame tests)
- [ ] `tests/test_rules.py` — remove `TestGetGameResult` class (moved to `test_endgame.py`); remove `get_game_result` import; add re-export shim in `rules.py`

---

## Detection Algorithms

### END-01/END-02: Checkmate and Stalemate

**Input:** `XiangqiState`, `RepetitionState` (not used for check/stalemate)

**Output:** `'BLACK_WINS'` or `'RED_WINS'` (called only when `len(legal_moves) == 0`)

**Algorithm:**
```python
def checkmate_or_stalemate(state: XiangqiState) -> str:
    # Called only when generate_legal_moves(state) == []
    in_check = is_in_check(state, state.turn)
    if in_check:
        # Checkmate: current player loses
        return 'BLACK_WINS' if state.turn == +1 else 'RED_WINS'
    else:
        # Stalemate (困毙): current player loses in Xiangqi
        return 'BLACK_WINS' if state.turn == +1 else 'RED_WINS'
```
Note: both branches return the same value (opponent wins). The `in_check` distinction matters only for code clarity and future extension (e.g., if some rules variants differ). The return is `'BLACK_WINS'` if red to move, `'RED_WINS'` if black to move.

**Boundary conditions:**
- `generate_legal_moves()` must be called with the CURRENT `state.turn` (correct player)
- If `king_positions` is missing a key (king captured), `is_in_check()` returns `False`; `generate_legal_moves()` will return `[]` (no general → no legal moves); `get_game_result()` should return `'BLACK_WINS'` if black general is missing (red captured it) or `'RED_WINS'` if red general is missing. This is implicitly handled by the same check/stalemate logic: if red has no general, black to move (implied by board state) and `is_in_check(black)` = `False`; the `BLACK_WINS` branch fires.
- **Edge case:** Both generals missing → the game should already be over from the capture. `apply_move()` does not enforce immediate win; the `get_game_result()` check catches this on the next call.

---

### END-04: Repetition Draw

**Input:** `XiangqiState.zobrist_hash_history` (list of `int`, length = plies + 1)

**Output:** `'DRAW'` if any hash appears >= 3 times; `None` otherwise

**Algorithm:**
```python
def check_repetition(state: XiangqiState) -> str | None:
    history = state.zobrist_hash_history
    # Count occurrences of each hash; any >= 3 triggers draw
    seen: dict[int, int] = {}
    for h in history:
        seen[h] = seen.get(h, 0) + 1
        if seen[h] >= 3:
            return 'DRAW'
    return None
```

**Why `seen[h] >= 3` and not `seen[h] > 2`:** Equivalent, but `>= 3` is more explicit against the spec "appears 3 times."

**Why count from scratch each call:** `hash_history` is a Python list (max ~500 entries for a typical game); O(n) scan per `get_game_result()` call is negligible. No need to maintain a running counter unless profiling shows it matters (premature optimization warning: do not pre-compute until measured).

**Boundary conditions:**
- `hash_history` may have length 1 (initial position). No repetition possible.
- The hash includes side-to-move (from `update_hash` XORing the turn bit). Two identical board states with different sides to move produce different hashes. This is correct per RULES.md §10.5.
- **OPEN (minor):** Should `get_game_result()` check repetition BEFORE checking long check/chase, or after? CONTEXT specifies the priority order starts with repetition. This is implemented as written.

---

### END-03: Long Check (长将)

**Input:** `XiangqiState` (post-move), `RepetitionState`

**Output:** `'DRAW'` if 4+ consecutive checking moves; `None` otherwise

**Algorithm:**
```python
def update_check_count(prev_state: XiangqiState, move: int, new_state: XiangqiState,
                       rep_state: RepetitionState) -> None:
    """Update consecutive_check_count after a move is applied."""
    # The player who just moved is the OPPOSITE of new_state.turn
    mover = new_state.turn * -1
    if is_in_check(new_state, mover):
        rep_state.consecutive_check_count += 1
    else:
        rep_state.consecutive_check_count = 0


def check_long_check(state: XiangqiState, rep_state: RepetitionState) -> str | None:
    if rep_state.consecutive_check_count >= 4:
        # Both sides not in check (we are in a position after 4+ consecutive checks)
        # Standard WXO rule: draw
        return 'DRAW'
    return None
```

**State update timing:** `rep_state.consecutive_check_count` is incremented BEFORE `get_game_result()` is called for the new position. The count of "consecutive checking positions" equals the count of consecutive moves that gave check. At position N (after 4 checking moves), `consecutive_check_count == 4`.

**Why `>= 4`:** A "continuous check for 4+ moves" means the 4th checking move triggers the draw condition. Position after move 4: `count == 4` → draw.

**Reset logic:** Any move that does NOT give check resets the counter to 0. This includes non-checking legal moves, checkmates (caught earlier in priority), and stalemates.

**Boundary conditions:**
- The opponent must NOT be in check at the draw position (per WXO Rule 22.2: if the checking side has no non-checking move, position is draw). Our `check_long_check()` is called before the check/stalemate branch, so if the position is also checkmate, repetition/check_long_check takes priority per CONTEXT priority order.
- **OPEN (minor):** If both long check AND long chase conditions are simultaneously true (extremely rare), which takes priority? CONTEXT priority order says long check checked before long chase. Both return `'DRAW'` for long check, `'RED_WINS'/'BLACK_WINS'` for long chase. If both trigger, long check wins (draw) per priority.

---

### END-03: Long Chase (长捉)

**Input:** `XiangqiState` (pre and post-move), `RepetitionState`, the move that was just applied

**Output:** `'RED_WINS'` or `'BLACK_WINS'` (chaser loses) or `None`

**Algorithm — Chase Detection (`is_chase`):**
```python
def _attacked_squares_by_piece(board: np.ndarray, from_sq: int,
                                color: int) -> list[int]:
    """Return list of square indices that the piece at from_sq attacks.

    Reuses gen_* from moves.py, but for a specific piece (not all pieces).
    This gives the attack set without the self-check filter.
    """
    from .moves import gen_chariot, gen_cannon, gen_general, gen_soldier
    from .types import sq_to_rc, rc_to_sq, Piece
    fr, fc = sq_to_rc(from_sq)
    piece = int(board[fr, fc])
    pt = abs(piece)
    attacks: list[int] = []
    if pt == 1:
        attacks = gen_general(board, from_sq, color)
    elif pt == 5:
        attacks = gen_chariot(board, from_sq, color)
    elif pt == 6:
        attacks = gen_cannon(board, from_sq, color)
    elif pt == 7:
        attacks = gen_soldier(board, from_sq, color)
    # gen_* return full moves; extract to_sq
    to_sqs = [m & 0x1FF for m in attacks]
    return to_sqs


def is_chase(prev_state: XiangqiState, move: int) -> tuple[int, int] | None:
    """Return (attacking_sq, target_sq) if this move is a chase, else None.

    A chase = the moving piece attacks a non-king enemy piece.
    The target must be an enemy piece that is NOT the opponent's general.
    """
    from_sq, to_sq, _ = (move & 0x1FF), ((move >> 9) & 0x7F), ((move >> 16) & 0x1)
    mover_color = prev_state.turn  # color BEFORE the move

    # Get attack set of the moving piece on the POST-move board
    post_board = prev_state.board.copy()
    # Simulate the move on a temp board (already applied in prev_state.copy())
    fr, fc = divmod(from_sq, 9)
    tr, tc = divmod(to_sq, 9)
    moving_piece = int(post_board[fr, fc])
    post_board[tr, tc] = moving_piece
    post_board[fr, fc] = np.int8(0)

    attacked = _attacked_squares_by_piece(post_board, to_sq, mover_color)

    # Find enemy non-king pieces among attacked squares
    for sq in attacked:
        r, c = divmod(sq, 9)
        p = int(post_board[r, c])
        if p == 0:
            continue
        enemy = -mover_color
        if (p > 0) != (enemy > 0):  # p belongs to enemy
            if abs(p) != 1:  # not the general
                return (to_sq, sq)
    return None
```

**Algorithm — Chase Sequence Update:**
```python
def update_chase_seq(prev_state: XiangqiState, move: int,
                     new_state: XiangqiState,
                     rep_state: RepetitionState) -> None:
    """Update chase_seq after a move. Returns None (updates rep_state in place)."""
    mover_color = prev_state.turn  # who just moved

    chase = is_chase(prev_state, move)

    if chase is None:
        # Non-chase move: reset sequence if opponent just moved
        # (the opponent interrupted the sequence)
        rep_state.chase_seq = []
        rep_state.last_chasing_color = 0
        return

    att_sq, tgt_sq = chase

    # Meaningful progress: gives check, captures, or moves to a new square
    opponent = -mover_color
    gives_check = is_in_check(new_state, opponent)
    captured = len(new_state.move_history) > len(prev_state.move_history)
    # Check if to_sq is new in the chase sequence
    chase_squares = {sq for _, sq in rep_state.chase_seq}
    is_new_square = att_sq not in chase_squares

    meaningful = gives_check or captured or is_new_square

    if not meaningful:
        # Same (attacker, target) repeated → extend sequence
        rep_state.chase_seq.append((att_sq, tgt_sq))
    else:
        # Meaningful progress breaks the sequence
        rep_state.chase_seq = [(att_sq, tgt_sq)]  # start new sequence

    rep_state.last_chasing_color = mover_color


def check_long_chase(state: XiangqiState, rep_state: RepetitionState) -> str | None:
    if len(rep_state.chase_seq) >= 4 and rep_state.last_chasing_color != 0:
        # Same (att, tgt) x4 consecutive → chaser loses
        chaser = rep_state.last_chasing_color
        return 'RED_WINS' if chaser == -1 else 'BLACK_WINS'
    return None
```

**Why "is_new_square" checks `att_sq` not `tgt_sq`:** The chasing piece moves to `att_sq` (which is `to_sq` of the move). If the chasing piece has never moved to `att_sq` before in the current chase sequence, that's meaningful progress.

**"Meaningful progress" breaks the chase** (CONTEXT §Specific Ideas):
1. Giving check (`is_in_check(new_state, opponent)`) → reset sequence with new (att, tgt) pair
2. Capturing a piece → reset sequence
3. Moving to a square never visited in the current chase sequence → reset sequence (new pair)

**Reset on opponent non-chase:** If the opponent makes a non-chase move, `rep_state.chase_seq = []`. When the original chasing side resumes chasing, it starts from count 0. This is per CONTEXT §Claude's Discretion decision.

**Boundary conditions:**
- **OPEN:** What if both sides are chasing each other's pieces simultaneously? This is a rare edge case. The sequence tracks `last_chasing_color`, so when red chases and then black chases, red's sequence resets (opponent non-chase). Black's sequence starts fresh. This may not trigger long-chase for either side. Per WXO rules, this could be perpetual siege (长围) — deferred as out of scope.
- Chase targets must be non-king pieces. The king is handled by the long-check rule, not the long-chase rule.
- Pawn-only perpetual: if a soldier keeps attacking the same enemy soldier from the same square (edge case in xiangqi), this is correctly detected as a chase.

---

## Code Examples

### get_game_result — Full Skeleton (endgame.py)

```python
"""Endgame detection: checkmate, stalemate, draw conditions."""
from __future__ import annotations

from .types import ROWS, COLS
from .state import XiangqiState
from .repetition import RepetitionState, check_repetition, check_long_check, check_long_chase
from .legal import generate_legal_moves, is_in_check


def get_game_result(state: XiangqiState,
                    rep_state: RepetitionState | None = None) -> str:
    """Return game result: 'RED_WINS', 'BLACK_WINS', 'DRAW', or 'IN_PROGRESS'.

    Priority order (per CONTEXT.md):
    1. Threefold repetition → DRAW
    2. Long check (4+ consecutive) → DRAW
    3. Long chase (4+ consecutive same target) → chaser loses
    4. No legal moves + in check → checkmate → opponent wins
    5. No legal moves + not in check → stalemate (困毙) → opponent wins
    6. Otherwise → IN_PROGRESS
    """
    if rep_state is None:
        rep_state = RepetitionState()

    # Perpetual conditions
    if (d := check_repetition(state)) is not None:
        return d
    if (d := check_long_check(state, rep_state)) is not None:
        return d
    if (d := check_long_chase(state, rep_state)) is not None:
        return d

    # Terminal positions
    legal = generate_legal_moves(state)
    if len(legal) == 0:
        in_check = is_in_check(state, state.turn)
        # In Xiangqi: both checkmate and stalemate are losses for the player to move
        return 'BLACK_WINS' if state.turn == +1 else 'RED_WINS'

    return 'IN_PROGRESS'
```

### RepetitionState and update (repetition.py)

```python
"""Repetition detection, perpetual check/chase tracking."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np

from .types import ROWS, COLS, sq_to_rc, rc_to_sq
from .state import XiangqiState
from .legal import is_in_check, generate_legal_moves
from .moves import gen_chariot, gen_cannon, gen_general, gen_soldier


@dataclass
class RepetitionState:
    """Tracks state needed for perpetual-rule detection across a game."""
    consecutive_check_count: int = 0
    chase_seq: List[tuple[int, int]] = field(default_factory=list)
    last_chasing_color: int = 0  # +1 red, -1 black, 0 = none

    def update(self, prev_state: XiangqiState, move: int,
               new_state: XiangqiState) -> None:
        """Update counters after a move is applied.

        Call this AFTER apply_move() has flipped turn and updated hash.
        prev_state: board BEFORE the move (turn = mover's color)
        new_state: board AFTER the move (turn = opponent's color)
        """
        mover = new_state.turn * -1  # who just moved

        # ── Long check tracking ──────────────────────────────────
        if is_in_check(new_state, mover):
            self.consecutive_check_count += 1
        else:
            self.consecutive_check_count = 0

        # ── Long chase tracking ───────────────────────────────────
        chase = _detect_chase(prev_state, move, new_state, mover)
        if chase is None:
            self.chase_seq = []
            self.last_chasing_color = 0
        else:
            att_sq, tgt_sq = chase
            opponent = -mover
            gives_check = is_in_check(new_state, opponent)
            captured = (len(new_state.move_history) > len(prev_state.move_history) and
                        tgt_sq in [(m >> 9) & 0x7F for m in new_state.move_history[-1:]])
            chase_sq = {sq for _, sq in self.chase_seq}
            is_new = att_sq not in chase_sq
            if gives_check or captured or is_new:
                self.chase_seq = [(att_sq, tgt_sq)]
            else:
                self.chase_seq.append((att_sq, tgt_sq))
            self.last_chasing_color = mover

    def reset(self) -> None:
        """Reset all counters (for game restart)."""
        self.consecutive_check_count = 0
        self.chase_seq = []
        self.last_chasing_color = 0


# ─── Public check functions ────────────────────────────────────────────────

def check_repetition(state: XiangqiState) -> str | None:
    """Return 'DRAW' if any position appears 3+ times, else None."""
    seen: dict[int, int] = {}
    for h in state.zobrist_hash_history:
        seen[h] = seen.get(h, 0) + 1
        if seen[h] >= 3:
            return 'DRAW'
    return None


def check_long_check(state: XiangqiState,
                     rep_state: RepetitionState) -> str | None:
    """Return 'DRAW' if 4+ consecutive checking moves, else None."""
    if rep_state.consecutive_check_count >= 4:
        return 'DRAW'
    return None


def check_long_chase(state: XiangqiState,
                     rep_state: RepetitionState) -> str | None:
    """Return winner if chaser loses after 4+ consecutive chases, else None."""
    if len(rep_state.chase_seq) >= 4 and rep_state.last_chasing_color != 0:
        chaser = rep_state.last_chasing_color
        return 'RED_WINS' if chaser == -1 else 'BLACK_WINS'
    return None


# ─── Internal helpers ───────────────────────────────────────────────────────

def _detect_chase(prev_state: XiangqiState, move: int,
                  new_state: XiangqiState, mover: int) -> tuple[int, int] | None:
    """Return (attacking_sq, target_sq) if this move is a chase, else None.

    A chase = the moving piece attacks a non-king enemy piece.
    """
    from_sq = move & 0x1FF
    to_sq = (move >> 9) & 0x7F

    # Compute attack set of the piece at to_sq on the post-move board
    # Use prev_state board (pre-move) + simulate the move
    board = prev_state.board.copy()
    fr, fc = divmod(from_sq, 9)
    tr, tc = divmod(to_sq, 9)
    piece = int(board[fr, fc])
    board[tr, tc] = piece
    board[fr, fc] = np.int8(0)

    pt = abs(piece)
    if pt == 1:
        moves = gen_general(board, to_sq, mover)
    elif pt == 5:
        moves = gen_chariot(board, to_sq, mover)
    elif pt == 6:
        moves = gen_cannon(board, to_sq, mover)
    elif pt == 7:
        moves = gen_soldier(board, to_sq, mover)
    else:
        return None  # only general, chariot, cannon, soldier can chase

    attacked_sqs = {(m >> 9) & 0x7F for m in moves}

    for sq in attacked_sqs:
        r, c = divmod(sq, 9)
        p = int(board[r, c])
        if p == 0:
            continue
        enemy = -mover
        if (p > 0) != (enemy > 0) and abs(p) != 1:
            return (to_sq, sq)
    return None
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `get_game_result` in rules.py | `get_game_result` in endgame.py | Phase 3 | Clean separation of concerns; engine.py imports from dedicated module |
| No perpetual tracking | `RepetitionState` in repetition.py | Phase 3 | Enables END-03/END-04 detection with clean undo support |
| Simple check/stalemate only | Priority-ordered: repetition → long check → long chase → terminal | Phase 3 | Correct WXO rule ordering |

**Deprecated/outdated:**
- `rules.py` as location for `get_game_result` — replaced by `endgame.py`
- Module-level global variables for perpetual tracking — replaced by `RepetitionState` dataclass

---

## Open Questions

### OPEN-1: Rules.py absorption or stub?
**What's unclear:** After moving `get_game_result` to `endgame.py`, what happens to `rules.py`?
**What we know:** Phase 4 `engine.py` will import from engine modules. If `rules.py` disappears entirely, imports from Phase 2 test files (`test_rules.py`, `test_legal.py`) that import from `rules.py` break.
**Recommendation:** Make `rules.py` a thin re-export shim:
```python
from .endgame import get_game_result
from .legal import flying_general_violation, is_in_check
__all__ = ['flying_general_violation', 'get_game_result', 'is_in_check']
```
This preserves Phase 2 test compatibility while routing the real logic to the right module. Resolve in Phase 3 plan.

### OPEN-2: `is_chase` attack-set computation
**What's unclear:** The `_detect_chase` function needs to compute the attack set of a specific piece. Is it correct to reuse the gen_* generators from `moves.py` without the self-check filter?
**What we know:** `gen_chariot`, `gen_cannon`, `gen_general`, `gen_soldier` are pseudo-legal (no self-check filter). They return all destinations that a piece CAN reach given board topology. A chase attack is simply: does the piece attack square X? These generators give all destination squares, so the intersection check is correct.
**Recommendation:** The approach is sound. The gen_* functions return encoded moves; extracting `to_sq` from each gives the attack set. Chases only apply to general, chariot, cannon, and soldier (advisor/elephant/horse cannot be "chasing" in the WXO sense — they block, not chase).
**Confidence:** MEDIUM — not verified against a reference implementation of chase detection. Flag for test validation.

### OPEN-3: Chase vs. "attacking the same piece type"
**What's unclear:** The CONTEXT says "chase = the moving piece attacks a specific enemy piece" and tracks `(attacking_piece_sq, target_piece_sq)`. Is it possible for a piece to move to a square where it attacks the same enemy piece type but NOT the same specific piece?
**What we know:** The WXO rule is about the specific piece being chased. If red chariot moves from A to B and attacks black chariot at C in both positions, and then later moves from B to D and still attacks the same black chariot at C, those are 2 consecutive chases of the same (chariot, specific black chariot at C). The tracking is by `(attacker_sq, target_sq)`, so the chariot moving to different squares (B, D) while attacking the same target produces different `(attacker_sq, target_sq)` pairs — sequence is NOT broken by "new square" because `attacker_sq` changes.
**Recommendation:** The algorithm as written handles this correctly. If the chasing piece moves to a new square but still attacks the same target, it's still a chase (the `(attacker_sq, target_sq)` pair is different, but this adds to the sequence). The "new square = meaningful progress" rule applies when the chasing piece moves to a square and attacks a DIFFERENT enemy piece — that's a new chase sequence.
**Confidence:** MEDIUM — the interpretation of "new square = meaningful progress" needs validation against WXO examples.

### OPEN-4: Test fixture FEN positions
**What's unclear:** Exact FEN strings for long-check and long-chase test positions.
**What we know:** Checkmate/stalemate positions are available from `test_rules.py`. Long-check and long-chase positions need to be constructed.
**Recommendation:** Construct positions programmatically by setting up the board directly with `make_state()` (existing helper pattern), then simulating the required number of checking/chasing moves to reach the threshold. Use `apply_move()` to walk the game forward to the target state, verifying at each step that the correct condition is accumulating. Example:
```python
def test_long_check_4_moves_draw():
    """Red chariot checks black king 4 times in a row with no escape."""
    rep_state = RepetitionState()
    state = _build_long_check_position()  # sets up initial checking position
    for i in range(4):
        moves = generate_legal_moves(state)
        checking_move = _select_checking_move(state, moves)
        snap = state.copy()
        apply_move(state, checking_move)
        rep_state.update(snap, checking_move, state)
    result = get_game_result(state, rep_state)
    assert result == 'DRAW'
```

---

## Sources

### Primary (HIGH confidence)
- `src/xiangqi/engine/rules.py` — existing `get_game_result()`, confirmed behavior for checkmate/stalemate
- `src/xiangqi/engine/legal.py` — `is_in_check()`, `generate_legal_moves()`, `apply_move()`, confirmed board-update semantics
- `src/xiangqi/engine/state.py` — `XiangqiState` dataclass, `compute_hash()`, `update_hash()`, confirmed hash-history semantics
- `.planning/phases/03-endgame-detection/03-CONTEXT.md` — locked decisions, authoritative for this phase
- `.planning/research/RULES.md` §8 — WXO draw conditions, long check/chase specification

### Secondary (MEDIUM confidence)
- `.planning/ROADMAP.md` §Phase 3 — deliverables list (superseded for file count by CONTEXT.md)
- WXO Rules — long check/chase detection algorithm (general description matches implementation approach)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pure Python + numpy, no new dependencies
- Architecture: HIGH — decisions trace directly to CONTEXT.md locked choices
- Algorithms: HIGH for END-01/END-02/END-04; MEDIUM for END-03 (chase detection not verified against reference)
- Pitfalls: HIGH — derived from existing code patterns and RULES.md edge cases

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (rules domain is stable; no fast-moving libraries involved)
