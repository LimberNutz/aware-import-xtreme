# Snapshots

Machine-generated, token-efficient summaries of the project state. Feed these to an LLM for quick context.

## Files

| File | Contents |
|------|----------|
| `tree.txt` | Filtered directory tree (excludes `__pycache__`, `.git`, `node_modules`, etc.) |
| `entrypoints.txt` | Detected entry points, CLI commands, routes |
| `deps.txt` | Dependencies from `requirements.txt` |
| `db.txt` | Database/ORM detection (none in this project) |
| `tests.txt` | Test infrastructure summary |
| `env.txt` | Environment file detection (key names only, never secrets) |

## Regenerate

```bash
python tools/blueprint/snapshot.py
```

## When to Regenerate

- After adding/removing files or dependencies
- After changing entry points or project structure
- Before feeding context to an LLM for a new task
