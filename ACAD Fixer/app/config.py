"""Config loader for ACAD Fixer."""
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class AppConfig:
    oda_exe: str = ""
    cad_root: str = ""
    default_csv: str = ""
    work_root: str = r"C:\temp"
    oda_version: str = "ACAD2018"
    pdf_rotation: int = 270

    @classmethod
    def load(cls, path: Optional[str] = None) -> "AppConfig":
        cfg_path = Path(path) if path else Path("config.yaml")
        if not cfg_path.exists():
            logging.warning(f"Config file not found: {cfg_path}; using defaults")
            return cls()
        if yaml is None:
            raise RuntimeError("pyyaml is required to load config.yaml")
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(
            oda_exe=data.get("oda_exe", ""),
            cad_root=data.get("cad_root", ""),
            default_csv=data.get("default_csv", ""),
            work_root=data.get("work_root", r"C:\temp"),
            oda_version=data.get("oda_version", "ACAD2018"),
            pdf_rotation=int(data.get("pdf_rotation", 270)),
        )

    def validate_for_run(self) -> list:
        """Returns list of error messages (empty if OK)."""
        errors = []
        if not self.oda_exe or not Path(self.oda_exe).exists():
            errors.append(f"oda_exe not found: {self.oda_exe}")
        if not self.cad_root or not Path(self.cad_root).exists():
            errors.append(f"cad_root not found: {self.cad_root}")
        return errors
