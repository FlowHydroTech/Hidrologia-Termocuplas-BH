"""
Métodos para calcular flujos verticales de agua a partir de datos de temperatura.

Este módulo implementa los 5 métodos principales usados en VFLUX2:
1. McCallum (2012) - Método combinado más robusto
2. Hatch - Amplitud (2006)
3. Hatch - Fase (2006)
4. Keery et al. (2007)
5. Luce et al. (2013)

Basado en las ecuaciones de conducción-advección de calor en medios porosos.
"""

import numpy as np
from typing import Dict, Optional


def calculate_thermal_diffusivity(
    thermal_conductivity: float,
    volumetric_heat_capacity: float
) -> float:
    """
    Calcula la difusividad térmica.
    
    α = λ / C
    
    Parameters
    ----------
    thermal_conductivity : float
        Conductividad térmica (W/m·K)
    volumetric_heat_capacity : float
        Capacidad calorífica volumétrica (J/m³·K)
        
    Returns
    -------
    float
        Difusividad térmica (m²/s)
    """
    return thermal_conductivity / volumetric_heat_capacity


def hatch_amplitude_method(
    amplitude_shallow: float,
    amplitude_deep: float,
    depth_difference: float,
    thermal_diffusivity: float,
    angular_frequency: float
) -> float:
    """
    Método de Hatch et al. (2006) - Ratio de Amplitudes.
    
    Calcula el flujo vertical usando la atenuación de amplitud entre dos sensores.
    
    v = (α / Δz) * ln(A₁ / A₂)
    
    Parameters
    ----------
    amplitude_shallow : float
        Amplitud de la señal térmica superficial (°C)
    amplitude_deep : float
        Amplitud de la señal térmica profunda (°C)
    depth_difference : float
        Diferencia de profundidad entre sensores (m) - positivo hacia abajo
    thermal_diffusivity : float
        Difusividad térmica del medio (m²/s)
    angular_frequency : float
        Frecuencia angular de la señal (rad/s) - típicamente ω = 2π/86400 para ciclo diario
        
    Returns
    -------
    float
        Flujo vertical de agua (m/s), positivo = flujo descendente (infiltración)
    
    References
    ----------
    Hatch, C. E., et al. (2006). Quantifying surface water–groundwater interactions 
    using time series analysis of streambed thermal records: Method development. 
    Water Resources Research, 42(10).
    """
    if amplitude_deep <= 0 or amplitude_shallow <= 0:
        return np.nan
    
    # Ratio de amplitudes
    Ar = amplitude_shallow / amplitude_deep
    
    if Ar <= 1:
        return np.nan  # Indica flujo ascendente o sin flujo
    
    # Ecuación de Hatch - Amplitud
    v = (thermal_diffusivity / depth_difference) * np.log(Ar)
    
    return v


def hatch_phase_method(
    phase_shallow: float,
    phase_deep: float,
    depth_difference: float,
    thermal_diffusivity: float,
    angular_frequency: float,
    thermal_conductivity: float,
    heat_capacity_water: float
) -> float:
    """
    Método de Hatch et al. (2006) - Desfase Temporal.
    
    Calcula el flujo vertical usando el desfase de fase entre dos sensores.
    
    ECUACIÓN CORREGIDA:
    v = [Δφ - √((ω×Δz²)/(4α))] × (2λ)/(Cw×Δz)
    
    donde el primer término √((ω×Δz²)/(4α)) es el desfase por conducción pura
    y debe restarse del desfase total medido para obtener el desfase advectivo.
    
    Parameters
    ----------
    phase_shallow : float
        Fase de la señal térmica superficial (radianes)
    phase_deep : float
        Fase de la señal térmica profunda (radianes)
    depth_difference : float
        Diferencia de profundidad entre sensores (m)
    thermal_diffusivity : float
        Difusividad térmica del medio (m²/s)
    angular_frequency : float
        Frecuencia angular de la señal (rad/s)
    thermal_conductivity : float
        Conductividad térmica del sedimento (W/m·K)
    heat_capacity_water : float
        Capacidad calorífica volumétrica del agua (J/m³·K)
        
    Returns
    -------
    float
        Flujo vertical de agua (m/s)
    
    References
    ----------
    Hatch, C. E., et al. (2006). Water Resources Research, 42(10).
    Stallman, R. W. (1965). Journal of Geophysical Research, 70(12).
    """
    # Calcular desfase total (señal profunda se retrasa)
    delta_phase_total = phase_deep - phase_shallow
    
    # Normalizar a [0, 2π]
    while delta_phase_total < 0:
        delta_phase_total += 2 * np.pi
    while delta_phase_total > 2 * np.pi:
        delta_phase_total -= 2 * np.pi
    
    # Calcular desfase por conducción pura (sin flujo)
    delta_phase_conductive = np.sqrt((angular_frequency * depth_difference**2) / (4 * thermal_diffusivity))
    
    # Desfase causado por advección
    delta_phase_advective = delta_phase_total - delta_phase_conductive
    
    if delta_phase_advective <= 0:
        # No hay desfase advectivo o flujo ascendente
        return 0.0  # O podría retornar NaN dependiendo del caso de uso
    
    # Ecuación de Hatch - Fase CORREGIDA (con término conductivo)
    # v = (Δφ_adv / Δz) × (2λ / Cw)
    v = (delta_phase_advective / depth_difference) * (2 * thermal_conductivity) / heat_capacity_water
    
    return v


def keery_method(
    amplitude_shallow: float,
    amplitude_deep: float,
    phase_shallow: float,
    phase_deep: float,
    depth_difference: float,
    thermal_diffusivity: float,
    angular_frequency: float,
    thermal_conductivity: float,
    heat_capacity_water: float,
    heat_capacity_sediment: float
) -> float:
    """
    Método de Keery et al. (2007).
    
    Método mejorado que considera la capacidad calorífica del agua y sedimento.
    
    Parameters
    ----------
    amplitude_shallow : float
        Amplitud superficial (°C)
    amplitude_deep : float
        Amplitud profunda (°C)
    phase_shallow : float
        Fase superficial (rad)
    phase_deep : float
        Fase profunda (rad)
    depth_difference : float
        Diferencia de profundidad (m)
    thermal_diffusivity : float
        Difusividad térmica (m²/s)
    angular_frequency : float
        Frecuencia angular (rad/s)
    thermal_conductivity : float
        Conductividad térmica (W/m·K)
    heat_capacity_water : float
        Capacidad calorífica volumétrica del agua (J/m³·K)
    heat_capacity_sediment : float
        Capacidad calorífica volumétrica del sedimento (J/m³·K)
        
    Returns
    -------
    float
        Flujo vertical (m/s)
    
    References
    ----------
    Keery, J., et al. (2007). Temporal and spatial variability of groundwater–surface 
    water fluxes: Development and application of an analytical method using temperature 
    time series. Journal of Hydrology, 336(1-2), 1-16.
    """
    if amplitude_deep <= 0 or amplitude_shallow <= 0:
        return np.nan
    
    # Parámetros
    Ar = amplitude_shallow / amplitude_deep
    delta_phi = phase_deep - phase_shallow
    
    # Normalizar fase
    while delta_phi < 0:
        delta_phi += 2 * np.pi
    
    # Parámetro beta
    beta = np.sqrt(angular_frequency / (2 * thermal_diffusivity))
    
    # Ecuación de Keery (simplificada)
    # v = (2α / Δz) * [ln(Ar) + βΔz - Δφ/βΔz]
    
    numerator = np.log(Ar) + beta * depth_difference - delta_phi / (beta * depth_difference)
    v = (2 * thermal_diffusivity / depth_difference) * numerator
    
    return v


def mccallum_method(
    amplitude_shallow: float,
    amplitude_deep: float,
    phase_shallow: float,
    phase_deep: float,
    depth_difference: float,
    thermal_diffusivity: float,
    angular_frequency: float
) -> float:
    """
    Método de McCallum et al. (2012) - Método Combinado.
    
    Este es el método MÁS ROBUSTO y recomendado por VFLUX2.
    Combina información de amplitud y fase para mayor estabilidad.
    
    Parameters
    ----------
    amplitude_shallow : float
        Amplitud superficial (°C)
    amplitude_deep : float
        Amplitud profunda (°C)
    phase_shallow : float
        Fase superficial (rad)
    phase_deep : float
        Fase profunda (rad)
    depth_difference : float
        Diferencia de profundidad (m)
    thermal_diffusivity : float
        Difusividad térmica (m²/s)
    angular_frequency : float
        Frecuencia angular (rad/s)
        
    Returns
    -------
    float
        Flujo vertical (m/s)
    
    References
    ----------
    McCallum, A. M., et al. (2012). Limitations of the use of environmental tracers 
    to infer groundwater age. Groundwater, 50(6), 949-951.
    """
    if amplitude_deep <= 0 or amplitude_shallow <= 0:
        return np.nan
    
    # ΔA y Δφ
    delta_A = np.log(amplitude_shallow / amplitude_deep)
    delta_phi = phase_deep - phase_shallow
    
    # Normalizar fase a [0, 2π]
    while delta_phi < 0:
        delta_phi += 2 * np.pi
    while delta_phi > 2 * np.pi:
        delta_phi -= 2 * np.pi
    
    # Parámetro de atenuación
    # v = α/Δz * [ΔA + √(ΔA² + (ωΔz²)/(4α) - Δφ²)]
    
    term1 = delta_A
    term2_inside = delta_A**2 + (angular_frequency * depth_difference**2) / (4 * thermal_diffusivity) - delta_phi**2
    
    if term2_inside < 0:
        # Si el término es negativo, usar solo amplitud
        return hatch_amplitude_method(amplitude_shallow, amplitude_deep, 
                                       depth_difference, thermal_diffusivity, 
                                       angular_frequency)
    
    term2 = np.sqrt(term2_inside)
    
    v = (thermal_diffusivity / depth_difference) * (term1 + term2)
    
    return v


def luce_method(
    amplitude_shallow: float,
    amplitude_deep: float,
    depth_difference: float,
    angular_frequency: float
) -> float:
    """
    Método de Luce et al. (2013) - Método empírico simplificado.
    
    Método simple útil para diagnóstico rápido.
    
    Parameters
    ----------
    amplitude_shallow : float
        Amplitud superficial (°C)
    amplitude_deep : float
        Amplitud profunda (°C)
    depth_difference : float
        Diferencia de profundidad (m)
    angular_frequency : float
        Frecuencia angular (rad/s)
        
    Returns
    -------
    float
        Flujo vertical (m/s)
    
    References
    ----------
    Luce, C. H., et al. (2013). Solutions for the diurnally forced advection-diffusion 
    equation to estimate bulk fluid velocity and diffusivity in streambeds from temperature 
    time series. Water Resources Research, 49(1), 488-506.
    """
    if amplitude_deep <= 0 or amplitude_shallow <= 0:
        return np.nan
    
    Ar = amplitude_shallow / amplitude_deep
    
    if Ar <= 1:
        return np.nan
    
    # Ecuación simplificada de Luce
    # v ≈ (ω * Δz) / (2 * ln(Ar))
    
    v = (angular_frequency * depth_difference) / (2 * np.log(Ar))
    
    return v


def calculate_vflux_all_methods(
    amplitude_shallow: float,
    amplitude_deep: float,
    phase_shallow: float,
    phase_deep: float,
    depth_difference: float,
    thermal_conductivity: float,
    heat_capacity_sediment: float,
    heat_capacity_water: float,
    angular_frequency: float = 2 * np.pi / 86400  # Ciclo diario por defecto
) -> Dict[str, float]:
    """
    Calcula el flujo vertical usando TODOS los métodos disponibles.
    
    Parameters
    ----------
    amplitude_shallow : float
        Amplitud sensor superficial (°C)
    amplitude_deep : float
        Amplitud sensor profundo (°C)
    phase_shallow : float
        Fase sensor superficial (rad)
    phase_deep : float
        Fase sensor profundo (rad)
    depth_difference : float
        Diferencia de profundidad (m)
    thermal_conductivity : float
        Conductividad térmica (W/m·K)
    heat_capacity_sediment : float
        Capacidad calorífica volumétrica sedimento (J/m³·K)
    heat_capacity_water : float
        Capacidad calorífica volumétrica agua (J/m³·K)
    angular_frequency : float
        Frecuencia angular (rad/s), default = 2π/86400 (ciclo diario)
        
    Returns
    -------
    dict
        Diccionario con flujos calculados por cada método (m/s)
    """
    # Calcular difusividad térmica
    alpha = calculate_thermal_diffusivity(thermal_conductivity, heat_capacity_sediment)
    
    # Calcular flujo con cada método
    results = {
        'mccallum': mccallum_method(
            amplitude_shallow, amplitude_deep, phase_shallow, phase_deep,
            depth_difference, alpha, angular_frequency
        ),
        'hatch_amplitude': hatch_amplitude_method(
            amplitude_shallow, amplitude_deep, depth_difference, 
            alpha, angular_frequency
        ),
        'hatch_phase': hatch_phase_method(
            phase_shallow, phase_deep, depth_difference, 
            alpha, angular_frequency, thermal_conductivity, heat_capacity_water
        ),
        'keery': keery_method(
            amplitude_shallow, amplitude_deep, phase_shallow, phase_deep,
            depth_difference, alpha, angular_frequency, thermal_conductivity,
            heat_capacity_water, heat_capacity_sediment
        ),
        'luce': luce_method(
            amplitude_shallow, amplitude_deep, depth_difference, angular_frequency
        )
    }
    
    # Convertir a mm/día para interpretación
    results_mm_day = {
        method: flux * 1000 * 86400 if not np.isnan(flux) else np.nan
        for method, flux in results.items()
    }
    
    return {
        'flux_m_s': results,
        'flux_mm_day': results_mm_day,
        'thermal_diffusivity': alpha
    }
