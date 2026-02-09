import numpy as np
import scipy.io
import pandas as pd
from pathlib import Path
import re
import glob


# ================================================================
# CARGA DE DATOS - MATLAB (.mat)
# ================================================================

def load_matlab_data(path):
    """
    Carga un archivo .mat y detecta automáticamente la estructura del dataset.
    Compatible con:
        - time + temps
        - site12_data
        - data / DATA / dataset
        - cualquier matriz NxM donde col0 = tiempo y resto = temperaturas
    """

    mat = scipy.io.loadmat(path)

    # === 1) Formato estándar: time + temps ===
    if "time" in mat and "temps" in mat:
        time = np.squeeze(mat["time"])
        temps = mat["temps"]
        print("✔ Detectado formato: time + temps")
        return time, temps

    # === 2) Formatos tipo MATLAB originales (site12_data, data, DATA…) ===
    candidate_keys = ["site12_data", "data", "DATA", "dataset"]

    for key in candidate_keys:
        if key in mat:
            raw = np.array(mat[key])
            print(f"✔ Detectado dataset matriz: '{key}' con forma {raw.shape}")

            time = np.squeeze(raw[:, 0])
            temps = raw[:, 1:]
            return time, temps

    # === 3) Cualquier matriz NxM válida ===
    for k, v in mat.items():
        if isinstance(v, np.ndarray) and v.ndim == 2 and v.shape[1] >= 2:
            print(f"✔ Detectada matriz válida '{k}'. Usando col0=tiempo, resto=temperaturas.")
            raw = v
            time = np.squeeze(raw[:, 0])
            temps = raw[:, 1:]
            return time, temps

    # Ningún formato válido
    raise ValueError(
        f"No se encontraron variables válidas en el archivo .mat.\n"
        f"Variables disponibles: {list(mat.keys())}"
    )


# ================================================================
# CARGA DE DATOS - iButton CSV (DS1922L / DS1923)
# ================================================================

def load_ibutton_csv(filepath):
    """
    Carga un archivo CSV exportado desde un datalogger iButton (DS1922L/DS1923).

    El formato tiene un encabezado con metadatos y luego datos tabulares:
        Date/Time,Unit,Value
        20-12-25 9:45:01,C,20,765   (<-- decimales con coma europea)

    Parameters
    ----------
    filepath : str or Path
        Ruta al archivo CSV.

    Returns
    -------
    dict con:
        'df': DataFrame con columnas ['datetime', 'temperature']
        'metadata': dict con info del sensor (part_number, registration, sample_rate, etc.)
    """
    filepath = Path(filepath)
    metadata = {}
    data_start_line = None

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f):
            line_stripped = line.strip()
            # Buscar inicio de datos
            if line_stripped.startswith("Date/Time,Unit,Value"):
                data_start_line = i + 1
                continue
            # Parsear metadatos del header
            if ':' in line_stripped and data_start_line is None:
                parts = line_stripped.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().replace('?', '').replace('1-Wire/iButton ', '')
                    val = parts[1].strip()
                    metadata[key] = val

    if data_start_line is None:
        raise ValueError(f"No se encontró la línea 'Date/Time,Unit,Value' en {filepath.name}")

    # Leer datos: manejar el formato donde el valor decimal usa coma
    # Ej: "20-12-25 9:45:01,C,20,765" -> date="20-12-25 9:45:01", unit="C", value="20,765"->20.765
    rows = []
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    for line in lines[data_start_line:]:
        line = line.strip()
        if not line:
            continue
        # Formato: "DD-MM-YY H:MM:SS,C,NN,DDD"
        # Split por coma: [fecha, unidad, parte_entera, parte_decimal]
        parts = line.split(',')
        if len(parts) < 3:
            continue
        datetime_str = parts[0].strip()
        # unit = parts[1].strip()  # siempre "C"
        # El valor puede ser "20,765" -> parts[2]="20" y parts[3]="765"
        if len(parts) == 4:
            temp_str = parts[2].strip() + '.' + parts[3].strip()
        elif len(parts) == 3:
            temp_str = parts[2].strip()
        else:
            continue

        try:
            temperature = float(temp_str)
        except ValueError:
            continue

        # Parsear fecha: "DD-MM-YY H:MM:SS" o "DD-MM-YY HH:MM:SS"
        try:
            dt = pd.to_datetime(datetime_str, format='%d-%m-%y %H:%M:%S')
        except Exception:
            try:
                dt = pd.to_datetime(datetime_str, dayfirst=True)
            except Exception:
                continue

        rows.append({'datetime': dt, 'temperature': temperature})

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError(f"No se pudieron leer datos de temperatura de {filepath.name}")

    df = df.sort_values('datetime').reset_index(drop=True)

    sensor_id = metadata.get('Registration Number', filepath.stem)
    part_number = metadata.get('Part Number', 'Unknown')
    sample_rate = metadata.get('Sample Rate', 'Unknown')

    print(f"  ✔ {filepath.name}: {part_number} | {len(df)} registros | "
          f"{df['datetime'].min().strftime('%Y-%m-%d')} → {df['datetime'].max().strftime('%Y-%m-%d')} | "
          f"T: [{df['temperature'].min():.1f}, {df['temperature'].max():.1f}] °C")

    return {
        'df': df,
        'metadata': metadata,
        'sensor_id': sensor_id,
        'part_number': part_number,
        'sample_rate': sample_rate
    }


def load_all_ibuttons(directory, pattern="*.csv"):
    """
    Carga todos los archivos iButton CSV de un directorio.

    Parameters
    ----------
    directory : str or Path
        Carpeta con los archivos CSV.
    pattern : str
        Patrón glob para filtrar archivos.

    Returns
    -------
    list[dict] : Lista de diccionarios, cada uno con 'df', 'metadata', 'sensor_id', etc.
                 Ordenados por fecha de inicio de misión.
    """
    directory = Path(directory)
    files = sorted(directory.glob(pattern))

    if not files:
        raise FileNotFoundError(f"No se encontraron archivos {pattern} en {directory}")

    print(f"Cargando {len(files)} archivos iButton desde {directory.name}/")
    print("=" * 80)

    sensors = []
    for f in files:
        try:
            result = load_ibutton_csv(f)
            sensors.append(result)
        except Exception as e:
            print(f"  ✗ Error al leer {f.name}: {e}")

    print("=" * 80)
    print(f"Sensores cargados exitosamente: {len(sensors)}/{len(files)}")
    return sensors


def ibuttons_to_dataframe(sensors, sensor_labels=None):
    """
    Combina múltiples sensores iButton en un único DataFrame alineado temporalmente.

    Parameters
    ----------
    sensors : list[dict]
        Lista de diccionarios de load_ibutton_csv / load_all_ibuttons.
    sensor_labels : list[str], optional
        Nombres para cada sensor. Si None, usa 'temp_1', 'temp_2', etc.

    Returns
    -------
    df : pd.DataFrame
        DataFrame con columna 'fecha' y una columna de temperatura por sensor.
    """
    if sensor_labels is None:
        sensor_labels = [f'temp_{i+1}' for i in range(len(sensors))]

    if len(sensor_labels) != len(sensors):
        raise ValueError(f"sensor_labels ({len(sensor_labels)}) != sensores ({len(sensors)})")

    # Merge all on datetime
    df_merged = None
    for i, (sensor, label) in enumerate(zip(sensors, sensor_labels)):
        df_s = sensor['df'][['datetime', 'temperature']].copy()
        df_s = df_s.rename(columns={'temperature': label, 'datetime': 'fecha'})
        df_s = df_s.set_index('fecha')

        if df_merged is None:
            df_merged = df_s
        else:
            df_merged = df_merged.join(df_s, how='outer')

    df_merged = df_merged.sort_index().reset_index()
    return df_merged


def load_termocuplas_excel(path):
    """
    Carga datos de termocuplas desde un archivo Excel.

    Parameters
    ----------
    path : str or Path
        Ruta al archivo .xlsx con datos de temperatura.
        Se espera que tenga columnas: 'fecha', 'temp1', 'temp2', ... (o similar).

    Returns
    -------
    df : pd.DataFrame
        DataFrame con columna 'fecha' (datetime) y columnas de temperatura.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    df = pd.read_excel(path)

    # Detectar columna de fecha
    date_cols = [c for c in df.columns if 'fecha' in c.lower() or 'date' in c.lower() or 'time' in c.lower()]
    if date_cols:
        df = df.rename(columns={date_cols[0]: 'fecha'})
    elif df.columns[0] not in ['fecha']:
        df = df.rename(columns={df.columns[0]: 'fecha'})

    df['fecha'] = pd.to_datetime(df['fecha'])
    df = df.sort_values('fecha').reset_index(drop=True)

    temp_cols = [c for c in df.columns if c != 'fecha']
    print(f"✔ Cargado {path.name}: {len(df)} registros, {len(temp_cols)} sensores")
    print(f"  Periodo: {df['fecha'].min()} → {df['fecha'].max()}")

    return df


# ================================================================
# EXPORTAR RESULTADOS
# ================================================================

def save_results(df_resampled, spectrum, freqs, flux, sensitivity, out_dir):
    """
    Save results to CSV and log files.
    """
    Path(out_dir).mkdir(exist_ok=True)
    df_resampled.to_csv(f"{out_dir}/temperaturas_remuestreadas_python.csv", index=False)
    pd.DataFrame({'freq': freqs, 'amplitude': spectrum}).to_csv(f"{out_dir}/espectro_AR12_python.csv", index=False)
    pd.DataFrame({'flux': [flux]}).to_csv(f"{out_dir}/flujo_estimado_python.csv", index=False)
    pd.DataFrame({'sensitivity': [sensitivity]}).to_csv(f"{out_dir}/sensibilidad_flujo_python.csv", index=False)
    with open(f"{out_dir}/log_python.txt", "w") as f:
        f.write("Exportación completada correctamente.\n")
