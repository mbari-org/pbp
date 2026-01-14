# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building standalone mbari-pbp distribution.

Usage:
    poetry run pyinstaller pbp.spec

This creates a directory bundle (--onedir) with faster startup than --onefile.
The dist/pbp/ directory contains the executable and all dependencies.
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all submodules for packages that use dynamic imports
hiddenimports = [
    'pbp.hmb_gen.main_hmb_generator',
    'pbp.cloud.main_cloud',
    'pbp.hmb_plot.main_plot',
    'pbp.meta_gen.main_meta_generator',
]

# Add PyPAM and its dependencies
hiddenimports += collect_submodules('pypam')
hiddenimports += collect_submodules('soundfile')
hiddenimports += collect_submodules('h5netcdf')
hiddenimports += collect_submodules('netCDF4')
hiddenimports += collect_submodules('scipy')
hiddenimports += collect_submodules('numpy')

# Collect data files for packages that need them
datas = []
datas += collect_data_files('soundfile')
datas += collect_data_files('h5netcdf')
datas += collect_data_files('pypam')

a = Analysis(
    ['pbp/main_cli.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test and development packages to reduce size
        'pytest',
        'ty',
        'ruff',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # Changed: Create --onedir bundle
    name='pbp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pbp',
)
