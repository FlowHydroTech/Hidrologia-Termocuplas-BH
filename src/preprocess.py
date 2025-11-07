"""
Funciones de preprocesamiento de datos de termocuplas.
"""

import pandas as pd


def align_and_resample(df, freq="15min"):
    """
    Alinea temporalmente los 3 sensores.
    """
    df_resampled = pd.DataFrame()
    df_resampled["fecha"] = pd.date_range(df.fecha1.min(), df.fecha1.max(), freq=freq)
    df_resampled["temp1"] = df.set_index("fecha1")["temp1"].reindex(df_resampled["fecha"]).interpolate()
    df_resampled["temp2"] = df.set_index("fecha2")["temp2"].reindex(df_resampled["fecha"]).interpolate()
    df_resampled["temp3"] = df.set_index("fecha3")["temp3"].reindex(df_resampled["fecha"]).interpolate()
    return df_resampled
