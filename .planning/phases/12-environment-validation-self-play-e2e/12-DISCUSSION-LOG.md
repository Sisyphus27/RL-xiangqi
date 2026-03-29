# Phase 12: Environment Validation - Self-Play E2E - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 12-environment-validation-self-play-e2e
**Areas discussed:** 随机 Agent 策略, 验证范围与深度, 测试组织与报告, 性能基准

---

## 随机 Agent 策略

| Option | Description | Selected |
|--------|-------------|----------|
| 仅合法动作采样 | 从 legal_mask 获取合法动作索引随机选择，只测试正常路径 | ✓ |
| 全空间采样 + 重试 | 从全 8100 均匀采样，非法就吃 -2.0 继续 | |
| 混合采样 (90/10) | 90% legal_mask + 10% 全空间 | |

**User's choice:** 仅合法动作采样
**Notes:** 非法动作处理已在 Phase 11 单元测试覆盖，self-play 专注于正常游戏路径

---

## 验证范围与深度

| Option | Description | Selected |
|--------|-------------|----------|
| 仅 R7 | 4 条核心要求：100 局无崩溃、60-120 步、~50/50、合法动作验证 | |
| R7 + 统计增强 | R7 基础 + 终局原因分布 + reward 统计 | ✓ |
| R7 + R8 + 统计增强 | 加 SyncVectorEnv 并行自对弈 | |

**User's choice:** R7 + 统计增强
**Notes:** SyncVectorEnv 已在 Phase 09 验证基本功能，不需要重复验证

---

## 测试组织

| Option | Description | Selected |
|--------|-------------|----------|
| 新建 test_selfplay.py | 与 test_rl.py 分离，职责清晰 | ✓ |
| 追加到 test_rl.py | 集中管理但文件变长 | |

**User's choice:** 新建 test_selfplay.py

---

## 报告格式

| Option | Description | Selected |
|--------|-------------|----------|
| pytest stdout 输出 | print() 输出，pytest -s 查看 | ✓ |
| JSON/CSV 文件报告 | 保存详细数据，便于后续分析 | |

**User's choice:** pytest stdout 输出

---

## 性能基准

| Option | Description | Selected |
|--------|-------------|----------|
| 不测性能 | v1.0 再做性能优化 | |
| 轻量计时（参考） | 记录总耗时和每步耗时，无阈值 | ✓ |
| 严格性能验证 | 对照 RESEARCH.md §9 目标 | |

**User's choice:** 轻量计时（参考）
**Notes:** 不设通过阈值，仅供参考

---

## Claude's Discretion

- 具体测试函数拆分方式
- 统计输出排版格式
- 随机种子选择

## Deferred Ideas

- SyncVectorEnv 并行自对弈 — v1.0
- 严格性能基准 — v1.0
- 神经网络策略自对弈 — v1.0
