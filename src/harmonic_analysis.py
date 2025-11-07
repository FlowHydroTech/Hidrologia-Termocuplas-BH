"""
Análisis armónico de señales de temperatura.
"""

import numpy as np
import pandas as pd
from scipy import signal
from scipy.fft import fft, fftfreq


def compute_fft(temperature_series: pd.Series, sampling_rate: float) -> tuple:
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
        (frequencies, amplitudes)
    """
    n = len(temperature_series)
    yf = fft(temperature_series.values)
    xf = fftfreq(n, 1 / sampling_rate)
    
    # Solo frecuencias positivas
    positive_freq_idx = xf > 0
    return xf[positive_freq_idx], np.abs(yf[positive_freq_idx])


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


def fit_harmonic_model(time: np.ndarray, temperature: np.ndarray) -> dict:
    """
    Ajusta un modelo armónico simple a los datos de temperatura.
    
    T(t) = A + B*sin(ωt + φ)
    
    Parameters
    ----------
    time : np.ndarray
        Vector de tiempo
    temperature : np.ndarray
        Vector de temperatura
        
    Returns
    -------
    dict
        Parámetros del modelo: {'mean': A, 'amplitude': B, 'omega': ω, 'phase': φ}
    """
    mean_temp = np.mean(temperature)
    detrended = temperature - mean_temp
    
    # Estimación inicial con FFT
    sampling_rate = 1 / np.mean(np.diff(time))
    dominant_freq = extract_dominant_frequency(pd.Series(temperature), sampling_rate)
    omega = 2 * np.pi * dominant_freq
    
    # Ajuste de amplitud y fase
    from scipy.optimize import curve_fit
    
    def harmonic(t, A, B, omega, phi):
        return A + B * np.sin(omega * t + phi)
    
    p0 = [mean_temp, np.std(detrended), omega, 0]
    popt, _ = curve_fit(harmonic, time, temperature, p0=p0)
    
    return {
        'mean': popt[0],
        'amplitude': popt[1],
        'omega': popt[2],
        'phase': popt[3]
    }
