#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Etapa 7 — Propagación cuadrática de incertidumbre (props IDIEM).
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
from config_05A import ACTIVE_TCS, TC_CONFIG, PAIR_MAP, UNCERTAINTIES_LAB


@task(
    name="propagacion-incertidumbre-IDIEM",
    description="Propagación cuadrática de incertidumbre basada en parámetros IDIEM.",
    tags=["incertidumbre", "IDIEM", "rio-cuncumen"],
)
def calcular_incertidumbre(
    all_flux_results: dict, harmonic_results: dict
) -> pd.DataFrame:
    """Propagación cuadrática de incertidumbre (props IDIEM)."""
    rows = []
    for tc_name in ACTIVE_TCS:
        tc_map = TC_CONFIG[tc_name]
        for pair_key, (pos_sh, pos_dp) in PAIR_MAP.items():
            label = f"{tc_name}: {pair_key.replace('_', '-')}"
            if label not in all_flux_results:
                continue
            shallow = tc_map[pos_sh]
            deep_s = tc_map[pos_dp]
            ha = all_flux_results[label]["flux_mm_day"].get("hatch_amplitude", np.nan)
            if np.isnan(ha) or ha == 0:
                continue

            r2_s = harmonic_results.get(shallow, {}).get("r_squared", 0.5)
            r2_d = harmonic_results.get(deep_s, {}).get("r_squared", 0.5)
            r2_avg = (r2_s + r2_d) / 2
            u_harm = 0.05 if r2_avg > 0.8 else (0.10 if r2_avg > 0.5 else 0.20)

            u_total = np.sqrt(
                UNCERTAINTIES_LAB["alpha_e"] ** 2
                + UNCERTAINTIES_LAB["dz"] ** 2
                + u_harm ** 2
            )
            u_abs = abs(ha) * u_total
            rows.append({
                "TC": tc_name,
                "Par": pair_key.replace("_", "→"),
                "Flujo HA (mm/d)": round(ha, 1),
                "u_rel (%)": round(u_total * 100, 1),
                "u_abs (mm/d)": round(u_abs, 1),
                "IC 95% bajo": round(ha - 1.96 * u_abs, 1),
                "IC 95% alto": round(ha + 1.96 * u_abs, 1),
                "u_armónico (%)": round(u_harm * 100, 1),
            })

    df_u = pd.DataFrame(rows)
    print(f"  u_rel promedio: ±{df_u['u_rel (%)'].mean():.1f}%")
    return df_u


if __name__ == "__main__":
    from stage_01_carga import cargar_datos
    from stage_02_alineacion import alinear_datos
    from stage_03_armonico import analisis_armonico
    from stage_04_flujo import calcular_flujos
    sensors = cargar_datos.fn()
    _, df_al, _ = alinear_datos.fn(sensors)
    hr = analisis_armonico.fn(df_al)
    afr, _, _, _ = calcular_flujos.fn(df_al, hr)
    df_u = calcular_incertidumbre.fn(afr, hr)
    print(f"OK — u_rel promedio: ±{df_u['u_rel (%)'].mean():.1f}%")
