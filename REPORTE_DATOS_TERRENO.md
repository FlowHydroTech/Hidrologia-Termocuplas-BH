# Reporte de Análisis de Datos de Terreno — VFLUX2 Python

## Estimación de Flujos Verticales en Zona Hiporreica mediante Trazado Térmico

**Proyecto:** Hidrología – Termocuplas BH  
**Fecha de análisis:** Enero 2026  
**Notebook:** `notebooks/05_datos_terreno.ipynb`  
**Autores:** [Completar]  

---

## 1. Introducción

Este reporte documenta el análisis completo de datos de terreno obtenidos mediante sensores de temperatura iButton instalados en el lecho de un cauce. La metodología se basa en la implementación en Python del software VFLUX2 (Gordon et al., 2012), que estima flujos verticales de intercambio agua superficial–subterránea a partir de la propagación de señales térmicas diurnas en el sedimento.

### 1.1 Marco Teórico

La ecuación de transporte de calor 1D en un medio poroso saturado con flujo vertical es:

$$\frac{\partial T}{\partial t} = \kappa_e \frac{\partial^2 T}{\partial z^2} - \frac{n_f C_w}{C_s} v_f \frac{\partial T}{\partial z}$$

donde:
- $T$ = temperatura [°C]
- $\kappa_e = \lambda / C_s$ = difusividad térmica efectiva [m²/s]
- $\lambda$ = conductividad térmica del sedimento [W/m·K]
- $C_s$ = capacidad calórica volumétrica del sedimento [J/m³·K]
- $C_w$ = capacidad calórica volumétrica del agua [J/m³·K]
- $v_f$ = velocidad de Darcy vertical [m/s]
- $n_f$ = porosidad efectiva [-]

La señal térmica diurna se propaga como una onda amortiguada, cuya atenuación de amplitud y desfasamiento con la profundidad permiten estimar el flujo vertical.

---

## 2. Configuración de Campo

### 2.1 Instrumentación

| Parámetro | Valor |
|-----------|-------|
| **Termocuplas** | 2 (TC1, TC5) |
| **Sensores por termocupla** | 3 (superficie, intermedio, inferior) |
| **Total sensores** | 6 iButton |
| **Intervalo de muestreo** | 30 minutos |
| **Periodo de monitoreo** | 21-Dic-2025 a 22-Ene-2026 (~33 días) |

### 2.2 Profundidades de Instalación

| Posición | Profundidad (mbnt) | Descripción |
|----------|-------------------|-------------|
| Superficie | 0.00 m | Interfaz agua-sedimento |
| Intermedio | 0.28 m | Zona media del perfil |
| Inferior | 0.56 m | Base del perfil de monitoreo |

**Nota:** mbnt = metros bajo nivel de terreno. Las separaciones entre sensores son constantes: Δz = 0.28 m.

### 2.3 Mapeo de Sensores

| Termocupla | Posición | Sensor ID | Tipo | Profundidad |
|------------|----------|-----------|------|-------------|
| TC1 | Superficie | A400000082BAF041 | DS1923 | 0.00 m |
| TC1 | Intermedio | 7D000000828FA841 | DS1922L | 0.28 m |
| TC1 | Inferior | 5900000082B86A41 | DS1923 | 0.56 m |
| TC5 | Superficie | 3800000082952A41 | DS1922L | 0.00 m |
| TC5 | Intermedio | B000000082987741 | DS1922L | 0.28 m |
| TC5 | Inferior | 2800000082978041 | DS1922L | 0.56 m |

**Resolución de sensores:**
- DS1922L: 0.0625°C (alta resolución)
- DS1923: 0.5°C (resolución estándar)

El mapeo sensor→profundidad fue verificado comparando los rangos de amplitud térmica de cada sensor con las gráficas de referencia generadas por VFLUX2 en MATLAB.

---

## 3. Parámetros Térmicos del Sedimento

| Parámetro | Símbolo | Valor | Unidad |
|-----------|---------|-------|--------|
| Conductividad térmica | λ | 1.80 | W/m·K |
| Capacidad calórica sedimento | Cₛ | 2.80 × 10⁶ | J/m³·K |
| Capacidad calórica agua | Cw | 4.18 × 10⁶ | J/m³·K |
| Difusividad térmica efectiva | κₑ | 6.43 × 10⁻⁷ | m²/s |
| Frecuencia angular (P=24h) | ω | 7.27 × 10⁻⁵ | rad/s |
| Longitud de penetración | d | 0.133 | m |

La longitud de penetración $d = \sqrt{2\kappa_e / \omega} = 0.133$ m indica que la señal diurna se atenúa al 37% a 13.3 cm de profundidad. Con sensores a 56 cm, la señal experimenta una atenuación significativa (~1.5% de la amplitud superficial).

---

## 4. Estadísticas Descriptivas

### 4.1 Resumen por Termocupla y Profundidad

| TC | Posición | Prof (cm) | N | T̄ (°C) | T_min (°C) | T_max (°C) | Rango (°C) | σ (°C) |
|----|----------|-----------|---|---------|------------|------------|------------|--------|
| TC1 | Superficie | 0 | 1560 | 17.50 | 13.06 | 23.76 | 10.70 | 2.700 |
| TC1 | Intermedio | 28 | 1560 | 17.53 | 14.73 | 20.30 | 5.57 | 1.170 |
| TC1 | Inferior | 56 | 1560 | 17.65 | 16.51 | 19.08 | 2.57 | 0.467 |
| TC5 | Superficie | 0 | 1560 | 18.21 | 14.23 | 22.75 | 8.52 | 2.122 |
| TC5 | Intermedio | 28 | 1560 | 18.20 | 16.38 | 19.38 | 3.00 | 0.672 |
| TC5 | Inferior | 56 | 1560 | 18.01 | 16.45 | 19.08 | 2.63 | 0.613 |

### 4.2 Observaciones

- El rango térmico decrece con la profundidad en ambas termocuplas: comportamiento esperado para la propagación conductiva-advectiva de calor.
- TC1 superficie muestra mayor variabilidad (σ = 2.7°C) que TC5 (σ = 2.1°C), sugiriendo mayor exposición solar o menor protección riparia.
- Las temperaturas medias son similares entre TC1 (17.5°C) y TC5 (18.1°C), indicando condiciones térmicas comparables.

---

## 5. Análisis Armónico

Se ajustó un modelo sinusoidal de ciclo diario (P = 24 h) a cada serie temporal:

$$T(t) = T_0 + A \sin(\omega t + \varphi)$$

### 5.1 Resultados del Ajuste

| Sensor | TC | Prof | Amplitud A (°C) | Fase φ (°) | T₀ (°C) | R² | Calidad |
|--------|----|------|-----------------|-----------|---------|-----|---------|
| temp_5 | TC1 | 0 cm | 3.424 | 57.3 | 17.54 | 0.793 | ●●● |
| temp_4 | TC1 | 28 cm | 1.308 | 346.3 | 17.55 | 0.620 | ●●○ |
| temp_3 | TC1 | 56 cm | 0.107 | 251.3 | 17.70 | 0.010 | ●○○ |
| temp_2 | TC5 | 0 cm | 2.699 | 37.0 | 18.23 | 0.808 | ●●● |
| temp_6 | TC5 | 28 cm | 0.332 | 247.4 | 18.21 | 0.123 | ●○○ |
| temp_1 | TC5 | 56 cm | 0.169 | 109.1 | 18.01 | 0.038 | ●○○ |

**Calidad:** ●●● (R² > 0.7: fuerte) | ●●○ (R² > 0.3: moderada) | ●○○ (R² < 0.3: débil)

### 5.2 Interpretación

- **Atenuación de amplitud:** TC1: 3.42 → 1.31 → 0.11°C; TC5: 2.70 → 0.33 → 0.17°C. La amplitud decrece monotónicamente con la profundidad (✓ coherente).
- **R² en profundidad:** El bajo R² en los sensores profundos (< 0.04) indica que la señal diurna está prácticamente extinguida a 56 cm, consistente con la longitud de penetración calculada (d = 13.3 cm).
- **Sensores superficiales:** R² > 0.79 confirma una señal diurna robusta para los sensores de superficie.

---

## 6. Métodos de Estimación de Flujo

Se aplicaron 5 métodos analíticos implementados en VFLUX2:

| Método | Referencia | Usa Amplitud | Usa Fase | Observaciones |
|--------|-----------|:---:|:---:|------------|
| McCallum | McCallum et al. (2012) | ✓ | ✓ | Considera ambos: más robusto |
| Hatch-Amplitud | Hatch et al. (2006) | ✓ | ✗ | Solo atenuación de amplitud |
| Hatch-Fase | Hatch et al. (2006) | ✗ | ✓ | Solo desfasamiento |
| Keery | Keery et al. (2007) | ✓ | ✓ | Solución analítica alternativa |
| Luce | Luce et al. (2013) | ✓ | ✓ | Extensión con correcciones |

### 6.1 Ecuación de McCallum (2012) — Método Recomendado

$$v_f = \frac{2 \kappa_e}{\Delta z} \left[ \sqrt{\ln(A_r)^2 + \Delta\varphi^2} - \ln(A_r) \right] \cdot \frac{C_s}{C_w}$$

donde $A_r = A_{sup}/A_{prof}$ es el ratio de amplitudes y $\Delta\varphi$ es la diferencia de fase entre los sensores superior e inferior.

---

## 7. Resultados de Flujo Vertical

### 7.1 Tabla Completa (mm/día)

| Par | McCallum | Hatch-A | Hatch-φ | Keery | Luce |
|-----|----------|---------|---------|-------|------|
| TC1: sup→int | 246.0 | 381.7 | −6311.8 | 1191.4 | 1032.4 |
| TC1: int→inf | 624.8 | 992.6 | −5717.6 | 1413.7 | 1534.0 |
| TC1: sup→inf | 1878.1 | 687.1 | −364.0 | 679.4 | 1618.6 |
| TC5: sup→int | 650.6 | 831.1 | −4368.5 | 1144.1 | 1465.2 |
| TC5: int→inf | 225.0 | 267.0 | −4648.5 | 901.3 | 818.5 |
| TC5: sup→inf | 2390.4 | 549.1 | 389.1 | 399.5 | 1566.0 |

**Convención de signos:** (+) infiltración río→acuífero; (−) exfiltración acuífero→río.

### 7.2 Resumen por Termocupla (McCallum)

| Termocupla | q̄ (mm/día) | σ (mm/día) | Dirección |
|------------|-----------|-----------|-----------|
| TC1 | 916.3 | 697.5 | Infiltración ↓ |
| TC5 | 1088.7 | 936.7 | Infiltración ↓ |

### 7.3 Discusión de Resultados

1. **Dirección del flujo:** Ambas termocuplas indican consistentemente **infiltración** (flujo río → acuífero), lo cual es coherente con un tramo del cauce que recarga el acuífero subyacente.

2. **Método Hatch-Fase:** Produce estimaciones anómalas (valores negativos de gran magnitud) en la mayoría de los pares. Esto se debe a que el método basado únicamente en fase es muy sensible a la incertidumbre en la estimación del desfasamiento, especialmente cuando la señal diurna está fuertemente atenuada en los sensores profundos (R² < 0.05).

3. **Concordancia entre métodos:** Excluyendo Hatch-Fase, los métodos McCallum, Hatch-Amplitud, Keery y Luce producen estimaciones del mismo orden de magnitud (rango: ~225–2400 mm/día), con flujo siempre positivo (infiltración).

4. **Variabilidad entre pares:** Los pares sup→inf muestran valores más altos que sup→int o int→inf, probablemente por efecto de la mayor separación (Δz = 56 cm vs 28 cm) que amplifica la incertidumbre en las condiciones de frontera.

5. **Magnitud de los flujos:** Los valores estimados (orden de 10² a 10³ mm/día, equivalente a ~10⁻⁵ a 10⁻⁴ m/s) son elevados pero plausibles para lechos de cauces permeables con sedimentos gruesos (arenas y gravas).

---

## 8. Visualizaciones Generadas

| # | Archivo | Descripción |
|---|---------|-------------|
| 1 | `series_temperatura_terreno.png` | Series temporales completas de 6 sensores + panel ΔT |
| 2 | `temperatura_tc1_python.png` | TC1: 3 sensores, estilo MATLAB VFLUX2 |
| 3 | `temperatura_tc5_python.png` | TC5: 3 sensores, estilo MATLAB VFLUX2 |
| 4 | `tc1_tc5_python.png` | Comparación combinada TC1 y TC5 |
| 5 | `ajustes_armonicos_terreno.png` | Ajuste sinusoidal 2×3 (TC × posición, 7 días) |
| 6 | `flujos_verticales_terreno.png` | Barras de flujo agrupadas por TC y método |
| 7 | `perfil_termico_terreno.png` | Perfil vertical: atenuación de amplitud y desfase |
| 8 | `heatmap_temperatura_terreno.png` | Mapa espacio-temporal de temperatura |
| 9 | `boxplot_flujos_terreno.png` | Distribución de flujos por método y TC |

Todas las imágenes se encuentran en el directorio `image/`.

---

## 9. Datos Exportados

Los resultados numéricos se exportaron a `resultados_python/datos_terreno/`:

| Archivo | Contenido |
|---------|-----------|
| `flujos_todos_metodos.csv` | Flujos estimados por 5 métodos × 6 pares |
| `estadisticas_sensores.csv` | Estadísticas descriptivas de cada sensor |
| `temperaturas_alineadas.csv` | Series temporales alineadas a 30 min |
| `analisis_armonico.csv` | Amplitud, fase, R² por sensor |
| `mapeo_sensores.csv` | Mapeo sensor → termocupla → profundidad |

---

## 10. Control de Calidad

### 10.1 Anomalías Detectadas
- **Sensor 5900 (TC1 inferior):** Un valor atípico de 28.9°C en el último registro (2026-01-22 16:26:01), correspondiente al artefacto de extracción del sensor. Se eliminó mediante el cutoff temporal `cutoff_end = 2026-01-22 12:00:00`.

### 10.2 Limitaciones
- Los sensores DS1923 (superficie TC1 e inferior TC1) tienen resolución de 0.5°C, lo que puede introducir discretización en la señal.
- Los sensores a 56 cm presentan R² muy bajo (< 0.04) en el ajuste armónico, indicando que la señal diurna está prácticamente extinguida a esa profundidad.
- Los valores de flujo obtenidos con Hatch-Fase no son confiables y deben descartarse en el análisis.

### 10.3 Recomendaciones
1. Priorizar los resultados del **par sup→int (Δz = 28 cm)** con método **McCallum**, donde ambos sensores tienen señal diurna razonable.
2. Considerar la instalación de sensores a profundidades intermedias (10–15 cm) para capturar mejor la zona de atenuación.
3. Validar los flujos estimados con mediciones independientes (e.g., minipiezómetros, seepage meters).

---

## 11. Referencias

- Gordon, R. P., Lautz, L. K., Briggs, M. A., & McKenzie, J. M. (2012). Automated calculation of vertical pore-water flux from field temperature time series using the VFLUX method and computer program. *Journal of Hydrology*, 420–421, 142–158.
- Hatch, C. E., Fisher, A. T., Revenaugh, J. S., Constantz, J., & Ruehl, C. (2006). Quantifying surface water–groundwater interactions using time series analysis of streambed thermal records: Method development. *Water Resources Research*, 42(10).
- Keery, J., Binley, A., Crook, N., & Smith, J. W. N. (2007). Temporal and spatial variability of groundwater–surface water fluxes: Development and application of an analytical method using temperature time series. *Journal of Hydrology*, 336(1–2), 1–16.
- Luce, C. H., Tonina, D., Gariglio, F., & Applebee, R. (2013). Solutions for the diurnally forced advection-diffusion equation to estimate bulk fluid velocity and diffusivity in streambeds from temperature time series. *Water Resources Research*, 49(1), 488–506.
- McCallum, A. M., Andersen, M. S., Rau, G. C., & Acworth, R. I. (2012). A 1-D analytical method for estimating surface water–groundwater interactions and effective thermal diffusivity using temperature time series. *Water Resources Research*, 48(11).

---

*Documento generado automáticamente a partir del análisis en `notebooks/05_datos_terreno.ipynb`.*
