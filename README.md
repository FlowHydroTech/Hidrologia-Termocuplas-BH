
# VFLUX2 Python — Monitoreo Térmico de Intercambio Hídrico

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Implementación en Python del método VFLUX2 (MATLAB) para estimar flujos verticales de agua subterránea mediante el análisis de señales térmicas diurnas en lechos de ríos.

---

## Descripción

Este proyecto procesa datos de sensores iButton DS1922L desplegados en termocuplas verticales (TC) instaladas en el lecho de un río. Implementa 5 métodos analíticos para calcular el flujo vertical:

| Método | Referencia | Descripción |
|--------|-----------|-------------|
| **McCallum** | McCallum et al. (2012) | Ratio de amplitudes + desfase combinado |
| **Hatch-Amplitude** | Hatch et al. (2006) | Solo atenuación de amplitud |
| **Hatch-Phase** | Hatch et al. (2006) | Solo desfase temporal |
| **Keery** | Keery et al. (2007) | Variante europea |
| **Luce** | Luce et al. (2013) | Difusividad efectiva |

---

## Estructura del Proyecto

```
Hidrologia-Termocuplas-BH/
├── data/
│   ├── raw/Datos_Terreno/              # Datos iButton crudos (.csv)
│   ├── Datos Termocuplas 25-02-2026/   # Datos filtrados (período extendido)
│   │   ├── tc1/, tc3/, tc5/            # Carpetas por termocupla
│   │   └── datos_filtrados_tcX.xlsx    # Excel con datos procesados
│   ├── processed/                       # Resultados intermedios
│   └── thermal_properties/              # Parámetros térmicos
├── image/                               # Visualizaciones generadas
│   └── panel_sig_integrado.html         # Mapa SIG interactivo
├── notebooks/
│   └── 05_datos_terreno.ipynb           # Notebook principal de análisis
├── resultados_python/                   # Salidas del procesamiento
│   └── datos_terreno/                   # Resultados por campaña
├── scripts/                             # Scripts de procesamiento
│   ├── procesar_datos_terreno.py        # Script principal automatizado
│   ├── analyze_sensors.py               # Análisis exploratorio
│   ├── check_outliers.py                # Detección de outliers
│   └── generate_tc_plots.py             # Generación de gráficos
├── src/vfluxx/                          # Librería Python
│   ├── io_utils.py                      # Carga de datos iButton
│   ├── preprocess.py                    # Alineación y remuestreo
│   ├── harmonic_analysis.py             # Ajuste armónico 24h
│   └── vflux_methods.py                 # 5 métodos de flujo
├── tests/                               # Tests unitarios
└── doc/                                 # Documentación técnica
```

---

## Instalación

### Requisitos
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (gestor de paquetes recomendado)

### Pasos

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/Hidrologia-Termocuplas-BH.git
cd Hidrologia-Termocuplas-BH

# Crear entorno virtual e instalar dependencias
uv venv
uv sync

# Activar entorno (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activar entorno (Linux/Mac)
source .venv/bin/activate
```

---

## Uso

### 1. Script Automatizado (Recomendado)

El script `procesar_datos_terreno.py` ejecuta el pipeline completo de 8 pasos:

```bash
# Procesar con configuración por defecto
python scripts/procesar_datos_terreno.py

# Especificar directorio de datos
python scripts/procesar_datos_terreno.py --data-dir data/raw/Nueva_Campaña

# Especificar directorio de salida
python scripts/procesar_datos_terreno.py --output-dir resultados/campaña_02

# Ver ayuda completa
python scripts/procesar_datos_terreno.py --help
```

**Pipeline de procesamiento:**
1. Carga de archivos iButton (.csv)
2. Mapeo sensor_id → termocupla
3. Alineación temporal y remuestreo
4. Control de calidad y estadísticas
5. Análisis armónico (ciclo 24h)
6. Cálculo de flujos (5 métodos)
7. Generación de visualizaciones
8. Exportación de resultados

**Salidas generadas:**
```
resultados_python/datos_terreno/
├── flujos_todos_metodos.csv       # Flujos por par de sensores
├── estadisticas_sensores.csv      # Estadísticas descriptivas
├── temperaturas_alineadas.csv     # Series temporales procesadas
├── analisis_armonico.csv          # Amplitudes, fases, R²
├── mapeo_sensores.csv             # Mapeo sensor → TC
├── resumen_procesamiento.xlsx     # Excel con 6 hojas
└── figuras/
    ├── series_temperatura_TC*.png # Series por termocupla
    ├── flujos_comparacion.png     # Comparación entre métodos
    ├── perfiles_amplitud.png      # Atenuación con profundidad
    └── mapa_sig_flujos.html       # Mapa interactivo
```

### 2. Notebook Interactivo

Para análisis exploratorio y visualizaciones interactivas:

```bash
# Abrir con Jupyter
jupyter notebook notebooks/05_datos_terreno.ipynb

# O abrir directamente en VS Code
code notebooks/05_datos_terreno.ipynb
```

El notebook incluye:
- Carga y mapeo de sensores iButton
- Control de calidad y estadísticas
- Visualización de series temporales
- Análisis armónico (ciclo 24h)
- Cálculo de flujos (5 métodos)
- **Mapa SIG interactivo** con popups Plotly

### 3. Scripts Auxiliares

```bash
# Análisis exploratorio de sensores
python scripts/analyze_sensors.py

# Detección de outliers
python scripts/check_outliers.py

# Generación de gráficos específicos
python scripts/generate_tc_plots.py
```

---

## Configuración de Sensores

Edita la configuración en `scripts/procesar_datos_terreno.py`:

```python
SENSOR_CONFIG = {
    "TC1": {
        "surface":      {"sensor_id": "A400000082BAF041", "depth_m": 0.00},
        "intermediate": {"sensor_id": "7D000000828FA841", "depth_m": 0.28},
        "deep":         {"sensor_id": "5900000082B86A41", "depth_m": 0.56},
    },
    "TC3": {
        "surface":      {"sensor_id": "F60000008290D841", "depth_m": 0.00},
        "intermediate": {"sensor_id": "2D00000082925E41", "depth_m": 0.20},
        "deep":         {"sensor_id": "B3000000828F2741", "depth_m": 0.40},
    },
    "TC5": {
        "surface":      {"sensor_id": "3800000082B9FA41", "depth_m": 0.00},
        "intermediate": {"sensor_id": "4800000082B90241", "depth_m": 0.28},
        "deep":         {"sensor_id": "B300000082B8E441", "depth_m": 0.56},
    },
}

STATION_COORDS_UTM = {
    "TC1": {"easting": 347285, "northing": 6473381},  # UTM 19S
    "TC3": {"easting": 347087, "northing": 6472284},
    "TC5": {"easting": 346618, "northing": 6471135},
}
```

---

## Parámetros Térmicos

Valores por defecto para sedimentos fluviales típicos:

```python
thermal_params = {
    "lambda_s": 1.8,      # Conductividad térmica [W/m·K]
    "C_s": 2.8e6,         # Capacidad calorífica sedimento [J/m³·K]
    "C_w": 4.18e6,        # Capacidad calorífica agua [J/m³·K]
    "n": 0.30,            # Porosidad [-]
    "period_hours": 24,   # Período armónico [h]
}
```

---

## Visualización SIG Interactiva

El mapa interactivo (`image/panel_sig_integrado.html`) incluye:

- **Mapa base**: Satélite ESRI / Topográfico / Etiquetas
- **Marcadores TC**: Clic para abrir popup con gráficos
- **Popup interactivo**:
  - Series de temperatura (3 profundidades)
  - Barras de flujo (4 métodos)
  - Perfil de amplitud + fase
  - Tabla resumen McCallum
- **Controles**: Medición, pantalla completa, minimapa

> El archivo HTML es autocontenido y se puede compartir por email/USB.

---

## Resultados Ejemplo

### Campaña Diciembre 2025 — Febrero 2026 (Actualizado)

| Termocupla | q̄ McCallum (mm/d) | σ (mm/d) | R² superficie | Período |
|------------|-------------------|----------|---------------|---------|
| TC1 | 73.9 | 205 | 0.847 | 66 días |
| TC3 | 81.7 | 98.9 | 0.752 | 66 días |
| TC5 | 78.9 | 208.6 | 0.825 | 66 días |

**Métricas de calidad:**
- Correlación McCallum vs Hatch-Amplitud: **r = 0.833**
- ~132 ciclos diurnos analizados
- Ventanas de análisis: 48h con paso de 12h

> **Nota**: Los datos de verano (Dic-Feb) muestran señales diurnas más fuertes (R² > 0.82) comparados con datos de invierno, mejorando la confiabilidad de las estimaciones.

---

## API de la Librería

```python
from vfluxx.io_utils import load_all_ibuttons, ibuttons_to_dataframe
from vfluxx.preprocess import align_and_resample
from vfluxx.harmonic_analysis import fit_harmonic_model
from vfluxx.vflux_methods import calculate_vflux_all_methods

# Cargar datos
sensors = load_all_ibuttons("data/raw/Datos_Terreno")
df_raw = ibuttons_to_dataframe(sensors, sensor_labels)

# Preprocesar
df_aligned = align_and_resample(df_raw, freq="30min")

# Análisis armónico
harmonic = fit_harmonic_model(df_aligned["fecha"], df_aligned["temp"])

# Calcular flujos
flux = calculate_vflux_all_methods(
    A_shallow=h1["amplitude"],
    A_deep=h2["amplitude"],
    phase_shallow=h1["phase"],
    phase_deep=h2["phase"],
    dz=0.28,
    thermal_params=thermal_params
)
```

---

## Referencias

- **VFLUX2**: Gordon, R.P. et al. (2012). VFLUX: A MATLAB program for calculating vertical fluxes. *Groundwater*, 50(5), 710-719.
- **McCallum et al. (2012)**: A one-dimensional analytical model for estimating surface water–groundwater exchange. *Water Resources Research*, 48, W12510.
- **Hatch et al. (2006)**: Quantifying surface water–groundwater interactions using time series analysis. *Water Resources Research*, 42, W09410.
- **Keery et al. (2007)**: Temporal and spatial variability of groundwater–surface water fluxes. *Journal of Hydrology*, 344, 188-198.
- **Luce et al. (2013)**: Solutions for the diurnally forced advection-diffusion equation. *Water Resources Research*, 49, 439-455.

---

## Licencia

MIT License — ver [LICENSE](LICENSE)

---

## Contacto

Proyecto Hidrología-Termocuplas-BH  
Flow Hydro - Tecnología

---

*Última actualización: Febrero 2025*