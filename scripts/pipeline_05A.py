#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pipeline_05A.py — Pipeline completo de procesamiento Hatch-Amplitude.
Río Cuncumén / Silala — 5 Termocuplas (TC1–TC5).

Replica las celdas 1–20 del notebook 05A_datos_terreno.ipynb.
Ejecutar desde la raíz del proyecto:
    python scripts/pipeline_05A.py

Etapas:
  1. Carga de datos Excel (5 TCs)
  2. Alineación temporal (30 min)
  3. Análisis armónico (ciclo 24 h)
  4. Cálculo de flujo (Hatch-Amplitude + McCallum)
  5. Series temporales (ventanas deslizantes 48 h / 12 h)
  6. Métricas de confiabilidad
  7. Propagación de incertidumbre
  8. Exportación (Excel multi-hoja + CSVs)
  9. Resumen ejecutivo

Salidas:
  data/processed/resultados_20260325/resultados/  (datos)
  data/processed/resultados_20260325/figuras/     (figuras)
  data/processed/resultados_20260325/contenido_web/ (HTML)

NOTA: Para ejecución orquestada con Prefect, usar prefect_pipeline.py
"""

import sys
from pathlib import Path

# --- Setup paths ---
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

from config_05A import (
    DATA_DIR, OUT_DIR, IMG_DIR,
    TC_CONFIG, DEPTHS_M, TC_ASSIGNMENT, ACTIVE_TCS,
    THERMAL_PARAMS_LAB, THERMAL_PARAMS_VFLUX, MATLAB_REFERENCE,
    TC_PERIODS, PAIR_MAP, SENSOR_MAPPINGS, UNCERTAINTIES_LAB,
    WINDOW_HOURS, STEP_HOURS,
)
from vfluxx.harmonic_analysis import fit_harmonic_model, analyze_sensor_pair
from vfluxx.vflux_methods import calculate_vflux_all_methods
from vfluxx.io_utils import ibuttons_to_dataframe
from vfluxx.preprocess import align_and_resample
from vfluxx.flux_timeseries import calculate_flux_timeseries


# ══════════════════════════════════════════════════════════════════════════
# 1. CARGA DE DATOS
# ══════════════════════════════════════════════════════════════════════════
def load_sensors():
    """Carga los 15 sensores iButton desde archivos Excel filtrados."""
    sensors = []
    for tc_name, (xlsx_rel, mapping) in SENSOR_MAPPINGS.items():
        tc_df = pd.read_excel(DATA_DIR / xlsx_rel)
        for sid, temp_col, date_col, pn in mapping:
            df_sensor = pd.DataFrame({
                "datetime": pd.to_datetime(tc_df[date_col]),
                "temperature": tc_df[temp_col],
            }).dropna()
            sensors.append({
                "df": df_sensor,
                "sensor_id": sid,
                "part_number": pn,
                "metadata": {"Registration Number": sid},
            })
    sensors = sorted(sensors, key=lambda x: x["sensor_id"])
    print(f"  {len(sensors)} sensores cargados desde {len(SENSOR_MAPPINGS)} TCs")
    return sensors


# ══════════════════════════════════════════════════════════════════════════
# 2. ALINEACIÓN TEMPORAL
# ══════════════════════════════════════════════════════════════════════════
def prepare_data(sensors):
    """Alinea y remuestrea a 30 min."""
    sensor_labels = [f"temp_{i+1}" for i in range(len(sensors))]
    df_raw = ibuttons_to_dataframe(sensors, sensor_labels=sensor_labels)
    df_aligned = align_and_resample(df_raw, freq="30min")
    print(f"  {len(df_aligned)} registros × {len(df_aligned.columns)} columnas")
    return df_raw, df_aligned, sensor_labels


# ══════════════════════════════════════════════════════════════════════════
# 3. ANÁLISIS ARMÓNICO
# ══════════════════════════════════════════════════════════════════════════
def run_harmonic_analysis(df_aligned):
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


# ══════════════════════════════════════════════════════════════════════════
# 4. CÁLCULO DE FLUJO
# ══════════════════════════════════════════════════════════════════════════
def calculate_fluxes(df_aligned, harmonic_results):
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


# ══════════════════════════════════════════════════════════════════════════
# 5. SERIES TEMPORALES (VENTANAS DESLIZANTES)
# ══════════════════════════════════════════════════════════════════════════
def compute_flux_timeseries(df_aligned, df_raw):
    """Calcula series temporales de flujo con ventanas deslizantes."""
    output_ts_dir = OUT_DIR / "series_temporales"
    output_ts_dir.mkdir(parents=True, exist_ok=True)
    output_ts_tc_dir = output_ts_dir / "por_tc"
    output_ts_tc_dir.mkdir(parents=True, exist_ok=True)

    flux_ts_results = {}
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


# ══════════════════════════════════════════════════════════════════════════
# 6. MÉTRICAS DE CONFIABILIDAD
# ══════════════════════════════════════════════════════════════════════════
def compute_reliability(all_flux_results, harmonic_results):
    """Índice de confiabilidad (IC) por par de sensores."""
    WEIGHTS = {
        "R2_sup": 0.25,
        "R2_inf": 0.20,
        "concordancia_HA_MC": 0.25,
        "consistencia_literatura": 0.15,
        "consistencia_fisica": 0.15,
    }
    ic_rows = []
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


# ══════════════════════════════════════════════════════════════════════════
# 7. PROPAGACIÓN DE INCERTIDUMBRE
# ══════════════════════════════════════════════════════════════════════════
def compute_uncertainty(all_flux_results, harmonic_results):
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


# ══════════════════════════════════════════════════════════════════════════
# 8. EXPORTACIÓN
# ══════════════════════════════════════════════════════════════════════════
def export_results(df_results, flujos_promedio_tc, df_iqr, df_ic, df_uncertainty,
                   harmonic_results):
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

    print(f"  Excel: {excel_path.name} (7 hojas)")
    print(f"  CSVs: flujos, confiabilidad, incertidumbre")


# ══════════════════════════════════════════════════════════════════════════
# 9. IQR DE SERIES TEMPORALES
# ══════════════════════════════════════════════════════════════════════════
def compute_iqr(flux_ts_results):
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
        # Resumen TC
        if vals_tc:
            v_all = np.array(vals_tc)
            ref = MATLAB_REFERENCE.get(tc_name, {})
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


# ══════════════════════════════════════════════════════════════════════════
# RESUMEN EJECUTIVO
# ══════════════════════════════════════════════════════════════════════════
def print_summary(flujos_promedio_tc, ic_rows, df_uncertainty):
    """Imprime resumen final del análisis."""
    print("\n" + "═" * 90)
    print(" RESUMEN EJECUTIVO — Pipeline 05A Hatch-Amplitude ".center(90, "═"))
    print("═" * 90)

    print("\n◼ FLUJO PROMEDIO POR TC (Hatch-Amplitude):")
    for tc, vals in flujos_promedio_tc.items():
        d = "↓ Infiltración" if vals["hatch_mean"] > 0 else "↑ Exfiltración"
        print(f"  {tc}: {vals['hatch_mean']:>7.1f} ± {vals['hatch_std']:.1f} mm/d ({d})")

    global_ha = np.mean([v["hatch_mean"] for v in flujos_promedio_tc.values()])
    print(f"\n  PROMEDIO GLOBAL: {global_ha:.1f} mm/d")

    ic_vals = [r["IC_total"] for r in ic_rows]
    print(f"\n◼ CONFIABILIDAD: IC promedio = {np.mean(ic_vals):.3f}")

    u_vals = df_uncertainty["u_rel (%)"].values
    print(f"◼ INCERTIDUMBRE: u_rel promedio = ±{np.mean(u_vals):.1f}%")

    print(f"\n◼ ARCHIVOS:")
    print(f"  {OUT_DIR.relative_to(PROJECT_ROOT)}/")
    print(f"  {IMG_DIR.relative_to(PROJECT_ROOT)}/")
    print("═" * 90)


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    print("═" * 70)
    print(" PIPELINE 05A — HATCH-AMPLITUDE — Río Cuncumén ".center(70, "═"))
    print("═" * 70)

    print("\n[1/8] Cargando datos...")
    sensors = load_sensors()

    print("[2/8] Preparando datos...")
    df_raw, df_aligned, sensor_labels = prepare_data(sensors)

    print("[3/8] Análisis armónico...")
    harmonic_results = run_harmonic_analysis(df_aligned)

    print("[4/8] Cálculo de flujo...")
    all_flux_results, pair_results, df_results, flujos_promedio_tc = calculate_fluxes(
        df_aligned, harmonic_results
    )

    print("[5/8] Series temporales (ventanas deslizantes)...")
    flux_ts_results = compute_flux_timeseries(df_aligned, df_raw)

    print("[6/8] IQR + Confiabilidad...")
    df_iqr = compute_iqr(flux_ts_results)
    df_ic, ic_rows = compute_reliability(all_flux_results, harmonic_results)

    print("[7/8] Propagación de incertidumbre...")
    df_uncertainty = compute_uncertainty(all_flux_results, harmonic_results)

    print("[8/8] Exportando resultados...")
    export_results(df_results, flujos_promedio_tc, df_iqr, df_ic, df_uncertainty,
                   harmonic_results)

    print_summary(flujos_promedio_tc, ic_rows, df_uncertainty)


if __name__ == "__main__":
    main()
