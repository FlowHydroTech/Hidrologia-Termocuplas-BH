#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Etapa 2 — Alineación temporal y remuestreo a 30 min.
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd
from prefect import task
from vfluxx.io_utils import ibuttons_to_dataframe
from vfluxx.preprocess import align_and_resample


@task(
    name="alineacion-temporal-30min",
    description="Alinea y remuestrea los 15 sensores a intervalos de 30 minutos.",
    tags=["preprocesamiento", "rio-cuncumen"],
)
def alinear_datos(sensors: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Alinea y remuestrea a 30 min."""
    sensor_labels = [f"temp_{i+1}" for i in range(len(sensors))]
    df_raw = ibuttons_to_dataframe(sensors, sensor_labels=sensor_labels)
    df_aligned = align_and_resample(df_raw, freq="30min")
    print(f"  {len(df_aligned)} registros × {len(df_aligned.columns)} columnas")
    return df_raw, df_aligned, sensor_labels


if __name__ == "__main__":
    from stage_01_carga import cargar_datos
    sensors = cargar_datos.fn()
    df_raw, df_aligned, labels = alinear_datos.fn(sensors)
    print(f"OK — {len(df_aligned)} registros, {len(labels)} sensores")
