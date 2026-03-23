# Phase 03: 终局判定 - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Detect all terminal game states in Xiangqi: checkmate, stalemate (困毙), perpetual check (长将), perpetual chase (长捉), and repetition draw. Builds on existing `get_game_result()` (rules.py), `XiangqiState.zobrist_hash_history`, and `is_in_check()`.

Deliverables (from ROADMAP.md):
- `src/xiangqi/engine/endgame.py` — `get_game_result()` (moved/refactored from rules.py), checkmate/stalemate detection
- `src/xiangqi/engine/repetition.py` — repetition detection + long check/long chase tracking
- `tests/test_endgame.py`, `tests/test_repetition.py`

Verification: all 5 END-01..END-05 requirements pass, boundary tests pass

</domain>

<decisions>
## Implementation Decisions

### END-04: Repetition draw — 3× any position in history → draw
- Use existing `XiangqiState.zobrist_hash_history`
- If any hash appears 3 or more times in the history → return `'DRAW'`
- Does NOT require consecutive repetitions; any 3 occurrences anywhere in history trigger draw
- Count = history.count(hash) ≥ 3

### END-03: Long check (长将) — 4 consecutive checking moves → draw
- 4 consecutive moves where the same side gives check (using `is_in_check()` after each move)
- Both sides not in check → draw (NOT loss for checking side)
- Standard WXO rule: continuous check for 4+ moves without resolution → draw

### END-03: Long chase (长捉) — 4 consecutive chases of same target → chaser loses
- A "chase" = a move where the moving piece attacks a specific enemy piece
- Track: `(attacking_piece_sq, target_piece_sq)` per move
- If the same `(attacking_piece_sq, target_piece_sq)` repeats 4 consecutive times by the same side → the chasing side loses
- Chaser loses (not draw): `RED_WINS` if red chases, `BLACK_WINS` if black chases
- "Meaningful progress" breaks the chase sequence: giving check, capturing a piece, or moving to a square never visited in the current chase sequence
- Chaser losing is used instead of draw because the chaser is deliberately creating the loop

### END-01: Checkmate detection (将死)
- No legal moves AND king is in check → current player loses
- Uses existing `generate_legal_moves()` + `is_in_check()`
- Return: `BLACK_WINS` if red to move and in check; `RED_WINS` if black to move and in check

### END-02: Stalemate detection (困毙)
- No legal moves AND king is NOT in check → current player loses (not draw in Xiangqi)
- Already implemented in `get_game_result()` in rules.py — keep the same behavior
- Return: `BLACK_WINS` if red to move; `RED_WINS` if black to move

### END-05: 60-move rule — SKIP
- Not implemented in Phase 3
- Optional per REQUIREMENTS.md (标注为 optional)

### Module organization — two files, minimal
- `src/xiangqi/engine/endgame.py`: `get_game_result()` (moved from rules.py), checkmate/stalemate logic
- `src/xiangqi/engine/repetition.py`: repetition detection (END-04), long check tracking, long chase tracking (END-03)
- `repetition.py` maintains chasing state: `chase_seq: list[tuple[int, int]]` and `consecutive_check_count: int`
- Phase 4 `engine.py` imports from both

### State tracking for perpetual rules
- `XiangqiState.zobrist_hash_history` already exists — used for repetition
- New fields needed in `repetition.py` (not in XiangqiState):
  - `chase_seq: list[tuple[int, int]]` — `(attacking_sq, target_sq)` sequence, reset on non-chase move
  - `consecutive_check_count: int` — count of consecutive checking moves, reset on non-check position
  - `last_chasing_color: int` — which side is doing the chasing (+1 red, -1 black)
- These live in `repetition.py` as module-level tracking state (passed as arguments to `get_game_result()`)

### get_game_result() refactor
- Move from `rules.py` to `endgame.py`
- Call into `repetition.py` to check repetition and perpetual conditions
- Priority order: repetition → long check → long chase → checkmate → stalemate → IN_PROGRESS

### Testing approach
- `test_endgame.py`: boundary positions for checkmate, stalemate, and draw
- `test_repetition.py`: repetition draw, long check draw, long chase loss
- Use `XiangqiState.from_fen()` for test fixture setup
- CPW perft values (44, 1,920, 79,666) still valid for baseline

### Claude's Discretion
- Whether `chase_seq` resets on opponent's intervening non-chase move (e.g., red chases → black makes a non-chase move → red chases again: does the count reset?)
  - Decision: count resets when the OPPONENT makes a non-chase move (sequence is per-side, per-target)
- Exact threshold for "meaningful progress" (capture/check/new square)
- Internal organization of the check/chase detection functions
- Whether to inline perpetual check/chase detection in `get_game_result()` or call a helper

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project requirements
- `.planning/REQUIREMENTS.md` — END-01 through END-05 are the authoritative spec; END-05 is optional
- `.planning/ROADMAP.md` §Phase 3 — Deliverables, verification criteria, exit criteria

### Research (design rationale)
- `.planning/research/RULES.md` — Full Xiangqi rules with long check/chase specifications
  - §8.3 The "Long" Repetition Rules (长将/长捉): exact tracking structure, "meaningful progress" definition
  - §8.2 Draw conditions: repetition, perpetual check, perpetual chase, perpetual siege

### Phase 1 context
- `.planning/phases/01-data-structures/01-CONTEXT.md` — Piece encoding, XiangqiState structure, Zobrist hash

### Phase 2 context
- `.planning/phases/02-move-generation/02-CONTEXT.md` — Move generation architecture, board-copy post-check, `is_in_check()`, `generate_legal_moves()`
- `src/xiangqi/engine/rules.py` — Existing `get_game_result()` to be moved/refactored

### Phase 2 accumulated decisions
- `STATE.md` §Accumulated Context: XiangqiState king_positions dict, board-copy post-check, raw 16-bit moves
- `STATE.md` §Accumulated Context §Decisions: stalemate = loss in Xiangqi (困毙), CPW perft reference values

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `XiangqiState.zobrist_hash_history` — already tracked, used for repetition detection
- `XiangqiState.halfmove_clock` — already tracked (foundation for 60-move rule, not used here)
- `XiangqiState.king_positions` — O(1) king lookup
- `is_in_check(state, color)` — already implemented in legal.py
- `generate_legal_moves(state)` — already implemented in legal.py
- `compute_hash(board, turn)` — from state.py, used for repetition check
- `get_game_result(state)` — existing in rules.py, will be moved to endgame.py
- `tests/test_rules.py` — existing test patterns for checkmate/stalemate positions (to be moved to test_endgame.py)

### Established Patterns
- Module-level private constants prefixed with `_` (same as Phase 1/2)
- Raw 16-bit move encoding — no Move objects, no dataclasses
- `List[int]` for move collections
- `np.int8` for board, `np.uint64` for Zobrist hash
- Tests use pytest, one test file per source module

### Integration Points
- `endgame.py` imported by `engine.py` (Phase 4) — `get_game_result()` is the main entry point
- `repetition.py` imported by `endgame.py` — check functions called from `get_game_result()`
- Phase 4 `engine.py` will use `get_game_result()` from `endgame.py` instead of from `rules.py`

</code_context>

<specifics>
## Specific Ideas

- Long chase definition: same `(attacking_piece_sq, target_piece_sq)` repeated 4 consecutive times by the same color
- "Meaningful progress" breaks chase sequence: (1) giving check, (2) capturing a piece, (3) moving a piece to a square never occupied in the current chase sequence
- Repetition: any position appearing 3× in `zobrist_hash_history` (not required to be consecutive)
- Long check: 4 consecutive moves where `is_in_check(opponent, state.turn)` is True after each move

</specifics>

<deferred>
## Deferred Ideas

- END-05 60-move rule — skipped as optional; can revisit in future phase
- Perpetual siege (长围) — generalization of long check/chase; rarely implemented, out of scope

</deferred>

---

*Phase: 03-endgame-detection*
*Context gathered: 2026-03-20*
