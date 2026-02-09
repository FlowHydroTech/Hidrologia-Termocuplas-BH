import sys
import time

ENABLE_PAUSES = False  # Cambia a True para activar pausas tipo MATLAB
LOG_FILE = "registro_ejecucion.log"
_log_buffer = []

def log(msg, end="\n"):
    print(msg, end=end, flush=True)
    _log_buffer.append(msg + end)

def log_header():
    log("=== INICIO EJECUCIÓN VFLUX2 ===")
    log("")
    log("%% ============================")
    log("%  4) Formatear estructura VFLUX")
    log("% =============================")

def log_beginning(title):
    log(f"Beginning {title} . . .")

def log_note(msg):
    log(f"Note: {msg}")

def log_done():
    log(" . . . Done!\n")

def log_section(title):
    log("")
    log("%% ============================")
    log(f"%  {title}")
    log("% =============================")

def log_processing_sensor(depth):
    log("")
    log(f"Processing sensor at {depth:.6f} meters depth . . .")

def log_spectrum_table(freqs, amps):
    log("AR(12) SPECTRUM")
    log("  Obs.    Freq.       Period          Amp.     ")
    for idx, (f, a) in enumerate(zip(freqs, amps), 1):
        period = 1.0 / f if f != 0 else 0.0
        log(f"{idx:5d}   {f:8.6f}   {period:12.6f}   {a:14.6f}")

def log_pause():
    if ENABLE_PAUSES:
        log("Pause for plot: press any key to continue.")
        input()

def log_flux_done():
    log("")
    log("=== FIN DE EJECUCIÓN VFLUX2 ===")

def export_log(path=LOG_FILE):
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(_log_buffer)
