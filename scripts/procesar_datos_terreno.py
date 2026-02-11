#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
PROCESAMIENTO AUTOMATIZADO DE DATOS DE TERRENO -- VFLUX2 Python
===============================================================================

Script profesional para el procesamiento batch de datos iButton de termocuplas
desplegadas en lechos de ríos. Implementa el pipeline completo VFLUX2:

    1. Carga de datos CSV iButton (OneWireViewer)
    2. Mapeo automático de sensores por sensor_id
    3. Control de calidad y alineación temporal
    4. Análisis armónico (ciclo diario 24h)
    5. Cálculo de flujo vertical (5 métodos analíticos)
    6. Generación de visualizaciones tipo SIG + MATLAB VFLUX2
    7. Exportación CSV / Excel con resumen ejecutivo

Uso:
    python scripts/procesar_datos_terreno.py
    python scripts/procesar_datos_terreno.py --data-dir data/raw/Datos_Terreno
    python scripts/procesar_datos_terreno.py --output-dir resultados/campaña_02

Autor: Proyecto Hidrología-Termocuplas-BH
Fecha: Febrero 2026
===============================================================================
"""

import argparse
import sys
import warnings
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator

warnings.filterwarnings("ignore", category=RuntimeWarning)

# ============================================================================
# PATH SETUP
# ============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from vfluxx.io_utils import load_all_ibuttons, ibuttons_to_dataframe
from vfluxx.preprocess import align_and_resample
from vfluxx.harmonic_analysis import fit_harmonic_model, analyze_sensor_pair
from vfluxx.vflux_methods import calculate_vflux_all_methods


# ============================================================================
# CONFIGURACION MAESTRA
# ============================================================================
SENSOR_CONFIG = {
    "TC1": {
        "surface":      {"sensor_id": "A400000082BAF041", "depth_m": 0.00},
        "intermediate": {"sensor_id": "7D000000828FA841", "depth_m": 0.28},
        "deep":         {"sensor_id": "5900000082B86A41", "depth_m": 0.56},
    },
    "TC3": {
        "surface":      {"sensor_id": "F60000008290D841", "depth_m": 0.00},
        "intermediate": {"sensor_id": "2D00000082925E41", "depth_m": 0.20},
        "deep":         {"sensor_id": "B3000000828F2741", "depth_m": 0.40},
    },
    "TC5": {
        "surface":      {"sensor_id": "3800000082952A41", "depth_m": 0.00},
        "intermediate": {"sensor_id": "B000000082987741", "depth_m": 0.28},
        "deep":         {"sensor_id": "2800000082978041", "depth_m": 0.56},
    },
}

STATION_COORDS_UTM = {
    "TC1": {"easting": 347285, "northing": 6473381},
    "TC2": {"easting": 347440, "northing": 6473566},
    "TC3": {"easting": 347087, "northing": 6472284},
    "TC4": {"easting": 347113, "northing": 6472121},
    "TC5": {"easting": 346618, "northing": 6471135},
}

THERMAL_PARAMS = {
    "lambda_sediment": 1.8,
    "C_sediment": 2.8e6,
    "C_water": 4.18e6,
    "omega": 2 * np.pi / 86400,
}

CUTOFF_START = pd.Timestamp("2025-12-21")
CUTOFF_END = pd.Timestamp("2026-01-22 12:00:00")

POSITION_LABELS = {"surface": "Superficie", "intermediate": "Intermedio", "deep": "Inferior"}
POSITION_SHORT = {"surface": "sup", "intermediate": "int", "deep": "inf"}

METHODS = ["mccallum", "hatch_amplitude", "hatch_phase", "keery", "luce"]
METHOD_NAMES = ["McCallum (2012)", "Hatch-Amplitud", "Hatch-Fase", "Keery (2007)", "Luce (2013)"]

# Paleta profesional
TC_PALETTE = {
    "TC1": ["#1f77b4", "#ff7f0e", "#2ca02c"],
    "TC3": ["#e377c2", "#7f7f7f", "#bcbd22"],
    "TC5": ["#d62728", "#9467bd", "#8c564b"],
}
TC_COLORS_MATLAB = {"surface": "#1f77b4", "intermediate": "#ff7f0e", "deep": "#2ca02c"}
POS_LABELS_PLOT = {"surface": "S. superior", "intermediate": "S. intermedio", "deep": "S. inferior"}


# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================
def setup_matplotlib():
    """Estilo publicación para todas las figuras."""
    plt.rcParams.update({
        "figure.figsize": (14, 6),
        "figure.dpi": 150,
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "legend.fontsize": 10,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.grid": False,
        "savefig.bbox": "tight",
        "savefig.dpi": 150,
    })


def resolve_sensors(sensors):
    """Resuelve el mapeo sensor_id -> temp_N y construye las estructuras dinámicas."""
    id_to_label = {s["sensor_id"]: f"temp_{i+1}" for i, s in enumerate(sensors)}
    sensor_labels = [f"temp_{i+1}" for i in range(len(sensors))]

    tc_configs = {}
    depths_m = {}
    tc_assignment = {}

    for tc_name, tc_positions in SENSOR_CONFIG.items():
        tc_map = {}
        for pos, info in tc_positions.items():
            label = id_to_label.get(info["sensor_id"])
            if label is None:
                print(f"  [AVISO] Sensor {info['sensor_id']} no encontrado para {tc_name}/{pos}")
                continue
            tc_map[pos] = label
            depths_m[label] = info["depth_m"]
            tc_assignment[label] = tc_name
        tc_configs[tc_name] = tc_map

    tc_list = sorted(tc_configs.keys())

    # Colores por sensor y por par
    sensor_colors = {}
    tc_pair_colors = {}
    for tc_name in tc_list:
        tc_map = tc_configs[tc_name]
        palette = TC_PALETTE.get(tc_name, ["#17becf", "#aec7e8", "#98df8a"])
        for i, pos in enumerate(["surface", "intermediate", "deep"]):
            if pos in tc_map:
                sensor_colors[tc_map[pos]] = palette[i]
        tc_pair_colors[f"{tc_name}: sup-int"] = palette[0]
        tc_pair_colors[f"{tc_name}: int-inf"] = palette[1]
        tc_pair_colors[f"{tc_name}: sup-inf"] = palette[2]

    return {
        "sensor_labels": sensor_labels,
        "tc_configs": tc_configs,
        "depths_m": depths_m,
        "tc_assignment": tc_assignment,
        "tc_list": tc_list,
        "sensor_colors": sensor_colors,
        "tc_pair_colors": tc_pair_colors,
    }


def run_harmonic_analysis(df_work, time_hours, sensor_labels, tc_assignment, depths_m):
    """Análisis armónico de ciclo diario para cada sensor."""
    harmonic_results = {}
    for col in sensor_labels:
        if col not in tc_assignment:
            continue
        series = df_work[col].values
        valid = ~np.isnan(series)
        if valid.sum() < 48:
            continue
        result = fit_harmonic_model(time_hours[valid], series[valid], period_hours=24.0)
        harmonic_results[col] = result
    return harmonic_results


def build_pairs(tc_list, tc_configs):
    """Construye todos los pares de sensores para análisis."""
    pairs = []
    for tc_name in tc_list:
        tc_map = tc_configs[tc_name]
        if "surface" in tc_map and "intermediate" in tc_map:
            pairs.append((tc_map["surface"], tc_map["intermediate"], f"{tc_name}: sup-int"))
        if "intermediate" in tc_map and "deep" in tc_map:
            pairs.append((tc_map["intermediate"], tc_map["deep"], f"{tc_name}: int-inf"))
        if "surface" in tc_map and "deep" in tc_map:
            pairs.append((tc_map["surface"], tc_map["deep"], f"{tc_name}: sup-inf"))
    return pairs


def run_pair_analysis(pairs, df_work, time_hours, depths_m, harmonic_results):
    """Analiza cada par de sensores."""
    pair_results = {}
    for s_shallow, s_deep, pair_label in pairs:
        mask = df_work[s_shallow].notna() & df_work[s_deep].notna()
        if mask.sum() < 48:
            continue
        t_valid = time_hours[mask]
        t1 = df_work[s_shallow].values[mask]
        t2 = df_work[s_deep].values[mask]
        params = analyze_sensor_pair(t_valid, t1, t2, period_hours=24.0)
        dz = abs(depths_m[s_deep] - depths_m[s_shallow])
        pair_results[pair_label] = {
            "params": params, "dz": dz,
            "s_shallow": s_shallow, "s_deep": s_deep,
        }
    return pair_results


def calculate_all_fluxes(pair_results):
    """Calcula flujos para cada par con los 5 métodos."""
    all_flux_results = {}
    for pair_name, pair_info in pair_results.items():
        params = pair_info["params"]
        dz = pair_info["dz"]
        flux_result = calculate_vflux_all_methods(
            amplitude_shallow=params["A_shallow"],
            amplitude_deep=params["A_deep"],
            phase_shallow=params["phi_shallow"],
            phase_deep=params["phi_deep"],
            depth_difference=dz,
            thermal_conductivity=THERMAL_PARAMS["lambda_sediment"],
            heat_capacity_sediment=THERMAL_PARAMS["C_sediment"],
            heat_capacity_water=THERMAL_PARAMS["C_water"],
            angular_frequency=THERMAL_PARAMS["omega"],
        )
        all_flux_results[pair_name] = flux_result
    return all_flux_results


# ============================================================================
# VISUALIZACIONES
# ============================================================================
def plot_series_overview(df_aligned, ctx, img_dir):
    """Fig 1: Vista general de todos los sensores (2 paneles)."""
    mask = (df_aligned["fecha"] >= CUTOFF_START) & (df_aligned["fecha"] <= CUTOFF_END)
    df_plot = df_aligned[mask].copy()
    tc_list = ctx["tc_list"]
    tc_configs = ctx["tc_configs"]
    depths_m = ctx["depths_m"]
    sensor_colors = ctx["sensor_colors"]
    linestyles = ["-", "--", "-.", ":"]

    fig, axes = plt.subplots(2, 1, figsize=(16, 10), sharex=True,
                             gridspec_kw={"height_ratios": [3, 1.5]})

    for tc_idx, tc_name in enumerate(tc_list):
        tc_map = tc_configs[tc_name]
        ls = linestyles[tc_idx % len(linestyles)]
        for pos in ["surface", "intermediate", "deep"]:
            if pos not in tc_map:
                continue
            col = tc_map[pos]
            depth_cm = depths_m[col] * 100
            d = df_plot.dropna(subset=[col])
            axes[0].plot(d["fecha"], d[col], color=sensor_colors[col], alpha=0.9,
                         linewidth=0.8, linestyle=ls,
                         label=f"{tc_name} {POSITION_SHORT[pos]} ({depth_cm:.0f} cm)")

    n_s = sum(len(tc_configs[tc]) for tc in tc_list)
    axes[0].set_ylabel("Temperatura (°C)")
    axes[0].set_title(f"Series de Temperatura — {n_s} sensores iButton ({len(tc_list)} TC)", fontweight="bold")
    axes[0].legend(loc="upper right", fontsize=7, ncol=min(len(tc_list), 3))
    for spine in axes[0].spines.values():
        spine.set_visible(True)

    dt_colors = plt.cm.tab10(np.linspace(0, 1, max(len(tc_list), 3)))
    for tc_idx, tc_name in enumerate(tc_list):
        tc_map = tc_configs[tc_name]
        if "surface" not in tc_map or "deep" not in tc_map:
            continue
        s_sup, s_deep = tc_map["surface"], tc_map["deep"]
        valid = df_plot[[s_sup, s_deep]].dropna()
        diff = valid[s_sup] - valid[s_deep]
        fechas = df_plot.loc[valid.index, "fecha"]
        dz_cm = abs(depths_m[s_deep] - depths_m[s_sup]) * 100
        axes[1].plot(fechas, diff, color=dt_colors[tc_idx], alpha=0.9, linewidth=0.8,
                     label=f"{tc_name}: ΔT(0-{dz_cm:.0f}cm)")

    axes[1].set_ylabel("ΔT (°C)")
    axes[1].set_xlabel("Fecha")
    axes[1].set_title("Diferencia de temperatura superficie - profundo", fontweight="bold")
    axes[1].legend(fontsize=9)
    axes[1].axhline(y=0, color="k", linestyle="--", linewidth=0.5)
    for spine in axes[1].spines.values():
        spine.set_visible(True)

    plt.tight_layout()
    path = img_dir / "01_series_temperatura_general.png"
    plt.savefig(str(path))
    plt.close()
    return path


def plot_series_per_tc(df_raw, ctx, img_dir):
    """Fig 2: Series por termocupla — estilo MATLAB VFLUX2."""
    tc_list = ctx["tc_list"]
    tc_configs = ctx["tc_configs"]
    depths_m = ctx["depths_m"]
    paths = []

    for tc_name in tc_list:
        tc_map = tc_configs[tc_name]
        plt.rcdefaults()
        fig, ax = plt.subplots(figsize=(14, 5), facecolor="white")
        ax.set_facecolor("white")

        for pos in ["surface", "intermediate", "deep"]:
            if pos not in tc_map:
                continue
            label = tc_map[pos]
            mask = (df_raw["fecha"] >= CUTOFF_START) & (df_raw["fecha"] <= CUTOFF_END)
            df_p = df_raw[mask].dropna(subset=[label])
            depth = depths_m[label]
            ax.plot(df_p["fecha"], df_p[label], color=TC_COLORS_MATLAB[pos],
                    linewidth=1.0, label=f"{POS_LABELS_PLOT[pos]} ({depth:.2f} mbnt)")

        ax.set_ylabel("Temperatura [°C]", fontsize=12)
        ax.set_title(f"Termocupla {tc_name} — Estilo MATLAB VFLUX2", fontweight="bold")
        ax.legend(loc="upper center", ncol=3, fontsize=11, frameon=False, bbox_to_anchor=(0.5, 1.12))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m %H:%M"))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right", fontsize=9)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(1.0)
        ax.tick_params(direction="in", top=True, right=True)
        ax.grid(False)

        plt.tight_layout()
        path = img_dir / f"02_serie_{tc_name.lower()}_matlab.png"
        plt.savefig(str(path), facecolor="white")
        plt.close()
        paths.append(path)

    # Combinado
    setup_matplotlib()
    n_tc = len(tc_list)
    fig, axes_tc = plt.subplots(n_tc, 1, figsize=(14, 4 * n_tc + 2), facecolor="white")
    if n_tc == 1:
        axes_tc = [axes_tc]

    for i, tc_name in enumerate(tc_list):
        ax = axes_tc[i]
        ax.set_facecolor("white")
        tc_map = tc_configs[tc_name]
        for pos in ["surface", "intermediate", "deep"]:
            if pos not in tc_map:
                continue
            label = tc_map[pos]
            mask = (df_raw["fecha"] >= CUTOFF_START) & (df_raw["fecha"] <= CUTOFF_END)
            df_p = df_raw[mask].dropna(subset=[label])
            depth = depths_m[label]
            ax.plot(df_p["fecha"], df_p[label], color=TC_COLORS_MATLAB[pos],
                    linewidth=1.0, label=f"{POS_LABELS_PLOT[pos]} ({depth:.2f} mbnt)")
        ax.set_ylabel("T [°C]")
        ax.set_title(f"Termocupla {tc_name}", fontsize=13, fontweight="bold")
        ax.legend(loc="upper center", ncol=3, fontsize=10, frameon=False, bbox_to_anchor=(0.5, 1.10))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m %H:%M"))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right", fontsize=9)
        for spine in ax.spines.values():
            spine.set_visible(True)
        ax.tick_params(direction="in", top=True, right=True)
        ax.grid(False)

    plt.tight_layout()
    path = img_dir / "02_series_todas_tc_matlab.png"
    plt.savefig(str(path), facecolor="white")
    plt.close()
    paths.append(path)
    return paths


def plot_harmonic_fits(df_work, time_hours, harmonic_results, ctx, img_dir):
    """Fig 3: Ajustes armónicos por TC (grilla NxTC x 3)."""
    tc_list = ctx["tc_list"]
    tc_configs = ctx["tc_configs"]
    depths_m = ctx["depths_m"]
    n_tc = len(tc_list)

    fig, axes = plt.subplots(n_tc, 3, figsize=(18, 5 * n_tc))
    if n_tc == 1:
        axes = axes.reshape(1, -1)

    for row_idx, tc_name in enumerate(tc_list):
        tc_map = tc_configs[tc_name]
        for col_idx, pos in enumerate(["surface", "intermediate", "deep"]):
            ax = axes[row_idx][col_idx]
            if pos not in tc_map or tc_map[pos] not in harmonic_results:
                ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", transform=ax.transAxes)
                ax.set_title(f"{tc_name} — {POSITION_LABELS[pos]}", fontsize=10)
                continue
            col = tc_map[pos]
            result = harmonic_results[col]
            series = df_work[col].values
            max_pts = min(len(time_hours), 48 * 7)
            t_plot = time_hours[:max_pts]
            s_plot = series[:max_pts]
            f_plot = result["fitted"][:max_pts]
            ax.plot(t_plot / 24, s_plot, ".", color="#aaaaaa", alpha=0.4, markersize=2, label="Datos")
            ax.plot(t_plot / 24, f_plot, "-", color="#d62728", linewidth=1.5,
                    label=f"Ajuste (R²={result['r_squared']:.3f})")
            depth_cm = depths_m[col] * 100
            ax.set_title(f"{tc_name} — {POSITION_LABELS[pos]} ({depth_cm:.0f} cm)\nA = {result['amplitude']:.3f}°C",
                         fontsize=10)
            ax.set_xlabel("Días" if row_idx == n_tc - 1 else "")
            ax.set_ylabel("T (°C)" if col_idx == 0 else "")
            ax.legend(fontsize=7, loc="upper right")
            for spine in ax.spines.values():
                spine.set_visible(True)

    plt.suptitle(f"Ajustes Armónicos del Ciclo Diario (24 h) — {n_tc} Termocuplas",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    path = img_dir / "03_ajustes_armonicos.png"
    plt.savefig(str(path))
    plt.close()
    return path


def plot_flux_bars(all_flux_results, ctx, img_dir):
    """Fig 4: Flujos verticales por par y método (barras agrupadas)."""
    tc_list = ctx["tc_list"]
    method_colors = {"mccallum": "#2c3e50", "hatch_amplitude": "#e74c3c",
                     "hatch_phase": "#3498db", "keery": "#27ae60", "luce": "#f39c12"}
    n_tc = len(tc_list)
    fig, axes = plt.subplots(1, n_tc, figsize=(7 * n_tc, 6), sharey=True)
    if n_tc == 1:
        axes = [axes]

    for ax_idx, tc_name in enumerate(tc_list):
        ax = axes[ax_idx]
        tc_pairs = {k: v for k, v in all_flux_results.items() if tc_name in k}
        pair_names = list(tc_pairs.keys())
        x = np.arange(len(pair_names))
        width = 0.15
        for i, (method, name) in enumerate(zip(METHODS, METHOD_NAMES)):
            vals = [tc_pairs[p]["flux_mm_day"].get(method, 0) for p in pair_names]
            offset = (i - 2) * width
            ax.bar(x + offset, vals, width, label=name, color=list(method_colors.values())[i],
                   alpha=0.85, edgecolor="white", linewidth=0.5)
        ax.set_xticks(x)
        short_names = [p.replace(f"{tc_name}: ", "") for p in pair_names]
        ax.set_xticklabels(short_names, fontsize=10)
        ax.set_title(f"{tc_name}", fontsize=13, fontweight="bold")
        ax.set_ylabel("Flujo q (mm/día)" if ax_idx == 0 else "")
        ax.axhline(y=0, color="k", linestyle="-", linewidth=0.8)
        ax.grid(True, alpha=0.2, axis="y")

    axes[0].legend(fontsize=8, loc="best")
    plt.suptitle(f"Flujo Vertical — 5 Métodos VFLUX2 ({n_tc} TCs)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    path = img_dir / "04_flujos_barras.png"
    plt.savefig(str(path))
    plt.close()
    return path


def plot_profile(harmonic_results, ctx, img_dir):
    """Fig 5: Perfil vertical de amplitud y fase por TC."""
    tc_list = ctx["tc_list"]
    tc_configs = ctx["tc_configs"]
    depths_m = ctx["depths_m"]
    n_tc = len(tc_list)

    fig, axes = plt.subplots(2, n_tc, figsize=(6 * n_tc, 10))
    if n_tc == 1:
        axes = axes.reshape(2, 1)

    for col_idx, tc_name in enumerate(tc_list):
        tc_map = tc_configs[tc_name]
        tc_sensors = [tc_map[p] for p in ["surface", "intermediate", "deep"] if p in tc_map]
        tc_amps = [harmonic_results[s]["amplitude"] for s in tc_sensors if s in harmonic_results]
        tc_phases = [harmonic_results[s]["phase"] for s in tc_sensors if s in harmonic_results]
        tc_r2 = [harmonic_results[s]["r_squared"] for s in tc_sensors if s in harmonic_results]
        tc_d = [depths_m[s] * 100 for s in tc_sensors if s in harmonic_results]

        ax1 = axes[0][col_idx]
        ax1.plot(tc_amps, tc_d, "o-", color="#e74c3c", markersize=12, linewidth=2.5, markeredgecolor="white")
        ax1.set_xlabel("Amplitud A (°C)")
        ax1.set_ylabel("Profundidad (cm)")
        ax1.set_title(f"{tc_name} — Atenuación de Amplitud", fontweight="bold")
        ax1.invert_yaxis()
        ax1.grid(True, alpha=0.2)
        for a, d, r2 in zip(tc_amps, tc_d, tc_r2):
            ax1.annotate(f"A={a:.3f}°C\nR²={r2:.3f}", (a, d), textcoords="offset points",
                         xytext=(15, -5), fontsize=9,
                         bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.7))

        ax2 = axes[1][col_idx]
        phases_deg = [np.degrees(p) for p in tc_phases]
        ax2.plot(phases_deg, tc_d, "s-", color="#3498db", markersize=12, linewidth=2.5, markeredgecolor="white")
        ax2.set_xlabel("Fase φ (grados)")
        ax2.set_ylabel("Profundidad (cm)")
        ax2.set_title(f"{tc_name} — Desfase con Profundidad", fontweight="bold")
        ax2.invert_yaxis()
        ax2.grid(True, alpha=0.2)
        for p, d in zip(phases_deg, tc_d):
            ax2.annotate(f"φ={p:.1f}°", (p, d), textcoords="offset points",
                         xytext=(15, -5), fontsize=9,
                         bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))

    plt.suptitle("Perfil Vertical de la Señal Térmica Diurna", fontsize=14, fontweight="bold")
    plt.tight_layout()
    path = img_dir / "05_perfil_vertical.png"
    plt.savefig(str(path))
    plt.close()
    return path


def plot_heatmap(df_aligned, ctx, img_dir):
    """Fig 6: Heatmap espacio-temporal de temperatura por TC."""
    tc_list = ctx["tc_list"]
    tc_configs = ctx["tc_configs"]
    depths_m = ctx["depths_m"]
    n_tc = len(tc_list)

    fig, axes = plt.subplots(1, n_tc, figsize=(7 * n_tc, 5))
    if n_tc == 1:
        axes = [axes]

    for ax_idx, tc_name in enumerate(tc_list):
        ax = axes[ax_idx]
        tc_map = tc_configs[tc_name]
        tc_sensors = [tc_map[p] for p in ["surface", "intermediate", "deep"] if p in tc_map]
        tc_depths_cm = [depths_m[s] * 100 for s in tc_sensors]
        mask = (df_aligned["fecha"] >= CUTOFF_START) & (df_aligned["fecha"] <= CUTOFF_END)
        df_tc = df_aligned[mask].copy()
        temp_matrix = np.column_stack([df_tc[s].values for s in tc_sensors])
        for j in range(temp_matrix.shape[1]):
            col_data = pd.Series(temp_matrix[:, j])
            temp_matrix[:, j] = col_data.interpolate(limit=4).values
        im = ax.imshow(temp_matrix.T, aspect="auto", cmap="RdYlBu_r",
                       extent=[mdates.date2num(df_tc["fecha"].iloc[0]),
                               mdates.date2num(df_tc["fecha"].iloc[-1]),
                               max(tc_depths_cm), min(tc_depths_cm)],
                       interpolation="bilinear")
        ax.set_ylabel("Profundidad (cm)")
        ax.set_title(f"{tc_name}", fontweight="bold")
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m"))
        ax.set_yticks(tc_depths_cm)
        plt.colorbar(im, ax=ax, label="T (°C)", shrink=0.8)

    plt.suptitle("Mapa Espacio-Temporal de Temperatura", fontsize=14, fontweight="bold")
    plt.tight_layout()
    path = img_dir / "06_heatmap_temperatura.png"
    plt.savefig(str(path))
    plt.close()
    return path


def plot_boxplot(all_flux_results, ctx, img_dir):
    """Fig 7: Boxplot de flujos por método y TC."""
    tc_list = ctx["tc_list"]
    n_tc = len(tc_list)
    colors_box = ["#2c3e50", "#e74c3c", "#3498db", "#27ae60", "#f39c12"]

    fig, axes = plt.subplots(1, n_tc, figsize=(7 * n_tc, 6), sharey=True)
    if n_tc == 1:
        axes = [axes]

    for ax_idx, tc_name in enumerate(tc_list):
        ax = axes[ax_idx]
        tc_pairs = {k: v for k, v in all_flux_results.items() if tc_name in k}
        data_by_method = {}
        for method, name in zip(METHODS, METHOD_NAMES):
            vals = [v["flux_mm_day"].get(method, np.nan) for v in tc_pairs.values()]
            vals = [x for x in vals if not np.isnan(x)]
            data_by_method[name] = vals
        bp = ax.boxplot(data_by_method.values(),
                        tick_labels=[n.split("(")[0].strip() for n in data_by_method.keys()],
                        patch_artist=True, widths=0.6)
        for patch, color in zip(bp["boxes"], colors_box):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        ax.axhline(y=0, color="k", linestyle="--", linewidth=0.8)
        ax.set_title(f"{tc_name}", fontsize=13, fontweight="bold")
        ax.set_ylabel("q (mm/día)" if ax_idx == 0 else "")
        ax.tick_params(axis="x", rotation=30)
        ax.grid(True, alpha=0.2, axis="y")

    plt.suptitle(f"Distribución de Flujos por Método ({n_tc} TCs)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    path = img_dir / "07_boxplot_flujos.png"
    plt.savefig(str(path))
    plt.close()
    return path


def plot_vflux2_fig1(df_aligned, df_work, time_hours, harmonic_results, ctx, img_dir):
    """VFLUX2 Figura 1: Series crudas, filtradas, amplitudes, fases (2x2)."""
    tc_list = ctx["tc_list"]
    tc_configs = ctx["tc_configs"]
    depths_m = ctx["depths_m"]
    sensor_colors = ctx["sensor_colors"]

    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    fig.suptitle("VFLUX2 Fig.1 — Series, Amplitudes y Fases (Datos Terreno)",
                 fontsize=14, fontweight="bold", y=0.98)

    mask_plot = (df_aligned["fecha"] >= CUTOFF_START) & (df_aligned["fecha"] <= CUTOFF_END)
    df_fig1 = df_aligned[mask_plot].copy()

    # a) Series crudas
    ax = axes[0, 0]
    for tc_name in tc_list:
        tc_map = tc_configs[tc_name]
        for pos in ["surface", "intermediate", "deep"]:
            if pos not in tc_map:
                continue
            s = tc_map[pos]
            depth_cm = depths_m[s] * 100
            lbl = f"{tc_name} {POSITION_SHORT[pos]} ({depth_cm:.0f} cm)"
            d = df_fig1.dropna(subset=[s])
            ls = "-" if tc_list.index(tc_name) % 2 == 0 else "--"
            ax.plot(d["fecha"], d[s], color=sensor_colors[s], linewidth=0.7, linestyle=ls, label=lbl)
    ax.set_ylabel("T (°C)")
    ax.set_title("a) Raw Time Series", fontweight="bold")
    ax.legend(fontsize=6, ncol=2, loc="upper right")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m"))
    ax.tick_params(axis="x", rotation=20, labelsize=8)
    ax.tick_params(direction="in", top=True, right=True)

    # b) Series filtradas
    ax = axes[0, 1]
    for tc_name in tc_list:
        tc_map = tc_configs[tc_name]
        for pos in ["surface", "intermediate", "deep"]:
            if pos not in tc_map:
                continue
            s = tc_map[pos]
            if s not in harmonic_results:
                continue
            hr = harmonic_results[s]
            t_h = time_hours
            T_fit = hr["offset"] + hr["amplitude"] * np.sin(2 * np.pi / 24.0 * t_h + hr["phase"])
            depth_cm = depths_m[s] * 100
            lbl = f"{tc_name} {POSITION_SHORT[pos]} ({depth_cm:.0f} cm)"
            ls = "-" if tc_list.index(tc_name) % 2 == 0 else "--"
            ax.plot(df_work["fecha"].values, T_fit, color=sensor_colors[s], linewidth=0.7, linestyle=ls, label=lbl)
    ax.set_ylabel("T (°C)")
    ax.set_title("b) Filtered (armónico diario)", fontweight="bold")
    ax.legend(fontsize=6, ncol=2, loc="upper right")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m"))
    ax.tick_params(axis="x", rotation=20, labelsize=8)
    ax.tick_params(direction="in", top=True, right=True)

    # c) Amplitudes
    ax = axes[1, 0]
    sensor_precision = 0.0625
    ls_map = ["-", "--", "-.", ":"]
    for tc_idx, tc_name in enumerate(tc_list):
        tc_map = tc_configs[tc_name]
        for pos in ["surface", "intermediate", "deep"]:
            if pos not in tc_map:
                continue
            s = tc_map[pos]
            if s not in harmonic_results:
                continue
            hr = harmonic_results[s]
            depth_cm = depths_m[s] * 100
            lbl = f"{tc_name} {POSITION_SHORT[pos]} ({depth_cm:.0f} cm): A={hr['amplitude']:.3f}°C"
            ax.axhline(y=hr["amplitude"], color=sensor_colors[s], linewidth=1.5,
                       linestyle=ls_map[tc_idx % len(ls_map)], label=lbl, alpha=0.8)
    ax.axhline(y=sensor_precision, color="red", linewidth=2.0, linestyle="-",
               label=f"Precisión ({sensor_precision}°C)", zorder=10)
    ax.set_ylabel("Amplitud (°C)")
    ax.set_title("c) Amplitudes", fontweight="bold")
    ax.legend(fontsize=6, loc="upper right")
    ax.set_ylim(bottom=0)
    ax.tick_params(direction="in", top=True, right=True)

    # d) Fases
    ax = axes[1, 1]
    for tc_idx, tc_name in enumerate(tc_list):
        tc_map = tc_configs[tc_name]
        for pos in ["surface", "intermediate", "deep"]:
            if pos not in tc_map:
                continue
            s = tc_map[pos]
            if s not in harmonic_results:
                continue
            hr = harmonic_results[s]
            depth_cm = depths_m[s] * 100
            phase_deg = np.degrees(hr["phase"])
            lbl = f"{tc_name} {POSITION_SHORT[pos]} ({depth_cm:.0f} cm): φ={phase_deg:.1f}°"
            ax.axhline(y=hr["phase"], color=sensor_colors[s], linewidth=1.5,
                       linestyle=ls_map[tc_idx % len(ls_map)], label=lbl, alpha=0.8)
    ax.set_ylabel("Fase (rad)")
    ax.set_title("d) Phase Angles", fontweight="bold")
    ax.legend(fontsize=6, loc="upper right")
    ax.tick_params(direction="in", top=True, right=True)

    plt.tight_layout()
    path = img_dir / "08_vflux2_fig1_series.png"
    plt.savefig(str(path))
    plt.close()
    return path


def plot_vflux2_fig2(all_flux_results, ctx, img_dir):
    """VFLUX2 Figura 2: Flujo por cada método (3x2)."""
    tc_list = ctx["tc_list"]
    tc_pair_colors = ctx["tc_pair_colors"]
    method_map = {
        "hatch_amplitude": "Hatch Amplitude", "hatch_phase": "Hatch Phase",
        "keery": "Keery Amplitude", "mccallum": "McCallum", "luce": "Luce",
    }
    flux_by_method = {}
    for method_key, method_label in method_map.items():
        flux_by_method[method_label] = {}
        for pair_name, flux_result in all_flux_results.items():
            flux_by_method[method_label][pair_name] = flux_result["flux_mm_day"].get(method_key, np.nan)

    n_rows = (len(method_map) + 1) // 2
    fig, axes = plt.subplots(n_rows, 2, figsize=(18, 5 * n_rows))
    fig.suptitle(f"VFLUX2 Fig.2 — Flujo por Método ({len(all_flux_results)} pares)",
                 fontsize=14, fontweight="bold", y=0.99)
    pair_order = list(all_flux_results.keys())
    x = np.arange(len(pair_order))

    for idx, (method_label, pair_flux) in enumerate(flux_by_method.items()):
        row, col = divmod(idx, 2)
        ax = axes[row, col]
        vals = [pair_flux.get(p, np.nan) for p in pair_order]
        colors = [tc_pair_colors.get(p, "#555") for p in pair_order]
        ax.bar(x, vals, color=colors, alpha=0.85, edgecolor="white", width=0.7)
        ax.axhline(y=0, color="k", linestyle="-", linewidth=0.8)
        ax.set_title(f"Flux ({method_label})", fontweight="bold", fontsize=11)
        ax.set_ylabel("Flujo (mm/día)")
        ax.set_xticks(x)
        short_labels = [p.split(": ")[0] + "\n" + p.split(": ")[1] if ": " in p else p for p in pair_order]
        ax.set_xticklabels(short_labels, fontsize=7)
        ax.grid(True, alpha=0.2, axis="y")
        ax.tick_params(direction="in", top=True, right=True)
        for i, v in enumerate(vals):
            if not np.isnan(v):
                ax.annotate(f"{v:.1f}", (i, v), ha="center",
                            va="bottom" if v >= 0 else "top", fontsize=6, fontweight="bold")

    # Panel resumen
    ax = axes[n_rows - 1, 1]
    ax.axis("off")
    summary = "RESUMEN (mm/día):\n"
    header = f"{'Método':<22}"
    for tc in tc_list:
        header += f" {tc + ' prom':>10}"
    summary += header + "\n" + "-" * (22 + 11 * len(tc_list)) + "\n"
    for method_key, method_label in method_map.items():
        line = f"{method_label:<22}"
        for tc in tc_list:
            tc_vals = [all_flux_results[p]["flux_mm_day"].get(method_key, np.nan)
                       for p in pair_order if tc in p]
            line += f" {np.nanmean(tc_vals):>10.1f}"
        summary += line + "\n"
    ax.text(0.1, 0.95, summary, transform=ax.transAxes, fontsize=10,
            verticalalignment="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8))

    plt.tight_layout()
    path = img_dir / "09_vflux2_fig2_flujo_metodo.png"
    plt.savefig(str(path))
    plt.close()
    return path


def generate_map_html(ctx, img_dir):
    """Genera mapa interactivo satelital ESRI con folium."""
    try:
        import folium
        import folium.plugins
        from pyproj import Transformer
    except ImportError:
        print("  [AVISO] folium/pyproj no instalados. Mapa omitido.")
        return None

    tc_list = ctx["tc_list"]
    transformer = Transformer.from_crs("EPSG:32719", "EPSG:4326", always_xy=True)
    coords_wgs84 = {}
    for station, utm in STATION_COORDS_UTM.items():
        lon, lat = transformer.transform(utm["easting"], utm["northing"])
        coords_wgs84[station] = {"lat": lat, "lon": lon}

    active = set(tc_list)
    center_lat = np.mean([v["lat"] for k, v in coords_wgs84.items() if k in active])
    center_lon = np.mean([v["lon"] for k, v in coords_wgs84.items() if k in active])

    m = folium.Map(
        location=[center_lat, center_lon], zoom_start=14,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
    )
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Esri Labels", name="Etiquetas", overlay=True,
    ).add_to(m)

    for station, coords in coords_wgs84.items():
        is_active = station in active
        utm = STATION_COORDS_UTM[station]
        if station in SENSOR_CONFIG:
            depths = sorted(set(v["depth_m"] for v in SENSOR_CONFIG[station].values()))
            depth_str = ", ".join(f"{d*100:.0f}" for d in depths) + " cm"
        else:
            depth_str = "Sin datos"
        popup_html = f"""<div style="font-family: Arial; font-size: 12px; min-width: 180px;">
            <b style="font-size: 14px; color: {'#c0392b' if is_active else '#7f8c8d'};">{station}</b><br>
            <hr style="margin: 3px 0;"><b>UTM:</b> {utm['easting']}E {utm['northing']}N<br>
            <b>WGS84:</b> {coords['lat']:.6f}°, {coords['lon']:.6f}°<br>
            <b>Prof:</b> {depth_str}<br>
            <b>Estado:</b> {'Activa' if is_active else 'Pendiente'}</div>"""
        folium.Marker(
            location=[coords["lat"], coords["lon"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{station} ({'activa' if is_active else 'pendiente'})",
            icon=folium.Icon(color="red" if is_active else "gray",
                             icon="thermometer-half" if is_active else "circle", prefix="fa"),
        ).add_to(m)

    ordered = ["TC5", "TC4", "TC3", "TC2", "TC1"]
    river_coords = [[coords_wgs84[s]["lat"], coords_wgs84[s]["lon"]] for s in ordered if s in coords_wgs84]
    folium.PolyLine(river_coords, color="cyan", weight=2, opacity=0.7, dash_array="8").add_to(m)
    folium.plugins.MeasureControl(position="bottomleft").add_to(m)
    folium.LayerControl().add_to(m)

    path = img_dir / "00_mapa_estaciones.html"
    m.save(str(path))
    return path


# ============================================================================
# EXPORTACION
# ============================================================================
def export_results(df_raw, df_aligned, df_stats, harmonic_results, all_flux_results,
                   pair_results, ctx, sensors, out_dir, img_dir, generated_images):
    """Exporta CSV + Excel con resumen ejecutivo."""
    tc_list = ctx["tc_list"]
    tc_configs = ctx["tc_configs"]
    depths_m = ctx["depths_m"]
    tc_assignment = ctx["tc_assignment"]

    # --- CSV individuales ---
    # 1. Flujos
    results_data = []
    for pair_name, flux_result in all_flux_results.items():
        for method, name in zip(METHODS, METHOD_NAMES):
            v_mm = flux_result["flux_mm_day"].get(method, np.nan)
            v_ms = flux_result["flux_m_s"].get(method, np.nan)
            results_data.append({
                "Par": pair_name,
                "Metodo": name,
                "q_mm_dia": round(v_mm, 2) if not np.isnan(v_mm) else np.nan,
                "q_m_s": v_ms,
                "Direccion": "Infiltracion" if v_mm > 0 else ("Exfiltracion" if v_mm < 0 else "-"),
            })
    df_flujos = pd.DataFrame(results_data)
    df_flujos.to_csv(out_dir / "flujos_todos_metodos.csv", index=False)

    # 2. Estadísticas
    df_stats.to_csv(out_dir / "estadisticas_sensores.csv", index=False)

    # 3. Temperaturas alineadas
    df_aligned.to_csv(out_dir / "temperaturas_alineadas.csv", index=False)

    # 4. Análisis armónico
    harm_export = []
    for col, r in harmonic_results.items():
        harm_export.append({
            "sensor": col,
            "tc": tc_assignment.get(col, "---"),
            "profundidad_m": depths_m.get(col, -1),
            "amplitud_C": r["amplitude"],
            "fase_rad": r["phase"],
            "fase_deg": np.degrees(r["phase"]),
            "offset_C": r["offset"],
            "R2": r["r_squared"],
        })
    df_armonicos = pd.DataFrame(harm_export)
    df_armonicos.to_csv(out_dir / "analisis_armonico.csv", index=False)

    # 5. Mapeo de sensores
    mapeo_export = []
    for tc_name in tc_list:
        tc_map = tc_configs[tc_name]
        for pos in ["surface", "intermediate", "deep"]:
            if pos not in tc_map:
                continue
            lbl = tc_map[pos]
            idx = int(lbl.split("_")[1]) - 1
            mapeo_export.append({
                "termocupla": tc_name,
                "posicion": pos,
                "label": lbl,
                "sensor_id": sensors[idx]["sensor_id"],
                "profundidad_m": depths_m[lbl],
            })
    df_mapeo = pd.DataFrame(mapeo_export)
    df_mapeo.to_csv(out_dir / "mapeo_sensores.csv", index=False)

    # --- EXCEL con resumen ejecutivo ---
    excel_path = out_dir / "resumen_procesamiento.xlsx"
    alpha_e = THERMAL_PARAMS["lambda_sediment"] / THERMAL_PARAMS["C_sediment"]
    d_pen = np.sqrt(2 * alpha_e / THERMAL_PARAMS["omega"])

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        # Hoja 1: Resumen ejecutivo
        resumen_data = [
            ["RESUMEN EJECUTIVO — PROCESAMIENTO VFLUX2", ""],
            ["Fecha de procesamiento", datetime.now().strftime("%Y-%m-%d %H:%M")],
            ["", ""],
            ["CONFIGURACIÓN DE CAMPO", ""],
            ["Termocuplas activas", ", ".join(tc_list)],
            ["Total sensores", sum(len(tc_configs[tc]) for tc in tc_list)],
            ["Periodo de análisis",
             f"{CUTOFF_START.strftime('%d-%b-%Y')} a {CUTOFF_END.strftime('%d-%b-%Y')}"],
            ["Frecuencia de muestreo", "30 min"],
            ["", ""],
            ["PARÁMETROS TÉRMICOS", ""],
            ["Conductividad λ (W/mK)", THERMAL_PARAMS["lambda_sediment"]],
            ["Cap. cal. sedimento Cs (MJ/m³K)", THERMAL_PARAMS["C_sediment"] / 1e6],
            ["Cap. cal. agua Cw (MJ/m³K)", THERMAL_PARAMS["C_water"] / 1e6],
            ["Difusividad κe (m²/s)", f"{alpha_e:.3e}"],
            ["Long. penetración d (m)", f"{d_pen:.3f}"],
            ["", ""],
            ["COORDENADAS (UTM 19S)", ""],
        ]
        for st, coords in STATION_COORDS_UTM.items():
            status = "ACTIVA" if st in set(tc_list) else "pendiente"
            resumen_data.append([f"{st} ({status})", f"{coords['easting']}E {coords['northing']}N"])

        resumen_data.extend([
            ["", ""],
            ["FLUJOS ESTIMADOS - McCallum (recomendado)", ""],
        ])
        for pair_name, flux in all_flux_results.items():
            v = flux["flux_mm_day"].get("mccallum", np.nan)
            resumen_data.append([pair_name, f"{v:.2f} mm/día" if not np.isnan(v) else "NaN"])

        resumen_data.extend([["", ""], ["IMÁGENES GENERADAS", ""]])
        for img in generated_images:
            resumen_data.append([Path(img).name, ""])

        df_resumen = pd.DataFrame(resumen_data, columns=["Campo", "Valor"])
        df_resumen.to_excel(writer, sheet_name="Resumen", index=False)

        # Hoja 2: Flujos
        df_flujos.to_excel(writer, sheet_name="Flujos_5_Metodos", index=False)

        # Hoja 3: Tabla pivotada
        pivot = df_flujos.pivot_table(values="q_mm_dia", index="Metodo", columns="Par", aggfunc="first")
        pivot.to_excel(writer, sheet_name="Flujos_Pivot")

        # Hoja 4: Estadísticas
        df_stats.to_excel(writer, sheet_name="Estadisticas_Sensores", index=False)

        # Hoja 5: Armónicos
        df_armonicos.to_excel(writer, sheet_name="Analisis_Armonico", index=False)

        # Hoja 6: Mapeo
        df_mapeo.to_excel(writer, sheet_name="Mapeo_Sensores", index=False)

    return excel_path


# ============================================================================
# MAIN
# ============================================================================
def main(data_dir=None, output_dir=None):
    """Pipeline principal de procesamiento."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("=" * 90)
    print("  PROCESAMIENTO AUTOMATIZADO DE DATOS DE TERRENO — VFLUX2 Python")
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)

    # Rutas
    if data_dir is None:
        data_dir = PROJECT_ROOT / "data" / "raw" / "Datos_Terreno"
    else:
        data_dir = Path(data_dir)

    if output_dir is None:
        out_dir = PROJECT_ROOT / "resultados_python" / "datos_terreno"
    else:
        out_dir = Path(output_dir)

    img_dir = out_dir / "figuras"
    out_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  Datos:   {data_dir}")
    print(f"  Salida:  {out_dir}")
    print(f"  Figuras: {img_dir}")

    # --- PASO 1: Carga ---
    print("\n[1/8] Cargando datos iButton...")
    sensors = load_all_ibuttons(data_dir)
    print(f"  {len(sensors)} archivos CSV cargados")

    # --- PASO 2: Mapeo ---
    print("\n[2/8] Resolviendo mapeo de sensores...")
    ctx = resolve_sensors(sensors)
    tc_list = ctx["tc_list"]
    sensor_labels = ctx["sensor_labels"]
    depths_m = ctx["depths_m"]
    tc_configs = ctx["tc_configs"]
    tc_assignment = ctx["tc_assignment"]
    n_tc = len(tc_list)
    n_sensors = sum(len(tc_configs[tc]) for tc in tc_list)
    print(f"  {n_tc} termocuplas ({', '.join(tc_list)}), {n_sensors} sensores configurados")

    # --- PASO 3: QC + alineación ---
    print("\n[3/8] Control de calidad y alineación temporal...")
    df_raw = ibuttons_to_dataframe(sensors, sensor_labels=sensor_labels)
    df_aligned = align_and_resample(df_raw, freq="30min")
    valid_mask = df_aligned[sensor_labels].notna().all(axis=1)
    df_valid = df_aligned[valid_mask].copy().reset_index(drop=True)
    df_work = df_valid if len(df_valid) > 48 else df_aligned.dropna(subset=sensor_labels[:2])
    df_work = df_work.reset_index(drop=True)
    t_start = df_work["fecha"].min()
    time_hours = ((df_work["fecha"] - t_start).dt.total_seconds() / 3600.0).values
    print(f"  {len(df_aligned)} registros alineados, {len(df_valid)} con datos completos")

    # Estadísticas descriptivas
    mask_field = (df_raw["fecha"] >= CUTOFF_START) & (df_raw["fecha"] <= CUTOFF_END)
    df_field = df_raw[mask_field].copy()
    stats_data = []
    for tc_name in tc_list:
        tc_map = tc_configs[tc_name]
        for pos in ["surface", "intermediate", "deep"]:
            if pos not in tc_map:
                continue
            col = tc_map[pos]
            s = df_field[col].dropna()
            stats_data.append({
                "TC": tc_name, "Posicion": POSITION_LABELS[pos],
                "Prof_cm": depths_m[col] * 100, "N": len(s),
                "T_media_C": round(s.mean(), 2), "T_min_C": round(s.min(), 2),
                "T_max_C": round(s.max(), 2), "Rango_C": round(s.max() - s.min(), 2),
                "Desv_std_C": round(s.std(), 3),
            })
    df_stats = pd.DataFrame(stats_data)

    # --- PASO 4: Análisis armónico ---
    print("\n[4/8] Análisis armónico (ciclo diario 24h)...")
    harmonic_results = run_harmonic_analysis(df_work, time_hours, sensor_labels, tc_assignment, depths_m)
    print(f"  {len(harmonic_results)} sensores analizados")
    for col, r in harmonic_results.items():
        tc = tc_assignment.get(col, "---")
        d = depths_m.get(col, -1) * 100
        q = "***" if r["r_squared"] > 0.7 else ("**" if r["r_squared"] > 0.3 else "*")
        print(f"    {tc} {d:.0f}cm: A={r['amplitude']:.3f}°C, R²={r['r_squared']:.3f} [{q}]")

    # --- PASO 5: Pares ---
    print("\n[5/8] Análisis de pares de sensores...")
    pairs = build_pairs(tc_list, tc_configs)
    pair_results = run_pair_analysis(pairs, df_work, time_hours, depths_m, harmonic_results)
    print(f"  {len(pair_results)} pares analizados")

    # --- PASO 6: Flujos ---
    print("\n[6/8] Cálculo de flujos verticales (5 métodos)...")
    all_flux_results = calculate_all_fluxes(pair_results)
    print(f"  {len(all_flux_results)} pares x 5 métodos = {len(all_flux_results)*5} cálculos")
    for pair_name, flux in all_flux_results.items():
        v = flux["flux_mm_day"].get("mccallum", np.nan)
        dir_str = "↓ infiltr." if v > 0 else "↑ exfiltr."
        print(f"    {pair_name}: q_McCallum = {v:.1f} mm/día ({dir_str})")

    # --- PASO 7: Visualizaciones ---
    print("\n[7/8] Generando visualizaciones...")
    setup_matplotlib()
    generated_images = []

    print("  → Mapa ESRI satelital...")
    p = generate_map_html(ctx, img_dir)
    if p:
        generated_images.append(p)

    print("  → Series temporales (vista general)...")
    generated_images.append(plot_series_overview(df_aligned, ctx, img_dir))

    print("  → Series por TC (estilo MATLAB VFLUX2)...")
    generated_images.extend(plot_series_per_tc(df_raw, ctx, img_dir))

    print("  → Ajustes armónicos...")
    generated_images.append(plot_harmonic_fits(df_work, time_hours, harmonic_results, ctx, img_dir))

    print("  → Flujos verticales (barras)...")
    generated_images.append(plot_flux_bars(all_flux_results, ctx, img_dir))

    print("  → Perfil vertical amplitud/fase...")
    generated_images.append(plot_profile(harmonic_results, ctx, img_dir))

    print("  → Heatmap espacio-temporal...")
    generated_images.append(plot_heatmap(df_aligned, ctx, img_dir))

    print("  → Boxplot flujos por método...")
    generated_images.append(plot_boxplot(all_flux_results, ctx, img_dir))

    print("  → VFLUX2 Fig.1 (series+amplitudes+fases)...")
    generated_images.append(plot_vflux2_fig1(df_aligned, df_work, time_hours, harmonic_results, ctx, img_dir))

    print("  → VFLUX2 Fig.2 (flujo por método)...")
    generated_images.append(plot_vflux2_fig2(all_flux_results, ctx, img_dir))

    print(f"  {len(generated_images)} archivos de imagen generados")

    # --- PASO 8: Exportación ---
    print("\n[8/8] Exportando resultados...")
    excel_path = export_results(
        df_raw, df_aligned, df_stats, harmonic_results, all_flux_results,
        pair_results, ctx, sensors, out_dir, img_dir, generated_images,
    )

    # Resumen final
    print("\n" + "=" * 90)
    print("  PROCESAMIENTO COMPLETADO EXITOSAMENTE")
    print("=" * 90)
    print(f"\n  Termocuplas: {', '.join(tc_list)}")
    print(f"  Sensores:    {n_sensors}")
    print(f"  Pares:       {len(pair_results)}")
    print(f"  Métodos:     5 (McCallum, Hatch-A, Hatch-φ, Keery, Luce)")
    print(f"\n  Archivos CSV:")
    for f in sorted(out_dir.glob("*.csv")):
        print(f"    - {f.name}")
    print(f"\n  Excel resumen: {excel_path.name}")
    print(f"\n  Figuras ({len(generated_images)}):")
    for img in generated_images:
        print(f"    - {Path(img).name}")
    print(f"\n  Directorio de salida: {out_dir}")
    print("=" * 90)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Procesamiento automatizado de datos de terreno VFLUX2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--data-dir", type=str, default=None,
                        help="Directorio con CSV iButton (default: data/raw/Datos_Terreno)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Directorio de salida (default: resultados_python/datos_terreno)")
    args = parser.parse_args()
    main(data_dir=args.data_dir, output_dir=args.output_dir)
