"""
Análisis armónico de señales de temperatura.

Este módulo replica el comportamiento del Captain Toolbox (arspec) usado en VFLUX2
para extraer parámetros armónicos de series temporales de temperatura.
"""

import numpy as np
import pandas as pd
from scipy.fft import fft, fftfreq
from scipy.optimize import curve_fit
from typing import Dict, Tuple, Optional


def compute_fft(temperature_series: pd.Series, sampling_rate: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calcula la transformada rápida de Fourier de una serie de temperatura.
    
    Parameters
    ----------
    temperature_series : pd.Series
        Serie temporal de temperatura
    sampling_rate : float
        Frecuencia de muestreo en Hz
        
    Returns
    -------
    tuple
        (frequencies, amplitudes) - Solo frecuencias positivas
    """
    n = len(temperature_series)
    
    # Remover tendencia
    temp_detrended = temperature_series.values - np.mean(temperature_series.values)
    
    # Calcular FFT
    yf = fft(temp_detrended)
    xf = fftfreq(n, 1 / sampling_rate)
    
    # Solo frecuencias positivas
    positive_freq_idx = xf > 0
    frequencies = xf[positive_freq_idx]
    amplitudes = 2.0 / n * np.abs(yf[positive_freq_idx])
    
    return frequencies, amplitudes


def compute_fft_spectrum(temperature_series: np.ndarray, 
                          sampling_interval_hours: float = 0.25) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calcula el espectro FFT de una serie de temperatura.
    
    Parameters
    ----------
    temperature_series : np.ndarray
        Serie de temperatura
    sampling_interval_hours : float
        Intervalo de muestreo en horas (default: 0.25 = 15 min)
    
    Returns
    -------
    tuple
        (freqs_per_day, amplitudes) - Frecuencias en ciclos/día
    """
    n = len(temperature_series)
    
    # Eliminar tendencia (detrend)
    temp_detrended = temperature_series - np.mean(temperature_series)
    
    # FFT
    yf = fft(temp_detrended)
    
    # Frecuencias en ciclos por hora
    freqs_per_hour = fftfreq(n, sampling_interval_hours)
    
    # Convertir a ciclos por día
    freqs_per_day = freqs_per_hour * 24
    
    # Solo frecuencias positivas
    positive_freq_idx = freqs_per_day > 0
    freqs_pos = freqs_per_day[positive_freq_idx]
    
    # Amplitudes normalizadas
    amplitudes = 2.0 / n * np.abs(yf[positive_freq_idx])
    
    return freqs_pos, amplitudes


def extract_dominant_frequency(temperature_series: pd.Series, sampling_rate: float) -> float:
    """
    Extrae la frecuencia dominante de una señal.
    
    Parameters
    ----------
    temperature_series : pd.Series
        Serie temporal de temperatura
    sampling_rate : float
        Frecuencia de muestreo en Hz
        
    Returns
    -------
    float
        Frecuencia dominante en Hz
    """
    freqs, amplitudes = compute_fft(temperature_series, sampling_rate)
    dominant_idx = np.argmax(amplitudes)
    return freqs[dominant_idx]


def harmonic_model(t: np.ndarray, A_mean: float, A_amp: float, 
                   omega: float, phi: float) -> np.ndarray:
    """
    Modelo armónico simple: T(t) = A_mean + A_amp * sin(omega * t + phi)
    
    Parameters
    ----------
    t : np.ndarray
        Vector de tiempo (en horas desde inicio)
    A_mean : float
        Temperatura media (offset)
    A_amp : float
        Amplitud de la oscilación
    omega : float
        Frecuencia angular (rad/hora)
    phi : float
        Fase inicial (radianes)
    
    Returns
    -------
    np.ndarray
        Serie de temperatura modelada
    """
    return A_mean + A_amp * np.sin(omega * t + phi)


def fit_harmonic_model(time: np.ndarray, temperature: np.ndarray) -> Optional[Dict[str, float]]:
    """
    Ajusta un modelo armónico simple a los datos de temperatura.
    
    T(t) = A + B*sin(ωt + φ)
    
    Parameters
    ----------
    time : np.ndarray
        Vector de tiempo (en horas desde el inicio)
    temperature : np.ndarray
        Vector de temperatura
        
    Returns
    -------
    dict or None
        Parámetros del modelo: {'mean': A, 'amplitude': B, 'omega': ω, 'phase': φ, 'period_hours': T}
        Retorna None si el ajuste falla
    """
    # Estimación inicial de parámetros
    mean_temp = np.mean(temperature)
    amp_temp = (np.max(temperature) - np.min(temperature)) / 2
    omega_daily = 2 * np.pi / 24  # rad/hora para ciclo diario (asumiendo datos horarios)
    phi_init = 0
    
    # Valores iniciales para curve_fit
    p0 = [mean_temp, amp_temp, omega_daily, phi_init]
    
    try:
        # Ajuste con curve_fit
        popt, pcov = curve_fit(harmonic_model, time, temperature, p0=p0, maxfev=5000)
        
        return {
            'mean': popt[0],
            'amplitude': popt[1],
            'omega': popt[2],
            'phase': popt[3],
            'period_hours': 2 * np.pi / popt[2]
        }
    except Exception as e:
        print(f"⚠️ Error en ajuste armónico: {e}")
        return None


def calculate_amplitude_ratio(amplitude_shallow: float, 
                               amplitude_deep: float) -> float:
    """
    Calcula ΔA = ln(A_shallow / A_deep)
    
    Parámetro fundamental para métodos de flujo térmico.
    
    Parameters
    ----------
    amplitude_shallow : float
        Amplitud del sensor superficial
    amplitude_deep : float
        Amplitud del sensor profundo
    
    Returns
    -------
    float
        ΔA (adimensional)
    """
    if amplitude_deep <= 0 or amplitude_shallow <= 0:
        return np.nan
    
    return np.log(amplitude_shallow / amplitude_deep)


def calculate_phase_shift(phase_shallow: float, phase_deep: float) -> float:
    """
    Calcula Δφ = φ_deep - φ_shallow
    
    Parámetro fundamental para métodos de flujo térmico.
    
    Parameters
    ----------
    phase_shallow : float
        Fase del sensor superficial (radianes)
    phase_deep : float
        Fase del sensor profundo (radianes)
    
    Returns
    -------
    float
        Δφ (radianes)
    """
    delta_phi = phase_deep - phase_shallow
    
    # Normalizar a rango [-π, π]
    while delta_phi > np.pi:
        delta_phi -= 2 * np.pi
    while delta_phi < -np.pi:
        delta_phi += 2 * np.pi
    
    return delta_phi


def analyze_sensor_pair(time_hours: np.ndarray,
                        temp_shallow: np.ndarray,
                        temp_deep: np.ndarray) -> Dict[str, float]:
    """
    Analiza un par de sensores y extrae todos los parámetros armónicos relevantes.
    
    Parameters
    ----------
    time_hours : np.ndarray
        Vector de tiempo en horas
    temp_shallow : np.ndarray
        Temperatura del sensor superficial
    temp_deep : np.ndarray
        Temperatura del sensor profundo
    
    Returns
    -------
    dict
        Diccionario con todos los parámetros: A1, A2, phi1, phi2, delta_A, delta_phi
    """
    # Ajustar modelo a cada sensor
    params_shallow = fit_harmonic_model(time_hours, temp_shallow)
    params_deep = fit_harmonic_model(time_hours, temp_deep)
    
    if params_shallow is None or params_deep is None:
        return None
    
    # Calcular ΔA y Δφ
    delta_A = calculate_amplitude_ratio(params_shallow['amplitude'], 
                                        params_deep['amplitude'])
    delta_phi = calculate_phase_shift(params_shallow['phase'], 
                                      params_deep['phase'])
    
    return {
        'A_shallow': params_shallow['amplitude'],
        'A_deep': params_deep['amplitude'],
        'phi_shallow': params_shallow['phase'],
        'phi_deep': params_deep['phase'],
        'mean_shallow': params_shallow['mean'],
        'mean_deep': params_deep['mean'],
        'delta_A': delta_A,
        'delta_phi': delta_phi,
        'period_hours': params_shallow['period_hours']
    }
