# scripts/test_metodos_vflux.py
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import curve_fit

from vfluxx.io_utils import load_matlab_data
from vfluxx.preprocess import build_dataframe, resample_temperatures
from vfluxx.flux_methods import FluxCalculator

BASE = Path(__file__).resolve().parents[1]
MAT_PATH = BASE / "data" / "MATLAB" / "example" / "site12_data.mat"

def ajuste_armonico(t, temp):
    """
    Ajusta una señal armónica de periodo diario y retorna amplitud y fase.
    t: array de tiempo en días
    temp: array de temperatura
    """
    def modelo(t, A, phi, offset):
        return A * np.sin(2 * np.pi * t + phi) + offset
    if len(temp) < 3:
        print("Advertencia: no hay suficientes datos para ajuste armónico (mínimo 3).")
        return np.nan, np.nan
    t_rel = (t - t[0]) / 1.0
    A0 = (np.nanmax(temp) - np.nanmin(temp)) / 2
    phi0 = 0
    offset0 = np.nanmean(temp)
    popt, _ = curve_fit(modelo, t_rel, temp, p0=[A0, phi0, offset0])
    A, phi, offset = popt
    return A, phi

if __name__ == "__main__":
    time, temps = load_matlab_data(MAT_PATH)
    df1 = build_dataframe(time, temps[:, 0])
    df2 = build_dataframe(time, temps[:, 1]) if temps.shape[1] > 1 else df1.copy()
    # Paso 1: Selección dinámica de frecuencia
    print("Seleccione la frecuencia de remuestreo:")
    print("1) 15min")
    print("2) 1H")
    print("3) 6H")
    print("4) 1D")
    freq_op = input("Ingrese el número de frecuencia (1/2/3/4): ").strip()
    if freq_op == "1":
        freq = "15min"
    elif freq_op == "2":
        freq = "1H"
    elif freq_op == "3":
        freq = "6H"
    elif freq_op == "4":
        freq = "1D"
    else:
        print("Opción inválida. Usando '15min' por defecto.")
        freq = "15min"

    # Paso 2: Generar dataset sintético robusto
    print("¿Desea usar un dataset sintético largo para validación? (s/n)")
    usar_sintetico = input().strip().lower()
    if usar_sintetico == "s":
        print("Generando dataset sintético físico validado (Keery/Hatch/McCallum)...")
        dias = 30
        n_sensores = 6
        dt_min = 60  # 1 hora
        n = int((24*60/dt_min)*dias)
        time = pd.date_range(start="2023-01-01", periods=n, freq=f"{dt_min}min")
        z = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])  # m
        T0 = 15.0
        g = 0.2   # gradiente térmico (°C/m)
        A0 = 1.0  # amplitud superficial
        D = 2.0   # decaimiento de amplitud (m⁻¹)
        S = 2.0   # desfase por metro (rad/m)
        omega = 2 * np.pi / 24.0  # rad/h
        temps = np.zeros((n, n_sensores))
        t_horas = (time - time[0]).total_seconds()/3600.0
        for i in range(n_sensores):
            amp = A0 * np.exp(-z[i]/D)
            phase = S * z[i]
            temps[:, i] = (T0 + g*z[i]
                + amp * np.sin(omega * t_horas - phase)
                + np.random.normal(0, 0.05, n))
        print(f"Dataset sintético generado: shape={temps.shape}")
        df1 = build_dataframe(time, temps[:, 0])
        df2 = build_dataframe(time, temps[:, 1])
    else:
        # Dataset real
        time, temps = load_matlab_data(MAT_PATH)
        df1 = build_dataframe(time, temps[:, 0])
        df2 = build_dataframe(time, temps[:, 1]) if temps.shape[1] > 1 else df1.copy()

    df1_resampled = resample_temperatures(df1, freq=freq)
    df2_resampled = resample_temperatures(df2, freq=freq)
    print(f"Longitud df1_resampled: {len(df1_resampled)}")
    print(f"Longitud df2_resampled: {len(df2_resampled)}")
    print(f"Longitud df1_resampled: {len(df1_resampled)}")
    print(f"Longitud df2_resampled: {len(df2_resampled)}")

    t_days = (df1_resampled['time'] - df1_resampled['time'].iloc[0]).dt.total_seconds() / 86400.0
    amp1, phase1 = ajuste_armonico(t_days.values, df1_resampled['temperature'].values)
    amp2, phase2 = ajuste_armonico(t_days.values, df2_resampled['temperature'].values)

    depth1 = 0.0   # T1 (0 cm)
    depth2 = 0.1   # T2 (10 cm)
    df_metodo = {
        depth1: {'amplitude': amp1, 'phase': phase1},
        depth2: {'amplitude': amp2, 'phase': phase2}
    }

    calc = FluxCalculator()

    for method in ["hatch", "keery", "mccallum"]:
        print(f"\n=== Método: {method.upper()} ===")
        flux = calc.estimate(method, df_metodo, depth1, depth2)
        if np.isnan(flux):
            print("Advertencia: flujo no calculable para este método y datos.")
        else:
            print(f"Flujo estimado: {flux:.6f} (unidades según método)")
