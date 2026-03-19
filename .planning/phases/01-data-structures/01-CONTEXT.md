# Phase 1: 数据结构 - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Build foundational data structures for the Xiangqi rule engine: board representation, piece encoding, move encoding, game state container with Zobrist hashing, and starting position constants. Pure infrastructure — no game logic, no UI, no RL interface.

Deliverables (from ROADMAP.md):
- `src/xiangqi/engine/types.py` — Piece enum, board representation, move encoding
- `src/xiangqi/engine/state.py` — XiangqiState dataclass, Zobrist hash initialization
- `src/xiangqi/engine/constants.py` — STARTING_FEN, palace/river boundary tables

Verification tests: `test_types.py`, `test_state.py`, `test_constants.py`

</domain>

<decisions>
## Implementation Decisions

### Piece naming convention
- Use pure Chinese pinyin for enum member names
- Enum: `R_SHUAI=1, B_JIANG=-1, R_SHI=2, B_SHI=-2, R_XIANG=3, B_XIANG=-3, R_MA=4, B_MA=-4, R_CHE=5, B_CHE=-5, R_PAO=6, B_PAO=-6, R_BING=7, B_ZU=-7`
- `__repr__` of each enum member shows Chinese character: `R_SHUAI.__repr__()` → `"帅"` (display only, not the enum name)
- Use `IntEnum` so arithmetic works and mypy/strict typing passes

### Zobrist table initialization
- Eager initialization: `_init_zobrist()` called at module import time
- Tables stored as module-level global: `_zobrist_piece = np.zeros((15, 90), dtype=np.uint64)`
- Fixed seed (e.g. `random.Random(0x20240319)`) for reproducibility across runs
- No lazy initialization — simplicity over deferred cost

### FEN format
- Use WXF XFEN standard (World Xiangqi Federation notation)
- Piece symbols: K/k=general, A/a=advisor, B/b=elephant, N/n=horse, R/r=chariot, C/c=cannon, P/p=soldier
- Starting FEN: `rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1`
- Active color: `w` = red to move (Xiangqi convention: red moves first)
- `from_fen()` and `to_fen()` implemented in Phase 1 constants module

### Boundary constant storage
- Use `np.ndarray` boolean masks of shape `(10, 9)` for palace and river boundaries
- Example: `_in_palace = np.zeros((10, 9), dtype=bool)` with regions set to True
- Both palace and home-half (elephant river restriction) as boolean masks
- Do NOT use Python sets of tuples — boolean masks are faster for NumPy vectorized checks

### Test file organization
- One test file per source module: `test_types.py`, `test_state.py`, `test_constants.py`
- Use `pytest` as test runner
- Tests live in `tests/` directory (not alongside source)
- Target: all Phase 1 tests pass before Phase 2 begins

### Move representation
- 16-bit integer encoding only (DATA-03 requirement): `from_sq | (to_sq << 9) | (is_capture << 16)`
- No `Move` dataclass object — keep implementation lean
- Flat square index: `sq = row * 9 + col`, reverse: `row, col = divmod(sq, 9)`
- Helper functions: `encode_move()`, `decode_move()`, `sq_to_rc()`, `rc_to_sq()` in `types.py`

### Claude's Discretion
- Internal organization of the Piece enum members (order, grouping)
- Exact location of helper functions (can live in `types.py` or a `_utils.py` submodule)
- Whether to use `@dataclass(slots=True)` vs plain class for XiangqiState
- Random seed value (any fixed non-zero 32/64-bit integer)
- Exact row/column index direction (as long as STARTING_FEN is consistent with it)
- Test fixture setup style

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project requirements
- `.planning/REQUIREMENTS.md` — DATA-01 through DATA-05 are the authoritative spec for Phase 1
- `.planning/ROADMAP.md` §Phase 1 — Deliverables, verification criteria, exit criteria

### Research (design rationale)
- `.planning/research/DATA_STRUCTURES.md` — Full design with code examples, performance notes, piece encoding table, Zobrist implementation, boundary table formats, FEN parsing
  - §1 Board Representation: board shape, coordinate convention
  - §2 Piece Encoding: signed int8 table, Piece IntEnum design
  - §3 Move Representation: 16-bit encoding, helper functions, flat index
  - §4 Game State: XiangqiState dataclass, Zobrist hashing, incremental hash update
  - §8 Performance: speed targets, optimization guidance

### Project context
- `.planning/PROJECT.md` — v0.1 goal, constraints (Python + PyTorch + PyQt6, MPS backend)
- `.planning/STATE.md` — Current milestone: v0.1

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None yet — this is a greenfield project. All source and test files are new.

### Established Patterns
- No existing Python code in this project yet. Researcher code in DATA_STRUCTURES.md is reference material, not runnable code to copy.

### Integration Points
- Phase 1 outputs (`types.py`, `state.py`, `constants.py`) are the foundation all subsequent phases depend on
- `XiangqiState` from `state.py` will be used by every subsequent phase (moves, rules, endgame, API)
- Piece encoding from `types.py` used throughout
- FEN parser in `constants.py` will be used by Phase 4 engine API
- No external dependencies beyond NumPy (confirmed in PROJECT.md constraints)

</code_context>

<specifics>
## Specific Ideas

- "Pure Chinese pinyin" means the enum member names ARE the pinyin: `R_SHUAI`, not `R_GENERAL`
- `__repr__` of enum members shows the Chinese character for human readability
- Palace boundaries: black palace = rows 0–2, cols 3–5; red palace = rows 7–9, cols 3–5
- River boundary: rows 4–5 (between the two sides)
- Elephant home-half: black elephant rows 0–4, red elephant rows 5–9

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 1 scope.

</deferred>

---

*Phase: 01-data-structures*
*Context gathered: 2026-03-19*
