import os
import shutil
import subprocess

from send2trash import send2trash

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView, QMenu, QMessageBox,
    QFileDialog, QInputDialog, QAbstractItemView, QApplication,
)
from PySide6.QtCore import Qt, Signal, QMimeData, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor, QAction, QDragEnterEvent, QDropEvent, QFontMetrics
from models.cml_row import FileEntry
from app.constants import SUPPORTED_EXTENSIONS


class FileListModel(QAbstractTableModel):
    COLUMNS = ["Filename", "Folder", "System Name", "Status", "Rows"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[FileEntry] = []

    def entries(self) -> list[FileEntry]:
        return self._entries

    def rowCount(self, parent=QModelIndex()):
        return len(self._entries)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.COLUMNS[section]
        if role == Qt.TextAlignmentRole and orientation == Qt.Horizontal and section == 4:
            return Qt.AlignLeft | Qt.AlignVCenter
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        entry = self._entries[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return entry.filename
            elif col == 1:
                return entry.folder
            elif col == 2:
                return entry.system_name
            elif col == 3:
                return entry.status
            elif col == 4:
                return str(entry.row_count) if entry.row_count > 0 else ""

        if role == Qt.ForegroundRole:
            if entry.status == "Error":
                return QColor("#e74c3c")
            if entry.status == "Missing":
                return QColor("#e67e22")
            if entry.status == "Parsed":
                return QColor("#2ecc71")

        if role == Qt.ToolTipRole:
            tip = entry.file_path
            if entry.error_message:
                tip += f"\nError: {entry.error_message}"
            return tip

        return None

    def add_files(self, file_paths: list[str]):
        # deduplicate by path
        existing = {e.file_path for e in self._entries}
        new_entries = []
        for fp in file_paths:
            fp = os.path.normpath(fp)
            if fp in existing:
                continue
            ext = os.path.splitext(fp)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            if os.path.basename(fp).startswith("~$"):
                continue
            entry = FileEntry(file_path=fp)
            if not os.path.exists(fp):
                entry.status = "Missing"
            new_entries.append(entry)
            existing.add(fp)

        if new_entries:
            start = len(self._entries)
            self.beginInsertRows(QModelIndex(), start, start + len(new_entries) - 1)
            self._entries.extend(new_entries)
            self.endInsertRows()

    def remove_rows(self, indices: list[int]):
        # remove in reverse order to keep indices valid
        for idx in sorted(indices, reverse=True):
            self.beginRemoveRows(QModelIndex(), idx, idx)
            self._entries.pop(idx)
            self.endRemoveRows()

    def clear(self):
        self.beginResetModel()
        self._entries.clear()
        self.endResetModel()

    def update_entry(self, file_path: str, status: str, row_count: int = 0, error: str = "", system_name: str = ""):
        for i, entry in enumerate(self._entries):
            if entry.file_path == file_path:
                entry.status = status
                entry.row_count = row_count
                entry.error_message = error
                if system_name:
                    entry.system_name = system_name
                self.dataChanged.emit(self.index(i, 0), self.index(i, self.columnCount() - 1))
                break

    def set_system_name(self, row: int, name: str):
        if 0 <= row < len(self._entries):
            self._entries[row].system_name = name
            idx = self.index(row, 2)
            self.dataChanged.emit(idx, idx)

    def sort_entries(self, key: str):
        self.beginResetModel()
        if key == "name":
            self._entries.sort(key=lambda e: e.filename.lower())
        elif key == "folder":
            self._entries.sort(key=lambda e: e.folder.lower())
        elif key == "modified":
            self._entries.sort(key=lambda e: e.modified_time, reverse=True)
        self.endResetModel()

    def deduplicate(self):
        self.beginResetModel()
        seen = set()
        unique = []
        for e in self._entries:
            if e.file_path not in seen:
                seen.add(e.file_path)
                unique.append(e)
        self._entries = unique
        self.endResetModel()

    def refresh_existence(self):
        for i, entry in enumerate(self._entries):
            if not os.path.exists(entry.file_path):
                entry.status = "Missing"
            elif entry.status == "Missing":
                entry.status = "Pending"
            self.dataChanged.emit(self.index(i, 0), self.index(i, self.columnCount() - 1))

    def flags(self, index):
        default = super().flags(index)
        if index.column() == 2:  # system name is editable
            return default | Qt.ItemIsEditable
        return default

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole and index.column() == 2:
            self._entries[index.row()].system_name = str(value)
            self.dataChanged.emit(index, index)
            return True
        return False


class FileListPanel(QWidget):
    files_changed = Signal()
    folder_dropped = Signal(str)  # emitted when a folder is dropped, for async scanning
    file_selected = Signal(str)   # emitted with file_path when a single row is selected
    traveler_dropped = Signal(str)  # emitted when a dropped file has an API-570 Traveler sheet

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.model = FileListModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # drag and drop
        self.table.setAcceptDrops(True)
        self.table.setDragDropMode(QAbstractItemView.DropOnly)
        self.table.viewport().setAcceptDrops(True)
        self.table.dragEnterEvent = self._drag_enter
        self.table.dragMoveEvent = self._drag_move
        self.table.dropEvent = self._drop

        # column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setCascadingSectionResizes(False)
        header.setStretchLastSection(True)
        header.setMinimumSectionSize(50)
        header.setDefaultSectionSize(150)
        header.sectionHandleDoubleClicked.connect(self._auto_fit_selected_columns)

        layout.addWidget(self.table)

        # emit file_selected when selection changes
        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def _auto_fit_selected_columns(self, clicked_logical_index: int):
        """Resize selected columns (and the double-clicked column) to fit
        the widest data-cell content, excluding the header text."""
        model = self.table.model()
        header = self.table.horizontalHeader()
        if not model or model.rowCount() == 0:
            return

        selected_cols: set[int] = set()
        selection = self.table.selectionModel().selectedIndexes()
        for idx in selection:
            selected_cols.add(idx.column())
        selected_cols.add(clicked_logical_index)

        fm = QFontMetrics(self.table.font())
        padding = 16
        min_width = header.minimumSectionSize()

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

    def _on_selection_changed(self):
        indices = self.table.selectionModel().selectedRows()
        if len(indices) == 1:
            row_idx = indices[0].row()
            entries = self.model.entries()
            if row_idx < len(entries):
                self.file_selected.emit(entries[row_idx].file_path)

    def _drag_enter(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drag_move(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drop(self, event: QDropEvent):
        paths = []
        folders = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                # Check if this file is a traveler spreadsheet
                if self._is_traveler_file(path):
                    self.traveler_dropped.emit(path)
                else:
                    paths.append(path)
            elif os.path.isdir(path):
                folders.append(path)
        if paths:
            self.model.add_files(paths)
            self.files_changed.emit()
        for folder in folders:
            self.folder_dropped.emit(folder)
        event.acceptProposedAction()

    @staticmethod
    def _is_traveler_file(path: str) -> bool:
        """Return True if the file contains an 'API-570 Traveler' sheet."""
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".xlsx", ".xlsm"):
            return False
        try:
            import openpyxl
            wb = openpyxl.load_workbook(path, read_only=True, data_only=False)
            names = [s.strip().lower() for s in wb.sheetnames]
            wb.close()
            return "api-570 traveler" in names
        except Exception:
            return False

    def _show_context_menu(self, pos):
        indices = self.table.selectionModel().selectedRows()
        menu = QMenu(self)

        if indices:
            row_idx = indices[0].row()
            entry = self.model.entries()[row_idx]

            open_file_action = QAction("Open File", self)
            open_file_action.triggered.connect(lambda _=None, p=entry.file_path: self._open_file(p))
            menu.addAction(open_file_action)

            open_folder_action = QAction("Open Containing Folder", self)
            open_folder_action.triggered.connect(lambda _=None, p=entry.file_path: self._open_folder(p))
            menu.addAction(open_folder_action)

            menu.addSeparator()

            copy_path_action = QAction("Copy Full Path", self)
            copy_path_action.triggered.connect(lambda _=None, p=entry.file_path: self._copy_to_clipboard(p))
            menu.addAction(copy_path_action)

            copy_name_action = QAction("Copy Filename", self)
            copy_name_action.triggered.connect(lambda _=None, n=entry.filename: self._copy_to_clipboard(n))
            menu.addAction(copy_name_action)

            menu.addSeparator()

            rename_action = QAction("Rename...", self)
            rename_action.triggered.connect(lambda _=None, r=row_idx: self._rename_file(r))
            menu.addAction(rename_action)

            move_action = QAction("Move to...", self)
            move_action.triggered.connect(lambda _=None, r=row_idx: self._move_file(r))
            menu.addAction(move_action)

            copy_to_action = QAction("Copy to...", self)
            copy_to_action.triggered.connect(lambda _=None, r=row_idx: self._copy_file(r))
            menu.addAction(copy_to_action)

            menu.addSeparator()

            remove_action = QAction("Remove from List", self)
            remove_action.triggered.connect(lambda _=None, idx=indices: self._remove_from_list(idx))
            menu.addAction(remove_action)

            menu.addSeparator()

            delete_action = QAction("Delete (Recycle Bin)", self)
            delete_action.triggered.connect(lambda _=None, idx=indices: self._delete_files(idx))
            menu.addAction(delete_action)

        menu.addSeparator()

        # sort submenu
        sort_menu = menu.addMenu("Sort by...")
        sort_name = QAction("Name", self)
        sort_name.triggered.connect(lambda: self.model.sort_entries("name"))
        sort_menu.addAction(sort_name)
        sort_folder = QAction("Folder", self)
        sort_folder.triggered.connect(lambda: self.model.sort_entries("folder"))
        sort_menu.addAction(sort_folder)
        sort_modified = QAction("Modified Time", self)
        sort_modified.triggered.connect(lambda: self.model.sort_entries("modified"))
        sort_menu.addAction(sort_modified)

        dedup_action = QAction("De-duplicate", self)
        dedup_action.triggered.connect(self.model.deduplicate)
        menu.addAction(dedup_action)

        refresh_action = QAction("Refresh File Status", self)
        refresh_action.triggered.connect(self.model.refresh_existence)
        menu.addAction(refresh_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _open_file(self, path: str):
        if os.path.exists(path):
            os.startfile(path)

    def _open_folder(self, path: str):
        folder = os.path.dirname(path)
        if os.path.isdir(folder):
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])

    def _copy_to_clipboard(self, text: str):
        QApplication.clipboard().setText(text)

    def _rename_file(self, row_idx: int):
        entry = self.model.entries()[row_idx]
        new_name, ok = QInputDialog.getText(
            self, "Rename File", "New filename:", text=entry.filename
        )
        if ok and new_name and new_name != entry.filename:
            old_path = entry.file_path
            new_path = os.path.join(entry.folder, new_name)
            try:
                os.rename(old_path, new_path)
                entry.file_path = new_path
                entry.filename = new_name
                self.model.dataChanged.emit(
                    self.model.index(row_idx, 0),
                    self.model.index(row_idx, self.model.columnCount() - 1),
                )
            except Exception as e:
                QMessageBox.warning(self, "Rename Failed", str(e))

    def _move_file(self, row_idx: int):
        entry = self.model.entries()[row_idx]
        dest_dir = QFileDialog.getExistingDirectory(self, "Move to folder", entry.folder)
        if dest_dir:
            new_path = os.path.join(dest_dir, entry.filename)
            try:
                shutil.move(entry.file_path, new_path)
                entry.file_path = new_path
                entry.folder = dest_dir
                self.model.dataChanged.emit(
                    self.model.index(row_idx, 0),
                    self.model.index(row_idx, self.model.columnCount() - 1),
                )
            except Exception as e:
                QMessageBox.warning(self, "Move Failed", str(e))

    def _copy_file(self, row_idx: int):
        entry = self.model.entries()[row_idx]
        dest_dir = QFileDialog.getExistingDirectory(self, "Copy to folder", entry.folder)
        if dest_dir:
            new_path = os.path.join(dest_dir, entry.filename)
            try:
                shutil.copy2(entry.file_path, new_path)
            except Exception as e:
                QMessageBox.warning(self, "Copy Failed", str(e))

    def _delete_files(self, indices):
        rows = sorted([i.row() for i in indices], reverse=True)
        reply = QMessageBox.question(
            self, "Delete Files",
            f"Send {len(rows)} file(s) to Recycle Bin?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        for row_idx in rows:
            entry = self.model.entries()[row_idx]
            try:
                send2trash(entry.file_path)
            except Exception:
                try:
                    os.remove(entry.file_path)
                except Exception as e:
                    QMessageBox.warning(self, "Delete Failed", str(e))
                    continue
            self.model.remove_rows([row_idx])
        self.files_changed.emit()

    def _remove_from_list(self, indices):
        rows = sorted([i.row() for i in indices], reverse=True)
        self.model.remove_rows(rows)
        self.files_changed.emit()

    def add_files(self, paths: list[str]):
        self.model.add_files(paths)
        self.files_changed.emit()

    def get_entries(self) -> list[FileEntry]:
        return self.model.entries()

    def clear(self):
        self.model.clear()
        self.files_changed.emit()
