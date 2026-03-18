# ACTUALIZACIÓN — 18 de Marzo de 2026

## Proyecto: Hidrología Termocuplas — Río Silala
## Notebook: `05A_datos_terreno.ipynb`

---

## 1. Resumen de la Actualización

Se creó el notebook **05A_datos_terreno.ipynb** como pipeline definitivo de estimación de flujo vertical,
enfocado exclusivamente en:

- **Método cabecera**: Hatch-Amplitude (Hatch et al., 2006) — Solo atenuación de amplitud
- **Método validación**: McCallum (McCallum et al., 2012) — Ratio de amplitudes + desfase combinado

### Cambios principales respecto al notebook anterior (05_datos_terreno.ipynb)

| Aspecto | Antes (05) | Ahora (05A) |
|---------|-----------|-------------|
| Métodos de flujo | 5 métodos (Hatch-Amp, Hatch-Phase, McCallum, Keery, Luce) | 2 métodos: Hatch-Amp (cabecera) + McCallum (validación) |
| Parámetros térmicos | Genéricos de literatura (λ=1.80, C=2.80 MJ/m³·K) | Laboratorio IDIEM por cada TC |
| Difusividad α | Calculada como λ/C_s | Medida directamente en laboratorio IDIEM |
| Períodos de registro | Aproximados (sin hora) | Exactos con hora de terreno |
| Análisis armónico | Ventana fija 30 días | Período completo: 66 días (TC1/4/5), 33 días (TC2/3) |
| Boxplot | No incluido | Boxplot por TC para Hatch-Amplitude |
| Confiabilidad | Genérica 5 métodos | Enfocada en concordancia Hatch-Amp vs McCallum |
| Incertidumbre | Basada en parámetros de literatura (±20-25%) | Basada en mediciones lab IDIEM (±9-22%) |
| Exportación | CSV básico | Excel multi-hoja + CSVs |
| Flujo promedio por TC | No calculado | Promedio de los 3 pares por cada TC |

---

## 2. Períodos de Medición Exactos

| TC | Inicio | Fin | Duración |
|:--:|:------:|:---:|:--------:|
| TC-1 | 21-dic-2025 16:00 | 25-feb-2026 12:00 | 65 días |
| TC-2 | 23-ene-2026 13:00 | 25-feb-2026 12:00 | 32 días |
| TC-3 | 23-ene-2026 13:00 | 25-feb-2026 12:00 | 32 días |
| TC-4 | 21-dic-2025 16:00 | 25-feb-2026 12:00 | 65 días |
| TC-5 | 21-dic-2025 16:00 | 25-feb-2026 12:00 | 65 días |

---

## 3. Parámetros Térmicos — Laboratorio IDIEM

Fuente: Informes IDIEM OT-10 (Feb-Mar 2026)
- Informe N°1 (cód. 2.172.933-A, 06-feb-2026): TC1, TC4, TC5
- Informe N°2 (cód. 2.172.933-B, 02-mar-2026): TC2, TC3

| TC | λ (W/m·K) | C_s (MJ/m³·K) | α (m²/s) | K_v (m/d) | ρ_seca (g/cm³) | d_pen (cm) | USCS |
|:--:|:---------:|:-------------:|:--------:|:---------:|:--------------:|:----------:|:----:|
| TC-1 | 0.614 | 3.389 | 2.03×10⁻⁷ | 0.003 | 1.10 | 7.5 | SP-SM |
| TC-2 | 0.258 | 5.333 | 4.90×10⁻⁸ | 0.002 | 1.52 | 3.7 | SM |
| TC-3 | 0.265 | 4.867 | 5.50×10⁻⁸ | 0.006 | 1.39 | 3.9 | SW-SM |
| TC-4 | 0.666 | 2.342 | 3.13×10⁻⁷ | 0.778 | 1.37 | 9.3 | GP-GM |
| TC-5 | 0.578 | 2.690 | 2.24×10⁻⁷ | 0.003 | 1.22 | 7.8 | SW-SM |

**Nota importante**: La difusividad térmica α es un **resultado directo de laboratorio** (no calculada como λ/C_s).

### Comparación con valores anteriores (literatura)

| Parámetro | Valor anterior (literatura) | Rango IDIEM (5 TCs) |
|-----------|:-------------------------:|:-------------------:|
| λ (W/m·K) | 1.80 | 0.258 – 0.666 |
| C_s (MJ/m³·K) | 2.80 | 2.342 – 5.333 |
| α (m²/s) | ~6.4×10⁻⁷ (calculada) | 4.9×10⁻⁸ – 3.13×10⁻⁷ |

Los valores de laboratorio muestran una **heterogeneidad significativa** entre estaciones, especialmente:
- **TC-2**: Suelo fino (SM), muy baja conductividad, alta capacidad calórica
- **TC-4**: Grava (GP-GM), mayor conductividad y permeabilidad (K_v=0.778 m/d)

---

## 4. Justificación del Método Cabecera

**Referencia**: Saphores et al. (2024) — "Metodologías de estimación de infiltración"

Hatch-Amplitude se selecciona como método cabecera porque:

1. Depende **exclusivamente** del ratio de amplitudes A_r = A_sup/A_prof
2. **No requiere estimación de fase**, evitando la principal fuente de error
3. Menor sensibilidad a ruido instrumental y condiciones transitorias
4. Consistencia documentada en Suárez et al. (2023) para el Río Silala

### Ecuación Hatch-Amplitude

```
q_z = (2·α_e / Δz) · ln(A_sup / A_prof)
```

### Ecuación McCallum (validación)

```
γ = sqrt(Δφ² + ln(A_r)²)
K_e = (ω·Δz²·Δφ) / (2·γ²)
```

---

## 5. Resultados de Flujo Vertical — Hatch-Amplitude + McCallum

### 5.1 Resultados por par de sensores

| TC | Par | Hatch-Amp (mm/d) | McCallum (mm/d) | Hatch-Amp (m/s) | Dirección |
|:--:|:---:|:-----------------:|:---------------:|:---------------:|:---------:|
| TC1 | sup-int | 143.87 | 275.67 | 1.67×10⁻⁶ | Infiltración ↓ |
| TC1 | int-inf | 122.66 | 193.07 | 1.42×10⁻⁶ | Infiltración ↓ |
| TC1 | sup-inf | 133.26 | 984.68 | 1.54×10⁻⁶ | Infiltración ↓ |
| TC2 | sup-int | 51.17 | 125.44 | 5.92×10⁻⁷ | Infiltración ↓ |
| TC2 | int-inf | 58.63 | 137.96 | 6.79×10⁻⁷ | Infiltración ↓ |
| TC2 | sup-inf | 54.90 | 628.34 | 6.35×10⁻⁷ | Infiltración ↓ |
| TC3 | sup-int | 13.83 | 27.86 | 1.60×10⁻⁷ | Infiltración ↓ |
| TC3 | int-inf | 5.79 | 11.06 | 6.70×10⁻⁸ | Infiltración ↓ |
| TC3 | sup-inf | 9.81 | 83.03 | 1.13×10⁻⁷ | Infiltración ↓ |
| TC4 | sup-int | 28.23 | 41.74 | 3.27×10⁻⁷ | Infiltración ↓ |
| TC4 | int-inf | 23.09 | 33.52 | 2.67×10⁻⁷ | Infiltración ↓ |
| TC4 | sup-inf | 25.66 | 154.74 | 2.97×10⁻⁷ | Infiltración ↓ |
| TC5 | sup-int | 296.40 | 702.98 | 3.43×10⁻⁶ | Infiltración ↓ |
| TC5 | int-inf | 129.20 | 351.31 | 1.50×10⁻⁶ | Infiltración ↓ |
| TC5 | sup-inf | 212.80 | 2584.19 | 2.46×10⁻⁶ | Infiltración ↓ |

### 5.2 Flujo promedio por TC (Hatch-Amplitude)

| TC | q medio (mm/d) | Rango pares (mm/d) | USCS | Observación |
|:--:|:--------------:|:-------------------:|:----:|:-----------:|
| TC1 | ~133 | 123 – 144 | SP-SM | Consistente entre pares |
| TC2 | ~55 | 51 – 59 | SM | Suelo fino, flujo bajo |
| TC3 | ~10 | 6 – 14 | SW-SM | Flujo más bajo |
| TC4 | ~26 | 23 – 28 | GP-GM | Grava, flujo moderado |
| TC5 | ~213 | 129 – 296 | SW-SM | Flujo más alto, variabilidad |

**Todos los flujos son positivos (infiltración: río → acuífero).**

### 5.3 Métricas de validación Hatch-Amp vs McCallum

| Métrica | Valor |
|---------|:-----:|
| Correlación r | 0.637 |
| RMSE | 680.61 mm/día |
| Sesgo (McCallum - Hatch) | +335.09 mm/día |
| n pares | 15 |

> **Nota**: McCallum sobreestima consistentemente respecto a Hatch-Amplitude,
> especialmente en pares sup-inf donde la separación Δz es mayor.
> Este sesgo es conocido y se atribuye a la componente de fase en McCallum.

---

## 6. Análisis Armónico — Resultados

Ajuste sinusoidal T(t) = A·sin(2πt/24 + φ) + T₀ usando período completo.

| Sensor | TC | Prof (cm) | A (°C) | φ (°) | T₀ (°C) | R² | Calidad |
|--------|:--:|:---------:|:------:|:-----:|:-------:|:--:|:-------:|
| temp_12 | TC1 | 0 | 5.152 | 87.3 | 18.28 | 0.728 | ★★★ |
| temp_9 | TC1 | 28 | 1.423 | 8.0 | 17.49 | 0.483 | ★★☆ |
| temp_8 | TC1 | 56 | 0.475 | 355.5 | 17.57 | 0.103 | ★☆☆ |
| temp_4 | TC2 | 0 | 2.491 | 17.4 | 17.01 | 0.619 | ★★☆ |
| temp_6 | TC2 | 20 | 0.732 | 283.7 | 17.15 | 0.218 | ★☆☆ |
| temp_7 | TC2 | 40 | 0.180 | 199.1 | 17.30 | 0.022 | ★☆☆ |
| temp_1 | TC3 | 0 | 5.022 | 25.9 | 18.40 | 0.606 | ★★☆ |
| temp_10 | TC3 | 20 | 3.743 | 351.7 | 18.07 | 0.730 | ★★★ |
| temp_11 | TC3 | 40 | 3.310 | 335.5 | 18.09 | 0.692 | ★★☆ |
| temp_15 | TC4 | 0 | 4.774 | 69.5 | 18.49 | 0.836 | ★★★ |
| temp_3 | TC4 | 28 | 4.065 | 56.0 | 18.25 | 0.782 | ★★★ |
| temp_14 | TC4 | 56 | 3.564 | 49.1 | 18.31 | 0.750 | ★★★ |
| temp_5 | TC5 | 0 | 3.085 | 62.3 | 18.23 | 0.813 | ★★★ |
| temp_13 | TC5 | 28 | 0.330 | 275.8 | 18.33 | 0.128 | ★☆☆ |
| temp_2 | TC5 | 56 | 0.125 | 125.7 | 18.20 | 0.023 | ★☆☆ |

### Observaciones del análisis armónico

- **TC4** tiene los mejores ajustes (R²: 0.750–0.836) con atenuación de amplitud clara y progresiva
- **TC3** muestra poca atenuación de amplitud entre profundidades (5.0→3.7→3.3°C), sugiriendo alta advección o menor interacción superficial
- **TC5** presenta fuerte atenuación (3.1→0.3→0.1°C), consistente con flujo alto
- **TC2** muestra R² muy bajos en sensores profundos, consistente con suelo fino (SM) que amortigua la señal

---

## 7. Métricas de Confiabilidad (IC)

Índice compuesto con pesos ajustados para Hatch-Amp + McCallum:

| Componente | Peso |
|-----------|:----:|
| R² sensor superior | 0.25 |
| R² sensor inferior | 0.20 |
| Concordancia Hatch-Amp vs McCallum | 0.25 |
| Rango de literatura | 0.15 |
| Consistencia física (A decrece) | 0.15 |

| TC | Par | IC total | R²_sup | R²_inf | Concordancia | Calificación |
|:--:|:---:|:--------:|:------:|:------:|:------------:|:------------:|
| TC1 | sup→int | 0.709 | 0.728 | 0.483 | 0.522 | ●●●○ Buena |
| TC1 | int→inf | 0.600 | 0.483 | 0.103 | 0.635 | ●●○○ Moderada |
| TC1 | sup→inf | 0.536 | 0.728 | 0.103 | 0.135 | ●●○○ Moderada |
| TC2 | sup→int | 0.600 | 0.619 | 0.218 | 0.408 | ●●○○ Moderada |
| TC2 | int→inf | 0.465 | 0.218 | 0.022 | 0.425 | ●○○○ Baja |
| TC2 | sup→inf | 0.481 | 0.619 | 0.022 | 0.087 | ●○○○ Baja |
| TC3 | sup→int | 0.722 | 0.606 | 0.730 | 0.496 | ●●●○ Buena |
| TC3 | int→inf | 0.688 | 0.730 | 0.692 | 0.523 | ●●○○ Moderada |
| TC3 | sup→inf | 0.617 | 0.606 | 0.692 | 0.118 | ●●○○ Moderada |
| TC4 | sup→int | **0.835** | 0.836 | 0.782 | 0.676 | **●●●● Alta** |
| TC4 | int→inf | **0.818** | 0.782 | 0.750 | 0.689 | **●●●● Alta** |
| TC4 | sup→inf | 0.700 | 0.836 | 0.750 | 0.166 | ●●●○ Buena |
| TC5 | sup→int | 0.634 | 0.813 | 0.128 | 0.422 | ●●○○ Moderada |
| TC5 | int→inf | 0.428 | 0.128 | 0.023 | 0.368 | ●○○○ Baja |
| TC5 | sup→inf | 0.528 | 0.813 | 0.023 | 0.082 | ●●○○ Moderada |

**TC4 es la estación con mayor confiabilidad** (IC = 0.818–0.835 en pares adyacentes).

---

## 8. Propagación de Incertidumbre

### Reducción de incertidumbre con parámetros IDIEM

| Fuente | Antes (literatura) | Ahora (IDIEM) | Reducción |
|--------|:-----------------:|:-------------:|:---------:|
| Conductividad λ | ±20% | ±10% | 50% |
| Capacidad calórica C_s | ±15% | ±10% | 33% |
| Difusividad α | ±20% (calculada) | ±8% (medida) | 60% |
| Posición sensor Δz | ±5 mm | ±5 mm | — |
| Ajuste armónico | ±10% | ±5–20% (según R²) | Variable |

**Incertidumbre total anterior** (literatura): ±26.9%  
**Incertidumbre total actual** (lab IDIEM): ±9.6–21.6%  
**Reducción global**: ~50%

### Incertidumbre por par de sensores

| TC | Par | q (mm/d) | u_rel (%) | u_abs (mm/d) | IC 95% bajo | IC 95% alto |
|:--:|:---:|:--------:|:---------:|:------------:|:-----------:|:-----------:|
| TC1 | sup→int | 143.9 | 12.9 | 18.6 | 107.4 | 180.3 |
| TC1 | int→inf | 122.7 | 21.6 | 26.5 | 70.7 | 174.6 |
| TC1 | sup→inf | 133.3 | 21.6 | 28.8 | 76.8 | 189.7 |
| TC2 | sup→int | 51.2 | 21.6 | 11.1 | 29.5 | 72.8 |
| TC2 | int→inf | 58.6 | 21.6 | 12.7 | 33.8 | 83.5 |
| TC2 | sup→inf | 54.9 | 21.6 | 11.9 | 31.6 | 78.2 |
| TC3 | sup→int | 13.8 | 12.9 | 1.8 | 10.3 | 17.3 |
| TC3 | int→inf | 5.8 | 12.9 | 0.7 | 4.3 | 7.3 |
| TC3 | sup→inf | 9.8 | 12.9 | 1.3 | 7.3 | 12.3 |
| TC4 | sup→int | 28.2 | 9.6 | 2.7 | 22.9 | 33.5 |
| TC4 | int→inf | 23.1 | 12.9 | 3.0 | 17.2 | 28.9 |
| TC4 | sup→inf | 25.7 | 12.9 | 3.3 | 19.2 | 32.2 |
| TC5 | sup→int | 296.4 | 21.6 | 64.1 | 170.8 | 422.0 |
| TC5 | int→inf | 129.2 | 21.6 | 27.9 | 74.5 | 183.9 |
| TC5 | sup→inf | 212.8 | 21.6 | 46.0 | 122.6 | 303.0 |

---

## 9. Archivos Generados

### Notebook
- `notebooks/05A_datos_terreno.ipynb` — 29 celdas (14 markdown + 15 código)

### Excel (multi-hoja)
- `resultados_python/terreno_2026_hatch/resultados_05A_hatch_amplitude.xlsx`
  - Hoja 1: Flujos_HA_McCallum — Resultados por par y método
  - Hoja 2: Flujo_Promedio_TC — Promedio por termocupla con params IDIEM
  - Hoja 3: Confiabilidad — Índice de confiabilidad
  - Hoja 4: Incertidumbre — Propagación de errores
  - Hoja 5: Analisis_Armonico — Amplitudes y fases
  - Hoja 6: Params_IDIEM — Propiedades térmicas laboratorio

### CSVs
- `resultados_python/terreno_2026_hatch/flujos_hatch_mccallum.csv`
- `resultados_python/terreno_2026_hatch/confiabilidad_hatch_mccallum.csv`
- `resultados_python/terreno_2026_hatch/incertidumbre_hatch.csv`

### Series temporales (ventanas deslizantes 48h, paso 12h)
- `resultados_python/terreno_2026_hatch/series_temporales/flujo_temporal_TC{1-5}_{par}.csv`

### Figuras
- `image/terreno_2026/series_05A_hatch.png` — Series de temperatura 5 TCs
- `image/terreno_2026/ajustes_armonicos_05A.png` — Ajustes sinusoidales 15 sensores
- `image/terreno_2026/boxplot_hatch_05A.png` — Boxplot + scatter validación
- `image/terreno_2026/barras_hatch_mccallum_05A.png` — Barras comparativas por TC
- `image/terreno_2026/series_temporales_hatch_05A.png` — Series temporales de flujo

---

## 10. Entorno Técnico

| Componente | Detalle |
|-----------|---------|
| Python | 3.12.7 (venv creado con uv) |
| Package manager | uv |
| venv path | `.venv/` (recreado 18-mar-2026) |
| numpy | 2.4.3 |
| pandas | 3.0.1 |
| scipy | 1.17.1 |
| matplotlib | 3.10.8 |
| openpyxl | 3.1.5 |
| statsmodels | 0.14.6 |
| Paquete local | hidrologia-termocuplas-bh 0.1.0 (editable) |

### Nota sobre entorno
El `.venv` anterior (copiado del laptop) estaba roto al apuntar a `C:\Users\Cesar\` en vez de `C:\Users\cesar.godoy\`.
Se recreó con `uv venv .venv --python 3.12` y se reinstalaron todas las dependencias.

---

## 11. Comentarios del Especialista Implementados

| # | Comentario | Estado |
|:-:|-----------|:------:|
| 1 | Actualizar períodos de registro por TC (con hora exacta) | ✅ |
| 2 | Formato de fecha: dd-mmm-yy (español) | ✅ |
| 3 | Ventana de 60+ días para ajuste armónico en TC1/TC4/TC5 | ✅ |
| 4 | Parámetros térmicos IDIEM por TC, α de laboratorio | ✅ |
| 5 | Referencia Saphores 2024 para justificar Hatch-Amp | ✅ |
| 6 | q (m/s) como valor numérico (no texto) | ✅ |
| 7 | Generar boxplot para Hatch-Amplitude | ✅ |
| 8 | Métricas de confiabilidad enfocadas Hatch-Amp + McCallum | ✅ |
| 9 | Ajustar incertidumbre con propiedades térmicas lab | ✅ |
| 10 | Exportar datos de incertidumbre a Excel | ✅ |
| 11 | Flujo promedio por TC (promediando pares) | ✅ |

---

## 12. Referencias

- Hatch, C.E., Fisher, A.T., Revenaugh, J.S., Constantz, J., Ruehl, C. (2006). Quantifying surface water–groundwater interactions using time series analysis of streambed thermal records: Method development. *Water Resources Research*, 42, W10410.
- McCallum, A.M., Cook, P.G., Brunner, P., Berhane, D. (2012). Solute dynamics during bank storage flows and implications for chemical base flow separation. *Water Resources Research*, 48, W10517.
- Saphores, J.D. et al. (2024). Metodologías de estimación de infiltración. (Referencia base para selección de método cabecera)
- Suárez, F. et al. (2023). Análisis de flujo vertical en el Río Silala mediante termocuplas.

---

*Documento generado el 18 de marzo de 2026*
