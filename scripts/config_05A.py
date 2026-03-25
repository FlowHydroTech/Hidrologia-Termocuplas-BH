"""
Configuración compartida para el análisis 05A — Hatch-Amplitude.
Río Cuncumén / Silala — 5 Termocuplas (TC1–TC5).

Importar desde scripts con:
    from config_05A import *

Fuentes de datos:
    - Informes IDIEM N°1 (2.172.933-A) y N°2 (2.172.933-B)
    - Resultados IDIEM.xlsx (hoja "Resumen resultados")
    - Referencia MATLAB VFLUX2 (18-mar-2026)
"""

import numpy as np
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════
# RUTAS
# ══════════════════════════════════════════════════════════════════════════
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "Datos Termocuplas 25-02-2026"

# --- Salidas consolidadas bajo data/processed/ ---
RUN_ID = "resultados_20260325"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / RUN_ID
OUT_DIR = PROCESSED_DIR / "resultados"
IMG_DIR = PROCESSED_DIR / "figuras"
WEB_DIR = PROCESSED_DIR / "contenido_web"
SERIES_DIR = OUT_DIR / "series_temporales"

# Alias legacy (retrocompatibilidad temporal)
LEGACY_OUT_DIR = PROJECT_ROOT / "resultados_python" / "terreno_2026_hatch"
LEGACY_IMG_DIR = PROJECT_ROOT / "image" / "terreno_2026"

# ══════════════════════════════════════════════════════════════════════════
# MAPEO SENSOR → TC → PROFUNDIDAD
# ══════════════════════════════════════════════════════════════════════════
TC_CONFIG = {
    "TC1": {"surface": "temp_12", "intermediate": "temp_9",  "deep": "temp_8"},
    "TC2": {"surface": "temp_4",  "intermediate": "temp_6",  "deep": "temp_7"},
    "TC3": {"surface": "temp_1",  "intermediate": "temp_10", "deep": "temp_11"},
    "TC4": {"surface": "temp_15", "intermediate": "temp_3",  "deep": "temp_14"},
    "TC5": {"surface": "temp_5",  "intermediate": "temp_13", "deep": "temp_2"},
}

DEPTHS_M = {
    "temp_12": 0.00, "temp_9": 0.28, "temp_8": 0.56,   # TC1
    "temp_4":  0.00, "temp_6": 0.20, "temp_7": 0.40,   # TC2
    "temp_1":  0.00, "temp_10": 0.20, "temp_11": 0.40,  # TC3
    "temp_15": 0.00, "temp_3": 0.28, "temp_14": 0.56,   # TC4
    "temp_5":  0.00, "temp_13": 0.28, "temp_2": 0.56,   # TC5
}

TC_ASSIGNMENT = {
    "temp_8": "TC1", "temp_9": "TC1", "temp_12": "TC1",
    "temp_4": "TC2", "temp_6": "TC2", "temp_7": "TC2",
    "temp_1": "TC3", "temp_10": "TC3", "temp_11": "TC3",
    "temp_3": "TC4", "temp_14": "TC4", "temp_15": "TC4",
    "temp_2": "TC5", "temp_5": "TC5", "temp_13": "TC5",
}

ACTIVE_TCS = ["TC1", "TC2", "TC3", "TC4", "TC5"]

STATION_COORDS_UTM = {
    "TC1": {"easting": 347285, "northing": 6473381},
    "TC2": {"easting": 347440, "northing": 6473566},
    "TC3": {"easting": 347087, "northing": 6472284},
    "TC4": {"easting": 347113, "northing": 6472121},
    "TC5": {"easting": 346618, "northing": 6471135},
}

# ══════════════════════════════════════════════════════════════════════════
# PARÁMETROS TÉRMICOS — LABORATORIO IDIEM (SI)
# ══════════════════════════════════════════════════════════════════════════
THERMAL_PARAMS_LAB = {
    "TC1": {
        "lambda_sediment": 0.614,   # W/m·K
        "C_sediment": 3.389e6,      # J/m³·K
        "alpha_e": 2.03e-7,         # m²/s
        "C_water": 4.18e6,          # J/m³·K
        "omega": 2 * np.pi / 86400, # rad/s
        "density_dry": 1.10,        # g/cm³
        "K_v": 0.0026,              # m/d
        "USCS": "SP-SM",
    },
    "TC2": {
        "lambda_sediment": 0.258,
        "C_sediment": 5.333e6,
        "alpha_e": 4.90e-8,
        "C_water": 4.18e6,
        "omega": 2 * np.pi / 86400,
        "density_dry": 1.52,
        "K_v": 0.0016,
        "USCS": "SM",
    },
    "TC3": {
        "lambda_sediment": 0.265,
        "C_sediment": 4.867e6,
        "alpha_e": 5.50e-8,
        "C_water": 4.18e6,
        "omega": 2 * np.pi / 86400,
        "density_dry": 1.39,
        "K_v": 0.0058,
        "USCS": "SW-SM",
    },
    "TC4": {
        "lambda_sediment": 0.666,
        "C_sediment": 2.342e6,
        "alpha_e": 3.13e-7,
        "C_water": 4.18e6,
        "omega": 2 * np.pi / 86400,
        "density_dry": 1.37,
        "K_v": 0.778,
        "USCS": "GP-GM",
    },
    "TC5": {
        "lambda_sediment": 0.578,
        "C_sediment": 2.690e6,
        "alpha_e": 2.24e-7,
        "C_water": 4.18e6,
        "omega": 2 * np.pi / 86400,
        "density_dry": 1.22,
        "K_v": 0.0031,
        "USCS": "SW-SM",
    },
}

# ══════════════════════════════════════════════════════════════════════════
# PARÁMETROS EN UNIDADES VFLUX (compatibilidad VFLUX2/MATLAB)
# ══════════════════════════════════════════════════════════════════════════
THERMAL_PARAMS_VFLUX = {
    "TC1": {"K_cal": 0.001467, "C_cal": 0.809971, "Ce_J": 3080.9,
            "D_m2s": 2.03e-7, "rho_kg": 1100, "beta_d50": 0.080},
    "TC2": {"K_cal": 0.000617, "C_cal": 1.274587, "Ce_J": 3508.6,
            "D_m2s": 4.90e-8, "rho_kg": 1520, "beta_d50": 0.004},
    "TC3": {"K_cal": 0.000633, "C_cal": 1.163213, "Ce_J": 3501.4,
            "D_m2s": 5.50e-8, "rho_kg": 1390, "beta_d50": 0.070},
    "TC4": {"K_cal": 0.001592, "C_cal": 0.559738, "Ce_J": 1709.5,
            "D_m2s": 3.13e-7, "rho_kg": 1370, "beta_d50": 0.200},
    "TC5": {"K_cal": 0.001381, "C_cal": 0.642910, "Ce_J": 2204.9,
            "D_m2s": 2.24e-7, "rho_kg": 1220, "beta_d50": 0.035},
}

# ══════════════════════════════════════════════════════════════════════════
# FLUJO DE REFERENCIA MATLAB VFLUX2
# ══════════════════════════════════════════════════════════════════════════
MATLAB_REFERENCE = {
    "TC1": {"min": 226, "max": 342, "mean": 281},
    "TC2": {"min": 303, "max": 322, "mean": 311},
    "TC3": {"min": 1909, "max": 2722, "mean": 2246},
    "TC4": {"min": 1365, "max": 1866, "mean": 1555},
    "TC5": {"min": 138, "max": 259, "mean": 181},
}

# Períodos de registro por TC
TC_PERIODS = {
    "TC1": ("2025-12-21 16:00", "2026-02-25 12:00"),
    "TC2": ("2026-01-23 13:00", "2026-02-25 12:00"),
    "TC3": ("2026-01-23 13:00", "2026-02-25 12:00"),
    "TC4": ("2025-12-21 16:00", "2026-02-25 12:00"),
    "TC5": ("2025-12-21 16:00", "2026-02-25 12:00"),
}

# ══════════════════════════════════════════════════════════════════════════
# COLORES Y ESTILOS
# ══════════════════════════════════════════════════════════════════════════
TC_COLORS = {
    "TC1": "#1f77b4", "TC2": "#ff7f0e", "TC3": "#2ca02c",
    "TC4": "#9467bd", "TC5": "#d62728",
}

PAIR_MAP = {
    "sup_int": ("surface", "intermediate"),
    "int_inf": ("intermediate", "deep"),
    "sup_inf": ("surface", "deep"),
}

PAIR_LABELS = {
    "sup_int": "Sup → Int (z₁–z₂)",
    "int_inf": "Int → Inf (z₂–z₃)",
    "sup_inf": "Sup → Inf (z₁–z₃)",
}

PAIR_COLORS_MATLAB = {
    "sup_int": "#0072BD",
    "int_inf": "#D95319",
    "sup_inf": "#EDB120",
}

# Mapeo sensor_mappings para carga de Excel
SENSOR_MAPPINGS = {
    "tc1": ("tc1/datos_filtrados_tc1.xlsx", [
        ("A400000082BAF041", "temp1", "fecha1", "DS1923"),
        ("7D000000828FA841", "temp2", "fecha2", "DS1922L"),
        ("5900000082B86A41", "temp3", "fecha3", "DS1923"),
    ]),
    "tc2": ("tc2/datos_filtrados_tc2.xlsx", [
        ("2E000000828FF441", "temp1", "fecha1", "DS1922L"),
        ("4600000082991C41", "temp2", "fecha2", "DS1922L"),
        ("4B0000008298EA41", "temp3", "fecha3", "DS1922L"),
    ]),
    "tc3": ("tc3/datos_filtrados_tc3.xlsx", [
        ("0600000082994E41", "temp1", "fecha1", "DS1922L"),
        ("870000008290BE41", "temp2", "fecha2", "DS1922L"),
        ("98000000828FD441", "temp3", "fecha3", "DS1922L"),
    ]),
    "tc4": ("tc4/datos_filtrados_tc4.xlsx", [
        ("F60000008290D841", "temp1", "fecha1", "DS1922L"),
        ("2D00000082925E41", "temp2", "fecha2", "DS1922L"),
        ("B3000000828F2741", "temp3", "fecha3", "DS1922L"),
    ]),
    "tc5": ("tc5/datos_filtrados_tc5.xlsx", [
        ("3800000082952A41", "temp1", "fecha1", "DS1922L"),
        ("B000000082987741", "temp2", "fecha2", "DS1922L"),
        ("2800000082978041", "temp3", "fecha3", "DS1922L"),
    ]),
}

# Incertidumbres de laboratorio (equipo KD2 PRO / IDIEM)
UNCERTAINTIES_LAB = {
    "lambda": 0.10,
    "C_sed": 0.10,
    "alpha_e": 0.08,
    "dz": 0.005 / 0.28,
    "harmonic": 0.10,
}

# Parámetros de ventana deslizante
WINDOW_HOURS = 48
STEP_HOURS = 12
