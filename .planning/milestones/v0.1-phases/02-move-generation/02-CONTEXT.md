# Phase 2: 棋子走法生成与规则校验 - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate legal moves for all 7 Xiangqi piece types, detect check, enforce face-to-face rule, and provide the foundation for move execution (apply/undo). Pure Python — no UI, no RL interface.

Deliverables (from ROADMAP.md):
- `src/xiangqi/engine/moves.py` — gen_general, gen_chariot, gen_horse, gen_cannon, gen_advisor, gen_elephant, gen_soldier
- `src/xiangqi/engine/legal.py` — is_legal_move(), generate_legal_moves(), is_in_check()
- `src/xiangqi/engine/rules.py` — face-to-face rule, self-check prevention

Verification: test_moves.py, test_legal.py, test_rules.py, Perft depth=1~3

</domain>

<decisions>
## Implementation Decisions

### Move generation architecture — pure generators + board copy
- Each `gen_*()` function is **pure**: returns all pseudo-legal moves given current board geometry and piece blocking — NO king safety check inside generators
- `generate_legal_moves()` collects all pseudo-legal moves, then filters by simulating each on a board copy (via XiangqiState.copy()) and keeping only moves where own king is safe
- Rationale: generators are independently testable; correctness over micro-optimization for Xiangqi's small branching factor (~50 moves max)
- Use `king_positions` dict (Phase 1) for O(1) king lookup during check detection

### Per-piece move generators — geometry-only, no state dependency
- `gen_general(state)` — orthogonal 1-step, constrained to palace via _in_palace mask (from constants.py)
- `gen_chariot(state)` — slide orthogonally until blocked, collect each reachable square
- `gen_horse(state)` — 8 leg directions, check blocking with knee-position table
- `gen_cannon(state)` — slide orthogonally, collect non-blocked squares (quiet) + exactly-1-intervenor squares (capture)
- `gen_advisor(state)` — diagonal 1-step, constrained to palace
- `gen_elephant(state)` — diagonal 2-step, check elephant-eye (midpoint blocked), constrained to own half via _elephant_home_half mask
- `gen_soldier(state)` — forward 1-step if before river; forward/left/right if after river

### Return type — raw 16-bit integers
- All generator functions return `list[int]`, each int is a 16-bit move encoding (from_sq | (to_sq << 9))
- Consistent with Phase 1: no Move dataclass, no named tuples
- Helper: `encode_move(from_sq, to_sq, is_capture=0)` already exists in types.py

### Sliding piece implementation — direction scanning
- For Chariot and Cannon: scan 4 orthogonal directions, stop on first blocker (Chariot) or collect on exactly-1-intervenor (Cannon)
- Do NOT precompute full attack bitmasks — direction scanning is fast enough for 10×9 board and keeps memory flat
- Direction offsets: [(−1,0), (1,0), (0,−1), (0,1)] for orthogonal; horse knee positions precomputed as list of (knee_row, knee_col) deltas

### Test strategy — per-piece tests with minimal FEN boards
- One test per piece type: `test_gen_chariot()`, `test_gen_horse()`, etc.
- Each uses `XiangqiState.from_fen()` to create a minimal board with only that piece + known blockers
- Assert exact move count: e.g., unblocked horse = 8 moves, blocked horse = 2 moves
- `test_total_moves_starting_position()` — validates 44 total legal moves from initial position
- `test_is_in_check()` — set up board where known piece attacks king, assert is_in_check returns correct color
- `test_face_to_face_rule()` — set up generals facing each other, assert no column move is legal
- Use pytest fixtures from tests/conftest.py (Phase 1)

### Face-to-face rule implementation
- When generating moves for a piece on the same file as the enemy general with no pieces between: do not generate moves that would leave both generals facing each other
- Check: if from_sq and enemy_general_sq share the same column, scan squares between them — if all empty, this file is blocked for non-general pieces

### State mutation methods
- `apply_move(state, move)` — update board, switch turn, update king_positions if general moved, append hash to history (Phase 1 zobrist)
- `undo_move(state, move)` — reverse all apply_move effects
- These live in legal.py (Phase 2), referenced by engine.py (Phase 4)

### Claude's Discretion
- Internal organization of knee-position tables (can be list of tuples or dict)
- Whether to inline the face-to-face check in each generator or as a post-filter
- Horse knee-position: exact offset pairs (e.g., (−1,0) then (−2,−1), (−2,+1), etc.)
- Whether to use a `PIECE_ATTACKS` direction constant table or encode directions inline
- Test fixture naming and organization style

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project requirements
- `.planning/REQUIREMENTS.md` — MOVE-01 through MOVE-07, RULE-01 through RULE-06 are the authoritative spec
- `.planning/ROADMAP.md` §Phase 2 — Deliverables, verification criteria, exit criteria

### Research (design rationale)
- `.planning/research/RULES.md` — Full Xiangqi rules with move specifications, face-to-face rule, elephant constraints
  - §2 Pieces — All Legal Moves: exact movement for each piece type, including horse leg-blocking, elephant eye-blocking
  - §1 Board Layout: coordinate system, palace boundaries, river
- `.planning/research/DATA_STRUCTURES.md` — Phase 1 design rationale (attack representation, board scanning approaches)
  - §4 Performance notes on move generation strategies

### Phase 1 context (required reading)
- `.planning/phases/01-data-structures/01-CONTEXT.md` — Piece encoding, board representation, move encoding, boundary masks, XiangqiState king_positions
- `.planning/phases/01-data-structures/01-02-PLAN.md` — XiangqiState implementation with king_positions dict

### Project context
- `.planning/PROJECT.md` — v0.1 goal, constraints (Python + NumPy, no external deps beyond NumPy)
- `.planning/STATE.md` — Current milestone: v0.1, Phase 1 complete

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets (from Phase 1)
- `XiangqiState` from `src/xiangqi/engine/state.py` — board, turn, king_positions, copy(), zobrist_hash
- `_in_palace` from `src/xiangqi/engine/constants.py` — boolean ndarray (10, 9)
- `_elephant_home_half` from `src/xiangqi/engine/constants.py` — boolean ndarray (10, 9)
- `encode_move()`, `decode_move()` from `src/xiangqi/engine/types.py` — 16-bit move encoding
- `sq_to_rc()`, `rc_to_sq()` from `src/xiangqi/engine/types.py` — coordinate conversion
- `STARTING_FEN` from `src/xiangqi/engine/constants.py` — initial position for Perft tests
- `tests/conftest.py` — pytest fixtures (to be extended with Phase 2 fixtures)

### Established Patterns (from Phase 1)
- Module-level private constants prefixed with `_` (e.g., `_in_palace`, `_zobrist_piece`)
- `IntEnum` for piece types, pinyin names, signed encoding
- NumPy for all board operations and boolean masks
- Eager initialization at module import time
- Tests in `tests/` directory, one test file per source module

### Integration Points
- moves.py, legal.py, rules.py import from `xiangqi.engine.types`, `xiangqi.engine.state`, `xiangqi.engine.constants`
- Phase 4 `engine.py` calls `generate_legal_moves()` and `is_in_check()`
- Phase 3 endgame detection uses `is_in_check()` and `generate_legal_moves()`
- Phase 2 tests use `XiangqiState.from_fen()` (to be implemented in Phase 4's fen.py, but FEN parsing already exists in constants.py)

</code_context>

<specifics>
## Specific Ideas

- Horse knee positions: standard Xiangqi horse has 8 possible jumps:
  - Leg 1 at (−1,0) → jumps (−2,−1) and (−2,+1)
  - Leg 1 at (+1,0) → jumps (+2,−1) and (+2,+1)
  - Leg 1 at (0,−1) → jumps (−1,−2) and (+1,−2)
  - Leg 1 at (0,+1) → jumps (−1,+2) and (+1,+2)
- Elephant eye: midpoint of the 2-step diagonal must be empty (analogous to horse leg)
- Face-to-face check: when red general at (r, c) and black general at (r', c) with c == c', all squares between rows r+1 to r'−1 must be non-empty for any non-general piece to move on that file

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 2 scope.

</deferred>

---

*Phase: 02-move-generation*
*Context gathered: 2026-03-19*
