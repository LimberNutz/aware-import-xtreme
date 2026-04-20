# Snapshots

Machine-generated summaries of the project state. Feed these to an LLM for quick context.

## Files

| File | Contents |
|------|----------|
| `rehydrate_bundle.txt` | **START HERE** - Compact <200 line one-shot LLM context |
| `how_it_works.txt` | Synthesized 6-8 bullet summary explaining the app |
| `architecture.txt` | Architecture pattern detection (layered apps, GUI, directory roles) |
| `api_surface.txt` | Key classes and public functions from core modules |
| `config_patterns.txt` | Configuration files, QSettings keys, AppConfig fields |
| `integrations.txt` | External integrations (Excel I/O, PDF parsing, CSV, fuzzy matching, etc.) |
| `data_flow.txt` | Import-based data flow hints (main imports, most referenced modules) |
| `docs_index.txt` | Documentation index with one-line summaries |
| `tree.txt` | Filtered directory tree |
| `entrypoints.txt` | Detected entry points |
| `deps.txt` | Dependencies |
| `db.txt` | Database/ORM detection |
| `tests.txt` | Test infrastructure |
| `env.txt` | Environment files (key names only) |

## Regenerate

```bash
python tools/blueprint/snapshot.py
```
