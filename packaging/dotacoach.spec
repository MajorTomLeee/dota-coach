# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Dota Coach GUI
# 用法（项目根目录）：
#   uv run pyinstaller packaging/dotacoach.spec --noconfirm

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path.cwd()
SRC = ROOT / "src" / "dotacoach"

# 把 web/ 下的 HTML 资源 + 默认 rules.yaml 一并打包
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
    console=False,  # GUI 模式，无控制台窗口
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=False,
    name="DotaCoach",
)
app = BUNDLE(
    coll,
    name="DotaCoach.app",
    icon=None,
    bundle_identifier="top.bowie.dotacoach",
    info_plist={
        "CFBundleName": "Dota Coach",
        "CFBundleDisplayName": "Dota Coach",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
        "LSUIElement": True,  # 仅托盘，不在 Dock 显示
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "11.0",
    },
)
