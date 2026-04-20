import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QLineEdit, QFileDialog, QTableWidget, QTableWidgetItem, QCheckBox,
    QHeaderView, QMessageBox, QAbstractItemView, QApplication,
)
from PySide6.QtCore import Qt, QSettings

_SETTINGS_KEY = "search_folder"

def _load_search_folder() -> str:
    return QSettings("CMLBatchBuilder", "AwareImport").value(_SETTINGS_KEY, "", type=str)

def _save_search_folder(path: str):
    QSettings("CMLBatchBuilder", "AwareImport").setValue(_SETTINGS_KEY, path.strip())


class FuzzyMatchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fuzzy Match Entity Names")
        self.setMinimumSize(700, 500)
        self.matched_files: list[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # instructions
        layout.addWidget(QLabel("Paste entity names (one per line):"))

        self.names_input = QTextEdit()
        self.names_input.setPlaceholderText("REFG-010\nREFG-011\nREFG-012")
        self.names_input.setMaximumHeight(150)
        layout.addWidget(self.names_input)

        # folder picker
        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Search Folder:"))
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select folder to search...")
        saved = _load_search_folder()
        if saved:
            self.folder_input.setText(saved)
        folder_row.addWidget(self.folder_input, 1)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(browse_btn)
        layout.addLayout(folder_row)

        # match button
        match_btn = QPushButton("Find Matches")
        match_btn.clicked.connect(self._run_match)
        layout.addWidget(match_btn)

        # results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Entity Name", "Matched File", "Score"])
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.results_table)

        # buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        add_btn = QPushButton("Add Matched Files")
        add_btn.clicked.connect(self._accept_matches)
        btn_row.addWidget(add_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _browse_folder(self):
        start = self.folder_input.text().strip() or _load_search_folder()
        folder = QFileDialog.getExistingDirectory(self, "Select Search Folder", start)
        if folder:
            self.folder_input.setText(folder)
            _save_search_folder(folder)

    def _run_match(self):
        names_text = self.names_input.toPlainText().strip()
        folder = self.folder_input.text().strip()
        if not names_text or not folder:
            QMessageBox.warning(self, "Missing Input", "Enter entity names and select a folder.")
            return

        names = [n.strip() for n in names_text.splitlines() if n.strip()]

        from services.file_discovery import fuzzy_match_files
        results = fuzzy_match_files(names, folder)

        self.results_table.setRowCount(len(results))
        for i, (entity, matched, score) in enumerate(results):
            self.results_table.setItem(i, 0, QTableWidgetItem(entity))
            display_path = os.path.basename(matched) if matched else "(no match)"
            item = QTableWidgetItem(display_path)
            item.setToolTip(matched)
            self.results_table.setItem(i, 1, item)
            score_item = QTableWidgetItem(str(score))
            score_item.setTextAlignment(Qt.AlignCenter)
            self.results_table.setItem(i, 2, score_item)

        self._match_results = results

    def _accept_matches(self):
        if not hasattr(self, "_match_results"):
            return
        self.matched_files = [
            matched for _, matched, score in self._match_results
            if matched and score >= 60
        ]
        self.accept()


class SearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search for UT Sheets")
        self.setMinimumSize(750, 520)
        self.found_files: list[str] = []
        self._unmatched: list[str] = []
        self._search_results: list[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # folder (top row)
        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Search Folder:"))
        self.folder_input = QLineEdit()
        saved = _load_search_folder()
        if saved:
            self.folder_input.setText(saved)
        folder_row.addWidget(self.folder_input, 1)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(browse_btn)
        layout.addLayout(folder_row)

        # keyword / batch paste area
        kw_label = QLabel("Search (comma-separated keywords, or paste a list from Excel):")
        layout.addWidget(kw_label)
        self.keyword_input = QTextEdit()
        self.keyword_input.setPlaceholderText(
            "Keyword1, Keyword2, Keyword3\n\nOR paste multiple entity names (one per line):\nREFG-010\nREFG-011\nREFG-012"
        )
        self.keyword_input.setMaximumHeight(120)
        layout.addWidget(self.keyword_input)

        # filename filter
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filename must also contain:"))
        self.filter_input = QLineEdit()
        self.filter_input.setText("UT")
        self.filter_input.setPlaceholderText("e.g. UT, DR  (leave blank for no filter)")
        self.filter_input.setToolTip(
            "Only return files whose name also contains one of these terms.\n"
            "Separate multiple terms with commas, e.g. UT, DR.\n"
            "Use this to exclude VT, MT, CAD, etc. when entity names overlap."
        )
        filter_row.addWidget(self.filter_input, 1)
        layout.addLayout(filter_row)

        # options
        self.search_content_cb = QCheckBox("Also search inside Excel content (slower, single-keyword only)")
        layout.addWidget(self.search_content_cb)

        self.exact_match_cb = QCheckBox("Exact word match (e.g. 'DR' won't match 'Drain')")
        self.exact_match_cb.setToolTip(
            "When checked, search for whole words only.\n"
            "For example, 'DR' will match 'DR UT Report' but not 'Drain Report'."
        )
        layout.addWidget(self.exact_match_cb)

        # search button
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._run_search)
        layout.addWidget(search_btn)

        # unmatched summary label + action buttons (hidden until needed)
        self.unmatched_label = QLabel("")
        self.unmatched_label.setStyleSheet("color: #e67e22; padding: 2px;")
        self.unmatched_label.setWordWrap(True)
        self.unmatched_label.setVisible(False)
        layout.addWidget(self.unmatched_label)

        self._unmatched_btn_row = QHBoxLayout()
        self._copy_list_btn = QPushButton("Copy List")
        self._copy_list_btn.setToolTip("Copy missing names to clipboard (one per line)")
        self._copy_list_btn.clicked.connect(self._copy_unmatched_list)
        self._unmatched_btn_row.addWidget(self._copy_list_btn)
        self._copy_csv_btn = QPushButton("Copy CSV")
        self._copy_csv_btn.setToolTip("Copy missing names to clipboard (comma-separated)")
        self._copy_csv_btn.clicked.connect(self._copy_unmatched_csv)
        self._unmatched_btn_row.addWidget(self._copy_csv_btn)
        self._search_missing_btn = QPushButton("Search Missing in Another Directory...")
        self._search_missing_btn.setToolTip(
            "Browse for a different folder and search only for the\n"
            "missing entities listed above. New matches are appended\n"
            "to the results table without duplicating existing ones."
        )
        self._search_missing_btn.clicked.connect(self._search_missing_in_another_dir)
        self._unmatched_btn_row.addWidget(self._search_missing_btn)
        self._unmatched_btn_row.addStretch()
        layout.addLayout(self._unmatched_btn_row)
        self._set_unmatched_buttons_visible(False)

        # results
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Matched Term", "Filename", "Path"])
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.results_table)

        # buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        add_all_btn = QPushButton("Add All")
        add_all_btn.setToolTip("Add all results to the file list")
        add_all_btn.clicked.connect(self._accept_all_results)
        btn_row.addWidget(add_all_btn)
        add_btn = QPushButton("Add Selected")
        add_btn.clicked.connect(self._accept_results)
        btn_row.addWidget(add_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _browse_folder(self):
        start = self.folder_input.text().strip() or _load_search_folder()
        folder = QFileDialog.getExistingDirectory(self, "Select Search Folder", start)
        if folder:
            self.folder_input.setText(folder)
            _save_search_folder(folder)

    def _set_unmatched_buttons_visible(self, visible: bool):
        self._copy_list_btn.setVisible(visible)
        self._copy_csv_btn.setVisible(visible)
        self._search_missing_btn.setVisible(visible)

    def _update_unmatched_ui(self):
        if self._unmatched:
            self.unmatched_label.setText(
                f"No matches for {len(self._unmatched)} name(s): {', '.join(self._unmatched)}"
            )
            self.unmatched_label.setVisible(True)
            self._set_unmatched_buttons_visible(True)
        else:
            self.unmatched_label.setVisible(False)
            self._set_unmatched_buttons_visible(False)

    def _copy_unmatched_list(self):
        if self._unmatched:
            QApplication.clipboard().setText("\n".join(self._unmatched))

    def _copy_unmatched_csv(self):
        if self._unmatched:
            QApplication.clipboard().setText(", ".join(self._unmatched))

    def _search_missing_in_another_dir(self):
        if not self._unmatched:
            return
        start = self.folder_input.text().strip() or _load_search_folder()
        folder = QFileDialog.getExistingDirectory(self, "Select Folder for Missing Entities", start)
        if not folder:
            return

        name_filter = self.filter_input.text().strip()
        from services.file_discovery import batch_search_files
        new_matches, still_missing = batch_search_files(
            self._unmatched, folder, name_filter=name_filter,
            exact_match=self.exact_match_cb.isChecked(),
        )

        # Append new matches to results table, skip duplicates
        existing_paths = set(self._search_results)
        added = 0
        for kw, fpath in new_matches:
            if fpath in existing_paths:
                continue
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(kw))
            self.results_table.setItem(row, 1, QTableWidgetItem(os.path.basename(fpath)))
            self.results_table.setItem(row, 2, QTableWidgetItem(fpath))
            self._search_results.append(fpath)
            existing_paths.add(fpath)
            added += 1

        self._unmatched = still_missing
        self._update_unmatched_ui()

        if added:
            QMessageBox.information(
                self, "Re-Search Results",
                f"Found {added} additional file(s) in:\n{folder}\n\n"
                f"Still missing: {len(self._unmatched)} name(s)."
            )
        else:
            QMessageBox.information(
                self, "Re-Search Results",
                f"No new matches found in:\n{folder}"
            )

    def _run_search(self):
        raw_text = self.keyword_input.toPlainText().strip()
        folder = self.folder_input.text().strip()
        if not raw_text or not folder:
            QMessageBox.warning(self, "Missing Input", "Enter a keyword and select a folder.")
            return

        name_filter = self.filter_input.text().strip()
        lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]

        # Support comma-separated keywords on a single line
        if len(lines) == 1 and "," in lines[0]:
            lines = [k.strip() for k in lines[0].split(",") if k.strip()]

        if len(lines) > 1:
            # --- Batch mode: multiple entity names pasted ---
            from services.file_discovery import batch_search_files
            matches, unmatched = batch_search_files(lines, folder, name_filter=name_filter, exact_match=self.exact_match_cb.isChecked())

            self.results_table.setRowCount(len(matches))
            self._search_results = [fpath for _, fpath in matches]
            for i, (kw, fpath) in enumerate(matches):
                self.results_table.setItem(i, 0, QTableWidgetItem(kw))
                self.results_table.setItem(i, 1, QTableWidgetItem(os.path.basename(fpath)))
                self.results_table.setItem(i, 2, QTableWidgetItem(fpath))

            self._unmatched = unmatched
            self._update_unmatched_ui()
        else:
            # --- Single keyword mode ---
            from services.file_discovery import search_files_by_keyword
            keyword = lines[0]
            results = search_files_by_keyword(
                keyword, folder, self.search_content_cb.isChecked(), name_filter=name_filter, exact_match=self.exact_match_cb.isChecked(),
            )

            self.results_table.setRowCount(len(results))
            self._search_results = results
            for i, fpath in enumerate(results):
                self.results_table.setItem(i, 0, QTableWidgetItem(keyword))
                self.results_table.setItem(i, 1, QTableWidgetItem(os.path.basename(fpath)))
                self.results_table.setItem(i, 2, QTableWidgetItem(fpath))

            self._unmatched = []
            self._update_unmatched_ui()

    def _accept_all_results(self):
        if not hasattr(self, "_search_results") or not self._search_results:
            return
        self.found_files = list(self._search_results)
        self.accept()

    def _accept_results(self):
        if not hasattr(self, "_search_results"):
            return
        selected = self.results_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "No Selection", "Select one or more files to add.")
            return
        indices = [idx.row() for idx in selected]
        self.found_files = [self._search_results[i] for i in indices]
        self.accept()
