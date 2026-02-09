import pandas as pd
import numpy as np

def build_dataframe(time, temps):
    """
    Build DataFrame from time and temperature arrays.

    Parameters
    ----------
    time : np.ndarray
        Array of timestamps.
    temps : np.ndarray
        Array of temperature values.

    Returns
    -------
    df : pandas.DataFrame
        DataFrame with time and temperatures.
    """
    # Auditoría de forma
    time = np.squeeze(time)
    temps = np.squeeze(temps)
    if time.ndim != 1 or temps.ndim != 1:
        raise ValueError(f"Las variables deben ser 1D. time shape: {time.shape}, temps shape: {temps.shape}")
    if time.shape[0] != temps.shape[0]:
        raise ValueError(f"Dimensiones incompatibles: time ({time.shape[0]}) vs temps ({temps.shape[0]})")
    df = pd.DataFrame({'time': time, 'temperature': temps})
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)
    return df

def resample_temperatures(df, freq='15min'):
    """
    Resample temperature data to specified frequency, interpolate gaps.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with time and temperature.
    freq : str
        Resampling frequency (default '15min').

    Returns
    -------
    df_resampled : pandas.DataFrame
        Resampled and interpolated DataFrame.
    """
    df = df.set_index('time')
    df_resampled = df.resample(freq).mean()
    df_resampled['temperature'] = df_resampled['temperature'].interpolate(method='linear')
    df_resampled = df_resampled.reset_index()
    return df_resampled


def align_and_resample(df, freq='30min'):
    """
    Alinea múltiples series de temperatura a un eje temporal común y regular.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con columna 'fecha' (datetime) y columnas de temperatura
        (ej: 'temp_1', 'temp_2', ..., 'temp1', 'temp2', etc.).
    freq : str
        Frecuencia de remuestreo (default '30min'). Formatos pandas válidos:
        '15min', '30min', '1h', etc.

    Returns
    -------
    df_aligned : pd.DataFrame
        DataFrame remuestreado con 'fecha' como columna y temperaturas interpoladas.
    """
    # Detectar columna de fecha
    date_col = None
    for c in df.columns:
        if c.lower() in ['fecha', 'date', 'datetime', 'time', 'timestamp']:
            date_col = c
            break
    if date_col is None:
        date_col = df.columns[0]

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col)

    # Solo columnas numéricas (temperaturas)
    temp_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # Remuestrear a frecuencia regular
    df_resampled = df[temp_cols].resample(freq).mean()

    # Interpolar gaps (máximo 4 periodos consecutivos)
    max_gap = 4
    df_resampled = df_resampled.interpolate(method='linear', limit=max_gap)

    # Eliminar filas donde todos los sensores son NaN
    df_resampled = df_resampled.dropna(how='all')

    df_resampled = df_resampled.reset_index()
    df_resampled = df_resampled.rename(columns={df_resampled.columns[0]: 'fecha'})

    n_original = len(df)
    n_resampled = len(df_resampled)
    n_sensores = len(temp_cols)
    n_nan = df_resampled[temp_cols].isna().sum().sum()

    print(f"✔ Alineación temporal completada:")
    print(f"  • Registros: {n_original} → {n_resampled} (freq={freq})")
    print(f"  • Sensores: {n_sensores}")
    print(f"  • Periodo: {df_resampled['fecha'].min()} → {df_resampled['fecha'].max()}")
    print(f"  • Valores NaN restantes: {n_nan}")

    return df_resampled
