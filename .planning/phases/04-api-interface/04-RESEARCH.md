# Phase 04: api-interface - Research

**Researched:** 2026-03-20
**Domain:** Python class API design, FEN serialization, undo/move-stack mechanics, pyffish cross-validation
**Confidence:** HIGH

## Summary

Phase 4 wraps all previously built internal modules (`XiangqiState`, `legal`, `endgame`, `repetition`) behind a single `XiangqiEngine` facade. The engine holds state and a private `RepetitionState`, exposes 7 methods plus 3 read-only properties, and manages a move-undo stack. FEN import/export lives on the engine class itself, not a separate module. Four test files cover the API surface, perft benchmarking, boundary positions, and pyffish cross-validation.

**Primary recommendation:** Build `XiangqiEngine` as a thin facade — every method delegates to one of the four existing internal modules. The only non-trivial logic is the `undo()` stack, which must snapshot and restore `RepetitionState` alongside board state.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Engine holds and owns XiangqiState** — external callers never touch internal modules directly
- **FEN on the Engine class** — `XiangqiEngine.from_fen(fen)` (classmethod) and `engine.to_fen()` (instance method), no separate `fen.py` module
- **7 public methods** (API-01): `reset()`, `apply(move)`, `undo()`, `is_legal(move)`, `legal_moves()`, `is_check()`, `result()`
- **3 read-only properties**: `board` (np.ndarray), `turn` (int), `move_history` (list)
- **Exceptions**: illegal move/FEN → `ValueError`; empty undo stack → `IndexError("nothing to undo")`
- **Undo mechanism**: incremental tuple stack `(from_sq, to_sq, captured, piece, prev_hash, prev_halfmove, prev_king_positions)`; `RepetitionState` snapshot + restore on undo
- **RepetitionState fully encapsulated** in engine; `reset()` reinitializes it; only `result()` is public
- **pyffish**: skip if unavailable via `pytest.importorskip`; completely separate `test_pyffish.py`; only validates perft(1) 44 moves

### Claude's Discretion

- Internal stack structure (tuple fields, snapshot format)
- Exact test assertions (exact values, number of test cases)
- Performance measurement approach

### Deferred Ideas (OUT OF SCOPE)

- END-05 60-move rule
- `engine.to_pgn()` / `engine.to_uci()` PGN/UCI export
- Separate `fen.py` module
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-01 | `XiangqiEngine` with `reset()`, `apply(move)`, `undo()`, `is_legal(move)`, `legal_moves()`, `is_check()`, `result()` | All 7 methods delegated to internal modules; signature and return types confirmed |
| API-02 | State correctly updated after apply (board, turn, move_history, halfmove_clock) | `legal.apply_move` already handles all 5 fields; engine wraps it |
| API-03 | FEN parse + export: `from_fen(fen)`, `to_fen()` | `XiangqiState.from_fen()` and `constants.to_fen()` already exist; engine re-exposes them |
| API-04 | Performance: legal moves < 10ms/position, full evaluation < 100ms | Pytest timing via `pytest.mark.slow` or explicit timer; test_perft.py already exists |
| TEST-01 | Perft depth 1-3 reference values (44, 1,920, 79,666) | `test_perft.py` already exists with correct CPW values; may need rewrite through engine API |
| TEST-02 | pyffish cross-validation of all legal moves | pyffish returns UCI strings; convert to/from 16-bit encoding for comparison |
| TEST-03 | Boundary positions: checkmate, stalemate, in-check positions | `test_endgame.py` already exists; may need engine-API rewrite |
| TEST-04 | Special rules: long-check draw, repetition draw, long-chase loss | `test_repetition.py` already exists; may need engine-API rewrite |
</phase_requirements>

---

## Standard Stack

No new external libraries are needed for the engine itself. All required modules already exist in `src/xiangqi/engine/`.

### Core

| Module | File | Purpose | Why Standard |
|--------|------|---------|--------------|
| `XiangqiEngine` | `src/xiangqi/engine/engine.py` (new) | Facade class — all Phase 4 deliverables | Owns state, delegates to internal modules |
| `XiangqiState` | `state.py` (existing) | Board, turn, move_history, halfmove_clock, zobrist_hash_history, king_positions | Already fully implemented |
| `legal.apply_move` | `legal.py` (existing) | Apply a move and update all state fields | Already handles board, king_positions, turn, hash, history, halfmove_clock |
| `legal.is_legal_move` | `legal.py` (existing) | Check if a move is legal | Already implemented |
| `legal.generate_legal_moves` | `legal.py` (existing) | Generate all legal moves | Already implemented |
| `legal.is_in_check` | `legal.py` (existing) | Check if a color is in check | Already implemented |
| `endgame.get_game_result` | `endgame.py` (existing) | Return game result string | Already implements END-01..END-04 |
| `RepetitionState` | `repetition.py` (existing) | Tracks check/chase sequences | Already implemented; engine wraps it |
| `constants.to_fen` | `constants.py` (existing) | Serialize board+turn to FEN string | Already implemented |
| `XiangqiState.from_fen` | `state.py` (existing) | Parse FEN to state | Already implemented |

### Test Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `pytest` | >= 8.0 | Test framework |
| `pyffish` | latest | Xiangqi move cross-validation (optional; skip if unavailable) |

**Installation:**
```bash
conda activate xqrl
pip install pytest
# optional cross-validation:
brew install stockfish   # macOS; or apt install stockfish on Linux
pip install pyffish
```

---

## Architecture Patterns

### Recommended Project Structure

```
src/xiangqi/engine/
├── types.py       # Piece IntEnum, move encoding (EXISTING)
├── constants.py   # STARTING_FEN, IN_PALACE, from_fen/to_fen (EXISTING)
├── state.py       # XiangqiState dataclass (EXISTING)
├── moves.py       # Piece move generators (EXISTING)
├── legal.py       # is_legal, generate_legal_moves, apply_move (EXISTING)
├── endgame.py     # get_game_result (EXISTING)
├── repetition.py  # RepetitionState (EXISTING)
└── engine.py      # XiangqiEngine facade (NEW — Phase 4 deliverable)
```

```
tests/
├── conftest.py       # Shared fixtures (EXISTING)
├── test_types.py     # Piece encoding tests (EXISTING)
├── test_state.py     # XiangqiState tests (EXISTING)
├── test_legal.py     # Legal move tests (EXISTING)
├── test_perft.py     # Perft benchmarks (EXISTING — may need engine-API rewrite)
├── test_endgame.py   # Endgame boundary tests (EXISTING)
├── test_repetition.py # Repetition rule tests (EXISTING)
├── test_api.py       # Full API integration tests (NEW)
└── test_pyffish.py   # pyffish cross-validation (NEW)
```

### Pattern 1: Facade Class (Engine as Coordinator)

**What:** `XiangqiEngine` holds private `XiangqiState` and `RepetitionState` instances. All public methods delegate to one of the four internal modules. The engine never duplicates logic that already exists in `legal.py`, `state.py`, or `endgame.py`.

**When to use:** Every public method.

**Example skeleton:**
```python
# Source: src/xiangqi/engine/engine.py (new)
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np

from .state import XiangqiState
from .legal import (
    apply_move as _apply_move,
    is_legal_move,
    generate_legal_moves,
    is_in_check,
)
from .endgame import get_game_result
from .repetition import RepetitionState
from .constants import to_fen, from_fen
from .types import encode_move


@dataclass
class XiangqiEngine:
    """Clean public API wrapping all internal Xiangqi engine modules."""

    _state: XiangqiState = field(default=None)
    _rep_state: RepetitionState = field(default_factory=RepetitionState)
    _undo_stack: list = field(default_factory=list)

    # ── Factory constructors ─────────────────────────────────────────────────

    @classmethod
    def starting(cls) -> XiangqiEngine:
        """Create engine at standard starting position."""
        eng = cls()
        eng._state = XiangqiState.starting()
        return eng

    @classmethod
    def from_fen(cls, fen: str) -> XiangqiEngine:
        """Create engine from FEN string (raises ValueError on parse error)."""
        try:
            eng = cls()
            eng._state = XiangqiState.from_fen(fen)
            return eng
        except Exception as exc:
            raise ValueError(f"Invalid FEN: {fen}") from exc

    # ── Public API ──────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset to starting position. Clears undo stack and RepetitionState."""
        self._state = XiangqiState.starting()
        self._rep_state.reset()
        self._undo_stack.clear()

    def apply(self, move: int) -> int:
        """Apply a move. Returns captured piece (0 if none). Raises ValueError if illegal."""
        if not is_legal_move(self._state, move):
            raise ValueError(f"Illegal move: {move}")
        # Snapshot for undo
        from_sq = move & 0x1FF
        to_sq   = (move >> 9) & 0x7F
        fr, fc = divmod(from_sq, 9)
        tr, tc = divmod(to_sq, 9)
        piece = int(self._state.board[fr, fc])
        captured = int(self._state.board[tr, tc])
        prev_hash = self._state.zobrist_hash_history[-1]
        prev_halfmove = self._state.halfmove_clock
        prev_king_positions = dict(self._state.king_positions)

        # Snapshot RepetitionState via its public interface
        # (RepetitionState is a dataclass; copy it)
        rep_snapshot = RepetitionState(
            consecutive_check_count=self._rep_state.consecutive_check_count,
            chase_seq=list(self._rep_state.chase_seq),
            last_chasing_color=self._rep_state.last_chasing_color,
        )

        prev_turn = self._state.turn
        captured = _apply_move(self._state, move)

        # Update RepetitionState
        self._rep_state.update(prev_state_for_rep(), move, self._state)

        self._undo_stack.append(UndoEntry(
            from_sq=from_sq, to_sq=to_sq, captured=captured,
            piece=piece, prev_hash=prev_hash, prev_halfmove=prev_halfmove,
            prev_king_positions=prev_king_positions,
            rep_snapshot=rep_snapshot,
        ))
        return captured

    def undo(self) -> None:
        """Undo the last move. Raises IndexError if stack is empty."""
        if not self._undo_stack:
            raise IndexError("nothing to undo")
        entry: UndoEntry = self._undo_stack.pop()
        fr, fc = divmod(entry.from_sq, 9)
        tr, tc = divmod(entry.to_sq, 9)
        # Restore board
        self._state.board[fr, fc] = np.int8(entry.piece)
        self._state.board[tr, tc] = np.int8(entry.captured)
        # Restore state fields
        self._state.turn = -self._state.turn
        self._state.zobrist_hash_history.append(entry.prev_hash)
        self._state.halfmove_clock = entry.prev_halfmove
        self._state.king_positions = entry.prev_king_positions
        self._state.move_history.pop()
        # Restore RepetitionState
        self._rep_state = entry.rep_snapshot

    def is_legal(self, move: int) -> bool:
        return is_legal_move(self._state, move)

    def legal_moves(self) -> List[int]:
        return generate_legal_moves(self._state)

    def is_check(self) -> bool:
        return is_in_check(self._state, self._state.turn)

    def result(self) -> str:
        return get_game_result(self._state, self._rep_state)

    def to_fen(self) -> str:
        return to_fen(self._state.board, self._state.turn)

    # ── Read-only properties ────────────────────────────────────────────────

    @property
    def board(self) -> np.ndarray:
        return self._state.board

    @property
    def turn(self) -> int:
        return self._state.turn

    @property
    def move_history(self) -> list:
        return self._state.move_history
```

**Key implementation note for `apply()` RepetitionState update:**
The `prev_state` needed by `RepetitionState.update()` is the pre-move board. Since `apply()` mutates state in-place, take a `self._state.copy()` BEFORE calling `_apply_move`. The update call should be:
```python
prev_state = self._state.copy()
captured = _apply_move(self._state, move)
self._rep_state.update(prev_state, move, self._state)
```

### Pattern 2: Undo Entry Snapshot

**What:** Each undo entry stores everything needed to reverse one move, including a `RepetitionState` snapshot.

**Fields stored per entry:**
```python
@dataclass
class UndoEntry:
    from_sq: int
    to_sq: int
    captured: int       # 0 = no capture
    piece: int          # the moving piece
    prev_hash: int      # zobrist_hash_history value before this move
    prev_halfmove: int
    prev_king_positions: dict[int, int]
    rep_snapshot: RepetitionState  # shallow copy of RepetitionState
```

**Undo restores:**
- Board: `board[from_sq] = piece; board[to_sq] = captured`
- Turn: `state.turn = -state.turn` (flip back)
- Hash: `state.zobrist_hash_history.append(prev_hash)` (appends the pre-move hash, so it now appears twice)
- halfmove_clock: direct restore
- king_positions: direct dict restore
- move_history: `pop()`
- `_rep_state`: `self._rep_state = entry.rep_snapshot`

**Important:** The hash restoration appends the pre-move hash to `zobrist_hash_history`, so after undo the hash appears at positions `[n-2, n-1]` — both equal. This is correct because the position occurred before the undone move. The `check_repetition()` function scans all hashes, so this double-entry correctly prevents false repetition draws caused by undo.

### Pattern 3: pyffish UCI-to-Move Conversion

**What:** pyffish returns legal moves as UCI strings (e.g., `"h2e2"` for column+row notation). These must be converted to the project's 16-bit integer encoding for comparison.

**Conversion approach:**
```python
# UCI: "h2e2" → from_sq=h2, to_sq=e2
# File-to-column: 'a'=0, 'b'=1, ... 'i'=8
# Rank-to-row: '9'=black back rank=0, '1'=red back rank=9
# Xiangqi UCI rank order: '9' is rank 0 (top), '1' is rank 9 (bottom)

def uci_to_sq(uci_sq: str) -> int:
    """Convert UCI square like 'h2' to flat square index 0-89."""
    col = ord(uci_sq[0]) - ord('a')   # 'a'=0 ... 'i'=8
    rank_char = uci_sq[1]
    row = 9 - int(rank_char)          # '9' -> row 0, '1' -> row 9
    return row * 9 + col

def uci_to_move(uci: str) -> int:
    """Convert UCI string like 'h2e2' to 16-bit move integer."""
    from_sq = uci_to_sq(uci[:2])
    to_sq   = uci_to_sq(uci[2:])
    return encode_move(from_sq, to_sq)
```

**pyffish verification flow:**
```python
import pytest
pyffish = pytest.importorskip("pyffish", reason="pyffish not installed")

def test_pyffish_starting_position():
    """Verify all 44 starting-position moves match pyffish."""
    # pyffish legal moves for starting position (red to move)
    pyffish_moves = pyffish.legal_moves("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w")
    engine = XiangqiEngine.starting()
    engine_moves = set(engine.legal_moves())
    pyffish_moves_set = set(uci_to_move(m) for m in pyffish_moves)
    assert engine_moves == pyffish_moves_set, f"Mismatch: {engine_moves ^ pyffish_moves_set}"
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Move legality checking | Custom logic | `legal.is_legal_move()` | Already handles all 7 piece types, face-to-face rule, self-check filter |
| Zobrist hash update | Custom incremental hash | `state.update_hash()` | Correctly XORs removed piece, captured piece, added piece, turn bit |
| Game result detection | Custom if/else tree | `endgame.get_game_result()` | Handles END-01..END-04 with correct priority order |
| Repetition tracking | Custom counter | `RepetitionState` + `update()` | Handles long-check, long-chase, and threefold repetition |
| FEN parsing | Custom parser | `XiangqiState.from_fen()` | Already handles WXF format, rank/row mapping, piece mapping |
| FEN serialization | Custom serializer | `constants.to_fen()` | Already handles board-to-rank encoding, run-length, turn field |

**Key insight:** Every piece of logic needed by the engine already exists in one of the four internal modules. The engine's job is wiring, not computing.

---

## Common Pitfalls

### Pitfall 1: Applying move BEFORE legality check
**What goes wrong:** If `apply()` calls `_apply_move` before checking legality, illegal moves corrupt state.
**How to avoid:** Always call `is_legal_move()` first; raise `ValueError` if False; only then call `_apply_move`.
```python
# Correct order:
if not is_legal_move(self._state, move):
    raise ValueError(f"Illegal move: {move}")
captured = _apply_move(self._state, move)
```

### Pitfall 2: RepetitionState not snapshot on undo
**What goes wrong:** Undoing a move without restoring `_rep_state` causes `result()` to see stale check/chase counts.
**How to avoid:** Store `rep_snapshot` in every undo entry. On `undo()`, restore `self._rep_state = entry.rep_snapshot`.

### Pitfall 3: Zobrist hash double-counting after undo
**What goes wrong:** If undo pops from `zobrist_hash_history` (reducing length), `check_repetition()` sees a gap. If undo appends the pre-move hash, the position appears twice consecutively, which is correct.
**How to avoid:** Always **append** the saved `prev_hash` — this represents the position state before the undone move. The history should now show the position twice (before and after the undone move), which is the correct state.

### Pitfall 4: FEN roundtrip losing information
**What goes wrong:** `to_fen()` produces a 5-field FEN (rank/color/-/0/1) but `from_fen()` only reads the first two fields (board + turn). Any extra fields after the first two are silently ignored by `XiangqiState.from_fen()`.
**How to avoid:** Test roundtrip explicitly: `assert engine.to_fen() == fen` for full FEN strings. For partial FEN, compare first two fields.

### Pitfall 5: `undo()` calling `RepetitionState.reset()` instead of restoring snapshot
**What goes wrong:** `reset()` zeroes all counters, losing the full game history. Only a snapshot restore preserves the correct state.
**How to avoid:** Store a copy of `RepetitionState` as a dataclass in the undo stack; restore by direct assignment `self._rep_state = snapshot`.

### Pitfall 6: `apply()` not creating prev_state copy for RepetitionState
**What goes wrong:** `RepetitionState.update()` needs the pre-move board. If `prev_state` points to the same object as post-move state, the detection is wrong.
**How to avoid:** Call `self._state.copy()` before `_apply_move()`:
```python
prev_state = self._state.copy()
_apply_move(self._state, move)
self._rep_state.update(prev_state, move, self._state)
```

### Pitfall 7: pyffish returns moves in UCI format but engine uses 16-bit integers
**What goes wrong:** Direct set comparison fails because types differ.
**How to avoid:** Always convert pyffish UCI strings to 16-bit integers via `uci_to_move()` before comparing. Verify the column mapping: `a=0, b=1, ..., i=8`. Verify the row mapping: `9=0 (black back), 1=9 (red back)`.

### Pitfall 8: FEN parsing errors not wrapped as ValueError
**What goes wrong:** If `XiangqiState.from_fen()` raises a different exception type (KeyError, IndexError), callers can't catch it uniformly.
**How to avoid:** Wrap in `try/except` and re-raise as `ValueError(f"Invalid FEN: {fen}")`.

---

## Code Examples

### Example: Full engine lifecycle

```python
# Source: src/xiangqi/engine/engine.py (new)
from src.xiangqi.engine.engine import XiangqiEngine

# Start from standard position
eng = XiangqiEngine.starting()
assert eng.turn == +1
assert len(eng.legal_moves()) == 44
assert eng.result() == 'IN_PROGRESS'

# Apply a known move (red soldier at col 4 advances from row 6 to row 5)
# Soldier at (6,4) = sq 6*9+4 = 58; advances to (5,4) = sq 5*9+4 = 49
move = encode_move(58, 49)
captured = eng.apply(move)
assert captured == 0
assert eng.turn == -1
assert eng.result() == 'IN_PROGRESS'

# Undo
eng.undo()
assert eng.turn == +1
assert eng.result() == 'IN_PROGRESS'

# FEN roundtrip
eng2 = XiangqiEngine.from_fen(eng.to_fen())
assert eng2.legal_moves() == eng.legal_moves()
```

### Example: pyffish cross-validation

```python
# Source: tests/test_pyffish.py (new)
import pytest

pyffish = pytest.importorskip("pyffish")

from src.xiangqi.engine.engine import XiangqiEngine
from src.xiangqi.engine.types import encode_move

STARTING_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w"

def uci_sq_to_flat(uci_sq: str) -> int:
    col = ord(uci_sq[0]) - ord('a')
    row = 9 - int(uci_sq[1])
    return row * 9 + col

def uci_to_move(uci: str) -> int:
    return encode_move(uci_sq_to_flat(uci[:2]), uci_sq_to_flat(uci[2:]))

def test_pyffish_starting_position():
    """All 44 starting-position legal moves match pyffish."""
    pyffish_moves = pyffish.legal_moves(STARTING_FEN)
    eng = XiangqiEngine.starting()
    engine_moves = set(eng.legal_moves())
    pf_moves = set(uci_to_move(m) for m in pyffish_moves)

    only_engine = engine_moves - pf_moves
    only_pyffish = pf_moves - engine_moves

    assert not only_engine, f"Moves in engine but not pyffish: {only_engine}"
    assert not only_pyffish, f"Moves in pyffish but not engine: {only_pyffish}"
    assert len(engine_moves) == 44, f"Expected 44, got {len(engine_moves)}"
```

### Example: Engine API test (test_api.py)

```python
# Source: tests/test_api.py (new)
import pytest
import numpy as np

from src.xiangqi.engine.engine import XiangqiEngine
from src.xiangqi.engine.types import Piece, encode_move

class TestXiangqiEngineAPI:
    def test_starting_position(self):
        eng = XiangqiEngine.starting()
        assert eng.turn == +1
        assert eng.board.shape == (10, 9)
        assert len(eng.legal_moves()) == 44

    def test_apply_updates_state(self):
        eng = XiangqiEngine.starting()
        eng.reset()
        assert len(eng.move_history) == 0
        # Red pawn at (6,4) advances: sq 58 -> 49
        move = encode_move(58, 49)
        captured = eng.apply(move)
        assert captured == 0
        assert eng.turn == -1
        assert len(eng.move_history) == 1

    def test_illegal_move_raises(self):
        eng = XiangqiEngine.starting()
        with pytest.raises(ValueError):
            eng.apply(0)  # invalid move encoding

    def test_undo_empty_raises(self):
        eng = XiangqiEngine.starting()
        with pytest.raises(IndexError, match="nothing to undo"):
            eng.undo()

    def test_undo_restores_state(self):
        eng = XiangqiEngine.starting()
        move = encode_move(58, 49)
        eng.apply(move)
        eng.undo()
        assert eng.turn == +1
        assert len(eng.move_history) == 0

    def test_fen_roundtrip(self):
        eng = XiangqiEngine.starting()
        fen = eng.to_fen()
        eng2 = XiangqiEngine.from_fen(fen)
        assert eng2.to_fen() == fen
        assert eng2.legal_moves() == eng.legal_moves()

    def test_invalid_fen_raises(self):
        with pytest.raises(ValueError, match="Invalid FEN"):
            XiangqiEngine.from_fen("not a valid fen string")

    def test_is_check(self):
        # Set up a check position
        eng = XiangqiEngine.from_fen("... w ...")  # TODO: actual check FEN
        assert eng.is_check() == True

    def test_result_checkmate(self):
        # Set up checkmate position
        eng = XiangqiEngine.from_fen("... w ...")  # TODO: actual checkmate FEN
        assert eng.result() in ('RED_WINS', 'BLACK_WINS')
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Multiple public classes (XiangqiState, standalone functions) | Single `XiangqiEngine` facade | Phase 4 | External callers get one type to import |
| FEN in standalone module | FEN on Engine class | Phase 4 decision | Less indirection; factory methods feel natural |
| RepetitionState inside XiangqiState | RepetitionState owned by Engine | Phase 3 decision | Cleaner separation of concerns |
| No undo mechanism | Incremental undo stack with full snapshots | Phase 4 | Enables AI search algorithms that need move unmake |

**Deprecated/outdated:**
- `src/xiangqi/engine/rules.py` — exists from Phase 2; `flying_general_violation` moved to `legal.py`; `rules.py` may be redundant or contain face-to-face checks. Confirm which functions in `rules.py` are still needed vs. already covered by `legal.py`.

---

## Open Questions

1. **Is `src/xiangqi/engine/rules.py` still needed after Phase 2?**
   - What we know: Phase 2 created `rules.py` for face-to-face general and flying-general-violation checks. Phase 2 context says `flying_general_violation` now lives in `legal.py`. The `rules.py` module may be empty or contain overlapping logic.
   - What's unclear: Does `rules.py` export any symbols still referenced elsewhere?
   - Recommendation: Check if `rules.py` is imported anywhere (grep for `from .rules import` or `from xiangqi.engine.rules import`). If nothing imports it, mark it deprecated in Phase 4 cleanup or remove it.

2. **Should `RepetitionState.copy()` be a proper method?**
   - What we know: The undo snapshot uses `RepetitionState(...)` constructor to copy fields. `RepetitionState` is a dataclass with only primitive/JSON-compatible fields, so shallow copies of lists are needed for `chase_seq`.
   - What's unclear: A `copy()` method on `RepetitionState` would be cleaner.
   - Recommendation: Add a `copy()` method to `RepetitionState` in Phase 4 as a small hygiene improvement (not a separate Phase 2.2 task). This avoids open-coding the field copying in the engine.

3. **TEST-01 perft through engine API vs. direct calls?**
   - What we know: `test_perft.py` already exists and calls `XiangqiState.starting()`, `generate_legal_moves`, etc. directly. The CONTEXT says new `test_api.py` covers API integration.
   - What's unclear: Should `test_perft.py` be rewritten to use the engine API, or kept using direct module calls for performance?
   - Recommendation: Keep `test_perft.py` using direct calls (it benchmarks move generation performance and doesn't need engine wrapping). Add a thin `test_engine_perft.py` that uses engine API to verify the wrapper adds no overhead.

4. **Performance target API-04: how to measure?**
   - What we know: `legal.generate_legal_moves()` is the bottleneck; perft(3) = 79,666 nodes already runs in existing tests. The API-04 target is `< 10ms/position` for legal moves and `< 100ms` for full evaluation.
   - What's unclear: What constitutes "full evaluation"? Is it `result()` call or a full perft to depth N?
   - Recommendation: Implement as `pytest` timed tests using `time.perf_counter()`:
     ```python
     def test_legal_moves_performance():
         eng = XiangqiEngine.starting()
         start = time.perf_counter()
         moves = eng.legal_moves()
         elapsed = (time.perf_counter() - start) * 1000
         assert elapsed < 10, f"legal_moves took {elapsed:.2f}ms > 10ms"
     ```

---

## Validation Architecture

> Included because `workflow.nyquist_validation` key is absent from `.planning/config.json` (treating as enabled).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 8.0 |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `conda activate xqrl && pytest tests/test_api.py -x -q` |
| Full suite command | `conda activate xqrl && pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | All 7 methods exist and return correct types | unit | `pytest tests/test_api.py::TestXiangqiEngineAPI -x` | NEW |
| API-02 | apply() updates board/turn/move_history/halfmove_clock | unit | `pytest tests/test_api.py::TestStateUpdate -x` | NEW |
| API-03 | from_fen/to_fen roundtrip | unit | `pytest tests/test_api.py::TestFEN -x` | NEW |
| API-04 | legal_moves < 10ms, result() < 100ms | performance | `pytest tests/test_api.py::TestPerformance -x` | NEW |
| TEST-01 | Perft depth 1-3 = 44/1920/79666 through engine | unit | `pytest tests/test_api.py::TestPerft -x` | NEW (or test_perft.py update) |
| TEST-02 | pyffish cross-validation (44 starting moves) | integration | `pytest tests/test_pyffish.py -x` | NEW |
| TEST-03 | Checkmate/stalemate/in-check positions | unit | `pytest tests/test_api.py::TestBoundaryPositions -x` | NEW |
| TEST-04 | Long-check draw, repetition draw, long-chase loss | unit | `pytest tests/test_api.py::TestSpecialRules -x` | NEW |

### Sampling Rate
- **Per task commit:** `conda activate xqrl && pytest tests/test_api.py -x -q`
- **Per wave merge:** `conda activate xqrl && pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `src/xiangqi/engine/engine.py` — `XiangqiEngine` class (covers API-01 through API-04)
- [ ] `tests/test_api.py` — full API integration suite (covers API-01/02/03/04, TEST-01/03/04)
- [ ] `tests/test_pyffish.py` — pyffish cross-validation (covers TEST-02)
- [ ] `src/xiangqi/engine/repetition.py` — add `RepetitionState.copy()` method (hygiene, supports clean undo snapshots)

*(All test infrastructure (pytest, conftest.py) already exists.)*

---

## Sources

### Primary (HIGH confidence)
- `src/xiangqi/engine/state.py` — XiangqiState with from_fen(), copy(), king_positions, zobrist_hash_history
- `src/xiangqi/engine/legal.py` — apply_move(), is_legal_move(), generate_legal_moves(), is_in_check(), flying_general_violation()
- `src/xiangqi/engine/endgame.py` — get_game_result() with lazy repetition import
- `src/xiangqi/engine/repetition.py` — RepetitionState.update(), check_repetition(), check_long_check(), check_long_chase()
- `src/xiangqi/engine/constants.py` — STARTING_FEN, from_fen(), to_fen()
- `src/xiangqi/engine/types.py` — Piece IntEnum, encode_move/decode_move
- `tests/test_perft.py` — CPW-verified reference values (44, 1920, 79666, 3290240)

### Secondary (MEDIUM confidence)
- pyffish GitHub / PyPI — UCI string format for xiangqi moves (verified via WebSearch)
- ChessProgramming.org Perft Results — CPW-verified Xiangqi perft values

### Tertiary (LOW confidence)
- None — all critical facts verified against existing source code

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all modules exist and are fully read from source
- Architecture: HIGH — facade pattern with locked decisions; all 7 methods map to existing functions
- Pitfalls: HIGH — each pitfall traced to a specific source-code detail

**Research date:** 2026-03-20
**Valid until:** 2026-04-19 (stable domain; no fast-moving libraries involved)
