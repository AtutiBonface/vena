# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py', 'pillar.py', 'settings.py', 'aboutPage.py', 'addlink.py', 'downloadingIndicator.py', 'settingsPage.py', 'networkManager.py', 'progressManager.py', 'storage.py', 'taskManager.py', 'venaUtils.py', 'venaWorker.py'],
    pathex=['images'],
    binaries=[],
    datas=[
        ('images/*', 'images')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # Exclude binaries here
    name='VenaApp',
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
    icon=['images\\main.ico'],
)

# Collect step to gather all files into a directory
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='venaApp',
)

