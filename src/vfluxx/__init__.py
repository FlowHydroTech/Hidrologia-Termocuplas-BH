"""
vfluxx: Librería profesional para análisis de flujo vertical en suelos usando termocuplas.
Inspirada en VFLUX2 (MATLAB).
"""

# ==========================
# IMPORTS DEL MÓDULO
# ==========================
from .io_utils import (
    load_matlab_data, save_results,
    load_ibutton_csv, load_all_ibuttons, ibuttons_to_dataframe,
    load_termocuplas_excel
)
from .preprocess import build_dataframe, resample_temperatures, align_and_resample
from .harmonic_analysis import (
    compute_ar_spectrum, clean_zero_freqs,
    fit_harmonic_model, analyze_sensor_pair
)
from .flux_methods import FluxCalculator
from .vflux_methods import calculate_vflux_all_methods
from .flux_timeseries import (
    calculate_flux_timeseries, export_flux_timeseries, batch_calculate_flux_timeseries
)
from .visualization import plot_spectrum, plot_flux, plot_temperatures
from .logger_vflux import (
    log, log_header, log_section, log_note, log_processing_sensor,
    log_done, log_pause, log_spectrum_table, log_flux_done,
    export_log, ENABLE_PAUSES
)


# ==========================
# CLASE PRINCIPAL
# ==========================
class VFluxPython:
    """
    Clase principal para ejecutar el flujo completo de análisis VFLUX2 en Python.
    """

    def __init__(self, mat_path: str):
        self.mat_path = mat_path
        self.time = None
        self.temps = None

    # ======================================================
    # MÉTODO PRINCIPAL: EJECUTAR TODO EL PIPELINE
    # ======================================================
    def run_all(self, out_dir: str = "resultados_python"):
        import os
        import pandas as pd
        log_header()
        os.makedirs(out_dir, exist_ok=True)
        self.time, self.temps = load_matlab_data(self.mat_path)
        n_sensores = self.temps.shape[1]

        # Preguntar modo de ejecución
        print("Seleccione modo de procesamiento:")
        print("1) MATLAB (global)")
        print("2) Avanzado (multisensor)")
        print("3) Ambos (híbrido)")
        modo = input("Ingrese el número de modo (1/2/3): ").strip()
        if modo == "1":
            modo_str = "matlab"
        elif modo == "2":
            modo_str = "avanzado"
        elif modo == "3":
            modo_str = "hibrido"
        else:
            print("Modo inválido. Usando 'matlab' por defecto.")
            modo_str = "matlab"
        # Preguntar método de flujo (mover fuera para ambos modos)
        print("Seleccione método de flujo vertical:")
        print("1) Hatch (amplitud)")
        print("2) Keery (amplitud + fase)")
        print("3) McCallum (combinado)")
        metodo = input("Ingrese el número de método (1/2/3): ").strip()
        if metodo == "1":
            metodo_str = "hatch"
        elif metodo == "2":
            metodo_str = "keery"
        elif metodo == "3":
            metodo_str = "mccallum"
        else:
            print("Método inválido. Usando 'hatch' por defecto.")
            metodo_str = "hatch"

        if modo_str in ["matlab", "hibrido"]:
            # MODO MATLAB
            log_section("format")
            df_global = build_dataframe(self.time, self.temps.mean(axis=1))
            from .flux_methods import FluxCalculator
            calc = FluxCalculator()
            log_note("Resampling started (global)")
            df_resampled = resample_temperatures(df_global)
            if len(df_resampled) < 2:
                log_note("Advertencia: datos insuficientes, se interpolará para completar.")
                df_resampled = df_global.copy()
            log_done()
            log_section("DHR filtering")
            ar_order = min(12, len(df_resampled) - 1) if len(df_resampled) > 1 else 1
            log_note(f"ARorder set to {ar_order}")
            spectrum, freqs = compute_ar_spectrum(df_resampled, order=ar_order)
            freqs = clean_zero_freqs(freqs)
            log_spectrum_table(freqs, spectrum)
            log_done()
            log_section("flux estimation")
            # Calcular flujo usando FluxCalculator y método seleccionado
            depth1 = 0.0
            depth2 = 0.5
            df_metodo = {
                depth1: {'amplitude': spectrum[0] if len(spectrum) > 0 else 1, 'phase': 0},
                depth2: {'amplitude': spectrum[1] if len(spectrum) > 1 else 1, 'phase': 0.1}
            }
            flux = calc.estimate(metodo_str, df_metodo, depth1, depth2)
            sensitivity = 0.0  # Sensibilidad: placeholder
            if pd.isna(flux):
                log_note("Advertencia: flujo no calculable, se asigna 0.")
                flux = 0.0
            # Usar el método seleccionado para el cálculo de flujo
            # Para modo global, usar los dos primeros sensores (o los más superficiales)
            depth1 = 0.0
            depth2 = 0.5
            # Simular amplitud y fase para compatibilidad (solo amplitud si Hatch)
            df_metodo = {
                depth1: {'amplitude': spectrum[0] if len(spectrum) > 0 else 1, 'phase': 0},
                depth2: {'amplitude': spectrum[1] if len(spectrum) > 1 else 1, 'phase': 0.1}
            }
            flux = calc.estimate(metodo_str, df_metodo, depth1, depth2)
            sensitivity = 0.0  # Sensibilidad: placeholder
            log_done()
            # Exportar archivos globales
            df_resampled.to_csv(f"{out_dir}/temperaturas_resampleadas_python.csv", index=False)
            # Asegurar longitud igual
            min_len = min(len(freqs), len(spectrum))
            if min_len == 0:
                log_note("Advertencia: espectro vacío, se exporta fila nula.")
                pd.DataFrame({"freq": [0], "amplitude": [0]}).to_csv(f"{out_dir}/espectro_AR12_python.csv", index=False)
            else:
                pd.DataFrame({"freq": freqs[:min_len], "amplitude": spectrum[:min_len]}).to_csv(f"{out_dir}/espectro_AR12_python.csv", index=False)
                pd.DataFrame({"flux": [flux]}).to_csv(f"{out_dir}/flujo_estimado_python.csv", index=False)
                pd.DataFrame({"sensitivity": [sensitivity]}).to_csv(f"{out_dir}/sensibilidad_flujo_python.csv", index=False)
                plot_spectrum(freqs[:min_len], spectrum[:min_len], out_dir)
            plot_flux(df_resampled, out_dir)
            plot_temperatures(df_global, out_dir)
            log_flux_done()
            export_log(f"{out_dir}/registro_ejecucion.log")

        if modo_str in ["avanzado", "hibrido"]:
            # MODO AVANZADO
            from .flux_methods import FluxCalculator
            calc = FluxCalculator()
            flux_list = []
            sens_list = []
            for i in range(n_sensores):
                depth_cm = (i+1) * 10
                depth_m = depth_cm / 100.0
                log_processing_sensor(depth_m)
                log_note("Resampling started")
                df_sensor = build_dataframe(self.time, self.temps[:, i])
                df_resampled = resample_temperatures(df_sensor)
                if len(df_resampled) < 2:
                    log_note(f"Advertencia: sensor {i+1} datos insuficientes, se interpolará para completar.")
                    df_resampled = df_sensor.copy()
                log_done()
                log_section("DHR filtering")
                ar_order = min(12, len(df_resampled) - 1) if len(df_resampled) > 1 else 1
                log_note(f"ARorder set to {ar_order}")
                spectrum, freqs = compute_ar_spectrum(df_resampled, order=ar_order)
                freqs = clean_zero_freqs(freqs)
                log_spectrum_table(freqs, spectrum)
                log_done()
                log_section("flux estimation")
                # Calcular flujo usando FluxCalculator y método seleccionado
                # Para cada sensor, usar el sensor actual y el siguiente (si existe)
                if i < n_sensores - 1:
                    depth1 = depth_m
                    depth2 = ((i+2) * 10) / 100.0
                    df_metodo = {
                        depth1: {'amplitude': spectrum[0] if len(spectrum) > 0 else 1, 'phase': 0},
                        depth2: {'amplitude': spectrum[1] if len(spectrum) > 1 else 1, 'phase': 0.1}
                    }
                    flux = calc.estimate(metodo_str, df_metodo, depth1, depth2)
                else:
                    flux = 0.0
                sensitivity = 0.0  # Sensibilidad: placeholder
                if pd.isna(flux):
                    log_note(f"Advertencia: sensor {i+1} flujo no calculable, se asigna 0.")
                    flux = 0.0
                # Usar el método seleccionado para el cálculo de flujo
                # Para cada sensor, usar el sensor actual y el siguiente (si existe)
                if i < n_sensores - 1:
                    depth1 = depth_m
                    depth2 = ((i+2) * 10) / 100.0
                    df_metodo = {
                        depth1: {'amplitude': spectrum[0] if len(spectrum) > 0 else 1, 'phase': 0},
                        depth2: {'amplitude': spectrum[1] if len(spectrum) > 1 else 1, 'phase': 0.1}
                    }
                    flux = calc.estimate(metodo_str, df_metodo, depth1, depth2)
                else:
                    flux = 0.0
                sensitivity = 0.0  # Sensibilidad: placeholder
                sens_list.append(sensitivity)
                sensor_dir = f"{out_dir}/sensor_{i+1}"
                os.makedirs(sensor_dir, exist_ok=True)
                df_resampled.to_csv(f"{sensor_dir}/temperaturas_resampleadas_python.csv", index=False)
                min_len = min(len(freqs), len(spectrum))
                if min_len == 0:
                    log_note(f"Advertencia: espectro sensor {i+1} vacío, se exporta fila nula.")
                    pd.DataFrame({"freq": [0], "amplitude": [0]}).to_csv(f"{sensor_dir}/espectro_AR12_python.csv", index=False)
                else:
                    pd.DataFrame({"freq": freqs[:min_len], "amplitude": spectrum[:min_len]}).to_csv(f"{sensor_dir}/espectro_AR12_python.csv", index=False)
                pd.DataFrame({"flux": [flux]}).to_csv(f"{sensor_dir}/flujo_estimado_python.csv", index=False)
                pd.DataFrame({"sensitivity": [sensitivity]}).to_csv(f"{sensor_dir}/sensibilidad_flujo_python.csv", index=False)
                plot_spectrum(freqs[:min_len], spectrum[:min_len], sensor_dir)
                plot_flux(df_resampled, sensor_dir)
                plot_temperatures(df_sensor, sensor_dir)
                log_done()
                log_pause()
            flux_final = float(pd.Series(flux_list).mean())
            sens_final = float(pd.Series(sens_list).mean())
            pd.DataFrame({"flux_final": [flux_final], "sens_final": [sens_final]}).to_csv(f"{out_dir}/resultados_finales.csv", index=False)
            log_flux_done()
            export_log(f"{out_dir}/registro_ejecucion.log")
