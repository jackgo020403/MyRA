# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Research Assistant GUI.
This packages the application into a single executable with all dependencies.
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all necessary data files and submodules
datas = []
datas += collect_data_files('anthropic')
datas += collect_data_files('pydantic')
datas += [('ra_orchestrator/prompts/*.md', 'ra_orchestrator/prompts')]

# Collect all submodules
hiddenimports = []
hiddenimports += collect_submodules('anthropic')
hiddenimports += collect_submodules('pydantic')
hiddenimports += collect_submodules('PyQt6')
hiddenimports += collect_submodules('dotenv')
hiddenimports += collect_submodules('requests')
hiddenimports += collect_submodules('bs4')
hiddenimports += collect_submodules('openpyxl')
hiddenimports += ['ra_orchestrator', 'ra_orchestrator.agents', 'ra_orchestrator.excel']

a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.datas,
    [],
    name='ResearchAssistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file if you have one
)
