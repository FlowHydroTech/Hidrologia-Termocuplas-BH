"""
Funciones de visualización para datos de termocuplas.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Optional


def plot_temperature_series(
    df: pd.DataFrame,
    columns: Optional[list] = None,
    title: str = "Series de Temperatura",
    figsize: tuple = (12, 6)
) -> plt.Figure:
    """
    Grafica series temporales de temperatura.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con datos de temperatura
    columns : list, optional
        Columnas a graficar. Si es None, grafica todas.
    title : str
        Título del gráfico
    figsize : tuple
        Tamaño de la figura
        
    Returns
    -------
    plt.Figure
        Figura de matplotlib
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    if columns is None:
        columns = df.columns
    
    for col in columns:
        ax.plot(df.index, df[col], label=col)
    
    ax.set_xlabel('Tiempo')
    ax.set_ylabel('Temperatura (°C)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    return fig


def plot_fft_spectrum(
    frequencies: np.ndarray,
    amplitudes: np.ndarray,
    title: str = "Espectro de Frecuencias",
    figsize: tuple = (10, 5)
) -> plt.Figure:
    """
    Grafica el espectro de frecuencias.
    
    Parameters
    ----------
    frequencies : np.ndarray
        Frecuencias
    amplitudes : np.ndarray
        Amplitudes
    title : str
        Título del gráfico
    figsize : tuple
        Tamaño de la figura
        
    Returns
    -------
    plt.Figure
        Figura de matplotlib
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.plot(frequencies, amplitudes)
    ax.set_xlabel('Frecuencia (Hz)')
    ax.set_ylabel('Amplitud')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    
    return fig


def plot_depth_profile(
    depths: np.ndarray,
    values: np.ndarray,
    ylabel: str = "Valor",
    title: str = "Perfil de Profundidad",
    figsize: tuple = (6, 8)
) -> plt.Figure:
    """
    Grafica un perfil vertical.
    
    Parameters
    ----------
    depths : np.ndarray
        Profundidades
    values : np.ndarray
        Valores a graficar
    ylabel : str
        Etiqueta del eje y
    title : str
        Título del gráfico
    figsize : tuple
        Tamaño de la figura
        
    Returns
    -------
    plt.Figure
        Figura de matplotlib
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.plot(values, depths, 'o-')
    ax.set_ylabel('Profundidad (m)')
    ax.set_xlabel(ylabel)
    ax.set_title(title)
    ax.invert_yaxis()  # Profundidad aumenta hacia abajo
    ax.grid(True, alpha=0.3)
    
    return fig
