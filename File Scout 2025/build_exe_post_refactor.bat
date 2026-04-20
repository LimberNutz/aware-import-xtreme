@echo off
REM ========================================
REM File Scout 3.3 - Build Script (Post-Refactor)
REM ========================================
REM This script builds File Scout as a standalone .exe
REM using PyInstaller with all necessary packages and modules.

echo.
echo ========================================
echo File Scout 3.3 - EXE Builder (Post-Refactor)
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from python.org
    pause
    exit /b 1
)

echo [1/6] Checking PyInstaller installation...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
) else (
    echo ✓ PyInstaller is installed
)

echo.
echo [2/6] Checking for icon files...
if exist "filescout.ico" (
    echo ✓ Found filescout.ico
    set "ICON_ARG=--icon=filescout.ico"
) else (
    echo WARNING: filescout.ico not found
    echo Run create_icon.py first to generate icons
    echo Continuing without custom icon...
    set "ICON_ARG="
)

echo.
echo [3/6] Checking for source file...
if not exist "File Scout 3.3.py" (
    echo ERROR: File Scout 3.3.py not found in current directory
    pause
    exit /b 1
)
echo ✓ Found File Scout 3.3.py

echo.
echo [4/6] Checking package structure...
if not exist "ui\" (
    echo ERROR: ui\ package not found - refactor incomplete
    pause
    exit /b 1
)
if not exist "core\" (
    echo ERROR: core\ package not found - refactor incomplete
    pause
    exit /b 1
)
if not exist "features\" (
    echo ERROR: features\ package not found - refactor incomplete
    pause
    exit /b 1
)
if not exist "utils\" (
    echo ERROR: utils\ package not found - refactor incomplete
    pause
    exit /b 1
)
echo ✓ All package directories found

echo.
echo [5/6] Building executable...
echo This may take 3-7 minutes due to package structure...
echo.

REM Build the executable with all packages
pyinstaller ^
  --name "FileScout" ^
  --windowed ^
  --onefile ^
  %ICON_ARG% ^
  --add-data "ui;ui" ^
  --add-data "core;core" ^
  --add-data "features;features" ^
  --add-data "utils;utils" ^
  --add-data "config.py;." ^
  --add-data "file_audit_dialog.py;." ^
  --add-data "filescout.png;." ^
  --hidden-import "ui.main_window" ^
  --hidden-import "ui.dialogs.file_audit_dialog" ^
  --hidden-import "ui.dialogs.profile_manager" ^
  --hidden-import "ui.dialogs.smart_sort_dialog" ^
  --hidden-import "ui.widgets.custom_widgets" ^
  --hidden-import "core.file_scanner" ^
  --hidden-import "core.search_engine" ^
  --hidden-import "features.preview.manager" ^
  --hidden-import "features.preview.handlers" ^
  --hidden-import "features.smart_sort.fuzzy_matcher" ^
  --hidden-import "features.smart_sort.pattern_matcher" ^
  --hidden-import "features.smart_sort.sort_executor" ^
  --hidden-import "utils.themes" ^
  --hidden-import "utils.excel_exporter" ^
  --hidden-import "config" ^
  --hidden-import "constants" ^
  --hidden-import "openpyxl" ^
  --hidden-import "csv" ^
  --hidden-import "json" ^
  --hidden-import "pandas" ^
  --hidden-import "send2trash" ^
  --hidden-import "PIL" ^
  --hidden-import "pathlib" ^
  --hidden-import "argparse" ^
  --hidden-import "hashlib" ^
  --hidden-import "mimetypes" ^
  --hidden-import "shutil" ^
  --hidden-import "datetime" ^
  --hidden-import "subprocess" ^
  --hidden-import "google.auth" ^
  --hidden-import "google.auth.oauthlib" ^
  --hidden-import "google.auth.transport.requests" ^
  --hidden-import "googleapiclient.discovery" ^
  --hidden-import "googleapiclient.http" ^
  --exclude-module "PySide6" ^
  --hidden-import "fitz" ^
  --collect-all "pandas" ^
  --collect-all "openpyxl" ^
  --clean ^
  "File Scout 3.3.py"

if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Build failed!
    echo ========================================
    echo Check the error messages above
    pause
    exit /b 1
)

echo.
echo [6/6] Verifying build...
if exist "dist\FileScout.exe" (
    echo.
    echo ========================================
    echo ✓ BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable location: dist\FileScout.exe
    
    REM Get file size
    for %%A in ("dist\FileScout.exe") do set "SIZE=%%~zA"
    set /a "SIZE_MB=%SIZE% / 1048576"
    echo File size: %SIZE_MB% MB
    
    echo.
    echo Next steps:
    echo  1. Test the executable: dist\FileScout.exe
    echo  2. Copy filescout.png to the same folder as FileScout.exe
    echo  3. Update paths in install_context_menu.reg
    echo  4. Run create_desktop_shortcuts.bat
    echo.
    echo Optional:
    echo  • Copy FileScout.exe to a permanent location
    echo  • Create a shortcut in shell:startup for auto-start
    echo  • Install context menu with install_context_menu.reg
    echo.
) else (
    echo.
    echo ========================================
    echo ERROR: FileScout.exe was not created
    echo ========================================
    echo Check the build output above for errors
    pause
    exit /b 1
)

REM Optional: Copy icon to dist folder
if exist "filescout.png" (
    echo Copying icon to dist folder...
    copy /Y "filescout.png" "dist\filescout.png" >nul 2>&1
    echo ✓ Icon copied
    echo.
)

echo Build artifacts saved in: build\ and dist\
echo You can safely delete the build\ folder after testing
echo.
pause
