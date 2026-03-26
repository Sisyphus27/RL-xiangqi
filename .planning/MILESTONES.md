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

## v0.2 PyQt6 UI + RandomAI + AI Interface (Shipped: 2026-03-26)

**Phases:** 4 phases (05-08) | **Plans:** 22+ | **Commits:** 112 (since v0.2 start)
**Files changed:** 29 | **Lines added:** 2,784 | **Timeline:** 4 days

**Key accomplishments:**

- **PyQt6 board rendering** — QGraphicsView 9×10 grid, river gap, palace diagonals in center columns, 32 pieces with Chinese chars, responsive scaling
- **Turn-aware piece interaction** — gold selection ring, legal move dots, mapToScene() coordinate conversion, click-to-move
- **AIPlayer ABC + EngineSnapshot** — frozen dataclass with thread-safe deep copy, AIPlayer.suggest_move() contract
- **RandomAI** — black side AI returning random legal moves via EngineSnapshot.legal_moves
- **GameController orchestration** — QThread AI worker, status bar "AI 思考中..." indicator, QMessageBox game-over popup
- **Game control toolbar** — New Game + Undo buttons, Ctrl+N/Ctrl+Z shortcuts, double-step undo for human+AI pair
- **Random side assignment** — human randomly plays Red or Black each new game

**Known gaps:** Nyquist VALIDATION.md not finalized; phase-level SUMMARY.md missing for 07/08

---
