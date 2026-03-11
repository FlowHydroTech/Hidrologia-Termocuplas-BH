#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VFLUX2 Python - Script Principal para Análisis de Flujo Vertical
================================================================

Proyecto: Hidrología Río Silala - Termocuplas
Fecha: Marzo 2026
Autor: Equipo de Hidrología

Este script ejecuta el pipeline completo de análisis VFLUX2:
1. Carga de datos de termocuplas
2. Análisis armónico
3. Cálculo de flujo por 5 métodos
4. Generación de gráficos
5. Exportación a Excel

Uso:
    python main.py
"""

import sys
import io

# Configurar stdout para UTF-8 en Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configurar path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Importar módulos VFLUX2
try:
    from vfluxx.vflux_methods import calculate_vflux_all_methods
    from vfluxx.harmonic_analysis import fit_harmonic_model, analyze_sensor_pair
    print("✅ Módulos VFLUX2 cargados correctamente")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("   Ejecute: pip install -e .")
    sys.exit(1)


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Parámetros térmicos (calibrados para Río Silala)
THERMAL_PARAMS = {
    'thermal_conductivity': 1.80,      # W/m·K
    'heat_capacity_sediment': 2.8e6,   # J/m³·K
    'heat_capacity_water': 4.18e6,     # J/m³·K
    'angular_frequency': 2 * np.pi / 86400.0  # rad/s (ciclo diario)
}

# Configuración de termocuplas (ACTUALIZADO 11-MAR-2026: 5 termocuplas)
# TC1, TC4, TC5: 65 días de datos (21 Dic 2025 - 25 Feb 2026)
# TC2, TC3: 32 días de datos (23 Ene 2026 - 25 Feb 2026)
TC_CONFIG = {
    'TC1': {'depths_m': [0.00, 0.28, 0.56], 'active': True},   # 65 días
    'TC2': {'depths_m': [0.00, 0.20, 0.40], 'active': True},   # 32 días
    'TC3': {'depths_m': [0.00, 0.20, 0.40], 'active': True},   # 32 días
    'TC4': {'depths_m': [0.00, 0.28, 0.56], 'active': True},   # 65 días
    'TC5': {'depths_m': [0.00, 0.28, 0.56], 'active': True}    # 65 días
}

# Directorios
DATA_DIR = PROJECT_ROOT / 'data' / 'Datos Termocuplas 25-02-2026'
OUTPUT_DIR = PROJECT_ROOT / 'resultados_python' / 'datos_terreno'
FIGS_DIR = OUTPUT_DIR / 'figuras'
SERIES_DIR = OUTPUT_DIR / 'series_temporales'


def setup_directories():
    """Crear directorios de salida si no existen."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGS_DIR.mkdir(exist_ok=True)
    SERIES_DIR.mkdir(exist_ok=True)
    print(f"📁 Directorio de salida: {OUTPUT_DIR}")


def load_tc_data(tc_name: str) -> pd.DataFrame:
    """Cargar datos de una termocupla específica."""
    tc_dir = DATA_DIR / tc_name.lower()
    xlsx_file = tc_dir / f'datos_filtrados_{tc_name.lower()}.xlsx'
    
    if not xlsx_file.exists():
        print(f"⚠️ Archivo no encontrado: {xlsx_file}")
        return None
    
    df = pd.read_excel(xlsx_file)
    print(f"  📊 {tc_name}: {len(df)} registros cargados")
    return df


def process_sensor_pair(df: pd.DataFrame, tc_name: str, 
                        shallow_col: str, deep_col: str,
                        depth_shallow: float, depth_deep: float) -> dict:
    """Procesar un par de sensores y calcular flujo."""
    
    # Extraer series de temperatura
    temp_shallow = df[shallow_col].values
    temp_deep = df[deep_col].values
    
    # Crear vector de tiempo en horas (asumiendo 30 min entre datos)
    time_hours = np.arange(len(temp_shallow)) * 0.5
    
    # Análisis armónico
    result_shallow = fit_harmonic_model(time_hours, temp_shallow, period_hours=24.0)
    result_deep = fit_harmonic_model(time_hours, temp_deep, period_hours=24.0)
    
    if result_shallow is None or result_deep is None:
        return None
    
    # Parámetros para VFLUX
    params = {
        'amplitude_shallow': result_shallow['amplitude'],
        'amplitude_deep': result_deep['amplitude'],
        'phase_shallow': result_shallow['phase'],
        'phase_deep': result_deep['phase'],
        'depth_difference': abs(depth_deep - depth_shallow),
        **THERMAL_PARAMS
    }
    
    # Calcular flujo
    flux_result = calculate_vflux_all_methods(**params)
    
    return {
        'tc': tc_name,
        'pair': f"{shallow_col}-{deep_col}",
        'depth_shallow': depth_shallow,
        'depth_deep': depth_deep,
        'dz': params['depth_difference'],
        'A_shallow': params['amplitude_shallow'],
        'A_deep': params['amplitude_deep'],
        'R2_shallow': result_shallow.get('r_squared', np.nan),
        'R2_deep': result_deep.get('r_squared', np.nan),
        'flux_mccallum': flux_result['flux_mm_day']['mccallum'],
        'flux_hatch_amp': flux_result['flux_mm_day']['hatch_amplitude'],
        'flux_hatch_phase': flux_result['flux_mm_day']['hatch_phase'],
        'flux_keery': flux_result['flux_mm_day']['keery'],
        'flux_luce': flux_result['flux_mm_day']['luce']
    }


def generate_summary_plot(df_results: pd.DataFrame):
    """Generar gráfico resumen de flujos por método."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Gráfico 1: Barras por método
    methods = ['flux_mccallum', 'flux_hatch_amp', 'flux_keery', 'flux_luce']
    method_labels = ['McCallum', 'Hatch-Amp', 'Keery', 'Luce']
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6']
    
    means = [df_results[m].mean() for m in methods]
    stds = [df_results[m].std() for m in methods]
    
    ax1 = axes[0]
    bars = ax1.bar(method_labels, means, color=colors, edgecolor='black', alpha=0.8)
    ax1.errorbar(method_labels, means, yerr=stds, fmt='none', color='black', capsize=5)
    ax1.set_ylabel('Flujo (mm/día)')
    ax1.set_title('Flujo Promedio por Método VFLUX2')
    ax1.axhline(y=78, color='red', linestyle='--', label='Referencia DGA')
    ax1.legend()
    
    # Gráfico 2: Boxplot por TC (5 termocuplas)
    ax2 = axes[1]
    tc_list = sorted(df_results['tc'].unique())
    data_by_tc = [df_results[df_results['tc'] == tc]['flux_mccallum'].values for tc in tc_list]
    bp = ax2.boxplot(data_by_tc, labels=tc_list, patch_artist=True)
    tc_colors = ['#3498db', '#ff7f0e', '#2ecc71', '#9467bd', '#d62728']  # 5 colores
    for patch, color in zip(bp['boxes'], tc_colors[:len(bp['boxes'])]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax2.set_ylabel('Flujo McCallum (mm/día)')
    ax2.set_title('Distribución de Flujo por Estación (TC1-TC5)')
    
    plt.tight_layout()
    fig_path = FIGS_DIR / 'resumen_flujos_reunion.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  📈 Gráfico guardado: {fig_path.name}")


def export_to_excel(df_results: pd.DataFrame):
    """Exportar resultados a Excel con formato."""
    excel_path = OUTPUT_DIR / 'resumen_reunion_marzo2026.xlsx'
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Hoja 1: Resumen
        df_results.to_excel(writer, sheet_name='Resultados_Detalle', index=False)
        
        # Hoja 2: Estadísticas
        stats = df_results.groupby('tc').agg({
            'flux_mccallum': ['mean', 'std', 'min', 'max'],
            'flux_hatch_amp': ['mean', 'std'],
            'R2_shallow': 'mean'
        }).round(2)
        stats.to_excel(writer, sheet_name='Estadisticas_TC')
        
        # Hoja 3: Resumen por método
        method_stats = pd.DataFrame({
            'Método': ['McCallum', 'Hatch-Amplitud', 'Hatch-Fase', 'Keery', 'Luce'],
            'Media (mm/d)': [
                df_results['flux_mccallum'].mean(),
                df_results['flux_hatch_amp'].mean(),
                df_results['flux_hatch_phase'].mean(),
                df_results['flux_keery'].mean(),
                df_results['flux_luce'].mean()
            ],
            'Std (mm/d)': [
                df_results['flux_mccallum'].std(),
                df_results['flux_hatch_amp'].std(),
                df_results['flux_hatch_phase'].std(),
                df_results['flux_keery'].std(),
                df_results['flux_luce'].std()
            ]
        }).round(2)
        method_stats.to_excel(writer, sheet_name='Resumen_Metodos', index=False)
    
    print(f"  📊 Excel guardado: {excel_path.name}")
    return excel_path


def main():
    """Función principal del pipeline VFLUX2."""
    print("\n" + "="*60)
    print("   VFLUX2 PYTHON - ANÁLISIS DE FLUJO VERTICAL")
    print("   Proyecto Río Silala - Marzo 2026")
    print("="*60 + "\n")
    
    # Setup
    setup_directories()
    
    # Procesar cada termocupla
    all_results = []
    
    for tc_name, config in TC_CONFIG.items():
        if not config['active']:
            continue
            
        print(f"\n🔬 Procesando {tc_name}...")
        
        # Cargar datos
        df = load_tc_data(tc_name)
        if df is None:
            continue
        
        # Procesar pares de sensores
        depths = config['depths_m']
        cols = [c for c in df.columns if 'temp' in c.lower()]
        
        if len(cols) >= 3 and len(depths) >= 3:
            # Par superficie-intermedio
            result = process_sensor_pair(df, tc_name, cols[0], cols[1], depths[0], depths[1])
            if result:
                all_results.append(result)
            
            # Par superficie-inferior
            result = process_sensor_pair(df, tc_name, cols[0], cols[2], depths[0], depths[2])
            if result:
                all_results.append(result)
            
            # Par intermedio-inferior
            result = process_sensor_pair(df, tc_name, cols[1], cols[2], depths[1], depths[2])
            if result:
                all_results.append(result)
    
    # Crear DataFrame de resultados
    if not all_results:
        print("\n❌ No se obtuvieron resultados. Verifique los datos de entrada.")
        return
    
    df_results = pd.DataFrame(all_results)
    
    # Generar salidas
    print("\n📤 Generando salidas...")
    
    # Gráficos
    generate_summary_plot(df_results)
    
    # Excel
    excel_path = export_to_excel(df_results)
    
    # Resumen en consola
    print("\n" + "="*60)
    print("   RESUMEN DE RESULTADOS")
    print("="*60)
    print(f"\n  Pares procesados: {len(df_results)}")
    print(f"  Flujo McCallum promedio: {df_results['flux_mccallum'].mean():.1f} ± {df_results['flux_mccallum'].std():.1f} mm/día")
    print(f"  R² promedio (superficie): {df_results['R2_shallow'].mean():.3f}")
    
    print("\n  📁 Archivos generados:")
    print(f"     - {FIGS_DIR / 'resumen_flujos_reunion.png'}")
    print(f"     - {excel_path}")
    
    print("\n✅ Pipeline VFLUX2 completado exitosamente")
    print("="*60 + "\n")
    
    return df_results


if __name__ == "__main__":
    results = main()
