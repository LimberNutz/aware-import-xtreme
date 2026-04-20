import os
import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView, QTextEdit,
    QLabel, QSplitter, QAbstractItemView, QMenu, QApplication,
    QStyledItemDelegate, QDialog, QLineEdit, QCheckBox, QPushButton,
    QGridLayout, QMessageBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer, QSortFilterProxyModel
from PySide6.QtGui import QColor, QAction, QShortcut, QKeySequence, QFontMetrics
from models.cml_row import CMLRow, EntityInfoRow

# No cap on warning display — show every warning in the log.


class PreviewTableModel(QAbstractTableModel):
    COLUMNS = [
        "CML", "CML Location", "Component Type", "Component", "OD", "Nom.",
        "C.A.", "T-Min", "Mat. Spec.", "Mat. Grade", "Pressure", "Temp.",
        "J.E.", "Access", "Insulation", "Install Date", "Status", "NDE",
        "System Name", "Source",
    ]

    # column index -> CMLRow attribute name (editable columns only: 0-17)
    FIELD_MAP = {
        0: "cml", 1: "cml_location", 2: "component_type", 3: "component",
        4: "od", 5: "nom", 6: "ca", 7: "tmin", 8: "mat_spec", 9: "mat_grade",
        10: "pressure", 11: "temp", 12: "je", 13: "access", 14: "insulation",
        15: "install_date", 16: "status", 17: "nde",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[CMLRow] = []
        self._changed_cells: set[tuple[int, int]] = set()  # (row_idx, col_idx)
        self._undo_stack: list[list[tuple[int, int, str, str]]] = []  # Grouped edits
        self._current_undo_group: list[tuple[int, int, str, str]] | None = None

    def begin_undo_group(self):
        self._current_undo_group = []

    def end_undo_group(self):
        if self._current_undo_group is not None:
            if self._current_undo_group:
                self._undo_stack.append(self._current_undo_group)
            self._current_undo_group = None

    def set_rows(self, rows: list[CMLRow]):
        self.beginResetModel()
        self._rows = rows
        self._changed_cells.clear()
        self._undo_stack.clear()
        self.endResetModel()

    def rows(self) -> list[CMLRow]:
        return self._rows

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.COLUMNS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            fields = [
                row.cml, row.cml_location, row.component_type, row.component,
                row.od, row.nom, row.ca, row.tmin, row.mat_spec, row.mat_grade,
                row.pressure, row.temp, row.je, row.access, row.insulation,
                row.install_date, row.status, row.nde, row.system_name,
                _short_source(row.source_file),
            ]
            return fields[col] if col < len(fields) else ""

        if role == Qt.ForegroundRole:
            if row.warnings:
                return QColor("#e67e22")
            if not row.is_valid:
                return QColor("#e74c3c")

        if role == Qt.ToolTipRole:
            if row.warnings:
                return "\n".join(row.warnings)

        return None

    def flags(self, index):
        default = super().flags(index)
        if index.isValid() and index.column() in self.FIELD_MAP:
            return default | Qt.ItemIsEditable
        return default

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not index.isValid():
            return False
        col = index.column()
        if col not in self.FIELD_MAP:
            return False
        row_obj = self._rows[index.row()]
        attr = self.FIELD_MAP[col]
        new_val = str(value).strip()
        old_val = getattr(row_obj, attr)
        if old_val == new_val:
            return False
            
        edit = (index.row(), col, old_val, new_val)
        if self._current_undo_group is not None:
            self._current_undo_group.append(edit)
        else:
            self._undo_stack.append([edit])
            
        setattr(row_obj, attr, new_val)
        self._changed_cells.add((index.row(), col))
        self.dataChanged.emit(index, index)
        return True

    def undo(self):
        if not self._undo_stack:
            return
        edits = self._undo_stack.pop()
        
        for row_idx, col, old_val, _new_val in reversed(edits):
            row_obj = self._rows[row_idx]
            attr = self.FIELD_MAP[col]
            setattr(row_obj, attr, old_val)
            # remove from changed_cells if no remaining edits touch this cell
            still_changed = False
            for group in self._undo_stack:
                if any(r == row_idx and c == col for r, c, _, _ in group):
                    still_changed = True
                    break
            if not still_changed:
                self._changed_cells.discard((row_idx, col))
            idx = self.index(row_idx, col)
            self.dataChanged.emit(idx, idx)

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def has_changes(self) -> bool:
        return len(self._changed_cells) > 0

    def changed_cells(self) -> set[tuple[int, int]]:
        return self._changed_cells

    def clear_changes(self):
        self._changed_cells.clear()

    def clear(self):
        self.beginResetModel()
        self._rows.clear()
        self._changed_cells.clear()
        self._undo_stack.clear()
        self.endResetModel()


def _short_source(path: str) -> str:
    return os.path.basename(path) if path else ""


class SortFilterProxy(QSortFilterProxyModel):
    """Proxy that enables column-header sorting with numeric-aware comparison."""

    def lessThan(self, left, right):
        left_data = str(self.sourceModel().data(left, Qt.DisplayRole) or "")
        right_data = str(self.sourceModel().data(right, Qt.DisplayRole) or "")
        try:
            return float(left_data) < float(right_data)
        except (ValueError, TypeError):
            return left_data.lower() < right_data.lower()


# ---------------------------------------------------------------------------
# Baseline inspection threshold constant.
#
# Engineering rationale (API 570 / owner-user baseline logic):
# Pipe is manufactured to a nominal wall thickness with a mill tolerance
# of up to −12.5%.  A brand-new pipe may legitimately measure as low as
# 87.5% of nominal.  When NO prior inspection history exists (baseline),
# any UT reading below this threshold MAY represent real metal loss rather
# than mill tolerance.  Such readings are flagged for engineering review
# (t-min calculation, API 579 / B31G / RSTRENG fitness-for-service).
#
# The flag is a passive visual indicator only – it does not block any
# workflow and does not modify stored data.
# ---------------------------------------------------------------------------
_BASELINE_THRESHOLD_FACTOR = 0.875

# Light-amber highlight for rows that fail the baseline threshold check
_FLAG_BG_COLOR = QColor(255, 170, 0, 90)  # RGBA – amber tint, visible on dark theme


def _is_row_flagged(row: dict) -> bool:
    """Return True if the row needs engineering attention.

    Two conditions trigger a flag:
    1. UT Reading is present but below 87.5% of nominal (baseline threshold).
    2. UT Reading is blank on a row that has complete physical data (OD + Nom +
       CML Location present) — likely a missed measurement.

    Edge cases:
    - Nominal missing/zero/non-numeric  → do not flag condition 1.
    - Inspection Notes non-blank         → do not flag (anomaly already documented).
    """
    notes = (row.get("Inspection Notes") or "").strip()
    if notes:
        return False

    nom_str = (row.get("Nom.") or "").strip()
    ut_str  = (row.get("UT Reading") or "").strip()
    od_str  = (row.get("OD") or "").strip()
    loc_str = (row.get("CML Location") or "").strip()

    # Condition 2: missing UT reading on an otherwise complete row
    if not ut_str and nom_str and od_str and loc_str:
        return True

    # Condition 1: reading below 87.5% threshold
    if not nom_str or not ut_str:
        return False
    try:
        nom = float(nom_str)
        ut  = float(ut_str)
    except (ValueError, TypeError):
        return False
    if nom <= 0:
        return False

    return ut < nom * _BASELINE_THRESHOLD_FACTOR


def _flag_reason(row: dict) -> str:
    """Return a short human-readable reason string for a flagged row."""
    ut_str  = (row.get("UT Reading") or "").strip()
    nom_str = (row.get("Nom.") or "").strip()

    if not ut_str:
        return "Missing UT Reading"

    try:
        nom = float(nom_str)
        ut  = float(ut_str)
        threshold = nom * _BASELINE_THRESHOLD_FACTOR
        return (
            f"UT Reading ({ut}) < 87.5% of Nom. ({nom}) — "
            f"threshold = {threshold:.4f}"
        )
    except (ValueError, TypeError):
        return "Below baseline threshold"


class ThicknessActivityModel(QAbstractTableModel):
    """Editable model for Thickness Activity view (columns A:S)."""

    COLUMNS = [
        "CML", "CML Location", "Component Type", "Component", "OD", "Nom.",
        "C.A.", "T-Min", "Mat. Spec.", "Mat. Grade", "Pressure", "Temp.",
        "First Insp Date", "First UT Reading", "Last Insp Date", "Last UT Reading",
        "UT Reading", "Inspection Notes", "Inspected By",
    ]

    # All 19 columns are editable (indices 0-18)
    EDITABLE_COLS = set(range(19))

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[dict] = []
        self._flagged_rows: set[int] = set()  # row indices flagged by baseline threshold
        self._changed_cells: set[tuple[int, int]] = set()
        self._undo_stack: list[list[tuple[int, int, str, str]]] = []  # Grouped edits
        self._current_undo_group: list[tuple[int, int, str, str]] | None = None

    def begin_undo_group(self):
        self._current_undo_group = []

    def end_undo_group(self):
        if self._current_undo_group is not None:
            if self._current_undo_group:
                self._undo_stack.append(self._current_undo_group)
            self._current_undo_group = None

    def _recompute_flags(self):
        """Recompute the set of row indices that fail the 87.5% baseline threshold."""
        self._flagged_rows = {i for i, row in enumerate(self._rows) if _is_row_flagged(row)}

    def flagged_count(self) -> int:
        return len(self._flagged_rows)

    def set_rows(self, rows: list[dict]):
        self.beginResetModel()
        self._rows = rows
        self._changed_cells.clear()
        self._undo_stack.clear()
        self._recompute_flags()
        self.endResetModel()

    def rows(self) -> list[dict]:
        return self._rows

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.COLUMNS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row_idx = index.row()
        row = self._rows[row_idx]
        col_name = self.COLUMNS[index.column()]

        if role == Qt.DisplayRole:
            return row.get(col_name, "")

        if role == Qt.BackgroundRole:
            # Baseline threshold flag: highlight entire row in light amber
            if row_idx in self._flagged_rows:
                return _FLAG_BG_COLOR

        if role == Qt.ForegroundRole:
            if row.get("_error"):
                return QColor("#e74c3c")

        if role == Qt.ToolTipRole:
            if row_idx in self._flagged_rows:
                return _flag_reason(row)
            if row.get("_error"):
                return row["_error"]

        return None

    def flags(self, index):
        default = super().flags(index)
        if index.isValid() and index.column() in self.EDITABLE_COLS:
            return default | Qt.ItemIsEditable
        return default

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not index.isValid():
            return False
        col = index.column()
        if col not in self.EDITABLE_COLS:
            return False
        row_dict = self._rows[index.row()]
        col_name = self.COLUMNS[col]
        new_val = str(value).strip()
        old_val = row_dict.get(col_name, "")
        if old_val == new_val:
            return False
            
        edit = (index.row(), col, old_val, new_val)
        if self._current_undo_group is not None:
            self._current_undo_group.append(edit)
        else:
            self._undo_stack.append([edit])
            
        row_dict[col_name] = new_val
        self._changed_cells.add((index.row(), col))
        # Re-evaluate flag for this row if Nom., UT Reading, or Inspection Notes changed
        if col_name in ("Nom.", "UT Reading", "Inspection Notes"):
            self._update_flag_for_row(index.row())
        self.dataChanged.emit(index, index)
        return True

    def _update_flag_for_row(self, row_idx: int):
        """Recompute flag for a single row and emit change for entire row if needed."""
        was_flagged = row_idx in self._flagged_rows
        is_flagged = _is_row_flagged(self._rows[row_idx])
        if is_flagged:
            self._flagged_rows.add(row_idx)
        else:
            self._flagged_rows.discard(row_idx)
        if was_flagged != is_flagged:
            # Repaint entire row
            self.dataChanged.emit(
                self.index(row_idx, 0),
                self.index(row_idx, len(self.COLUMNS) - 1),
            )

    def undo(self):
        if not self._undo_stack:
            return
        edits = self._undo_stack.pop()
        
        for row_idx, col, old_val, _new_val in reversed(edits):
            col_name = self.COLUMNS[col]
            self._rows[row_idx][col_name] = old_val
            
            still_changed = False
            for group in self._undo_stack:
                if any(r == row_idx and c == col for r, c, _, _ in group):
                    still_changed = True
                    break
            if not still_changed:
                self._changed_cells.discard((row_idx, col))
                
            # Re-evaluate flag if undo touched a relevant column
            if col_name in ("Nom.", "UT Reading", "Inspection Notes"):
                self._update_flag_for_row(row_idx)
            idx = self.index(row_idx, col)
            self.dataChanged.emit(idx, idx)

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def has_changes(self) -> bool:
        return len(self._changed_cells) > 0

    def changed_cells(self) -> set[tuple[int, int]]:
        return self._changed_cells

    def clear_changes(self):
        self._changed_cells.clear()

    def clear(self):
        self.beginResetModel()
        self._rows.clear()
        self._changed_cells.clear()
        self._undo_stack.clear()
        self.endResetModel()


class EntityInfoModel(QAbstractTableModel):
    COLUMNS = [
        "System Path", "System Name", "System Type", "Equipment ID", "Equipment Description",
        "J.E.", "Year Built", "InService", "InService Date", "Class", "Stress Table Used",
        "PID Drawing", "PID Number", "PFD", "PFD Number", "PSM Covered", "Diameter",
        "Process Service", "Flags", "Source",
    ]

    FIELD_MAP = {
        4: "equipment_description",
        6: "year_built",
        8: "in_service_date",
        9: "class_name",
        10: "stress_table_used",
        11: "pid_drawing",
        12: "pid_number",
        13: "pfd",
        14: "pfd_number",
        16: "diameter",
        17: "process_service",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[EntityInfoRow] = []
        self._changed_cells: set[tuple[int, int]] = set()
        self._undo_stack: list[list[tuple[int, int, str, str]]] = []
        self._current_undo_group: list[tuple[int, int, str, str]] | None = None

    def begin_undo_group(self):
        self._current_undo_group = []

    def end_undo_group(self):
        if self._current_undo_group is not None:
            if self._current_undo_group:
                self._undo_stack.append(self._current_undo_group)
            self._current_undo_group = None

    def set_rows(self, rows: list[EntityInfoRow]):
        self.beginResetModel()
        self._rows = rows
        self._changed_cells.clear()
        self._undo_stack.clear()
        self.endResetModel()

    def rows(self) -> list[EntityInfoRow]:
        return self._rows

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.COLUMNS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            fields = [
                row.system_path,
                row.system_name,
                row.system_type,
                row.equipment_id,
                row.equipment_description,
                row.joint_efficiency,
                row.year_built,
                row.in_service,
                row.in_service_date,
                row.class_name,
                row.stress_table_used,
                row.pid_drawing,
                row.pid_number,
                row.pfd,
                row.pfd_number,
                row.psm_covered,
                row.diameter,
                row.process_service,
                "; ".join(row.warnings),
                _short_source(row.source_file or row.source_pdf),
            ]
            return fields[col] if col < len(fields) else ""

        if role == Qt.ForegroundRole:
            if row.warnings:
                return QColor("#e67e22")
            if not row.is_valid:
                return QColor("#e74c3c")

        if role == Qt.ToolTipRole:
            tips = []
            if row.warnings:
                tips.extend(row.warnings)
            if row.field_sources:
                tips.append("")
                tips.append("Sources:")
                for key in sorted(row.field_sources.keys()):
                    tips.append(f"{key}: {row.field_sources[key]}")
            if tips:
                return "\n".join(tips).strip()

        return None

    def flags(self, index):
        default = super().flags(index)
        if index.isValid() and index.column() in self.FIELD_MAP:
            return default | Qt.ItemIsEditable
        return default

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not index.isValid():
            return False
        col = index.column()
        if col not in self.FIELD_MAP:
            return False
        row_obj = self._rows[index.row()]
        attr = self.FIELD_MAP[col]
        new_val = str(value).strip()
        old_val = getattr(row_obj, attr)
        if old_val == new_val:
            return False

        edit = (index.row(), col, old_val, new_val)
        if self._current_undo_group is not None:
            self._current_undo_group.append(edit)
        else:
            self._undo_stack.append([edit])

        setattr(row_obj, attr, new_val)
        row_obj.field_sources[attr] = "manual"
        if attr == "year_built" and new_val and row_obj.field_sources.get("in_service_date") != "manual":
            # Derive 01/01/YYYY from the year
            from services.entity_info import _parse_year  # local import to avoid circular
            year = _parse_year(new_val)
            row_obj.in_service_date = f"01/01/{year}" if year else new_val
            row_obj.field_sources["in_service_date"] = "derived"
        if attr == "year_built" and not new_val and row_obj.field_sources.get("in_service_date") == "derived":
            row_obj.in_service_date = ""
        if attr == "pid_number":
            row_obj.pid_drawing = "Yes" if new_val else "No"
            row_obj.field_sources["pid_drawing"] = "manual"
        self._refresh_row_flags(row_obj)
        self._changed_cells.add((index.row(), col))
        self.dataChanged.emit(index, index)
        if attr == "year_built":
            derived_idx = self.index(index.row(), 8)
            self.dataChanged.emit(derived_idx, derived_idx)
        if attr == "pid_number":
            derived_idx = self.index(index.row(), 11)
            self.dataChanged.emit(derived_idx, derived_idx)
        return True

    def _refresh_row_flags(self, row_obj: EntityInfoRow):
        warnings = [w for w in row_obj.warnings if not any(
            token in w for token in (
                "Missing Year Built",
                "Missing Equipment Description",
                "Missing Stress Table Used",
                "Missing Diameter",
                "PID not found",
            )
        )]
        if not row_obj.equipment_description:
            warnings.append(f"[{row_obj.system_name}] Missing Equipment Description")
        if not row_obj.year_built:
            warnings.append(f"[{row_obj.system_name}] Missing Year Built")
        if not row_obj.stress_table_used:
            warnings.append(f"[{row_obj.system_name}] Missing Stress Table Used")
        if not row_obj.diameter:
            warnings.append(f"[{row_obj.system_name}] Missing Diameter")
        if not row_obj.pid_number:
            warnings.append(f"[{row_obj.system_name}] PID not found; PID Drawing defaulted to No")
        row_obj.warnings = warnings
        row_obj.is_valid = not any("Missing Year Built" in warning for warning in warnings)

    def undo(self):
        if not self._undo_stack:
            return
        edits = self._undo_stack.pop()

        for row_idx, col, old_val, _new_val in reversed(edits):
            row_obj = self._rows[row_idx]
            attr = self.FIELD_MAP[col]
            setattr(row_obj, attr, old_val)
            if attr == "year_built" and row_obj.field_sources.get("in_service_date") != "manual":
                from services.entity_info import _parse_year
                year = _parse_year(old_val)
                row_obj.in_service_date = f"01/01/{year}" if year else (old_val if "/" in old_val else f"1/1/{old_val}") if old_val else ""
            if attr == "pid_number":
                row_obj.pid_drawing = "Yes" if old_val else "No"
            self._refresh_row_flags(row_obj)
            still_changed = False
            for group in self._undo_stack:
                if any(r == row_idx and c == col for r, c, _, _ in group):
                    still_changed = True
                    break
            if not still_changed:
                self._changed_cells.discard((row_idx, col))
            idx = self.index(row_idx, col)
            self.dataChanged.emit(idx, idx)
            if attr == "year_built":
                derived_idx = self.index(row_idx, 8)
                self.dataChanged.emit(derived_idx, derived_idx)

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def has_changes(self) -> bool:
        return len(self._changed_cells) > 0

    def changed_cells(self) -> set[tuple[int, int]]:
        return self._changed_cells

    def clear_changes(self):
        self._changed_cells.clear()

    def clear(self):
        self.beginResetModel()
        self._rows.clear()
        self._changed_cells.clear()
        self._undo_stack.clear()
        self.endResetModel()


class PreviewDelegate(QStyledItemDelegate):
    """Custom delegate that pre-fills the editor with the current cell value
    so that Tab navigation does not erase adjacent cells.
    Also forces the model's BackgroundRole to paint, which QSS would otherwise override."""

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        # Paint model's BackgroundRole AFTER the styled pass so the amber
        # highlight overlays on top of the QSS-painted background.
        # The color has an alpha channel so text remains readable.
        bg = index.data(Qt.BackgroundRole)
        if bg is not None:
            painter.fillRect(option.rect, bg)

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        return editor

    def setEditorData(self, editor, index):
        current = index.data(Qt.DisplayRole) or ""
        editor.setText(str(current))
        editor.selectAll()


class FindReplaceDialog(QDialog):
    def __init__(self, panel, parent=None):
        super().__init__(parent)
        self.panel = panel
        self.setWindowTitle("Find and Replace")
        self.setModal(False)
        
        layout = QGridLayout(self)
        
        layout.addWidget(QLabel("Find what:"), 0, 0)
        self.find_input = QLineEdit()
        layout.addWidget(self.find_input, 0, 1)
        
        layout.addWidget(QLabel("Replace with:"), 1, 0)
        self.replace_input = QLineEdit()
        layout.addWidget(self.replace_input, 1, 1)
        
        self.match_case_cb = QCheckBox("Match case")
        layout.addWidget(self.match_case_cb, 2, 0, 1, 2)
        
        self.exact_match_cb = QCheckBox("Match entire cell contents")
        layout.addWidget(self.exact_match_cb, 3, 0, 1, 2)
        
        self.find_btn = QPushButton("Find Next")
        self.find_btn.clicked.connect(self._find_next)
        layout.addWidget(self.find_btn, 0, 2)
        
        self.replace_btn = QPushButton("Replace")
        self.replace_btn.clicked.connect(self._replace)
        layout.addWidget(self.replace_btn, 1, 2)
        
        self.replace_all_btn = QPushButton("Replace All")
        self.replace_all_btn.clicked.connect(self._replace_all)
        layout.addWidget(self.replace_all_btn, 2, 2)

    def _get_start_pos(self):
        idx = self.panel.table.currentIndex()
        if idx.isValid():
            return idx.row(), idx.column()
        return 0, -1

    def _matches(self, text, query, match_case, exact):
        if not match_case:
            text = text.lower()
            query = query.lower()
        if exact:
            return text == query
        return query in text

    def _do_find(self, start_row, start_col, show_msg=True):
        proxy = self.panel._sort_proxy
        if not proxy.rowCount():
            return False
            
        query = self.find_input.text()
        if not query:
            return False
            
        match_case = self.match_case_cb.isChecked()
        exact = self.exact_match_cb.isChecked()
        
        rows = proxy.rowCount()
        cols = proxy.columnCount()
        
        start_idx = start_row * cols + start_col + 1
        total_cells = rows * cols
        
        for i in range(total_cells):
            curr = (start_idx + i) % total_cells
            curr_r = curr // cols
            curr_c = curr % cols
            
            idx = proxy.index(curr_r, curr_c)
            val = str(proxy.data(idx, Qt.DisplayRole) or "")
            
            if self._matches(val, query, match_case, exact):
                self.panel.table.setCurrentIndex(idx)
                return True
                
        if show_msg:
            QMessageBox.information(self, "Find", f"Cannot find '{query}'")
        return False

    def _find_next(self):
        r, c = self._get_start_pos()
        self._do_find(r, c)

    def _replace(self):
        proxy = self.panel._sort_proxy
        active = self.panel._active_model()
        idx = self.panel.table.currentIndex()
        query = self.find_input.text()
        
        if idx.isValid():
            val = str(proxy.data(idx, Qt.DisplayRole) or "")
            match_case = self.match_case_cb.isChecked()
            exact = self.exact_match_cb.isChecked()
            
            if self._matches(val, query, match_case, exact):
                repl = self.replace_input.text()
                if exact:
                    new_val = repl
                elif match_case:
                    new_val = val.replace(query, repl)
                else:
                    compiled = re.compile(re.escape(query), flags=re.IGNORECASE)
                    new_val = compiled.sub(repl, val)
                
                editable = active.FIELD_MAP if hasattr(active, 'FIELD_MAP') else active.EDITABLE_COLS
                if idx.column() in editable:
                    proxy.setData(idx, new_val, Qt.EditRole)
                    
        self._find_next()

    def _replace_all(self):
        model = self.panel._active_model()
        query = self.find_input.text()
        if not query:
            return
            
        match_case = self.match_case_cb.isChecked()
        exact = self.exact_match_cb.isChecked()
        repl = self.replace_input.text()
        
        editable = model.FIELD_MAP if hasattr(model, 'FIELD_MAP') else model.EDITABLE_COLS
        
        if hasattr(model, "begin_undo_group"):
            model.begin_undo_group()
            
        rows = model.rowCount()
        cols = model.columnCount()
        count = 0
        
        if not match_case and not exact:
            compiled = re.compile(re.escape(query), flags=re.IGNORECASE)
        
        for r in range(rows):
            for c in range(cols):
                if c not in editable:
                    continue
                    
                idx = model.index(r, c)
                val = str(model.data(idx, Qt.DisplayRole) or "")
                
                if self._matches(val, query, match_case, exact):
                    if exact:
                        new_val = repl
                    elif match_case:
                        new_val = val.replace(query, repl)
                    else:
                        new_val = compiled.sub(repl, val)
                    
                    if val != new_val:
                        model.setData(idx, new_val, Qt.EditRole)
                        count += 1
                        
        if hasattr(model, "end_undo_group"):
            model.end_undo_group()
            
        QMessageBox.information(self, "Replace All", f"Made {count} replacement(s).")


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_mode = "CML Import"
        self._find_replace_dlg = None
        self._resize_scheduled = False
        # Persistent column widths keyed by mode name: mode -> list of (col, width)
        self._saved_col_widths: dict[str, list[tuple[int, int]]] = {}
        # Guard: True while we are programmatically resizing columns (skip save)
        self._programmatic_resize = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)

        # preview table
        self.model = PreviewTableModel()
        self.ta_model = ThicknessActivityModel()
        self.entity_model = EntityInfoModel()
        self._sort_proxy = SortFilterProxy(self)
        self._sort_proxy.setSourceModel(self.model)
        self._sort_proxy.setDynamicSortFilter(False)
        self.table = QTableView()
        self.table.setModel(self._sort_proxy)
        self.table.setItemDelegate(PreviewDelegate(self.table))
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_copy_menu)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setCascadingSectionResizes(False)
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(50)
        header.sectionHandleDoubleClicked.connect(self._auto_fit_selected_columns)
        header.setDefaultSectionSize(100)
        # Save column widths whenever the user manually resizes a column
        header.sectionResized.connect(self._on_section_resized)
        self.table.setWordWrap(False)
        self.table.setTextElideMode(Qt.ElideRight)
        splitter.addWidget(self.table)

        # validation / messages panel
        msg_widget = QWidget()
        msg_layout = QVBoxLayout(msg_widget)
        msg_layout.setContentsMargins(4, 4, 4, 4)
        msg_layout.setSpacing(2)

        self.summary_label = QLabel("No data loaded.")
        self.summary_label.setStyleSheet("font-weight: bold; padding: 4px;")
        msg_layout.addWidget(self.summary_label)

        # Clickable warning list — clicking a row entry scrolls the table to that CML
        self.messages_box = QListWidget()
        self.messages_box.setSelectionMode(QAbstractItemView.SingleSelection)
        self.messages_box.itemClicked.connect(self._on_warning_clicked)
        msg_layout.addWidget(self.messages_box)

        splitter.addWidget(msg_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        # Ctrl+C shortcut
        copy_shortcut = QShortcut(QKeySequence.Copy, self.table)
        copy_shortcut.activated.connect(self._copy_selection)

        # Ctrl+V shortcut
        paste_shortcut = QShortcut(QKeySequence.Paste, self.table)
        paste_shortcut.activated.connect(self._paste_selection)

        # Ctrl+F find shortcut
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self.table)
        find_shortcut.activated.connect(lambda: self._show_find_replace("find"))

        # Ctrl+H replace shortcut
        replace_shortcut = QShortcut(QKeySequence("Ctrl+H"), self.table)
        replace_shortcut.activated.connect(lambda: self._show_find_replace("replace"))

        # Ctrl+Z undo shortcut
        undo_shortcut = QShortcut(QKeySequence.Undo, self.table)
        undo_shortcut.activated.connect(self._undo)

        # Spacebar / Delete to clear selected cells
        del_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self.table)
        del_shortcut.activated.connect(self._clear_selected_cells)
        space_shortcut = QShortcut(QKeySequence(Qt.Key_Space), self.table)
        space_shortcut.activated.connect(self._clear_selected_cells)

    def _show_find_replace(self, mode="find"):
        if self._find_replace_dlg is None:
            self._find_replace_dlg = FindReplaceDialog(self, self)
        
        self._find_replace_dlg.show()
        self._find_replace_dlg.raise_()
        self._find_replace_dlg.activateWindow()
        self._find_replace_dlg.find_input.setFocus()
        self._find_replace_dlg.find_input.selectAll()

    def _active_model(self):
        """Return the model currently driving the table."""
        if self._current_mode == "Thickness Activity":
            return self.ta_model
        if self._current_mode == "Info Page Builder":
            return self.entity_model
        return self.model

    def _on_warning_clicked(self, item: QListWidgetItem):
        """Scroll the table to the source row stored in the clicked warning item."""
        row_idx = item.data(Qt.UserRole)
        if row_idx is None:
            return
        # Map source row -> proxy row
        proxy = self._sort_proxy
        source_model = self._active_model()
        source_idx = source_model.index(row_idx, 0)
        proxy_idx = proxy.mapFromSource(source_idx)
        if proxy_idx.isValid():
            self.table.scrollTo(proxy_idx, QAbstractItemView.PositionAtCenter)
            self.table.setCurrentIndex(proxy_idx)

    def set_data(self, rows: list[CMLRow], errors: list[str]):
        self.model.set_rows(rows)

        # build summary
        total = len(rows)
        warnings_count = sum(1 for r in rows if r.warnings)
        invalid_count = sum(1 for r in rows if not r.is_valid)
        self.summary_label.setText(
            f"Rows: {total}  |  Warnings: {warnings_count}  |  Invalid: {invalid_count}"
        )

        self.messages_box.clear()

        # Error entries (no associated row)
        if errors:
            hdr = QListWidgetItem("=== ERRORS ===")
            hdr.setFlags(Qt.ItemIsEnabled)  # not selectable
            self.messages_box.addItem(hdr)
            for err in errors:
                it = QListWidgetItem(err)
                it.setData(Qt.UserRole, None)
                self.messages_box.addItem(it)

        # Warning entries — one item per warning, storing source row index
        if any(r.warnings for r in rows):
            hdr = QListWidgetItem("=== WARNINGS ===")
            hdr.setFlags(Qt.ItemIsEnabled)
            self.messages_box.addItem(hdr)
            for row_idx, r in enumerate(rows):
                for w in r.warnings:
                    it = QListWidgetItem(f"[{r.system_name} / {r.cml}] {w}")
                    it.setData(Qt.UserRole, row_idx)
                    it.setToolTip("Click to jump to this row in the table")
                    self.messages_box.addItem(it)

        self._schedule_resize_columns()

    def _on_section_resized(self, logical_index: int, old_size: int, new_size: int):
        """Persist column widths whenever the user manually resizes a column.
        Ignored during programmatic resize passes."""
        if self._programmatic_resize:
            return
        header = self.table.horizontalHeader()
        model = self.table.model()
        if model is None:
            return
        widths = [
            (col, header.sectionSize(col))
            for col in range(model.columnCount())
            if not self.table.isColumnHidden(col)
        ]
        self._saved_col_widths[self._current_mode] = widths

    def _restore_col_widths(self) -> bool:
        """Restore saved column widths for the current mode.
        Returns True if widths were restored, False if none were saved."""
        saved = self._saved_col_widths.get(self._current_mode)
        if not saved:
            return False
        header = self.table.horizontalHeader()
        model = self.table.model()
        if model is None:
            return False
        for col, width in saved:
            if col < model.columnCount():
                header.resizeSection(col, width)
        return True

    def _show_copy_menu(self, pos):
        menu = QMenu(self)

        undo_action = QAction("Undo\tCtrl+Z", self)
        undo_action.setEnabled(self._active_model().can_undo())
        undo_action.triggered.connect(self._undo)
        menu.addAction(undo_action)

        menu.addSeparator()

        copy_sel_action = QAction("Copy Selection\tCtrl+C", self)
        copy_sel_action.triggered.connect(self._copy_selection)
        menu.addAction(copy_sel_action)

        copy_all_action = QAction("Copy All Rows (with headers)", self)
        copy_all_action.triggered.connect(self._copy_all_rows)
        menu.addAction(copy_all_action)
        
        menu.addSeparator()
        
        paste_action = QAction("Paste\tCtrl+V", self)
        paste_action.triggered.connect(self._paste_selection)
        menu.addAction(paste_action)

        menu.addSeparator()

        find_action = QAction("Find/Replace\tCtrl+F", self)
        find_action.triggered.connect(lambda: self._show_find_replace("find"))
        menu.addAction(find_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _undo(self):
        self._active_model().undo()

    def _clear_selected_cells(self):
        selection = self.table.selectionModel().selectedIndexes()
        if not selection:
            return
        active = self._active_model()
        editable = active.FIELD_MAP if hasattr(active, 'FIELD_MAP') else active.EDITABLE_COLS
        
        if hasattr(active, "begin_undo_group"):
            active.begin_undo_group()
            
        for idx in selection:
            if idx.column() in editable:
                source_idx = self._sort_proxy.mapToSource(idx)
                active.setData(source_idx, "", Qt.EditRole)
                
        if hasattr(active, "end_undo_group"):
            active.end_undo_group()

    def _copy_selection(self):
        selection = self.table.selectionModel().selectedIndexes()
        if not selection:
            return
        # organise by row then column
        rows_dict: dict[int, dict[int, str]] = {}
        for idx in selection:
            rows_dict.setdefault(idx.row(), {})[idx.column()] = str(idx.data() or "")
        sorted_rows = sorted(rows_dict.keys())
        col_set = sorted({c for cols in rows_dict.values() for c in cols})
        lines = []
        for r in sorted_rows:
            cells = [rows_dict[r].get(c, "") for c in col_set]
            lines.append("\t".join(cells))
        QApplication.clipboard().setText("\n".join(lines))

    def _copy_all_rows(self):
        proxy = self._sort_proxy
        if not proxy.rowCount():
            return
        active = self._active_model()
        headers = active.COLUMNS
        lines = ["\t".join(headers)]
        for r in range(proxy.rowCount()):
            cells = []
            for c in range(proxy.columnCount()):
                val = proxy.data(proxy.index(r, c), Qt.DisplayRole)
                cells.append(str(val) if val else "")
            lines.append("\t".join(cells))
        QApplication.clipboard().setText("\n".join(lines))

    def _paste_selection(self):
        clipboard_text = QApplication.clipboard().text()
        if not clipboard_text:
            return

        # Parse clipboard data (split by newlines, then tabs)
        rows_data = []
        for line in clipboard_text.split("\n"):
            line = line.strip("\r")
            if line or rows_data:
                rows_data.append(line.split("\t"))
        
        if rows_data and not any(rows_data[-1]):
            rows_data.pop()

        if not rows_data:
            return

        clip_height = len(rows_data)
        clip_width = max(len(row) for row in rows_data)
        if clip_width == 0:
            return

        rows_data = [row + [""] * (clip_width - len(row)) for row in rows_data]

        selection = self.table.selectionModel().selectedIndexes()
        if not selection:
            return

        active = self._active_model()
        proxy = self._sort_proxy
        editable = active.FIELD_MAP if hasattr(active, 'FIELD_MAP') else active.EDITABLE_COLS
        
        if hasattr(active, "begin_undo_group"):
            active.begin_undo_group()

        # If clipboard is a single value (1x1)
        if len(rows_data) == 1 and len(rows_data[0]) == 1:
            val = rows_data[0][0]
            for idx in selection:
                if idx.column() in editable:
                    proxy.setData(idx, val, Qt.EditRole)
        else:
            # Check if selection is exactly one column and matches clipboard row count
            selected_cells = sorted(selection, key=lambda idx: (idx.column(), idx.row()))
            unique_cols = {idx.column() for idx in selection}
            unique_rows = {idx.row() for idx in selection}
            
            if len(unique_cols) == 1 and len(selection) == len(rows_data) and all(len(r) == 1 for r in rows_data):
                # Paste 1D list into 1D selection
                for idx, row_data in zip(selected_cells, rows_data):
                    if idx.column() in editable:
                        proxy.setData(idx, row_data[0], Qt.EditRole)
            else:
                min_row = min(idx.row() for idx in selection)
                min_col = min(idx.column() for idx in selection)
                max_row = max(idx.row() for idx in selection)
                max_col = max(idx.column() for idx in selection)
                selection_is_rectangular = len(selection) == len(unique_rows) * len(unique_cols)

                if selection_is_rectangular and (len(unique_rows) > clip_height or len(unique_cols) > clip_width):
                    # Repeat the clipboard block to fill the selected rectangle.
                    for target_row in range(min_row, max_row + 1):
                        if target_row >= proxy.rowCount():
                            break

                        for target_col in range(min_col, max_col + 1):
                            if target_col >= proxy.columnCount():
                                break

                            if target_col not in editable:
                                continue

                            row_offset = (target_row - min_row) % clip_height
                            col_offset = (target_col - min_col) % clip_width
                            idx = proxy.index(target_row, target_col)
                            proxy.setData(idx, rows_data[row_offset][col_offset], Qt.EditRole)
                else:
                    # Block paste from top-left
                    for r_offset, row_data in enumerate(rows_data):
                        target_row = min_row + r_offset
                        if target_row >= proxy.rowCount():
                            break

                        for c_offset, val in enumerate(row_data):
                            target_col = min_col + c_offset
                            if target_col >= proxy.columnCount():
                                break

                            if target_col in editable:
                                idx = proxy.index(target_row, target_col)
                                proxy.setData(idx, val, Qt.EditRole)

        if hasattr(active, "end_undo_group"):
            active.end_undo_group()

    def set_mode(self, mode: str):
        self._current_mode = mode
        if mode == "Thickness Activity":
            self._sort_proxy.setSourceModel(self.ta_model)
            self.summary_label.setText("Thickness Activity — select a file to view.")
            self.messages_box.clear()
        elif mode == "Info Page Builder":
            self._sort_proxy.setSourceModel(self.entity_model)
            if self.entity_model.rowCount():
                valid = sum(1 for r in self.entity_model.rows() if r.is_valid)
                flagged = sum(1 for r in self.entity_model.rows() if r.warnings)
                self.summary_label.setText(
                    f"Info Page Builder — Rows: {self.entity_model.rowCount()}  |  Valid: {valid}  |  Flagged: {flagged}"
                )
            else:
                self.summary_label.setText("Info Page Builder — click Build Info Pages to create entity rows.")
            self.messages_box.clear()
        else:
            self._sort_proxy.setSourceModel(self.model)
            # restore CML Import summary if data exists
            if self.model.rowCount():
                total = self.model.rowCount()
                warnings_count = sum(1 for r in self.model.rows() if r.warnings)
                invalid_count = sum(1 for r in self.model.rows() if not r.is_valid)
                self.summary_label.setText(
                    f"Rows: {total}  |  Warnings: {warnings_count}  |  Invalid: {invalid_count}"
                )
            else:
                self.summary_label.setText("No data loaded.")
        self.table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self._schedule_resize_columns()

    def set_thickness_data(self, rows: list[dict], errors: list[str]):
        self.ta_model.set_rows(rows)
        total = len(rows)
        err_count = len(errors)
        flagged = self.ta_model.flagged_count()
        if total == 0 and err_count == 0:
            self.summary_label.setText("No thickness activity rows found.")
        else:
            parts = [f"Thickness Activity \u2014 Rows: {total}"]
            if flagged:
                parts.append(f"Flagged: {flagged}")
            if err_count:
                parts.append(f"Errors: {err_count}")
            self.summary_label.setText("  |  ".join(parts))

        # Build messages: parser errors first, then one line per flagged row
        lines = list(errors)
        flagged_lines = []
        for i, row in enumerate(rows):
            if self.ta_model._flagged_rows and i in self.ta_model._flagged_rows:
                cml  = row.get("CML", "") or f"row {i + 1}"
                loc  = row.get("CML Location", "")
                reason = _flag_reason(row)
                flagged_lines.append(f"[{cml}] {loc} \u2014 {reason}")
        if flagged_lines:
            if lines:
                lines.append("")
            lines.append("=== FLAGGED ROWS ===")
            lines.extend(flagged_lines)

        self.messages_box.clear()
        for line in lines:
            self.messages_box.addItem(QListWidgetItem(line))
        self._schedule_resize_columns()

    def set_entity_data(self, rows: list[EntityInfoRow], errors: list[str]):
        self.entity_model.set_rows(rows)
        total = len(rows)
        valid = sum(1 for r in rows if r.is_valid)
        flagged = sum(1 for r in rows if r.warnings)
        if total == 0 and not errors:
            self.summary_label.setText("Info Page Builder — no entity rows built.")
        else:
            parts = [f"Info Page Builder — Rows: {total}"]
            parts.append(f"Valid: {valid}")
            if flagged:
                parts.append(f"Flagged: {flagged}")
            if errors:
                parts.append(f"Errors: {len(errors)}")
            self.summary_label.setText("  |  ".join(parts))
        lines = list(errors)
        for row in rows:
            lines.extend(row.warnings)
        self.messages_box.clear()
        for line in lines:
            self.messages_box.addItem(QListWidgetItem(line))
        self._schedule_resize_columns()

    def _resize_columns_smart(self):
        """Compute and apply default column widths weighted by content type.
        Called only when no saved widths exist for the current mode."""
        model = self.table.model()
        header = self.table.horizontalHeader()

        if not model:
            return

        visible_cols = [col for col in range(model.columnCount()) if not self.table.isColumnHidden(col)]
        if not visible_cols:
            return

        available = self.table.viewport().width() - 8
        if available <= 0:
            return

        weights = [self._column_weight(str(model.headerData(col, Qt.Horizontal) or "")) for col in visible_cols]
        total_weight = sum(weights) or 1
        assigned = 0

        self._programmatic_resize = True
        try:
            for idx, col in enumerate(visible_cols):
                if idx == len(visible_cols) - 1:
                    width = max(28, available - assigned)
                else:
                    width = max(28, int(available * weights[idx] / total_weight))
                    assigned += width
                header.resizeSection(col, width)
        finally:
            self._programmatic_resize = False

    def _auto_fit_selected_columns(self, clicked_logical_index: int):
        """Resize selected columns (and the double-clicked column) to fit
        the widest data-cell content, excluding the header text.
        Persists the resulting widths so they survive entity switches."""
        model = self.table.model()
        header = self.table.horizontalHeader()
        if not model or model.rowCount() == 0:
            return

        # Gather selected column indices from current selection
        selected_cols: set[int] = set()
        selection = self.table.selectionModel().selectedIndexes()
        for idx in selection:
            selected_cols.add(idx.column())

        # Always include the column whose border was double-clicked
        selected_cols.add(clicked_logical_index)

        fm = QFontMetrics(self.table.font())
        padding = 16  # cell margin / padding
        min_width = header.minimumSectionSize()

        self._programmatic_resize = True
        try:
            for col in selected_cols:
                if self.table.isColumnHidden(col):
                    continue
                max_w = 0
                for row in range(model.rowCount()):
                    text = str(model.data(model.index(row, col), Qt.DisplayRole) or "")
                    text_w = fm.horizontalAdvance(text)
                    if text_w > max_w:
                        max_w = text_w
                width = max(min_width, max_w + padding)
                header.resizeSection(col, width)
        finally:
            self._programmatic_resize = False

        # Persist the updated layout (all visible columns)
        widths = [
            (col, header.sectionSize(col))
            for col in range(model.columnCount())
            if not self.table.isColumnHidden(col)
        ]
        self._saved_col_widths[self._current_mode] = widths

    def _schedule_resize_columns(self):
        if self._resize_scheduled:
            return
        self._resize_scheduled = True
        QTimer.singleShot(0, self._run_scheduled_resize)

    def _run_scheduled_resize(self):
        self._resize_scheduled = False
        # Always apply column visibility first (hide/show System Path, etc.)
        self._apply_column_visibility()
        # Restore user's saved widths if available, otherwise use smart defaults
        if not self._restore_col_widths():
            self._resize_columns_smart()

    def _apply_column_visibility(self):
        """Show/hide columns based on current mode (e.g. hide System Path in Info Page Builder).
        Does NOT change column widths."""
        model = self.table.model()
        if not model:
            return
        hide_path = self._current_mode == "Info Page Builder"
        self._programmatic_resize = True
        try:
            header = self.table.horizontalHeader()
            for col in range(model.columnCount()):
                header.setSectionResizeMode(col, QHeaderView.Interactive)
                header_text = str(model.headerData(col, Qt.Horizontal) or "")
                self.table.setColumnHidden(col, hide_path and header_text == "System Path")
        finally:
            self._programmatic_resize = False


    def _column_weight(self, header_text: str) -> int:
        if self._current_mode == "Info Page Builder":
            if header_text in {"Equipment Description", "Process Service", "Stress Table Used", "Flags"}:
                return 2
            if header_text in {"PID Number", "Source"}:
                return 1
            return 1
        if self._current_mode == "Thickness Activity":
            if header_text == "Inspection Notes":
                return 2
            return 1
        if header_text in {"Location", "Component", "Source"}:
            return 2
        return 1

    def clear(self):
        self.model.clear()
        self.ta_model.clear()
        self.entity_model.clear()
        self.summary_label.setText("No data loaded.")
        self.messages_box.clear()

