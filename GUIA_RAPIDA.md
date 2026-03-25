# Guía Rápida — VFLUX2 Python · Hidrología Termocuplas BH

**Proyecto**: Estimación de flujos verticales de agua subterránea — Río Cuncumén 
**Método principal**: Hatch-Amplitude (2006)  
**Sensores**: iButton DS1922L en 5 termocuplas (TC1–TC5)  
**Fecha de entrega**: Marzo 2026

---

## 1. Requisitos previos

- **Python 3.12** o superior  
- **uv** (gestor de paquetes) — instalar con: `pip install uv` o desde [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/)  
- Sistema operativo: Windows 10/11, Linux o macOS  
- ~500 MB de espacio en disco (incluyendo entorno virtual)

---

## 2. Instalación paso a paso

### 2.1 Descomprimir el archivo ZIP

Extraer `Hidrologia-Termocuplas-BH_entrega_YYYYMMDD.zip` en la carpeta de trabajo.

### 2.2 Instalar dependencias y crear entorno virtual

Desde la raíz del proyecto:

```bash
cd Hidrologia-Termocuplas-BH
uv sync
```

Esto crea automáticamente el entorno virtual `.venv`, instala todas las dependencias definidas en `pyproject.toml` (numpy, pandas, scipy, matplotlib, plotly, folium, pyproj, openpyxl) y el paquete local `vfluxx`.

El archivo `uv.lock` garantiza versiones reproducibles.

> **Alternativa sin uv**: Si no se dispone de `uv`, se puede usar pip manualmente:
> ```bash
> python -m venv .venv
> # Activar: .venv\Scripts\activate (Windows) o source .venv/bin/activate (Linux/Mac)
> pip install -r requirements.txt
> pip install -e .
> ```

---

## 3. Estructura del proyecto

```
Hidrologia-Termocuplas-BH/
│
├── src/vfluxx/                  # Librería de cálculo (core)
│   ├── harmonic_analysis.py     #   Ajuste armónico 24h
│   ├── vflux_methods.py         #   Métodos Hatch, McCallum, Keery, Luce
│   ├── flux_timeseries.py       #   Series temporales ventana deslizante
│   ├── io_utils.py              #   Lectura datos iButton / Excel
│   └── preprocess.py            #   Alineación y remuestreo
│
├── scripts/                     # Scripts de ejecución directa
│   ├── config_05A.py            #   Configuración (parámetros, rutas, constantes)
│   ├── pipeline_05A.py          #   Pipeline completo (carga → exportación)
│   ├── figuras_05A.py           #   Generación de figuras estáticas
│   └── paneles_05A.py           #   Paneles interactivos (HTML)
│
├── notebooks/
│   └── 05A_datos_terreno.ipynb  # Notebook interactivo (mismo análisis)
│
├── data/                        # Datos de entrada
│   ├── Datos Termocuplas 25-02-2026/
│   │   ├── tc1/datos_filtrados_tc1.xlsx
│   │   ├── tc2/datos_filtrados_tc2.xlsx
│   │   ├── tc3/datos_filtrados_tc3.xlsx
│   │   ├── tc4/datos_filtrados_tc4.xlsx
│   │   └── tc5/datos_filtrados_tc5.xlsx
│   └── Resultados_IDIEM/
│       └── Resultados IDIEM.xlsx
│
├── tests/                       # Tests unitarios
├── pyproject.toml               # Metadatos del proyecto
├── requirements.txt             # Dependencias con versiones mínimas
└── README.md                    # Documentación completa
```

---

## 4. Ejecución

### Opción A — Scripts por línea de comandos (recomendado)

Ejecutar desde la carpeta `scripts/`:

```bash
cd scripts
```

**Paso 1: Pipeline completo** (carga datos → análisis armónico → cálculo de flujo → exportación)
```bash
uv run python pipeline_05A.py
```
Genera:
- `resultados_python/terreno_2026_hatch/resultados_05A_hatch_amplitude.xlsx` (Excel con 7 hojas)
- CSVs de flujos, confiabilidad e incertidumbre

**Paso 2: Figuras estáticas** (PNG + PDF calidad publicación)
```bash
uv run python figuras_05A.py
```
Genera en `image/terreno_2026/`:
- Series de temperatura por TC
- Ajustes armónicos 5×3
- Boxplot comparativo Hatch vs McCallum
- Barras de flujo por TC con referencia MATLAB
- Forest-plot con intervalos de confianza 95%
- Panel de series temporales de flujo
- Figuras de publicación (300 DPI)

**Paso 3: Paneles interactivos** (HTML con Plotly + Folium)
```bash
uv run python paneles_05A.py
```
Genera en `image/terreno_2026/`:
- `selector_ventana_TC{1-5}.html` — Selectores con range-slider
- `perfil_flujo_rio_05A.html` — Perfil longitudinal del río
- `panel_sig_integrado_05A.html` — Mapa SIG con capas satelital/topográfica

### Opción B — Notebook interactivo

```bash
uv run jupyter notebook notebooks/05A_datos_terreno.ipynb
```

Ejecutar todas las celdas en orden (Kernel → Restart & Run All).

---

## 5. Resultados principales

| Termocupla | Flujo Hatch-Amplitude (mm/día) | Dirección |
|:---:|:---:|:---:|
| TC1 | 347 ± 34 | ↓ Infiltración |
| TC2 | 330 ± 15 | ↓ Infiltración |
| TC3 | 1720 ± 494 | ↓ Infiltración |
| TC4 | 1740 ± 126 | ↓ Infiltración |
| TC5 | 220 ± 117 | ↓ Infiltración |

- **Promedio global**: 871 mm/día
- **Índice de confiabilidad**: IC = 0.573
- **Incertidumbre relativa**: ±17.3%

---

## 6. Nota sobre codificación (Windows)

Los scripts usan caracteres Unicode para la salida en consola. En Windows, si aparecen caracteres extraños, ejecutar antes:

```powershell
$env:PYTHONIOENCODING = "utf-8"
```

O combinado con uv:
```powershell
$env:PYTHONIOENCODING = "utf-8"; uv run python scripts/pipeline_05A.py
```

O bien ejecutar directamente:
```powershell
$env:PYTHONIOENCODING = "utf-8"; python pipeline_05A.py
```

---

## 7. Tests

Para ejecutar los tests unitarios:

```bash
cd ..
uv run pytest tests/ -v
```

---

## 8. Contacto

Para consultas técnicas sobre el análisis o los resultados, contactar al equipo de desarrollo Flow.
