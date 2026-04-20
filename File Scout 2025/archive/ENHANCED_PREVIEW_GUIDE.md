# File Scout 3.2 - Enhanced Preview System

## 🎉 New Preview Features

File Scout now supports **50+ file types** with intelligent preview handling, syntax highlighting, and detailed file information!

---

## 📋 Supported File Types

### 📝 **Text & Code Files** (Syntax Highlighted)
- **Programming Languages**: Python (.py), JavaScript (.js), Java (.java), C/C++ (.c, .cpp, .h), C# (.cs), PHP (.php), Ruby (.rb), Go (.go), Rust (.rs), Swift (.swift), Kotlin (.kt), Scala (.scala)
- **Web Technologies**: HTML (.html), CSS (.css), TypeScript (.ts), JSX (.jsx), XML (.xml)
- **Configuration**: JSON (.json), YAML (.yml, .yaml), TOML (.toml), INI (.ini), .env, .gitignore
- **Scripts**: Shell (.sh), Batch (.bat), PowerShell (.ps1), SQL (.sql)
- **Documentation**: Markdown (.md), reStructuredText (.rst), Text (.txt), Log (.log)

### 📄 **Document Files**
- **PDF** (.pdf) - Text extraction with page count
- **Word** (.docx) - Document content preview
- **Excel** (.xlsx, .xls) - Spreadsheet data grid (first 10x10 cells)
- **PowerPoint** (.pptx) - Slide text content

### 🖼️ **Image Files**
- **Formats**: JPG, PNG, GIF, BMP, TIFF, WebP, SVG
- **Features**: Scaled preview, dimensions, file size, tooltip info

### 🎵 **Audio Files**
- **Formats**: MP3, FLAC, OGG, WAV, M4A, AAC
- **Features**: Metadata extraction (artist, album, title, bitrate, duration)

### 🎬 **Video Files**
- **Formats**: MP4, AVI, MKV, MOV, WMV, FLV, WebM
- **Features**: File information, size, format details

### 📦 **Archive Files**
- **ZIP** (.zip) - Complete file listing, total size, file count
- **Other Archives** (.rar, .7z, .tar, .gz) - Basic info support

### 🔧 **Binary Files**
- **Formats**: EXE, DLL, BIN, DAT, IMG, ISO
- **Features**: Hex dump view with ASCII representation

---

## 🎨 Preview Tabs

### **🖼️ Image Tab**
- Scaled image preview (max 400x300)
- Hover tooltip with dimensions and file size
- Supports all common image formats

### **📄 Text/Code Tab**
- Plain text view for all supported files
- Monospace font (Consolas) for better readability
- Fallback when syntax highlighting unavailable

### **🎨 Formatted Tab**
- **Syntax-highlighted code** with line numbers
- **Monokai theme** for dark, professional appearance
- **Markdown rendering** with formatting
- **JSON pretty-printing** with proper indentation
- Auto-switches to this tab when syntax highlighting is available

### **ℹ️ Properties Tab**
- **File Information**: Name, path, extension, size, MIME type
- **Timestamps**: Created, modified, accessed dates
- **Attributes**: Read-only, hidden, executable status
- **Preview Handler**: Shows which handler is processing the file
- **Hash Information**: MD5 hash of first 8KB (for files < 50MB)

---

## 🚀 Installation

### **Basic Preview (No Extra Dependencies)**
The enhanced preview system works out-of-the-box for:
- Images
- Plain text files
- ZIP archives
- Binary files (hex view)
- File properties

### **Full Enhanced Preview**
Install optional dependencies for maximum functionality:

```bash
# Install all preview dependencies
pip install -r preview_requirements.txt

# Or install individually:
pip install Pygments          # Syntax highlighting
pip install PyMuPDF           # PDF preview
pip install python-docx       # Word documents
pip install python-pptx       # PowerPoint
pip install mutagen           # Audio metadata
```

---

## 💡 Usage Examples

### **1. Code Review**
```bash
# Search for Python files
FileScout.exe --dir "C:\MyProject" --exts "py"

# Select any .py file → See syntax-highlighted code with line numbers
# Switch between Text and Formatted tabs to compare views
```

### **2. Document Inspection**
```bash
# Find all documents
FileScout.exe --dir "C:\Documents" --exts "pdf,docx,xlsx,pptx"

# Click PDF → See extracted text with page count
# Click Excel → See spreadsheet data in tabular format
# Click Word → See document paragraphs
```

### **3. Archive Management**
```bash
# Find ZIP files
FileScout.exe --dir "C:\Downloads" --exts "zip"

# Select ZIP → See complete file listing
# Properties tab shows total size and file count
```

### **4. Media Organization**
```bash
# Find audio files
FileScout.exe --dir "C:\Music" --exts "mp3,flac,wav"

# Select audio file → See metadata (artist, album, etc.)
# Properties tab shows file size and format info
```

---

## 🔧 Technical Details

### **Preview Handler Architecture**
```python
class PreviewHandler:
    def can_handle(self, file_path)      # Check if supported
    def generate_preview(self, file_path)  # Return (type, content, metadata)

# Built-in handlers:
- TextPreviewHandler      # Text files with syntax highlighting
- CodePreviewHandler      # Source code with Pygments
- PDFPreviewHandler       # PDF text extraction
- ExcelPreviewHandler     # Spreadsheet data
- WordPreviewHandler      # Document content
- PowerPointPreviewHandler # Slide text
- AudioPreviewHandler     # Metadata extraction
- VideoPreviewHandler     # File information
- ArchivePreviewHandler   # ZIP contents
- HexPreviewHandler       # Binary hex dump
```

### **Performance Features**
- **Lazy Loading**: Libraries loaded only when needed
- **Size Limits**: Prevents memory issues with large files
- **Async Safe**: Non-blocking preview generation
- **Error Handling**: Graceful fallbacks for unsupported files

### **Memory Management**
- Text files: 5KB limit for preview
- Images: Scaled to 400x300 maximum
- Archives: First 50 files listed
- Binary files: First 512 bytes in hex view
- Documents: First 20 paragraphs/slides

---

## 🎯 Preview Features by File Type

| File Type | Text Tab | Formatted Tab | Properties | Special Features |
|-----------|----------|---------------|------------|------------------|
| **Python** | ✓ Code | ✓ Syntax Highlighted | ✓ | Line numbers, Monokai theme |
| **JavaScript** | ✓ Code | ✓ Syntax Highlighted | ✓ | Full ES6+ syntax support |
| **JSON** | ✓ Raw | ✓ Pretty Printed | ✓ | Proper indentation |
| **Markdown** | ✓ Source | ✓ Rendered | ✓ | Headers, lists, formatting |
| **PDF** | ✓ Text | ✗ | ✓ | Page count, text extraction |
| **Excel** | ✓ Data | ✗ | ✓ | 10x10 grid, sheet info |
| **Word** | ✓ Text | ✗ | ✓ | Paragraph content |
| **ZIP** | ✓ Listing | ✗ | ✓ | File count, total size |
| **Image** | ✗ | ✗ | ✓ | Scaled preview, dimensions |
| **Audio** | ✓ Metadata | ✗ | ✓ | Artist, album, bitrate |
| **Binary** | ✓ Hex | ✗ | ✓ | 512 bytes, ASCII view |

---

## 🛠️ Troubleshooting

### **"PyMuPDF not installed"**
```bash
pip install PyMuPDF
```
PDF preview requires this library.

### **"python-docx not installed"**
```bash
pip install python-docx
```
Word document preview requires this library.

### **"mutagen not installed"**
```bash
pip install mutagen
```
Audio metadata requires this library.

### **Syntax highlighting not working**
```bash
pip install Pygments
```
Code highlighting requires Pygments.

### **Preview shows "No preview handler available"**
- The file type is not yet supported
- Check the file extension
- Ensure the file exists and is readable

### **Large files cause slow preview**
- Preview system automatically limits file sizes
- Text files: 5KB maximum
- Images: Automatically scaled
- Archives: First 50 files only

---

## 🔮 Future Enhancements

### **Planned Features**
- **Video Thumbnails**: Extract first frame from video files
- **Image Similarity**: Perceptual hashing for duplicate detection
- **More Archive Formats**: RAR, 7Z, TAR.GZ full support
- **Document Rendering**: Actual document layout preview
- **Code Analysis**: Function detection, complexity metrics
- **Batch Preview**: Preview multiple files simultaneously

### **Potential Handlers**
```python
# Future preview handlers:
- VideoThumbnailHandler    # Extract video frames
- ImageAnalysisHandler     # EXIF data, similarity
- CodeAnalysisHandler      # Function detection
- DatabaseHandler          # SQLite database preview
- ConfigHandler           # Specialized config file parsing
```

---

## 📊 Performance Impact

### **Memory Usage**
- Base system: ~50MB
- With all dependencies: ~55MB
- Preview generation: <5MB additional

### **Startup Time**
- No impact on application startup
- Libraries loaded lazily when needed
- Preview generation: <100ms for text files

### **File Size Limits**
- Text files: 5KB preview limit
- Images: Scaled to 400x300
- Archives: 50 file listing limit
- Binary: 512 bytes hex view

---

## 🎉 Benefits

1. **Faster File Inspection**: No need to open external applications
2. **Code Review**: Syntax-highlighted code with line numbers
3. **Document Preview**: Quick content without opening Office
4. **Archive Management**: See ZIP contents without extraction
5. **Media Organization**: Metadata for audio/video files
6. **Binary Analysis**: Hex view for executable files
7. **Universal Properties**: Detailed file information for all types

---

## 📝 Version History

### **v3.2 - Enhanced Preview System**
- ✅ 50+ file type support
- ✅ Syntax highlighting with Pygments
- ✅ Document preview (PDF, Word, Excel, PowerPoint)
- ✅ Audio/video metadata
- ✅ Archive content listing
- ✅ Hex dump for binary files
- ✅ Enhanced properties tab
- ✅ Multi-tab interface
- ✅ Lazy loading for performance

---

**File Scout 3.2** - Now with intelligent file preview! 🚀

For the best experience, install the optional dependencies:
```bash
pip install -r preview_requirements.txt
```
