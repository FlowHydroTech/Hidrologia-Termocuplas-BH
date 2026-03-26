#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Etapa 11 — Generación de paneles interactivos HTML (Plotly + Folium).

Reutiliza las funciones de paneles_05A.py pero redirige salidas
HTML a contenido_web/ en lugar de figuras/.
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from prefect import task
from config_05A import WEB_DIR


@task(
    name="generar-paneles-html-interactivos",
    description="Genera paneles HTML interactivos (selectores TC, perfil río, mapa SIG, mapa MAD).",
    tags=["paneles", "html", "plotly", "folium", "rio-cuncumen"],
)
def generar_paneles(
    flux_ts_results: dict,
    all_flux_results: dict,
    flujos_promedio_tc: dict,
    df_aligned,
) -> list[str]:
    """Genera paneles HTML interactivos y retorna lista de archivos."""
    WEB_DIR.mkdir(parents=True, exist_ok=True)

    # Importar paneles y redirigir salida a WEB_DIR
    import paneles_05A as pan_mod

    # Parchar temporalmente IMG_DIR del módulo para que escriba en WEB_DIR
    import config_05A
    original_img_dir = config_05A.IMG_DIR
    config_05A.IMG_DIR = WEB_DIR
    pan_mod.IMG_DIR = WEB_DIR

    try:
        all_data = pan_mod._load_flux_ts_csvs()

        print("  [1/4] Selectores interactivos por TC...")
        pan_mod.gen_selectors(all_data)

        print("  [2/4] Perfil del río...")
        pan_mod.gen_perfil_rio(flujos_promedio_tc)

        print("  [3/4] Panel SIG integrado...")
        pan_mod.gen_panel_sig(df_aligned, flux_ts_results, all_flux_results)

        print("  [4/4] Panel SIG tendencia central MAD...")
        pan_mod.gen_panel_tendencia_central_mad(df_aligned, flux_ts_results)
    finally:
        # Restaurar
        config_05A.IMG_DIR = original_img_dir
        pan_mod.IMG_DIR = original_img_dir

    created = [str(p) for p in WEB_DIR.glob("*.html")]
    print(f"  {len(created)} archivos HTML en {WEB_DIR.relative_to(WEB_DIR.parent.parent.parent)}/")
    return created


if __name__ == "__main__":
    print("Esta etapa requiere datos de etapas previas. Ejecutar vía prefect_pipeline.py")
