"""
Tests para el módulo de análisis armónico.
"""

import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from harmonic_analysis import (
    compute_fft,
    extract_dominant_frequency,
    fit_harmonic_model
)


def test_compute_fft():
    """Test básico de FFT con señal sintética."""
    # Crear señal sintética: 1 Hz
    sampling_rate = 100  # Hz
    duration = 1  # segundo
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
    frequency = 1  # Hz
    signal = np.sin(2 * np.pi * frequency * t)
    
    freqs, amplitudes = compute_fft(pd.Series(signal), sampling_rate)
    
    # Encontrar frecuencia dominante
    dominant_idx = np.argmax(amplitudes)
    dominant_freq = freqs[dominant_idx]
    
    assert np.isclose(dominant_freq, frequency, rtol=0.1)


def test_extract_dominant_frequency():
    """Test de extracción de frecuencia dominante."""
    sampling_rate = 100
    duration = 2
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
    frequency = 5  # Hz
    signal = np.sin(2 * np.pi * frequency * t) + 0.1 * np.random.randn(len(t))
    
    dominant_freq = extract_dominant_frequency(pd.Series(signal), sampling_rate)
    
    assert np.isclose(dominant_freq, frequency, rtol=0.1)


def test_fit_harmonic_model():
    """Test de ajuste de modelo armónico."""
    # Parámetros conocidos
    mean = 10
    amplitude = 5
    omega = 2 * np.pi / 24  # Ciclo diario
    phase = np.pi / 4
    
    # Generar datos
    t = np.linspace(0, 48, 100)  # 48 horas
    temperature = mean + amplitude * np.sin(omega * t + phase)
    
    # Ajustar modelo
    params = fit_harmonic_model(t, temperature)
    
    # Verificar parámetros
    assert np.isclose(params['mean'], mean, rtol=0.1)
    assert np.isclose(params['amplitude'], amplitude, rtol=0.1)
    assert np.isclose(params['omega'], omega, rtol=0.1)


if __name__ == '__main__':
    pytest.main([__file__])
