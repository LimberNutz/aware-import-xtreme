# File Scout 2025

A powerful and intuitive file management utility for Windows that helps you find, organize, and audit files across directories with advanced filtering, duplicate detection, and smart organization features.

![File Scout Logo](filescout.png)

## ✨ Key Features

### 🔍 **Advanced File Search**
- **Multi-criteria filtering** by name, size, date, extensions, and keywords
- **Real-time search progress** with live results as files are found
- **Pattern matching** with wildcards and regular expressions
- **Content search** within text files
- **Large file detection** to identify space hogs
- **Recent file discovery** with date range filtering

### 🔄 **Duplicate File Finder**
- **SHA256 hash-based detection** for accurate duplicate identification
- **Grouped duplicate display** showing all identical files
- **Size and date comparison** for quick verification
- **Selective deletion** with recycle bin support
- **Duplicate statistics** and space recovery reports

### 📁 **Smart Sort Organization**
- **Pattern-based folder matching** automatically suggests destinations
- **Fuzzy matching** for unmatched files with intelligent suggestions
- **Preview before execution** shows exactly where files will go
- **Batch operations** for moving or copying multiple files
- **Custom folder patterns** for your specific organization needs

### 📄 **File Preview System**
- **In-app previews** for 50+ file types without opening external programs
- **PDF viewer** with zoom, pan, search, and highlighting
- **Office documents** (Word, Excel, PowerPoint) preview
- **Code files** with syntax highlighting
- **Images, audio, video** metadata display
- **Archive contents** listing (ZIP files)
- **Hex view** for binary files

### 📊 **File Audit with Google Drive Integration**
- **Google Drive folder scanning** for missing inspection files
- **Live Google Sheets integration** for real-time traveler data
- **Excel file support** for offline audits
- **Automated compliance checking** for API-510, API-570, Tank Traveler
- **Export results** to Excel or CSV for reporting

### 🎯 **Productivity Features**
- **Search profiles** save and reuse common search configurations
- **System tray integration** for quick access
- **Windows Explorer context menu** for right-click folder scanning
- **Toast notifications** for search completion
- **Keyboard shortcuts** for power users
- **Excel export** of search results
- **Theme support** with 33 color schemes

## 🚀 Quick Start

### Installation

1. **Download the latest release** or clone the repository
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python "File Scout 3.2.py"
   ```

### First-Time Setup

1. **Launch File Scout** - it will minimize to your system tray
2. **Set up system integration** (optional):
   - Install Windows Explorer context menu: Edit `install_context_menu.reg` with your FileScout.exe path, then double-click to install
   - Create desktop shortcuts: Run `create_desktop_shortcuts.bat`
3. **Configure Google Drive** (for File Audit):
   - Place `google_credentials.json` in the File Scout directory
   - First use will guide you through OAuth authentication

## 📖 Usage Guide

### Basic File Search

1. **Select Directory**: Click "Browse" or drag-and-drop a folder
2. **Configure Filters**:
   - **File Types**: Choose from presets (Documents, Images, etc.) or custom extensions
   - **Size Range**: Set minimum/maximum file sizes
   - **Date Range**: Filter by modification date
   - **Keywords**: Search within filenames or content
3. **Start Search**: Click "Search" to begin
4. **Review Results**: Double-click files to preview, right-click for actions

### Finding Duplicates

1. **Select Directory**: Choose the folder to scan
2. **Switch to Duplicate Mode**: Click "Find Duplicates" tab
3. **Start Scan**: Click "Search" to find duplicate files
4. **Review Groups**: Each group shows identical files
5. **Remove Duplicates**: Select files and choose "Send to Recycle Bin"

### Smart Sort Organization

1. **Select Files**: Use search results or drag files to the dialog
2. **Choose Destination Root**: Where organized folders will be created
3. **Select Sort Mode**:
   - **Pattern Matching**: Automatically matches files to existing folders
   - **Extension-Based**: Groups by file type
   - **Date-Based**: Organizes by creation/modification date
4. **Preview Mappings**: Review where files will be moved
5. **Execute**: Choose "Move" or "Copy" to organize files

### File Preview

- **Double-click** any file in results to preview
- **PDF Viewer**: Full navigation, zoom, search within documents
- **Office Documents**: Preview without opening external programs
- **Code Files**: Syntax-highlighted view with line numbers
- **Media Files**: View metadata and technical information

### Search Profiles

1. **Configure a Search**: Set up your filters and criteria
2. **Save Profile**: File → Save Search Profile
3. **Load Profile**: File → Load Search Profile or access from tray menu
4. **Quick Access**: Recent profiles appear in system tray menu

## 🛠️ Advanced Features

### Command Line Interface

File Scout supports command-line operation for automation:

```bash
# Basic search
python "File Scout 3.2.py" --dir "C:\Documents" --exts "pdf,docx"

# Find duplicates
python "File Scout 3.2.py" --dir "C:\Photos" --duplicates

# Size-based search
python "File Scout 3.2.py" --dir "C:\" --min-size 102400 --exts "mp4,avi"

# Recent files
python "File Scout 3.2.py" --dir "C:\Projects" --days 7
```

### Windows Integration

**Context Menu**:
- Right-click any folder → "File Scout Here"
- Right-click any folder → "Find Duplicates with File Scout"

**System Tray**:
- Double-click to show/hide main window
- Right-click for quick actions and recent profiles
- Close button minimizes to tray (don't exit)

**Keyboard Shortcuts**:
- `Ctrl+H` - Hide to system tray
- `Ctrl++` - Zoom in (in previews)
- `Ctrl+-` - Zoom out (in previews)
- `Ctrl+0` - Reset zoom (in previews)

### File Audit Feature

**For Compliance and Inspection Management**:
1. **Open File Audit**: Tools → File Audit Dialog
2. **Connect Data Source**:
   - **Google Sheets**: Paste live Sheet URL
   - **Excel File**: Browse to local file
3. **Configure Audit**: Select required file types and inspection criteria
4. **Run Audit**: Scan Google Drive folders for missing files
5. **Export Results**: Generate compliance reports in Excel/CSV

## 📋 Supported File Types

### Documents
- **PDF** (.pdf) - Full viewer with search and highlighting
- **Microsoft Word** (.docx) - Preview and metadata
- **Microsoft Excel** (.xlsx, .xls, .xlsm) - Sheet preview
- **Microsoft PowerPoint** (.pptx) - Slide preview
- **Plain Text** (.txt, .log, .csv, .json, .xml, etc.)

### Code Files
- **Python** (.py) - Syntax highlighting
- **JavaScript** (.js, .jsx) - Syntax highlighting
- **Web** (.html, .css, .scss) - Syntax highlighting
- **SQL** (.sql) - Syntax highlighting
- **And many more** - 50+ programming languages

### Media Files
- **Images** (.jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp, .svg, .heic)
- **Audio** (.mp3, .flac, .wav, .aac, .ogg) - Metadata display
- **Video** (.mp4, .avi, .mkv, .mov, .wmv) - Technical information

### Archives
- **ZIP files** (.zip) - Content listing
- **Other formats** - Basic metadata

### Other Files
- **Binary files** - Hexadecimal view
- **Configuration files** - Text preview
- **Database files** - Basic metadata

## 🔧 Configuration

### Settings Location
File Scout stores settings in Windows Registry:
```
HKEY_CURRENT_USER\Software\WindsurfAI\FileScout
```

### Customization Options
- **Themes**: 33 built-in color schemes (View → Themes)
- **Zoom Levels**: Adjustable UI scaling (View → Zoom)
- **File Associations**: Configure external editors
- **Search Limits**: Adjust MAX_RESULTS and MAX_SCAN_FILES in constants.py

### Performance Tuning
- **Large Directory Threshold**: Modify LARGE_DIR_THRESHOLD for performance
- **Memory Usage**: Preview size limited to 1MB by default
- **Concurrent Processing**: Uses ThreadPoolExecutor for file operations

## 🏗️ Architecture

File Scout follows a modular architecture:

```
File Scout 2025/
├── ui/                     # User interface layer
│   ├── main_window.py      # Main application window
│   ├── dialogs/            # Dialog windows
│   └── widgets/            # Custom UI components
├── core/                   # Business logic
│   ├── search_engine.py    # File search and duplicate detection
│   └── file_scanner.py     # Background scanning worker
├── features/               # Feature modules
│   ├── preview/            # File preview system
│   └── smart_sort/         # Organization algorithms
├── utils/                  # Utilities
│   ├── themes.py           # UI themes
│   └── excel_exporter.py   # Export functionality
└── constants.py            # Application constants
```

## 🔌 API Reference

### SearchEngine Class
```python
from core.search_engine import SearchEngine

engine = SearchEngine()
# Find files
for file_info in engine.find_files(params):
    print(file_info['path'])

# Find duplicates
for duplicate_group in engine.find_duplicates(params):
    print(f"Found {len(duplicate_group)} duplicates")
```

### PreviewManager Class
```python
from features.preview.manager import PreviewManager

preview = PreviewManager()
result = preview.generate_preview("document.pdf")
print(result.content_type)  # "pdf_dual"
print(result.data)          # Rendered content
print(result.metadata)      # File information
```

## 🐛 Troubleshooting

### Common Issues

**Application won't start**:
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (requires 3.8+)
- Verify PyQt6 installation: `pip install PyQt6==6.8.0`

**System tray icon not showing**:
- Windows 10/11: Check tray icon settings
- Ensure File Scout is allowed to show notifications

**Google Drive authentication fails**:
- Verify `google_credentials.json` is in the correct directory
- Check that Google Drive API is enabled in your Google Cloud project
- Ensure OAuth client type is set to "Desktop app"

**Search is slow**:
- Reduce search scope or add more specific filters
- Increase LARGE_DIR_THRESHOLD in constants.py
- Check antivirus software isn't interfering

**Preview not working for some files**:
- Install optional dependencies for specific file types
- Check file permissions and ensure files aren't corrupted
- Very large files may exceed preview size limits

### Performance Tips

1. **Use specific filters** - Narrow search criteria for faster results
2. **Exclude system folders** - Add Windows, Program Files to exclusions
3. **Adjust scan limits** - Modify MAX_SCAN_FILES for your system
4. **Use SSD storage** - Faster disk access improves search speed
5. **Close unnecessary applications** - Free up system resources

## 📝 Version History

### v3.2 (Current)
- ✨ Complete modular architecture refactor
- ✨ Enhanced preview system with 50+ file type support
- ✨ Smart Sort with pattern matching and fuzzy suggestions
- ✨ File Audit with Google Drive integration
- ✨ System tray and context menu integration
- ✨ Theme support and UI improvements

### v3.1
- ✨ Basic duplicate file detection
- ✨ File preview for common formats
- ✨ Search profiles functionality

### v3.0
- ✨ Initial PyQt6 interface
- ✨ Basic file search capabilities
- ✨ Excel export functionality

## 🤝 Contributing

File Scout is open to contributions! Areas for improvement:

- **Additional file format support** in preview system
- **More sorting algorithms** for Smart Sort
- **Performance optimizations** for large directories
- **Cross-platform support** (currently Windows-focused)
- **Additional export formats** (JSON, XML, etc.)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues, questions, or feature requests:

1. **Check the troubleshooting section** above
2. **Review existing issues** in the project repository
3. **Create a new issue** with detailed information:
   - File Scout version
   - Windows version
   - Steps to reproduce
   - Error messages or screenshots

## 🙏 Acknowledgments

- **PyQt6** - For the powerful Qt Python bindings
- **PyMuPDF** - For PDF rendering and navigation
- **Google APIs** - For Drive and Sheets integration
- **openpyxl** - For Excel file handling
- **Pygments** - For syntax highlighting in code previews

---

**File Scout 2025** - Making file management effortless! 🎯

*Built with ❤️ for power users and professionals who need to take control of their digital files.*
