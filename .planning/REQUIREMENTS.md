# Requirements: RL-Xiangqi — v0.1 构建象棋引擎

**Defined:** 2026-03-19
**Core Value:** 完整中国象棋规则引擎，作为 RL 训练和 UI 的公共基础
**Scope:** 纯规则引擎，不含 UI、RL 接口、AI 搜索

---

## v0.1 Requirements

### 数据结构 (DATA)

- [ ] **DATA-01**: 棋盘以 `np.ndarray(10, 9, dtype=np.int8)` 表示，0=空，+1..+7=红方棋子，-1..-7=黑方棋子
- [ ] **DATA-02**: 棋子类型以 `IntEnum` 定义：帅、将、车、马、炮、士、象/相、兵/卒，红色正数、黑色负数
- [ ] **DATA-03**: 走法以 16-bit 整数编码 `(from_sq | (to_sq << 9) | (is_capture << 16))`，flat index = `from_sq * 90 + to_sq`
- [ ] **DATA-04**: `XiangqiState` 含：board、turn、move_history、halfmove_clock、zobrist_hash_history
- [ ] **DATA-05**: 初始局面常量 `STARTING_FEN`，标准开局棋盘坐标

### 棋子走法生成 (MOVE)

- [ ] **MOVE-01**: 帅/将：每步直走一格，限九宫内
- [ ] **MOVE-02**: 车：直线滑动任意距离，遇己方停止、遇敌方可吃
- [ ] **MOVE-03**: 马：日字走法，有蹩马腿判断（正交邻格有棋则阻）
- [ ] **MOVE-04**: 炮：直线滑动任意距离，吃子须隔一子（炮架）再跳吃
- [ ] **MOVE-05**: 士：斜线走一格，限九宫内
- [ ] **MOVE-06**: 象/相：田字对角走两格，有塞象眼判断，禁止过河
- [ ] **MOVE-07**: 兵/卒：过河前只前进一格，过河后可前进或左右走一格

### 规则校验 (RULE)

- [ ] **RULE-01**: `is_legal_move(state, move)` 校验走法合法性（棋子归属、路径阻塞、将军禁止）
- [ ] **RULE-02**: `generate_legal_moves(state)` 返回所有合法走法列表（含将军过滤）
- [ ] **RULE-03**: 将军检测：任意棋子能吃掉对方帅/将时返回被将军方
- [ ] **RULE-04**: 不能将帅/将移动到被将军位置（自投罗网检测）
- [ ] **RULE-05**: 面对面规则：双方将帅之间无子且同列时，该列子不能移动
- [x] **RULE-06**: `get_game_result(state)` 返回红胜/黑胜/和棋/进行中 (endgame.py)

### 终局判定 (ENDGAME)

- [x] **END-01**: 将死检测：无合法走法且被将军 → 判负
- [x] **END-02**: 困毙检测：无合法走法且不处将军 → 判负（中国象棋困毙为负）
- [x] **END-03**: 长将判和：连续长将（≥4步）无法解除 → 和棋
- [x] **END-04**: 重复局面：历史中出现 3 次相同 Zobrist 哈希 → 和棋
- [ ] **END-05**: 60步规则（可选）：连续 60 步无吃子且无兵过河 → 和棋

### API 接口 (API)

- [ ] **API-01**: `XiangqiEngine` 类：`reset()`、`apply_move(move)`、`undo_move()`、`is_legal(move)`、`legal_moves()`、`is_check()`、`result()`
- [ ] **API-02**: 走法执行后状态正确更新（board、turn、move_history、halfmove_clock）
- [ ] **API-03**: FEN 解析与导出：`from_fen(fen)`、`to_fen()`
- [ ] **API-04**: 性能：合法走法生成 < 10ms/局面，完整局面评估 < 100ms

### 测试 (TEST)

- [x] **TEST-01**: Perft 测试：depth=1 ≈ 44 种，depth=2 ≈ 1,916 种，depth=3 ≈ 72,987 种
- [ ] **TEST-02**: 参考 `pyffish` 库交叉验证所有走法合法性（`pyffish` 可用时）
- [x] **TEST-03**: 边界局面：将军局面、将死局面、困毙局面 (test_endgame.py)
- [x] **TEST-04**: 特殊规则：长将和棋、重复局面和棋、面对面规则 (test_repetition.py)

---

## Future Requirements

### v0.2 — RL 环境

- **RL-01**: Gymnasium `Env` 接口（`reset()`、`step()`、`observation_space`、`action_space`）
- **RL-02**: AlphaZero 风格 board planes 观察表示 `(16, 10, 9)`
- **RL-03**: 走法掩码（legal move mask）支持

### v0.3 — UI 界面

- **UI-01**: PyQt6 棋盘渲染（10×9 网格）
- **UI-02**: 棋子显示与点击走棋交互
- **UI-03**: 走法高亮和历史记录面板

### v1.0 — AI 对弈

- **AI-01**: Alpha-Beta 搜索剪枝
- **AI-02**: MCTS/PUCT 走法选择
- **AI-03**: 神经网络策略/价值评估

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Gymnasium RL 环境接口 | v0.2 处理 |
| PyQt6 图形界面 | v0.3 处理 |
| AI 搜索算法 | v1.0 处理 |
| UCI 协议接口 | 用于 AI 对战，v1.0 后 |
| 开局库 / 残局库 | 不影响引擎核心正确性 |
| 棋子图片资源 | UI 相关，v0.3 处理 |
| 在线功能 | 专注人机对弈，联网功能超出范围 |

---

## Traceability

| REQ-ID | Description | Phase | Status |
|--------|-------------|-------|--------|
| DATA-01 | board ndarray(10,9) | Phase 1 | [x] |
| DATA-02 | Piece IntEnum | Phase 1 | [x] |
| DATA-03 | Move 16-bit encoding | Phase 1 | [x] |
| DATA-04 | XiangqiState dataclass | Phase 1 | [x] |
| DATA-05 | STARTING_FEN | Phase 1 | [x] |
| MOVE-01 | General move gen | Phase 2 | [x] |
| MOVE-02 | Chariot move gen | Phase 2 | [x] |
| MOVE-03 | Horse move gen | Phase 2 | [x] |
| MOVE-04 | Cannon move gen | Phase 2 | [x] |
| MOVE-05 | Advisor move gen | Phase 2 | [x] |
| MOVE-06 | Elephant move gen | Phase 2 | [x] |
| MOVE-07 | Soldier move gen | Phase 2 | [x] |
| RULE-01 | is_legal_move | Phase 2 | [x] |
| RULE-02 | generate_legal_moves | Phase 2 | [x] |
| RULE-03 | is_in_check | Phase 2 | [x] |
| RULE-04 | no self-check moves | Phase 2 | [x] |
| RULE-05 | face-to-face rule | Phase 2 | [x] |
| RULE-06 | get_game_result | Phase 2 | [x] |
| TEST-01 | Perft depth 1-3 | Phase 2 | [x] |
| END-01 | checkmate detection | Phase 3 | [ ] |
| END-02 | stalemate detection | Phase 3 | [ ] |
| END-03 | perpetual check draw | Phase 3 | [ ] |
| END-04 | repetition draw | Phase 3 | [ ] |
| END-05 | 60-move rule (opt) | Phase 3 | [ ] |
| API-01 | XiangqiEngine class | Phase 4 | [x] |
| API-02 | state update correctness | Phase 4 | [x] |
| API-03 | FEN parse/export | Phase 4 | [x] |
| API-04 | performance targets | Phase 4 | [ ] |
| TEST-02 | pyffish cross-validate | Phase 4 | [ ] |
| TEST-03 | boundary positions | Phase 4 | [ ] |
| TEST-04 | special rules tests | Phase 4 | [ ] |

**Coverage:** 21/31 satisfied

---

*Requirements defined: 2026-03-19*
*Last updated: 2026-03-19 after v0.1 milestone scope definition*
