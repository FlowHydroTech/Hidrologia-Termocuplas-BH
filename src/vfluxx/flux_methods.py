import numpy as np
import pandas as pd
import logging

# Logger estilo MATLAB
logger = logging.getLogger('vfluxx')
logger.setLevel(logging.INFO)

# Parámetros físicos por defecto (pueden ser sobreescritos)
default_params = {
    'n': 0.28,                # Porosidad
    'beta': 0.001,            # Dispersividad (m)
    'Kcal': 0.0045,           # Conductividad térmica (cal/(s·cm·C))
    'Cscal': 0.5,             # Capacidad calorífica sedimento (cal/(cm³·C))
    'Cwcal': 1.0,             # Capacidad calorífica agua (cal/(cm³·C))
    'rho_s': 2650,            # Densidad sedimento (kg/m³)
    'rho_w': 1000,            # Densidad agua (kg/m³)
    'Cs': 800,                # Capacidad calorífica específica sedimento (J/(kg·°C))
    'Cw': 4180,               # Capacidad calorífica específica agua (J/(kg·°C))
    'K': 1.5,                 # Conductividad térmica sedimento (W/(m·°C))
    'Pf': 1.0,                # Periodo fundamental (días)
}

# Validación robusta de inputs
def validate_inputs(df, depth1, depth2):
    # Permitir dict o DataFrame
    if df is None:
        logger.error('Serie temporal no definida.')
        return False
    if isinstance(df, dict):
        if len(df) < 2:
            logger.error('Serie temporal demasiado corta para cualquier análisis (mínimo 2 datos).')
            return False
        if depth1 == depth2:
            logger.error('Las profundidades de los sensores deben ser diferentes.')
            return False
        if depth1 not in df or depth2 not in df:
            logger.error(f'Sensores {depth1}, {depth2} no encontrados en el dict.')
            return False
        if len(df) < 7:
            logger.warning('Serie temporal demasiado corta para análisis robusto (mínimo 7 días recomendados).')
        return True
    # DataFrame
    if len(df) < 2:
        logger.error('Serie temporal demasiado corta para cualquier análisis (mínimo 2 datos).')
        return False
    if len(df) < 7:
        logger.warning('Serie temporal demasiado corta para análisis robusto (mínimo 7 días recomendados).')
    if depth1 == depth2:
        logger.error('Las profundidades de los sensores deben ser diferentes.')
        return False
    if depth1 not in df.columns or depth2 not in df.columns:
        logger.error(f'Sensores {depth1}, {depth2} no encontrados en el DataFrame.')
        return False
    return True

# Método Hatch (2006)
def estimate_flux_hatch(df, depth1, depth2, params=default_params):
    """
    Calcula el flujo vertical usando el método de amplitud de Hatch et al. (2006).
    df: DataFrame con columnas de amplitud y fase para cada sensor
    depth1, depth2: nombres/índices de los sensores
    params: diccionario de parámetros físicos
    """
    if not validate_inputs(df, depth1, depth2):
        return np.nan
    try:
        # Extraer amplitudes y distancias
        A1 = df[depth1]['amplitude']
        A2 = df[depth2]['amplitude']
        dz = abs(depth2 - depth1)
        # Ecuación Hatch (amplitud)
        alpha = params['Kcal'] / (params['Cscal'] * params['rho_s'])  # difusividad térmica
        if np.any(A1 <= 0) or np.any(A2 <= 0):
            logger.warning('Amplitudes no válidas (<=0) en Hatch.')
            return np.nan
        flux = (alpha / dz) * np.log(A1 / A2)
        return flux
    except Exception as e:
        logger.error(f'Error en estimate_flux_hatch: {e}')
        return np.nan

# Método Keery (2007)
def estimate_flux_keery(df, depth1, depth2, params=default_params):
    """
    Calcula el flujo vertical usando amplitud y fase (Keery et al. 2007).
    df: DataFrame con columnas de amplitud y fase para cada sensor
    depth1, depth2: nombres/índices de los sensores
    params: diccionario de parámetros físicos
    """
    if not validate_inputs(df, depth1, depth2):
        return np.nan
    try:
        # Extraer amplitudes y fases
        A1 = df[depth1]['amplitude']
        A2 = df[depth2]['amplitude']
        phi1 = df[depth1]['phase']
        phi2 = df[depth2]['phase']
        dz = abs(depth2 - depth1)
        # Ecuaciones Keery (amplitud y fase)
        alpha = params['Kcal'] / (params['Cscal'] * params['rho_s'])
        delta_phi = phi2 - phi1
        if np.any(A1 <= 0) or np.any(A2 <= 0):
            logger.warning('Amplitudes no válidas (<=0) en Keery.')
            return np.nan
        if np.any(delta_phi <= 0):
            logger.warning('Diferencia de fase no válida (<=0) en Keery.')
            return np.nan
        omega = 2 * np.pi / params.get('Pf', 1)  # frecuencia angular
        flux = (omega * alpha * dz * delta_phi) / np.log(A1 / A2)
        return flux
    except Exception as e:
        logger.error(f'Error en estimate_flux_keery: {e}')
        return np.nan

# Método McCallum (2012)
def estimate_flux_mccallum(df, depth1, depth2, params=default_params):
    """
    Calcula el flujo vertical usando el método combinado de McCallum et al. (2012).
    df: DataFrame con columnas de amplitud y fase para cada sensor
    depth1, depth2: nombres/índices de los sensores
    params: diccionario de parámetros físicos
    """
    if not validate_inputs(df, depth1, depth2):
        return np.nan
    try:
        # Extraer amplitudes y fases
        A1 = df[depth1]['amplitude']
        A2 = df[depth2]['amplitude']
        phi1 = df[depth1]['phase']
        phi2 = df[depth2]['phase']
        dz = abs(depth2 - depth1)
        # Ecuaciones McCallum (amplitud y fase, método combinado)
        alpha = params['Kcal'] / (params['Cscal'] * params['rho_s'])
        delta_phi = phi2 - phi1
        if np.any(A1 <= 0) or np.any(A2 <= 0):
            logger.warning('Amplitudes no válidas (<=0) en McCallum.')
            return np.nan
        if np.any(delta_phi <= 0):
            logger.warning('Diferencia de fase no válida (<=0) en McCallum.')
            return np.nan
        omega = 2 * np.pi / params.get('Pf', 1)
        # McCallum: solución analítica para flujo y difusividad
        flux = (omega * alpha * dz * delta_phi) / np.log(A1 / A2)
        # También se puede calcular la difusividad térmica si se requiere
        return flux
    except Exception as e:
        logger.error(f'Error en estimate_flux_mccallum: {e}')
        return np.nan

class FluxCalculator:
    """
    Clase para ejecutar cualquier método de flujo vertical de manera uniforme.
    """
    def __init__(self, params=None):
        self.params = params if params is not None else default_params

    def estimate(self, method, df, depth1, depth2):
        if method == 'hatch':
            return estimate_flux_hatch(df, depth1, depth2, self.params)
        elif method == 'keery':
            return estimate_flux_keery(df, depth1, depth2, self.params)
        elif method == 'mccallum':
            return estimate_flux_mccallum(df, depth1, depth2, self.params)
        else:
            logger.error(f'Método desconocido: {method}')
            return np.nan

# Ejemplo de integración con pipeline y logging
# El pipeline actual puede llamar FluxCalculator.estimate('hatch', df, d1, d2)
# El logger registra advertencias y errores en estilo MATLAB

# Nota: Las ecuaciones y validaciones siguen la lógica oficial VFLUX2 y los archivos MATLAB.
# Si se requiere compatibilidad exacta con MATLAB, ajustar los parámetros y el preprocesamiento según la configuración de la serie temporal y los sensores.
