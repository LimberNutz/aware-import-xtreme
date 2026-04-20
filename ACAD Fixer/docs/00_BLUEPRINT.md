# Project Blueprint

> **Purpose**: Automates updating of CAD (DWG/DXF) and PDF title blocks using CML CSV reports.

## Repo Assessment

| Attribute | Value |
|-----------|-------|
| Language | Python 3.11+ |
| Framework | argparse (CLI) |
| DB / ORM | None (QSettings for config) |
| Tests | None configured |
| Entry point | python main.py |

## Architecture Overview

```
ACAD Fixer/
├── main.py              # CLI entry point
├── requirements.txt     # Python dependencies
├── config.yaml          # Configuration (cad_root, oda_exe)
├── app/
│   ├── cli.py           # Argument parser setup
│   ├── cad/             # DWG/DXF handling (ezdxf, ODA)
│   ├── domain/          # Business logic (classification, conversion)
│   ├── parsers/         # CML CSV parsing
│   ├── pdf/             # PDF text redaction/stamping (PyMuPDF)
│   └── pipeline/        # Job orchestration (run, parse, validate)
├── tools/               # Developer utilities
└── docs/                # Blueprint documentation
```

**Note**: Run `python tools/blueprint/snapshot.py` to auto-generate architecture detection, API surface, and data flow hints.

## Data Flow

```
main.py -> app.cli (parse args) -> app.pipeline.run_job (JobManager)
  |
  +-> run: Execute full pipeline (parse -> validate -> update CAD/PDF)
  +-> parse: Parse CML CSV only
  +-> validate: Validate parsed data only
  +-> probe-dxf: Inspect DXF file structure
  +-> probe-pdf: Inspect PDF file structure

Data sources: CML CSV reports
Output: Updated DWG/DXF files, stamped PDFs, CSV logs
Persistence: QSettings (Windows Registry) for configuration
```

**Note**: The `docs/snapshots/data_flow.txt` file auto-generates import-based data flow hints.

## Key Conventions

- Configuration via config.yaml and QSettings
- CLI-first design with subcommands (run, parse, validate, probe-dxf, probe-pdf)
- Dry-run mode for safe testing
- Separate parsers for CML CSV specificity
- CAD operations via ezdxf and ODA File Converter
- PDF operations via PyMuPDF

## File Inventory

| File | Role |
|------|------|
| main.py | CLI entry point and command routing |
| app/cli.py | argparse setup and subcommand definitions |
| app/pipeline/run_job.py | JobManager orchestrates parse/validate/update workflows |
| app/cad/ | DWG/DXF file handling and title block updates |
| app/pdf/ | PDF text redaction and stamping |
| app/parsers/ | CML CSV parsing and data extraction |
| app/domain/ | Material classification and unit conversion logic |
| config.yaml | User configuration (cad_root, oda_exe paths) |

## Snapshots

Run `python tools/blueprint/snapshot.py` to generate comprehensive project snapshots:
- `rehydrate_bundle.txt` - Compact LLM context (start here)
- `how_it_works.txt` - Synthesized app summary
- `architecture.txt` - Architecture pattern detection
- `api_surface.txt` - Key classes and functions
- `config_patterns.txt` - Configuration patterns
- `integrations.txt` - External integrations
- `data_flow.txt` - Import relationships
- Plus tree, entrypoints, deps, db, tests, env, docs_index
