# Rehydration Prompt

> Paste this into a new LLM session to quickly load project context.

---

You are about to work on a software project. Before making any changes, load the following context files **in order**. Read each one fully before proceeding.

## Step 1 — Load the rehydration bundle

Read `docs/snapshots/rehydrate_bundle.txt` first. It contains:
- Repo name, detected stack, key directories
- Primary entry points and test commands
- A prioritised file-loading list

## Step 2 — Load architecture context

Read these files in order:
1. `docs/00_BLUEPRINT.md` — architecture overview, data flow, file inventory
2. `docs/INTERFACE_MAP.md` — public interfaces, signal map, module APIs
3. `docs/DB_CONTRACT.md` — persistence layer (or lack thereof)

## Step 3 — Load guardrails

Read these before writing any code:
1. `docs/SAFE_CHANGELOG.md` — high-risk areas, change checklist
2. `.llm/rules.md` — hard rules for LLM behaviour in this repo
3. `tools/blueprint/verify_before_merge.md` — pre-merge checklist

## Step 4 — Scope your change

Use `tools/blueprint/change_request_template.md` to structure the task:
- What are you changing?
- Which files are affected?
- What invariants must hold?
- What tests confirm success?

## Step 5 — Work

Now you may read source files and make changes. Follow the locality rule: stay within the files relevant to your task. Do not roam.

## Step 6 — Verify

Before declaring "done", walk through `tools/blueprint/verify_before_merge.md`.

---

**Shortcut for small fixes**: If your change is a single-file bug fix, you can skip to Step 4 after reading `rehydrate_bundle.txt` and `.llm/rules.md`.
