# Change Request

> Copy this template and fill it in before starting work. Keeps LLM sessions focused and auditable.

## 1. Summary

**What**: (one sentence — what is being changed)
**Why**: (one sentence — what problem does this solve)
**Type**: [ ] Bug fix  [ ] Feature  [ ] Refactor  [ ] Config  [ ] Docs

## 2. Affected Files

| File | Change Type | Notes |
|------|-------------|-------|
| `path/to/file.py` | Modify / Create / Delete | Brief description |

## 3. Invariants That Must Hold

- [ ] `CMLRow` field set unchanged (unless intentionally extending the model)
- [ ] `AWARE_CSV_HEADERS` order unchanged (unless intentionally changing CSV contract)
- [ ] Session file version backward-compatible (bump `SESSION_VERSION` if schema changes)
- [ ] Write-back column mappings consistent between parser and writer
- [ ] No secrets in committed files
- [ ] (Add task-specific invariants here)

## 4. Interfaces Touched

| Interface | Current Signature | Change |
|-----------|-------------------|--------|
| (function/signal name) | (current args → return) | (what changes) |

## 5. Test Plan

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |

## 6. Rollback Plan

If this change causes problems:
- (How to revert — e.g., "git revert", "restore file from backup")

## 7. Post-Change

- [ ] Run `python tools/blueprint/snapshot.py` to update snapshots
- [ ] Update `docs/00_BLUEPRINT.md` if architecture changed
- [ ] Update `docs/INTERFACE_MAP.md` if public interfaces changed
- [ ] Walk through `tools/blueprint/verify_before_merge.md`
