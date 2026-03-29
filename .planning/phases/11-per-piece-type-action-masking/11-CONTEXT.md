# Phase 11: Per-piece-type action masking - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

将 XiangqiEnv 的动作掩码和奖励信号从内部实现升级为公开 API，并完善兵卒过河价值区分。具体包括：

1. 公开 `get_legal_mask(player)` 和 `get_piece_legal_mask(piece_type, player)` 方法（R4）
2. 修复兵卒价值为过河前 1、过河后 2（R5）
3. 添加基本正确性测试覆盖

不包含：神经网络训练、策略头、将军奖励、团队奖励（v1.0 范围）

</domain>

<decisions>
## Implementation Decisions

### 奖励信号
- **D-01:** 兵卒过河价值区分 — 未过河 Soldier=1，过河后 Soldier=2。过河判断：红兵在 0-4 行（对方半场），黑卒在 5-9 行。材质捕获奖励 = piece_value / 100
- **D-02:** 不加将军奖励 — Phase 11 仅保留终局奖励（+1/-1/0）+ 材质捕获 + 非法惩罚（-2.0）。团队/合作奖励推迟到 v1.0

### 公开 API 设计
- **D-03:** `get_legal_mask(player=1|-1)` — 公开方法，仅支持查询当前回合方的合法动作掩码。传入非当前方返回全零掩码（不报错）
- **D-04:** `get_piece_legal_mask(piece_type, player)` — 公开方法，仅支持查询当前回合方指定棋子类型的掩码。传入非当前方返回全零掩码。piece_type 为 0-6 索引
- **D-05:** 现有 `_build_legal_mask()` 和 `_build_piece_masks()` 内部方法保留，公开方法包装调用它们

### 测试范围
- **D-06:** 基本正确性测试 — 掩码形状验证、奖励值验证（各棋子类型材质奖励）、非法动作处理、兵卒过河前后价值区分

### Claude's Discretion
- 内部方法重构细节
- 测试用例的具体 FEN 和动作编码选择
- 过河判断的具体实现方式（行号比较）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 需求规格
- `.planning/REQUIREMENTS.md` §R4 — Legal Move Masking 定义（get_legal_mask, get_piece_legal_mask, 非法动作处理）
- `.planning/REQUIREMENTS.md` §R5 — Basic Reward Signal 定义（终局奖励、材质捕获、棋子价值表、非法惩罚）

### 研究文档
- `.planning/research/RL_ENV.md` §4 — 奖励设计（棋子价值表、_compute_reward 参考实现）
- `.planning/research/RL_ENV.md` §2 — 动作空间设计（flat discrete 8100，legal mask 计算）
- `.planning/research/RL_ENV.md` §6 — Gymnasium 模式（MaskedCategorical，masked softmax）
- `.planning/research/RL_ENV.md` §10 — 多智能体 RL（逐棋子类型网络，get_piece_legal_mask 使用方式）

### 核心代码
- `src/xiangqi/rl/env.py` — XiangqiEnv 主文件，Phase 11 的主要修改目标
- `src/xiangqi/engine/types.py` — Piece IntEnum，encode_move/decode_move
- `src/xiangqi/engine/engine.py` — XiangqiEngine.legal_moves(), is_legal(), apply()
- `tests/test_rl.py` — 现有 RL 测试

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_build_legal_mask()` (env.py:184-191): 已实现完整合法掩码构建，遍历 engine.legal_moves()，无需重写
- `_build_piece_masks()` (env.py:193-224): 已实现逐棋子类型掩码构建，含 canonical rotation 处理
- `_compute_reward()` (env.py:226-236): 已实现材质捕获奖励计算，只需修复兵卒价值
- `PIECE_VALUES` dict (env.py:35): 当前 {0:0, 1:0, 2:2, 3:2, 4:4, 5:9, 6:4.5, 7:1}，Soldier 需改为动态

### Established Patterns
- 信息通过 `info` dict 返回（reset/step 返回的 info 中包含 legal_mask, piece_masks）
- 棋子类型索引：`pt = abs(piece) - 1` → 0=将帅, 1=士, 2=象, 3=马, 4=车, 5=炮, 6=兵卒
- 动作编码：`action = from_sq * 90 + to_sq`，Discrete(8100)

### Integration Points
- 公开方法将在 env.py 中实现，被外部 RL 训练代码调用
- `info["legal_mask"]` 和 `info["piece_masks"]` 继续由 reset()/step() 返回
- 奖励计算在 step() 中调用，_compute_reward 需要支持兵卒过河判断

</code_context>

<specifics>
## Specific Ideas

- 兵卒过河判断：用棋盘行号比较。红兵 row <= 4 为过河，黑卒 row >= 5 为过河。需在 _compute_reward 中获取被捕获兵的坐标
- 公开 API 返回全零掩码（非当前方）而非抛异常，保持与 Gymnasium 风格一致

</specifics>

<deferred>
## Deferred Ideas

- 将军奖励（+0.05）— 推迟到 v1.0 团队奖励设计阶段
- 对手掩码查询（查任意一方的合法动作）— 当前 RL 训练不需要，对手建模在 v1.0

</deferred>

---

*Phase: 11-per-piece-type-action-masking*
*Context gathered: 2026-03-28*
