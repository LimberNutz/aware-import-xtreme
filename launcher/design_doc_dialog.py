import sys
import importlib.util
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QTextEdit, QFileDialog, QGroupBox, QMessageBox,
)
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QFont, QTextCursor


# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------

def _load_builder():
    path = (
        Path(__file__).parent.parent
        / "AwareImport"
        / "DesignDocImporter"
        / "design_doc_csv_builder2.py"
    )
    spec = importlib.util.spec_from_file_location("design_doc_csv_builder2", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Stdout redirector → Qt signal
# ---------------------------------------------------------------------------

class _SignalWriter:
    def __init__(self, signal):
        self._signal = signal
        self._buf = ""

    def write(self, text: str) -> int:
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if line.strip():
                self._signal.emit(line)
        return len(text)

    def flush(self):
        if self._buf.strip():
            self._signal.emit(self._buf)
            self._buf = ""

    def isatty(self):
        return False


# ---------------------------------------------------------------------------
# Worker thread
# ---------------------------------------------------------------------------

class DesignDocWorker(QThread):
    log_line = Signal(str)
    finished = Signal(bool, str)   # success, message

    def __init__(self, builder, config: dict):
        super().__init__()
        self._builder = builder
        self._config  = config

    def run(self):
        writer     = _SignalWriter(self.log_line)
        old_stdout = sys.stdout
        sys.stdout = writer
        try:
            cfg      = self._config
            entities = list(cfg.get("ENTITIES", []))

            if cfg.get("AUTO_DISCOVER_ENTITIES", True) and not entities:
                self.log_line.emit("[INFO] Auto-discovering entities from filenames...")
                entities = self._builder.discover_entities(
                    root_dir          = cfg["ROOT_DIR"],
                    max_depth         = cfg.get("MAX_DEPTH", 10),
                    ignore_recover_files = cfg.get("IGNORE_RECOVER_FILES", True),
                    prefer_dwg        = cfg.get("PREFER_DWG_FOR_ENTITY_DISCOVERY", True),
                )

            if not entities:
                self.log_line.emit("[ERROR] No entities supplied or discovered.")
                self.finished.emit(False, "No entities found.")
                return

            self._builder.run_job(
                root_dir          = cfg["ROOT_DIR"],
                system_path_base  = cfg["SYSTEM_PATH_BASE"],
                entities          = entities,
                max_depth         = cfg.get("MAX_DEPTH", 10),
                output_dir        = cfg.get("OUTPUT_DIR", ""),
                output_filename   = cfg.get("OUTPUT_FILENAME", ""),
                project_name      = cfg.get("PROJECT_NAME", ""),
                ignore_recover_files = cfg.get("IGNORE_RECOVER_FILES", True),
            )
            self.finished.emit(True, "CSV written successfully.")

        except SystemExit as exc:
            self.finished.emit(False, f"Aborted (exit code {exc.code})")
        except Exception as exc:
            self.finished.emit(False, str(exc))
        finally:
            sys.stdout = old_stdout
            writer.flush()


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------

class DesignDocDialog(QDialog):
    def __init__(self, cwd: str, parent=None):
        super().__init__(parent)
        self._cwd     = cwd
        self._worker  = None
        self._builder = None
        self.setWindowTitle("Design Doc Importer")
        self.resize(760, 660)
        self._init_ui()
        self._load_default_config()

    # ------------------------------------------------------------------
    # UI build
    # ------------------------------------------------------------------

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)

        # --- Config file row ---
        cfg_grp    = QGroupBox("Config File")
        cfg_layout = QHBoxLayout(cfg_grp)
        self._cfg_edit = QLineEdit()
        self._cfg_edit.setPlaceholderText("Path to job_config.txt  (optional)")
        cfg_layout.addWidget(self._cfg_edit)
        browse_cfg = QPushButton("Browse…")
        browse_cfg.clicked.connect(lambda: self._browse_file(
            self._cfg_edit, "Config Files (*.txt);;All Files (*)"
        ))
        cfg_layout.addWidget(browse_cfg)
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(lambda: self._load_config_file())
        cfg_layout.addWidget(load_btn)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(lambda: self._save_config_file())
        cfg_layout.addWidget(save_btn)
        root.addWidget(cfg_grp)

        # --- Form fields ---
        fields_grp = QGroupBox("Configuration")
        form       = QFormLayout(fields_grp)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setSpacing(8)

        # CAD Root Dir
        root_row = QHBoxLayout()
        self._root_edit = QLineEdit()
        self._root_edit.setPlaceholderText("Root CAD folder containing .dwg files")
        root_row.addWidget(self._root_edit)
        root_browse = QPushButton("Browse…")
        root_browse.clicked.connect(lambda: self._browse_dir(self._root_edit))
        root_row.addWidget(root_browse)
        form.addRow("CAD Root Dir:", root_row)

        # System Path Base
        self._syspath_edit = QLineEdit()
        self._syspath_edit.setPlaceholderText("e.g.  XCEL > Site > Unit > Piping >")
        form.addRow("System Path Base:", self._syspath_edit)

        # Output Dir
        out_row = QHBoxLayout()
        self._outdir_edit = QLineEdit()
        self._outdir_edit.setPlaceholderText("Leave blank to save alongside this script")
        out_row.addWidget(self._outdir_edit)
        out_browse = QPushButton("Browse…")
        out_browse.clicked.connect(lambda: self._browse_dir(self._outdir_edit))
        out_row.addWidget(out_browse)
        form.addRow("Output Dir:", out_row)

        # Project Name
        self._project_edit = QLineEdit()
        self._project_edit.setPlaceholderText("Used in output filename  e.g. GoldenGrain")
        form.addRow("Project Name:", self._project_edit)

        # Max Depth
        self._depth_spin = QSpinBox()
        self._depth_spin.setRange(1, 20)
        self._depth_spin.setValue(10)
        self._depth_spin.setFixedWidth(70)
        form.addRow("Max Depth:", self._depth_spin)

        # Checkboxes
        self._ignore_recover_cb = QCheckBox("Ignore _recover files")
        self._ignore_recover_cb.setChecked(True)
        form.addRow("", self._ignore_recover_cb)

        self._prefer_dwg_cb = QCheckBox("Prefer DWG for entity discovery")
        self._prefer_dwg_cb.setChecked(True)
        form.addRow("", self._prefer_dwg_cb)

        root.addWidget(fields_grp)

        # --- Run button ---
        run_row = QHBoxLayout()
        run_row.addStretch()
        self._run_btn = QPushButton("▶   Run")
        self._run_btn.setMinimumWidth(150)
        self._run_btn.setMinimumHeight(36)
        self._run_btn.setStyleSheet(
            "QPushButton { background-color: #2d7d32; color: #fff; "
            "border: none; border-radius: 3px; font-weight: bold; padding: 8px 24px; }"
            "QPushButton:hover { background-color: #388e3c; }"
            "QPushButton:disabled { background-color: #252526; color: #6d6d6d; }"
        )
        self._run_btn.clicked.connect(self._on_run)
        run_row.addWidget(self._run_btn)
        run_row.addStretch()
        root.addLayout(run_row)

        # --- Log output ---
        log_grp    = QGroupBox("Output Log")
        log_layout = QVBoxLayout(log_grp)
        log_layout.setContentsMargins(6, 6, 6, 6)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Consolas", 10))
        self._log.setMinimumHeight(160)
        log_layout.addWidget(self._log)
        root.addWidget(log_grp, 1)

        # --- Close ---
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        close_row.addWidget(close_btn)
        root.addLayout(close_row)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _browse_dir(self, target: QLineEdit):
        start = target.text() or self._cwd
        path  = QFileDialog.getExistingDirectory(self, "Select Directory", start)
        if path:
            target.setText(path)

    def _browse_file(self, target: QLineEdit, filt: str):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", self._cwd, filt)
        if path:
            target.setText(path)

    def _get_builder(self):
        if self._builder is None:
            self._builder = _load_builder()
        return self._builder

    def _build_config(self) -> dict:
        return {
            "ROOT_DIR":                       self._root_edit.text().strip(),
            "SYSTEM_PATH_BASE":               self._syspath_edit.text().strip(),
            "OUTPUT_DIR":                     self._outdir_edit.text().strip(),
            "OUTPUT_FILENAME":                "",
            "PROJECT_NAME":                   self._project_edit.text().strip(),
            "MAX_DEPTH":                      self._depth_spin.value(),
            "ENTITIES":                       [],
            "AUTO_DISCOVER_ENTITIES":         True,
            "IGNORE_RECOVER_FILES":           self._ignore_recover_cb.isChecked(),
            "PREFER_DWG_FOR_ENTITY_DISCOVERY": self._prefer_dwg_cb.isChecked(),
        }

    # ------------------------------------------------------------------
    # Config file I/O
    # ------------------------------------------------------------------

    def _load_default_config(self):
        default = Path(self._cwd) / "job_config.txt"
        if default.is_file():
            self._cfg_edit.setText(str(default))
            self._load_config_file(quiet=True)

    def _load_config_file(self, quiet: bool = False):
        path = self._cfg_edit.text().strip()
        if not path or not Path(path).is_file():
            if not quiet:
                QMessageBox.warning(self, "Config File", "File not found.")
            return
        try:
            builder = self._get_builder()
            cfg     = builder.parse_config_file(path)
            self._root_edit.setText(cfg.get("ROOT_DIR", ""))
            self._syspath_edit.setText(cfg.get("SYSTEM_PATH_BASE", ""))
            self._outdir_edit.setText(cfg.get("OUTPUT_DIR", ""))
            self._project_edit.setText(cfg.get("PROJECT_NAME", ""))
            self._depth_spin.setValue(cfg.get("MAX_DEPTH", 10))
            self._ignore_recover_cb.setChecked(cfg.get("IGNORE_RECOVER_FILES", True))
            self._prefer_dwg_cb.setChecked(cfg.get("PREFER_DWG_FOR_ENTITY_DISCOVERY", True))
            if not quiet:
                self._append_log(f"[INFO] Config loaded from {path}")
        except SystemExit:
            if not quiet:
                QMessageBox.warning(self, "Config File", "Invalid config file format.")
        except Exception as exc:
            if not quiet:
                QMessageBox.warning(self, "Load Error", str(exc))

    def _save_config_file(self):
        path = self._cfg_edit.text().strip()
        if not path:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Config File",
                str(Path(self._cwd) / "job_config.txt"),
                "Config Files (*.txt);;All Files (*)",
            )
            if not path:
                return
            self._cfg_edit.setText(path)
        lines = [
            f"ROOT_DIR={self._root_edit.text()}",
            f"SYSTEM_PATH_BASE={self._syspath_edit.text()}",
            f"MAX_DEPTH={self._depth_spin.value()}",
            f"OUTPUT_DIR={self._outdir_edit.text()}",
            f"PROJECT_NAME={self._project_edit.text()}",
            "AUTO_DISCOVER_ENTITIES=true",
            f"IGNORE_RECOVER_FILES={'true' if self._ignore_recover_cb.isChecked() else 'false'}",
            f"PREFER_DWG_FOR_ENTITY_DISCOVERY={'true' if self._prefer_dwg_cb.isChecked() else 'false'}",
        ]
        try:
            Path(path).write_text("\n".join(lines), encoding="utf-8")
            self._append_log(f"[INFO] Config saved to {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Save Error", str(exc))

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def _on_run(self):
        cfg = self._build_config()
        if not cfg["ROOT_DIR"]:
            QMessageBox.warning(self, "Missing Field", "CAD Root Dir is required.")
            return
        if not cfg["SYSTEM_PATH_BASE"]:
            QMessageBox.warning(self, "Missing Field", "System Path Base is required.")
            return
        if self._worker and self._worker.isRunning():
            return

        self._log.clear()
        self._append_log(f"[{datetime.now().strftime('%H:%M:%S')}] Starting job…")
        self._run_btn.setEnabled(False)
        self._run_btn.setText("Running…")

        try:
            builder = self._get_builder()
        except Exception as exc:
            QMessageBox.critical(self, "Import Error", f"Failed to load builder:\n{exc}")
            self._run_btn.setEnabled(True)
            self._run_btn.setText("▶   Run")
            return

        self._worker = DesignDocWorker(builder, cfg)
        self._worker.log_line.connect(self._append_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self, success: bool, msg: str):
        self._run_btn.setEnabled(True)
        self._run_btn.setText("▶   Run")
        marker = "✔" if success else "✘"
        self._append_log(f"\n{marker}  {msg}")

    def _append_log(self, line: str):
        self._log.append(line)
        self._log.moveCursor(QTextCursor.MoveOperation.End)
