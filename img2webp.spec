# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# データファイルとフォルダ
datas = [
    ('src/img2webp', 'img2webp'),
    ('config/config.json', 'config'),
    ('config/gui_settings.json', 'config'),
]

# 隠されたインポート
hiddenimports = [
    'PIL._tkinter_finder',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.scrolledtext',
    'queue',
    'threading',
    'json',
    'pathlib',
    'docx',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'img2webp',
    'img2webp.gui',
    'img2webp.core',
    'img2webp.config',
    'img2webp.utils',
]

a = Analysis(
    ['gui.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='img2webp',
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
    icon=None,
)
