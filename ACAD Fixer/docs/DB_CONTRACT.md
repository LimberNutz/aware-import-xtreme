# Database Contract

## Status: No Database

This project does not use a database. It operates with:

### Data Sources
- **CML CSV files**: Input data for title block updates
- **DWG/DXF files**: CAD files to be modified
- **PDF files**: PDF documents to be stamped

### Persistence
- **QSettings (Windows Registry)**: Configuration persistence for user settings
- **config.yaml**: User-editable configuration file (cad_root, oda_exe paths)
- **CSV output logs**: Job execution results and audit trails

### Invariants
- CML CSV must follow expected format (asset identifiers, title block fields)
- DWG/DXF files must be accessible via ODA File Converter or ezdxf
- PDF files must be readable by PyMuPDF
- Dry-run mode never modifies source files
