"""
Funciones de preprocesamiento de datos de termocuplas.
"""

import pandas as pd
import numpy as np
from scipy.interpolate import interp1d


def align_and_resample(df, freq="15min"):
    """
    Alinea temporalmente los 3 sensores usando interpolación.
    
    Los sensores pueden tener pequeños desfases temporales (ej. 2-4 minutos).
    Esta función crea una grilla temporal común y reinterpola todas las series.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con columnas: fecha1, temp1, fecha2, temp2, fecha3, temp3
    freq : str
        Frecuencia de resampleo (default: "15min")
        
    Returns
    -------
    pd.DataFrame
        DataFrame alineado con columnas: fecha, temp1, temp2, temp3
    """
    # Crear grilla temporal común basada en el rango total
    fecha_min = min(df.fecha1.min(), df.fecha2.min(), df.fecha3.min())
    fecha_max = max(df.fecha1.max(), df.fecha2.max(), df.fecha3.max())
    
    fecha_grid = pd.date_range(fecha_min, fecha_max, freq=freq)
    
    # Crear DataFrame resultante
    df_aligned = pd.DataFrame({'fecha': fecha_grid})
    
    # Convertir fechas a timestamps numéricos para interpolación
    fecha_grid_num = fecha_grid.astype(np.int64) // 10**9  # Convertir a segundos
    
    # Interpolar cada sensor
    # Sensor 1
    fecha1_num = df['fecha1'].astype(np.int64) // 10**9
    f1 = interp1d(fecha1_num, df['temp1'], kind='linear', fill_value='extrapolate')
    df_aligned['temp1'] = f1(fecha_grid_num)
    
    # Sensor 2
    fecha2_num = df['fecha2'].astype(np.int64) // 10**9
    f2 = interp1d(fecha2_num, df['temp2'], kind='linear', fill_value='extrapolate')
    df_aligned['temp2'] = f2(fecha_grid_num)
    
    # Sensor 3
    fecha3_num = df['fecha3'].astype(np.int64) // 10**9
    f3 = interp1d(fecha3_num, df['temp3'], kind='linear', fill_value='extrapolate')
    df_aligned['temp3'] = f3(fecha_grid_num)
    
    return df_aligned
