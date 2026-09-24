# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).resolve()
VERSION = (ROOT / "version.txt").read_text(encoding="utf-8").strip() or "1.0.0"

# Calculator modules are imported lazily at runtime. Explicit hidden imports
# keep PyInstaller packaging deterministic without collecting every dependency.
hiddenimports = [
    "calculators.afr_lambda",
    "calculators.stoich",
    "calculators.ve",
    "calculators.injector_flow",
    "calculators.throttle",
    "calculators.runner",
    "calculators.power_torque",
    "calculators.turbo",
    "calculators.header",
    "ecu_tools.engine_dyno",
]

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "assets"), "assets"),
        (str(ROOT / "version.txt"), "."),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f"ASLAN-TUNER-v{VERSION}",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(ROOT / "assets" / "aslan_tuner.ico"),
)
