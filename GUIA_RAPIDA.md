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
├── scripts/                     # Scripts de ejecución
│   ├── config_05A.py            #   Configuración (parámetros, rutas, constantes)
│   ├── pipeline_05A.py          #   Pipeline de cálculo (carga → exportación)
│   ├── figuras_05A.py           #   10 figuras estáticas (PNG + PDF)
│   ├── paneles_05A.py           #   4 paneles interactivos (Plotly + Folium)
│   ├── prefect_pipeline.py      #   Orquestador Prefect (11 etapas + dashboard)
│   ├── run_pipeline.py          #   Ejecución Python pura (sin servidor)
│   └── stages/                  #   Tareas Prefect modularizadas (11 stages)
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
├── Dockerfile                   # Imagen Docker multi-stage
├── docker-compose.yml           # 3 modos de ejecución Docker
├── pyproject.toml               # Metadatos del proyecto
├── requirements.txt             # Dependencias con versiones mínimas
├── GUIA_RAPIDA.md / .txt        # Esta guía (Markdown + texto plano)
├── GLOSARIO_TECNICO.md          # Glosario de términos técnicos
└── README.md                    # Documentación completa
```

---

## 4. Ejecución — 3 modos disponibles

### Modo A — Python puro (el más simple)

Ejecuta las 11 etapas del pipeline sin servidor ni dashboard:

```bash
python scripts/run_pipeline.py
```

> **Con uv**: `uv run python scripts/run_pipeline.py`

### Modo B — Prefect + Dashboard interactivo

Requiere dos terminales:

```bash
# Terminal 1: Iniciar servidor Prefect
prefect server start

# Terminal 2: Ejecutar pipeline
python scripts/prefect_pipeline.py
```

Dashboard disponible en: **http://localhost:4200**

Flags opcionales:
- `--no-figs` — Omitir generación de figuras
- `--no-html` — Omitir paneles HTML
- `--no-server` — No verificar servidor Prefect

### Modo C — Docker (contenedores)

Requiere Docker Desktop instalado y en ejecución.

```bash
# Completo: Pipeline + Dashboard Prefect
docker compose up

# Solo pipeline Python puro (sin Prefect)
docker compose run --rm standalone

# Solo Dashboard Prefect
docker compose up prefect
```

Dashboard Docker: **http://localhost:4200**

### Pipeline: 11 etapas

| # | Etapa | Descripción |
|:-:|:------|:------------|
| 1 | Carga | Lectura de datos iButton (5 TC × 3 sensores) |
| 2 | Alineación | Alineación temporal a grilla común 10 min |
| 3 | Armónico | Ajuste armónico 24 h por sensor |
| 4 | Flujo | Cálculo Hatch-Amplitude + McCallum |
| 5 | Series | Series temporales ventana deslizante 48 h |
| 6 | Confiabilidad | Índice IC por termocupla |
| 7 | Incertidumbre | Bootstrap + propagación δλ, δC |
| 8 | IQR | Tabla estadística por par de sensores |
| 9 | Exportación | Excel 7 hojas + CSVs |
| 10 | Resumen | Resumen ejecutivo en consola |
| 11a | Figuras | 10 figuras estáticas (PNG + PDF, 300 DPI) |
| 11b | Paneles | 4 paneles HTML interactivos |

### Archivos de salida

Directorio consolidado: `data/processed/resultados_20260325/`

**Resultados** (`resultados/`):
- `resultados_05A_hatch_amplitude.xlsx` — Excel con 7 hojas
- CSVs de flujos, confiabilidad, incertidumbre, IQR
- `resumen_estadistico_tendencia_central_MAD.csv` + `.xlsx` — Tabla estadística filtrada
- `series_temporales/` — CSVs de flujo por TC

**Figuras** (`figuras/` — PNG + PDF, 300 DPI):
- Series de temperatura por TC
- Ajustes armónicos 5×3
- Boxplot comparativo Hatch vs McCallum
- Barras de flujo por TC con referencia MATLAB
- Forest-plot con intervalos de confianza 95%
- Series temporales de flujo con bandas MATLAB
- Boxplot y series de publicación (estilo Flow v3)
- **Series tendencia central** (filtrado MAD)
- **Boxplot tendencia central** (filtrado MAD)

**Paneles interactivos** (`contenido_web/`):
- `selector_ventana_TC{1-5}.html` — Selectores con range-slider
- `perfil_flujo_rio_05A.html` — Perfil longitudinal del río
- `panel_sig_integrado_05A.html` — Mapa SIG con capas satelital/topográfica
- `panel_sig_tendencia_central_mad.html` — **Mapa interactivo tendencia central MAD**

### Opción legacy — Notebook interactivo

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
