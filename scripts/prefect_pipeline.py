#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
prefect_pipeline.py — Orquestador Prefect del pipeline Hatch-Amplitude.
Río Cuncumén / Silala — 5 Termocuplas (TC1–TC5).

Ejecutar:
    # 1) Iniciar servidor Prefect (dashboard en http://localhost:4200)
    prefect server start

    # 2) En otra terminal, ejecutar pipeline
    python scripts/prefect_pipeline.py

    # Modo rápido sin dashboard (efímero)
    python scripts/prefect_pipeline.py --no-server

Etapas:
   1. Carga de datos Excel (5 TCs)
   2. Alineación temporal (30 min)
   3. Análisis armónico (ciclo 24 h)
   4. Cálculo de flujo (Hatch-Amplitude + McCallum)
   5. Series temporales (ventanas deslizantes 48 h / 12 h)
   6. Métricas de confiabilidad
   7. Propagación de incertidumbre
   8. Exportación (Excel multi-hoja + CSVs)
   9. IQR + Resumen ejecutivo
  10. Figuras estáticas (matplotlib)
  11. Paneles interactivos (Plotly + Folium)

Salidas:
  data/processed/<run_id>/
  ├── figuras/           PNG, PDF
  ├── resultados/        Excel, CSVs, series_temporales/
  └── contenido_web/     HTML interactivos
"""
import os
import sys
import logging
import urllib.request
from pathlib import Path

# Forzar UTF-8 en stdout/stderr para consolas Windows (cp1252)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Silenciar errores cosméticos de EventsWorker en modo efímero ──
logging.getLogger("prefect.events.utilities").setLevel(logging.CRITICAL)
logging.getLogger("prefect._internal.concurrency").setLevel(logging.CRITICAL)

# ── Conexión al servidor Prefect ──
# Si ya hay PREFECT_API_URL definida (Docker, CI), respetarla.
# Si no, intentar conectar al servidor local; si no responde, modo efímero.
PREFECT_SERVER_URL = "http://127.0.0.1:4200/api"

if not os.environ.get("PREFECT_API_URL"):
    if "--no-server" in sys.argv:
        # Forzar modo efímero explícitamente
        os.environ["PREFECT_SERVER_ALLOW_EPHEMERAL_MODE"] = "true"
        os.environ["PREFECT_API_URL"] = ""
        print("[config] Modo efímero (--no-server)")
    else:
        # Intentar conectar al servidor local
        try:
            req = urllib.request.Request(
                f"{PREFECT_SERVER_URL}/health", method="GET"
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    os.environ["PREFECT_API_URL"] = PREFECT_SERVER_URL
                    print(f"[config] Conectado a servidor Prefect: {PREFECT_SERVER_URL}")
                else:
                    raise ConnectionError()
        except Exception:
            os.environ["PREFECT_SERVER_ALLOW_EPHEMERAL_MODE"] = "true"
            os.environ["PREFECT_API_URL"] = ""
            print("[config] Servidor no disponible → modo efímero")
            print("         Iniciar con: prefect server start")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from prefect import flow
from config_05A import PROCESSED_DIR, OUT_DIR, IMG_DIR, WEB_DIR, SERIES_DIR

# Importar tasks desde cada etapa
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


@flow(
    name="hatch-amplitude-rio-cuncumen",
    description=(
        "Pipeline completo Hatch-Amplitude para estimación de flujo vertical "
        "en lechos de río — Río Cuncumén / Silala. "
        "5 termocuplas, 15 sensores iButton, métodos Hatch-Amplitude y McCallum."
    ),
    version="1.0.0",
    flow_run_name="hatch-amplitude-{date}",
)
def pipeline_hatch_amplitude(
    generar_figs: bool = True,
    generar_html: bool = True,
    date: str = "20260325",
):
    """
    Pipeline completo Hatch-Amplitude con 11 etapas orquestadas por Prefect.

    Parámetros:
        generar_figs : bool  — Generar figuras estáticas (matplotlib)
        generar_html : bool  — Generar paneles interactivos (Plotly + Folium)
        date : str           — Identificador de la corrida (se usa en flow_run_name)
    """
    # Crear directorios de salida
    for d in [PROCESSED_DIR, OUT_DIR, IMG_DIR, WEB_DIR, SERIES_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(" PIPELINE HATCH-AMPLITUDE - Rio Cuncumen (Prefect) ".center(70, "="))
    print("=" * 70)

    # ---------- Etapa 1: Carga ----------
    print("\n[1/11] Cargando datos...")
    sensors = cargar_datos()

    # ---------- Etapa 2: Alineación ----------
    print("[2/11] Alineación temporal...")
    df_raw, df_aligned, sensor_labels = alinear_datos(sensors)

    # ---------- Etapa 3: Armónico ----------
    print("[3/11] Análisis armónico...")
    harmonic_results = analisis_armonico(df_aligned)

    # ---------- Etapa 4: Flujo ----------
    print("[4/11] Cálculo de flujo...")
    all_flux_results, pair_results, df_results, flujos_promedio_tc = calcular_flujos(
        df_aligned, harmonic_results
    )

    # ---------- Etapa 5: Series temporales ----------
    print("[5/11] Series temporales...")
    flux_ts_results = calcular_series_temporales(df_aligned, df_raw)

    # ---------- Etapa 6: Confiabilidad ----------
    print("[6/11] Confiabilidad...")
    df_ic, ic_rows = calcular_confiabilidad(all_flux_results, harmonic_results)

    # ---------- Etapa 7: Incertidumbre ----------
    print("[7/11] Incertidumbre...")
    df_uncertainty = calcular_incertidumbre(all_flux_results, harmonic_results)

    # ---------- Etapa 9a: IQR (necesario para exportación) ----------
    print("[8/11] Tabla IQR...")
    df_iqr = calcular_iqr(flux_ts_results)

    # ---------- Etapa 8: Exportación ----------
    print("[9/11] Exportación...")
    excel_path = exportar_resultados(
        df_results, flujos_promedio_tc, df_iqr, df_ic, df_uncertainty,
        harmonic_results,
    )

    # ---------- Etapa 9b: Resumen ----------
    print("[10/11] Resumen ejecutivo...")
    resumen_ejecutivo(flujos_promedio_tc, ic_rows, df_uncertainty)

    # ---------- Etapa 10: Figuras ----------
    if generar_figs:
        print("[11a/11] Figuras estáticas...")
        generar_figuras(df_raw, df_aligned, harmonic_results,
                        all_flux_results, flux_ts_results)

    # ---------- Etapa 11: Paneles ----------
    if generar_html:
        print("[11b/11] Paneles HTML...")
        generar_paneles(flux_ts_results, all_flux_results,
                        flujos_promedio_tc, df_aligned)

    print("\n" + "=" * 70)
    print(f" OK Pipeline completado - Salidas en {PROCESSED_DIR.relative_to(PROJECT_ROOT)}/")
    print("=" * 70)


if __name__ == "__main__":
    from datetime import date as _date
    pipeline_hatch_amplitude(date=_date.today().strftime("%Y%m%d"))
