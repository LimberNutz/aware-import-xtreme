# File Scout 3.2 - Phase 1 Features Guide

## 🎉 New Features Overview

File Scout now includes powerful system integration features to make it easier to use and always accessible:

### ✨ **Phase 1 Features**

1. **System Tray Icon** - Always accessible from your taskbar
2. **Toast Notifications** - Get notified when searches complete
3. **Windows Explorer Context Menu** - Right-click folders to scan them
4. **Desktop Shortcuts** - Pre-configured searches for common tasks

---

## 📋 Feature Details

### 1. System Tray Icon

File Scout now runs in your system tray, providing quick access without cluttering your taskbar.

#### **Features:**
- **Minimize to Tray**: Close the window to minimize to tray (app keeps running)
- **Double-click**: Restore/hide the window
- **Right-click menu** with quick actions:
  - 🔍 Quick Search - Open File Scout
  - 🔄 Find Duplicates - Start duplicate scan
  - 🗂️ Smart Sort - Organize files
  - 📋 Recent Profiles - Load saved search profiles (up to 10)
  - 👁️ Show/Hide Window
  - 🚪 Exit - Completely close the app

#### **Keyboard Shortcut:**
- `Ctrl+H` - Minimize to tray

#### **How to Exit Completely:**
- Right-click tray icon → Exit
- Or: File menu → Exit

---

### 2. Toast Notifications

Get desktop notifications for important events, even when File Scout is minimized.

#### **You'll See Notifications For:**
- ✅ **Search Complete** - "Found 45 files" or "Found 10 duplicate files in 3 groups"
- 💾 **Profile Saved** - "Search profile 'My Docs' saved successfully"
- 📂 **Profile Loaded** - "Loaded search profile: My Docs"
- ⬇️ **Minimized** - Reminds you the app is still running in the tray

#### **Notification Duration:**
- 3 seconds (automatically dismiss)
- Click notification to focus File Scout window

---

### 3. Windows Explorer Context Menu Integration

Right-click any folder in Windows Explorer to quickly scan it with File Scout!

#### **Installation:**

1. **Locate the Registry Files:**
   - `install_context_menu.reg` - Adds context menu
   - `uninstall_context_menu.reg` - Removes context menu

2. **Before Installing:**
   - Open `install_context_menu.reg` in Notepad
   - Replace **ALL instances** of `C:\\Path\\To\\FileScout.exe` with your actual path
   - Example: `C:\\Users\\YourName\\Desktop\\FileScout.exe`
   - Save the file

3. **Install:**
   - Double-click `install_context_menu.reg`
   - Click "Yes" to confirm
   - You'll see "Registry keys successfully added"

4. **Verify:**
   - Right-click any folder in Windows Explorer
   - You should see:
     - **"File Scout Here"** - Search this folder
     - **"Find Duplicates with File Scout"** - Find duplicate files

#### **Usage:**
- **Right-click folder** → "File Scout Here"
  - Opens File Scout with that folder selected
  - Ready to search immediately

- **Right-click folder** → "Find Duplicates with File Scout"
  - Opens File Scout in duplicate finding mode
  - Automatically scans the selected folder

#### **Uninstall:**
- Double-click `uninstall_context_menu.reg`
- Context menu items will be removed

---

### 4. Desktop Shortcuts (Pre-configured Searches)

Create handy shortcuts for common search tasks!

#### **Quick Setup:**

1. Run `create_desktop_shortcuts.bat`
2. Click "Yes" if prompted
3. Five shortcuts will appear on your desktop

#### **Shortcuts Created:**

1. **🔄 File Scout - Find Duplicates**
   - Scans your user folder for duplicate files
   - Great for cleaning up downloads and documents

2. **📏 File Scout - Large Files**
   - Finds files larger than 100MB
   - Helps identify space hogs on your C: drive

3. **🕒 File Scout - Recent Files**
   - Finds files modified in the last 7 days
   - Quick way to find what you worked on recently

4. **🖼️ File Scout - Images**
   - Finds all image files (jpg, png, gif, etc.)
   - Perfect for organizing photo collections

5. **📄 File Scout - Documents**
   - Finds all documents (pdf, docx, xlsx, etc.)
   - Locate all your documents in one search

#### **Customizing Shortcuts:**

To create your own custom shortcut:

1. Right-click desktop → New → Shortcut
2. Enter: `"C:\Path\To\FileScout.exe" --dir "C:\Folder" [options]`
3. Name it and click Finish

**Command-line Options:**
```
--dir "path"           - Directory to search
--duplicates           - Start in duplicate mode
--exts "jpg,png,pdf"   - File extensions
--min-size 1024        - Min size in KB (1024 = 1MB)
--max-size 102400      - Max size in KB (102400 = 100MB)
--keywords "word1,word2" - Search for these words
```

**Examples:**
```batch
REM Find PDFs in Documents
"FileScout.exe" --dir "%USERPROFILE%\Documents" --exts "pdf"

REM Find videos larger than 500MB
"FileScout.exe" --dir "D:\Videos" --exts "mp4,avi,mkv" --min-size 512000

REM Find duplicates in Photos
"FileScout.exe" --dir "C:\Users\Public\Pictures" --duplicates
```

---

## 🎯 Quick Start Guide

### First Time Setup:

1. **Run File Scout** - It will minimize to system tray
2. **Install Context Menu** (optional):
   - Edit `install_context_menu.reg` with your FileScout.exe path
   - Double-click to install
3. **Create Shortcuts** (optional):
   - Run `create_desktop_shortcuts.bat`
4. **Save Profiles**:
   - Configure a search you use often
   - File menu → Save Search Profile
   - Access it from the tray menu!

### Daily Usage:

- **Quick Access**: Double-click tray icon
- **From Explorer**: Right-click folder → "File Scout Here"
- **From Desktop**: Use pre-configured shortcuts
- **Background Searches**: Start search, minimize to tray, get notified when done

---

## 🛠️ Tips & Tricks

### 1. **Run at Startup** (Optional)
To have File Scout always available:
- Press `Win+R`
- Type: `shell:startup`
- Create a shortcut to FileScout.exe in that folder
- File Scout will start minimized in tray on login

### 2. **Keyboard Shortcuts**
- `Ctrl+H` - Hide to tray
- `Ctrl++` - Zoom in
- `Ctrl+-` - Zoom out
- `Ctrl+0` - Reset zoom

### 3. **Profile Power User Tip**
Create profiles for:
- Work documents (specific folder, doc extensions, last 30 days)
- Photos to organize (image extensions, min size filter)
- Cleanup scans (duplicates, large files)
- Access them instantly from the tray menu!

### 4. **Toast Notification Management**
- Windows 10/11: Settings → System → Notifications
- Find "File Scout" to customize notification behavior
- Can enable/disable sound, banner style, etc.

---

## 📦 Building the EXE

To package File Scout as a standalone .exe:

### Using PyInstaller:

```bash
# Install PyInstaller
pip install pyinstaller

# Create the EXE (windowed, no console)
pyinstaller --name "FileScout" --windowed --onefile "File Scout 3.2.py"

# The EXE will be in: dist\FileScout.exe
```

### Recommended PyInstaller Options:

```bash
pyinstaller ^
  --name "FileScout" ^
  --windowed ^
  --onefile ^
  --icon=filescout.ico ^
  --add-data "file_audit_dialog.py;." ^
  "File Scout 3.2.py"
```

### After Building:

1. Copy `FileScout.exe` to your desired location
2. Update paths in `install_context_menu.reg`
3. Run `create_desktop_shortcuts.bat` from the same folder as the EXE

---

## ❓ Troubleshooting

### **System Tray Icon Not Showing:**
- Check Windows tray settings: Right-click taskbar → Taskbar settings → Select which icons appear
- Make sure File Scout is allowed to show in tray

### **Context Menu Not Working:**
- Verify the path in the .reg file is correct
- Use double backslashes: `C:\\Users\\...` not `C:\Users\...`
- Run as Administrator when installing the .reg file

### **Toast Notifications Not Appearing:**
- Check Windows notification settings for File Scout
- Make sure "Focus Assist" is not blocking notifications

### **Shortcuts Don't Work:**
- Make sure FileScout.exe is in the same folder as the .bat file
- Check that paths don't have special characters
- Run .bat as Administrator if needed

---

## 📝 Version History

### v3.2 - Phase 1 Features
- ✨ System tray icon with context menu
- ✨ Toast notifications for search completion
- ✨ Windows Explorer context menu integration
- ✨ Desktop shortcut creator for common tasks
- ✨ Command-line --duplicates flag
- ✨ Minimize to tray on window close
- ✨ Recent profiles in tray menu (up to 10)

---

## 🚀 Coming in Phase 2

- Global hotkeys (e.g., Ctrl+Alt+F to open File Scout)
- File drop zone when minimized
- Send To menu integration
- Scheduled scans

---

## 💬 Feedback

Enjoying File Scout? Have suggestions for new features? Let us know!

---

**File Scout v3.2** - Making file management effortless! 🎯
