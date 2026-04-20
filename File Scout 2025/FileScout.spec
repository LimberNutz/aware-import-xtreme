# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('ui', 'ui'), ('core', 'core'), ('features', 'features'), ('utils', 'utils'), ('config.py', '.'), ('file_audit_dialog.py', '.'), ('filescout.png', '.')]
binaries = []
hiddenimports = ['ui.main_window', 'ui.dialogs.file_audit_dialog', 'ui.dialogs.profile_manager', 'ui.dialogs.smart_sort_dialog', 'ui.widgets.custom_widgets', 'core.file_scanner', 'core.search_engine', 'features.preview.manager', 'features.preview.handlers', 'features.smart_sort.fuzzy_matcher', 'features.smart_sort.pattern_matcher', 'features.smart_sort.sort_executor', 'utils.themes', 'utils.excel_exporter', 'config', 'constants', 'openpyxl', 'csv', 'json', 'pandas', 'send2trash', 'PIL', 'pathlib', 'argparse', 'hashlib', 'mimetypes', 'shutil', 'datetime', 'subprocess', 'google.auth', 'google.auth.oauthlib', 'google.auth.transport.requests', 'googleapiclient.discovery', 'googleapiclient.http', 'fitz']
tmp_ret = collect_all('pandas')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('openpyxl')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['File Scout 3.3.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6', 'tensorflow', 'keras', 'torch', 'torchvision', 'torchaudio', 'scipy', 'matplotlib', 'jupyter', 'notebook', 'sklearn', 'nltk', 'spacy', 'cv2', 'pygame'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FileScout',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['filescout.ico'],
)
