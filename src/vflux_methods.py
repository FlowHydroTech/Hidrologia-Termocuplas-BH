"""
Métodos para calcular flujos verticales de agua a partir de datos de temperatura.
"""

import numpy as np
import pandas as pd


def amplitude_ratio_method(
    amplitude_shallow: float,
    amplitude_deep: float,
    depth_difference: float,
    thermal_diffusivity: float,
    angular_frequency: float
) -> float:
    """
    Calcula el flujo vertical usando el método de ratio de amplitudes.
    
    Basado en Hatch et al. (2006) y Keery et al. (2007).
    
    Parameters
    ----------
    amplitude_shallow : float
        Amplitud de la señal térmica superficial (°C)
    amplitude_deep : float
        Amplitud de la señal térmica profunda (°C)
    depth_difference : float
        Diferencia de profundidad entre sensores (m)
    thermal_diffusivity : float
        Difusividad térmica del medio (m²/s)
    angular_frequency : float
        Frecuencia angular de la señal (rad/s)
        
    Returns
    -------
    float
        Flujo vertical de agua (m/s), positivo hacia abajo
    """
    if amplitude_deep <= 0 or amplitude_shallow <= 0:
        return np.nan
    
    Ar = amplitude_shallow / amplitude_deep
    if Ar <= 1:
        return np.nan  # No hay flujo descendente
    
    v = (thermal_diffusivity / depth_difference) * np.log(Ar)
    return v


def phase_shift_method(
    phase_shallow: float,
    phase_deep: float,
    depth_difference: float,
    thermal_diffusivity: float,
    angular_frequency: float
) -> float:
    """
    Calcula el flujo vertical usando el método de desfase temporal.
    
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
        
    Returns
    -------
    float
        Flujo vertical de agua (m/s)
    """
    delta_phase = phase_deep - phase_shallow
    
    # Ajustar para que esté en el rango correcto
    while delta_phase < 0:
        delta_phase += 2 * np.pi
    while delta_phase > 2 * np.pi:
        delta_phase -= 2 * np.pi
    
    v = (4 * thermal_diffusivity * delta_phase) / (angular_frequency * depth_difference**2)
    return v


def calculate_thermal_diffusivity(
    thermal_conductivity: float,
    volumetric_heat_capacity: float
) -> float:
    """
    Calcula la difusividad térmica.
    
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
