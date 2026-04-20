# File Audit Feature - Google Drive & Sheets Integration

## Overview
The File Audit feature has been integrated into File Scout as a separate dialog accessible from the **Tools** menu. This feature allows you to audit Google Drive folders for missing inspection files based on traveler data from **live Google Sheets** or local Excel files.

## What It Does
- **Reads from live Google Sheets** (always current data) OR local Excel files
- Automatically detects input type (Sheet URL vs file path)
- Parses traveler data (API-510, API-570, Tank Traveler tabs)
- Scans Google Drive folders linked to each entity
- Checks for required files (Photos, VT Reports, UT Reports, ISO drawings, DR files)
- Uses "partial credit" logic - only checks files if corresponding fields are filled
- Exports missing items to Excel or CSV

## 🎉 NEW: Live Google Sheets Support
No more manual exports! You can now:
- ✅ **Use live Google Sheet URLs** - Always get current data
- ✅ **Auto-detect input type** - Just paste the Sheet URL
- ✅ **Same authentication** - Drive and Sheets use the same OAuth login
- ✅ **Faster** - No file downloads or temporary files
- ✅ **Excel still works** - Local files supported as fallback

## Setup Instructions

### 1. Install Dependencies
```bash
cd "C:\Users\cherr\Desktop\Codes\File Scout 2025"
pip install -r requirements.txt
```

This will install the Google Drive API libraries:
- google-auth
- google-auth-oauthlib
- google-auth-httplib2
- google-api-python-client

### 2. Obtain Google OAuth Credentials
You need OAuth credentials to access Google Drive:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Choose "Desktop app" as the application type
6. Download the credentials JSON file
7. Rename it to `google_credentials.json`
8. Place it in the File Scout 2025 directory

**Important:** The credentials file should be named exactly `google_credentials.json` and placed in:
```
C:\Users\cherr\Desktop\Codes\File Scout 2025\google_credentials.json
```

### 3. First-Time Authentication
On first use:
1. Open File Scout
2. Go to **Tools → File Audit (Google Drive)...**
3. Click **"🔐 Authenticate with Google"**
4. A browser window will open
5. Log in with your Google account
6. Grant the app read-only access to Google Drive
7. The credentials will be saved in `google_token.pickle`

After first authentication, you won't need to log in again unless you revoke access.

## Usage

### Basic Workflow

#### Using Google Sheets (Recommended)
1. Open File Scout
2. Go to **Tools → File Audit (Google Drive)...**
3. **Paste your Google Sheet URL** into the input field
   - Example: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`
   - Or just the Sheet ID: `YOUR_SHEET_ID`
4. Select which tabs to audit (API-510, API-570, Tank)
5. (Optional) Filter by inspector initials
6. Click **"🔐 Authenticate with Google"** (first time only)
7. Click **"▶ Start Audit"**
8. Watch as it reads live data from your Sheet!
9. Review results in the table
10. Export to Excel or CSV

#### Using Excel Files (Fallback)
1. Open File Scout
2. Go to **Tools → File Audit (Google Drive)...**
3. Click **Browse Local File...** to select your Excel traveler file
4. Continue with steps 4-10 above

### Traveler File Requirements

**For Google Sheets (Recommended):**
- Live Google Sheet URL or Sheet ID
- Must have one or more of these tabs:
  - "API-510 Traveler"
  - "API-570 Traveler"
  - "Tank Traveler"
- Headers should be in Row 6
- Data should start in Row 7
- Entity names in Column A
- Entity cells must have hyperlinks to Google Drive folders
- **No need to download or export** - reads directly from Sheet!

**For Excel Files (Fallback):**
- Excel file (.xlsx or .xls)
- Same requirements as above

### File Matching Rules (Enhanced for Nested Structures)
The audit now intelligently searches through nested subfolders:

| File Type | Checked When | What It Looks For | Where It Looks |
|-----------|--------------|-------------------|----------------|
| **Photos** | EXT VT Date is filled | Image files (.jpg, .png, etc.) with inspection-related keywords | First checks dedicated photo folders, then looks for images named with inspection terms like "overview", "bottom head", "nozzle", "shell", etc. |
| **EXT VT Report** | EXT VT Report column has value | Files with "vt", "visual", or "inspection" in name | Inside folders containing "external" (e.g., `EXTERNAL INSPECTION\...`) |
| **INT VT Report** | INT VT Report column has value | Files with "vt", "visual", "inspection", or "internal" in name | Inside folders containing "internal" (e.g., `INTERNAL INSPECTION\Internal Inspection\...`) |
| **UT Report** | UT Report column has value | Files with "ut", "thickness", "utt", or "ultrasonic" in name | Anywhere in folder structure (Excel/PDF files) |

**Supported File Extensions:**
- Reports: `.xlsx`, `.xls`, `.pdf`, `.docx`, `.doc`
- Photos: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tiff`, `.tif`, `.webp`

**Examples of Matching Paths:**
- ✅ `EXTERNAL INSPECTION\3001-VE-001_EXTERNAL VT.xlsx`
- ✅ `INTERNAL INSPECTION\Internal Inspection\3001-VE-001_INTERNAL VT.xlsx`
- ✅ `PICTURES\photo1.jpg` (photos in dedicated folder)
- ✅ `Photos\IMG_0001.jpeg` (photos in dedicated folder)
- ✅ `EXTERNAL INSPECTION\Bottom Head.jpg` (loose inspection photo)
- ✅ `EXTERNAL INSPECTION\OVERVIEW.jpg` (loose inspection photo)
- ✅ `3004-VE-001\NP.jpg` (loose inspection photo)
- ✅ `UT Reports\Thickness_Report.xlsx`

**Photo Detection Strategy:**
1. **First**: Looks for images in folders named "photo", "picture", "pic", or "image"
2. **Fallback**: If no photo folder, looks for images with inspection keywords:
   - Overview, head, shell, nozzle, bottom, top, vessel, tank, internal, external, view, np
3. **Excludes**: Logo, icon, signature, letterhead images (not inspection photos)

### Filtering by Inspector
- Leave the "Inspector Initials" field blank to audit all entities
- Enter initials (e.g., "PO", "CS") to audit only entities assigned to that inspector
- The filter checks the API and TECH columns

### Clickable Entity Links
- Entity names in the results table are **clickable hyperlinks** (shown in blue with underline)
- Click any entity name to open its Google Drive folder in your browser
- Cursor changes to a pointing hand when hovering over clickable entities
- Useful for quick navigation to folders that are missing files

### Enhanced Diagnostics
The audit provides detailed diagnostic information to help understand why files are missing:

**Example Error Messages:**
- "No image files found in folder" (truly no images)
- "Found 12 images, but all were excluded (logo/icon/signature files)" (wrong type of images)
- "Found 8 images, but none matched inspection criteria" (images present but not inspection photos)
- "Found 5 reports in external folders, but none with VT/visual/inspection keywords" (reports exist but missing keywords)
- "Folder is empty (no files or subfolders found)" (vs "Unable to access folder (permission denied)")

**Benefits:**
- Know exactly what was found vs what was expected
- Understand if it's a missing file issue or a naming/organization issue
- Better assignee tracking for missing folder links

### Export Options
- **Export to Excel** - Creates formatted Excel file with results
- **Export to CSV** - Creates CSV file for import into other systems

## Troubleshooting

### "Feature Unavailable" Message
- The Google Drive API libraries are not installed
- Run: `pip install -r requirements.txt`

### "Credentials Missing" Error
- You need to create the `google_credentials.json` file
- Follow the setup instructions above

### "Authentication Failed"
- Delete `google_token.pickle` and try again
- Make sure you're using the correct Google account
- Check that you granted Drive access permissions

### "Folder Not Found" or "Folder Access" Errors
- Verify the Drive folder link in the traveler is correct
- Make sure you have access to the folder
- Try opening the folder in your browser first
- Check that the hyperlink in Excel points to a valid Drive folder

### "No Entities Found"
- Check that the traveler file has the correct format
- Ensure data starts in Row 7
- Verify tab names match exactly (case-sensitive)

## Technical Details

### Architecture
```
File Scout Main Window
└── Tools Menu
    └── File Audit (Google Drive)...
        └── FileAuditDialog
            ├── Traveler Parser
            ├── Drive Scanner  
            ├── File Matcher
            └── Results Table
```

### File Locations
- Main dialog: `file_audit_dialog.py`
- OAuth credentials: `google_credentials.json` (you create this)
- Auth token: `google_token.pickle` (auto-generated)
- Requirements: `requirements.txt`

### Permissions Required
- **Google Drive (Read-Only)** - To scan folders and list files
- No write access is requested or needed

### Data Privacy
- All processing happens locally on your computer
- File Audit only reads Drive metadata (file names, folder structure)
- No file contents are downloaded or accessed
- No data is sent to external servers
- OAuth tokens are stored locally and never shared

## Integration with File Scout

### Theme Support
The File Audit dialog automatically uses File Scout's current theme:
- All File Scout themes are supported
- Dialog styling matches the main application
- Theme changes don't require reopening the dialog

### Menu Access
```
File Scout Menu Bar
├── File
├── Settings
│   └── Theme (applies to File Audit too)
└── Tools
    ├── Smart Sort...
    └── File Audit (Google Drive)...  ← NEW
```

## Version Info
- Integrated: October 19, 2025
- Based on: North Traveler File Auditor
- Compatible with: File Scout 3.2+
- Python: 3.8+
- PyQt: 6.x

## Support
If you encounter issues:
1. Check this README for troubleshooting steps
2. Verify your Google OAuth credentials are set up correctly
3. Ensure you have the latest dependencies installed
4. Check that your traveler file matches the expected format

## Future Enhancements
Potential improvements for future versions:
- Support for additional traveler tab formats
- Batch processing multiple traveler files
- Custom file matching rules
- Integration with IDMS systems
- Automatic remediation suggestions
- Scheduled/automated audits
