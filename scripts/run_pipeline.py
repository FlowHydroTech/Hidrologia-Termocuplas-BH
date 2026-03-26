#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_pipeline.py — Ejecución directa del pipeline Hatch-Amplitude SIN Prefect.
Río Cuncumén / Silala — 5 Termocuplas (TC1–TC5).

Mismo pipeline de 11 etapas que prefect_pipeline.py, pero ejecutado como
funciones Python puras (sin decoradores @flow/@task).

Ejecutar:
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --skip-figs
    python scripts/run_pipeline.py --skip-html

Salidas:
  data/processed/<run_id>/
  ├── figuras/           PNG, PDF
  ├── resultados/        Excel, CSVs, series_temporales/
  └── contenido_web/     HTML interactivos
"""
import os
import sys
import time
import warnings
from pathlib import Path

# Forzar UTF-8 en consolas Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Silenciar warnings cosméticos de scipy.optimize y prefect artifacts
warnings.filterwarnings("ignore", category=UserWarning, module="prefect.artifacts")
warnings.filterwarnings("ignore", category=FutureWarning, module="prefect")
warnings.filterwarnings("ignore", message=".*Covariance of the parameters.*")

# Deshabilitar el sistema de eventos de Prefect (EventsWorker) para evitar
# que al terminar el proceso emita warnings en stderr.
import logging
for _logger_name in (
    "prefect.events", "prefect.events.utilities",
    "prefect._internal.concurrency", "prefect._internal.concurrency.services",
):
    logging.getLogger(_logger_name).setLevel(logging.CRITICAL)

# Desactivar Prefect event emission completamente (modo standalone)
os.environ["PREFECT_SERVER_ALLOW_EPHEMERAL_MODE"] = "false"

# Parchear funciones de artifacts como no-ops para evitar que Prefect
# intente levantar un servidor efímero al ejecutarlas fuera de un flow.
import prefect.artifacts as _artifacts
_artifacts.create_table_artifact = lambda **kw: None
_artifacts.create_markdown_artifact = lambda **kw: None

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# ── Importar funciones reales (sin decorador Prefect) ──
# Cada stage define una función decorada con @task de Prefect.
# Podemos invocar .fn para obtener la función subyacente sin Prefect,
# o simplemente llamar la función directamente (Prefect ignora @task
# cuando no hay un flow activo y usa el modo síncrono).
from config_05A import PROCESSED_DIR, OUT_DIR, IMG_DIR, WEB_DIR, SERIES_DIR

from stages.stage_01_carga import cargar_datos
from stages.stage_02_alineacion import alinear_datos
from stages.stage_03_armonico import analisis_armonico
from stages.stage_04_flujo import calcular_flujos
from stages.stage_05_series_temporales import calcular_series_temporales
from stages.stage_06_confiabilidad import calcular_confiabilidad
from stages.stage_07_incertidumbre import calcular_incertidumbre
from stages.stage_08_exportacion import exportar_resultados
from stages.stage_09_resumen import calcular_iqr, resumen_ejecutivo
from stages.stage_10_figuras import generar_figuras
from stages.stage_11_paneles import generar_paneles


def run(*, generar_figs: bool = True, generar_html: bool = True) -> None:
    """Ejecuta las 11 etapas secuencialmente sin Prefect."""
    t0 = time.perf_counter()

    # Crear directorios de salida
    for d in [PROCESSED_DIR, OUT_DIR, IMG_DIR, WEB_DIR, SERIES_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(" PIPELINE HATCH-AMPLITUDE - Río Cuncumén (Python) ".center(70, "="))
    print("=" * 70)

    # Acceder a la función subyacente (.fn) para evitar que Prefect
    # intente crear un flow run efímero al llamar un @task fuera de @flow.
    _cargar = cargar_datos.fn
    _alinear = alinear_datos.fn
    _armonico = analisis_armonico.fn
    _flujos = calcular_flujos.fn
    _series = calcular_series_temporales.fn
    _confiab = calcular_confiabilidad.fn
    _incert = calcular_incertidumbre.fn
    _export = exportar_resultados.fn
    _iqr = calcular_iqr.fn
    _resumen = resumen_ejecutivo.fn
    _figuras = generar_figuras.fn
    _paneles = generar_paneles.fn

    # ---------- Etapa 1 ----------
    print("\n[1/11] Cargando datos...")
    sensors = _cargar()

    # ---------- Etapa 2 ----------
    print("[2/11] Alineación temporal...")
    df_raw, df_aligned, sensor_labels = _alinear(sensors)

    # ---------- Etapa 3 ----------
    print("[3/11] Análisis armónico...")
    harmonic_results = _armonico(df_aligned)

    # ---------- Etapa 4 ----------
    print("[4/11] Cálculo de flujo...")
    all_flux_results, pair_results, df_results, flujos_promedio_tc = _flujos(
        df_aligned, harmonic_results
    )

    # ---------- Etapa 5 ----------
    print("[5/11] Series temporales...")
    flux_ts_results = _series(df_aligned, df_raw)

    # ---------- Etapa 6 ----------
    print("[6/11] Confiabilidad...")
    df_ic, ic_rows = _confiab(all_flux_results, harmonic_results)

    # ---------- Etapa 7 ----------
    print("[7/11] Incertidumbre...")
    df_uncertainty = _incert(all_flux_results, harmonic_results)

    # ---------- Etapa 8 ----------
    print("[8/11] Tabla IQR...")
    df_iqr = _iqr(flux_ts_results)

    # ---------- Etapa 9 ----------
    print("[9/11] Exportación...")
    excel_path = _export(
        df_results, flujos_promedio_tc, df_iqr, df_ic, df_uncertainty,
        harmonic_results,
    )

    # ---------- Etapa 10 ----------
    print("[10/11] Resumen ejecutivo...")
    _resumen(flujos_promedio_tc, ic_rows, df_uncertainty)

    # ---------- Etapa 11a ----------
    if generar_figs:
        print("[11a/11] Figuras estáticas...")
        _figuras(df_raw, df_aligned, harmonic_results,
                 all_flux_results, flux_ts_results)

    # ---------- Etapa 11b ----------
    if generar_html:
        print("[11b/11] Paneles HTML...")
        _paneles(flux_ts_results, all_flux_results,
                 flujos_promedio_tc, df_aligned)

    elapsed = time.perf_counter() - t0
    print("\n" + "=" * 70)
    print(f" OK Pipeline completado en {elapsed:.1f}s")
    print(f"    Salidas en {PROCESSED_DIR.relative_to(PROJECT_ROOT)}/")
    print("=" * 70)


if __name__ == "__main__":
    skip_figs = "--skip-figs" in sys.argv
    skip_html = "--skip-html" in sys.argv
    run(generar_figs=not skip_figs, generar_html=not skip_html)
