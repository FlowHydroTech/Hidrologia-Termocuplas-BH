#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Etapa 3 — Análisis armónico (ciclo diurno 24 h) para cada sensor.
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
from config_05A import ACTIVE_TCS, TC_CONFIG, TC_PERIODS
from vfluxx.harmonic_analysis import fit_harmonic_model


@task(
    name="analisis-armonico-24h",
    description="Ajusta modelo sinusoidal (P=24 h) a los 15 sensores.",
    tags=["armonico", "rio-cuncumen"],
)
def analisis_armonico(df_aligned: pd.DataFrame) -> dict:
    """Ajusta modelo sinusoidal (P=24h) a cada sensor."""
    harmonic_results = {}
    for tc_name in ACTIVE_TCS:
        tc_map = TC_CONFIG[tc_name]
        tc_start = pd.Timestamp(TC_PERIODS[tc_name][0])
        tc_end = pd.Timestamp(TC_PERIODS[tc_name][1])
        mask = (df_aligned["fecha"] >= tc_start) & (df_aligned["fecha"] <= tc_end)
        df_tc = df_aligned[mask].copy()
        t_start = df_tc["fecha"].min()
        t_hours = (df_tc["fecha"] - t_start).dt.total_seconds() / 3600.0
        dias = (tc_end - tc_start).days

        for pos in ["surface", "intermediate", "deep"]:
            col = tc_map[pos]
            if col not in df_tc.columns:
                continue
            series = df_tc[col].values
            valid = ~np.isnan(series)
            if valid.sum() < 48:
                continue
            result = fit_harmonic_model(
                t_hours.values[valid], series[valid], period_hours=24.0
            )
            result["tc_name"] = tc_name
            result["time_hours"] = t_hours.values[valid]
            result["n_days"] = dias
            harmonic_results[col] = result

    n_ok = sum(1 for r in harmonic_results.values() if r["r_squared"] > 0.3)
    print(f"  {len(harmonic_results)} sensores analizados, {n_ok} con R² > 0.30")
    return harmonic_results


if __name__ == "__main__":
    from stage_01_carga import cargar_datos
    from stage_02_alineacion import alinear_datos
    sensors = cargar_datos.fn()
    _, df_aligned, _ = alinear_datos.fn(sensors)
    hr = analisis_armonico.fn(df_aligned)
    print(f"OK — {len(hr)} sensores analizados")
