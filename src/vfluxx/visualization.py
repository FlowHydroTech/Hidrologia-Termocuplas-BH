import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

def plot_spectrum(freq, amp, out_dir):
    """
    Plot AR(12) spectrum and save as PNG.
    """
    plt.figure()
    plt.plot(freq, amp)
    plt.xlabel('Frecuencia')
    plt.ylabel('Amplitud')
    plt.title('Espectro AR(12)')
    plt.savefig(f"{out_dir}/espectro_AR12_python.png")
    plt.close()

def plot_flux(df_resampled, out_dir):
    """
    Plot estimated flux and save as PNG.
    """
    plt.figure()
    plt.plot(df_resampled['time'], df_resampled['temperature'])
    plt.xlabel('Tiempo')
    plt.ylabel('Temperatura')
    plt.title('Temperaturas Remuestreadas')
    plt.savefig(f"{out_dir}/flujo_estimado_python.png")
    plt.close()

def plot_temperatures(df, out_dir):
    """
    Plot original temperatures and save as PNG.
    """
    plt.figure()
    plt.plot(df['time'], df['temperature'])
    plt.xlabel('Tiempo')
    plt.ylabel('Temperatura')
    plt.title('Temperaturas Originales')
    plt.savefig(f"{out_dir}/temperaturas_remuestreadas_python.png")
    plt.close()
