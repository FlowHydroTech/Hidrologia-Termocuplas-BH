#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Etapa 4 — Cálculo de flujo Hatch-Amplitude + McCallum para los 15 pares.
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
from config_05A import (
    ACTIVE_TCS, TC_CONFIG, TC_PERIODS, DEPTHS_M,
    THERMAL_PARAMS_LAB, THERMAL_PARAMS_VFLUX, PAIR_MAP,
)
from vfluxx.harmonic_analysis import analyze_sensor_pair
from vfluxx.vflux_methods import calculate_vflux_all_methods


@task(
    name="calculo-flujo-hatch-mccallum",
    description="Calcula flujo vertical (Hatch-Amplitude + McCallum) para 15 pares de sensores.",
    tags=["flujo", "hatch", "mccallum", "rio-cuncumen"],
)
def calcular_flujos(
    df_aligned: pd.DataFrame, harmonic_results: dict
) -> tuple[dict, dict, pd.DataFrame, dict]:
    """Calcula flujo Hatch-Amplitude + McCallum para los 15 pares."""
    all_flux_results = {}
    pair_results = {}
    rows = []

    for tc_name in ACTIVE_TCS:
        tc_map = TC_CONFIG[tc_name]
        tp = THERMAL_PARAMS_LAB[tc_name]
        beta_tc = THERMAL_PARAMS_VFLUX[tc_name]["beta_d50"]
        tc_start = pd.Timestamp(TC_PERIODS[tc_name][0])
        tc_end = pd.Timestamp(TC_PERIODS[tc_name][1])
        mask = (df_aligned["fecha"] >= tc_start) & (df_aligned["fecha"] <= tc_end)
        df_tc = df_aligned[mask]
        t_start = df_tc["fecha"].min()

        for pair_key, (pos_sh, pos_dp) in PAIR_MAP.items():
            s_shallow = tc_map[pos_sh]
            s_deep = tc_map[pos_dp]
            dz = abs(DEPTHS_M[s_deep] - DEPTHS_M[s_shallow])
            label = f"{tc_name}: {pair_key.replace('_', '-')}"

            valid = df_tc[s_shallow].notna() & df_tc[s_deep].notna()
            if valid.sum() < 48:
                continue
            t_valid = ((df_tc["fecha"] - t_start).dt.total_seconds() / 3600.0).values[valid]
            t1 = df_tc[s_shallow].values[valid]
            t2 = df_tc[s_deep].values[valid]

            params = analyze_sensor_pair(t_valid, t1, t2, period_hours=24.0)
            pair_results[label] = {"params": params, "dz": dz}

            flux_result = calculate_vflux_all_methods(
                amplitude_shallow=params["A_shallow"],
                amplitude_deep=params["A_deep"],
                phase_shallow=params["phi_shallow"],
                phase_deep=params["phi_deep"],
                depth_difference=dz,
                thermal_conductivity=tp["lambda_sediment"],
                heat_capacity_sediment=tp["C_sediment"],
                heat_capacity_water=tp["C_water"],
                angular_frequency=tp["omega"],
                beta=beta_tc,
            )
            all_flux_results[label] = flux_result

            ha = flux_result["flux_mm_day"].get("hatch_amplitude", np.nan)
            mc = flux_result["flux_mm_day"].get("mccallum", np.nan)
            rows.append({
                "TC": tc_name, "Par": pair_key.replace("_", "→"),
                "HA_mm_d": round(ha, 1) if not np.isnan(ha) else np.nan,
                "MC_mm_d": round(mc, 1) if not np.isnan(mc) else np.nan,
                "Ar": round(params["amplitude_ratio"], 4),
                "dz_m": dz,
            })

    df_results = pd.DataFrame(rows)

    # Flujo promedio por TC
    flujos_promedio_tc = {}
    for tc_name in ACTIVE_TCS:
        df_tc = df_results[df_results["TC"] == tc_name]
        ha_vals = df_tc["HA_mm_d"].dropna().values
        mc_vals = df_tc["MC_mm_d"].dropna().values
        flujos_promedio_tc[tc_name] = {
            "hatch_mean": np.mean(ha_vals) if len(ha_vals) > 0 else np.nan,
            "hatch_std": np.std(ha_vals, ddof=1) if len(ha_vals) > 1 else 0,
            "mc_mean": np.mean(mc_vals) if len(mc_vals) > 0 else np.nan,
            "mc_std": np.std(mc_vals, ddof=1) if len(mc_vals) > 1 else 0,
        }

    print(f"  {len(all_flux_results)} pares calculados")
    return all_flux_results, pair_results, df_results, flujos_promedio_tc


if __name__ == "__main__":
    from stage_01_carga import cargar_datos
    from stage_02_alineacion import alinear_datos
    from stage_03_armonico import analisis_armonico
    sensors = cargar_datos.fn()
    _, df_aligned, _ = alinear_datos.fn(sensors)
    hr = analisis_armonico.fn(df_aligned)
    afr, pr, dfr, fpt = calcular_flujos.fn(df_aligned, hr)
    print(f"OK — {len(afr)} pares calculados")
