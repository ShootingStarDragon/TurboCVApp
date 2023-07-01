# -*- mode: python ; coding: utf-8 -*-
from kivy_deps import sdl2, glew

block_cipher = None

basedir = os.path.join(os.sep, os.getcwd().split(os.path.sep)[0] + os.sep, *os.getcwd().split(os.path.sep)[:-1]) + os.path.sep
print("file location?", basedir)

a = Analysis(
    ['example_sepiafilter.py'],
    pathex=[],
    binaries=[],
    datas=[(basedir + "FastCVApp.py", "."), (basedir + "FCVAutils.py", "."), (basedir + "examples\\creativecommonsmedia\\", "examples\\creativecommonsmedia"), (basedir + "fonts", "fonts"), (basedir + "logviewer", "logviewer")],
    hiddenimports=['kivy', 'blosc2', 'kivy.modules.inspector'],
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
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    name='SepiaFilter',
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
)
