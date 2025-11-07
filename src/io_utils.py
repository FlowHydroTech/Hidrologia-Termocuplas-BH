"""
Utilidades para entrada/salida de datos.
"""

import pandas as pd


def load_termocuplas_excel(path):
    """
    Carga archivo Excel con columnas:
    fecha1, temp1, fecha2, temp2, fecha3, temp3
    """
    df = pd.read_excel(path)
    df["fecha1"] = pd.to_datetime(df["fecha1"])
    df["fecha2"] = pd.to_datetime(df["fecha2"])
    df["fecha3"] = pd.to_datetime(df["fecha3"])
    return df
