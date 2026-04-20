#!/usr/bin/env python3
"""
File Scout Enhanced Preview Test Script
Creates test files to demonstrate the new preview functionality.
"""

import os
import json
import zipfile
from pathlib import Path

def create_test_files():
    """Create various test files to preview."""
    test_dir = Path("preview_test_files")
    test_dir.mkdir(exist_ok=True)
    
    print("Creating test files for enhanced preview...")
    
    # 1. Python code file (syntax highlighting)
    py_file = test_dir / "sample_code.py"
    py_content = '''#!/usr/bin/env python3
"""
Sample Python file for syntax highlighting test.
"""

import os
import sys
from pathlib import Path

def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def main():
    print("Fibonacci sequence:")
    for i in range(10):
        print(f"F({i}) = {calculate_fibonacci(i)}")

if __name__ == "__main__":
    main()
'''
    py_file.write_text(py_content, encoding='utf-8')
    print(f"✓ Created: {py_file}")
    
    # 2. JSON file (formatted preview)
    json_file = test_dir / "config.json"
    json_content = {
        "app_name": "File Scout",
        "version": "3.2",
        "features": {
            "system_tray": True,
            "toast_notifications": True,
            "context_menu": True,
            "enhanced_preview": True
        },
        "file_types": [
            "text", "code", "pdf", "excel", "word", "image"
        ]
    }
    json_file.write_text(json.dumps(json_content, indent=2), encoding='utf-8')
    print(f"✓ Created: {json_file}")
    
    # 3. Markdown file (formatted preview)
    md_file = test_dir / "README.md"
    md_content = '''# File Scout Enhanced Preview

## Features

- **Syntax Highlighting**: Code files with colored syntax
- **Document Preview**: PDF, Word, Excel, PowerPoint
- **Media Info**: Audio metadata and video information
- **Archive Contents**: ZIP file listings
- **Hex View**: Binary file inspection

## Supported File Types

### Code Files
- Python (.py)
- JavaScript (.js)
- HTML/CSS
- And many more!

### Documents
- PDF (.pdf)
- Word (.docx)
- Excel (.xlsx)
- PowerPoint (.pptx)

### Media
- Images (.jpg, .png, .gif)
- Audio (.mp3, .flac, .wav)
- Video (.mp4, .avi, .mkv)

### Archives
- ZIP files with content listing
'''
    md_file.write_text(md_content, encoding='utf-8')
    print(f"✓ Created: {md_file}")
    
    # 4. ZIP archive (content preview)
    zip_file = test_dir / "sample_archive.zip"
    with zipfile.ZipFile(zip_file, 'w') as zf:
        # Add some files to the archive
        zf.writestr("document.txt", "This is a sample text file inside the archive.")
        zf.writestr("data.json", '{"type": "test", "value": 123}')
        zf.writestr("subfolder/nested.txt", "Nested file content here.")
        zf.writestr("readme.txt", "Archive created for File Scout preview testing.")
    print(f"✓ Created: {zip_file}")
    
    # 5. Binary file (hex preview)
    bin_file = test_dir / "sample_binary.bin"
    binary_data = bytes(range(256)) * 2  # Create some binary data
    bin_file.write_bytes(binary_data)
    print(f"✓ Created: {bin_file}")
    
    # 6. Configuration file
    cfg_file = test_dir / "settings.ini"
    cfg_content = '''[Application]
name=File Scout
version=3.2
author=WindsurfAI

[Display]
theme=light
zoom_level=100
show_hidden_files=false

[Search]
max_results=10000
include_subdirs=true
case_sensitive=false
'''
    cfg_file.write_text(cfg_content, encoding='utf-8')
    print(f"✓ Created: {cfg_file}")
    
    # 7. Log file
    log_file = test_dir / "application.log"
    log_content = '''2025-01-30 10:00:00 INFO: Application started
2025-01-30 10:00:01 INFO: Loading configuration
2025-01-30 10:00:02 DEBUG: System tray initialized
2025-01-30 10:00:03 INFO: Preview handlers registered
2025-01-30 10:00:04 WARNING: PyMuPDF not available - PDF preview disabled
2025-01-30 10:00:05 INFO: Enhanced preview system ready
2025-01-30 10:00:06 DEBUG: User selected file for preview
2025-01-30 10:00:07 INFO: Preview generated successfully
'''
    log_file.write_text(log_content, encoding='utf-8')
    print(f"✓ Created: {log_file}")
    
    # 8. SQL file
    sql_file = test_dir / "sample_query.sql"
    sql_content = '''-- Sample SQL queries for testing
SELECT * FROM files 
WHERE size > 1024 
  AND created_date >= '2025-01-01'
ORDER BY size DESC;

-- Find duplicate files
SELECT file_hash, COUNT(*) as duplicate_count
FROM files 
GROUP BY file_hash 
HAVING COUNT(*) > 1;

-- File type statistics
SELECT 
    SUBSTRING_INDEX(file_name, '.', -1) as extension,
    COUNT(*) as count,
    SUM(size) as total_size
FROM files 
GROUP BY extension 
ORDER BY count DESC;
'''
    sql_file.write_text(sql_content, encoding='utf-8')
    print(f"✓ Created: {sql_file}")
    
    print(f"\n🎉 Test files created in: {test_dir.absolute()}")
    print("\nTo test the enhanced preview:")
    print("1. Run File Scout 3.2")
    print("2. Search in the test directory")
    print("3. Select different files to see enhanced previews!")
    print("\nPreview features to test:")
    print("• Python/SQL/JSON files - syntax highlighting")
    print("• Markdown files - formatted rendering")  
    print("• ZIP files - content listing")
    print("• Binary files - hex dump view")
    print("• All files - detailed properties tab")
    
    return test_dir

if __name__ == "__main__":
    create_test_files()
