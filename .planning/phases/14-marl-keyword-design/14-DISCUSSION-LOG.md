# Phase 14: MARL Keyword Design - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-29
**Phase:** 14-MARL Keyword Design
**Areas discussed:** Stage 1 keyword scope, Stage 2 extraction logic, Venue scope & year range

---

## Stage 1 Keyword Scope

| Option | Description | Selected |
|--------|-------------|----------|
| MARL core terms (~20-25) | Only MARL core: multi-agent RL, heterogeneous agents, teammate modeling, active inference, etc. | |
| MARL + adjacent fields (~30-35) | MARL core + game theory, cooperative AI, mechanism design, coordination | |
| Broadest coverage (~35-40) | All above + opponent modeling, ToM, ad-hoc teamwork, communication learning, emergent behavior | |

**User's choice:** MARL core terms, with the note: "你需要先阅读AIM论文来精确范围，因为MARL范围非常广"
**Notes:** After reading AIM paper, refined to ~25 keywords anchored by AIM's terminology. User requested expanded heterogeneous keywords since that is the main innovation point.

### Specific keyword list

| Option | Description | Selected |
|--------|-------------|----------|
| A组: AIM-anchored core (~22) | 5 groups based on AIM paper concepts | |
| B组: Extended synonyms (~32) | A组 + additional synonyms and variants | |

**User's choice:** A组 (core), with heterogeneous section expanded to 7 keywords
**Notes:** User specifically requested more heterogeneous coverage: "关于异构的部分能否再多点，毕竟这个将来是主要创新点"

---

## Stage 2 Extraction Logic

| Option | Description | Selected |
|--------|-------------|----------|
| By topic (6 AND/OR groups) | 6 topic groups: MARL core, cooperation, heterogeneity, modeling, execution, application. Group-inner OR, group-inter AND. | ✓ |
| By relevance level (3 core + 3 optional) | 3 mandatory AND groups + 3 optional OR groups. Higher precision but may miss edge cases. | |
| Custom | User specifies group structure | |

**User's choice:** 6 topic groups with full coverage
**Notes:** Group 3 (heterogeneity) has the richest synonym set: heterogeneous | diverse | asymmetric | type-aware | role-based | different action space

---

## Venue Scope & Year Range

### Venues

| Option | Description | Selected |
|--------|-------------|----------|
| Slim + add AAMAS (~11) | Keep ML/AI top venues, add AAMAS/JAAMAS, remove irrelevant (CVPR, ACL, etc.) | |
| Keep all + add AAMAS (~20) | Retain all 18 existing venues + add AAMAS + JAAMAS | ✓ |
| Custom | User specifies venue list | |

**User's choice:** Keep all 18 existing venues + add AAMAS + JAAMAS

### Year Range

| Option | Description | Selected |
|--------|-------------|----------|
| 2020-2026 (existing) | Broad coverage of recent MARL literature | |
| 2024-2026 | Focus on cutting-edge work only | ✓ |

**User's choice:** 2024-2026 (user explicitly specified)
**Notes:** Narrowing to recent work aligns with the goal of capturing the latest active inference + heterogeneous MARL research.

---

## Claude's Discretion

- Exact keyword deduplication and ordering in config JSON
- Wildcard matching strategy (DBLP API behavior dependent)
- Fine-tuning pagination/retry settings for calibration test
- Stage 2 JSON nesting format details

## Deferred Ideas

None — discussion stayed within phase scope.
