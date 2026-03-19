# Roadmap: RL-Xiangqi v0.1 构建象棋引擎

**Milestone:** v0.1
**Started:** 2026-03-19
**Core Deliverable:** 完整中国象棋规则引擎（纯 Python，无 UI、无 RL 接口）

---

## Phase 1 — 数据结构

**Goal:** 棋盘、走法、局面状态的基础数据结构

**Requirements:** DATA-01, DATA-02, DATA-03, DATA-04, DATA-05

**Deliverables:**
- `src/xiangqi/engine/types.py` — Piece 枚举、Board 表示（np.int8 array）、Move 编码
- `src/xiangqi/engine/state.py` — XiangqiState dataclass、Zobrist hash 初始化
- `src/xiangqi/engine/constants.py` — STARTING_FEN、九宫边界表、河界表

**Verification:**
- [x] `test_types.py` — 棋子编码正负、board shape (10,9)、Move 编码/解码 roundtrip
- [x] `test_state.py` — 初始局面 board 对应 STARTING_FEN

**Exit criteria:** 所有 5 个 DATA 需求覆盖，测试通过 ✓

**Plans:**
- [x] `01-01-PLAN.md` — types.py + constants.py + their tests (Wave 1, DATA-01/02/03/05) ✓
- [x] `01-02-PLAN.md` — state.py + test_state.py + conftest.py + pyproject.toml (Wave 2, DATA-04) ✓

---

## Phase Map

| Phase | Plans | Status |
|-------|-------|--------|
| Phase 1: 数据结构 | 2/2 complete | Complete ✓ |
| Phase 2 | 0/1 pending | Pending |
| Phase 3 | 0/1 pending | Pending |
| Phase 4 | 0/1 pending | Pending |

---

## Phase 2 — 棋子走法生成与规则校验

**Goal:** 7 种棋子合法走法生成 + 将军检测 + 面对面规则

**Requirements:** MOVE-01..MOVE-07, RULE-01..RULE-06

**Deliverables:**
- `src/xiangqi/engine/moves.py` — 各棋子走法生成器（gen_general, gen_chariot, gen_horse, gen_cannon, gen_advisor, gen_elephant, gen_soldier）
- `src/xiangqi/engine/legal.py` — `is_legal_move()`、`generate_legal_moves()`、`is_in_check()`
- `src/xiangqi/engine/rules.py` — 面对面规则、将军禁止自投罗网

**Verification:**
- [ ] `test_moves.py` — 各棋子从初始局面走法数量正确（44 total）
- [ ] `test_legal.py` —将军局面、被将军局面、将军禁止的走法被过滤
- [ ] `test_rules.py` — 面对面规则生效

**Exit criteria:** 所有 13 个 MOVE/RULE 需求覆盖，Perft depth=1~3 通过

---

## Phase 3 — 终局判定

**Goal:** 将死、困毙、长将/长捉和棋、重复局面和棋

**Requirements:** END-01, END-02, END-03, END-04, END-05

**Deliverables:**
- `src/xiangqi/engine/endgame.py` — `get_game_result()`、`checkmate?`/`stalemate?` 检测
- `src/xiangqi/engine/repetition.py` — Zobrist 哈希历史跟踪、重复局面检测
- `src/xiangqi/engine/perpetual.py` — 长将/长捉计数器，≥4步判和

**Verification:**
- [ ] `test_endgame.py` — 将死局面、困毙局面返回正确结果
- [ ] `test_repetition.py` — 三次重复局面触发和棋
- [ ] `test_perpetual.py` — 长将局面触发和棋

**Exit criteria:** 所有 5 个 END 需求覆盖，边界测试通过

---

## Phase 4 — API 接口与集成测试

**Goal:** 干净对外 API + FEN 支持 + pyffish 交叉验证

**Requirements:** API-01, API-02, API-03, API-04, TEST-01, TEST-02, TEST-03, TEST-04

**Deliverables:**
- `src/xiangqi/engine/engine.py` — `XiangqiEngine` 类，对齐 API-01 全部方法
- `src/xiangqi/engine/fen.py` — `from_fen()`、`to_fen()`
- `tests/test_api.py` — 完整 API 集成测试
- `tests/test_perft.py` — Perft 基准测试（depth 1-4）
- `tests/test_pyffish.py` — pyffish 交叉验证（若 pyffish 可用则执行）

**Verification:**
- [ ] `test_api.py` — apply/undo move 状态正确、legal_moves 覆盖完整
- [ ] `test_perft.py` — depth=1 ≈ 44, depth=2 ≈ 1,916, depth=3 ≈ 72,987
- [ ] `test_pyffish.py` — 所有合法走法与 pyffish 一致（跳过若 pyffish 不可用）
- [ ] 性能：legal_moves() < 10ms, 完整评估 < 100ms

**Exit criteria:** 引擎通过全部测试，可作为独立模块使用

---

## Phase Map

| Requirement | Phase |
|-------------|-------|
| DATA-01..05 | Phase 1 |
| MOVE-01..07, RULE-01..06 | Phase 2 |
| END-01..05 | Phase 3 |
| API-01..04 | Phase 4 |
| TEST-01..04 | Phase 4 |

**Coverage:** 29 requirements → 4 phases ✓

---

## Milestone Definition of Done

- [ ] Phase 1-4 全部完成并 commit
- [ ] `src/xiangqi/engine/` 模块可独立安装使用（`pip install -e .`）
- [ ] 测试覆盖率 ≥ 90%
- [ ] README.md 说明引擎使用方法
- [ ] 提交 PR 并通过 review

---

*Roadmap created: 2026-03-19*
*Last updated: 2026-03-19 after Phase 1 plan 01-02 completion*
