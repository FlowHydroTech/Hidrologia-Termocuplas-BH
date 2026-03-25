#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
figuras_05A.py — Generación de figuras estáticas para el análisis 05A.

Ejecutar desde la raíz del proyecto:
    python scripts/figuras_05A.py

Requiere:
  - Haber ejecutado pipeline_05A.py (o que existan los CSVs en OUT_DIR).

Figuras generadas (image/terreno_2026/):
  1. series_05A_hatch.png           — Series de temperatura 5 TC combinadas
  2. temperatura_TC*_05A.png        — Series individuales por TC
  3. ajustes_armonicos_05A.png      — Matriz de ajustes sinusoidales
  4. boxplot_hatch_05A.png          — Boxplot HA + scatter HA vs MC
  5. barras_hatch_only_05A.png      — Barras HA por TC con ref. MATLAB
  6. flujo_ic95_informe_cap4.png/pdf— Forest-plot IC 95 %
  7. flux_hatch_amplitude_TC*.png   — Series flujo por TC (réplica MATLAB)
  8. series_flujo_hatch_5TC.png/pdf — Panel combinado 5×1
  9. boxplot_hatch_amplitude_informe— Boxplot publicación (series temporales)
 10. series_temporales_hatch_informe— Series publicación panel 5×1
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.ticker import FuncFormatter
import warnings
warnings.filterwarnings("ignore")

from config_05A import (
    PROJECT_ROOT, DATA_DIR, OUT_DIR, IMG_DIR,
    TC_CONFIG, DEPTHS_M, TC_ASSIGNMENT, ACTIVE_TCS,
    THERMAL_PARAMS_LAB, THERMAL_PARAMS_VFLUX, MATLAB_REFERENCE,
    TC_PERIODS, TC_COLORS, PAIR_MAP, PAIR_LABELS, PAIR_COLORS_MATLAB,
)

# Importar pipeline para obtener datos en memoria
import pipeline_05A as pipe


# ══════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════
def _pub_style():
    """Aplica estilo publicación."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 9,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.45,
    })


def _set_sci_yaxis(ax, y_lo, y_hi):
    """Eje Y en notación científica ×10^exp."""
    abs_max = max(abs(y_lo), abs(y_hi))
    if abs_max < 5e-5:
        exp, factor = -6, 1e6
    else:
        exp, factor = -5, 1e5
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x * factor:.1f}"))
    sup_map = {"-": "⁻", "5": "⁵", "6": "⁶"}
    exp_str = "".join(sup_map[c] for c in str(exp))
    ax.annotate(f"×10{exp_str}", xy=(0, 1.02), xycoords="axes fraction",
                fontsize=10, ha="left", va="bottom")


DATE_FMT = "%d-%b"

# Colores posición para series temperatura
_tc_colors_matlab = {"surface": "#0072BD", "intermediate": "#D95319", "deep": "#EDB120"}
_pos_labels = {"surface": "Superficial", "intermediate": "Intermedio", "deep": "Profundo"}


# ══════════════════════════════════════════════════════════════════════════
# 1. SERIES DE TEMPERATURA
# ══════════════════════════════════════════════════════════════════════════
def fig_temperatura(df_raw):
    """Panel combinado 5×1 + individuales de temperatura."""
    _pub_style()
    fig, axes = plt.subplots(len(ACTIVE_TCS), 1, figsize=(16, 3.5 * len(ACTIVE_TCS)),
                             sharex=False)
    for idx, tc_name in enumerate(ACTIVE_TCS):
        ax = axes[idx]
        tc_map = TC_CONFIG[tc_name]
        tc_start = pd.Timestamp(TC_PERIODS[tc_name][0])
        tc_end = pd.Timestamp(TC_PERIODS[tc_name][1])
        for pos in ["surface", "intermediate", "deep"]:
            label = tc_map[pos]
            d_m = DEPTHS_M[label]
            mask = (df_raw["fecha"] >= tc_start) & (df_raw["fecha"] <= tc_end)
            df_plot = df_raw[mask].dropna(subset=[label])
            ax.plot(df_plot["fecha"], df_plot[label], color=_tc_colors_matlab[pos],
                    linewidth=1.0, label=f"{_pos_labels[pos]} ({d_m:.2f} m)")
        tp = THERMAL_PARAMS_LAB[tc_name]
        dias = (tc_end - tc_start).days
        ax.set_ylabel("Temperatura [°C]")
        ax.set_title(f'{tc_name} — {tp["USCS"]} | λ={tp["lambda_sediment"]:.3f} W/m·K | '
                     f'α={tp["alpha_e"]:.2e} m²/s | {dias} días', fontsize=10, pad=4)
        ax.legend(loc="upper right", ncol=3, fontsize=8, framealpha=0.9)
        ax.xaxis.set_major_formatter(mdates.DateFormatter(DATE_FMT))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right", fontsize=9)

    fig.suptitle("Series Temporales de Temperatura [°C] — 5 Termocuplas",
                 fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(str(IMG_DIR / "series_05A_hatch.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Individuales
    for tc_name in ACTIVE_TCS:
        tc_map = TC_CONFIG[tc_name]
        tc_start = pd.Timestamp(TC_PERIODS[tc_name][0])
        tc_end = pd.Timestamp(TC_PERIODS[tc_name][1])
        tp = THERMAL_PARAMS_LAB[tc_name]
        dias = (tc_end - tc_start).days
        fig_i, ax_i = plt.subplots(figsize=(14, 4))
        for pos in ["surface", "intermediate", "deep"]:
            label = tc_map[pos]
            d_m = DEPTHS_M[label]
            mask = (df_raw["fecha"] >= tc_start) & (df_raw["fecha"] <= tc_end)
            df_plot = df_raw[mask].dropna(subset=[label])
            ax_i.plot(df_plot["fecha"], df_plot[label], color=_tc_colors_matlab[pos],
                      linewidth=1.2, label=f"{_pos_labels[pos]} ({d_m:.2f} m)")
        ax_i.set_ylabel("Temperatura [°C]")
        ax_i.set_xlabel("Fecha")
        ax_i.set_title(f"Serie Temporal de Temperatura — {tc_name} ({tp['USCS']})\n"
                       f"λ = {tp['lambda_sediment']:.3f} W/m·K  |  "
                       f"α = {tp['alpha_e']:.2e} m²/s  |  {dias} días",
                       fontsize=11, fontweight="bold")
        ax_i.legend(loc="upper right", ncol=3, fontsize=9, framealpha=0.9)
        ax_i.xaxis.set_major_formatter(mdates.DateFormatter(DATE_FMT))
        ax_i.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.setp(ax_i.xaxis.get_majorticklabels(), rotation=45, ha="right", fontsize=9)
        fig_i.tight_layout()
        fig_i.savefig(str(IMG_DIR / f"temperatura_{tc_name}_05A.png"), dpi=150,
                      bbox_inches="tight")
        plt.close(fig_i)

    print(f"  ✔ Temperatura: combinada + {len(ACTIVE_TCS)} individuales")


# ══════════════════════════════════════════════════════════════════════════
# 2. AJUSTES ARMÓNICOS
# ══════════════════════════════════════════════════════════════════════════
def fig_armonicos(df_aligned, harmonic_results):
    """Matriz 5×3 de ajustes sinusoidales."""
    _pub_style()
    fig, axes = plt.subplots(len(ACTIVE_TCS), 3, figsize=(18, 3.5 * len(ACTIVE_TCS)))
    for row_idx, tc_name in enumerate(ACTIVE_TCS):
        tc_map = TC_CONFIG[tc_name]
        for col_idx, (pos, pos_es) in enumerate([
            ("surface", "Superficie"), ("intermediate", "Intermedio"), ("deep", "Inferior")
        ]):
            ax = axes[row_idx][col_idx]
            col = tc_map[pos]
            if col not in harmonic_results:
                ax.text(0.5, 0.5, "Sin datos", ha="center", va="center",
                        transform=ax.transAxes)
                continue
            result = harmonic_results[col]
            t_h = result["time_hours"]
            tc_start = pd.Timestamp(TC_PERIODS[tc_name][0])
            tc_end = pd.Timestamp(TC_PERIODS[tc_name][1])
            mask_tc = (df_aligned["fecha"] >= tc_start) & (df_aligned["fecha"] <= tc_end)
            df_tc = df_aligned[mask_tc]
            series = df_tc[col].dropna().values
            # Primeros 7 días
            max_7d = 7 * 48  # 30-min intervals
            t_plot = t_h[:max_7d]
            s_plot = series[:min(len(series), max_7d)]
            t_fit = np.linspace(t_plot[0], t_plot[-1], 500) if len(t_plot) > 0 else []
            if len(t_fit) > 0:
                fitted = (result["amplitude"] * np.sin(
                    2 * np.pi * t_fit / 24.0 + result["phase"]) + result["offset"])
                ax.plot(t_plot, s_plot[:len(t_plot)], ".", color="#999", markersize=2,
                        alpha=0.6, label="Datos")
                ax.plot(t_fit, fitted, "-", color=TC_COLORS[tc_name], linewidth=1.5,
                        label=f"Ajuste R²={result['r_squared']:.3f}")
            ax.set_title(f"{tc_name} {pos_es} ({DEPTHS_M[col]*100:.0f} cm)",
                         fontsize=9, pad=3)
            ax.legend(fontsize=7, loc="upper right")
            if col_idx == 0:
                ax.set_ylabel("T [°C]")
            if row_idx == len(ACTIVE_TCS) - 1:
                ax.set_xlabel("Horas")

    fig.suptitle("Ajustes Armónicos — Primeros 7 días de monitoreo",
                 fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(str(IMG_DIR / "ajustes_armonicos_05A.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  ✔ Ajustes armónicos 5×3")


# ══════════════════════════════════════════════════════════════════════════
# 3. BOXPLOT + SCATTER (HA por TC, HA vs MC)
# ══════════════════════════════════════════════════════════════════════════
def fig_boxplot_scatter(all_flux_results):
    """Boxplot HA + validación cruzada scatter."""
    _pub_style()
    fig, axes = plt.subplots(1, 2, figsize=(16, 5.5))

    # Panel 1: Boxplot
    ax1 = axes[0]
    data_ha, labels_ha, colors_bp = [], [], []
    for tc_name in ACTIVE_TCS:
        tc_pairs = {k: v for k, v in all_flux_results.items() if tc_name in k}
        vals = [v["flux_mm_day"].get("hatch_amplitude", np.nan) for v in tc_pairs.values()]
        vals = [x for x in vals if not np.isnan(x)]
        data_ha.append(vals)
        labels_ha.append(tc_name)
        colors_bp.append(TC_COLORS[tc_name])

    bp1 = ax1.boxplot(data_ha, tick_labels=labels_ha, patch_artist=True, widths=0.6)
    for patch, color in zip(bp1["boxes"], colors_bp):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    for i, vals in enumerate(data_ha):
        x = np.random.normal(i + 1, 0.04, size=len(vals))
        ax1.scatter(x, vals, color=colors_bp[i], alpha=0.8, s=70, zorder=5,
                    edgecolors="white")
    ax1.axhline(y=0, color="k", linestyle="--", linewidth=0.8)
    ax1.set_ylabel("Flujo q [mm/día]")
    ax1.set_title("Hatch-Amplitude — Flujo por Termocupla", fontsize=11, fontweight="bold")

    # Panel 2: Scatter HA vs MC
    ax2 = axes[1]
    all_ha_vals, all_mc_vals, all_colors = [], [], []
    for tc_name in ACTIVE_TCS:
        tc_pairs = {k: v for k, v in all_flux_results.items() if tc_name in k}
        for fr in tc_pairs.values():
            ha = fr["flux_mm_day"].get("hatch_amplitude", np.nan)
            mc = fr["flux_mm_day"].get("mccallum", np.nan)
            if not np.isnan(ha) and not np.isnan(mc):
                all_ha_vals.append(ha)
                all_mc_vals.append(mc)
                all_colors.append(TC_COLORS[tc_name])
    ax2.scatter(all_ha_vals, all_mc_vals, c=all_colors, s=110, alpha=0.8,
                edgecolors="white", linewidth=1, zorder=5)
    if all_ha_vals:
        lim = max(abs(min(all_ha_vals + all_mc_vals)),
                  abs(max(all_ha_vals + all_mc_vals))) * 1.1
        ax2.plot([-lim, lim], [-lim, lim], "k--", alpha=0.5, label="1:1")
        ax2.set_xlim(-lim, lim)
        ax2.set_ylim(-lim, lim)
    if len(all_ha_vals) > 2:
        corr = np.corrcoef(all_ha_vals, all_mc_vals)[0, 1]
        ax2.text(0.05, 0.95, f"r = {corr:.3f}\nn = {len(all_ha_vals)}",
                 transform=ax2.transAxes, fontsize=11, va="top",
                 bbox=dict(boxstyle="round", facecolor="white", alpha=0.9))
    for tc_name in ACTIVE_TCS:
        ax2.scatter([], [], color=TC_COLORS[tc_name], s=80, label=tc_name)
    ax2.legend(fontsize=9, loc="lower right")
    ax2.set_xlabel("Hatch-Amplitude q [mm/día]")
    ax2.set_ylabel("McCallum q [mm/día]")
    ax2.set_title("Validación Hatch-Amp vs McCallum", fontsize=11, fontweight="bold")

    fig.tight_layout()
    fig.savefig(str(IMG_DIR / "boxplot_hatch_05A.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  ✔ Boxplot + scatter HA vs MC")


# ══════════════════════════════════════════════════════════════════════════
# 4. BARRAS HA POR TC
# ══════════════════════════════════════════════════════════════════════════
def fig_barras(all_flux_results):
    """Barras Hatch-Amplitude con referencia MATLAB."""
    _pub_style()
    fig, axes = plt.subplots(1, len(ACTIVE_TCS), figsize=(5 * len(ACTIVE_TCS), 5))
    for ax_idx, tc_name in enumerate(ACTIVE_TCS):
        ax = axes[ax_idx]
        tc_pairs = {k: v for k, v in all_flux_results.items() if tc_name in k}
        pair_names = list(tc_pairs.keys())
        x = np.arange(len(pair_names))
        vals = [tc_pairs[p]["flux_mm_day"].get("hatch_amplitude", 0) for p in pair_names]
        bars = ax.bar(x, vals, width=0.6, color=TC_COLORS[tc_name], alpha=0.85,
                      edgecolor="white", linewidth=1.2)
        for bar_i, val in zip(bars, vals):
            ax.text(bar_i.get_x() + bar_i.get_width() / 2, bar_i.get_height() + 1,
                    f"{val:.0f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
        short_names = [p.replace(f"{tc_name}: ", "") for p in pair_names]
        ax.set_xticks(x)
        ax.set_xticklabels(short_names, fontsize=8, rotation=20, ha="right")
        ref = MATLAB_REFERENCE.get(tc_name, {})
        if ref:
            ax.axhline(y=ref["mean"], color="#555555", linestyle="--", linewidth=1.2, alpha=0.7)
            ymax = max(max(vals), ref["mean"]) if vals else ref["mean"]
            ax.text(len(pair_names) - 0.5, ref["mean"] + ymax * 0.02,
                    f"MATLAB: {ref['mean']} mm/d", fontsize=7, va="bottom",
                    color="#555555", fontstyle="italic")
            ax.set_ylim(top=ymax * 1.15)
        tp = THERMAL_PARAMS_LAB[tc_name]
        ax.set_title(f'{tc_name}\n({tp["USCS"]})', fontsize=11, fontweight="bold")
        ax.set_ylabel("Flujo Hatch-Amplitude [mm/día]" if ax_idx == 0 else "")
        ax.axhline(y=0, color="k", linestyle="-", linewidth=0.8)
        ax.grid(True, axis="both", alpha=0.55, linewidth=0.5, color="#999999")
    fig.suptitle("Flujo Vertical Hatch-Amplitude por Termocupla [mm/día]\n"
                 "(línea punteada = referencia MATLAB VFLUX2)",
                 fontsize=13, fontweight="bold", y=1.03)
    fig.tight_layout()
    fig.savefig(str(IMG_DIR / "barras_hatch_only_05A.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  ✔ Barras HA por TC")


# ══════════════════════════════════════════════════════════════════════════
# 5. FOREST-PLOT IC 95 %
# ══════════════════════════════════════════════════════════════════════════
def fig_forest_plot():
    """Forest-plot IC 95 % + barras confiabilidad (lee CSVs)."""
    _pub_style()
    base = OUT_DIR
    csv_iqr = base / "tabla_iqr_hatch_amplitude.csv"
    csv_unc = base / "incertidumbre_hatch.csv"
    csv_conf = base / "confiabilidad_hatch_mccallum.csv"

    if not all(p.exists() for p in [csv_iqr, csv_unc, csv_conf]):
        print("  ⚠ Forest-plot: CSVs no encontrados, saltar")
        return

    df_iqr_raw = pd.read_csv(csv_iqr)
    df_unc = pd.read_csv(csv_unc)
    df_conf = pd.read_csv(csv_conf)

    # Filtrar solo filas TOTAL (resumen por TC)
    df_iqr = df_iqr_raw[df_iqr_raw["Par"] == "TOTAL"].reset_index(drop=True)
    if df_iqr.empty:
        print("  Forest-plot: sin filas TOTAL en IQR, saltar")
        return

    tc = df_iqr["TC"].values
    q_mean = df_iqr["Media"].values
    q_q1 = df_iqr["Q1"].values
    q_q3 = df_iqr["Q3"].values
    # Referencia MATLAB desde config
    q_mat = np.array([MATLAB_REFERENCE.get(t, {}).get("mean", np.nan) for t in tc])
    n_tc = len(tc)

    ic_lo = np.array([df_unc.loc[df_unc["TC"] == t, "IC 95% bajo"].mean() for t in tc])
    ic_hi = np.array([df_unc.loc[df_unc["TC"] == t, "IC 95% alto"].mean() for t in tc])
    ic_sc = np.array([df_conf.loc[df_conf["TC"] == t, "IC_total"].max() for t in tc])

    cmap = LinearSegmentedColormap.from_list("conf", ["#C62828", "#FFB300", "#2E7D32"], N=256)
    norm = Normalize(vmin=0.40, vmax=0.85)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8.5),
                                    gridspec_kw={"height_ratios": [3.2, 1], "hspace": 0.35})
    y = np.arange(n_tc)

    mat_in_range = q_mat[q_mat < 1200]
    x_max = max(ic_hi.max(), mat_in_range.max() if len(mat_in_range) else ic_hi.max()) * 1.55

    for i in range(n_tc):
        c = cmap(norm(ic_sc[i]))
        ax1.barh(i, q_q3[i] - q_q1[i], left=q_q1[i], height=0.38,
                 color=c, alpha=0.45, edgecolor="none", zorder=2)
        ax1.plot([ic_lo[i], ic_hi[i]], [i, i], color=c, linewidth=2.2,
                 solid_capstyle="round", zorder=3)
        ax1.plot([ic_lo[i], ic_lo[i]], [i - 0.10, i + 0.10], color=c, lw=1.8, zorder=3)
        ax1.plot([ic_hi[i], ic_hi[i]], [i - 0.10, i + 0.10], color=c, lw=1.8, zorder=3)
        ax1.scatter(q_mean[i], i, s=110, color=c, edgecolors="k",
                    linewidths=0.7, zorder=5)
        if q_mat[i] <= x_max * 0.75:
            ax1.scatter(q_mat[i], i, marker="D", s=70, facecolors="none",
                        edgecolors="#1565C0", linewidths=1.4, zorder=5)
        else:
            ax1.annotate("", xy=(x_max - 20, i + 0.15),
                         xytext=(ic_hi[i] + 35, i + 0.15),
                         arrowprops=dict(arrowstyle="-|>", color="#1565C0",
                                         lw=1.3, mutation_scale=10))
            ax1.text(ic_hi[i] + 40, i + 0.30,
                     f"MATLAB = {q_mat[i]:.0f} mm/d", fontsize=7.5,
                     color="#1565C0", fontstyle="italic", va="center")
        label_x = ic_hi[i] + 12
        offset_y = -0.22 if q_mat[i] > x_max * 0.75 else 0
        ax1.text(label_x, i + offset_y,
                 f"{q_mean[i]:.0f}  [{ic_lo[i]:.0f}–{ic_hi[i]:.0f}]",
                 va="center", fontsize=9, color="#333")

    ax1.set_xlim(0, x_max)
    ax1.set_yticks(y)
    ax1.set_yticklabels(tc, fontweight="bold")
    ax1.invert_yaxis()
    ax1.set_xlabel("Flujo vertical  $q$  (mm/día)", fontsize=11)
    ax1.set_title("(a)  Flujo vertical Hatch-Amplitude con IC 95 %",
                  fontweight="bold", loc="left", pad=8)
    ax1.axvline(0, color="k", lw=0.6)
    ax1.grid(True, axis="both", alpha=0.5, lw=0.5, color="#999999")

    legend_items = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#888",
                   markeredgecolor="k", markersize=8, label="Media HA (3 pares)"),
        mpatches.Patch(facecolor="#999", alpha=0.45, label="Rango IQR (Q1–Q3)"),
        plt.Line2D([0], [0], color="#888", lw=2.2, label="IC 95 % (propagación)"),
        plt.Line2D([0], [0], marker="D", color="w", markerfacecolor="none",
                   markeredgecolor="#1565C0", markersize=7, markeredgewidth=1.3,
                   label="Ref. MATLAB VFLUX2"),
    ]
    ax1.legend(handles=legend_items, loc="lower right", frameon=True,
               framealpha=0.92, edgecolor="#ccc")

    # Panel (b)
    bar_colors = [cmap(norm(v)) for v in ic_sc]
    ax2.barh(y, ic_sc, height=0.48, color=bar_colors,
             edgecolor="white", linewidth=0.8, zorder=3)
    ax2.axvline(0.70, color="#2E7D32", ls="--", lw=0.9, alpha=0.7)
    ax2.axvline(0.55, color="#E65100", ls="--", lw=0.9, alpha=0.7)
    ax2.text(0.71, n_tc - 0.5, "Alta", fontsize=7.5, color="#2E7D32",
             fontweight="bold", va="top")
    ax2.text(0.56, n_tc - 0.5, "Moderada", fontsize=7.5, color="#E65100",
             fontweight="bold", va="top")
    ax2.text(0.41, n_tc - 0.5, "Precaución", fontsize=7.5, color="#C62828",
             fontweight="bold", va="top")
    for i, v in enumerate(ic_sc):
        ax2.text(v + 0.012, i, f"{v:.2f}", va="center", fontsize=9.5,
                 fontweight="bold", color="#333")
    ax2.set_xlim(0.35, 0.95)
    ax2.set_yticks(y)
    ax2.set_yticklabels(tc, fontweight="bold")
    ax2.invert_yaxis()
    ax2.set_xlabel("Índice de confiabilidad  IC$_{total}$  (mejor par)", fontsize=11)
    ax2.set_title("(b)  Índice de confiabilidad compuesto",
                  fontweight="bold", loc="left", pad=6)
    ax2.grid(True, axis="both", alpha=0.5, lw=0.5, color="#999999")

    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=[ax1, ax2], location="right", pad=0.03,
                        fraction=0.022, aspect=35, shrink=0.80)
    cbar.set_label("IC$_{total}$", fontsize=10)
    cbar.ax.tick_params(labelsize=8)

    fig.suptitle("Río Silala — Flujo vertical por estación termocupla\n"
                 "Dic 2025 – Feb 2026  ·  Método: Hatch-Amplitude",
                 fontsize=12, fontweight="bold", y=1.01)

    plt.tight_layout(rect=[0, 0.02, 0.94, 0.95])
    for ext in ("png", "pdf"):
        fig.savefig(IMG_DIR / f"flujo_ic95_informe_cap4.{ext}",
                    dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.3)
    plt.close(fig)
    print("  ✔ Forest-plot IC 95 % (PNG + PDF)")


# ══════════════════════════════════════════════════════════════════════════
# 6. SERIES FLUJO POR TC — RÉPLICA MATLAB
# ══════════════════════════════════════════════════════════════════════════
def fig_flux_matlab():
    """Figuras individuales y panel 5×1 de flujo — formato MATLAB."""
    _pub_style()
    BASE_TS = OUT_DIR / "series_temporales"
    PAIRS = ["sup_int", "int_inf", "sup_inf"]

    # Cargar datos
    all_data = {}
    for tc in ACTIVE_TCS:
        all_data[tc] = {}
        for pair in PAIRS:
            fpath = BASE_TS / f"flujo_temporal_{tc}_{pair}.csv"
            if not fpath.exists():
                continue
            df = pd.read_csv(fpath, parse_dates=["datetime"])
            if "flux_hatch_amplitude_mm_day" not in df.columns:
                continue
            df["flux_ms"] = df["flux_hatch_amplitude_mm_day"] / 1000.0 / 86400.0
            mask = df["flux_ms"].notna() & np.isfinite(df["flux_ms"])
            all_data[tc][pair] = df.loc[mask, ["datetime", "flux_ms"]].copy()

    # Individuales
    for tc in ACTIVE_TCS:
        fig, ax = plt.subplots(figsize=(12, 4.2))
        y_max, y_min = -np.inf, np.inf
        for pair in PAIRS:
            if pair not in all_data[tc]:
                continue
            d = all_data[tc][pair]
            ax.plot(d["datetime"], d["flux_ms"], "-o",
                    color=PAIR_COLORS_MATLAB[pair], label=PAIR_LABELS[pair],
                    linewidth=1.4, markersize=4.5, alpha=0.9)
            y_max = max(y_max, d["flux_ms"].max())
            y_min = min(y_min, d["flux_ms"].min())
        span = y_max - y_min
        margin = span * 0.08 if span > 0 else abs(y_max) * 0.1
        y_lo = 0 if y_min >= 0 else y_min - margin
        y_hi = y_max + margin
        ax.set_ylim(y_lo, y_hi)
        _set_sci_yaxis(ax, y_lo, y_hi)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        ax.set_title(f"Flux (Hatch Amplitude) — {tc}", fontweight="bold")
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Flujo vertical (m/s)")
        ax.legend(loc="best", ncol=3, framealpha=0.92, edgecolor="0.8")
        fig.tight_layout()
        for ext in ("png", "pdf"):
            fig.savefig(IMG_DIR / f"flux_hatch_amplitude_{tc}.{ext}", bbox_inches="tight")
        plt.close(fig)

    # Panel 5×1
    fig, axes = plt.subplots(5, 1, figsize=(14, 22), sharex=True)
    for i, tc in enumerate(ACTIVE_TCS):
        ax = axes[i]
        y_max, y_min = -np.inf, np.inf
        for pair in PAIRS:
            if pair not in all_data[tc]:
                continue
            d = all_data[tc][pair]
            ax.plot(d["datetime"], d["flux_ms"], "-o",
                    color=PAIR_COLORS_MATLAB[pair], label=PAIR_LABELS[pair],
                    linewidth=1.2, markersize=3.5, alpha=0.9)
            y_max = max(y_max, d["flux_ms"].max())
            y_min = min(y_min, d["flux_ms"].min())
        span = y_max - y_min
        margin = span * 0.08 if span > 0 else abs(y_max) * 0.1
        y_lo = 0 if y_min >= 0 else y_min - margin
        y_hi = y_max + margin
        ax.set_ylim(y_lo, y_hi)
        _set_sci_yaxis(ax, y_lo, y_hi)
        ax.set_title(f"Flux (Hatch Amplitude) — {tc}", fontweight="bold", fontsize=13)
        ax.set_ylabel("Flujo (m/s)")
        if i == 0:
            ax.legend(loc="upper right", ncol=3, framealpha=0.92, fontsize=9)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    axes[-1].set_xlabel("Fecha")
    fig.tight_layout(h_pad=2.5)
    for ext in ("png", "pdf"):
        fig.savefig(IMG_DIR / f"series_flujo_hatch_5TC.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"  ✔ Flujo MATLAB: 5 individuales + panel combinado")


# ══════════════════════════════════════════════════════════════════════════
# 7. BOXPLOT PUBLICACIÓN (SERIES TEMPORALES)
# ══════════════════════════════════════════════════════════════════════════
def fig_boxplot_pub(flux_ts_results):
    """Boxplot estilo publicación/informe."""
    _pub_style()
    boxplot_data = {}
    for pair_name, df_flux in flux_ts_results.items():
        tc = pair_name.split("_")[0]
        df_ok = df_flux[df_flux["quality_flag"] == 0]
        if "flux_hatch_amplitude_mm_day" in df_ok.columns:
            vals = df_ok["flux_hatch_amplitude_mm_day"].dropna().values
            if tc not in boxplot_data:
                boxplot_data[tc] = []
            boxplot_data[tc].extend(vals.tolist())

    tc_order = ACTIVE_TCS
    data_list = [np.array(boxplot_data.get(tc, [])) for tc in tc_order]
    positions = np.arange(1, len(tc_order) + 1)
    colors_box = [TC_COLORS[tc] for tc in tc_order]

    fig, ax = plt.subplots(figsize=(10, 6))
    bp = ax.boxplot(data_list, positions=positions, patch_artist=True, widths=0.55,
                    showfliers=False,
                    medianprops=dict(color="black", linewidth=1.8),
                    whiskerprops=dict(linewidth=1.2),
                    capprops=dict(linewidth=1.2))
    for patch, color in zip(bp["boxes"], colors_box):
        patch.set_facecolor(color)
        patch.set_alpha(0.55)
        patch.set_edgecolor("black")
        patch.set_linewidth(1.0)
    for i, (tc, vals) in enumerate(zip(tc_order, data_list)):
        if len(vals) == 0:
            continue
        x_jitter = np.random.default_rng(42).normal(positions[i], 0.08, size=len(vals))
        ax.scatter(x_jitter, vals, color=colors_box[i], alpha=0.35, s=18,
                   edgecolors="none", zorder=4)
    for i, tc in enumerate(tc_order):
        ref = MATLAB_REFERENCE.get(tc, {})
        if ref:
            ax.scatter(positions[i], ref["mean"], marker="D", s=90, facecolors="none",
                       edgecolors="#1565C0", linewidths=1.5, zorder=6,
                       label="Ref. MATLAB VFLUX2" if i == 0 else None)
    for i, (tc, vals) in enumerate(zip(tc_order, data_list)):
        if len(vals) == 0:
            continue
        med = np.median(vals)
        q3 = np.percentile(vals, 75)
        ax.text(positions[i], q3 + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.02,
                f"med={med:.0f}\nn={len(vals)}",
                ha="center", va="bottom", fontsize=8, color="#333",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                          alpha=0.8, edgecolor="none"))

    uscs_labels = [f"{tc}\n({THERMAL_PARAMS_LAB[tc]['USCS']})" for tc in tc_order]
    ax.set_xticks(positions)
    ax.set_xticklabels(uscs_labels, fontsize=10, fontweight="bold")
    ax.set_ylabel("Flujo vertical $q$ (mm/día)", fontsize=12)
    ax.set_title("Distribución del Flujo Hatch-Amplitude por Termocupla\n"
                 "Río Cuncumén — Dic 2025 a Feb 2026 — Ventanas deslizantes 48 h",
                 fontsize=13, fontweight="bold", pad=12)
    ax.axhline(y=0, color="k", linestyle="-", linewidth=0.6, alpha=0.4)
    ax.grid(True, axis="y", alpha=0.4, linewidth=0.5, color="#999999")

    legend_items = [
        mpatches.Patch(facecolor="#aaa", alpha=0.55, edgecolor="k", linewidth=0.8,
                       label="Rango IQR (Q1–Q3)"),
        plt.Line2D([0], [0], color="k", linewidth=1.8, label="Mediana"),
        plt.Line2D([0], [0], marker="D", color="w", markerfacecolor="none",
                   markeredgecolor="#1565C0", markersize=8, markeredgewidth=1.5,
                   label="Ref. MATLAB VFLUX2"),
    ]
    ax.legend(handles=legend_items, loc="upper right", frameon=True,
              framealpha=0.92, edgecolor="#ccc", fontsize=9)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(IMG_DIR / f"boxplot_hatch_amplitude_informe.{ext}",
                    dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.25)
    plt.close(fig)
    print("  ✔ Boxplot publicación")


# ══════════════════════════════════════════════════════════════════════════
# 8. SERIES TEMPORALES PUBLICACIÓN (5×1)
# ══════════════════════════════════════════════════════════════════════════
def fig_series_pub(flux_ts_results):
    """Panel 5×1 de series temporales — estilo publicación."""
    _pub_style()
    pair_dash = {"sup_int": "-", "int_inf": "--", "sup_inf": "-."}
    pair_marker = {"sup_int": "o", "int_inf": "s", "sup_inf": "^"}
    pair_label = {
        "sup_int": "Sup → Int ($z_1$–$z_2$)",
        "int_inf": "Int → Inf ($z_2$–$z_3$)",
        "sup_inf": "Sup → Inf ($z_1$–$z_3$)",
    }

    n_tcs = len(ACTIVE_TCS)
    fig, axes = plt.subplots(n_tcs, 1, figsize=(14, 3.2 * n_tcs), sharex=False)
    if n_tcs == 1:
        axes = [axes]

    for ax_idx, (ax, tc_name) in enumerate(zip(axes, ACTIVE_TCS)):
        color = TC_COLORS[tc_name]
        tp = THERMAL_PARAMS_LAB[tc_name]
        ref = MATLAB_REFERENCE.get(tc_name, {})
        for pair_name, df_flux in flux_ts_results.items():
            if tc_name not in pair_name:
                continue
            df_valid = df_flux[df_flux["quality_flag"] == 0]
            if len(df_valid) == 0:
                continue
            pt = pair_name.split("_", 1)[1]
            ax.plot(df_valid["datetime"],
                    df_valid["flux_hatch_amplitude_mm_day"],
                    linestyle=pair_dash.get(pt, "-"), color=color, alpha=0.8,
                    marker=pair_marker.get(pt, "o"), markersize=3.5, linewidth=1.2,
                    label=pair_label.get(pt, pt),
                    markeredgewidth=0.3, markeredgecolor="white")
        if ref:
            ax.axhspan(ref["min"], ref["max"], alpha=0.07, color="#555555", zorder=0)
            ax.axhline(y=ref["mean"], color="#888888", linestyle="--", linewidth=1.0,
                       alpha=0.6, zorder=1,
                       label=f'MATLAB prom: {ref["mean"]} mm/d')
        ax.axhline(y=0, color="k", linestyle="-", linewidth=0.5, alpha=0.3)
        ax.grid(True, axis="both", alpha=0.35, linewidth=0.4, color="#aaaaaa")
        ax.set_ylabel("$q$ (mm/día)", fontsize=11)
        title_str = (f"{tc_name} — {tp['USCS']} | "
                     f"$\\alpha_e$ = {tp['alpha_e']:.2e} m²/s")
        if ref:
            title_str += f" | ref MATLAB: {ref['mean']} mm/d"
        ax.set_title(title_str, fontsize=10, fontweight="bold", pad=6, loc="left")
        ax.legend(loc="upper right", fontsize=7.5, frameon=True,
                  framealpha=0.92, edgecolor="#ccc", ncol=2, handlelength=2.5)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        ax.tick_params(axis="both", labelsize=9)

    axes[-1].set_xlabel("Fecha", fontsize=11)
    fig.suptitle("Series Temporales de Flujo Hatch-Amplitude por Termocupla\n"
                 "Río Cuncumén — Monitoreo Dic 2025 – Feb 2026 — Ventanas 48 h",
                 fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(IMG_DIR / f"series_temporales_hatch_informe.{ext}",
                    dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.2)
    plt.close(fig)
    print("  ✔ Series publicación 5×1")


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════
def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    print("═" * 70)
    print(" FIGURAS 05A — Hatch-Amplitude ".center(70, "═"))
    print("═" * 70)

    # Ejecutar pipeline para obtener datos
    print("\n[0/8] Ejecutando pipeline de datos...")
    pipe.OUT_DIR.mkdir(parents=True, exist_ok=True)
    sensors = pipe.load_sensors()
    df_raw, df_aligned, _ = pipe.prepare_data(sensors)
    harmonic_results = pipe.run_harmonic_analysis(df_aligned)
    all_flux_results, _, df_results, flujos_promedio_tc = pipe.calculate_fluxes(
        df_aligned, harmonic_results)
    flux_ts_results = pipe.compute_flux_timeseries(df_aligned, df_raw)
    df_iqr = pipe.compute_iqr(flux_ts_results)
    df_ic, ic_rows = pipe.compute_reliability(all_flux_results, harmonic_results)
    df_uncertainty = pipe.compute_uncertainty(all_flux_results, harmonic_results)
    pipe.export_results(df_results, flujos_promedio_tc, df_iqr, df_ic,
                        df_uncertainty, harmonic_results)

    # Generar figuras
    print("\n[1/8] Series de temperatura...")
    fig_temperatura(df_raw)

    print("[2/8] Ajustes armónicos...")
    fig_armonicos(df_aligned, harmonic_results)

    print("[3/8] Boxplot + scatter...")
    fig_boxplot_scatter(all_flux_results)

    print("[4/8] Barras HA por TC...")
    fig_barras(all_flux_results)

    print("[5/8] Forest-plot IC 95 %...")
    fig_forest_plot()

    print("[6/8] Series flujo MATLAB...")
    fig_flux_matlab()

    print("[7/8] Boxplot publicación...")
    fig_boxplot_pub(flux_ts_results)

    print("[8/8] Series publicación...")
    fig_series_pub(flux_ts_results)

    print(f"\n✔ Todas las figuras exportadas a {IMG_DIR.relative_to(PROJECT_ROOT)}/")


if __name__ == "__main__":
    main()
