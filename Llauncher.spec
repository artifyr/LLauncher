# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

base_dir = os.path.dirname(os.path.abspath(SPEC))

datas = [
    (os.path.join(base_dir, 'assets'), 'assets'),
    (os.path.join(base_dir, 'profiles.json'), '.'),
]
binaries = []
hiddenimports = ['PIL', 'PIL._tkinter_finder']

tmp_ctk = collect_all('customtkinter')
datas += tmp_ctk[0]; binaries += tmp_ctk[1]; hiddenimports += tmp_ctk[2]

tmp_pws = collect_all('pywinstyles')
datas += tmp_pws[0]; binaries += tmp_pws[1]; hiddenimports += tmp_pws[2]

a = Analysis(
    [os.path.join(base_dir, 'launcher.py')],
    pathex=[base_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'pandas', 'torch', 'IPython', 'notebook'],
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
    name='LLauncher',
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
    icon=[os.path.join(base_dir, 'assets', 'llauncher.ico')],
)
