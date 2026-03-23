# Milestones

## v0.1 Core Engine (Shipped: 2026-03-21)

**Phases:** 7 phases (01-04, 02.1, 02.2, 04.1) | **Plans:** 11 | **Commits:** 93
**Files changed:** 93 | **Lines added:** 22,774 | **Timeline:** 2 days

**Key accomplishments:**

- **Board & state foundations** — Piece IntEnum (Chinese chars), 16-bit move encoding, XiangqiState dataclass with Zobrist hashing, WXF FEN parser, ndarray boundary masks
- **Full move generation (CPW-verified)** — All 7 piece types; perft(1)=44, (2)=1,920, (3)=79,666, (4)=3,290,240 all match CPW reference values
- **Endgame rule engine** — checkmate, stalemate (kunbi=loss), threefold repetition, long check, long chase — 30 new tests, 132 passing
- **XiangqiEngine public API facade** — apply/undo/legal_moves/is_legal/result + full FEN roundtrip — 171 tests passing
- **Geometry pre-validation with 58x perf gain** — `_is_valid_geometry()` before board copy; `legal_moves()` 29ms → 0.5ms
- **Corrected checkmate test geometry** — Redesigned stalemate test board; 102 tests passing

**Known gaps:** pyffish cross-validation skipped (stockfish unavailable on Windows); END-01/02/03/04 checkboxes not updated in archived REQUIREMENTS.md

---
