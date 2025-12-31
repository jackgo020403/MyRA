# -*- mode: python ; coding: utf-8 -*-
"""
LIGHTWEIGHT PyInstaller spec file for Research Assistant GUI.
Only includes necessary dependencies - excludes heavy ML libraries.
"""

import sys
from PyInstaller.utils.hooks import collect_data_files

# Collect only necessary data files
datas = []
datas += [('ra_orchestrator/prompts/*.md', 'ra_orchestrator/prompts')]

# Only include what we actually use
hiddenimports = [
    'anthropic',
    'pydantic',
    'PyQt6',
    'dotenv',
    'requests',
    'bs4',
    'openpyxl',
    'ra_orchestrator',
    'ra_orchestrator.agents',
    'ra_orchestrator.excel',
]

# EXCLUDE heavy libraries we don't use
excludes = [
    'torch',
    'tensorflow',
    'scipy',
    'numpy',
    'pandas',
    'matplotlib',
    'sklearn',
    'IPython',
    'jupyter',
    'notebook',
    'sympy',
    'nltk',
    'transformers',
    'librosa',
    'soundfile',
    'torchaudio',
    'h5py',
    'PIL',
    'pytest',
    'sphinx',
    'babel',
    'jinja2',
    'zmq',
]

a = Analysis(
    ['gui_app_simple.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add .ico for Windows, .icns for Mac if you have one
)

# For macOS, create .app bundle
import sys
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='ResearchAssistant.app',
        icon=None,  # Add .icns file path here if you have an icon
        bundle_identifier='com.yourname.researchassistant',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',
        },
    )
