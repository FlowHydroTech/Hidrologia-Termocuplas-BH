"""
flux_timeseries.py - Cálculo de series temporales de flujo vertical VFLUX2.

Este módulo implementa el cálculo de flujo vertical usando ventanas móviles
(sliding windows) para generar una serie temporal de estimaciones de flujo
en lugar de un único valor agregado.

Autor: Cesar Godoy
Fecha: 2026-03-05
"""

import numpy as np
import pandas as pd
from pathlib import Path
from .harmonic_analysis import fit_harmonic_model
from .vflux_methods import calculate_vflux_all_methods


def calculate_flux_timeseries(
    time_array,
    temp_shallow,
    temp_deep,
    depth_shallow,
    depth_deep,
    thermal_params,
    window_hours=48,
    step_hours=12,
    min_r2=0.3,
    period_hours=24.0
):
    """
    Calcula la serie temporal de flujo vertical usando ventanas móviles.
    
    Este método implementa el enfoque VFLUX2 de Gordon et al. (2012) para
    estimar flujo en cada ventana temporal, generando una serie de estimaciones.
    
    Parameters
    ----------
    time_array : np.ndarray or pd.DatetimeIndex
        Vector de tiempo (datetime o horas desde inicio).
    temp_shallow : np.ndarray
        Serie de temperatura del sensor superficial (°C).
    temp_deep : np.ndarray
        Serie de temperatura del sensor profundo (°C).
    depth_shallow : float
        Profundidad del sensor superficial (m).
    depth_deep : float
        Profundidad del sensor profundo (m).
    thermal_params : dict
        Parámetros térmicos del sedimento:
        - 'lambda_sediment': Conductividad térmica (W/m·K)
        - 'C_sediment': Capacidad calórica volumétrica sedimento (J/m³·K)
        - 'C_water': Capacidad calórica volumétrica agua (J/m³·K)
        - 'omega': Frecuencia angular (rad/s), default 2π/86400
    window_hours : int
        Tamaño de la ventana en horas (default 48 = 2 días).
    step_hours : int
        Paso entre ventanas en horas (default 12 = cada 12h).
    min_r2 : float
        R² mínimo para considerar ajuste válido (default 0.3).
    period_hours : float
        Período del armónico a ajustar (default 24 = ciclo diario).
        
    Returns
    -------
    pd.DataFrame con columnas:
        - 'datetime': Centro de la ventana temporal
        - 'datetime_start': Inicio de la ventana
        - 'datetime_end': Fin de la ventana
        - 'flux_mccallum_mm_day': Flujo McCallum (mm/día)
        - 'flux_hatch_amplitude_mm_day': Flujo Hatch-Amplitud (mm/día)
        - 'flux_keery_mm_day': Flujo Keery (mm/día)
        - 'flux_luce_mm_day': Flujo Luce (mm/día)
        - 'A_shallow': Amplitud sensor superficial (°C)
        - 'A_deep': Amplitud sensor profundo (°C)
        - 'r2_shallow': R² ajuste superficial
        - 'r2_deep': R² ajuste profundo
        - 'quality_flag': Flag de calidad (0=válido, 1=R² bajo, 2=datos insuficientes)
    """
    # Convertir a arrays numpy
    temp_shallow = np.asarray(temp_shallow, dtype=float)
    temp_deep = np.asarray(temp_deep, dtype=float)
    
    # Manejar diferentes formatos de tiempo
    if isinstance(time_array, pd.DatetimeIndex):
        datetimes = time_array
        # Calcular horas desde inicio
        time_hours = (datetimes - datetimes[0]).total_seconds() / 3600.0
    elif isinstance(time_array, pd.Series):
        datetimes = pd.DatetimeIndex(time_array)
        time_hours = (datetimes - datetimes[0]).total_seconds() / 3600.0
    else:
        # Asumir que ya es horas
        time_hours = np.asarray(time_array, dtype=float)
        # Crear datetime sintético (cada hora)
        datetimes = pd.date_range(start='2026-01-01', periods=len(time_hours), freq='h')
    
    # Parámetros térmicos
    lambda_s = thermal_params.get('lambda_sediment', 1.8)
    Cs = thermal_params.get('C_sediment', 2.80e6)
    Cw = thermal_params.get('C_water', 4.18e6)
    omega = thermal_params.get('omega', 2 * np.pi / 86400)
    beta = thermal_params.get('beta', 0.0)
    
    # Diferencia de profundidad
    dz = abs(depth_deep - depth_shallow)
    
    # Calcular número de puntos por ventana y paso
    # Asumir muestreo regular
    if len(time_hours) > 1:
        dt_hours = np.median(np.diff(time_hours))
    else:
        dt_hours = 0.5  # Asumir 30 min si no hay suficientes datos
    
    points_per_window = int(window_hours / dt_hours)
    points_per_step = int(step_hours / dt_hours)
    
    n_data = len(time_hours)
    
    # Lista para almacenar resultados
    results = []
    
    # Iterar por ventanas
    start_idx = 0
    window_num = 0
    
    while start_idx + points_per_window <= n_data:
        end_idx = start_idx + points_per_window
        
        # Extraer ventana
        t_window = time_hours[start_idx:end_idx]
        ts_window = temp_shallow[start_idx:end_idx]
        td_window = temp_deep[start_idx:end_idx]
        dt_center = datetimes[start_idx:end_idx]
        
        # Tiempo relativo dentro de la ventana (horas desde inicio de ventana)
        t_rel = t_window - t_window[0]
        
        # Verificar datos válidos
        valid_shallow = np.sum(~np.isnan(ts_window))
        valid_deep = np.sum(~np.isnan(td_window))
        
        quality_flag = 0
        
        if valid_shallow < points_per_window * 0.7 or valid_deep < points_per_window * 0.7:
            # Datos insuficientes
            quality_flag = 2
            results.append({
                'datetime': dt_center[len(dt_center)//2],
                'datetime_start': dt_center[0],
                'datetime_end': dt_center[-1],
                'flux_mccallum_mm_day': np.nan,
                'flux_hatch_amplitude_mm_day': np.nan,
                'flux_keery_mm_day': np.nan,
                'flux_luce_mm_day': np.nan,
                'A_shallow': np.nan,
                'A_deep': np.nan,
                'r2_shallow': np.nan,
                'r2_deep': np.nan,
                'delta_phi': np.nan,
                'quality_flag': quality_flag
            })
            start_idx += points_per_step
            window_num += 1
            continue
        
        # Ajustar armónico a cada sensor
        try:
            fit_s = fit_harmonic_model(t_rel, ts_window, period_hours)
            fit_d = fit_harmonic_model(t_rel, td_window, period_hours)
            
            A_s = fit_s['amplitude']
            A_d = fit_d['amplitude']
            phi_s = fit_s['phase']
            phi_d = fit_d['phase']
            r2_s = fit_s['r_squared']
            r2_d = fit_d['r_squared']
            
            # Verificar calidad del ajuste
            if r2_s < min_r2 or r2_d < min_r2:
                quality_flag = 1
            
            # Calcular flujo con todos los métodos
            flux_result = calculate_vflux_all_methods(
                amplitude_shallow=A_s,
                amplitude_deep=A_d,
                phase_shallow=phi_s,
                phase_deep=phi_d,
                depth_difference=dz,
                thermal_conductivity=lambda_s,
                heat_capacity_sediment=Cs,
                heat_capacity_water=Cw,
                angular_frequency=omega,
                beta=beta,
                quiet=True,
            )
            
            # Desfase
            delta_phi = phi_d - phi_s
            if delta_phi < 0:
                delta_phi += 2 * np.pi
            
            results.append({
                'datetime': dt_center[len(dt_center)//2],
                'datetime_start': dt_center[0],
                'datetime_end': dt_center[-1],
                'flux_mccallum_mm_day': flux_result['flux_mm_day'].get('mccallum', np.nan),
                'flux_hatch_amplitude_mm_day': flux_result['flux_mm_day'].get('hatch_amplitude', np.nan),
                'flux_keery_mm_day': flux_result['flux_mm_day'].get('keery', np.nan),
                'flux_luce_mm_day': flux_result['flux_mm_day'].get('luce', np.nan),
                'A_shallow': A_s,
                'A_deep': A_d,
                'r2_shallow': r2_s,
                'r2_deep': r2_d,
                'delta_phi': delta_phi,
                'quality_flag': quality_flag
            })
            
        except Exception as e:
            quality_flag = 2
            results.append({
                'datetime': dt_center[len(dt_center)//2],
                'datetime_start': dt_center[0],
                'datetime_end': dt_center[-1],
                'flux_mccallum_mm_day': np.nan,
                'flux_hatch_amplitude_mm_day': np.nan,
                'flux_keery_mm_day': np.nan,
                'flux_luce_mm_day': np.nan,
                'A_shallow': np.nan,
                'A_deep': np.nan,
                'r2_shallow': np.nan,
                'r2_deep': np.nan,
                'delta_phi': np.nan,
                'quality_flag': quality_flag
            })
        
        start_idx += points_per_step
        window_num += 1
    
    # Crear DataFrame
    df_results = pd.DataFrame(results)
    
    return df_results


def export_flux_timeseries(
    df_flux,
    output_path,
    pair_name="",
    include_metadata=True
):
    """
    Exporta la serie temporal de flujo a CSV y/o Excel.
    
    Parameters
    ----------
    df_flux : pd.DataFrame
        DataFrame con serie temporal de flujo (salida de calculate_flux_timeseries).
    output_path : str or Path
        Ruta del archivo de salida (con extensión .csv o .xlsx).
    pair_name : str
        Nombre del par de sensores para incluir en el archivo.
    include_metadata : bool
        Si True, incluye metadatos en el archivo.
        
    Returns
    -------
    str : Ruta del archivo exportado.
    """
    output_path = Path(output_path)
    
    # Preparar DataFrame para exportación
    df_export = df_flux.copy()
    
    # Renombrar columnas para claridad
    column_rename = {
        'datetime': 'Fecha_Hora_Centro',
        'datetime_start': 'Inicio_Ventana',
        'datetime_end': 'Fin_Ventana',
        'flux_mccallum_mm_day': 'Flujo_McCallum_mm_dia',
        'flux_hatch_amplitude_mm_day': 'Flujo_Hatch_Amplitud_mm_dia',
        'flux_keery_mm_day': 'Flujo_Keery_mm_dia',
        'flux_luce_mm_day': 'Flujo_Luce_mm_dia',
        'A_shallow': 'Amplitud_Sup_C',
        'A_deep': 'Amplitud_Prof_C',
        'r2_shallow': 'R2_Sup',
        'r2_deep': 'R2_Prof',
        'delta_phi': 'Desfase_rad',
        'quality_flag': 'Flag_Calidad'
    }
    df_export = df_export.rename(columns=column_rename)
    
    # Agregar columna de par si se especifica
    if pair_name:
        df_export.insert(0, 'Par_Sensores', pair_name)
    
    # Exportar según extensión
    if output_path.suffix.lower() == '.xlsx':
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='Serie_Temporal_Flujo', index=False)
            
            # Hoja de metadatos
            if include_metadata:
                meta = pd.DataFrame({
                    'Campo': ['Par Sensores', 'N registros', 'Fecha inicio', 'Fecha fin',
                              'Flujo medio (mm/día)', 'Flujo mediana (mm/día)', 
                              'Registros válidos (%)', 'R² medio sup', 'R² medio prof'],
                    'Valor': [
                        pair_name,
                        len(df_export),
                        df_export['Inicio_Ventana'].min() if len(df_export) > 0 else 'N/A',
                        df_export['Fin_Ventana'].max() if len(df_export) > 0 else 'N/A',
                        df_export['Flujo_Hatch_Amplitud_mm_dia'].mean(),
                        df_export['Flujo_Hatch_Amplitud_mm_dia'].median(),
                        (df_export['Flag_Calidad'] == 0).sum() / len(df_export) * 100 if len(df_export) > 0 else 0,
                        df_export['R2_Sup'].mean(),
                        df_export['R2_Prof'].mean()
                    ]
                })
                meta.to_excel(writer, sheet_name='Metadatos', index=False)
                
    else:  # CSV
        df_export.to_csv(output_path, index=False, float_format='%.4f')
    
    return str(output_path)


def batch_calculate_flux_timeseries(
    df_temperatures,
    sensor_pairs,
    thermal_params,
    output_dir,
    window_hours=48,
    step_hours=12
):
    """
    Calcula series temporales de flujo para múltiples pares de sensores.
    
    Parameters
    ----------
    df_temperatures : pd.DataFrame
        DataFrame con datetime como índice y columnas de temperatura por sensor.
    sensor_pairs : list of dict
        Lista de pares a procesar, cada uno con:
        - 'name': Nombre del par (ej: 'TC1_sup_int')
        - 'shallow': Nombre columna sensor superficial
        - 'deep': Nombre columna sensor profundo
        - 'depth_shallow': Profundidad sensor superficial (m)
        - 'depth_deep': Profundidad sensor profundo (m)
    thermal_params : dict
        Parámetros térmicos del sedimento.
    output_dir : str or Path
        Directorio de salida para archivos.
    window_hours : int
        Tamaño de ventana en horas.
    step_hours : int
        Paso entre ventanas en horas.
        
    Returns
    -------
    dict : Diccionario con DataFrames de resultados por par.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    for pair in sensor_pairs:
        pair_name = pair['name']
        print(f"\n  Procesando par: {pair_name}")
        
        try:
            # Extraer series
            temp_shallow = df_temperatures[pair['shallow']].values
            temp_deep = df_temperatures[pair['deep']].values
            time_array = df_temperatures.index
            
            # Calcular serie temporal
            df_flux = calculate_flux_timeseries(
                time_array=time_array,
                temp_shallow=temp_shallow,
                temp_deep=temp_deep,
                depth_shallow=pair['depth_shallow'],
                depth_deep=pair['depth_deep'],
                thermal_params=thermal_params,
                window_hours=window_hours,
                step_hours=step_hours
            )
            
            # Exportar a CSV
            csv_path = output_dir / f"flujo_temporal_{pair_name}.csv"
            export_flux_timeseries(df_flux, csv_path, pair_name)
            
            # Estadísticas rápidas
            n_valid = (df_flux['quality_flag'] == 0).sum()
            flux_mean = df_flux['flux_hatch_amplitude_mm_day'].mean()
            
            print(f"    ✓ {len(df_flux)} ventanas, {n_valid} válidas")
            print(f"    ✓ Flujo medio: {flux_mean:.1f} mm/día")
            print(f"    ✓ Exportado: {csv_path.name}")
            
            results[pair_name] = df_flux
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            results[pair_name] = None
    
    # Exportar resumen consolidado
    print(f"\n  Generando resumen consolidado...")
    
    # Combinar todos los resultados
    all_results = []
    for pair_name, df_flux in results.items():
        if df_flux is not None:
            df_temp = df_flux.copy()
            df_temp.insert(0, 'par', pair_name)
            all_results.append(df_temp)
    
    if all_results:
        df_all = pd.concat(all_results, ignore_index=True)
        
        # Excel consolidado
        xlsx_path = output_dir / "series_temporales_flujo_consolidado.xlsx"
        with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
            df_all.to_excel(writer, sheet_name='Todos_los_Pares', index=False)
            
            # Una hoja por par
            for pair_name, df_flux in results.items():
                if df_flux is not None:
                    sheet_name = pair_name[:31]  # Excel limita nombres a 31 chars
                    df_flux.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"  ✓ Consolidado exportado: {xlsx_path.name}")
    
    return results
