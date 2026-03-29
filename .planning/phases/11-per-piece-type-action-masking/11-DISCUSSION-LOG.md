# Phase 11: Per-piece-type action masking - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 11-per-piece-type-action-masking
**Areas discussed:** 兵卒过河价值区分, 将军奖励, 公开 API 设计, 测试覆盖范围

---

## 兵卒过河价值区分

| Option | Description | Selected |
|--------|-------------|----------|
| 区分过河前后 | 过河前 1，过河后 2。与 R5 和研究文档一致 | ✓ |
| 固定值 1 | 保持 PIECE_VALUES[7]=1 不变 | |
| 固定值 1.5 | 用中间值，不区分过河 | |

**User's choice:** 区分过河前后（推荐）
**Notes:** 红兵 row <= 4 过河，黑卒 row >= 5 过河

---

## 将军奖励

| Option | Description | Selected |
|--------|-------------|----------|
| 不加 | 保持简单，只有终局+材质捕获奖励 | ✓ |
| 加 +0.05 | 给将军方额外奖励，增加激励但复杂化奖励设计 | |

**User's choice:** 不加（推荐）
**Notes:** 团队/合作奖励推迟到 v1.0

---

## 公开 API 设计

| Option | Description | Selected |
|--------|-------------|----------|
| 仅当前方 | player 参数仅用于验证，非当前方返回空掩码 | ✓ |
| 支持任意一方 | 可查任意一方掩码，实现复杂但支持对手建模 | |

**User's choice:** 仅当前方（推荐）
**Notes:** 非当前方返回全零掩码，不抛异常

---

## 测试覆盖范围

| Option | Description | Selected |
|--------|-------------|----------|
| 基本正确性 | 掩码形状、奖励值、非法动作、兵卒过河价值 | ✓ |
| 全面覆盖 | 每个棋子类型单独测试 + 特定位置 + 边界情况 | |

**User's choice:** 基本正确性（推荐）
**Notes:** 覆盖关键路径即可

---

## Claude's Discretion

- 内部方法重构细节
- 测试用例的具体 FEN 和动作编码选择
- 过河判断的具体实现方式

## Deferred Ideas

- 将军奖励（+0.05）— v1.0
- 对手掩码查询 — v1.0
