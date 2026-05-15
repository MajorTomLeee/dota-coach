# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Dota Coach GUI - Windows
# Usage: uv run pyinstaller packaging/dotacoach-win.spec --noconfirm

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path.cwd()
SRC = ROOT / "src" / "dotacoach"

datas = [
    (str(SRC / "gui" / "web" / "setup.html"), "dotacoach/gui/web"),
    (str(SRC / "gui" / "web" / "viewer.html"), "dotacoach/gui/web"),
    (str(SRC / "db" / "schema.sql"), "dotacoach/db"),
    (str(ROOT / "config" / "rules.yaml"), "config"),
]
datas += collect_data_files("edge_tts")
datas += collect_data_files("certifi")

hiddenimports = (
    collect_submodules("dotacoach")
    + collect_submodules("anthropic")
    + collect_submodules("clr_loader")  # pythonnet for pywebview backend
    + ["pkg_resources.py2_warn"]
)

a = Analysis(
    [str(SRC / "gui" / "tray.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "test", "unittest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="DotaCoach",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI 模式
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=False,
    name="DotaCoach",
)
