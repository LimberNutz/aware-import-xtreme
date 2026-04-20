# Interface Map

## Entry Points

| Type | Path | Invocation |
|------|------|-----------|
| CLI | main.py | python main.py [command] [options] |

## Public Module Interfaces

### app/cli.py
- `setup_parser()` -> argparse.ArgumentParser: Sets up CLI argument parser with subcommands

### app/pipeline/run_job.py
- `JobManager(args)`: Orchestrates job execution
- `JobManager.run()`: Execute full pipeline
- `JobManager.parse_only()`: Parse CML CSV only
- `JobManager.validate_only()`: Validate parsed data only
- `JobManager.probe_dxf(file)`: Inspect DXF structure
- `JobManager.probe_pdf(file)`: Inspect PDF structure

### CLI Subcommands
- `run`: Execute full title block update pipeline
- `parse`: Parse CML CSV and output intermediate data
- `validate`: Validate parsed data against business rules
- `probe-dxf`: Inspect DXF file for debugging
- `probe-pdf`: Inspect PDF file for debugging

### Common Options
- `--asset`: Asset identifier (e.g., GG-TF-10)
- `--csv`: Path to CML CSV import file
- `--dry-run`: Execute without writing files
- `--config`: Path to config.yaml (default: ./config.yaml)
