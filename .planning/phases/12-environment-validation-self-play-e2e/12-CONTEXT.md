# Phase 12: Environment Validation - Self-Play E2E - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

通过 Random vs Random 自对弈端到端验证整个 RL 环境管道（Phase 09-11 集成验证）。验证 XiangqiEnv 的 reset/step/reward/terminal/masking 在完整游戏循环中无崩溃，收集统计指标，确认 v0.3 环境就绪。

不包含：神经网络训练、策略网络、SyncVectorEnv 并行自对弈、性能优化（v1.0 范围）

</domain>

<decisions>
## Implementation Decisions

### 随机 Agent 策略
- **D-01:** 仅从 `info["legal_mask"]` 合法动作索引中随机采样。不测试非法动作路径（已在 Phase 11 单元测试覆盖）。每步通过 `np.random.choice(np.where(mask == 1.0)[0])` 选择动作

### 验证范围
- **D-02:** 核心验证 R7 的 4 条要求（100 局无崩溃、60-120 步平均、~50/50 胜负分布、合法动作验证），额外收集：
  - 终局原因分布：将杀、困毙、4-fold 重复和棋、50-move 和棋、WXF 长将/长捉
  - Reward 统计：平均 reward、最大、最小、标准差
  - 每局游戏长度分布（min/max/mean/median）

### 测试组织
- **D-03:** 新建 `tests/test_selfplay.py`，与 `tests/test_rl.py` 单元测试分离。包含一个主测试函数运行完整 100 局自对弈并断言统计指标

### 报告格式
- **D-04:** 统计信息通过 `print()` 输出到 pytest stdout（`pytest -s tests/test_selfplay.py` 查看）。不生成额外文件报告

### 性能基准
- **D-05:** 轻量计时 — 记录 100 局总耗时和平均每步耗时，仅供参考不设通过阈值。性能优化推迟到 v1.0 真实训练阶段

### Claude's Discretion
- 具体测试函数拆分方式（1 个大函数 vs 多个小函数）
- 统计输出的排版格式
- 随机种子选择（是否固定种子保证可复现）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 需求规格
- `.planning/REQUIREMENTS.md` §R7 — Self-Play End-to-End Validation 定义（100 局、游戏长度、胜负分布、合法动作验证）

### 核心代码
- `src/xiangqi/rl/env.py` — XiangqiEnv 主文件（reset, step, get_legal_mask, _compute_reward）
- `tests/test_rl.py` — 现有 29 个 RL 单元测试（参考测试风格和 fixture）
- `src/xiangqi/engine/engine.py` — XiangqiEngine.legal_moves(), result(), apply()
- `src/xiangqi/engine/types.py` — encode_move/decode_move

### 研究文档
- `.planning/research/RL_ENV.md` §7 — Self-Play Training Loop Structure（参考自对弈循环架构）
- `.planning/research/RL_ENV.md` §9 — Performance Requirements for Batch Simulation（性能参考目标）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `XiangqiEnv` (env.py): 完整的 gym.Env 实现，reset/step/legal_mask/reward 全部就绪
- `info["legal_mask"]` (8100,) float32: 每步返回的合法动作掩码，随机 agent 直接使用
- `_compute_reward()` (env.py:260-284): 材质捕获 + 兵卒过河奖励，终局 +1/-1/0
- `engine.result()` (engine.py): 返回 "IN_PROGRESS"/"RED_WINS"/"BLACK_WINS"/"DRAW" 字符串
- `gymnasium.make("Xiangqi-v0")` (env.py:288): 已注册的 entry point

### Established Patterns
- 动作编码: `action = from_sq * 90 + to_sq`，Discrete(8100)
- 棋子类型索引: `pt = abs(piece) - 1` (0-6)
- Info dict: 包含 legal_mask, piece_masks, piece_type_to_move, player_to_move
- 测试使用 `conda activate xqrl` 环境
- 现有 test_rl.py 有 659 行 / 29 个测试函数

### Integration Points
- 新建 `tests/test_selfplay.py` 导入 XiangqiEnv
- 自对弈循环调用 env.reset() → while not terminated → step(random_legal_action)
- 统计收集在循环内累计，循环后输出

</code_context>

<specifics>
## Specific Ideas

- 可固定随机种子保证可复现（如 `env.reset(seed=42 + game_idx)`）
- 终局原因需要从 env 内部获取 — 当前 step() 返回的 info 不包含具体终局原因（仅 terminated=True + reward），可能需要通过 `self._engine.result()` 暴露或从 reward 值推断
- 每步验证 legal_mask 与 engine.legal_moves() 一致（Phase 11 已有单元测试，self-play 可选择性抽查）

</specifics>

<deferred>
## Deferred Ideas

- SyncVectorEnv 并行自对弈 — v1.0 真实训练时再做性能验证
- 严格性能基准测试（对照 50-200 games/sec 目标）— v1.0
- 神经网络策略自对弈 — v1.0
- Replay buffer 集成测试 — v1.0

</deferred>

---

*Phase: 12-environment-validation-self-play-e2e*
*Context gathered: 2026-03-28*
