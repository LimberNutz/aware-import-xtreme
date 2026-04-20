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

_REQ_GROUP_STYLE = (
    "QGroupBox { color: #ff8a65; border: 1px solid #ff8a65; border-radius: 3px; "
    "margin-top: 8px; padding-top: 4px; font-size: 11px; font-weight: bold; }"
    "QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }"
)
_HINT_STYLE  = "color: #7a7a7a; font-size: 11px; font-style: italic; border: none;"
_REQ_LABEL   = "color: #ff8a65; border: none;"


def _req_label(text: str) -> "QLabel":
    lbl = QLabel(text)
    lbl.setStyleSheet(_REQ_LABEL)
    return lbl


def _hint(text: str) -> "QLabel":
    lbl = QLabel(text)
    lbl.setStyleSheet(_HINT_STYLE)
    lbl.setWordWrap(True)
    return lbl


class DesignDocDialog(QDialog):
    def __init__(self, cwd: str, parent=None):
        super().__init__(parent)
        self._cwd     = cwd
        self._worker  = None
        self._builder = None
        self.setWindowTitle("Design Doc Importer")
        self.resize(820, 760)
        self._init_ui()
        self._load_default_config()

    # ------------------------------------------------------------------
    # UI build
    # ------------------------------------------------------------------

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(14, 14, 14, 10)

        # ── Config File row ──────────────────────────────────────────────
        cfg_grp    = QGroupBox("Config File  —  load or save a job_config.txt")
        cfg_layout = QHBoxLayout(cfg_grp)
        self._cfg_edit = QLineEdit()
        self._cfg_edit.setPlaceholderText(
            "Path to an existing job_config.txt  (leave blank to build manually below)"
        )
        cfg_layout.addWidget(self._cfg_edit)
        browse_cfg = QPushButton("Browse…")
        browse_cfg.clicked.connect(
            lambda: self._browse_file(self._cfg_edit, "Config Files (*.txt);;All Files (*)")
        )
        cfg_layout.addWidget(browse_cfg)
        load_btn = QPushButton("Load")
        load_btn.setToolTip("Populate all fields below from the selected config file")
        load_btn.clicked.connect(lambda: self._load_config_file())
        cfg_layout.addWidget(load_btn)
        save_btn = QPushButton("Save Config")
        save_btn.setToolTip("Write the current field values to a job_config.txt")
        save_btn.clicked.connect(lambda: self._save_config_file())
        cfg_layout.addWidget(save_btn)
        new_btn = QPushButton("New / Clear")
        new_btn.setToolTip("Clear all fields to start a fresh config")
        new_btn.clicked.connect(self._clear_fields)
        cfg_layout.addWidget(new_btn)
        root.addWidget(cfg_grp)

        # ── REQUIRED ─────────────────────────────────────────────────────
        req_grp  = QGroupBox("Required  ✱")
        req_grp.setStyleSheet(_REQ_GROUP_STYLE)
        req_form = QFormLayout(req_grp)
        req_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        req_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        req_form.setSpacing(5)
        req_form.setContentsMargins(10, 10, 10, 10)

        # CAD Root Dir
        root_row = QHBoxLayout()
        self._root_edit = QLineEdit()
        self._root_edit.setPlaceholderText(
            r"e.g.  C:\Projects\GoldenGrain\CAD"
        )
        root_row.addWidget(self._root_edit)
        root_browse = QPushButton("Browse…")
        root_browse.clicked.connect(lambda: self._browse_dir(self._root_edit))
        root_row.addWidget(root_browse)
        req_form.addRow(_req_label("CAD Root Dir  ✱"), root_row)
        req_form.addRow(
            "",
            _hint(
                "Point this at the folder that contains your .dwg files — NOT the "
                "PDF subfolder.  PDFs in subfolders (e.g. CAD PDF\\) are found automatically."
            ),
        )

        # System Path Base
        self._syspath_edit = QLineEdit()
        self._syspath_edit.setPlaceholderText(
            "e.g.  XCEL > Golden Grain Energy > Mason City, IA > Unit > Piping >"
        )
        req_form.addRow(_req_label("System Path Base  ✱"), self._syspath_edit)
        req_form.addRow(
            "",
            _hint(
                "The Aware IDMS hierarchy path that sits above each entity.  "
                "Each entity name is appended automatically  (e.g.  … > GG-DIS-01)."
            ),
        )
        root.addWidget(req_grp)

        # ── OUTPUT OPTIONS ────────────────────────────────────────────────
        out_grp  = QGroupBox("Output  —  where and how the CSV is saved  (all optional)")
        out_form = QFormLayout(out_grp)
        out_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        out_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        out_form.setSpacing(5)
        out_form.setContentsMargins(10, 10, 10, 10)

        # Output Dir
        outdir_row = QHBoxLayout()
        self._outdir_edit = QLineEdit()
        self._outdir_edit.setPlaceholderText(
            "Leave blank → CSV is saved in the DesignDocImporter folder"
        )
        outdir_row.addWidget(self._outdir_edit)
        outdir_browse = QPushButton("Browse…")
        outdir_browse.clicked.connect(lambda: self._browse_dir(self._outdir_edit))
        outdir_row.addWidget(outdir_browse)
        out_form.addRow("Output Dir:", outdir_row)

        # Project Name
        self._project_edit = QLineEdit()
        self._project_edit.setPlaceholderText(
            "e.g.  GoldenGrain  →  output file: Equip_CADimport_GoldenGrain_20260417.csv"
        )
        out_form.addRow("Project Name:", self._project_edit)

        # Filename Override
        self._outfile_edit = QLineEdit()
        self._outfile_edit.setPlaceholderText(
            "Optional — overrides the auto-generated name entirely  "
            "e.g.  Equip_DesignDocs_MyJob.csv"
        )
        out_form.addRow("Filename Override:", self._outfile_edit)
        root.addWidget(out_grp)

        # ── SCAN OPTIONS ──────────────────────────────────────────────────
        scan_grp  = QGroupBox("Scan Options  —  controls how files are discovered")
        scan_form = QFormLayout(scan_grp)
        scan_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        scan_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        scan_form.setSpacing(5)
        scan_form.setContentsMargins(10, 10, 10, 10)

        # Max Depth
        depth_row = QHBoxLayout()
        self._depth_spin = QSpinBox()
        self._depth_spin.setRange(1, 20)
        self._depth_spin.setValue(10)
        self._depth_spin.setFixedWidth(65)
        depth_row.addWidget(self._depth_spin)
        depth_row.addWidget(
            _hint("  Folder levels to scan.  2 is usually enough for a CAD → CAD PDF structure.")
        )
        depth_row.addStretch()
        scan_form.addRow("Max Depth:", depth_row)

        self._auto_discover_cb = QCheckBox(
            "Auto-discover entities from filenames  "
            "(recommended — no manual entity list needed)"
        )
        self._auto_discover_cb.setChecked(True)
        scan_form.addRow("", self._auto_discover_cb)

        self._ignore_recover_cb = QCheckBox(
            "Ignore _recover files  (skip AutoCAD automatic backup files)"
        )
        self._ignore_recover_cb.setChecked(True)
        scan_form.addRow("", self._ignore_recover_cb)

        self._prefer_dwg_cb = QCheckBox(
            "Prefer DWG for entity discovery  "
            "(use .dwg filenames as the entity source rather than PDFs)"
        )
        self._prefer_dwg_cb.setChecked(True)
        scan_form.addRow("", self._prefer_dwg_cb)
        root.addWidget(scan_grp)

        # ── Run button ────────────────────────────────────────────────────
        run_row = QHBoxLayout()
        run_row.addStretch()
        self._run_btn = QPushButton("▶   Run")
        self._run_btn.setMinimumWidth(160)
        self._run_btn.setMinimumHeight(36)
        self._run_btn.setStyleSheet(
            "QPushButton { background-color: #2d7d32; color: #fff; border: none; "
            "border-radius: 3px; font-weight: bold; padding: 8px 24px; }"
            "QPushButton:hover { background-color: #388e3c; }"
            "QPushButton:disabled { background-color: #252526; color: #6d6d6d; }"
        )
        self._run_btn.clicked.connect(self._on_run)
        run_row.addWidget(self._run_btn)
        run_row.addStretch()
        root.addLayout(run_row)

        # ── Output Log ────────────────────────────────────────────────────
        log_grp    = QGroupBox("Output Log")
        log_layout = QVBoxLayout(log_grp)
        log_layout.setContentsMargins(6, 6, 6, 6)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Consolas", 10))
        self._log.setMinimumHeight(140)
        log_layout.addWidget(self._log)
        root.addWidget(log_grp, 1)

        # ── Close ─────────────────────────────────────────────────────────
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
            "ROOT_DIR":                        self._root_edit.text().strip(),
            "SYSTEM_PATH_BASE":                self._syspath_edit.text().strip(),
            "OUTPUT_DIR":                      self._outdir_edit.text().strip(),
            "OUTPUT_FILENAME":                 self._outfile_edit.text().strip(),
            "PROJECT_NAME":                    self._project_edit.text().strip(),
            "MAX_DEPTH":                       self._depth_spin.value(),
            "ENTITIES":                        [],
            "AUTO_DISCOVER_ENTITIES":          self._auto_discover_cb.isChecked(),
            "IGNORE_RECOVER_FILES":            self._ignore_recover_cb.isChecked(),
            "PREFER_DWG_FOR_ENTITY_DISCOVERY": self._prefer_dwg_cb.isChecked(),
        }

    def _clear_fields(self):
        self._cfg_edit.clear()
        self._root_edit.clear()
        self._syspath_edit.clear()
        self._outdir_edit.clear()
        self._project_edit.clear()
        self._outfile_edit.clear()
        self._depth_spin.setValue(10)
        self._auto_discover_cb.setChecked(True)
        self._ignore_recover_cb.setChecked(True)
        self._prefer_dwg_cb.setChecked(True)
        self._log.clear()

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
            self._outfile_edit.setText(cfg.get("OUTPUT_FILENAME", ""))
            self._project_edit.setText(cfg.get("PROJECT_NAME", ""))
            self._depth_spin.setValue(cfg.get("MAX_DEPTH", 10))
            self._auto_discover_cb.setChecked(cfg.get("AUTO_DISCOVER_ENTITIES", True))
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
            "# Design Doc Importer — job config",
            "#",
            "# REQUIRED",
            f"ROOT_DIR={self._root_edit.text()}",
            f"SYSTEM_PATH_BASE={self._syspath_edit.text()}",
            "#",
            "# OUTPUT (all optional)",
            f"OUTPUT_DIR={self._outdir_edit.text()}",
            f"PROJECT_NAME={self._project_edit.text()}",
            f"OUTPUT_FILENAME={self._outfile_edit.text()}",
            "#",
            "# SCAN OPTIONS",
            f"MAX_DEPTH={self._depth_spin.value()}",
            f"AUTO_DISCOVER_ENTITIES={'true' if self._auto_discover_cb.isChecked() else 'false'}",
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
            QMessageBox.warning(self, "Missing Required Field",
                                "CAD Root Dir is required.\n\n"
                                "Point it at the folder containing your .dwg files.")
            self._root_edit.setFocus()
            return
        if not cfg["SYSTEM_PATH_BASE"]:
            QMessageBox.warning(self, "Missing Required Field",
                                "System Path Base is required.\n\n"
                                "This is the Aware IDMS hierarchy path above your entities\n"
                                "e.g.  XCEL > Site > Unit > Piping >")
            self._syspath_edit.setFocus()
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
