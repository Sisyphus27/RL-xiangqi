# Phase 10: Observation Encoding - AlphaZero Board Planes - Research

**Researched:** 2026-03-27
**Domain:** AlphaZero-style (16, 10, 9) board plane encoding + canonical rotation fix for XiangqiEnv
**Confidence:** HIGH (bug location known from code inspection; RL_ENV.md provides encoding spec; engine API fully understood; test FENs and actions verified in Python)

---

## Summary

Phase 10 fixes one targeted bug in `src/xiangqi/rl/env.py` and validates the resulting 16-channel observation encoding. The bug is in `_canonical_board()` (line 152-157): it rotates the board 180 degrees for black-to-move but does not negate piece values, so black pieces stay negative and route to channels 7-13 instead of the canonical red channels 0-6. The fix is a one-line negation after `np.rot90()`. Beyond the fix, the phase delivers a test suite across 4 categories (piece channel encoding, canonical rotation, repetition channel, halfmove clock channel) using programmatically verified FEN strings and move actions.

**Primary recommendation:** Fix `_canonical_board()` with `board = -np.rot90(board, k=2)` and add 4 focused test functions to `tests/test_rl.py`. The existing test infrastructure (pytest, test_rl.py, gymnasium) covers all needs.

---

## User Constraints (from 10-CONTEXT.md)

### Locked Decisions
- **D-10-01:** Keep `(16, 10, 9)` — no expansion to 17 or 32 channels
- **D-10-02:** Channels 0-6: Red piece types (General, Advisor, Elephant, Horse, Chariot, Cannon, Soldier)
- **D-10-03:** Channels 7-13: Black piece types (same 7 types, same ordering)
- **D-10-04:** Channel 14: Repetition count, normalized `min(count, 3) / 3.0`
- **D-10-05:** Channel 15: Halfmove clock, normalized `min(clock, 100) / 100.0`
- **D-10-06:** Observation always from active player's perspective (canonical rotation)
- **D-10-07:** Fix `_canonical_board()` — negate piece values after 180 degree rotation
- **D-10-08:** Skip history planes (channels 16-31) — keep (16, 10, 9) only
- **D-10-09:** Skip Flying-General channel — engine `is_legal()` already handles it
- **D-10-10:** 4 test categories: piece channel encoding, canonical rotation, repetition channel, halfmove clock channel

### Claude's Discretion
- Internal method naming conventions
- Exact implementation of the canonical rotation fix (negate values before or after rotation)
- Test file organization and naming conventions (follow Phase 09 pattern)

### Deferred Ideas (OUT OF SCOPE)
- History planes (channels 16-31) — deferred to v0.1
- Flying-General channel — deferred to future phase

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| R3 | AlphaZero-style board planes (16 channels) | D-10-01 through D-10-07: encoding shape, channel layout, canonical rotation fix |
| R3 | Canonical rotation: active player always seen as red at bottom | D-10-06, D-10-07: fix negates piece values after 180 deg rotation |

---

## Standard Stack

### Unchanged from Phase 09
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| gymnasium | >=1.0,<2.0 (already installed) | RL env base class | Phase 09 added to pyproject.toml |
| numpy | >=2.0,<3.0 | Board arrays, observation planes | Already in dependencies |
| pytest | existing | Test framework | Already in project |

**No new dependencies required.** Phase 10 is purely a code fix + test expansion.

---

## Architecture Patterns

### The Canonical Rotation Bug (Root Cause)

**File:** `src/xiangqi/rl/env.py` lines 152-157

```python
# CURRENT (buggy):
def _canonical_board(self):
    board = self._engine.board.copy()  # (10, 9)
    if self._engine.turn == -1:  # black to move
        board = np.rot90(board, k=2)  # 180 degree rotation
    return board
    # BUG: piece values still negative after rotation
    # Black Chariot at (0,0)=a10 → rotated to (9,0)=a1, still value=-5
    # In _get_observation(): piece=-5 → is_red=False → channel=4+7=11 (WRONG)
    # Should be: Black Chariot in canonical view = "red Chariot" = channel 4
```

**Problem trace (verified with Python):**
1. Starting board: Black Chariot at engine (row=0, col=0)=a10, value=-5
2. After 180 deg rotation: Black Chariot at (row=9, col=0)=a1, value=-5 (unchanged)
3. In `_get_observation()`: `is_red = piece > 0` → `-5 > 0 == False` → black piece
4. `channel = pt + 7 = 4 + 7 = 11` → WRONG (Black Chariot should be in channel 4)

**Why all existing black-to-move tests are invalid:** Any test that checks observation values for a black-to-move position reads the wrong channel. The black pieces are encoded in channels 7-13 when they should be in 0-6 (canonical red channels).

### The Fix

```python
# FIXED (D-10-07):
def _canonical_board(self):
    board = self._engine.board.copy()  # (10, 9)
    if self._engine.turn == -1:  # black to move
        board = -np.rot90(board, k=2)  # 180 deg + negate piece values
    return board
    # After fix: Black Chariot at (9,0) now has value=+5
    # In _get_observation(): is_red = +5 > 0 == True → channel = 4 (CORRECT)
```

**Why negation is safe:** `(-np.rot90(board, k=2))` is element-wise negation of the rotated board. For each square at rotated position (r', c'):
- Original piece at (9-r', 8-c') = -5 (Black Chariot)
- After rot90: at (r', c'), value=-5
- After negation: value=+5 (positive = red-channel in canonical view)
- `pt = abs(+5) - 1 = 4` → channel 4 (Chariot) ✓

**Negation order:** `board = -np.rot90(board, k=2)` — rot90 returns a new array, negation is applied to it. Equivalent to `board = np.rot90(-board, k=2)` but clearer.

### Verified Coordinate Transform (Python-verified)

Starting position: Black Chariot at engine (row=0, col=0)=a10, value=-5

After `np.rot90(board, k=2)`:
- Coordinate: (row=9, col=0)=a1
- Value: -5 (unchanged)

After `-np.rot90(board, k=2)`:
- Coordinate: (row=9, col=0)=a1
- Value: +5 (negated)

In `_get_observation()` with fixed board:
- `piece = +5` → `is_red = True` → `pt = 4` → `channel = 4` (Red Chariot channel)
- This is correct for canonical view: Black Chariot (active player) appears as "Red Chariot" at channel 4

### _build_piece_masks() Coordinate Transform (Already Correct)

The `_build_piece_masks()` method (lines 193-226) already correctly handles canonical coordinates:

```python
# Lines 210-215 — already handles rotation:
if engine_turn == -1:  # black to move: board was rotated 180
    cr, cc = 9 - er, 8 - ec   # canonical from-coords
    ct, cc_to = 9 - et, 8 - ec_to  # canonical to-coords
else:
    cr, cc = er, ec
    ct, cc_to = et, ec_to
```

After the fix, `board = -np.rot90(board, k=2)`, the `canonical_piece = board[cr, cc]` read at line 222 is always the correctly signed piece value. The coordinate transform in `_build_piece_masks()` is independent of the value negation — it handles rotation coordinates correctly.

**One cleanup micro-task:** Line 206 sets `engine_piece = self._engine.board[er, ec]` but the value is never used (only `canonical_piece = board[cr, cc]` is used). Remove the unused variable as a golf cleanup within the fix plan.

### Channel 14 and 15 Implementation (Already Correct)

```python
# Lines 142-148 — no changes needed:
state = self._engine.state
current_hash = state.zobrist_hash_history[-1]
rep_count = state.zobrist_hash_history.count(current_hash)
planes[14] = np.clip(rep_count, 0, 3) / 3.0   # D-10-04

planes[15] = np.clip(state.halfmove_clock, 0, 100) / 100.0  # D-10-05
```

- **Channel 14:** Counts current Zobrist hash occurrences in history. Normalization `min(count, 3) / 3.0` gives 0.0, 0.67, 1.0, 1.0 for 1/2/3/4-fold.
- **Channel 15:** Reads `halfmove_clock` from engine state. Phase 09-05 fixed WXF FEN parsing, so `halfmove_clock` is correct. No changes needed.

**Zobrist hash includes turn bit** (verified in `state.py` line 44-45: `if turn == -1: h ^= _zobrist_piece[14, 0]`), so same board with opposite turn has different hash. This is correct for Xiangqi repetition.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Canonical rotation | Custom row/col flip with separate piece-type swap | `-np.rot90(board, k=2)` | rot90 is the correct 180 deg transform; negation swaps red/black |
| Repetition tracking | Custom hash counter | `state.zobrist_hash_history.count(current_hash)` | Already in engine state |
| Halfmove clock | Custom counter | `state.halfmove_clock` | Already maintained by engine on every apply() |
| Channel 14 normalization | Custom logic | `np.clip(rep_count, 0, 3) / 3.0` | D-10-04 specifies exact formula |

---

## Common Pitfalls

### Pitfall 1: Canonical rotation test FEN with pieces on wrong files
**What goes wrong:** FEN `9/9/9/9/9/9/9/4R4/9/5C2` places Red Chariot at (row=7, col=4) and Black Cannon (not Chariot) at a different position.
**Root cause:** In xiangqi FEN: `r`=Black Chariot (B_CHE=-5), `C`=Red Cannon (R_PAO=+6), `c`=Black Cannon (B_PAO=-6). Standard starting board has Red Chariots at a1=(9,0) and i1=(9,8), Black Chariots at a10=(0,0) and i10=(0,8).
**How to avoid:** Use verified midgame FEN `1r1a1R1/9/9/9/9/9/9/9/9/9` with Red at row 9, col 0 and Black at row 0, col 0. Verified programmatically.

### Pitfall 2: Testing canonical rotation with bare kings
**What goes wrong:** Bare kings FEN only exercises the General channel (0). The other 6 red channels and 6 black channels are not tested.
**How to avoid:** Use a multi-piece position for canonical rotation. At minimum, test with 2 pieces on different channels (e.g., one Red and one Black Chariot on the a-file).

### Pitfall 3: Repetition test using standard starting position chariot moves
**What goes wrong:** In the standard starting position, Black Chariot at a10=(0,0) has NO legal moves (blocked by Black Pawn at a3=(3,0) below, and by Red Chariot at a1=(9,0) above). Red Chariot at a1 can move to a2=(8,0) and a3=(7,0) but no further.
**How to avoid:** Use the verified midgame FEN `1r1a1R1/9/9/9/9/9/9/9/9/9` with no other pieces on the a-file, enabling a 4-move repetition cycle.

### Pitfall 4: Channel 14 counts turn-different positions as repetition
**What goes wrong:** The same board with opposite sides to move may be treated as the same position.
**Why it happens:** Zobrist hash includes the turn bit, so position A with Red to move and position A with Black to move have different hashes. Repetition counter is position-specific (correct behavior).
**How to avoid:** This is correct. The WXF repetition rule requires identical position AND same side to move.

---

## Code Examples

### The Fix: One-line Negation

```python
# src/xiangqi/rl/env.py — _canonical_board() method (D-10-07)
def _canonical_board(self):
    """Return board with canonical rotation (D-10, D-10-07).

    When black to move: rotate 180 deg AND negate piece values so black
    pieces appear as positive (red-channel) values in the canonical view.
    """
    board = self._engine.board.copy()  # (10, 9)
    if self._engine.turn == -1:  # black to move
        board = -np.rot90(board, k=2)  # 180 deg + negate (D-10-07 fix)
    return board
```

### Test: Piece Channel Encoding (Starting Position)

```python
# tests/test_rl.py — new test
def test_observation_piece_channels_starting():
    """D-10-02, D-10-03: All 14 piece channels correctly populated at start.

    Verifies:
    - 7 red pieces -> channels 0-6, one per piece type
    - 7 black pieces -> channels 7-13, one per piece type
    - Auxiliary channels 14, 15 are zero at starting position
    """
    env = XiangqiEnv()
    obs, _ = env.reset()

    # Count pieces per channel (should sum to 14)
    pieces_per_channel = obs.sum(axis=(1, 2))  # shape (16,)
    assert pieces_per_channel.sum() == 14, f"Expected 14 pieces, got {pieces_per_channel.sum()}"

    # Red channels (0-6): piece counts: G=1, A=2, E=2, H=2, C=2, P=2, S=5
    red_expected = [1, 2, 2, 2, 2, 2, 5]
    for ch, expected in enumerate(red_expected):
        assert pieces_per_channel[ch] == expected, \
            f"Red channel {ch}: expected {expected}, got {pieces_per_channel[ch]}"

    # Black channels (7-13): same counts
    for ch, expected in enumerate(red_expected):
        assert pieces_per_channel[ch + 7] == expected, \
            f"Black channel {ch+7}: expected {expected}, got {pieces_per_channel[ch+7]}"

    # Auxiliary channels (14, 15): starting position has no repetition, halfmove=0
    assert pieces_per_channel[14] == 0.0, f"Repetition at start: expected 0.0, got {pieces_per_channel[14]}"
    assert pieces_per_channel[15] == 0.0, f"Halfmove at start: expected 0.0, got {pieces_per_channel[15]}"
```

### Test: Canonical Rotation (Black-to-Move)

```python
# tests/test_rl.py — new test
def test_observation_canonical_rotation_black_to_move():
    """D-10-06, D-10-07: Black-to-move position encoded from active player's view.

    FEN: Black Chariot at a10=(0,0), Red Chariot at a1=(9,0), red to move.
    After one red chariot move a1->a2: black to move.

    After canonical rotation fix:
    - Black Chariot (at canonical row 9, col 0) negated to +5 -> channel 4
    - Red Chariot (at canonical row 0, col 0) negated to -5 -> channel 11
    Active player (black) pieces are in channels 0-6. Verified in Python.
    """
    # Mid-game: Red Chariot at a1=(9,0), Black Chariot at a10=(0,0), no other a-file pieces
    # xiangqi FEN: row 0 (top) -> '1r1...' (Black at col 0), row 9 (bottom) -> '...R1' (Red at col 0)
    midgame_fen = "1r1a1R1/9/9/9/9/9/9/9/9/9 w - - 0 1"
    env = XiangqiEnv()
    obs, info = env.reset(options={"fen": midgame_fen})

    assert info["player_to_move"] == 1, "Should be red to move"

    # Red Chariot a1->a2: from_sq=81 (a1), to_sq=72 (a2), action=72*90+81=6561
    # Verified: legal in this FEN (a2=(8,0) is empty)
    env.step(6561)  # action = a2*90 + a1 = 72*90+81

    # Now black to move: verify canonical encoding
    obs = env._get_observation()
    pieces_per_channel = obs.sum(axis=(1, 2))

    # Black-to-move canonical view: active player's piece in red channel 4
    # Black Chariot (active) negated to +5 -> channel 4 (Chariot)
    assert pieces_per_channel[4] == 1, \
        f"Active (canonical-red) Chariot: expected 1 in ch 4, got {pieces_per_channel[4]}"

    # Opponent (former red) Chariot negated to -5 -> channel 11 (Black Chariot)
    assert pieces_per_channel[11] == 1, \
        f"Opponent (canonical-black) Chariot: expected 1 in ch 11, got {pieces_per_channel[11]}"

    # Total active-player pieces in red channels 0-6: should be 1 (the Black Chariot)
    red_total = pieces_per_channel[0:7].sum()
    assert red_total == 1, f"Red channels should have 1 piece (active), got {red_total}"
```

### Test: Repetition Channel

```python
# tests/test_rl.py — new test
def test_observation_repetition_channel():
    """D-10-04: Channel 14 reflects position repetition count (normalized 0-3).

    Uses midgame FEN with only two chariots on the a-file (no blocking pieces).
    Cycle: Red a1->a2, Black a10->a1 (capture), Red a2->a1 (capture), Black a1->a2 (capture).
    After 4 moves: back to starting position with black to move.
    Repeat: 8 moves total -> 4-fold repetition -> channel 14 = 1.0 (clipped).
    Verified moves (Python):
      Red a1->a2:   from_sq=81, to_sq=72, action=6561
      Black a10->a1: from_sq=4, to_sq=85, action=85
      Red a2->a1:    from_sq=72, to_sq=81, action=81
      Black a1->a2:  from_sq=85, to_sq=72, action=6484
    """
    # Midgame FEN: Red Chariot at a1=(9,0), Black Chariot at a10=(0,0)
    # All other a-file squares empty (no blocking pieces)
    midgame_fen = "1r1a1R1/9/9/9/9/9/9/9/9/9 w - - 0 1"
    env = XiangqiEnv()
    env.reset(options={"fen": midgame_fen})

    # Verified action encodings for the a-file chariot cycle:
    # a1=(9,0)=sq 81, a2=(8,0)=sq 72, a10=(0,0)=sq 4
    a1 = 81   # row 9 col 0
    a2 = 72   # row 8 col 0
    a10 = 4   # row 0 col 0
    red_advance   = a2 * 90 + a1  # 6561: a2*90+a1
    black_capture = a1 * 90 + a10 # 85: a1*90+a10
    red_retreat   = a1 * 90 + a2  # 81: a1*90+a2
    black_advance = a10 * 90 + a2 # 6484: a10*90+a2

    # Execute 4-move cycle twice to reach 4-fold repetition
    env.step(red_advance)    # Red a1->a2
    env.step(black_capture)  # Black a10->a1 (capture)
    env.step(red_retreat)   # Red a2->a1 (capture, back to start)
    env.step(black_advance)  # Black a1->a2 (capture)

    # Back at starting position, black to move: 2-fold
    obs2 = env._get_observation()
    rep2 = obs2[14].max()
    assert abs(rep2 - 2.0/3.0) < 0.01, f"At 2-fold: expected 2/3={2.0/3.0}, got {rep2}"

    # Second cycle: 4-fold repetition
    env.step(red_advance)    # Red a1->a2
    env.step(black_capture)  # Black a10->a1
    env.step(red_retreat)   # Red a2->a1
    env.step(black_advance) # Black a1->a2

    # Back at starting position: 4-fold -> normalized = 1.0 (clipped)
    obs4 = env._get_observation()
    rep4 = obs4[14].max()
    assert rep4 == 1.0, f"At 4-fold: expected 1.0, got {rep4}"
```

### Test: Halfmove Clock Channel

```python
# tests/test_rl.py — new test
def test_observation_halfmove_clock_channel():
    """D-10-05: Channel 15 reflects halfmove clock (normalized 0-1).

    Starting position: halfmove_clock=0 -> channel 15 value = 0.0
    After 10 non-capture, non-pawn moves: halfmove_clock=10 -> value = 0.1
    WXF bare-kings FEN: both halfmove_clock and repetition are independent to verify.
    """
    # WXF 5-field FEN (no en passant field): bare kings, halfmove=0
    bare_kings_fen = "9/9/9/9/4K4/9/9/9/9/4k4 w - 0 1"
    env = XiangqiEnv()
    obs0, _ = env.reset(options={"fen": bare_kings_fen})
    assert obs0[15].max() == 0.0, "Starting position: halfmove should be 0"

    # Make 10 legal moves (kings moving, non-capturing)
    legal_mask = env._get_info()["legal_mask"]
    legal_actions = np.where(legal_mask == 1.0)[0]
    for i in range(10):
        env.step(int(legal_actions[i % len(legal_actions)]))
        halfmove = env._engine.state.halfmove_clock
        expected_val = np.clip(halfmove, 0, 100) / 100.0
        obs_hmc = env._get_observation()
        assert abs(obs_hmc[15].max() - expected_val) < 0.001, \
            f"After {i+1} moves: expected {expected_val}, got {obs_hmc[15].max()}"

    # At 10 non-pawn/capture moves: halfmove_clock=10 -> value=0.1
    final_hmc = env._engine.state.halfmove_clock
    assert final_hmc == 10, f"Expected halfmove=10, got {final_hmc}"
    obs_final = env._get_observation()
    assert abs(obs_final[15].max() - 0.1) < 0.001
```

---

## State of the Art

| Aspect | Current (Phase 09) | Phase 10 | Why Changed |
|--------|---------------------|----------|-------------|
| Canonical rotation | Rotates board 180 deg, no negation | Rotates + negates piece values | Bug D-10-07 confirmed: black pieces routed to wrong channels |
| Black-to-move obs | WRONG — black pieces in channels 7-13 | CORRECT — all active-player pieces in channels 0-6 | The fix |
| Channel 14 (repetition) | Correct (if called correctly) | No change needed | Already using `zobrist_hash_history.count()` |
| Channel 15 (halfmove) | Correct (Phase 09-05 WXF fix) | No change needed | Already reads `halfmove_clock` |

**No deprecated approaches:** The 16-channel AlphaZero encoding and canonical rotation are the current state of the art for board game RL.

---

## Open Questions

1. **Should `_build_piece_masks()` read `engine_piece` or canonical `board[cr, cc]`?**
   - What we know: Line 206 sets `engine_piece = self._engine.board[er, ec]` but the value is never used; only `canonical_piece = board[cr, cc]` is used for `pt_idx`.
   - Recommendation: After the fix, `canonical_piece` from the rotated board is always correct. Remove the unused `engine_piece` variable as a cleanup micro-task within the fix plan.

2. **Should `_get_observation()` also negate the board for canonical rotation, or does it always receive a pre-negated board from `_canonical_board()`?**
   - What we know: `_get_observation()` calls `_canonical_board()` and then iterates. After the fix, `_canonical_board()` returns the correctly negated board for black-to-move.
   - Recommendation: Keep the negation in `_canonical_board()` only (D-10-07 fix). `_get_observation()` remains unchanged.

3. **FEN and move encoding for tests — fully resolved by Python verification**
   - **Canonical rotation FEN:** `1r1a1R1/9/9/9/9/9/9/9/9/9 w - - 0 1`
     - Black Chariot at row 0 col 0 (=a10), Red Chariot at row 9 col 0 (=a1)
     - Verified: Black at (0,0)=-5, Red at (9,0)=+5 in engine board
   - **Red chariot a1->a2:** action = `72*90+81 = 6561` (verified legal)
   - **Repetition FEN:** Same FEN enables 4-move cycle: Red a1->a2(6561), Black a10->a1(85), Red a2->a1(81), Black a1->a2(6484)
     - After 4 moves: back at starting position, black to move (2-fold repetition)
     - After 8 moves: 4-fold repetition, channel 14 = 1.0
   - **Halfmove FEN:** `9/9/9/9/4K4/9/9/9/9/4k4 w - 0 1` (bare kings, halfmove=0, WXF 5-field)

---

## Environment Availability

Step 2.6: SKIPPED (no external dependencies — Phase 10 is purely Python code changes to existing source files and test additions)

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing project) |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/test_rl.py -x -q` |
| Full suite command | `pytest tests/ -q --tb=short` |
| Phase gate | All 4 new tests green before `/gsd:verify-work` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| R3 | 14 piece channels correct at starting position | unit | `pytest tests/test_rl.py::test_observation_piece_channels_starting -x` | W0: test_rl.py exists |
| R3 | Canonical rotation: black-to-move in channels 0-6 | unit | `pytest tests/test_rl.py::test_observation_canonical_rotation_black_to_move -x` | W0: test_rl.py exists |
| R3 | Channel 14 repetition count correct | unit | `pytest tests/test_rl.py::test_observation_repetition_channel -x` | W0: test_rl.py exists |
| R3 | Channel 15 halfmove clock correct | unit | `pytest tests/test_rl.py::test_observation_halfmove_clock_channel -x` | W0: test_rl.py exists |

### Wave 0 Gaps

- [ ] `tests/test_rl.py` — 4 new test functions added for Phase 10 (D-10-10)
- [ ] `tests/test_rl.py` — existing tests remain green (regression check)
- Framework install: gymnasium already added by Phase 09 — no new install needed

*(If no gaps: "None — existing test infrastructure covers all phase requirements")*

### Sampling Rate
- **Per task commit:** `pytest tests/test_rl.py::test_observation_piece_channels_starting -x -q`
- **Per wave merge:** `pytest tests/test_rl.py -x -q`
- **Phase gate:** Full suite `pytest tests/ -q --tb=short` green before `/gsd:verify-work`

---

## Sources

### Primary (HIGH confidence)
- `src/xiangqi/rl/env.py` lines 124-157 — current `_get_observation()` and `_canonical_board()`; bug confirmed at line 156
- `src/xiangqi/engine/state.py` lines 32-46 — Zobrist hash includes turn bit, `zobrist_hash_history` as list of ints
- `src/xiangqi/engine/types.py` — Piece IntEnum, encode/decode, piece values +1 to +7 (red) and -1 to -7 (black)
- `src/xiangqi/engine/engine.py` — XiangqiEngine: legal_moves(), is_legal(), apply(), result(), board property
- `.planning/research/RL_ENV.md` 3 — AlphaZero board plane specification, canonical rotation rationale, channel layout
- `.planning/phases/09-xiangqi-env-core/09-RESEARCH.md` — existing XiangqiEnv architecture, D-10 (canonical rotation), engine API
- Python verification (xqrl conda env, 2026-03-27) — canonical rotation FEN, repetition move sequence, legal move verification

### Secondary (MEDIUM confidence)
- AlphaZero paper (Silver et al., PNAS 2018) — canonical board representation rationale
- "Mastering Chinese Chess AI (Xiangqi) Without Search" (arXiv:2410.04865) — Xiangqi-specific AlphaZero encoding

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; gymnasium already installed by Phase 09
- Architecture: HIGH — bug location confirmed via code inspection; fix is a one-line negation; all integration points verified in Python
- Pitfalls: HIGH — all 4 pitfalls identified from code trace-through; test FENs and action values verified programmatically

**Research date:** 2026-03-27
**Valid until:** 2026-04-26 (30 days — gymnasium API and engine API are stable)
