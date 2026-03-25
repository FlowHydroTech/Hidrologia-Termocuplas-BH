#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Etapa 8 — Exportación (Excel multi-hoja + CSVs individuales).
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import numpy as np
import pandas as pd
from prefect import task
from prefect.artifacts import create_table_artifact
from config_05A import (
    ACTIVE_TCS, TC_CONFIG, TC_ASSIGNMENT, DEPTHS_M,
    THERMAL_PARAMS_LAB, OUT_DIR,
)


@task(
    name="exportacion-excel-csv",
    description="Exporta resultados a Excel multi-hoja (7 hojas) y CSVs individuales.",
    tags=["exportacion", "rio-cuncumen"],
)
def exportar_resultados(
    df_results: pd.DataFrame,
    flujos_promedio_tc: dict,
    df_iqr: pd.DataFrame | None,
    df_ic: pd.DataFrame,
    df_uncertainty: pd.DataFrame,
    harmonic_results: dict,
) -> Path:
    """Exporta Excel multi-hoja + CSVs individuales."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    excel_path = OUT_DIR / "resultados_05A_hatch_amplitude.xlsx"

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df_results.to_excel(writer, sheet_name="Flujos_HA_McCallum", index=False)

        tc_summary = []
        for tc_name, vals in flujos_promedio_tc.items():
            tp = THERMAL_PARAMS_LAB[tc_name]
            tc_summary.append({
                "TC": tc_name,
                "Hatch_Amp_medio_mm_d": round(vals["hatch_mean"], 2),
                "Hatch_Amp_std_mm_d": round(vals["hatch_std"], 2),
                "McCallum_medio_mm_d": round(vals["mc_mean"], 2),
                "McCallum_std_mm_d": round(vals["mc_std"], 2),
                "lambda_W_mK": tp["lambda_sediment"],
                "C_sed_MJ_m3K": tp["C_sediment"] / 1e6,
                "alpha_m2_s": tp["alpha_e"],
                "K_v_m_d": tp["K_v"],
                "USCS": tp["USCS"],
            })
        pd.DataFrame(tc_summary).to_excel(writer, sheet_name="Flujo_Promedio_TC", index=False)

        if df_iqr is not None:
            df_iqr.to_excel(writer, sheet_name="IQR_Hatch_Amplitude", index=False)
        df_ic.to_excel(writer, sheet_name="Confiabilidad", index=False)
        df_uncertainty.to_excel(writer, sheet_name="Incertidumbre", index=False)

        harm_data = []
        for col, r in harmonic_results.items():
            harm_data.append({
                "sensor": col,
                "TC": TC_ASSIGNMENT[col],
                "profundidad_m": DEPTHS_M[col],
                "amplitud_C": round(r["amplitude"], 4),
                "fase_rad": round(r["phase"], 4),
                "R2": round(r["r_squared"], 4),
                "n_dias": r.get("n_days", 0),
            })
        pd.DataFrame(harm_data).to_excel(writer, sheet_name="Analisis_Armonico", index=False)

        idiem_data = []
        for tc_name, tp in THERMAL_PARAMS_LAB.items():
            idiem_data.append({
                "TC": tc_name,
                "lambda_W_mK": tp["lambda_sediment"],
                "C_sed_MJ_m3K": tp["C_sediment"] / 1e6,
                "alpha_e_m2_s": tp["alpha_e"],
                "C_water_MJ_m3K": tp["C_water"] / 1e6,
                "K_v_m_d": tp["K_v"],
                "density_dry_g_cm3": tp["density_dry"],
                "USCS": tp["USCS"],
            })
        pd.DataFrame(idiem_data).to_excel(writer, sheet_name="Params_IDIEM", index=False)

    # CSVs
    df_results.to_csv(OUT_DIR / "flujos_hatch_mccallum.csv", index=False)
    df_ic.to_csv(OUT_DIR / "confiabilidad_hatch_mccallum.csv", index=False)
    df_uncertainty.to_csv(OUT_DIR / "incertidumbre_hatch.csv", index=False)

    # --- Artefacto Prefect: tabla resumen de flujos ---
    try:
        tc_table = []
        for tc_name, vals in flujos_promedio_tc.items():
            tc_table.append({
                "TC": tc_name,
                "Hatch (mm/d)": f"{vals['hatch_mean']:.1f} ± {vals['hatch_std']:.1f}",
                "McCallum (mm/d)": f"{vals['mc_mean']:.1f} ± {vals['mc_std']:.1f}",
            })
        create_table_artifact(
            key="flujos-promedio-por-tc",
            table=tc_table,
            description="Flujo promedio Hatch-Amplitude y McCallum por termocupla.",
        )
    except Exception:
        pass  # Si no hay contexto Prefect activo, ignorar

    print(f"  Excel: {excel_path.name} (7 hojas)")
    print(f"  CSVs: flujos, confiabilidad, incertidumbre")
    return excel_path


if __name__ == "__main__":
    print("Esta etapa requiere datos de etapas previas. Ejecutar vía prefect_pipeline.py")
