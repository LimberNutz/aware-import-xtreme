# File Audit Utility

A Python utility for auditing files in directories based on keyword matches. Designed to help audit file inventories by matching file names with custom keywords and exporting the results to a formatted Excel spreadsheet.

## Features

- **Keyword-based file search**: Search for files containing specific keywords in their names
- **Multiple keyword support**: Enter multiple search terms separated by commas
- **Case-insensitive matching**: Matches keywords regardless of case
- **Regular expression support**: Advanced pattern matching capabilities
- **File filtering**: Focus on specific file types (documents, drawings, spreadsheets, images)
- **Recursive search**: Scan through all subdirectories
- **Excel export**: Export results to a formatted Excel spreadsheet with:
  - Filename in column A
  - Extension in column B
  - Directory path in column C
  - Modified date in column D
  - Last modifier in column E (when available)
- **PyQt6 GUI**: User-friendly graphical interface
- **Progress tracking**: Live updates on search progress
- **Organized output**: Files are grouped by parent directories for better organization

## Requirements

- Python 3.7 or newer
- PyQt6
- openpyxl
- pandas
- pywin32

## Installation

1. Ensure you have Python installed on your system
2. Clone or download this repository
3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:

```bash
python file_audit_util.py
```

2. Using the application:
   - Click "Browse" to select the parent directory to search
   - Enter keywords separated by commas (e.g., "UTT, Report, Drawing")
   - Select file type filter (optional)
   - Check "Use Regular Expressions" for advanced pattern matching (optional)
   - Click "Start Search" to begin
   - When the search completes, click "Export to Excel" to save the results

## Excel Output Format

The exported Excel file contains:
- Formatted headers with frozen top row
- Auto-filter functionality
- Files grouped by parent directory
- Columns for filename, extension, directory path, modified date, and last modifier

## Use Case

This utility was designed to help audit what is displayed in project trackers versus what is actually done and uploaded. For example, finding all UTT (Ultrasonic Thickness Testing) reports across a large directory structure with file naming variations.
