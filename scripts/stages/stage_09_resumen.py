#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Etapa 9 — Resumen ejecutivo + IQR de series temporales.
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
from prefect.artifacts import create_markdown_artifact
from config_05A import ACTIVE_TCS, MATLAB_REFERENCE, OUT_DIR, PROCESSED_DIR


@task(
    name="tabla-IQR-hatch-amplitude",
    description="Genera tabla IQR de Hatch-Amplitude desde series temporales.",
    tags=["iqr", "estadistica", "rio-cuncumen"],
)
def calcular_iqr(flux_ts_results: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Tabla IQR de Hatch-Amplitude (series temporales)."""
    iqr_rows = []
    for tc_name in ACTIVE_TCS:
        vals_tc = []
        for pname, dff in flux_ts_results.items():
            if tc_name not in pname:
                continue
            df_ok = dff[dff["quality_flag"] == 0]
            if "flux_hatch_amplitude_mm_day" not in df_ok.columns:
                continue
            v = df_ok["flux_hatch_amplitude_mm_day"].dropna().values
            if len(v) == 0:
                continue
            vals_tc.extend(v.tolist())
            pt = pname.split("_", 1)[1]
            iqr_rows.append({
                "TC": tc_name,
                "Par": pt.replace("_", "→"),
                "n": len(v),
                "Media": round(np.mean(v), 1),
                "Mediana": round(np.median(v), 1),
                "Q1": round(np.percentile(v, 25), 1),
                "Q3": round(np.percentile(v, 75), 1),
                "IQR": round(np.percentile(v, 75) - np.percentile(v, 25), 1),
                "Min": round(np.min(v), 1),
                "Max": round(np.max(v), 1),
            })
        if vals_tc:
            v_all = np.array(vals_tc)
            iqr_rows.append({
                "TC": tc_name, "Par": "TOTAL",
                "n": len(v_all),
                "Media": round(np.mean(v_all), 1),
                "Mediana": round(np.median(v_all), 1),
                "Q1": round(np.percentile(v_all, 25), 1),
                "Q3": round(np.percentile(v_all, 75), 1),
                "IQR": round(np.percentile(v_all, 75) - np.percentile(v_all, 25), 1),
                "Min": round(np.min(v_all), 1),
                "Max": round(np.max(v_all), 1),
            })

    df_iqr = pd.DataFrame(iqr_rows)
    df_iqr.to_csv(OUT_DIR / "tabla_iqr_hatch_amplitude.csv", index=False)
    print(f"  IQR exportado: {len(iqr_rows)} filas")
    return df_iqr


@task(
    name="resumen-ejecutivo-pipeline",
    description="Imprime y registra resumen ejecutivo del análisis Hatch-Amplitude.",
    tags=["resumen", "rio-cuncumen"],
)
def resumen_ejecutivo(
    flujos_promedio_tc: dict,
    ic_rows: list[dict],
    df_uncertainty: pd.DataFrame,
) -> str:
    """Imprime resumen final del análisis."""
    lines = []
    lines.append("=" * 90)
    lines.append(" RESUMEN EJECUTIVO - Pipeline Hatch-Amplitude Rio Cuncumen ".center(90, "="))
    lines.append("=" * 90)

    lines.append("\n* FLUJO PROMEDIO POR TC (Hatch-Amplitude):")
    for tc, vals in flujos_promedio_tc.items():
        d = "Infiltracion" if vals["hatch_mean"] > 0 else "Exfiltracion"
        lines.append(f"  {tc}: {vals['hatch_mean']:>7.1f} +/- {vals['hatch_std']:.1f} mm/d ({d})")

    global_ha = np.mean([v["hatch_mean"] for v in flujos_promedio_tc.values()])
    lines.append(f"\n  PROMEDIO GLOBAL: {global_ha:.1f} mm/d")

    ic_vals = [r["IC_total"] for r in ic_rows]
    lines.append(f"\n* CONFIABILIDAD: IC promedio = {np.mean(ic_vals):.3f}")

    u_vals = df_uncertainty["u_rel (%)"].values
    lines.append(f"* INCERTIDUMBRE: u_rel promedio = +/-{np.mean(u_vals):.1f}%")

    lines.append(f"\n* SALIDAS: {PROCESSED_DIR.relative_to(PROCESSED_DIR.parent.parent.parent)}/")
    lines.append("=" * 90)

    report = "\n".join(lines)
    print(report)

    # --- Artefacto Prefect: resumen Markdown ---
    try:
        md = "# Resumen Ejecutivo — Hatch-Amplitude Río Cuncumén\n\n"
        md += "| TC | Flujo HA (mm/d) | Dirección |\n|---|---|---|\n"
        for tc, vals in flujos_promedio_tc.items():
            d = "↓ Infiltración" if vals["hatch_mean"] > 0 else "↑ Exfiltración"
            md += f"| {tc} | {vals['hatch_mean']:.1f} ± {vals['hatch_std']:.1f} | {d} |\n"
        md += f"\n**Promedio global**: {global_ha:.1f} mm/d\n"
        md += f"\n**IC promedio**: {np.mean(ic_vals):.3f}\n"
        md += f"\n**Incertidumbre relativa promedio**: ±{np.mean(u_vals):.1f}%\n"

        create_markdown_artifact(
            key="resumen-ejecutivo-hatch-amplitude",
            markdown=md,
            description="Resumen ejecutivo del análisis Hatch-Amplitude — Río Cuncumén.",
        )
    except Exception:
        pass

    return report


if __name__ == "__main__":
    print("Esta etapa requiere datos de etapas previas. Ejecutar vía prefect_pipeline.py")
