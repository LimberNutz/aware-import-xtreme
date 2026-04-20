# CML Drawing Title Block Automator

Standalone utility to automate the updating of CAD (DWG/DXF) and PDF title blocks using CML CSV reports.

## Prerequisites

1.  **Python 3.11+**
2.  **ODA File Converter** (Installed and in PATH, or specify path in config)
3.  **Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Run a Job
```bash
python main.py run --asset GG-TF-10 --csv "./data/cml_import.csv"
```

### Dry Run
```bash
python main.py run --asset GG-TF-10 --csv "./data/cml_import.csv" --dry-run
```

### Configuration
Update `config.yaml` with your local paths:
- `cad_root`: Where your original DWGs live.
- `oda_exe`: Path to `ODAFileConverter.exe`.

## Architecture
- `parsers/`: Handles GG CML CSV specificity.
- `cad/`: Uses `ezdxf` and ODA for DWG round-tripping.
- `pdf/`: Uses `PyMuPDF` for text redaction/stamping.
- `domain/`: Business logic for material classification and unit conversion.
