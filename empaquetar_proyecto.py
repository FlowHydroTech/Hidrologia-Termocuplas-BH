#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Empaqueta los archivos necesarios del proyecto Hidrología-Termocuplas-BH
en un ZIP listo para entrega al cliente.

Uso:
    python empaquetar_proyecto.py

Genera:
    Hidrologia-Termocuplas-BH_entrega.zip
"""

import zipfile
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent
ZIP_NAME = f"Hidrologia-Termocuplas-BH_entrega_{date.today():%Y%m%d}.zip"
ZIP_PATH = ROOT / ZIP_NAME

# ── Archivos raíz ──────────────────────────────────────────────────
ROOT_FILES = [
    "pyproject.toml",
    "uv.lock",
    "requirements.txt",
    "README.md",
    "GUIA_RAPIDA.md",
    "GUIA_RAPIDA.txt",
]

# ── Paquete fuente (src/vfluxx) ───────────────────────────────────
SRC_PACKAGE = "src/vfluxx"

# ── Scripts ejecutables ───────────────────────────────────────────
SCRIPTS = [
    "scripts/config_05A.py",
    "scripts/pipeline_05A.py",
    "scripts/figuras_05A.py",
    "scripts/paneles_05A.py",
]

# ── Notebook principal ────────────────────────────────────────────
NOTEBOOKS = [
    "notebooks/05A_datos_terreno.ipynb",
]

# ── Tests ─────────────────────────────────────────────────────────
TESTS = [
    "tests/test_flux.py",
    "tests/test_harmonics.py",
    "tests/test_preprocess.py",
]

# ── Datos (solo los Excel filtrados por TC + IDIEM) ───────────────
DATA_FILES = [
    "data/Datos Termocuplas 25-02-2026/tc1/datos_filtrados_tc1.xlsx",
    "data/Datos Termocuplas 25-02-2026/tc2/datos_filtrados_tc2.xlsx",
    "data/Datos Termocuplas 25-02-2026/tc3/datos_filtrados_tc3.xlsx",
    "data/Datos Termocuplas 25-02-2026/tc4/datos_filtrados_tc4.xlsx",
    "data/Datos Termocuplas 25-02-2026/tc5/datos_filtrados_tc5.xlsx",
    "data/Resultados_IDIEM/Resultados IDIEM.xlsx",
]


def collect_files():
    """Recolecta lista de (ruta_absoluta, ruta_en_zip)."""
    files = []

    # Archivos raíz
    for f in ROOT_FILES:
        p = ROOT / f
        if p.exists():
            files.append((p, f))

    # Paquete src/vfluxx (todos los .py, excluir __pycache__)
    pkg = ROOT / SRC_PACKAGE
    for p in sorted(pkg.rglob("*.py")):
        if "__pycache__" in str(p):
            continue
        rel = p.relative_to(ROOT).as_posix()
        files.append((p, rel))

    # Scripts
    for f in SCRIPTS:
        p = ROOT / f
        if p.exists():
            files.append((p, f))

    # Notebooks
    for f in NOTEBOOKS:
        p = ROOT / f
        if p.exists():
            files.append((p, f))

    # Tests
    for f in TESTS:
        p = ROOT / f
        if p.exists():
            files.append((p, f))

    # Datos
    for f in DATA_FILES:
        p = ROOT / f
        if p.exists():
            files.append((p, f))

    return files


def main():
    files = collect_files()

    # Validar que todos los archivos críticos existen
    missing = [f for (p, f) in files if not p.exists()]
    if missing:
        print("ADVERTENCIA: archivos faltantes:")
        for m in missing:
            print(f"  - {m}")

    # Crear ZIP
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for abs_path, arc_name in files:
            zf.write(abs_path, arcname=arc_name)
            print(f"  + {arc_name}")

    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"\n{'='*60}")
    print(f"ZIP generado: {ZIP_NAME}")
    print(f"Archivos: {len(files)}")
    print(f"Tamaño: {size_mb:.1f} MB")
    print(f"Ubicación: {ZIP_PATH}")
    print(f"{'='*60}")

    # Instrucciones para el cliente
    print("""
INSTRUCCIONES PARA EL CLIENTE:
  1. Descomprimir el ZIP
  2. Instalar uv (si no lo tiene):
       pip install uv
  3. Instalar dependencias + entorno virtual:
       cd Hidrologia-Termocuplas-BH
       uv sync
  4. Ejecutar pipeline:
       cd scripts
       uv run python pipeline_05A.py
  5. Generar figuras:
       uv run python figuras_05A.py
  6. Generar paneles interactivos:
       uv run python paneles_05A.py
  7. O abrir el notebook:
       uv run jupyter notebook notebooks/05A_datos_terreno.ipynb
""")


if __name__ == "__main__":
    main()
