#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Etapa 6 — Métricas de confiabilidad (IC) por par de sensores.
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
from config_05A import ACTIVE_TCS, TC_CONFIG, PAIR_MAP


@task(
    name="metricas-confiabilidad-IC",
    description="Calcula el Índice de Confiabilidad (IC) ponderado para cada par de sensores.",
    tags=["confiabilidad", "rio-cuncumen"],
)
def calcular_confiabilidad(
    all_flux_results: dict, harmonic_results: dict
) -> tuple[pd.DataFrame, list[dict]]:
    """Índice de confiabilidad (IC) por par de sensores."""
    WEIGHTS = {
        "R2_sup": 0.25,
        "R2_inf": 0.20,
        "concordancia_HA_MC": 0.25,
        "consistencia_literatura": 0.15,
        "consistencia_fisica": 0.15,
    }
    ic_rows: list[dict] = []
    for tc_name in ACTIVE_TCS:
        tc_map = TC_CONFIG[tc_name]
        for pair_key, (pos_sh, pos_dp) in PAIR_MAP.items():
            label = f"{tc_name}: {pair_key.replace('_', '-')}"
            if label not in all_flux_results:
                continue
            shallow = tc_map[pos_sh]
            deep_s = tc_map[pos_dp]
            r2_s = harmonic_results.get(shallow, {}).get("r_squared", 0)
            r2_d = harmonic_results.get(deep_s, {}).get("r_squared", 0)

            ha = all_flux_results[label]["flux_mm_day"].get("hatch_amplitude", np.nan)
            mc = all_flux_results[label]["flux_mm_day"].get("mccallum", np.nan)

            # Concordancia HA-MC
            if not np.isnan(ha) and not np.isnan(mc) and max(abs(ha), abs(mc)) > 0:
                concord = 1 - abs(ha - mc) / max(abs(ha), abs(mc))
            else:
                concord = 0
            concord = max(0, min(1, concord))

            # Consistencia con literatura (10–600 mm/d para ríos aluviales)
            ic_lit = 1.0 if 10 <= abs(ha) <= 600 else (0.5 if abs(ha) <= 2000 else 0.1) if not np.isnan(ha) else 0

            # Consistencia física (amplitud disminuye con profundidad)
            amp_s = harmonic_results.get(shallow, {}).get("amplitude", 0)
            amp_d = harmonic_results.get(deep_s, {}).get("amplitude", 0)
            ic_phys = 1.0 if amp_s > amp_d else 0.5

            ic_total = (
                WEIGHTS["R2_sup"] * r2_s
                + WEIGHTS["R2_inf"] * r2_d
                + WEIGHTS["concordancia_HA_MC"] * concord
                + WEIGHTS["consistencia_literatura"] * ic_lit
                + WEIGHTS["consistencia_fisica"] * ic_phys
            )
            ic_rows.append({
                "TC": tc_name,
                "Par": pair_key.replace("_", "→"),
                "IC_total": round(ic_total, 3),
                "R2_sup": round(r2_s, 3),
                "R2_inf": round(r2_d, 3),
                "Concord_HA_MC": round(concord, 3),
                "IC_lit": round(ic_lit, 1),
                "IC_physics": round(ic_phys, 1),
                "HA_mm_d": round(ha, 1) if not np.isnan(ha) else np.nan,
                "MC_mm_d": round(mc, 1) if not np.isnan(mc) else np.nan,
            })

    df_ic = pd.DataFrame(ic_rows)
    print(f"  IC promedio: {df_ic['IC_total'].mean():.3f}")
    return df_ic, ic_rows


if __name__ == "__main__":
    from stage_01_carga import cargar_datos
    from stage_02_alineacion import alinear_datos
    from stage_03_armonico import analisis_armonico
    from stage_04_flujo import calcular_flujos
    sensors = cargar_datos.fn()
    _, df_al, _ = alinear_datos.fn(sensors)
    hr = analisis_armonico.fn(df_al)
    afr, _, _, _ = calcular_flujos.fn(df_al, hr)
    df_ic, _ = calcular_confiabilidad.fn(afr, hr)
    print(f"OK — IC promedio: {df_ic['IC_total'].mean():.3f}")
