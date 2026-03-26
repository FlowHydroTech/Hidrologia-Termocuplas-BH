"""
Genera 3 ZIPs autocontenidos para distribuir el pipeline Hatch-Amplitude.

  Modo A: Python puro   (run_pipeline.py, sin Prefect)
  Modo B: Prefect        (prefect_pipeline.py + dashboard)
  Modo C: Docker          (docker compose, sin instalación Python)

Uso:
    python scripts/build_packages.py

Salida:
    dist/
      ModoA_PythonPuro_YYYYMMDD.zip
      ModoB_Prefect_YYYYMMDD.zip
      ModoC_Docker_YYYYMMDD.zip
"""

import zipfile
import os
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
TAG = date.today().strftime("%Y%m%d")

# ── Archivos comunes a los 3 modos ──────────────────────────────────────
_COMMON_DIRS = [
    "src/vfluxx",
    "scripts/stages",
    "data/Datos Termocuplas 25-02-2026",
    "data/Resultados_IDIEM",
    "tests",
]

_COMMON_SCRIPTS = [
    "scripts/config_05A.py",
    "scripts/pipeline_05A.py",
    "scripts/figuras_05A.py",
    "scripts/paneles_05A.py",
]

_COMMON_ROOT_FILES = [
    "pyproject.toml",
    "requirements.txt",
    "README.md",
    "GUIA_RAPIDA.md",
    "GUIA_RAPIDA.txt",
    "GLOSARIO_TECNICO.md",
]

# ── Exclusiones ──────────────────────────────────────────────────────────
_SKIP_PATTERNS = {
    "__pycache__",
    ".egg-info",
    ".pyc",
    "cotizaciones y EDP",
}


def _should_skip(path_str: str) -> bool:
    for pat in _SKIP_PATTERNS:
        if pat in path_str:
            return True
    return False


def _add_dir(zf: zipfile.ZipFile, src_dir: Path, arc_prefix: str, base: str):
    """Agrega un directorio completo al ZIP."""
    full = base / src_dir if not src_dir.is_absolute() else src_dir
    if not full.exists():
        print(f"  WARN: {src_dir} no existe, saltando")
        return
    for root_path, _dirs, files in os.walk(full):
        for f in files:
            fp = Path(root_path) / f
            rel = fp.relative_to(base)
            if _should_skip(str(rel)):
                continue
            arcname = f"{arc_prefix}/{rel}"
            zf.write(fp, arcname)


def _add_file(zf: zipfile.ZipFile, src: Path, arc_prefix: str, base: str):
    full = base / src if not src.is_absolute() else src
    if not full.exists():
        print(f"  WARN: {src} no existe, saltando")
        return
    rel = full.relative_to(base)
    zf.write(full, f"{arc_prefix}/{rel}")


def _add_common(zf: zipfile.ZipFile, prefix: str):
    """Agrega archivos comunes al ZIP."""
    for d in _COMMON_DIRS:
        _add_dir(zf, Path(d), prefix, ROOT)
    for f in _COMMON_SCRIPTS:
        _add_file(zf, Path(f), prefix, ROOT)
    for f in _COMMON_ROOT_FILES:
        _add_file(zf, Path(f), prefix, ROOT)


# ═════════════════════════════════════════════════════════════════════════
# LEEME.txt para cada modo
# ═════════════════════════════════════════════════════════════════════════

LEEME_A = """\
================================================================================
  MODO A — PYTHON PURO (sin servidor, sin Docker)
  Pipeline Hatch-Amplitude — Rio Cuncumen / Silala
================================================================================

  REQUISITOS:
    - Python 3.12 o superior
    - Conexion a internet (primera vez, para instalar dependencias)

  PASOS:
  ------

  1. Descomprimir este ZIP en una carpeta de trabajo.

  2. Abrir una terminal (PowerShell o CMD) en la carpeta descomprimida.

  3. Crear entorno virtual e instalar dependencias:

     OPCION con uv (recomendado, mas rapido):
       pip install uv
       uv sync

     OPCION con pip (clasico):
       python -m venv .venv
       .venv\\Scripts\\activate        (Windows)
       pip install -r requirements.txt
       pip install -e .

  4. Ejecutar el pipeline completo:

       python scripts/run_pipeline.py

     Esto ejecuta las 11 etapas automaticamente:
       Carga -> Alineacion -> Armonico -> Flujo -> Series ->
       Confiabilidad -> Incertidumbre -> IQR -> Exportacion ->
       Resumen -> Figuras + Paneles HTML

  5. Resultados en:
       data/processed/resultados_20260325/
         resultados/    (Excel, CSVs, estadisticas)
         figuras/       (PNG + PDF, 300 DPI)
         contenido_web/ (8 HTML interactivos)

  NOTA WINDOWS: Si aparecen caracteres extranos en consola:
       $env:PYTHONIOENCODING = "utf-8"
       python scripts/run_pipeline.py

  TESTS:
       python -m pytest tests/ -v

================================================================================
"""

LEEME_B = """\
================================================================================
  MODO B — PREFECT + DASHBOARD INTERACTIVO
  Pipeline Hatch-Amplitude — Rio Cuncumen / Silala
================================================================================

  REQUISITOS:
    - Python 3.12 o superior
    - Conexion a internet (primera vez, para instalar dependencias)
    - 2 terminales abiertas

  PASOS:
  ------

  1. Descomprimir este ZIP en una carpeta de trabajo.

  2. Crear entorno virtual e instalar dependencias:

     OPCION con uv (recomendado):
       pip install uv
       uv sync

     OPCION con pip:
       python -m venv .venv
       .venv\\Scripts\\activate
       pip install -r requirements.txt
       pip install -e .

  3. TERMINAL 1 — Iniciar servidor Prefect:

       prefect server start

     Esperar a que aparezca: "Prefect server started!"
     Dashboard disponible en: http://localhost:4200

  4. TERMINAL 2 — Ejecutar el pipeline:

       python scripts/prefect_pipeline.py

     Flags opcionales:
       --no-figs     Omitir figuras estaticas
       --no-html     Omitir paneles HTML
       --no-server   No verificar servidor Prefect

  5. Monitorear ejecucion en el dashboard:
       http://localhost:4200

  6. Resultados en:
       data/processed/resultados_20260325/
         resultados/    (Excel, CSVs, estadisticas)
         figuras/       (PNG + PDF, 300 DPI)
         contenido_web/ (8 HTML interactivos)

  DETENER SERVIDOR:
     Ctrl+C en Terminal 1

  NOTA WINDOWS: Si aparecen caracteres extranos:
     $env:PYTHONIOENCODING = "utf-8"

================================================================================
"""

LEEME_C = """\
================================================================================
  MODO C — DOCKER (contenedores, sin instalar Python)
  Pipeline Hatch-Amplitude — Rio Cuncumen / Silala
================================================================================

  REQUISITOS:
    - Docker Desktop instalado y ejecutandose
      Descargar: https://www.docker.com/products/docker-desktop/

  PASOS:
  ------

  1. Descomprimir este ZIP en una carpeta de trabajo.

  2. Abrir una terminal en la carpeta descomprimida.

  3. Elegir un modo de ejecucion:

     a) COMPLETO (Pipeline + Dashboard Prefect):

          docker compose up

        Dashboard: http://localhost:4200
        Al terminar: Ctrl+C  o  docker compose down

     b) SOLO PIPELINE Python puro (sin Prefect, mas rapido):

          docker compose run --rm standalone

     c) SOLO DASHBOARD Prefect (sin ejecutar pipeline):

          docker compose up prefect

  4. Resultados en:
       data/processed/resultados_20260325/
         resultados/    (Excel, CSVs, estadisticas)
         figuras/       (PNG + PDF, 300 DPI)
         contenido_web/ (8 HTML interactivos)

     (La carpeta data/ esta montada como volumen,
      los resultados quedan en el host directamente.)

  RECONSTRUIR IMAGEN (si cambian scripts o dependencias):
     docker compose build

  LIMPIAR CONTENEDORES:
     docker compose down --rmi local

================================================================================
"""


def build_zip(name: str, extra_files: list, extra_dirs: list, leeme: str):
    """Construye un ZIP autocontenido."""
    prefix = f"HatchAmplitude_{name}"
    zip_name = f"{name}_{TAG}.zip"
    zip_path = DIST / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # LEEME.txt
        zf.writestr(f"{prefix}/LEEME.txt", leeme)

        # Archivos comunes
        _add_common(zf, prefix)

        # Archivos específicos del modo
        for f in extra_files:
            _add_file(zf, Path(f), prefix, ROOT)

        # Directorios específicos
        for d in extra_dirs:
            _add_dir(zf, Path(d), prefix, ROOT)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    n_files = len(zipfile.ZipFile(zip_path).namelist())
    print(f"  {zip_name:45s} {size_mb:6.1f} MB  ({n_files} archivos)")
    return zip_path


def main():
    DIST.mkdir(exist_ok=True)
    print(f"Generando paquetes en {DIST}/\n")

    # ── Modo A: Python puro ──
    build_zip(
        "ModoA_PythonPuro",
        extra_files=["scripts/run_pipeline.py"],
        extra_dirs=[],
        leeme=LEEME_A,
    )

    # ── Modo B: Prefect ──
    build_zip(
        "ModoB_Prefect",
        extra_files=[
            "scripts/run_pipeline.py",
            "scripts/prefect_pipeline.py",
        ],
        extra_dirs=[],
        leeme=LEEME_B,
    )

    # ── Modo C: Docker ──
    build_zip(
        "ModoC_Docker",
        extra_files=[
            "scripts/run_pipeline.py",
            "scripts/prefect_pipeline.py",
            "Dockerfile",
            "docker-compose.yml",
        ],
        extra_dirs=[],
        leeme=LEEME_C,
    )

    print(f"\nListo. Copiar contenido de {DIST}/ al directorio de respaldo.")


if __name__ == "__main__":
    main()
