# Capítulo 4: Procesamiento y Visualización de Datos

## 4.1 Descripción general

Para estimar el flujo de agua entre el río y el acuífero se desarrolló un programa computacional en lenguaje Python que automatiza todo el proceso de cálculo, desde la lectura de los datos de temperatura registrados en terreno hasta la generación de tablas, gráficos y mapas con los resultados finales.

El programa se basa en la metodología VFLUX2 (Gordon et al., 2012), que permite cuantificar el flujo vertical de agua a través del lecho de un río utilizando las variaciones diarias de temperatura medidas a distintas profundidades en el sedimento.

## 4.2 Datos de entrada

Los datos provienen de 15 sensores de temperatura tipo iButton (modelos DS1922L y DS1923), instalados en cinco estaciones de medición (TC1 a TC5) a lo largo del tramo de estudio del Río Silala. En cada estación se colocaron tres sensores a distintas profundidades bajo el lecho del río.

Los sensores registraron la temperatura cada 30 minutos durante el periodo comprendido entre el 21 de diciembre de 2025 y el 25 de febrero de 2026.

## 4.3 Etapas del procesamiento

El proceso computacional se organiza en las siguientes etapas secuenciales:

### Etapa 1 — Carga y preparación de datos

El programa lee los archivos generados por cada sensor, identifica automáticamente a qué estación y profundidad corresponde cada uno, y sincroniza todas las mediciones en una grilla temporal uniforme de 30 minutos. Se aplica un control de calidad para eliminar valores anómalos y recortar los periodos válidos por estación.

### Etapa 2 — Análisis armónico

Se ajusta una curva sinusoidal de periodo 24 horas a la señal de temperatura de cada sensor, extrayendo dos parámetros clave: la amplitud (cuánto varía la temperatura durante el día) y la fase (en qué momento del día ocurre el máximo). Estos parámetros se calculan para cada par de sensores ubicados a diferente profundidad dentro de una misma estación.

### Etapa 3 — Parámetros térmicos del sedimento

Se incorporan las propiedades térmicas del sedimento de cada estación, determinadas mediante ensayos de laboratorio realizados por el IDIEM (Universidad de Chile). Estos parámetros incluyen la conductividad térmica, la capacidad calórica del sólido y la dispersividad del grano, que caracterizan cómo conduce calor el material del lecho.

### Etapa 4 — Cálculo del flujo vertical

Con los datos armónicos y las propiedades del sedimento, el programa resuelve la ecuación de transporte de calor propuesta por Hatch et al. (2006), que relaciona la atenuación y el desfase de la señal térmica con la velocidad del agua que fluye verticalmente a través del sedimento.

El método principal utilizado es **Hatch-Amplitude**, que estima el flujo a partir de la razón de amplitudes entre las profundidades de medición. Como validación complementaria, se aplica el método de **McCallum et al. (2012)**, que combina información de amplitud y fase.

La ecuación se resuelve de forma numérica, ya que el flujo aparece de manera implícita en la fórmula. El programa utiliza un algoritmo de búsqueda de raíces que converge a la solución en fracciones de segundo.

### Etapa 5 — Generación de resultados

El programa calcula el flujo medio por estación y sus estadísticas descriptivas (mediana, rango intercuartil). Adicionalmente, se calculan:

- Un **índice de confiabilidad** que integra la calidad del ajuste armónico, la concordancia entre métodos y la coherencia física de los resultados.
- Una **estimación de incertidumbre** basada en la propagación de errores en los parámetros de entrada.
- La **comparación con los resultados del software MATLAB VFLUX2** como referencia de validación cruzada.

### Etapa 6 — Visualización y exportación

El programa genera automáticamente:

- **Gráficos de series de temperatura** para cada estación, mostrando las tres profundidades de medición.
- **Gráficos del ajuste armónico** superpuestos a los datos medidos.
- **Barras comparativas** del flujo estimado por estación con la referencia MATLAB.
- **Diagramas de caja** (boxplot) comparando los dos métodos de cálculo.
- **Series temporales de flujo** calculadas con ventanas deslizantes de 48 horas, que muestran la evolución del intercambio de agua durante todo el periodo de medición.
- **Mapas interactivos** con las ubicaciones de las estaciones y ventanas emergentes que despliegan las estadísticas y gráficos principales de cada punto.

Todos los resultados se exportan en formato Excel (con múltiples hojas temáticas), archivos CSV para análisis posterior, y archivos HTML para visualización interactiva en navegador web.

## 4.4 Resultados principales

El flujo promedio estimado para las cinco estaciones es de aproximadamente **443 mm/día** en dirección descendente, lo que indica **infiltración del río hacia el acuífero** en el tramo estudiado. Los valores varían entre 220 y 678 mm/día dependiendo de la estación, reflejando la heterogeneidad del lecho del río.

## 4.5 Resultados

Todo el procesamiento queda registrado en un cuaderno computacional interactivo (notebook Jupyter) que documenta cada paso junto con su resultado, permitiendo verificar, auditar o repetir el análisis completo en cualquier momento. El cuaderno `05A_datos_terreno.ipynb` contiene 47 celdas organizadas secuencialmente —código, texto explicativo y salidas gráficas— que conforman un documento ejecutable y autocontenido.

### 4.5.1 Cuaderno computacional (Jupyter Notebook)

El notebook constituye el registro primario del análisis. Cada celda de código produce una salida visible (tabla, gráfico o mensaje de diagnóstico) que queda almacenada dentro del propio archivo `.ipynb`, de modo que cualquier revisor puede inspeccionar los resultados sin necesidad de ejecutar el programa. Las celdas de texto intercaladas explican la metodología, las ecuaciones empleadas y los criterios de decisión adoptados en cada etapa.

El cuaderno se ejecuta de forma lineal: basta presionar *Run All* en el entorno Jupyter (o VS Code) para reproducir la totalidad del análisis, desde la lectura de datos crudos hasta la generación de figuras y tablas finales.

### 4.5.2 Scripts de Python (.py)

Como alternativa al notebook, el mismo procesamiento puede ejecutarse mediante archivos nativos de Python con extensión `.py`, ubicados en el directorio `scripts/`. Esta modalidad resulta conveniente para ejecuciones desatendidas, integración en flujos de trabajo automatizados o despliegue en servidores sin interfaz gráfica.

Los scripts disponibles son:

| Script | Función |
|---|---|
| `config_05A.py` | Configuración compartida: rutas, mapeo sensor → TC → profundidad, parámetros térmicos IDIEM y constantes del análisis. |
| `pipeline_05A.py` | Pipeline completo de procesamiento (replica las celdas 1–20 del notebook): carga de datos, alineación temporal, análisis armónico, cálculo de flujo Hatch-Amplitude y McCallum, series temporales con ventanas deslizantes, métricas de confiabilidad, propagación de incertidumbre y exportación a Excel/CSV. |
| `figuras_05A.py` | Generación de las 10 familias de figuras: series de temperatura por TC, ajustes armónicos, boxplot comparativo, barras de flujo con referencia MATLAB, forest-plot con intervalos de confianza al 95 %, series temporales de flujo por TC, paneles combinados y figuras de publicación (PDF 300 dpi). |
| `paneles_05A.py` | Generación de paneles interactivos HTML: selector de ventana temporal por TC, perfil longitudinal de flujo a lo largo del río y panel SIG integrado con mapa, series y estadísticas. |

Para ejecutar el procesamiento completo desde la línea de comandos:

```bash
# Instalar dependencias (una sola vez)
uv sync

# Ejecutar el pipeline de cálculo
uv run python scripts/pipeline_05A.py

# Generar figuras estáticas (PNG/PDF)
uv run python scripts/figuras_05A.py

# Generar paneles interactivos (HTML)
uv run python scripts/paneles_05A.py
```

Ambas vías de ejecución —notebook y scripts— producen resultados idénticos, ya que comparten la misma base de código del paquete `vfluxx` y la misma configuración centralizada en `config_05A.py`.

## 4.6 Exportación de Resultados

El programa exporta todos los resultados a una estructura organizada de archivos dentro del directorio `data/processed/resultados_24032026/`, que se describe a continuación.

### 4.6.1 Libro Excel multihoja

El archivo principal de resultados es `resultados_05A_hatch_amplitude.xlsx`, que contiene siete hojas temáticas:

| Hoja | Contenido |
|---|---|
| **Flujos_HA_McCallum** | Flujo vertical estimado (mm/día) por cada par de sensores y por ambos métodos (Hatch-Amplitude y McCallum). |
| **Flujo_Promedio_TC** | Flujo promedio por estación (TC1–TC5), calculado como la media de los tres pares de profundidad de cada TC. |
| **IQR_Hatch_Amplitude** | Estadísticas descriptivas del flujo (mediana, percentiles 25 y 75, rango intercuartil) incluyendo la referencia de resultados MATLAB VFLUX2. |
| **Confiabilidad** | Índice de confiabilidad por estación, que integra la calidad del ajuste armónico ($R^2$), la concordancia entre métodos y la coherencia física. |
| **Incertidumbre** | Propagación analítica de errores: incertidumbre del flujo estimada a partir de las incertidumbres en amplitud, profundidad y parámetros térmicos. |
| **Analisis_Armonico** | Amplitudes y fases del ajuste sinusoidal (24 h) para cada sensor, con indicadores de bondad de ajuste. |
| **Params_IDIEM** | Propiedades térmicas del sedimento por estación, determinadas por ensayos de laboratorio IDIEM (conductividad térmica $\lambda$, capacidad calórica $C_s$, dispersividad térmica $\alpha$, conductividad hidráulica $K_v$, clasificación USCS). |

### 4.6.2 Archivos CSV

Se generan archivos de valores separados por comas para facilitar la lectura desde cualquier herramienta de análisis:

- `flujos_hatch_mccallum.csv` — Flujos por par de sensores y método.
- `confiabilidad_hatch_mccallum.csv` — Índice de confiabilidad por estación.
- `incertidumbre_hatch.csv` — Incertidumbre propagada del flujo.
- `tabla_iqr_hatch_amplitude.csv` — Estadísticas IQR con referencia MATLAB.
- `estadisticos_ventana_2026-02-01_2026-02-20.csv` — Estadísticos calculados sobre la ventana temporal seleccionada.

### 4.6.3 Series temporales

El subdirectorio `series_temporales/` contiene la evolución temporal del flujo calculado con ventanas deslizantes de 48 horas y paso de 12 horas:

- **15 archivos individuales** (`flujo_temporal_TC{1–5}_{sup_int,int_inf,sup_inf}.csv`): serie de flujo para cada par de profundidades de cada estación.
- `series_flujo_todas_TC.csv` — Serie de flujo consolidada de las cinco estaciones.
- `temperatura_todas_TC.csv` — Series de temperatura consolidadas de los 15 sensores.
- Subdirectorio `por_tc/` — Series agrupadas por estación: un archivo de flujo (`series_flujo_TC*.csv`) y uno de temperatura (`temperatura_TC*.csv`) por cada TC.

### 4.6.4 Figuras

El subdirectorio `figuras/` almacena las visualizaciones generadas en tres formatos:

**Formato PNG (300 dpi)** — Para inclusión directa en informes y presentaciones:

- Series de temperatura por estación (`temperatura_TC{1–5}_05A.png`).
- Ajustes armónicos superpuestos a datos medidos (`ajustes_armonicos_05A.png`).
- Boxplot comparativo de métodos Hatch-Amplitude y McCallum (`boxplot_hatch_05A.png`).
- Barras de flujo por estación con referencia MATLAB (`barras_hatch_mccallum_05A.png`).
- Forest-plot con intervalos de confianza al 95 % (`flujo_ic95_informe_cap4.png`).
- Series temporales de flujo por estación (`flujo_TC{1–5}_05A.png`).
- Panel combinado de series temporales (`series_temporales_hatch_05A.png`).
- Series de flujo Hatch de las 5 TC (`series_flujo_hatch_5TC.png`).

**Formato PDF (vectorial)** — Para publicación en alta calidad:

- `boxplot_hatch_amplitude_informe.pdf`
- `flujo_ic95_informe_cap4.pdf`
- `flux_hatch_amplitude_TC{1–5}.pdf`
- `series_temporales_hatch_informe.pdf`
- `series_flujo_hatch_5TC.pdf`

**Formato HTML (interactivo)** — Para exploración dinámica en navegador web:

- `selector_ventana_TC{1–5}.html` — Selector interactivo de ventana temporal por estación, con visualización simultánea de temperatura y flujo.
- `perfil_flujo_rio_05A.html` — Perfil longitudinal de flujo a lo largo del tramo de estudio.
- `panel_sig_integrado_05A.html` — Panel SIG integrado que combina mapa de ubicaciones, series de temperatura, estadísticas de flujo y gráficos comparativos en una sola vista interactiva.
- `comparacion_tc_05A.html` — Comparación interactiva entre estaciones.
- `scatter_hatch_vs_mccallum_05A.html` — Diagrama de dispersión Hatch vs. McCallum.
- `panel_series_temporales_05A.html` — Panel interactivo con todas las series temporales.

### 4.6.5 Estructura del directorio de salida

```
data/processed/resultados_24032026/
├── resultados_05A_hatch_amplitude.xlsx
├── flujos_hatch_mccallum.csv
├── confiabilidad_hatch_mccallum.csv
├── incertidumbre_hatch.csv
├── tabla_iqr_hatch_amplitude.csv
├── estadisticos_ventana_2026-02-01_2026-02-20.csv
├── datos_terreno/
│   ├── tabla_iqr_hatch_amplitude.csv
│   └── tabla_iqr_hatch_amplitude.xlsx
├── series_temporales/
│   ├── flujo_temporal_TC1_sup_int.csv
│   ├── flujo_temporal_TC1_int_inf.csv
│   ├── flujo_temporal_TC1_sup_inf.csv
│   ├── ... (15 archivos, 3 por cada TC)
│   ├── series_flujo_todas_TC.csv
│   ├── temperatura_todas_TC.csv
│   └── por_tc/
│       ├── series_flujo_TC1.csv
│       ├── temperatura_TC1.csv
│       └── ... (10 archivos, 2 por cada TC)
└── figuras/
    ├── *.png    (figuras estáticas, 300 dpi)
    ├── *.pdf    (figuras vectoriales para publicación)
    └── *.html   (paneles interactivos)
```
