#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Etapa 1 — Carga de datos Excel (5 TCs, 15 sensores iButton).
Río Cuncumén / Silala.
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd
from prefect import task
from config_05A import DATA_DIR, SENSOR_MAPPINGS


@task(
    name="cargar-datos-termocuplas",
    description="Carga 15 sensores iButton desde archivos Excel filtrados (5 TCs).",
    tags=["datos", "carga", "rio-cuncumen"],
)
def cargar_datos() -> list[dict]:
    """Carga los 15 sensores iButton desde archivos Excel filtrados."""
    sensors: list[dict] = []
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


if __name__ == "__main__":
    data = cargar_datos.fn()
    print(f"OK — {len(data)} sensores")
