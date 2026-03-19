# Xiangqi (Chinese Chess) Engine Libraries & Tools Research

**Date:** 2026-03-19
**Purpose:** Research for RL-xiangqi project (Chinese Chess AI engine with RL)

---

## 1. Existing Python Xiangqi Engines / Libraries

### 1.1 Pure-Python Libraries

#### `xiangqigame` — C++ Core + Python Wrapper (Pybind11)
- **Repo:** [github.com/duanegoodner/xiangqigame](https://github.com/duanegoodner/xiangqigame)
- **Architecture:** C++ AI engine (Minimax + Alpha-Beta + Zobrist transposition table) wrapped in Python via **Pybind11**.
- **Python layer:** CLI, text-based board display, data logging.
- **Key lesson:** Keep move-generation core in C++, expose via Python for RL/UI integration.

#### `chinese_chess` (xiokuai) — Python + C++
- **Repo:** [github.com/xiokuai/chinese_chess](https://github.com/xiokuai/chinese_chess)
- Includes endgame challenge mode with preset library; supports test mode (AI vs AI).

#### Simple Xiangqi Library (unverified name, ~54 GitHub stars)
- Pure Python, updated November 2025. Covers move generation, piece placement, check/checkmate/draw detection.
- Useful as a reference for Python-native board logic, though likely slow for engine use.

### 1.2 Neural-Network-Based Engines

#### `ElephantArt` (CGLemon)
- **Repo:** [github.com/CGLemon/ElephantArt](https://github.com/CGLemon/ElephantArt)
- CNN + Monte Carlo Tree Search (MCTS) engine; supports **UCCI protocol**.
- No BLAS dependency required (though BLAS acceleration is optional).
- Directly relevant as an NN architecture reference for this project.

#### `Wukong-Xiangqi` (maksimKorzh / Code Monkey King)
- **Repo:** [github.com/maksimKorzh/wukong-xiangqi](https://github.com/maksimKorzh/wukong-xiangqi)
- Didactic/engine-for-learning project. Less powerful but clean code structure suitable as a tutorial reference.

#### `leela-xiangqi / lx0`
- **Repo:** [github.com/leela-xiangqi/lx0](https://github.com/leela-xiangqi/lx0)
- Lc0 adapted for Xiangqi — neural network UCI engine. Build system uses Python + Ninja.

### 1.3 Key Recommendation

> **Do not implement move generation from scratch in pure Python.** Use one of these strategies:
> 1. Implement move generation in C++ with Pybind11 wrapper (reference `xiangqigame`).
> 2. Use **Fairy-Stockfish / pyffish** for all move validation (see Section 4) — avoid reinventing the wheel.

---

## 2. Chinese Chess Notation: Formats & Standards

Reference: [WXF File Format Specification](https://www.wxf-xiangqi.org/images/computer-xiangqi/chinese-chess-file-format.pdf)
Reference: [FEN for Xiangqi Specification](https://www.wxf-xiangqi.org/images/computer-xiangqi/fen-for-xiangqi-chinese-chess.pdf)

### 2.1 FEN for Xiangqi

The 6-field FEN standard adapted for Chinese chess:

```
rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1
```

| Field | Meaning | Notes |
|-------|---------|-------|
| 1 | Piece placement | Rank 9 first, rank 1 last; files a–i left to right from Red's view |
| 2 | Active color | `w` = Red to move, `b` = Black to move |
| 3 | Castling | Not used (always `-`) |
| 4 | En passant | Not used (always `-`) |
| 5 | Halfmove clock | Ply count since last pawn move / capture |
| 6 | Fullmove number | Increments after Black's move |

**Piece codes (WXF standard):**

| Piece | Red (uppercase) | Black (lowercase) |
|-------|-----------------|-------------------|
| General | K | k |
| Advisor | A | a |
| Elephant | E | e |
| Chariot (Rook) | R | r |
| Horse | H | h |
| Cannon | C | c |
| Soldier (Pawn) | P | p |

**Board layout (90 intersection points):** 9 files × 10 ranks. Elephant and soldier movement is restricted by the River (rank 5). General and Advisor confined to the Palace (3×3).

### 2.2 Move Notation Formats

Four formats defined in the WXF standard:

| Format | Example | Description |
|--------|---------|-------------|
| **ICCS** | `H2-E2` | e.g., Horse from column H rank 2 to column E rank 2 |
| **AXF** | `C2=5` | Conventional notation with annotation symbols |
| **LALG** | `Ch2-e2` | Long algebraic — `[piece]origin-dest` |
| **SALG** | `Che2` | Short algebraic — `[piece abbreviation][destination]` |

**WXF 4-character notation:**
`[piece][from-file][operator][to-file-or-rank]`
- `+` = forward, `-` = backward, `=` = sideways, diagonal = new file number

Annotation symbols (`!`, `?`, `!!`, `++`, etc.) may follow moves in AXF/LALG/SALG.

### 2.3 XQF / ICCD File Format

- **XQF** is a binary/game-record format used by Xiangqi software (XQ = Xiangqi).
- **ICCD** is a text-based format on the International Chinese Chess Server.
- Both are used for storing complete game records including move history and metadata.
- Recommendation: implement **FEN parsing/serialization first**, as it is text-based and simpler; XQF support can be added later via a parser library.

### 2.4 Implementation Notes

- ICCS coordinates: files `a`–`i`, ranks `1`–`9` or `0`–`9` (note: not uniform, some systems use 0–9).
- FEN rank order goes from rank 9 down to rank 1 (top to bottom from Red's perspective).
- No castling or en passant in Xiangqi — fields 3 and 4 are always `-`.
- Stalemate = win for the player with the move (unlike Western chess).
- Perpetual check is a loss for the checking side.

---

## 3. Opening Books & Endgame Tablebases

### 3.1 Opening Books

- **Xiangqi Cloud Database (CDB):** Massive opening knowledge database built by analyzing positions with engines (not from game results). Covers most popular opening lines. Available via API.
- **Polyglot format** (`.bin` opening book): used by Western chess engines. May be adaptable for Xiangqi; Fairy-Stockfish/pyffish supports this.
- **ECCO opening classification:** Categorizes Xiangqi openings by opening system (e.g., Central Cannon, Fan Gong Pawn, etc.).
- For RL training: opening books are less critical — self-play will generate opening diversity organically.

### 3.2 Endgame Tablebases

- **FelicityEgtb** (MIT licensed): Xiangqi EGTB generator. One release reached 7.5 GB covering endgames where one side has up to 2 attackers vs. no attackers (armless). See [github.com/aanhashi/FelicityEgtb](https://github.com/aanhashi/FelicityEgtb).
- **New "Undetermined EGTB" design:** Compresses by omitting piece positions at specific squares with minimal effect, achieving ~15.5% size reduction vs. traditional EGTBs.
- **Syzygy-style EGTBs** (`.rtbw`/`.rtbz`) — not standard for Xiangqi; Fairy-Stockfish uses its own format.
- **Practical note:** For RL purposes, EGTBs are primarily useful as evaluation targets (supervision) for the value head, not as a primary data source.

### 3.3 Resources

| Resource | Type | License | URL |
|----------|------|---------|-----|
| Xiangqi CDB | Opening book | Unknown | xiangqi-db.com |
| FelicityEgtb | EGTB generator | MIT | github.com/aanhashi/FelicityEgtb |
| pyffish | EGTB support | GPL | pypi.org/project/pyffish |

---

## 4. UCI-Compatible Xiangqi Engines (Evaluation & Benchmarking)

### 4.1 Engines

#### Pikafish
- **URL:** [github.com/official-pikafish/Pikafish](https://github.com/official-pikafish/Pikafish)
- Strongest open-source Xiangqi engine. Derived from Stockfish. NNUE evaluation built-in.
- Protocol: **UCI** (not UCCI, but works with UCI-compatible GUIs).
- `bench 16 1 13 default depth` — standard benchmark command.
- Provides `nps` (nodes per second), `depth`, `score` metrics.

#### Fairy-Stockfish
- **URL:** [github.com/fairy-stockfish/Fairy-Stockfish](https://github.com/fairy-stockfish/Fairy-Stockfish)
- Multi-variant engine (Xiangqi, Janggi, Makruk, and many fairy variants).
- Protocols: UCI, UCCI, USI, CECP/XBoard.
- **Has built-in NNUE networks** for Xiangqi, Janggi, and Makruk.
- `bench 16 1 13 default depth mixed` — benchmark command.
- This is the **most Python-friendly option** via `pyffish` (see below).

#### lx0 (Leela Xiangqi)
- Lc0 ported to Xiangqi. Neural-network-only evaluation.
- Build uses Python + Ninja. Less mature than Pikafish.

### 4.2 Python Bindings

#### `pyffish` — Fairy-Stockfish Python Binding
- **URL:** [pypi.org/project/pyffish](https://pypi.org/project/pyffish/)
- **Install:** `pip install pyffish`
- Provides: `sf.legal_moves()`, `sf.get_fen()`, `sf.is_game_over()`, `sf.start_fen()`, SAN generation.
- Very fast (C++ backend).
- Works for Xiangqi and all Fairy-Stockfish variants.

```python
import pyffish as sf

# Get legal moves from starting position
moves = sf.legal_moves("xiangqi", sf.start_fen("xiangqi"), [])
print(moves)  # ['h3e3', 'h3+i5', ...]

# Make a move
new_fen = sf.get_fen("xiangqi", sf.start_fen("xiangqi"), ["h3e3"])

# Check game end
sf.is_game_over("xiangqi", new_fen, [])
```

### 4.3 Python Communication with UCI Engines

The `python-chess` library (`chess.engine` module) can communicate with any UCI engine via subprocess:

```python
import chess.engine

engine = chess.engine.SimpleEngine.popen_uci("/path/to/pikafish")
result = engine.analyze(board, chess.engine.Limit(depth=20))
print(result.info["score"], result.info["pv"])
engine.quit()
```

For Xiangqi, replace `chess` with a custom wrapper or use **Fairy-Stockfish directly** via `pyffish` for best results.

### 4.4 Benchmarking Recommendations

| Engine | Best For | NNUE | UCI/UCCI |
|--------|----------|------|----------|
| **Pikafish** | Strongest play, evaluation target | Yes | UCI |
| **Fairy-Stockfish** | Multi-variant, Python integration | Yes | Both |
| **lx0** | NN-based RL reference | Yes (LC0) | UCI |

---

## 5. PyQt6 for Chess UI — Specific Components

### 5.1 Framework: Graphics View Architecture

PyQt6's **QGraphicsView** is the standard approach for chess UIs:

| Component | Role |
|-----------|------|
| `QGraphicsScene` | Holds all board items; acts as the model |
| `QGraphicsView` | Renders the scene; handles scrolling, zooming, transformations |
| `QGraphicsItem` | Base class for pieces, squares, highlights |

For Xiangqi (9×10 board), a `QGraphicsRectItem` grid with `QGraphicsSvgItem` pieces is clean and performant.

### 5.2 Key Implementation Details

**Board:**
- 10 rows × 9 columns of intersection points (not cells like Western chess).
- River (horizontal band) at rank 5 — affects Elephant and Soldier rendering.
- Palace overlay — a 3×3 box at center of each side (ranks 1–3 for Red, 8–10 for Black).
- Diagonal intersections in palace (Advisors move diagonally within these).

**Piece Display:**
- `QGraphicsSvgItem` for scalable SVG piece images (preferred over pixmaps).
- Set `QGraphicsItem.GraphicsItemFlag.ItemIsMovable` on piece items for drag-and-drop.
- Square highlighting: `QGraphicsRectItem` with semi-transparent fill, toggled on click.

**Interaction:**
- `mousePressEvent` / `mouseMoveEvent` on `QGraphicsView` to detect piece pickup.
- `mouseReleaseEvent` to drop piece and validate move.
- Alternative: override `itemChange()` on pieces to handle snap-to-grid.

**Rendering:**
- Use `QPainter` on `QGraphicsView.drawBackground()` for the board lines (river, palace diagonals).
- Or render the board as a background `QGraphicsPixmapItem`.
- Support rotation (`QTransform.rotate(180)`) for Black's perspective.

**State Management:**
- Keep a `BoardModel` class independent of the UI (pure Python, no PyQt).
- The `QGraphicsScene` reads/writes to this model.
- Connect engine moves (from background thread) to animated piece movement via `QPropertyAnimation` or direct `setPos()`.

**Known Caveat:**
- One developer reported PyQt6 visual distortion when dragging pieces (clipping errors); PyQt5 is more stable for complex drag-and-drop. Consider **PyQt5 for the GUI layer** while keeping engine/RL code Python-native.

### 5.3 Recommended PyQt6 Components

```python
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QObject
```

- `QGraphicsScene` / `QGraphicsView` — board rendering.
- `QGraphicsSvgItem` — Xiangqi piece SVGs.
- `QGraphicsRectItem` — move highlights, legal-move indicators.
- `QGraphicsLineItem` — board lines (river, palace borders).
- `QGraphicsTextItem` — coordinate labels (optional).
- `QTimer` — for game clock / animation sequencing.
- `QThread` / `QObject.moveToThread` — for running the engine in a background thread (critical: never block the UI thread with search).
- `QDialog` — engine settings, game info, new game setup.

---

## 6. PyTorch Integration Patterns for Neural Networks

### 6.1 AlphaZero-Style Architecture (Primary Pattern)

The standard pattern for NN-based Xiangqi RL, used by ElephantArt, lx0, LunaChess, and others:

**Input:** Board state (piece positions encoded as feature planes).
**Output:** Dual-head network — policy `pθ(a|s)` and value `vθ(s) ∈ [-1, +1]`.

```
Input (9×10 board encoded)
  → Conv2d (many channels)
  → ×N Residual Blocks (Conv + BN + ReLU + Conv + BN + Add + ReLU)
  → Policy Head: Conv + BN + LogSoftmax → 90 policy outputs (one per intersection × piece type)
  → Value Head: Conv + BN + ReLU + Dense(1) + tanh → scalar value
```

### 6.2 MCTS Integration

For each turn, run N simulations:
1. From current state `s`, traverse/search tree using **PUCT** (similar to MCTS with NN prior):
   - `PUCT(s, a) = Q(s,a) + P(s,a) × U_exploration`
   - `Q(s,a)` from value network; `P(s,a)` from policy network.
2. When reaching a leaf, expand it and evaluate with the NN.
3. Backpropagate the value up the tree.
4. After N simulations, select the move with the highest visit count (not highest value).

**Training example at each step:** `(state, improved_policy, game_outcome)`.

### 6.3 Training Pipeline

```
1. Self-play (MCTS) → generate (state, π, z) tuples
2. Shuffle and batch the data
3. PyTorch training step:
   loss = (z - vθ(s))² + πᵀ log(pθ(s))  [value loss + policy loss]
4. Evaluate new net vs old net (SPRT or fixed games)
5. If new net is better → replace old net; else keep old
6. Repeat
```

### 6.4 Board Encoding for Xiangqi

| Feature Plane | Description |
|---|---|
| Red pieces (7 types) | 7 binary planes |
| Black pieces (7 types) | 7 binary planes |
| Turn indicator | 1 plane (all 0 or all 1) |
| Repetition count | 1–3 planes (for history) |
| River / Palace | Static feature planes |

Total input channels: ~16–20 for a basic encoding.

### 6.5 Speed Considerations

- Use batched inference (multiple positions per GPU forward pass) during self-play.
- Use `torch.no_grad()` during self-play (no gradient computation).
- Consider `torch.compile()` (PyTorch 2.0+) for significant speedups.
- For the initial prototype, CPU inference is acceptable; GPU dramatically speeds up MCTS batch evaluation.

### 6.6 Alternative: NNUE-Style Evaluation

Rather than full AlphaZero-style self-play, a simpler approach is to:
1. Use a handcrafted evaluation function (piece values + positional terms).
2. Train a small NNUE network (2–3 hidden layers) to predict the handcrafted evaluation.
3. Integrate into the alpha-beta search (like Pikafish/Fairy-Stockfish).

This is more feasible for a first milestone (v0.1) than full AlphaZero training.

---

## 7. Testing Frameworks for Chess Engines

### 7.1 Perft (Performance Test) — Move Generation Validation

**What it does:** Recursively enumerate all leaf nodes at depth N and count them. Compare against known correct counts.

**Why it works:** If the counts match known correct values, move generation, make/unmake, and legality checking are all correct. Any mismatch pinpoints a specific bug.

**Standard perft counts (Xiangqi starting position — approximate):**
| Depth | Approximate Nodes |
|-------|-------------------|
| 1 | ~44 legal moves |
| 2 | ~1,900 |
| 3 | ~84,000 |
| 4 | ~3,700,000 |
| 5 | ~160,000,000 |

> Note: Xiangqi perft counts are smaller than Western chess due to the narrower board (9 vs. 8 files) and restricted piece movement.

**Python perft implementation pattern:**

```python
def perft(board, depth):
    if depth == 0:
        return 1
    count = 0
    for move in board.legal_moves:
        board.push(move)
        if not board.is_check():
            count += perft(board, depth - 1)
        board.pop()
    return count

def divide(board, depth):
    """Divide shows per-move counts, narrowing down bugs."""
    for move in board.legal_moves:
        board.push(move)
        count = perft(board, depth - 1)
        board.pop()
        print(f"{move}: {count}")
```

### 7.2 Division Testing (Perft Divide)

`divide(depth)` outputs the perft count for each individual move. Comparing against known correct division tables isolates which move family has a bug. This is the primary debugging tool for move generation.

### 7.3 Test Suites

| Test Type | Purpose | Tools |
|-----------|---------|-------|
| **Perft** | Move generation correctness | Custom Python + pyffish reference |
| **Move legality** | Check/checkmate/stalemate/draw detection | Reference engine (pyffish) |
| **Move generation** | All legal moves per position | Reference vs. own engine |
| **Engine通信** | UCI/UCCI command/response | python-chess `chess.engine` |
| **SPRT testing** | Search strength regression detection | python-chess + custom runner |

### 7.4 Recommended Testing Stack

- **`pytest`** — test discovery, fixtures, parametrization.
- **`hypothesis`** (optional) — property-based testing for move validation (generate random legal positions, verify consistency with pyffish).
- **`pyffish`** as the reference engine for all correctness tests.
- **`time.perf_counter()`** for microbenchmarking perft speed.

### 7.5 Critical Xiangqi-Specific Tests

- **Flying General rule:** Kings cannot face each other with no intervening piece.
- **Elephant cannot cross river.**
- **Advisor confined to palace** (5 diagonal positions only).
- **Cannon capture:** must jump exactly one piece; cannot jump zero or more than one.
- **Soldier crossed-river:** lateral movement enabled only after crossing the river.
- **Horse blocked leg:** horse cannot move if the orthogonally adjacent square is occupied.
- **Perpetual check detection:** engine should not get stuck in infinite check loops.
- **Stalemate = loss**, not draw.

---

## 8. Potential Pitfalls in Python Chess Engine Development

### 8.1 Speed (The #1 Problem)

- Pure Python move generation is ~100–1000× slower than C++.
- Alpha-beta search in pure Python at depth >6 becomes prohibitively slow for Xiangqi.
- **Mitigation:** Keep the hot path (move generation, make/unmake, hash lookup) in C++; expose via Pybind11. Use Python only for RL logic, training loop, and UI.

### 8.2 Repetition / Draw Rules

- **Xiangqi 3-fold repetition = loss** (not a draw, unlike Western chess).
- Many engines get this wrong: they write hash keys into the repetition table only after verifying the position is legal, but the key must be written before generating moves.
- The halfmove clock (for 50-move rule) must be incremented on every non-capture, non-pawn move.

### 8.3 Make/Unmake Symmetry Bugs

- When pushing a move, all piece state changes must be perfectly reversed on pop. A common bug is forgetting to restore castling rights, en passant state, or halfmove clock.
- In Xiangqi: no castling, but palace/confinement state tracking can be error-prone.

### 8.4 Zobrist Hashing — Key Collisions

- Use a 64-bit hash. Probability of collision is negligible with proper random key generation.
- Key must be updated on every make/unmake — not recomputed from scratch each time (expensive).
- Verify hash consistency between Python and C++ layers if using Pybind11.

### 8.5 Search Bugs

- **Horizon effect:** Search may make desperate sacrifices just past the depth horizon.
- **Null move pruning** — risky in Xiangqi due to its tactical nature; disable for initial implementation.
- **Late move reductions (LMR):** Same risk; start simple (no LMR) and add only with test coverage.
- **Aspiration windows:** Start with a wide window, narrow after confirming the score is stable.

### 8.6 Piece Movement Bugs (Xiangqi-Specific)

| Piece | Common Bug |
|-------|-----------|
| Horse | Blocking piece check is one step away (not two like knight in chess) |
| Cannon | Must "jump" exactly 1 piece when capturing; 0 or >1 is illegal |
| Elephant | Diagonal movement is exactly 2 points; blocked by any piece at midpoint |
| Advisor | Only 5 legal squares in palace |
| Soldier | No lateral move before crossing river |

### 8.7 Transposition Table

- Store depth, score, flag (EXACT/LOWER/UPPER), and best move.
- When overwriting, use a depth-preferred replacement strategy (don't overwrite a deeper entry with a shallower one).
- The TT entry's best move should be searched first (highest impact move ordering gain — ~75% of cutoffs in Stockfish come from the TT move).

### 8.8 Endgame Boundary Conditions

- Engines often lack awareness of checkmate distance (mate distance pruning) and stalemate = loss rules near the endgame.
- Add mate distance pruning carefully: it can produce false mates if not exact.

---

## 9. Best Practices from Western Chess Engine Development

### 9.1 Board Representation

- **Bitboard vs. 0x88 / 10×9 array:** Western chess uses bitboards (64-bit). For Xiangqi, the 10×9 board fits well in a 90-element array (0-indexed, [0..89]). The **0x88 trick** is well-suited for Xiangqi's board — adapt the standard 0x88 offset checks from Western chess implementations.
- Fairy-Stockfish uses Stockfish's悠然board representation adapted for the 9×10 board; pikafish inherits Stockfish's NNUE/bitboard architecture.

### 9.2 Alpha-Beta with Iterative Deepening

```
for depth in range(1, max_depth + 1):
    score = alpha_beta(state, depth, alpha, beta, True)
    # Best move from this iteration becomes first move for next iteration
    # Store best move in transposition table
```

Iterative deepening: gives a best move at any time, improves move ordering for the next iteration.

### 9.3 Principal Variation Search (PVS)

PVS is a small modification to alpha-beta:
- After finding a PV move at a node, search it with a zero-width window `[alpha, alpha+1]`.
- If it fails high, re-search with the full window.
- Significantly reduces nodes searched in the PV.

### 9.4 Move Ordering (Priority Order)

1. **Transposition table best move** (highest impact — ~75% of cutoffs).
2. **Captures ordered by MVV-LVA** (Most Valuable Victim – Least Valuable Aggressor).
3. **Killer moves** (quiet moves that caused cutoffs at the same depth).
4. **History heuristic** (long-term move effectiveness score).
5. **Non-captures** ordered by history score.

### 9.5 Evaluation Function

Start simple:
- **Material values:** Chariot=9, Horse=4/4.5, Cannon=4.5, Advisor=2, Elephant=2, Soldier=1 (crossed river=2).
- **Positional terms:** Piece-square tables (PST), king safety, mobility, river/central control.

Advanced (NNUE):
- Use a 2–3 layer fully connected network on top of the board features.
- Train via supervised learning against Pikafish/Fairy-Stockfish evaluations.
- Full AlphaZero training can come in v0.2+.

### 9.6 Lazy SMP (Shared-Memory Parallelism)

- Multiple threads search independently with minimal synchronization.
- Only the transposition table is shared (requires careful locking or lockless design).
- Use `threading` or `multiprocessing` in Python for the RL/self-play workers; for the C++ engine core, use C++ threads.
- The Python RL training loop naturally parallelizes across CPU cores for self-play game generation.

### 9.7 Development Workflow

```
1. Move generation (C++) → Perft tests pass
2. Alpha-beta search (C++) → Plays legal moves
3. Basic evaluation (C++) → Plays somewhat sensibly
4. TT + move ordering (C++) → Significant strength boost
5. PyTorch NN value head (Python) → Integrate into C++ search via FEN eval
6. Self-play RL loop (Python) → Train policy
7. GUI integration (PyQt6) → Playable game
```

### 9.8 Sources & References

| Topic | Reference |
|-------|-----------|
| FEN / WXF notation specs | [wxf-xiangqi.org](https://www.wxf-xiangqi.org/images/computer-xiangqi/chinese-chess-file-format.pdf) |
| UCCI protocol | [xqbase.com/protocol/cchess_ucci.htm](http://www.xqbase.com/protocol/cchess_ucci.htm) |
| Pikafish | [github.com/official-pikafish/Pikafish](https://github.com/official-pikafish/Pikafish) |
| Fairy-Stockfish / pyffish | [github.com/fairy-stockfish/Fairy-Stockfish](https://github.com/fairy-stockfish/Fairy-Stockfish) |
| ElephantArt (CNN+MCTS) | [github.com/CGLemon/ElephantArt](https://github.com/CGLemon/ElephantArt) |
| xiangqigame (Pybind11) | [github.com/duanegoodner/xiangqigame](https://github.com/duanegoodner/xiangqigame) |
| FelicityEgtb | [github.com/aanhashi/FelicityEgtb](https://github.com/aanhashi/FelicityEgtb) |
| python-chess | [python-chess.readthedocs.io](https://python-chess.readthedocs.io/en/latest/) |
| PyQt6 Graphics View | [pythonguis.com/tutorials/pyqt6-qgraphics-vector-graphics/](https://www.pythonguis.com/tutorials/pyqt6-qgraphics-vector-graphics/) |
| AlphaZero RL pattern | LunaChess, AlphaZero_Chess (PyTorch) open-source repos |
