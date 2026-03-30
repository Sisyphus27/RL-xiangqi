---
phase: 14
slug: marl-keyword-design
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python (no formal framework — JSON validation + script dry run) |
| **Config file** | `paper_collect/dblp_config.json` |
| **Quick run command** | `python -c "import json; json.load(open('paper_collect/dblp_config.json'))"` |
| **Full suite command** | `cd paper_collect && python dblp_search.py --dry-run 2>&1 \| head -20` |
| **Estimated runtime** | ~2 seconds (validation), ~17 minutes (full test run) |

---

## Sampling Rate

- **After every task commit:** Run `python -c "import json; json.load(open('paper_collect/dblp_config.json'))"`
- **After every plan wave:** Verify config structure and keyword count
- **Before `/gsd:verify-work`:** Test run of `dblp_search.py` returns results
- **Max feedback latency:** 5 seconds (JSON parse)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | LIT-01 | structural | `python -c "import json; c=json.load(open('paper_collect/dblp_config.json')); assert len(c['search']['default_keywords']) >= 20"` | ✅ | ⬜ pending |
| 14-01-02 | 01 | 1 | LIT-02 | structural | `python -c "import json; c=json.load(open('paper_collect/dblp_config.json')); assert len(c['extract']['default_keywords']) >= 4"` | ✅ | ⬜ pending |
| 14-01-03 | 01 | 1 | LIT-03 | integration | `cd paper_collect && python dblp_search.py --max-queries 5 2>&1 \| grep -c "result"` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `paper_collect/dblp_config.json` — existing file, only content changes
- [ ] `paper_collect/dblp_search.py` — existing script, read-only

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Full pipeline test run returns reasonable volume (100-300 refined) | LIT-03 | Takes ~17 minutes, requires DBLP API access | Run `cd paper_collect && python dblp_search.py`, then `python dblp_keywords_extract.py`, check output count |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
