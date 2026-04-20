# LLM Rules for This Repository

> Hard constraints for any LLM session working on this codebase. Load this file early.

## 1. Locality Rule

Stay within the files relevant to your current task. Do not explore, read, or modify files outside the scope of the change request. If you need to understand a dependency, read only its public interface (see `docs/INTERFACE_MAP.md`), not its internals — unless the task specifically requires it.

## 2. Contract-First Rule

Before modifying any function, class, or data model, check its current contract:
- Read its signature, docstring, and callers
- Confirm your change preserves the contract, or explicitly document the contract change
- Key contracts in this repo:
  - `CMLRow` field set → consumed by parser, transformer, aggregator, exporter, writer, TA builder
  - `AWARE_CSV_HEADERS` → defines CSV column order for Aware import
  - `PIPING_COLUMN_MAP` ↔ `_FIELD_TO_COL` ↔ `_TA_COL_TO_EXCEL` → must stay in sync
  - `SESSION_VERSION` → bump when session schema changes

## 3. No Secrets Rule

Never include in any file:
- Passwords, API keys, tokens, or credentials
- Real user data or PII
- Hardcoded absolute paths to user machines
- Registry values or environment variable values (key names are fine)

## 4. Deterministic Generators Rule

Any generated file (snapshots, exports, reports) must produce identical output when run twice on the same repo state. This means:
- Sort collections before writing
- Use stable iteration order (sorted dicts, sorted file lists)
- Include timestamps only where explicitly designed (and use UTC)
- Never include random values or process IDs

## 5. Small Diffs Rule

Prefer the smallest diff that achieves the goal:
- Do not refactor code adjacent to your change "while you're in there"
- Do not add type annotations, docstrings, or comments to code you did not change
- Do not reorganise imports or reformat files beyond what your change touches
- Do not add features, configurability, or error handling for scenarios not in the request
- If a function works and your task doesn't require changing it, leave it alone

## 6. Preserve Interfaces Rule

Do not change public function signatures, signal definitions, or model fields unless the task explicitly requires it. If you must change an interface:
- Update ALL callers (grep for the old signature)
- Update `docs/INTERFACE_MAP.md`
- Note the break in the change request

## 7. Write-Back Safety Rule

This application writes back to user's source Excel files. Any change to:
- `services/excel_writer.py`
- `_FIELD_TO_COL`, `_TA_COL_TO_EXCEL`, `_TA_VIEW_COL_TO_NAME`
- `PIPING_COLUMN_MAP`

...requires verifying that the correct Excel cell coordinates are targeted. A mapping error silently corrupts user data.
