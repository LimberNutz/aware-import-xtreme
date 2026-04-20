@echo off
REM File Scout - Create Desktop Shortcuts with Pre-configured Searches
REM This batch file creates useful shortcuts on your desktop

setlocal EnableDelayedExpansion

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "EXE_PATH=%SCRIPT_DIR%FileScout.exe"

REM Check if FileScout.exe exists
if not exist "%EXE_PATH%" (
    echo ERROR: FileScout.exe not found in %SCRIPT_DIR%
    echo Please make sure FileScout.exe is in the same directory as this batch file.
    pause
    exit /b 1
)

echo Creating File Scout desktop shortcuts...
echo.

REM Desktop path
set "DESKTOP=%USERPROFILE%\Desktop"

REM Create Quick Duplicate Finder shortcut (User folder)
echo Creating: Duplicate Finder - User Folder
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\File Scout - Find Duplicates.lnk'); $s.TargetPath = '%EXE_PATH%'; $s.Arguments = '--dir \"%USERPROFILE%\"'; $s.Description = 'Find duplicate files in your user folder'; $s.Save()"

REM Create Large File Hunter shortcut (C:\ drive, files > 100MB)
echo Creating: Large File Hunter
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\File Scout - Large Files.lnk'); $s.TargetPath = '%EXE_PATH%'; $s.Arguments = '--dir \"C:\\\" --min-size 102400'; $s.Description = 'Find files larger than 100MB'; $s.Save()"

REM Create Recent Files Scanner (User folder, last 7 days)
echo Creating: Recent Files Scanner
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\File Scout - Recent Files.lnk'); $s.TargetPath = '%EXE_PATH%'; $s.Arguments = '--dir \"%USERPROFILE%\" --min-date \"!date!\"'; $s.Description = 'Find recently modified files (last 7 days)'; $s.Save()"

REM Create Image Organizer (User folder, image files only)
echo Creating: Image Organizer
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\File Scout - Images.lnk'); $s.TargetPath = '%EXE_PATH%'; $s.Arguments = '--dir \"%USERPROFILE%\" --exts \"jpg,jpeg,png,gif,bmp,webp\"'; $s.Description = 'Find all image files for organizing'; $s.Save()"

REM Create Document Finder
echo Creating: Document Finder
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\File Scout - Documents.lnk'); $s.TargetPath = '%EXE_PATH%'; $s.Arguments = '--dir \"%USERPROFILE%\" --exts \"doc,docx,pdf,txt,xlsx,pptx\"'; $s.Description = 'Find all documents'; $s.Save()"

echo.
echo ========================================
echo Desktop shortcuts created successfully!
echo ========================================
echo.
echo Shortcuts created:
echo   - File Scout - Find Duplicates
echo   - File Scout - Large Files
echo   - File Scout - Recent Files
echo   - File Scout - Images
echo   - File Scout - Documents
echo.
echo You can now double-click these shortcuts to quickly launch
echo File Scout with pre-configured search parameters.
echo.
pause
