#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Etapa 5 — Series temporales de flujo (ventanas deslizantes 48 h / 12 h).
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd
from prefect import task
from config_05A import (
    ACTIVE_TCS, TC_CONFIG, TC_PERIODS, DEPTHS_M,
    THERMAL_PARAMS_LAB, THERMAL_PARAMS_VFLUX, PAIR_MAP,
    SERIES_DIR, WINDOW_HOURS, STEP_HOURS,
)
from vfluxx.flux_timeseries import calculate_flux_timeseries


@task(
    name="series-temporales-flujo-48h",
    description="Calcula series temporales de flujo con ventanas deslizantes 48 h / 12 h.",
    tags=["series-temporales", "rio-cuncumen"],
)
def calcular_series_temporales(
    df_aligned: pd.DataFrame, df_raw: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """Calcula series temporales de flujo con ventanas deslizantes."""
    output_ts_dir = SERIES_DIR
    output_ts_dir.mkdir(parents=True, exist_ok=True)
    output_ts_tc_dir = output_ts_dir / "por_tc"
    output_ts_tc_dir.mkdir(parents=True, exist_ok=True)

    flux_ts_results: dict[str, pd.DataFrame] = {}
    for tc_name in ACTIVE_TCS:
        tp = THERMAL_PARAMS_LAB[tc_name]
        beta_tc = THERMAL_PARAMS_VFLUX[tc_name]["beta_d50"]
        config = TC_CONFIG[tc_name]
        tp_calc = {
            "lambda_sediment": tp["lambda_sediment"],
            "C_sediment": tp["C_sediment"],
            "C_water": tp["C_water"],
            "omega": tp["omega"],
            "beta": beta_tc,
        }
        for pair_type, (pos_sh, pos_dp) in PAIR_MAP.items():
            name = f"{tc_name}_{pair_type}"
            shallow_col = config[pos_sh]
            deep_col = config[pos_dp]
            df_flux = calculate_flux_timeseries(
                time_array=df_aligned["fecha"],
                temp_shallow=df_aligned[shallow_col].values,
                temp_deep=df_aligned[deep_col].values,
                depth_shallow=DEPTHS_M[shallow_col],
                depth_deep=DEPTHS_M[deep_col],
                thermal_params=tp_calc,
                window_hours=WINDOW_HOURS,
                step_hours=STEP_HOURS,
            )
            if df_flux is not None and len(df_flux) > 0:
                flux_ts_results[name] = df_flux
                df_flux.to_csv(output_ts_dir / f"flujo_temporal_{name}.csv", index=False)

    # Agrupar por TC
    for tc_name in ACTIVE_TCS:
        tc_dfs = []
        for pname, dff in flux_ts_results.items():
            if tc_name in pname:
                df_c = dff.copy()
                df_c["par"] = pname.split("_", 1)[1]
                tc_dfs.append(df_c)
        if tc_dfs:
            pd.concat(tc_dfs, ignore_index=True).to_csv(
                output_ts_tc_dir / f"series_flujo_{tc_name}.csv", index=False
            )

    # Combinada
    all_dfs = []
    for pname, dff in flux_ts_results.items():
        df_c = dff.copy()
        df_c["TC"] = pname.split("_")[0]
        df_c["par"] = pname.split("_", 1)[1]
        all_dfs.append(df_c)
    if all_dfs:
        pd.concat(all_dfs, ignore_index=True).to_csv(
            output_ts_dir / "series_flujo_todas_TC.csv", index=False
        )

    # Series de temperatura por TC
    for tc_name in ACTIVE_TCS:
        tc_map = TC_CONFIG[tc_name]
        tc_start = pd.Timestamp(TC_PERIODS[tc_name][0])
        tc_end = pd.Timestamp(TC_PERIODS[tc_name][1])
        mask = (df_raw["fecha"] >= tc_start) & (df_raw["fecha"] <= tc_end)
        cols = ["fecha"] + [tc_map[p] for p in ["surface", "intermediate", "deep"]]
        df_t = df_raw.loc[mask, cols].copy()
        rename = {tc_map["surface"]: f"{tc_name}_sup",
                  tc_map["intermediate"]: f"{tc_name}_int",
                  tc_map["deep"]: f"{tc_name}_inf"}
        df_t.rename(columns=rename, inplace=True)
        df_t.to_csv(output_ts_tc_dir / f"temperatura_{tc_name}.csv", index=False)

    print(f"  {len(flux_ts_results)} series temporales de flujo calculadas")
    return flux_ts_results


if __name__ == "__main__":
    from stage_01_carga import cargar_datos
    from stage_02_alineacion import alinear_datos
    sensors = cargar_datos.fn()
    df_raw, df_aligned, _ = alinear_datos.fn(sensors)
    fts = calcular_series_temporales.fn(df_aligned, df_raw)
    print(f"OK — {len(fts)} series")
