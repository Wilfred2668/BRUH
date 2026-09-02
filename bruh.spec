# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from pathlib import Path

block_cipher = None

# Collect all hidden imports across rules and internal packages
hidden_imports = []
hidden_imports += collect_submodules('bruh')
hidden_imports += collect_submodules('bruh.rules')
hidden_imports += collect_submodules('bruh.rules.languages')
hidden_imports += collect_submodules('bruh.rules.domains')
hidden_imports += collect_submodules('bruh.rules.system')
hidden_imports += collect_submodules('bruh.engine')
hidden_imports += collect_submodules('bruh.capture')
hidden_imports += collect_submodules('bruh.shell')
hidden_imports += collect_submodules('bruh.presentation')
hidden_imports += collect_submodules('bruh.personality')

# Collect shell scripts as package resources
datas = [
    ('src/bruh/shell/scripts/*', 'bruh/shell/scripts'),
]

a = Analysis(
    ['src/bruh/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['unittest', 'tkinter', 'pydoc'],
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
    name='bruh',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
