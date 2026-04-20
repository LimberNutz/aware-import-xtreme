"""
File Scout
----------
A powerful and intuitive utility for auditing and finding files across directories.
Features advanced filtering, duplicate finding, interactive results, and profile management.
"""

import os
import sys
import datetime
import json
import csv
import subprocess
from pathlib import Path
import mimetypes
import hashlib
import argparse
import shutil

# PyMuPDF — needed by PDFViewerWidget (stays in monolith)
try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from send2trash import send2trash
except Exception:
    send2trash = None

# Quiet benign Qt logs and stabilize HiDPI behavior before importing PyQt6 modules
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.screen=false;qt.svg.warning=false")
os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "RoundPreferFloor")

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QFileDialog, QProgressBar, QTableWidget, QComboBox,
                             QCheckBox, QGroupBox, QGridLayout, QMessageBox,
                             QListWidget, QSplitter, QDateEdit, QMenu,
                             QInputDialog, QTableWidgetItem, QHeaderView,
                             QDialog, QDialogButtonBox, QListWidgetItem, QWidgetAction,
                             QStatusBar, QTextEdit, QTabWidget, QSystemTrayIcon, QScrollArea,
                             QButtonGroup, QRadioButton)
from PyQt6.QtCore import Qt, QSize, QDate, QSettings, QTimer, QEvent, QPoint, QRect
from PyQt6.QtGui import QIcon, QColor, QAction, QActionGroup, QBrush, QPixmap, QGuiApplication, QFont, QImage, QPainter, QPen

# File Audit Dialog (Google Drive integration)
try:
    from ui.dialogs.file_audit_dialog import FileAuditDialog
    FILE_AUDIT_AVAILABLE = True
except ImportError:
    FILE_AUDIT_AVAILABLE = False

# --- Extracted modules (Phase 1) ---
from constants import (APP_NAME, APP_VERSION,
                       PreviewResult, ICON_SEARCH, ICON_STOP, ICON_EXPORT,
                       FILE_TYPE_MAPPINGS)
from config import get_settings
from utils.themes import THEME_COLORS
from utils.excel_exporter import ExcelExporter
from ui.widgets.custom_widgets import DropLineEdit
from features.preview.manager import PreviewManager
from ui.dialogs.profile_manager import ProfileManagerDialog
from ui.dialogs.smart_sort_dialog import SmartSortDialog
from core.file_scanner import FileSearchWorker
from core.search_engine import SearchEngine

class PDFViewerWidget(QWidget):
    """Full PDF viewer with pan, zoom, navigation, and search capabilities."""
    
    # Constants for PDF viewer
    SCROLLBAR_MARGIN = 40  # Margin for scrollbars
    MIN_WIDGET_WIDTH = 100  # Minimum widget width for calculations
    ZOOM_STEP = 1.2  # Zoom in/out multiplier
    MIN_ZOOM = 0.1  # Minimum zoom level
    MAX_ZOOM = 5.0  # Maximum zoom level
    DEFAULT_ZOOM = 1.0  # Default zoom level
    
    # Highlight colors
    HIGHLIGHT_COLOR = QColor(255, 255, 0, 100)  # Semi-transparent yellow
    CURRENT_MATCH_COLOR = QColor(255, 0, 0)  # Red
    CURRENT_MATCH_BORDER_WIDTH = 3  # Border width for current match
    
    def __init__(self):
        super().__init__()
        self.current_pdf = None
        self.current_page = 0
        self.zoom_factor = self.DEFAULT_ZOOM
        self.search_results = []
        self.current_search_index = 0
        self.search_cache = {}  # Cache search results by search term
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the PDF viewer UI."""
        layout = QVBoxLayout()
        
        # Toolbar with controls
        toolbar_layout = QHBoxLayout()
        
        # Navigation controls
        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.clicked.connect(self.previous_page)
        self.prev_btn.setEnabled(False)
        
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)
        
        self.page_label = QLabel("Page: 0 / 0")
        
        # Zoom controls
        self.zoom_out_btn = QPushButton("🔍−")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        
        self.zoom_label = QLabel("100%")
        
        self.zoom_in_btn = QPushButton("🔍+")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        
        self.fit_btn = QPushButton("Fit Width")
        self.fit_btn.clicked.connect(self.fit_width)
        
        # Pan controls
        self.pan_btn = QPushButton("✋ Drag Pan")
        self.pan_btn.setCheckable(True)
        self.pan_btn.setChecked(False)
        self.pan_btn.setToolTip("Enable mouse drag panning (click and drag to pan)")
        self.pan_btn.clicked.connect(self.toggle_pan_mode)
        
        self.reset_view_btn = QPushButton("⟲ Reset View")
        self.reset_view_btn.clicked.connect(self.reset_view)
        
        # Search controls
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in PDF...")
        self.search_input.returnPressed.connect(self.search_pdf)
        
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.clicked.connect(self.search_pdf)
        
        self.next_search_btn = QPushButton("Next ▶")
        self.next_search_btn.clicked.connect(self.next_search_result)
        self.next_search_btn.setEnabled(False)
        
        # Add controls to toolbar
        toolbar_layout.addWidget(self.prev_btn)
        toolbar_layout.addWidget(self.next_btn)
        toolbar_layout.addWidget(self.page_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.zoom_out_btn)
        toolbar_layout.addWidget(self.zoom_label)
        toolbar_layout.addWidget(self.zoom_in_btn)
        toolbar_layout.addWidget(self.fit_btn)
        toolbar_layout.addWidget(self.pan_btn)
        toolbar_layout.addWidget(self.reset_view_btn)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.search_input)
        toolbar_layout.addWidget(self.search_btn)
        toolbar_layout.addWidget(self.next_search_btn)
        
        # Scroll area for PDF display
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # PDF display label with mouse tracking for panning
        self.pdf_label = QLabel()
        self.pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        self.pdf_label.setText("No PDF loaded")
        self.pdf_label.setMouseTracking(True)  # Enable mouse tracking for pan hints
        
        self.scroll_area.setWidget(self.pdf_label)
        
        # Pan state for mouse drag panning
        self.pan_start_pos = None
        self.scroll_start_pos = None
        
        # Status bar — large enough to read easily
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #333; font-size: 14px; font-weight: bold; padding: 4px;")
        
        # Add everything to main layout
        layout.addLayout(toolbar_layout)
        layout.addWidget(self.scroll_area)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Enable mouse events for panning using event filter
        self.pdf_label.installEventFilter(self)
    
    def __del__(self):
        """Destructor to ensure PDF resources are freed."""
        if hasattr(self, 'current_pdf') and self.current_pdf:
            try:
                self.current_pdf.close()
            except Exception:
                pass
    
    def toggle_pan_mode(self):
        """Toggle drag pan mode on/off."""
        is_pan_mode = self.pan_btn.isChecked()
        if is_pan_mode:
            self.pdf_label.setCursor(Qt.CursorShape.OpenHandCursor)
            self.status_label.setText("Drag pan mode enabled - Click and drag to pan")
        else:
            self.pdf_label.setCursor(Qt.CursorShape.ArrowCursor)
            self.status_label.setText("Drag pan mode disabled")
    
    def reset_view(self):
        """Reset view to fit width and scroll to top."""
        if self.current_pdf:
            self.fit_width()
            self.scroll_area.verticalScrollBar().setValue(0)
            self.scroll_area.horizontalScrollBar().setValue(0)
            self.status_label.setText("View reset to fit width")
    
    def eventFilter(self, obj, event):
        """Handle events for mouse drag panning with error handling.
        
        Supports left-click and hold panning without requiring pan button toggle.
        """
        try:
            if obj is self.pdf_label:
                # Handle left-click drag panning (always enabled)
                if event.type() == QEvent.Type.MouseButtonPress:
                    if event.button() == Qt.MouseButton.LeftButton and self.current_pdf:
                        self.pan_start_pos = event.position()
                        self.scroll_start_pos = QPoint(
                            self.scroll_area.horizontalScrollBar().value(),
                            self.scroll_area.verticalScrollBar().value()
                        )
                        self.pdf_label.setCursor(Qt.CursorShape.ClosedHandCursor)
                        return True  # Event handled
                        
                elif event.type() == QEvent.Type.MouseMove:
                    if self.pan_start_pos is not None:
                        # Calculate the delta movement
                        delta = event.position() - self.pan_start_pos
                        
                        # Update scroll position
                        new_h_scroll = self.scroll_start_pos.x() - delta.x()
                        new_v_scroll = self.scroll_start_pos.y() - delta.y()
                        
                        # Set new scroll position
                        self.scroll_area.horizontalScrollBar().setValue(int(new_h_scroll))
                        self.scroll_area.verticalScrollBar().setValue(int(new_v_scroll))
                        
                        return True  # Event handled
                        
                elif event.type() == QEvent.Type.MouseButtonRelease:
                    if event.button() == Qt.MouseButton.LeftButton:
                        self.pan_start_pos = None
                        self.scroll_start_pos = None
                        # Restore cursor based on pan button state
                        if self.pan_btn.isChecked():
                            self.pdf_label.setCursor(Qt.CursorShape.OpenHandCursor)
                        else:
                            self.pdf_label.setCursor(Qt.CursorShape.ArrowCursor)
                        return True  # Event handled
        except Exception as e:
            # Silently handle errors to prevent crashes during pan operations
            self.pan_start_pos = None
            self.scroll_start_pos = None
            if hasattr(self, 'pdf_label'):
                self.pdf_label.setCursor(Qt.CursorShape.ArrowCursor)
            return False
        
        # Let parent class handle other events
        return super().eventFilter(obj, event)
    
    def load_pdf(self, file_path):
        """Load a PDF file for viewing."""
        try:
            if not PYMUPDF_AVAILABLE:
                self.status_label.setText("Error: PyMuPDF not installed")
                return
            
            # Close old PDF to free resources
            if self.current_pdf:
                try:
                    self.current_pdf.close()
                except Exception:
                    pass
            
            self.current_pdf = fitz.open(str(file_path))
            self.current_page = 0
            self.zoom_factor = self.DEFAULT_ZOOM
            self.search_results = []
            self.current_search_index = 0
            self.search_cache = {}  # Clear search cache for new PDF
            
            self.update_page(auto_fit=False)  # Load at 100% zoom initially
            self.update_controls()
            self.status_label.setText(f"Loaded: {Path(file_path).name}")
            
        except Exception as e:
            self.status_label.setText(f"Error loading PDF: {e}")
            self.pdf_label.setText("Failed to load PDF")
    
    def update_page(self, auto_fit=False, highlight_rects=None):
        """Update the current page display with optional highlighting.
        
        Uses PyMuPDF native annotations for pixel-perfect highlighting.
        Annotations are added before rendering and removed immediately after.
        """
        if not self.current_pdf or self.current_page >= self.current_pdf.page_count:
            return
        
        try:
            page = self.current_pdf[self.current_page]
            
            # Only auto-fit if specifically requested
            if auto_fit:
                widget_width = self.scroll_area.width() - self.SCROLLBAR_MARGIN
                if widget_width > self.MIN_WIDGET_WIDTH:
                    page_width = page.rect.width
                    self.zoom_factor = widget_width / page_width
            
            # Add temporary highlight annotations before rendering
            temp_annots = []
            if highlight_rects:
                for rect in highlight_rects:
                    try:
                        annot = page.add_highlight_annot(rect)
                        annot.set_colors(stroke=(1, 1, 0))  # Yellow highlight
                        annot.set_opacity(0.4)
                        annot.update()
                        temp_annots.append(annot)
                    except Exception:
                        continue
                
                # Add a distinctive rectangle annotation for the current match
                if hasattr(self, 'search_results') and self.search_results:
                    if self.current_search_index < len(self.search_results):
                        current_result = self.search_results[self.current_search_index]
                        if current_result['page'] == self.current_page:
                            try:
                                cur_rect = current_result['rect']
                                annot = page.add_rect_annot(cur_rect)
                                annot.set_colors(stroke=(1, 0, 0))  # Red border
                                annot.set_border(width=2)
                                annot.update()
                                temp_annots.append(annot)
                            except Exception:
                                pass
            
            # Render page with current zoom
            matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            pix = page.get_pixmap(matrix=matrix)
            
            # Convert to QImage and display
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            
            # Remove temporary annotations after rendering
            for annot in temp_annots:
                try:
                    page.delete_annot(annot)
                except Exception:
                    pass
            
            self.pdf_label.setPixmap(pixmap)
            self.pdf_label.setFixedSize(pixmap.size())
            
        except Exception as e:
            self.status_label.setText(f"Error rendering page: {e}")
    
    # _add_highlighting removed - now using PyMuPDF native annotations in update_page()
    
    def update_controls(self):
        """Update the state of navigation controls."""
        if self.current_pdf:
            total_pages = self.current_pdf.page_count
            self.page_label.setText(f"Page: {self.current_page + 1} / {total_pages}")
            
            self.prev_btn.setEnabled(self.current_page > 0)
            self.next_btn.setEnabled(self.current_page < total_pages - 1)
            
            self.zoom_label.setText(f"{int(self.zoom_factor * 100)}%")
        else:
            self.page_label.setText("Page: 0 / 0")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.zoom_label.setText("100%")
    
    def previous_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            # Clear highlights when navigating normally (not via search)
            self.update_page(auto_fit=False, highlight_rects=None)
            self.update_controls()
    
    def next_page(self):
        """Go to next page."""
        if self.current_pdf and self.current_page < self.current_pdf.page_count - 1:
            self.current_page += 1
            # Clear highlights when navigating normally (not via search)
            self.update_page(auto_fit=False, highlight_rects=None)
            self.update_controls()
    
    def zoom_in(self):
        """Zoom in the PDF view."""
        self.zoom_factor = min(self.zoom_factor * self.ZOOM_STEP, self.MAX_ZOOM)
        # Preserve highlights if we're on a search result page
        highlight_rects = self._get_current_page_highlights() if self.search_results else None
        self.update_page(auto_fit=False, highlight_rects=highlight_rects)
        self.update_controls()
    
    def zoom_out(self):
        """Zoom out the PDF view."""
        self.zoom_factor = max(self.zoom_factor / self.ZOOM_STEP, self.MIN_ZOOM)
        # Preserve highlights if we're on a search result page
        highlight_rects = self._get_current_page_highlights() if self.search_results else None
        self.update_page(auto_fit=False, highlight_rects=highlight_rects)
        self.update_controls()
    
    def _get_current_page_highlights(self):
        """Get highlight rectangles for the current page if we have search results."""
        if not self.search_results:
            return None
        
        current_page_rects = []
        for search_result in self.search_results:
            if search_result['page'] == self.current_page:
                current_page_rects.append(search_result['rect'])
        
        return current_page_rects if current_page_rects else None
    
    def fit_width(self):
        """Fit PDF to widget width."""
        if self.current_pdf and self.current_page < self.current_pdf.page_count:
            try:
                page = self.current_pdf[self.current_page]
                widget_width = self.scroll_area.width() - self.SCROLLBAR_MARGIN
                if widget_width > self.MIN_WIDGET_WIDTH:
                    page_width = page.rect.width
                    self.zoom_factor = widget_width / page_width
                    self.update_page(auto_fit=False)  # Don't auto-fit again
                    self.update_controls()
            except Exception as e:
                self.status_label.setText(f"Error fitting width: {e}")
    
    def search_pdf(self):
        """Search for text in the PDF with visual highlighting and caching."""
        if not self.current_pdf or not self.search_input.text().strip():
            return
        
        search_text = self.search_input.text().strip()
        
        # Check cache first to avoid redundant searches
        if search_text in self.search_cache:
            self.search_results = self.search_cache[search_text]
            if self.search_results:
                self.current_search_index = 0
                self.go_to_search_result(0)
                self.next_search_btn.setEnabled(len(self.search_results) > 1)
                self.status_label.setText(f"Found {len(self.search_results)} matches (cached)")
            else:
                self.update_page(auto_fit=False)
                self.status_label.setText("No matches found (cached)")
                self.next_search_btn.setEnabled(False)
            return
        
        self.search_results = []
        
        try:
            # Search through all pages and collect all matches (standard text)
            for page_num in range(self.current_pdf.page_count):
                page = self.current_pdf[page_num]
                text_instances = page.search_for(search_text)
                
                for inst in text_instances:
                    self.search_results.append({
                        'page': page_num,
                        'rect': inst,
                        'text': search_text
                    })
            
            # If no results found, try OCR fallback for CAD/vector PDFs
            if not self.search_results:
                self.search_results = self._search_with_ocr(search_text)
            
            # Cache the search results
            self.search_cache[search_text] = self.search_results
            
            if self.search_results:
                self.current_search_index = 0
                self.go_to_search_result(0)
                self.next_search_btn.setEnabled(len(self.search_results) > 1)
                self.status_label.setText(f"Found {len(self.search_results)} matches")
            else:
                # Clear any existing highlights
                self.update_page(auto_fit=False)
                self.status_label.setText("No matches found")
                self.next_search_btn.setEnabled(False)
                
        except Exception as e:
            self.status_label.setText(f"Search error: {e}")
    
    def _search_with_ocr(self, search_text):
        """Fallback search using OCR for CAD/vector PDFs where text is rendered as graphics.
        
        Uses PyMuPDF's built-in OCR via Tesseract to recognize text in the page image,
        then searches the OCR output for the query. This handles CAD drawings, scanned
        documents, and PDFs where text is stored as vector paths.
        """
        import os
        
        # Ensure Tesseract is discoverable
        tesseract_dir = r"C:\Program Files\Tesseract-OCR"
        if os.path.isdir(tesseract_dir) and tesseract_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = tesseract_dir + os.pathsep + os.environ["PATH"]
        
        ocr_results = []
        total_pages = self.current_pdf.page_count
        
        try:
            for page_num in range(total_pages):
                self.status_label.setText(f"OCR scanning page {page_num + 1}/{total_pages}...")
                QApplication.processEvents()  # Keep UI responsive
                
                page = self.current_pdf[page_num]
                
                # Build an OCR-enhanced textpage
                tp = page.get_textpage_ocr(dpi=300, full=True)
                
                # Search using the OCR textpage
                text_instances = page.search_for(search_text, textpage=tp)
                
                for inst in text_instances:
                    ocr_results.append({
                        'page': page_num,
                        'rect': inst,
                        'text': search_text
                    })
            
            if ocr_results:
                self.status_label.setText(f"Found {len(ocr_results)} matches (via OCR)")
            
        except Exception as e:
            # OCR not available — fail silently
            self.status_label.setText(f"No matches found (OCR unavailable: {e})")
        
        return ocr_results
    
    def next_search_result(self):
        """Go to next search result."""
        if self.search_results:
            self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
            self.go_to_search_result(self.current_search_index)
    
    def go_to_search_result(self, index):
        """Navigate to a specific search result with visual highlighting."""
        if 0 <= index < len(self.search_results):
            result = self.search_results[index]
            
            # Go to the page with the match
            self.current_page = result['page']
            
            # Collect all rectangles for the current page to highlight them
            current_page_rects = []
            for search_result in self.search_results:
                if search_result['page'] == self.current_page:
                    current_page_rects.append(search_result['rect'])
            
            # Update page with highlighting
            self.update_page(auto_fit=False, highlight_rects=current_page_rects)
            self.update_controls()
            
            # Highlight the found text (visual feedback)
            self.status_label.setText(f"Match {index + 1}/{len(self.search_results)} on page {result['page'] + 1}")
    
    def resizeEvent(self, event):
        """Handle resize events to maintain zoom."""
        super().resizeEvent(event)
        # Removed auto-fit on resize to respect manual zoom levels
    
    def wheelEvent(self, event):
        """Handle Ctrl+Mouse Wheel for zooming."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Get the angle delta (positive = zoom in, negative = zoom out)
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)


class FileScoutApp(QMainWindow):
    """Main application window for File Scout."""
    def __init__(self, cli_args=None):
        super().__init__()
        self.settings = get_settings()
        self.search_worker = None
        self.matching_files = []
        self.current_theme = 'light'
        self.duplicate_group_colors = [QColor("#FADBD8"), QColor("#D6EAF8"), QColor("#D1F2EB"), QColor("#FCF3CF"), QColor("#E8DAEF")]
        self.duplicate_group_counter = 0
        self.zoom_level = 100  # Default zoom percentage
        self.base_font_size = 9  # Base font size in points
        self.base_spacing = 10  # Base layout spacing in pixels
        self.base_groupbox_top_margin = 5  # Base top margin for QGroupBox content
        self.base_groupbox_margin_top = 10  # Base margin-top for QGroupBox in stylesheet
        self.base_groupbox_title_padding = 5  # Base title padding for QGroupBox
        
        # Result batching for performance
        self.result_batch = []
        self.batch_size = 50  # Add results in batches of 50
        self.display_limit = 5000  # Initial display limit
        self.hidden_results = []  # Results beyond display limit
        
        # Persistent File Audit Dialog (so results persist between opens)
        self.file_audit_dialog = None
        
        # System tray icon state
        self.tray_icon = None
        self.is_closing = False

        self._init_window()
        self._create_actions()
        self._create_menu_bar()
        self._create_main_widget()
        self._create_status_bar()
        self._create_system_tray()
        # Undo state for recycle-bin deletes
        self._undo_stack = []  # list of batches (list[str]) of original full paths
        self._last_delete_batch = None
        # Ensure button reflects initial state
        self._update_undo_button()
        
        self.load_settings()
        self.apply_theme(self.settings.value("theme", "light"))

        if cli_args:
            if cli_args.dir:
                # Set up directory and mode from command line
                QTimer.singleShot(100, lambda: self.setup_from_cli(cli_args))
            elif hasattr(cli_args, 'output') and cli_args.output:
                # Full CLI mode with output file
                QTimer.singleShot(100, lambda: self.run_from_cli(cli_args))

    def _init_window(self):
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1000, 700)

    def _create_actions(self):
        self.save_profile_action = QAction("Save Search Profile...", self)
        self.save_profile_action.triggered.connect(self.save_search_profile)
        self.manage_profiles_action = QAction("Manage Profiles...", self)
        self.manage_profiles_action.triggered.connect(self.manage_profiles)
        # Smart Sort action
        self.smart_sort_action = QAction("Smart Sort...", self)
        self.smart_sort_action.triggered.connect(self.open_smart_sort_dialog)
        # File Audit action (Google Drive)
        self.file_audit_action = QAction("File Audit (Google Drive)...", self)
        self.file_audit_action.triggered.connect(self.open_file_audit)
        self.file_audit_action.setEnabled(FILE_AUDIT_AVAILABLE)
        # Zoom actions
        self.zoom_in_action = QAction("Zoom In", self)
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_in_action.triggered.connect(self.zoom_in)
        self.zoom_out_action = QAction("Zoom Out", self)
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_out_action.triggered.connect(self.zoom_out)
        self.zoom_reset_action = QAction("Reset Zoom", self)
        self.zoom_reset_action.setShortcut("Ctrl+0")
        self.zoom_reset_action.triggered.connect(self.zoom_reset)
        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.quit_application)
        
        # Minimize to tray action
        self.minimize_to_tray_action = QAction("Minimize to Tray", self)
        self.minimize_to_tray_action.setShortcut("Ctrl+H")
        self.minimize_to_tray_action.triggered.connect(self.hide)

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.save_profile_action)
        file_menu.addAction(self.manage_profiles_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        settings_menu = menu_bar.addMenu("&Settings")
        theme_menu = settings_menu.addMenu("Theme")
        self.theme_action_group = QActionGroup(self)
        for theme_name in THEME_COLORS.keys():
            action = QAction(theme_name.replace('_', ' ').title(), self, checkable=True)
            action.triggered.connect(lambda checked, name=theme_name: self.apply_theme(name))
            self.theme_action_group.addAction(action)
            theme_menu.addAction(action)

        perf_menu = settings_menu.addMenu("Performance")
        self.count_files_checkbox = QCheckBox("Pre-count files for progress bar")
        self.count_files_checkbox.setChecked(True)
        count_action = QWidgetAction(self)
        count_action.setDefaultWidget(self.count_files_checkbox)
        perf_menu.addAction(count_action)
        
        # Tools menu
        tools_menu = menu_bar.addMenu("&Tools")
        tools_menu.addAction(self.smart_sort_action)
        tools_menu.addAction(self.file_audit_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)
        view_menu.addAction(self.zoom_reset_action)
        view_menu.addSeparator()
        # Preset zoom levels
        zoom_presets_menu = view_menu.addMenu("Zoom Presets")
        for zoom_pct in [75, 100, 125, 150, 175, 200]:
            action = QAction(f"{zoom_pct}%", self)
            action.triggered.connect(lambda checked, z=zoom_pct: self.set_zoom(z))
            zoom_presets_menu.addAction(action)
        view_menu.addSeparator()
        view_menu.addAction(self.minimize_to_tray_action)

    def _create_main_widget(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        search_panel = self._create_search_panel()
        results_panel = self._create_results_panel()
        splitter.addWidget(search_panel)
        splitter.addWidget(results_panel)
        splitter.setSizes([350, 650])

    def _create_search_panel(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(self.base_spacing)
        self.search_panel_layout = layout  # Store reference for zoom scaling

        mode_group = QGroupBox("Search Mode")
        mode_layout = QHBoxLayout()
        mode_layout.setContentsMargins(5, self.base_groupbox_top_margin, 5, 5)  # Add top margin
        self.search_mode_combo = QComboBox()
        self.search_mode_combo.addItems(["Find Files", "Find Duplicates"])
        self.search_mode_combo.setToolTip("Select 'Find Files' for normal search or 'Find Duplicates' to locate identical files.")
        self.search_mode_combo.currentIndexChanged.connect(self.toggle_search_mode_ui)
        mode_layout.addWidget(self.search_mode_combo)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        dir_group = QGroupBox("Search Directory")
        dir_layout = QHBoxLayout()
        dir_layout.setContentsMargins(5, self.base_groupbox_top_margin, 5, 5)  # Add top margin
        self.dir_input = DropLineEdit()
        self.dir_input.setPlaceholderText("Drag & drop a folder here or click Browse...")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(browse_btn)
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)

        self.keywords_group = QGroupBox("Keyword Filters")
        keywords_layout = QGridLayout()
        keywords_layout.setContentsMargins(5, self.base_groupbox_top_margin, 5, 5)  # Add top margin
        keywords_layout.addWidget(QLabel("Keywords:"), 0, 0)
        self.keywords_input = QLineEdit()
        self.keywords_input.setPlaceholderText("comma, separated, list")
        self.keywords_input.setToolTip("Find files with these words in the filename.")
        keywords_layout.addWidget(self.keywords_input, 0, 1)
        keywords_layout.addWidget(QLabel("Exclusions:"), 1, 0)
        self.exclusion_keywords_input = QLineEdit()
        self.exclusion_keywords_input.setPlaceholderText("ignore, these, words")
        self.exclusion_keywords_input.setToolTip("Exclude files with these words in the filename.")
        keywords_layout.addWidget(self.exclusion_keywords_input, 1, 1)
        
        self.regex_checkbox = QCheckBox("Use Regular Expressions")
        self.regex_checkbox.setToolTip("Treat keywords as powerful RegEx patterns.")
        self.whole_words_checkbox = QCheckBox("Match Whole Words Only")
        self.whole_words_checkbox.setToolTip("Ensure keywords match as a whole word (e.g., 'cat' won't match 'category').")
        self.regex_checkbox.stateChanged.connect(lambda state: self.whole_words_checkbox.setEnabled(not state))
        keywords_layout.addWidget(self.regex_checkbox, 2, 0, 1, 2)
        keywords_layout.addWidget(self.whole_words_checkbox, 3, 0, 1, 2)
        
        keywords_layout.addWidget(QLabel("Content Search:"), 4, 0)
        self.content_search_checkbox = QCheckBox("Search in file content")
        self.content_search_checkbox.setToolTip("Search for text within file contents (text files only).")
        keywords_layout.addWidget(self.content_search_checkbox, 4, 1)
        self.content_search_input = QLineEdit()
        self.content_search_input.setPlaceholderText("Text to find in files")
        self.content_search_input.setEnabled(False)
        keywords_layout.addWidget(self.content_search_input, 5, 0, 1, 2)
        self.content_search_checkbox.stateChanged.connect(lambda state: self.content_search_input.setEnabled(state))
        
        self.keywords_group.setLayout(keywords_layout)
        layout.addWidget(self.keywords_group)
        
        # --- MODIFIED: Added QLineEdit for custom extensions ---
        file_filter_group = QGroupBox("File Filters")
        file_filter_layout = QGridLayout()
        file_filter_layout.setContentsMargins(5, self.base_groupbox_top_margin, 5, 5)  # Add top margin
        file_filter_layout.addWidget(QLabel("Type Preset:"), 0, 0)
        self.file_types_combo = QComboBox()
        self.file_types_combo.addItems(FILE_TYPE_MAPPINGS.keys())
        file_filter_layout.addWidget(self.file_types_combo, 0, 1)
        file_filter_layout.addWidget(QLabel("Custom Exts:"), 1, 0)
        self.custom_exts_input = QLineEdit()
        self.custom_exts_input.setPlaceholderText(".ext1, .ext2, ext3")
        file_filter_layout.addWidget(self.custom_exts_input, 1, 1)
        file_filter_group.setLayout(file_filter_layout)
        layout.addWidget(file_filter_group)
        # --- END MODIFICATION ---

        size_group = QGroupBox("File Size Filter (KB)")
        size_layout = QHBoxLayout()
        size_layout.setContentsMargins(5, self.base_groupbox_top_margin, 5, 5)  # Add top margin
        size_layout.addWidget(QLabel("Min:"))
        self.min_size_input = QLineEdit()
        size_layout.addWidget(self.min_size_input)
        size_layout.addWidget(QLabel("Max:"))
        self.max_size_input = QLineEdit()
        size_layout.addWidget(self.max_size_input)
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)

        date_group = QGroupBox("Date Filter")
        date_layout = QGridLayout()
        date_layout.setContentsMargins(5, self.base_groupbox_top_margin, 5, 5)  # Add top margin
        self.use_date_filter = QCheckBox("Enable Date Filter")
        date_layout.addWidget(self.use_date_filter, 0, 0, 1, 2)
        date_layout.addWidget(QLabel("Filter by:"), 1, 0)
        self.date_filter_type = QComboBox()
        self.date_filter_type.addItems(["Modified Date", "Creation Date"])
        date_layout.addWidget(self.date_filter_type, 1, 1)
        date_layout.addWidget(QLabel("From:"), 2, 0)
        self.min_date_edit = QDateEdit(calendarPopup=True, date=QDate.currentDate().addYears(-1))
        date_layout.addWidget(self.min_date_edit, 2, 1)
        date_layout.addWidget(QLabel("To:"), 3, 0)
        self.max_date_edit = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        date_layout.addWidget(self.max_date_edit, 3, 1)
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)

        exclude_group = QGroupBox("Excluded Directories")
        exclude_layout = QVBoxLayout()
        exclude_layout.setContentsMargins(5, self.base_groupbox_top_margin, 5, 5)  # Add top margin
        self.exclude_dirs_list = QListWidget()
        exclude_layout.addWidget(self.exclude_dirs_list)
        exclude_btn_layout = QHBoxLayout()
        add_dir_btn = QPushButton("Add")
        add_dir_btn.clicked.connect(self.add_excluded_dir)
        remove_dir_btn = QPushButton("Remove")
        remove_dir_btn.clicked.connect(self.remove_excluded_dir)
        exclude_btn_layout.addWidget(add_dir_btn)
        exclude_btn_layout.addWidget(remove_dir_btn)
        exclude_layout.addLayout(exclude_btn_layout)
        exclude_group.setLayout(exclude_layout)
        layout.addWidget(exclude_group)

        layout.addStretch()
        scroll_area.setWidget(panel)
        return scroll_area

    def _create_results_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        search_control_layout = QHBoxLayout()
        self.search_btn = QPushButton(" Search")
        self.search_btn.setIcon(self._get_icon(ICON_SEARCH))
        self.search_btn.clicked.connect(self.start_search)
        self.stop_btn = QPushButton(" Stop")
        self.stop_btn.setIcon(self._get_icon(ICON_STOP))
        self.stop_btn.clicked.connect(self.stop_search)
        self.stop_btn.setEnabled(False)
        search_control_layout.addWidget(self.search_btn)
        search_control_layout.addWidget(self.stop_btn)
        search_control_layout.addStretch()
        layout.addLayout(search_control_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setProperty('theme-aware', True)  # Mark the progress bar for theme-aware styling
        layout.addWidget(self.progress_bar)

        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Files Found:"))
        self.file_count_label = QLabel("0")
        self.file_count_label.setStyleSheet("font-weight: bold;")
        count_layout.addWidget(self.file_count_label)
        count_layout.addStretch()
        results_layout.addLayout(count_layout)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter Results:"))
        self.results_filter_input = QLineEdit()
        self.results_filter_input.setPlaceholderText("Type to filter visible results...")
        self.results_filter_input.textChanged.connect(self.filter_results_table)
        filter_layout.addWidget(self.results_filter_input)
        self.export_btn = QPushButton(" Export")
        self.export_btn.setIcon(self._get_icon(ICON_EXPORT))
        self.export_btn.clicked.connect(self.show_export_options)
        self.export_btn.setEnabled(False)
        filter_layout.addWidget(self.export_btn)
        results_layout.addLayout(filter_layout)

        # Per-column filters row (built dynamically per mode)
        self.column_filters_widget = QWidget()
        self.column_filters_layout = QHBoxLayout(self.column_filters_widget)
        self.column_filters_layout.setContentsMargins(0, 0, 0, 0)
        self.column_filters_layout.setSpacing(6)
        self.column_filter_inputs = []
        results_layout.addWidget(self.column_filters_widget)

        results_splitter = QSplitter(Qt.Orientation.Vertical)
        self.results_table = QTableWidget()
        self.results_table.setSortingEnabled(True)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.verticalHeader().setVisible(False)
        # Let specific columns stretch (Path), not just the last column
        self.results_table.horizontalHeader().setStretchLastSection(False)
        # Show middle of long paths by eliding in the center
        self.results_table.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self.show_results_context_menu)
        self.results_table.itemSelectionChanged.connect(self.update_selection_and_preview)
        # Track manual resizing of the Path column and respond to table resizes
        self._sizing_in_progress = False
        self.user_resized_path = False
        self.results_table.horizontalHeader().sectionResized.connect(self._on_header_section_resized)
        self.results_table.viewport().installEventFilter(self)
        results_splitter.addWidget(self.results_table)

        self.preview_widget = QWidget()
        preview_layout = QVBoxLayout(self.preview_widget)
        self.preview_tabs = QTabWidget()
        
        # Enhanced preview tabs
        self.image_preview = QLabel("Select a file to preview")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setWordWrap(True)
        
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setFont(QFont("Consolas", 10))
        
        self.html_preview = QTextEdit()
        self.html_preview.setReadOnly(True)
        
        self.properties_preview = QTextEdit()
        self.properties_preview.setReadOnly(True)
        self.properties_preview.setFont(QFont("Consolas", 9))
        
        # Full PDF viewer widget with pan, zoom, navigation, and search
        self.pdf_viewer = PDFViewerWidget()
        
        self.preview_tabs.addTab(self.image_preview, "🖼️ Image")
        self.preview_tabs.addTab(self.text_preview, "📄 Text/Code")
        self.preview_tabs.addTab(self.html_preview, "🎨 Formatted")
        self.preview_tabs.addTab(self.pdf_viewer, "📋 PDF Viewer")
        self.preview_tabs.addTab(self.properties_preview, "ℹ️ Properties")
        
        # Initialize preview manager
        self.preview_manager = PreviewManager()
        
        preview_layout.addWidget(self.preview_tabs)
        results_splitter.addWidget(self.preview_widget)
        results_splitter.setSizes([500, 250])
        
        results_layout.addWidget(results_splitter)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        return panel

    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready.")
        self.selection_label = QLabel("")
        self.status_bar.addWidget(self.status_label, 1)
        # Load More button for large result sets
        self.load_more_btn = QPushButton("📥 Load More")
        self.load_more_btn.setVisible(False)
        self.load_more_btn.setToolTip("Load next 1,000 results")
        self.load_more_btn.clicked.connect(self.load_more_results)
        self.status_bar.addPermanentWidget(self.load_more_btn)
        # Undo button for last recycle-bin delete
        self.undo_btn = QPushButton("Undo Delete")
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self.undo_last_delete)
        self.status_bar.addPermanentWidget(self.undo_btn)
        self.status_bar.addPermanentWidget(self.selection_label)
    
    def _create_system_tray(self):
        """Create system tray icon with context menu."""
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Try to load icon from file, otherwise create a simple one
        icon_path = Path(__file__).resolve().parent.parent / "filescout.png"
        if icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            # Fallback: Create a simple blue square icon
            icon_pixmap = QPixmap(32, 32)
            icon_pixmap.fill(QColor(74, 144, 226))  # Blue color
            icon = QIcon(icon_pixmap)
        
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip(f"{APP_NAME} v{APP_VERSION}")
        
        # Create context menu
        tray_menu = QMenu()
        
        # Quick Search action
        search_action = QAction("🔍 Quick Search...", self)
        search_action.triggered.connect(self.show_and_focus)
        tray_menu.addAction(search_action)
        
        # Find Duplicates action
        duplicates_action = QAction("🔄 Find Duplicates", self)
        duplicates_action.triggered.connect(self.quick_duplicate_scan)
        tray_menu.addAction(duplicates_action)
        
        # Smart Sort action
        smart_sort_action = QAction("🗂️ Smart Sort...", self)
        smart_sort_action.triggered.connect(self.quick_smart_sort)
        tray_menu.addAction(smart_sort_action)
        
        tray_menu.addSeparator()
        
        # Recent Profiles submenu
        self.recent_profiles_menu = tray_menu.addMenu("📋 Recent Profiles")
        self._update_recent_profiles_menu()
        
        tray_menu.addSeparator()
        
        # Show/Hide window
        show_action = QAction("👁️ Show Window", self)
        show_action.triggered.connect(self.show_and_focus)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("⬇️ Hide Window", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("🚪 Exit", self)
        exit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Double-click to show/hide window
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Show the tray icon
        self.tray_icon.show()
    
    def _update_recent_profiles_menu(self):
        """Update the recent profiles submenu in system tray."""
        self.recent_profiles_menu.clear()
        profiles = self.settings.value("profiles", {})
        
        if not profiles:
            no_profiles_action = QAction("(No saved profiles)", self)
            no_profiles_action.setEnabled(False)
            self.recent_profiles_menu.addAction(no_profiles_action)
        else:
            for profile_name in sorted(profiles.keys())[:10]:  # Show max 10 profiles
                action = QAction(profile_name, self)
                action.triggered.connect(lambda checked, name=profile_name: self.load_profile_from_tray(name))
                self.recent_profiles_menu.addAction(action)
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show_and_focus()
    
    def show_and_focus(self):
        """Show window and bring to front."""
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.activateWindow()
        self.raise_()
    
    def quick_duplicate_scan(self):
        """Quick duplicate scan from tray menu."""
        self.show_and_focus()
        self.search_mode_combo.setCurrentIndex(1)  # Set to Find Duplicates
        if self.dir_input.text() and Path(self.dir_input.text()).is_dir():
            self.start_search()
        else:
            self.browse_directory()
    
    def quick_smart_sort(self):
        """Quick smart sort from tray menu."""
        self.show_and_focus()
        if self.matching_files:
            self.open_smart_sort_dialog()
        else:
            self.show_tray_notification("No Results", "Please run a search first before using Smart Sort.", QSystemTrayIcon.MessageIcon.Warning)
    
    def load_profile_from_tray(self, profile_name):
        """Load a profile from the tray menu."""
        profiles = self.settings.value("profiles", {})
        if profile_data := profiles.get(profile_name):
            self.show_and_focus()
            self.apply_search_profile(profile_data)
            self.status_label.setText(f"Loaded profile: {profile_name}")
            self.show_tray_notification("Profile Loaded", f"Loaded search profile: {profile_name}")
    
    def show_tray_notification(self, title, message, icon=QSystemTrayIcon.MessageIcon.Information):
        """Show a system tray notification (toast)."""
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon, 3000)  # 3 seconds
    
    def quit_application(self):
        """Properly quit the application."""
        self.is_closing = True
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()

    def toggle_search_mode_ui(self, index):
        is_file_search = (index == 0)
        self.keywords_group.setEnabled(is_file_search)
        self.use_date_filter.setEnabled(is_file_search)
        self.date_filter_type.setEnabled(is_file_search)
        self.min_date_edit.setEnabled(is_file_search)
        self.max_date_edit.setEnabled(is_file_search)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.dir_input.text())
        if directory: self.dir_input.setText(directory)

    def add_excluded_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Exclude")
        if directory: self.exclude_dirs_list.addItem(QListWidgetItem(Path(directory).as_posix()))

    def remove_excluded_dir(self):
        for item in self.exclude_dirs_list.selectedItems():
            self.exclude_dirs_list.takeItem(self.exclude_dirs_list.row(item))
            
    def start_search(self):
        if self.search_worker and self.search_worker.isRunning(): return
        search_dir = self.dir_input.text()
        if not search_dir or not Path(search_dir).is_dir():
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid search directory.")
            return

        params = self.get_current_search_parameters(for_worker=True)
        if params is None: return
        
        self.search_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.export_btn.setEnabled(False)
        self.results_table.setRowCount(0)
        self.matching_files.clear()
        self.duplicate_group_counter = 0
        # Clear result batching state for new search
        self.result_batch.clear()
        self.hidden_results.clear()
        self.display_limit = 5000
        self.preview_tabs.setTabVisible(0, False)
        self.preview_tabs.setTabVisible(1, False)

        self.search_worker = FileSearchWorker(params)
        self.search_worker.progress_update.connect(self.update_progress)
        self.search_worker.search_complete.connect(self.search_finished)
        
        if params['search_mode'] == 'duplicates':
            self.results_table.setColumnCount(4)
            self.results_table.setHorizontalHeaderLabels(["Group", "File", "Path", "Size (KB)"])
            self.results_table.setSortingEnabled(False)  # Disable during population
            self.search_worker.duplicate_group_found.connect(self.add_duplicate_group_to_table)
        else:
            self.results_table.setColumnCount(6)
            self.results_table.setHorizontalHeaderLabels(["File", "Path", "Ext", "Size (KB)", "Modified", "Created"])
            self.results_table.setSortingEnabled(False)  # Disable during population
            self.search_worker.live_result.connect(self.add_result_to_table)
        # Rebuild per-column filter inputs for current columns
        self._rebuild_column_filters()
        # Reset auto-sizing flag for a fresh layout per search
        self.user_resized_path = False
        # Apply column sizing so Path gets a sensible default width
        self._apply_results_column_sizes()
        
        self.search_worker.start()

    def stop_search(self):
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop()

    def update_progress_bar_style(self):
        # Get primary color from current theme for the progress bar
        if hasattr(self, 'current_theme') and hasattr(self, 'progress_bar'):
            colors = THEME_COLORS.get(self.current_theme, THEME_COLORS['light'])
            primary_color = colors.get('primary', '#3498db')  # Default to blue if primary not found
            self.progress_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {primary_color}; }}")
    
    def update_progress(self, value, message):
        self.status_label.setText(message)
        if value >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(value)
        else:
            self.progress_bar.setRange(0, 0)

    def add_result_to_table(self, file_info):
        """Add result with batching for better performance"""
        self.matching_files.append(file_info)
        self.result_batch.append(file_info)
        
        # Update count immediately
        total_count = len(self.matching_files)
        self.file_count_label.setText(str(total_count))
        
        # Batch insert for better performance
        if len(self.result_batch) >= self.batch_size:
            self._flush_result_batch()
    
    def _flush_result_batch(self):
        """Flush the result batch to the table"""
        if not self.result_batch:
            return
        
        # Disable sorting during batch insert for performance
        was_sorting_enabled = self.results_table.isSortingEnabled()
        self.results_table.setSortingEnabled(False)
        
        current_row_count = self.results_table.rowCount()
        
        for file_info in self.result_batch:
            # Check if we've hit the display limit
            if current_row_count >= self.display_limit:
                self.hidden_results.append(file_info)
                continue
            
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            filename_item = QTableWidgetItem(file_info.get('filename', ''))
            filename_item.setData(Qt.ItemDataRole.UserRole, file_info)
            
            size_item = QTableWidgetItem()
            size_item.setData(Qt.ItemDataRole.EditRole, file_info.get('size_kb', 0))
            
            self.results_table.setItem(row, 0, filename_item)
            path = file_info.get('path', '')
            if not path and 'full_path' in file_info:
                path = str(Path(file_info['full_path']).parent)
            self.results_table.setItem(row, 1, QTableWidgetItem(path))
            self.results_table.setItem(row, 2, QTableWidgetItem(file_info.get('extension', '')))
            self.results_table.setItem(row, 3, size_item)
            self.results_table.setItem(row, 4, QTableWidgetItem(file_info['modified_date'].strftime('%Y-%m-%d %H:%M')))
            self.results_table.setItem(row, 5, QTableWidgetItem(file_info['created_date'].strftime('%Y-%m-%d %H:%M')))
            
            if row == 0:
                self.export_btn.setEnabled(True)
            
            current_row_count += 1
        
        # Clear batch
        self.result_batch.clear()
        
        # Restore sorting if it was enabled
        if was_sorting_enabled:
            self.results_table.setSortingEnabled(True)
        
        # Process events to keep UI responsive
        QApplication.processEvents()
    
    def load_more_results(self):
        """Load next batch of hidden results"""
        if not self.hidden_results:
            return
        
        # Load next 1000 results
        batch_to_load = self.hidden_results[:1000]
        self.hidden_results = self.hidden_results[1000:]
        
        # Temporarily increase display limit
        self.display_limit += len(batch_to_load)
        
        # Add batch to result_batch and flush
        self.result_batch.extend(batch_to_load)
        self._flush_result_batch()
        
        # Update status
        if self.hidden_results:
            self.status_label.setText(f"Loaded more results. {len(self.hidden_results)} still hidden. Click 'Load More' to see them.")
        else:
            self.status_label.setText("All results loaded.")

    def add_duplicate_group_to_table(self, file_group):
        if not file_group: return
        self.duplicate_group_counter += 1
        group_color = self.duplicate_group_colors[self.duplicate_group_counter % len(self.duplicate_group_colors)]

        for file_info in file_group:
            self.matching_files.append(file_info)
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)

            group_item = QTableWidgetItem(str(self.duplicate_group_counter))
            filename_item = QTableWidgetItem(file_info.get('filename', ''))
            filename_item.setData(Qt.ItemDataRole.UserRole, file_info)
            path_item = QTableWidgetItem(file_info.get('path', ''))
            size_item = QTableWidgetItem()
            size_item.setData(Qt.ItemDataRole.EditRole, file_info.get('size_kb', 0))
            
            for item in [group_item, filename_item, path_item, size_item]:
                item.setBackground(QBrush(group_color))

            self.results_table.setItem(row, 0, group_item)
            self.results_table.setItem(row, 1, filename_item)
            self.results_table.setItem(row, 2, path_item)
            self.results_table.setItem(row, 3, size_item)

        if not self.export_btn.isEnabled(): self.export_btn.setEnabled(True)
        self.file_count_label.setText(str(len(self.matching_files)))
        QApplication.processEvents()

    def search_finished(self, success, message):
        self.search_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(100 if success else 0)
        
        # Flush any remaining results in batch
        self._flush_result_batch()
        
        # Update status with hidden results info
        if self.hidden_results:
            hidden_count = len(self.hidden_results)
            message += f" | ⚠️ Showing first {self.display_limit:,} results. {hidden_count:,} more hidden (click 'Load More' below)."
            # Show load more button if it exists
            if hasattr(self, 'load_more_btn'):
                self.load_more_btn.setVisible(True)
                self.load_more_btn.setText(f"📥 Load More ({hidden_count:,} hidden)")
        else:
            # Hide load more button
            if hasattr(self, 'load_more_btn'):
                self.load_more_btn.setVisible(False)
        
        self.status_label.setText(message)
        
        # Re-enable sorting after population is complete
        self.results_table.setSortingEnabled(True)
        
        if success:
            self.save_last_search_parameters()
            # Show toast notification for completed search
            if self.matching_files:
                # Resize to contents, then set interactive widths with smart default for Path
                self.results_table.resizeColumnsToContents()
                self._apply_results_column_sizes()
                
                # Show notification if window is hidden
                if not self.isVisible():
                    count = len(self.matching_files)
                    search_type = "duplicate files" if self.search_mode_combo.currentIndex() == 1 else "files"
                    self.show_tray_notification(
                        "Search Complete",
                        f"Found {count:,} {search_type}",
                        QSystemTrayIcon.MessageIcon.Information
                    )

    def _apply_results_column_sizes(self):
        """Default: content-sizing for non-Path columns; Path is interactive and starts wide.

        Keeps Path user-resizable while giving it a sensible default width.
        """
        header = self.results_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(60)

        cols = self.results_table.columnCount()
        # Make all columns user-resizable (Interactive mode)
        for i in range(cols):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        # Determine Path column index per mode
        path_col = 2 if self.search_mode_combo.currentText() == 'Find Duplicates' else 1
        # Provide a good starting width for Path column
        self._set_default_path_width(path_col)

    def _set_default_path_width(self, path_col: int):
        if self.user_resized_path:
            return  # Respect user's manual size
        self._sizing_in_progress = True
        try:
            table = self.results_table
            viewport_width = table.viewport().width()
            cols = table.columnCount()
            # Sum widths of non-path columns (after ResizeToContents)
            others = 0
            for i in range(cols):
                if i == path_col:
                    continue
                others += table.columnWidth(i)
            # Leave some margin for scrollbar and padding
            margin = 24
            target = max(150, viewport_width - others - margin)
            table.setColumnWidth(path_col, target)
        finally:
            # Delay unsetting sizing flag slightly to avoid treating our own set as user action
            self._sizing_in_progress = False

    def _on_header_section_resized(self, logicalIndex: int, oldSize: int, newSize: int):
        # If user drags the Path column, disable auto-sizing until next search
        path_col = 2 if self.search_mode_combo.currentText() == 'Find Duplicates' else 1
        if logicalIndex == path_col:
            if not self._sizing_in_progress:
                self.user_resized_path = True

    def eventFilter(self, obj, event):
        # Recalculate default Path width when the table viewport resizes (e.g., window/splitter changes)
        if obj is self.results_table.viewport() and event.type() == QEvent.Type.Resize:
            path_col = 2 if self.search_mode_combo.currentText() == 'Find Duplicates' else 1
            self._set_default_path_width(path_col)
        return False  # Don't filter the event, let it propagate normally

    def filter_results_table(self, text):
        # Combine global text and per-column filters
        self.apply_combined_filters(global_text=text)

    def _rebuild_column_filters(self):
        """Create one QLineEdit per column for per-column filtering."""
        # Clear previous inputs
        while self.column_filters_layout.count():
            item = self.column_filters_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.column_filter_inputs = []

        headers = [self.results_table.horizontalHeaderItem(i).text() for i in range(self.results_table.columnCount())]
        for idx, header in enumerate(headers):
            le = QLineEdit()
            le.setPlaceholderText(f"Filter {header}…")
            le.setToolTip(f"Filter by {header}")
            le.textChanged.connect(lambda _=None: self.apply_combined_filters())
            self.column_filters_layout.addWidget(le)
            self.column_filter_inputs.append(le)

    def _any_filters_active(self, global_text: str) -> bool:
        if global_text:
            return True
        return any(le.text() for le in self.column_filter_inputs)

    def apply_combined_filters(self, global_text: str | None = None):
        """Apply global and per-column filters together and update counts/visibility."""
        gtext = (global_text or self.results_filter_input.text()).lower().strip()
        col_filters = [le.text().lower().strip() for le in self.column_filter_inputs]

        visible_count = 0
        rows = self.results_table.rowCount()
        cols = self.results_table.columnCount()
        for i in range(rows):
            # Get column texts for this row once
            col_texts = [self.results_table.item(i, j).text().lower() if self.results_table.item(i, j) else "" for j in range(cols)]

            # Global filter: match if any column contains gtext
            global_match = True
            if gtext:
                global_match = any(gtext in t for t in col_texts)

            # Per-column filters: each non-empty filter must match its column
            percol_match = True
            for j, f in enumerate(col_filters):
                if f and f not in col_texts[j]:
                    percol_match = False
                    break

            match = global_match and percol_match
            self.results_table.setRowHidden(i, not match)
            if match:
                visible_count += 1

        # Update counts
        if self._any_filters_active(gtext):
            self.file_count_label.setText(f"{visible_count} / {len(self.matching_files)}")
        else:
            self.file_count_label.setText(str(len(self.matching_files)))

    def show_results_context_menu(self, pos):
        item = self.results_table.itemAt(pos)
        if not item: return

        is_dupe_mode = self.search_mode_combo.currentText() == 'Find Duplicates'
        file_item_col = 1 if is_dupe_mode else 0
        file_info = self.results_table.item(item.row(), file_item_col).data(Qt.ItemDataRole.UserRole)
        full_path = Path(file_info['full_path'])
        
        menu = QMenu()
        menu.addAction("Open File").triggered.connect(lambda: self._open_path(full_path))
        menu.addAction("Open Containing Folder").triggered.connect(lambda: self._open_path(full_path.parent))
        menu.addAction("Copy Full Path").triggered.connect(lambda: QApplication.clipboard().setText(str(full_path)))
        menu.addSeparator()
        # --- MODIFIED: Added "Copy" option ---
        menu.addAction("Copy Selected Files...").triggered.connect(self.copy_selected_files)
        menu.addAction("Move Selected Files...").triggered.connect(self.move_selected_files)
        menu.addAction("Delete Selected Files...").triggered.connect(self.delete_selected_files)
        menu.addSeparator()
        menu.addAction("Smart Sort...").triggered.connect(self.open_smart_sort_dialog)
    
        menu.exec(self.results_table.mapToGlobal(pos))
    
    def _open_path(self, path):
        try:
            if sys.platform == "win32": os.startfile(path)
            elif sys.platform == "darwin": subprocess.run(["open", path], check=True)
            else: subprocess.run(["xdg-open", path], check=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open path: {e}")

    def get_selected_file_paths(self):
        paths = []
        is_dupe_mode = self.search_mode_combo.currentText() == 'Find Duplicates'
        file_item_col = 1 if is_dupe_mode else 0
        for index in self.results_table.selectionModel().selectedRows():
            # Ensure row is not hidden by the filter
            if not self.results_table.isRowHidden(index.row()):
                item = self.results_table.item(index.row(), file_item_col)
                if item and item.data(Qt.ItemDataRole.UserRole):
                    paths.append(Path(item.data(Qt.ItemDataRole.UserRole)['full_path']))
        return paths

    def delete_selected_files(self):
        paths_to_delete = self.get_selected_file_paths()
        if not paths_to_delete: return
        # Require send2trash to ensure Recycle Bin behavior
        if send2trash is None:
            QMessageBox.critical(self, "Missing Dependency", "The 'send2trash' package is required to send files to the Recycle Bin.\nInstall with: pip install send2trash")
            return
        reply = QMessageBox.question(self, "Send to Recycle Bin", f"Send {len(paths_to_delete)} file(s) to the Recycle Bin?\nYou can Undo this action from the status bar.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return

        rows_to_delete = sorted([index.row() for index in self.results_table.selectionModel().selectedRows() if not self.results_table.isRowHidden(index.row())], reverse=True)
        
        # We need to map visible rows to file infos correctly
        all_file_infos = [self.results_table.item(row, 1 if self.search_mode_combo.currentText() == 'Find Duplicates' else 0).data(Qt.ItemDataRole.UserRole) for row in rows_to_delete]
        
        batch = []
        errors = []
        for row, file_info in zip(rows_to_delete, all_file_infos):
            try:
                fp = str(Path(file_info['full_path']))
                send2trash(fp)
                batch.append(fp)
                self.results_table.removeRow(row)
                if file_info in self.matching_files:
                    self.matching_files.remove(file_info)
            except Exception as e:
                errors.append((file_info.get('filename', fp), str(e)))
                continue
        if batch:
            self._last_delete_batch = batch
            self._undo_stack.append(batch)
            self._update_undo_button()
            self.status_label.setText(f"Sent {len(batch)} item(s) to Recycle Bin. Click 'Undo Delete' to restore.")
        
        if errors:
            QMessageBox.warning(self, "Some Items Not Deleted", "One or more files could not be sent to the Recycle Bin.\n" + "\n".join(f"- {name}: {err}" for name, err in errors))
        
        self.file_count_label.setText(str(len(self.matching_files)))
        self.update_selection_and_preview()

    def _update_undo_button(self):
        if hasattr(self, 'undo_btn'):
            self.undo_btn.setEnabled(bool(self._undo_stack))

    def undo_last_delete(self):
        """Attempt to restore the last batch of files from the Recycle Bin.
        
        Uses PowerShell's Restore-RecycleBin if available. Provides clear feedback
        and opens Recycle Bin if automatic restore fails.
        """
        if not self._undo_stack:
            return
        batch = self._undo_stack.pop()
        restored, failed = self._restore_from_recycle_bin_powershell(batch)
        
        if restored:
            QMessageBox.information(self, "Undo Complete", f"Restored {restored} item(s) from the Recycle Bin.")
            self.status_label.setText(f"Undo restored {restored} item(s).")
        if failed:
            msg = "\n".join(f"- {p}: {err}" for p, err in failed)
            QMessageBox.warning(self, "Undo Partial", f"Some items could not be restored automatically:\n{msg}\n\nOpening Recycle Bin for manual review.")
            self.status_label.setText("Some items could not be restored. See dialog for details.")
            # Open Recycle Bin folder for manual restore
            try:
                if sys.platform == "win32":
                    os.startfile("shell:RecycleBinFolder")
            except Exception:
                pass
        # Update button state after operation
        self._update_undo_button()

    def _restore_from_recycle_bin_powershell(self, paths):
        """Restore given original paths from Recycle Bin using PowerShell.
        
        Returns (restored_count, failed_list[(path, error)])
        """
        restored = 0
        failed = []
        for p in paths:
            try:
                if sys.platform != "win32":
                    failed.append((p, 'Restore supported only on Windows'))
                    continue
                # Escape single quotes for PowerShell and normalize backslashes
                ps_path = str(Path(p)).replace("'", "''")
                ps_script = (
                    "$shell = New-Object -ComObject Shell.Application; "
                    "$rb = $shell.NameSpace(0xA); "
                    "$origIdx = -1; "
                    "for($i=0; $i -lt 256; $i++){ if($rb.GetDetailsOf($null, $i) -eq 'Original Location'){ $origIdx = $i; break } } "
                    "; if($origIdx -eq -1){ Write-Output 'ERR:Original Location column not found'; exit 1 } "
                    f"$target = '{ps_path}'; "
                    "$match = $null; foreach($it in $rb.Items()){ $orig = $rb.GetDetailsOf($it, $origIdx); $full = [System.IO.Path]::Combine($orig, $it.Name); if($full -ieq $target){ $match = $it; break } } "
                    "; if($match){ try{ $match.InvokeVerb('RESTORE') | Out-Null; Write-Output 'OK' } catch { Write-Output ('ERR:' + $_.Exception.Message) } } else { Write-Output 'MISS' }"
                )
                cmd = ["powershell", "-NoProfile", "-Command", ps_script]
                proc = subprocess.run(cmd, capture_output=True, text=True)
                out = (proc.stdout or '').strip()
                err = (proc.stderr or '').strip()
                if 'OK' in out and proc.returncode == 0:
                    restored += 1
                elif 'MISS' in out and proc.returncode == 0:
                    failed.append((p, 'Not found in Recycle Bin'))
                else:
                    failed.append((p, err or out or f'Exit code {proc.returncode}'))
            except Exception as ex:
                failed.append((p, str(ex)))
        return restored, failed

    def move_selected_files(self):
        paths_to_move = self.get_selected_file_paths()
        if not paths_to_move: return
        target_dir = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if not target_dir: return
        
        target_path = Path(target_dir)
        rows_to_delete = sorted([index.row() for index in self.results_table.selectionModel().selectedRows() if not self.results_table.isRowHidden(index.row())], reverse=True)
        all_file_infos = [self.results_table.item(row, 1 if self.search_mode_combo.currentText() == 'Find Duplicates' else 0).data(Qt.ItemDataRole.UserRole) for row in rows_to_delete]

        for row, file_info in zip(rows_to_delete, all_file_infos):
            source_path = Path(file_info['full_path'])
            destination = target_path / source_path.name
            try:
                destination.parent.mkdir(parents=True, exist_ok=True)
                final_dest = self._generate_unique_dest_path(destination)
                source_path.rename(final_dest)
                self.results_table.removeRow(row)
                if file_info in self.matching_files:
                    self.matching_files.remove(file_info)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not move file '{file_info['filename']}':\n{e}")
                break
        self.file_count_label.setText(str(len(self.matching_files)))
        self.update_selection_and_preview()

    # --- NEW METHOD: Adapted from the second script's logic ---
    def _generate_unique_dest_path(self, original_dest_path: Path) -> Path:
        """Generates a unique path if original_dest_path exists by appending (1), (2), etc."""
        if not original_dest_path.exists():
            return original_dest_path

        p = original_dest_path
        base_name = p.stem
        ext = p.suffix
        parent_dir = p.parent
        counter = 1
        
        while True:
            new_name = f"{base_name} ({counter}){ext}"
            new_path = parent_dir / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    # --- NEW METHOD: For handling the copy action ---
    def copy_selected_files(self):
        """Copies selected files to a destination, renaming conflicts."""
        paths_to_copy = self.get_selected_file_paths()
        if not paths_to_copy:
            return

        target_dir = QFileDialog.getExistingDirectory(self, "Select Destination Folder for Copy")
        if not target_dir:
            return

        target_path = Path(target_dir)
        success_count = 0
        error_count = 0
        
        self.status_label.setText(f"Copying {len(paths_to_copy)} files...")
        QApplication.processEvents()

        for source_path in paths_to_copy:
            try:
                original_destination = target_path / source_path.name
                final_destination = self._generate_unique_dest_path(original_destination)
                
                shutil.copy2(source_path, final_destination)
                success_count += 1
            except Exception as e:
                error_count += 1
                reply = QMessageBox.critical(self, "Copy Error", 
                                             f"Could not copy file '{source_path.name}':\n{e}\n\nContinue with other files?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.Yes)
                if reply == QMessageBox.StandardButton.No:
                    break
        
        summary_message = f"Copied {success_count} file(s)."
        if error_count > 0:
            summary_message += f" Failed to copy {error_count} file(s)."

        QMessageBox.information(self, "Copy Complete", summary_message)
        self.status_label.setText(summary_message)

    def open_smart_sort_dialog(self):
        """Open the Smart Sort dialog populated with the current visible results."""
        # Collect file_info dicts from visible rows in the results table
        files = []
        is_dupe_mode = self.search_mode_combo.currentText() == 'Find Duplicates'
        file_item_col = 1 if is_dupe_mode else 0
        for row in range(self.results_table.rowCount()):
            if self.results_table.isRowHidden(row):
                continue
            item = self.results_table.item(row, file_item_col)
            if not item:
                continue
            fi = item.data(Qt.ItemDataRole.UserRole)
            if fi:
                files.append(fi)

        if not files:
            QMessageBox.information(self, "Smart Sort", "No files available to sort. Run a search or clear filters and try again.")
            return

        default_root = self.dir_input.text() or str(Path.home())
        dlg = SmartSortDialog(self, files, default_root, zoom_level=self.zoom_level)
        dlg.exec()

    def open_file_audit(self):
        """Open the File Audit dialog for Google Drive inspection."""
        if not FILE_AUDIT_AVAILABLE:
            QMessageBox.warning(
                self,
                "Feature Unavailable",
                "File Audit feature is not available.\n\n"
                "The file_audit_dialog module could not be loaded."
            )
            return
        
        # Create dialog only once - results persist between opens
        if self.file_audit_dialog is None:
            self.file_audit_dialog = FileAuditDialog(self, theme=self.current_theme, zoom_level=self.zoom_level)
        else:
            # Update theme/zoom if changed since last open
            self.file_audit_dialog.theme = self.current_theme
            self.file_audit_dialog.zoom_level = self.zoom_level
            self.file_audit_dialog._apply_theme()
            if self.zoom_level != 100:
                self.file_audit_dialog._apply_zoom()
        
        self.file_audit_dialog.exec()

    def remove_files_from_results(self, removed_paths):
        """Remove rows and internal entries for the given moved/copied file paths.

        removed_paths: iterable of pathlib.Path or str
        """
        if not removed_paths:
            return

        # Normalize to lowercased absolute strings for robust matching
        norm_set = set()
        for p in removed_paths:
            try:
                s = str(Path(p).resolve())
            except Exception:
                s = str(p)
            norm_set.add(s.lower())

        is_dupe_mode = self.search_mode_combo.currentText() == 'Find Duplicates'
        file_item_col = 1 if is_dupe_mode else 0

        # Remove matching rows from the table, bottom-up to keep indices valid
        rows_removed = 0
        for row in range(self.results_table.rowCount() - 1, -1, -1):
            item = self.results_table.item(row, file_item_col)
            if not item:
                continue
            fi = item.data(Qt.ItemDataRole.UserRole)
            if not fi:
                continue
            try:
                fp = str(Path(fi['full_path']).resolve()).lower()
            except Exception:
                fp = str(fi.get('full_path', '')).lower()
            if fp in norm_set:
                self.results_table.removeRow(row)
                rows_removed += 1

        # Rebuild matching_files excluding removed ones for safety (sorting/filtering may de-sync indices)
        new_list = []
        for fi in getattr(self, 'matching_files', []):
            try:
                fp = str(Path(fi['full_path']).resolve()).lower()
            except Exception:
                fp = str(fi.get('full_path', '')).lower()
            if fp not in norm_set:
                new_list.append(fi)
        self.matching_files = new_list

        # Update UI
        self.file_count_label.setText(str(len(self.matching_files)))
        if self.results_table.rowCount() == 0:
            self.export_btn.setEnabled(False)
        self.update_selection_and_preview()

    def update_selection_and_preview(self):
        self.update_selection_status()
        self.update_preview()

    def update_selection_status(self):
        selected_rows = self.results_table.selectionModel().selectedRows()
        if not selected_rows:
            self.selection_label.setText("")
            return

        total_size_bytes = 0
        is_dupe_mode = self.search_mode_combo.currentText() == 'Find Duplicates'
        file_item_col = 1 if is_dupe_mode else 0
        
        visible_selected_count = 0
        for index in selected_rows:
            if not self.results_table.isRowHidden(index.row()):
                visible_selected_count += 1
                item = self.results_table.item(index.row(), file_item_col)
                if item and item.data(Qt.ItemDataRole.UserRole):
                    total_size_bytes += item.data(Qt.ItemDataRole.UserRole)['size_bytes']

        if visible_selected_count == 0:
            self.selection_label.setText("")
            return

        size_str = f"{total_size_bytes / 1024:.2f} KB"
        if total_size_bytes > 1024*1024: size_str = f"{total_size_bytes / (1024*1024):.2f} MB"
        if total_size_bytes > 1024*1024*1024: size_str = f"{total_size_bytes / (1024*1024*1024):.2f} GB"
        self.selection_label.setText(f"{visible_selected_count} items selected ({size_str})")

    def update_preview(self):
        selected_items = self.results_table.selectedItems()
        if not selected_items:
            # Hide all tabs when no selection
            for i in range(self.preview_tabs.count()):
                self.preview_tabs.setTabVisible(i, False)
            return
            
        row = selected_items[0].row()
        is_dupe_mode = self.search_mode_combo.currentText() == 'Find Duplicates'
        file_item_col = 1 if is_dupe_mode else 0
        file_info = self.results_table.item(row, file_item_col).data(Qt.ItemDataRole.UserRole)
        file_path = Path(file_info['full_path'])
        
        # Hide all tabs initially
        for i in range(self.preview_tabs.count()):
            self.preview_tabs.setTabVisible(i, False)
        
        # Show file properties in all cases
        self._show_file_properties(file_path)
        self.preview_tabs.setTabVisible(4, True)  # Properties tab
        
        # Check if it's an image first
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type.startswith('image/'):
            self._show_image_preview(file_path)
            self.preview_tabs.setCurrentIndex(0)  # Image tab
            return
            
        # Use enhanced preview system
        content_type, content, metadata = self.preview_manager.generate_preview(str(file_path))
        
        if content_type == "error":
            self.text_preview.setPlainText(f"Preview Error: {content}")
            self.preview_tabs.setTabVisible(1, True)  # Text tab
            self.preview_tabs.setCurrentIndex(1)
        elif content_type == "text":
            self.text_preview.setPlainText(content)
            self.preview_tabs.setTabVisible(1, True)  # Text tab
            if metadata.get("syntax_highlighted"):
                self.preview_tabs.setCurrentIndex(2)  # Formatted tab if syntax highlighted
            else:
                self.preview_tabs.setCurrentIndex(1)  # Text tab
        elif content_type == "pdf_dual":
            # Handle PDF with both text extraction and full PDF viewer
            self.text_preview.setPlainText(content)
            
            # Load PDF into the full viewer widget using the actual file path
            self.pdf_viewer.load_pdf(file_path)
            
            # Show tabs: Text, PDF Viewer, Properties
            self.preview_tabs.setTabVisible(1, True)  # Text tab
            self.preview_tabs.setTabVisible(3, True)  # PDF Viewer tab
            self.preview_tabs.setCurrentIndex(3)  # Start with PDF Viewer tab
            
        elif content_type == "html":
            self.html_preview.setHtml(content)
            self.preview_tabs.setTabVisible(1, True)  # Text tab
            self.preview_tabs.setTabVisible(2, True)  # Formatted tab
            self.preview_tabs.setCurrentIndex(2)  # Formatted tab

    def _show_image_preview(self, file_path):
        """Display image preview with metadata."""
        try:
            pixmap = QPixmap(str(file_path))
            if not pixmap.isNull():
                # Scale image to fit preview area
                scaled_pixmap = pixmap.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio)
                self.image_preview.setPixmap(scaled_pixmap)
                
                # Add image info to the label
                img_size = pixmap.size()
                file_size = file_path.stat().st_size
                size_mb = file_size / (1024 * 1024)
                
                info_text = f"📐 {img_size.width()}×{img_size.height()} pixels\n"
                info_text += f"📦 {size_mb:.2f} MB\n"
                info_text += f"📁 {file_path.name}"
                
                self.image_preview.setToolTip(info_text)
                self.preview_tabs.setTabVisible(0, True)  # Image tab
            else:
                self.text_preview.setPlainText("Cannot load image file.")
                self.preview_tabs.setTabVisible(1, True)  # Text tab
                self.preview_tabs.setCurrentIndex(1)
        except Exception as e:
            self.text_preview.setPlainText(f"Error loading image: {e}")
            self.preview_tabs.setTabVisible(1, True)  # Text tab
            self.preview_tabs.setCurrentIndex(1)
    
    def _show_file_properties(self, file_path):
        """Display detailed file properties."""
        try:
            stat = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            # File size in different units
            size_bytes = stat.st_size
            if size_bytes < 1024:
                size_str = f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.2f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
            else:
                size_str = f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
            
            properties = [
                "📁 File Properties",
                "=" * 40,
                f"Name: {file_path.name}",
                f"Path: {file_path.parent}",
                f"Extension: {file_path.suffix or 'None'}",
                f"Size: {size_str}",
                f"MIME Type: {mime_type or 'Unknown'}",
                "",
                "📅 Timestamps",
                "=" * 40,
                f"Created: {datetime.datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}",
                f"Modified: {datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
                f"Accessed: {datetime.datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "🔐 Attributes",
                "=" * 40,
                f"Read-only: {'Yes' if not os.access(file_path, os.W_OK) else 'No'}",
                f"Hidden: {'Yes' if file_path.name.startswith('.') else 'No'}",
                f"Executable: {'Yes' if os.access(file_path, os.X_OK) else 'No'}",
            ]
            
            # Add file type specific info
            handler = self.preview_manager.get_handler(file_path)
            if handler:
                properties.extend([
                    "",
                    "🔍 Preview Handler",
                    "=" * 40,
                    f"Handler: {handler.name}",
                    f"Supported extensions: {', '.join(handler.extensions)}"
                ])
            
            # Add hash information for small files
            if size_bytes < 50 * 1024 * 1024:  # Files smaller than 50MB
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read(8192)).hexdigest()  # Hash first 8KB
                    properties.extend([
                        "",
                        "🔐 Hash (first 8KB)",
                        "=" * 40,
                        f"MD5: {file_hash}"
                    ])
                except:
                    pass
            
            self.properties_preview.setPlainText('\n'.join(properties))
            
        except Exception as e:
            self.properties_preview.setPlainText(f"Error reading file properties: {e}")

    def get_current_search_parameters(self, for_worker=False):
        params = {}
        params['search_mode'] = 'duplicates' if self.search_mode_combo.currentIndex() == 1 else 'files'
        params['search_dir'] = self.dir_input.text()
        params['keywords'] = self.keywords_input.text()
        params['exclusion_keywords'] = self.exclusion_keywords_input.text()
        params['use_regex'] = self.regex_checkbox.isChecked()
        params['whole_words'] = self.whole_words_checkbox.isChecked() and not params['use_regex']
        params['content_search'] = self.content_search_input.text() if self.content_search_checkbox.isChecked() else ""
        
        # --- MODIFIED: Custom extensions take priority over preset ---
        custom_exts_str = self.custom_exts_input.text().replace(' ', '').replace('.', '')
        if custom_exts_str:
            # If custom extensions are provided, use ONLY those (ignore preset)
            allowed_exts = set(ext.strip() for ext in custom_exts_str.split(',') if ext.strip())
        else:
            # Otherwise, use the preset
            allowed_exts = set(FILE_TYPE_MAPPINGS.get(self.file_types_combo.currentText(), []))
        params['allowed_extensions'] = list(allowed_exts)
        params['ui_file_type_preset'] = self.file_types_combo.currentText()
        params['ui_custom_exts'] = self.custom_exts_input.text()
        # --- END MODIFICATION ---

        try:
            params['min_size_kb'] = float(self.min_size_input.text()) if self.min_size_input.text() else None
            params['max_size_kb'] = float(self.max_size_input.text()) if self.max_size_input.text() else None
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "File size must be a valid number.")
            return None
        
        params['date_filter'] = self.use_date_filter.isChecked()
        if params['date_filter']:
            params['date_filter_type'] = 'modified' if self.date_filter_type.currentIndex() == 0 else 'created'
            min_qdate, max_qdate = self.min_date_edit.date(), self.max_date_edit.date()
            if for_worker:
                params['min_date'] = datetime.datetime(min_qdate.year(), min_qdate.month(), min_qdate.day(), 0, 0, 0)
                params['max_date'] = datetime.datetime(max_qdate.year(), max_qdate.month(), max_qdate.day(), 23, 59, 59)
            else:
                params['min_date_str'] = min_qdate.toString(Qt.DateFormat.ISODate)
                params['max_date_str'] = max_qdate.toString(Qt.DateFormat.ISODate)
        
        params['exclude_dirs'] = [self.exclude_dirs_list.item(i).text() for i in range(self.exclude_dirs_list.count())]
        if for_worker: 
            params['count_files'] = self.count_files_checkbox.isChecked()
            if params['search_mode'] == 'duplicates':
                 params['min_size_bytes'] = (params['min_size_kb'] or 0) * 1024
        return params

    def apply_search_profile(self, profile):
        self.search_mode_combo.setCurrentIndex(1 if profile.get('search_mode') == 'duplicates' else 0)
        self.dir_input.setText(profile.get('search_dir', ''))
        self.keywords_input.setText(profile.get('keywords', ''))
        self.exclusion_keywords_input.setText(profile.get('exclusion_keywords', ''))
        self.regex_checkbox.setChecked(profile.get('use_regex', False))
        self.whole_words_checkbox.setChecked(profile.get('whole_words', False))
        self.content_search_checkbox.setChecked(bool(profile.get('content_search', '')))
        self.content_search_input.setText(profile.get('content_search', ''))
        self.file_types_combo.setCurrentText(profile.get('ui_file_type_preset', 'All Files'))
        # --- MODIFIED: Load custom extensions from profile ---
        self.custom_exts_input.setText(profile.get('ui_custom_exts', ''))
        # --- END MODIFICATION ---
        min_size, max_size = profile.get('min_size_kb'), profile.get('max_size_kb')
        self.min_size_input.setText(str(min_size) if min_size is not None else '')
        self.max_size_input.setText(str(max_size) if max_size is not None else '')
        self.use_date_filter.setChecked(profile.get('date_filter', False))
        if profile.get('date_filter'):
            self.date_filter_type.setCurrentIndex(1 if profile.get('date_filter_type') == 'created' else 0)
            self.min_date_edit.setDate(QDate.fromString(profile.get('min_date_str'), Qt.DateFormat.ISODate))
            self.max_date_edit.setDate(QDate.fromString(profile.get('max_date_str'), Qt.DateFormat.ISODate))
        self.exclude_dirs_list.clear()
        self.exclude_dirs_list.addItems(profile.get('exclude_dirs', []))
        if 'theme' in profile:
            self.apply_theme(profile['theme'])
        if 'splitter_sizes' in profile:
            splitters = self.findChildren(QSplitter)
            for i, size in enumerate(profile['splitter_sizes']):
                if i < len(splitters):
                    splitters[i].setSizes([size, splitters[i].sizes()[1]])

    def save_search_profile(self):
        profile_name, ok = QInputDialog.getText(self, "Save Profile", "Enter profile name:")
        if not (ok and profile_name): return
        profiles = self.settings.value("profiles", {})
        if profile_name in profiles and QMessageBox.question(self, "Overwrite Profile", f"Profile '{profile_name}' already exists. Overwrite?") != QMessageBox.StandardButton.Yes:
            return
        profiles[profile_name] = {
            **self.get_current_search_parameters(for_worker=False),
            'theme': self.current_theme,
            'splitter_sizes': [splitter.sizes()[0] for splitter in self.findChildren(QSplitter)]
        }
        self.settings.setValue("profiles", profiles)
        QMessageBox.information(self, "Success", f"Profile '{profile_name}' saved.")
        # Update tray menu with new profile
        self._update_recent_profiles_menu()
        self.show_tray_notification("Profile Saved", f"Search profile '{profile_name}' saved successfully.")

    def manage_profiles(self):
        dialog = ProfileManagerDialog(self, zoom_level=self.zoom_level)
        if dialog.exec():
            profile_name = dialog.get_selected_profile_name()
            if profile_name and (profile_data := self.settings.value("profiles", {}).get(profile_name)):
                self.apply_search_profile(profile_data)
                self.status_label.setText(f"Loaded profile: {profile_name}")
                self.show_tray_notification("Profile Loaded", f"Loaded search profile: {profile_name}")
        # Update tray menu in case profiles were deleted
        self._update_recent_profiles_menu()
    
    def load_settings(self):
        self.restoreGeometry(self.settings.value("geometry", self.saveGeometry()))
        self.restoreState(self.settings.value("windowState", self.saveState()))
        self.count_files_checkbox.setChecked(self.settings.value("perf/count_files", True, type=bool))
        self.zoom_level = self.settings.value("zoom_level", 100, type=int)
        self.apply_zoom()
        self.load_last_search_parameters()

    def save_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("theme", self.current_theme)
        self.settings.setValue("perf/count_files", self.count_files_checkbox.isChecked())
        self.settings.setValue("zoom_level", self.zoom_level)
        self.save_last_search_parameters()
    
    def save_last_search_parameters(self):
        if params := self.get_current_search_parameters(for_worker=False):
            self.settings.setValue("last_search_params", json.dumps(params))
            
    def load_last_search_parameters(self):
        if params_json := self.settings.value("last_search_params"):
            try:
                self.apply_search_profile(json.loads(params_json))
            except json.JSONDecodeError:
                pass
    
    def closeEvent(self, event):
        """Handle window close event - minimize to tray instead of closing."""
        if not self.is_closing:
            # Minimize to tray instead of closing
            event.ignore()
            self.hide()
            if self.tray_icon:
                self.show_tray_notification(
                    f"{APP_NAME} Minimized",
                    "File Scout is still running in the system tray. Double-click the tray icon to restore.",
                    QSystemTrayIcon.MessageIcon.Information
                )
        else:
            # Actually closing
            self.save_settings()
            if self.search_worker and self.search_worker.isRunning():
                self.search_worker.stop()
                self.search_worker.wait(1000)
            event.accept()
            super().closeEvent(event)
    
    def wheelEvent(self, event):
        """Handle Ctrl+mouse wheel for zooming"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Get the angle delta (positive = zoom in, negative = zoom out)
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
    
    def zoom_in(self):
        """Increase zoom level by 10%"""
        self.set_zoom(min(self.zoom_level + 10, 300))
    
    def zoom_out(self):
        """Decrease zoom level by 10%"""
        self.set_zoom(max(self.zoom_level - 10, 50))
    
    def zoom_reset(self):
        """Reset zoom to 100%"""
        self.set_zoom(100)
    
    def set_zoom(self, zoom_percent):
        """Set zoom to specific percentage"""
        self.zoom_level = zoom_percent
        self.apply_zoom()
        self.status_label.setText(f"Zoom: {self.zoom_level}%")
    
    def apply_zoom(self):
        """Apply current zoom level to all UI elements"""
        zoom_factor = self.zoom_level / 100

        # Calculate new font size based on zoom
        new_font_size = max(7, int(self.base_font_size * zoom_factor))
        
        # Create font for the application
        app_font = self.font()
        app_font.setPointSize(new_font_size)
        
        # Apply to main window and all widgets
        self.setFont(app_font)
        
        # Update all child widgets
        for widget in self.findChildren(QWidget):
            widget.setFont(app_font)
        
        # Special handling for tables to adjust row heights
        for table in self.findChildren(QTableWidget):
            table.verticalHeader().setDefaultSectionSize(int(25 * zoom_factor))
        
        # Scale layout spacing
        scaled_spacing = int(self.base_spacing * zoom_factor)
        scaled_side = int(5 * zoom_factor)
        scaled_top_margin = int(self.base_groupbox_top_margin * zoom_factor) + new_font_size
        scaled_bottom = int(5 * zoom_factor)
        
        # Scale minimum heights for input widgets so they don't get squished
        input_min_h = int(28 * zoom_factor)
        for w in self.findChildren((QLineEdit, QComboBox, QDateEdit)):
            w.setMinimumHeight(input_min_h)
        
        # Update search panel spacing
        if hasattr(self, 'search_panel_layout'):
            self.search_panel_layout.setSpacing(scaled_spacing)
        
        # Update all QGroupBox content margins
        for groupbox in self.findChildren(QGroupBox):
            gb_layout = groupbox.layout()
            if gb_layout:
                gb_layout.setContentsMargins(
                    scaled_side,
                    scaled_top_margin,
                    scaled_side,
                    scaled_bottom
                )
        
        # Reapply theme to update QGroupBox margins in stylesheet
        self.apply_theme(self.current_theme)
        
        # Force update
        self.update()
    
    def _create_message_box(self, icon, title, text, buttons=QMessageBox.StandardButton.Ok):
        """Create a QMessageBox with proper zoom-scaled font"""
        msg_box = QMessageBox(icon, title, text, buttons, self)
        
        # Apply zoom to message box
        if self.zoom_level != 100:
            zoom_factor = self.zoom_level / 100
            font = msg_box.font()
            font.setPointSize(int(9 * zoom_factor))
            msg_box.setFont(font)
            
            # Also apply to all buttons
            for button in msg_box.findChildren(QPushButton):
                button.setFont(font)
        
        return msg_box
    
    def show_information(self, title, text):
        """Show information dialog with zoom-scaled font"""
        msg_box = self._create_message_box(QMessageBox.Icon.Information, title, text)
        return msg_box.exec()
    
    def show_warning(self, title, text):
        """Show warning dialog with zoom-scaled font"""
        msg_box = self._create_message_box(QMessageBox.Icon.Warning, title, text)
        return msg_box.exec()
    
    def show_question(self, title, text, buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):
        """Show question dialog with zoom-scaled font"""
        msg_box = self._create_message_box(QMessageBox.Icon.Question, title, text, buttons)
        return msg_box.exec()
    
    def show_critical(self, title, text):
        """Show critical error dialog with zoom-scaled font"""
        msg_box = self._create_message_box(QMessageBox.Icon.Critical, title, text)
        return msg_box.exec()

    def _get_icon(self, icon_data):
        from PyQt6.QtCore import QByteArray
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray.fromBase64(icon_data.encode()))
        return QIcon(pixmap)

    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        colors = THEME_COLORS.get(theme_name, THEME_COLORS['light'])
        for action in self.theme_action_group.actions():
            action.setChecked(action.text().lower().replace(' ', '_') == theme_name)
        
        # Calculate scaled values based on zoom
        zoom_factor = self.zoom_level / 100
        groupbox_margin_top = int(self.base_groupbox_margin_top * zoom_factor) + int(self.base_font_size * zoom_factor)
        groupbox_title_padding = int(self.base_groupbox_title_padding * zoom_factor)
        groupbox_padding_top = int(15 * zoom_factor)  # fully scaled (was title_padding + fixed 10)
        input_padding = int(5 * zoom_factor)
        btn_pad_v = int(6 * zoom_factor)
        btn_pad_h = int(12 * zoom_factor)
        cb_indicator = int(16 * zoom_factor)
        cb_spacing = int(5 * zoom_factor)
        
        style_sheet = f"""
        QWidget {{ background-color: {colors['background']}; color: {colors['text']}; }}
        QMainWindow, QDialog {{ background-color: {colors['background']}; }}
        QGroupBox {{ border: 1px solid {colors['border']}; border-radius: 6px; margin-top: {groupbox_margin_top}px; font-weight: bold; color: {colors['primary']}; padding-top: {groupbox_padding_top}px; }}
        QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top center; padding: {groupbox_title_padding}px {groupbox_title_padding}px; background-color: {colors['background']}; }}
        QTableWidget {{ border: 1px solid {colors['border']}; background-color: {colors['surface']}; gridline-color: {colors['grid']}; }}
        QTableWidget::item {{ border-bottom: 1px solid {colors['grid']}; padding: {input_padding}px; color: {colors['text']}; }}
        QTableWidget::item:selected {{ background-color: {colors['primary']}; color: {colors['surface']}; }}
        QHeaderView::section {{ background-color: {colors['header']}; color: {colors['text']}; padding: {btn_pad_v}px; border: 1px solid {colors['grid']}; font-weight: bold; }}
        QLineEdit, QDateEdit, QComboBox {{ background-color: {colors['surface']}; color: {colors['text']}; border: 1px solid {colors['border']}; border-radius: 4px; padding: {input_padding}px; }}
        QLineEdit:focus, QDateEdit:focus, QComboBox:focus {{ border-color: {colors['primary']}; }}
        QListWidget {{ background-color: {colors['surface']}; color: {colors['text']}; border: 1px solid {colors['border']}; border-radius: 4px; }}
        QListWidget::item:selected {{ background-color: {colors['primary']}; color: {colors['surface']}; }}
        QPushButton {{ background-color: {colors['primary']}; color: {colors['surface']}; border: none; border-radius: 4px; padding: {btn_pad_v}px {btn_pad_h}px; font-weight: bold; }}
        QPushButton:hover {{ background-color: {colors['secondary']}; }}
        QPushButton:disabled {{ background-color: {colors['border']}; color: {colors['text_secondary']}; }}
        QStatusBar {{ color: {colors['text_secondary']}; }}
        QTabWidget::pane {{ border: 1px solid {colors['border']}; background-color: {colors['surface']}; }}
        QTabBar::tab {{ background: {colors['header']}; color: {colors['text']}; padding: {input_padding}px; }}
        QTabBar::tab:selected {{ background: {colors['primary']}; color: {colors['surface']}; }}
        QProgressBar {{ border: 1px solid {colors['border']}; border-radius: 4px; background-color: {colors['surface']}; text-align: center; color: {colors['text']}; }}
        QProgressBar::chunk {{ background-color: {colors['primary']}; border-radius: 3px; }}
        QCheckBox {{ color: {colors['text']}; spacing: {cb_spacing}px; }}
        QCheckBox::indicator {{ width: {cb_indicator}px; height: {cb_indicator}px; border: 1px solid {colors['text']}; border-radius: 3px; background-color: {colors['surface']}; }}
        QCheckBox::indicator:hover {{ border-color: {colors['primary']}; }}
        QCheckBox::indicator:checked {{ background-color: {colors['primary']}; border-color: {colors['primary']}; }}
        QCheckBox::indicator:checked:hover {{ background-color: {colors['secondary']}; border-color: {colors['secondary']}; }}
        """
        self.setStyleSheet(style_sheet)
    
    def show_export_options(self):
        menu = QMenu(self)
        menu.addAction("Export Visible to Excel...").triggered.connect(lambda: self.export_to_excel(visible_only=True))
        menu.addAction("Export All to Excel...").triggered.connect(lambda: self.export_to_excel(visible_only=False))
        menu.addSeparator()
        menu.addAction("Export Visible to CSV...").triggered.connect(lambda: self.export_to_csv(visible_only=True))
        menu.addAction("Export All to CSV...").triggered.connect(lambda: self.export_to_csv(visible_only=False))
        menu.addSeparator()
        menu.addAction("Clear Results").triggered.connect(self.clear_results)
        menu.exec(self.export_btn.mapToGlobal(self.export_btn.rect().bottomLeft()))

    def clear_results(self):
        """Clear all search results from the table."""
        if self.results_table.rowCount() == 0:
            return
        reply = QMessageBox.question(self, "Clear Results", "Clear all search results?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.results_table.setRowCount(0)
            self.matching_files.clear()
            self.file_count_label.setText("0")
            self.export_btn.setEnabled(False)
            self.status_label.setText("Results cleared.")
            self.preview_tabs.setTabVisible(0, False)
            self.preview_tabs.setTabVisible(1, False)

    def _get_export_data(self, visible_only=True):
        headers = [self.results_table.horizontalHeaderItem(i).text() for i in range(self.results_table.columnCount())]
        data = []
        rows_to_process = range(self.results_table.rowCount())
        if visible_only:
            rows_to_process = [r for r in rows_to_process if not self.results_table.isRowHidden(r)]
        
        for row in rows_to_process:
            row_data = {}
            for col in range(len(headers)):
                item = self.results_table.item(row, col)
                row_data[headers[col]] = item.text() if item else ""
            data.append(row_data)
        return headers, data

    def export_to_excel(self, visible_only=True):
        headers, data = self._get_export_data(visible_only)
        if not data: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel File", f"file_scout_{datetime.datetime.now():%Y%m%d}.xlsx", "Excel Files (*.xlsx)")
        if not file_path: return
        try:
            ExcelExporter(theme=self.current_theme).export_data(file_path, headers, data)
            self._ask_to_open(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def export_to_csv(self, visible_only=True):
        headers, data = self._get_export_data(visible_only)
        if not data: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV File", f"file_scout_{datetime.datetime.now():%Y%m%d}.csv", "CSV Files (*.csv)")
        if not file_path: return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
            self._ask_to_open(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export to CSV: {e}")
            
    def _ask_to_open(self, file_path):
        self.status_label.setText(f"Exported successfully to {Path(file_path).name}")
        if QMessageBox.question(self, 'Export Complete', 'Do you want to open the exported file?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self._open_path(file_path)
    
    def setup_from_cli(self, args):
        """Configure the GUI from command-line arguments (for shortcuts and context menu)."""
        # Set directory if provided
        if args.dir and os.path.isdir(args.dir):
            self.dir_input.setText(args.dir)
        
        # Set search mode
        if hasattr(args, 'duplicates') and args.duplicates:
            self.search_mode_combo.setCurrentIndex(1)  # Find Duplicates mode
        
        # Set file extensions if provided
        if args.exts:
            self.custom_exts_input.setText(args.exts)
        
        # Set size filters if provided
        if args.min_size is not None:
            self.min_size_input.setText(str(args.min_size))
        if args.max_size is not None:
            self.max_size_input.setText(str(args.max_size))
        
        # Set keywords if provided
        if args.keywords:
            self.keywords_input.setText(args.keywords)
        if hasattr(args, 'exclude_keywords') and args.exclude_keywords:
            self.exclusion_keywords_input.setText(args.exclude_keywords)
        
        # Show notification
        self.show_tray_notification(
            "File Scout Ready",
            f"Ready to search: {args.dir if args.dir else 'No directory set'}",
            QSystemTrayIcon.MessageIcon.Information
        )
        
        self.status_label.setText("Ready. Click 'Search' to begin.")

    def run_from_cli(self, args):
        print(f"--- {APP_NAME} v{APP_VERSION} CLI Mode ---")
        if args.profile:
            profiles = self.settings.value("profiles", {})
            if args.profile in profiles:
                params = profiles[args.profile]
                if args.dir: params['search_dir'] = args.dir
                if args.keywords: params['keywords'] = args.keywords
                if args.exclude_keywords: params['exclusion_keywords'] = args.exclude_keywords
                if args.exts: params['allowed_extensions'] = [e.strip().lstrip('.') for e in args.exts.split(',')]
                if args.min_size is not None: params['min_size_kb'] = args.min_size
                if args.max_size is not None: params['max_size_kb'] = args.max_size
                if args.min_date: params['min_date'] = datetime.datetime.strptime(args.min_date, '%Y-%m-%d')
                if args.max_date: params['max_date'] = datetime.datetime.strptime(args.max_date, '%Y-%m-%d')
                if args.date_type: params['date_filter_type'] = args.date_type
                params['date_filter'] = bool(args.min_date or args.max_date)
            else:
                print(f"Profile '{args.profile}' not found.", file=sys.stderr)
                sys.exit(1)
        else:
            params = {
                'search_dir': args.dir, 'keywords': args.keywords or "", 'exclusion_keywords': args.exclude_keywords or "",
                'allowed_extensions': [e.strip().lstrip('.') for e in args.exts.split(',')] if args.exts else [],
                'min_size_kb': args.min_size, 'max_size_kb': args.max_size,
                'use_regex': False, 'whole_words': False, 'date_filter': bool(args.min_date or args.max_date),
                'date_filter_type': args.date_type or 'modified',
                'min_date': datetime.datetime.strptime(args.min_date, '%Y-%m-%d') if args.min_date else None,
                'max_date': datetime.datetime.strptime(args.max_date, '%Y-%m-%d') if args.max_date else None,
                'exclude_dirs': [], 'count_files': True, 'content_search': args.content_search or ""
            }
        engine = SearchEngine()
        engine.progress_update.connect(lambda v, m: print(f"\r> {m.ljust(60)}", end=""))
        results = list(engine.find_files(params))
        print(f"\nSearch complete. Found {len(results)} files.")

        if args.output:
            try:
                with open(args.output, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys() if results else [])
                    writer.writeheader()
                    writer.writerows(results)
                print(f"Results saved to {args.output}")
            except Exception as e:
                print(f"Error saving to output file: {e}", file=sys.stderr)
        else:
            for res in results: print(f"- {res['full_path']}")
        QApplication.quit()

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description=f"{APP_NAME} - File searching utility.", add_help=False)
    parser.add_argument('--dir', type=str, help="Directory to search")
    parser.add_argument('--keywords', type=str, help="Comma-separated keywords to include")
    parser.add_argument('--exclude-keywords', type=str, help="Comma-separated keywords to exclude")
    parser.add_argument('--exts', type=str, help="Comma-separated file extensions")
    parser.add_argument('--min-size', type=float, help="Minimum file size in KB")
    parser.add_argument('--max-size', type=float, help="Maximum file size in KB")
    parser.add_argument('--min-date', type=str, help="Minimum date (YYYY-MM-DD)")
    parser.add_argument('--max-date', type=str, help="Maximum date (YYYY-MM-DD)")
    parser.add_argument('--date-type', type=str, choices=['modified', 'created'], default='modified', help="Date type to filter")
    parser.add_argument('--content-search', type=str, help="Text to search within file contents")
    parser.add_argument('--profile', type=str, help="Load search parameters from a saved profile")
    parser.add_argument('--output', type=str, help="Output file path for results")
    parser.add_argument('--duplicates', action='store_true', help="Start in duplicate finding mode")
    args, _ = parser.parse_known_args()

    # Stabilize HiDPI rounding before creating the QApplication
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.RoundPreferFloor)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = FileScoutApp(cli_args=args)
    if not (args.dir and os.path.isdir(args.dir)):
        window.show()

    sys.exit(app.exec())

