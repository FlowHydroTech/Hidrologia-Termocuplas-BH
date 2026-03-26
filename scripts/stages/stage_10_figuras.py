#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Etapa 10 — Generación de figuras estáticas (matplotlib).

Reutiliza las funciones de figuras_05A.py, que ya leen IMG_DIR de config_05A.
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import matplotlib
matplotlib.use("Agg")

from prefect import task
from config_05A import IMG_DIR


@task(
    name="generar-figuras-estaticas",
    description="Genera 12 figuras estáticas (PNG/PDF) del análisis Hatch-Amplitude.",
    tags=["figuras", "matplotlib", "rio-cuncumen"],
)
def generar_figuras(
    df_raw, df_aligned, harmonic_results, all_flux_results, flux_ts_results
) -> list[str]:
    """Genera todas las figuras estáticas y retorna lista de archivos creados."""
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    import figuras_05A as fig_mod

    print("  [1/8] Series de temperatura...")
    fig_mod.fig_temperatura(df_raw)

    print("  [2/8] Ajustes armónicos...")
    fig_mod.fig_armonicos(df_aligned, harmonic_results)

    print("  [3/8] Boxplot + scatter...")
    fig_mod.fig_boxplot_scatter(all_flux_results)

    print("  [4/8] Barras HA por TC...")
    fig_mod.fig_barras(all_flux_results)

    print("  [5/8] Forest-plot IC 95%...")
    fig_mod.fig_forest_plot()

    print("  [6/8] Series flujo MATLAB...")
    fig_mod.fig_flux_matlab()

    print("  [7/10] Boxplot publicación...")
    fig_mod.fig_boxplot_pub(flux_ts_results)

    print("  [8/10] Series publicación...")
    fig_mod.fig_series_pub(flux_ts_results)

    print("  [9/10] Series tendencia central (MAD)...")
    fig_mod.fig_series_tendencia_central(flux_ts_results)

    print("  [10/10] Boxplot tendencia central (MAD) + resumen...")
    fig_mod.fig_boxplot_tendencia_central(flux_ts_results)

    created = [str(p) for p in IMG_DIR.glob("*") if p.is_file()]
    print(f"  {len(created)} archivos en {IMG_DIR.relative_to(IMG_DIR.parent.parent.parent)}/")
    return created


if __name__ == "__main__":
    print("Esta etapa requiere datos de etapas previas. Ejecutar vía prefect_pipeline.py")
