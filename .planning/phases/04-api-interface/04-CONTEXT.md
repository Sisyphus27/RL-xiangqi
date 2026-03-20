# Phase 4: API 接口与集成测试 - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a clean public `XiangqiEngine` API wrapping all internal modules (state, legal, moves, endgame, repetition), add FEN support, and deliver integration tests including pyffish cross-validation.

Deliverables (from ROADMAP.md):
- `src/xiangqi/engine/engine.py` — `XiangqiEngine` class with all API-01 methods
- `src/xiangqi/engine/fen.py` — `from_fen()` / `to_fen()` (both on Engine class)
- `tests/test_api.py` — full API integration tests
- `tests/test_perft.py` — Perft benchmark (depth 1–4)
- `tests/test_pyffish.py` — pyffish cross-validation (skip if unavailable)

**Runtime environment:** Always use conda environment `xqrl`. All commands run inside `conda activate xqrl`. Install missing packages with `pip install` inside that environment.

</domain>

<decisions>
## Implementation Decisions

### Engine 类的职责范围

- **Engine 持有并管理 XiangqiState**，对外提供统一接口，底层模块（state/legal/endgame/repetition）仅内部调用
- 外部调用方只通过 engine API 操作，无需知道内部模块的区分
- **FEN 导入/导出放在 Engine 类上**，不单独 fen.py 模块：`XiangqiEngine.from_fen(fen)` 创建实例，`engine.to_fen()` 导出

#### 对外公开的 7 个方法（API-01 全部）

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `reset()` | `None` | 重置到初始局面，重置 RepetitionState |
| `apply(move)` | `captured: int`（0=未吃子） | 委托 legal.apply_move(state, move)，自动更新 hash_history / halfmove_clock |
| `undo()` | `None` | 弹栈回退上一步，撤销 RepetitionState，空栈抛 IndexError |
| `is_legal(move)` | `bool` | 委托 legal.is_legal_move |
| `legal_moves()` | `list[int]` | 委托 legal.generate_legal_moves |
| `is_check()` | `bool` | 委托 legal.is_in_check |
| `result()` | `str` | 调用 endgame.get_game_result(state, _rep_state) |

#### FEN 支持
- `XiangqiEngine.from_fen(fen: str)` — 类方法，从 FEN 创建实例，等价于 `XiangqiState.from_fen` + 初始化 RepetitionState
- `engine.to_fen()` — 实例方法，导出当前局面 FEN

#### 只读属性暴露
- 通过 `@property` 只读暴露：`board`（np.ndarray）、`turn`（int）、`move_history`（list）
- 调用方只能读取，不能直接修改

#### 异常处理
- 非法走法 → 抛 `ValueError`
- 非法 FEN → 抛 `ValueError`
- undo() 空栈 → 抛 `IndexError("nothing to undo")`

---

### 撤销走法的实现机制

- **增量记录**：每次 apply() 把元组 `(from_sq, to_sq, captured, piece, prev_hash, prev_halfmove, prev_king_positions)` 入栈
- **undo() 公开**：调用方显式调用 `engine.undo()`，多步 undo 需要多次调用
- **undo() 同时回退 RepetitionState**：栈中存储撤销所需信息，undo 时正确恢复 check/chase 计数
- **apply/undo 共同维护 RepetitionState**：apply 后自动检测 check/chase 并更新；undo 后自动回退

---

### RepetitionState 与引擎的耦合方式

- **Engine 持有 `_rep_state: RepetitionState`**，apply/undo 时自动更新，result() 自动传入
- **完全封装**：RepetitionState 不对调用方暴露，调用方只调用 `result()` 获取终局判定
- **reset() 时重置 RepetitionState**：新开局或手动 reset 后，RepetitionState 回到干净初始状态
- **result() 无前置条件**：随时可调用，引擎保证内部状态同步
- **仅 result() 暴露终局信息**：不额外暴露 `is_long_check()` / `is_long_chase()` 等诊断方法

---

### pyffish 交叉验证的容错策略

- **不可用则跳过**：`pytest.importorskip("pyffish")` 或 try/except + `pytest.skip()`，测试套件仍然全绿
- **test_pyffish.py 完全独立**：单独文件，不混入 test_api.py
- **验证范围**：仅 perft(1) 初始局面的 44 步，与 pyffish 的 legal moves 逐一比对
- **失配则 FAIL + 详细输出**：打印具体哪个走法在引擎中有而 pyffish 没有（或相反），方便定位 bug
- **系统依赖**：需要先安装 `stockfish`（macOS: `brew install stockfish`），再 `pip install pyffish`（若无预编译 wheel 需从源码编译）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project requirements
- `.planning/REQUIREMENTS.md` — API-01 through API-04, TEST-01 through TEST-04 are the authoritative spec
- `.planning/ROADMAP.md` §Phase 4 — Deliverables, verification criteria, exit criteria

### Phase 1 context
- `.planning/phases/01-data-structures/01-CONTEXT.md` — Piece encoding, XiangqiState structure, Zobrist hash, FEN format (WXF)
- `src/xiangqi/engine/state.py` — XiangqiState with zobrist_hash_history, halfmove_clock, king_positions, from_fen(), copy()
- `src/xiangqi/engine/constants.py` — STARTING_FEN, from_fen(), to_fen()

### Phase 2 context
- `.planning/phases/02-move-generation/02-CONTEXT.md` — Move generation architecture, board-copy post-check
- `src/xiangqi/engine/legal.py` — apply_move(), is_legal_move(), generate_legal_moves(), is_in_check() — all will be called by engine.py internally

### Phase 3 context
- `.planning/phases/03-endgame-detection/03-CONTEXT.md` — RepetitionState lives in engine.py (Phase 4), long check → DRAW, long chase → chaser LOSES
- `src/xiangqi/engine/endgame.py` — get_game_result() with lazy import of repetition.py
- `src/xiangqi/engine/repetition.py` — RepetitionState class, check_repetition(), check_long_check(), check_long_chase()

### Accumulated decisions (STATE.md)
- [Phase 03]: RepetitionState lives in engine.py (Phase 4), not XiangqiState
- [Phase 03]: Long check → DRAW; Long chase → chaser LOSES (per WXO rules)
- [Phase 03]: enemy = -new_state.turn in _detect_chase
- [Phase 02-02]: CPW perft(1) = 44, perft(2) = 1,920, perft(3) = 79,666

### pyffish setup
- System dependency: `stockfish` must be installed first (brew/apt/compile)
- Python package: `pyffish` (pip install pyffish, or build from source if no wheel)
- pyproject.toml optional dep: `pip install -e ".[pyffish]"` to install pyffish

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `XiangqiState` (state.py) — already has from_fen(), copy(), zobrist_hash_history, halfmove_clock, king_positions
- `legal.apply_move(state, move)` (legal.py) — state-mutating, returns captured piece, already updates hash and halfmove_clock
- `legal.is_legal_move(state, move)` (legal.py) — returns bool
- `legal.generate_legal_moves(state)` (legal.py) — returns list[int]
- `legal.is_in_check(state, color)` (legal.py) — returns bool
- `endgame.get_game_result(state, rep_state)` (endgame.py) — lazy-imports repetition.py, priority order: repetition → long check → long chase → checkmate → stalemate
- `RepetitionState` (repetition.py) — has reset(), update() methods; stores consecutive_check_count, chase_seq, last_chasing_color

### Integration Points
- `engine.py` imports from: `xiangqi.engine.state`, `xiangqi.engine.legal`, `xiangqi.engine.endgame`, `xiangqi.engine.repetition`
- `engine.py` does NOT import from: `xiangqi.engine.moves` (legal.py already handles move generation internally)
- `test_api.py` imports: `XiangqiEngine`, `XiangqiState`, `Piece`
- `test_pyffish.py` imports: `pyffish` (conditional)

### Key design note: apply/undo stack
- Engine's undo requires storing pre-move state — specifically: `prev_hash` (uint64), `prev_halfmove` (int), `prev_king_positions` (dict), `captured` (int)
- The move history (`state.move_history`) already records applied moves; undo can read from it if needed
- `RepetitionState` must be restored on undo: if `_rep_state` snapshots before apply(), undo restores it

</code_context>

<specifics>
## Specific Ideas

- apply(move) delegates to legal.apply_move(state, move) — no duplicated board/hash logic
- FEN roundtrip: `XiangqiEngine.from_fen(fen)` → `engine.to_fen()` should equal input (modulo irrelevant FEN fields)
- Perft reference (CPW-verified via Fairy-Stockfish): perft(1) = 44, perft(2) = 1,920, perft(3) = 79,666
- pyffish legal moves are returned as UCI strings (e.g., "h2e2"); need to convert to/from 16-bit move encoding for comparison

</specifics>

<deferred>
## Deferred Ideas

- END-05 60-move rule — optional, skipped in Phase 3, can revisit later
- `engine.to_pgn()` / `engine.to_uci()` — UCI/PGN export, out of scope for v0.1
- `fen.py` as separate module — decided to keep FEN on Engine class, fen.py is not created

</deferred>

---

*Phase: 04-api-interface*
*Context gathered: 2026-03-20*
