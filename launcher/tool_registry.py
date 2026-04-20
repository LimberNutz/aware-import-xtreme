import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _python_for(tool_cwd: str) -> str:
    """Use the local .venv Python if one exists, otherwise fall back to the current interpreter."""
    venv = os.path.join(tool_cwd, ".venv", "Scripts", "python.exe")
    if os.path.isfile(venv):
        return venv
    return sys.executable


def get_tools() -> list[dict]:
    acad_cwd  = str(ROOT / "ACAD Fixer")
    aware_cwd = str(ROOT / "AwareImport")
    scout_cwd = str(ROOT / "File Scout 2025")
    ddi_cwd   = str(ROOT / "AwareImport" / "DesignDocImporter")

    return [
        {
            "id": "acad_fixer",
            "name": "ACAD Fixer",
            "tagline": "Automate CAD title blocks from CML reports",
            "icon": "📐",
            "features": [
                "DWG/DXF title block automation",
                "PDF stamp & redact",
                "Batch processing",
                "Dry-run preview mode",
            ],
            "cwd": acad_cwd,
            "cmd": [_python_for(acad_cwd), "main.py", "--gui"],
            "launch_mode": "subprocess",
        },
        {
            "id": "aware_import",
            "name": "AwareImport",
            "tagline": "Batch parse UT sheets → Aware CML import CSVs",
            "icon": "📊",
            "features": [
                "CML Import CSV builder",
                "Info Page Builder",
                "Thickness Activity view",
                "Session save & restore",
            ],
            "cwd": aware_cwd,
            "cmd": [_python_for(aware_cwd), "main.py"],
            "launch_mode": "subprocess",
        },
        {
            "id": "file_scout",
            "name": "File Scout 2025",
            "tagline": "Find, audit and organize files across directories",
            "icon": "🔍",
            "features": [
                "Advanced multi-criteria search",
                "Duplicate file detection",
                "Smart Sort organization",
                "Google Drive file audit",
            ],
            "cwd": scout_cwd,
            "cmd": [_python_for(scout_cwd), "File Scout 3.3.py"],
            "launch_mode": "subprocess",
        },
        {
            "id": "design_doc_importer",
            "name": "Design Doc Importer",
            "tagline": "Build Aware IDMS design document import CSVs",
            "icon": "📄",
            "features": [
                "Auto-discovers entities from filenames",
                "Scans DWG & PDF files",
                "Configurable via job_config.txt",
                "Outputs Aware-ready CSV",
            ],
            "cwd": ddi_cwd,
            "launch_mode": "dialog",
        },
    ]
