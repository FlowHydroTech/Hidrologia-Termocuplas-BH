# Hidrología – Proyecto Termocuplas (VFLUX2 → Python)

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-En%20Desarrollo-yellow.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

Este repositorio contiene el desarrollo metodológico y computacional para estimar **flujos verticales río–acuífero** mediante análisis térmico usando datos de **termocuplas**.

El objetivo central es **replicar en Python** el comportamiento del toolbox **VFLUX2 (MATLAB)** utilizando una arquitectura abierta, reproducible y escalable.

---

## ACTUALIZACIONES IMPORTANTES

### Corrección Crítica Identificada (Nov 2025)

Durante la validación de la implementación se identificó un **error de magnitud** en varios métodos VFLUX2:

-  **Hatch-Fase**: Error corregido (de 36,710,885% a 0.6%)
-  **Hatch-Amplitud**: Validado como correcto
-  **Keery, McCallum, Luce**: Correcciones pendientes

**Causa raíz:** Las ecuaciones no separaban correctamente el desfase conductivo (98.7%) del advectivo (1.3%). Ver [`SOLUCION_ERROR_MAGNITUD.md`](SOLUCION_ERROR_MAGNITUD.md) para detalles técnicos.

---

## Inicio Rápido

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/FlowHydroTech/Hidrologia-Termocuplas-BH.git
cd Hidrologia-Termocuplas-BH

# Crear ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

### Uso Básico

```python
# Ejecutar análisis completo
jupyter notebook notebooks/02_solver_vflux.ipynb
```

### Estructura del Proyecto

```
Hidrologia-Termocuplas-BH/
├── src/                          # Código fuente
│   ├── vflux_methods.py         # Métodos VFLUX2 (con correcciones)
│   ├── signal_processing.py    # Procesamiento de señales
│   └── data_loader.py           # Carga de datos
├── notebooks/                    # Notebooks interactivos
│   ├── 01_generate_synthetic_data.ipynb
│   ├── 02_solver_vflux.ipynb   # Análisis principal
│   └── 03_analisis_dimensional.ipynb  # Diagnóstico
├── tests/                       # Tests automatizados
├── data/                        # Datos de entrada
├── SOLUCION_ERROR_MAGNITUD.md   # Documentación técnica
├── AUDITORIA_VFLUX2.md          # Auditoría completa
└── README.md
```

---

## Estado Actual del Proyecto

### Métodos Implementados

| Método | Estado | Error | Comentarios |
|--------|--------|-------|-------------|
| **Hatch-Amplitud** | Validado | 0.0% | Funcionando correctamente |
| **Hatch-Fase** | Corregido | 0.6% | Corrección implementada Nov 2025 |
| **Keery (2007)** | En revisión | ~12,000% | Requiere corrección similar a Hatch-Fase |
| **McCallum (2012)** | En revisión | 0%* | *Usa fallback a Hatch-Amplitud |
| **Luce (2013)** | Pendiente | ~868,000% | Requiere revisión de ecuación empírica |

### Hallazgos Técnicos Clave

#### Problema de Separación de Componentes Térmicas

En medios porosos saturados, el desfase de fase tiene **dos componentes**:

```
Δφ_total = Δφ_conductivo + Δφ_advectivo
```

**Para flujos típicos (~5 mm/día):**
- Δφ_conductivo: **98.7%** (difusión térmica pura)
- Δφ_advectivo: **1.3%** (transporte con flujo de agua)

**Error identificado:** Los métodos asumían que TODO el desfase era advectivo.

**Solución implementada:**

```python
# 1. Calcular desfase conductivo (sin flujo)
delta_phi_cond = √((ω × Δz²) / (4 × α))

# 2. Extraer componente advectiva
delta_phi_adv = delta_phi_total - delta_phi_cond

# 3. Calcular flujo solo con componente advectiva
v = (delta_phi_adv / Δz) × (2λ) / Cw
```

### Validación con Datos Sintéticos

Se generaron series temporales con **flujo conocido de 5.0 mm/día**:

- Hatch-Fase recupera: **5.03 mm/día** (error 0.6%)
- Hatch-Amplitud recupera: **5.00 mm/día** (error 0.0%)
- Otros métodos: Errores significativos pendientes de corrección

Ver [`generate_synthetic_data.py`](generate_synthetic_data.py) para detalles.

---

## Documentación Adicional

- [`SOLUCION_ERROR_MAGNITUD.md`](SOLUCION_ERROR_MAGNITUD.md) - Análisis detallado de la corrección
- [`AUDITORIA_VFLUX2.md`](AUDITORIA_VFLUX2.md) - Auditoría completa de métodos
- [`doc/Manual_Completo_VFLUX2_v1.pdf`](doc/Manual_Completo_VFLUX2_v1.pdf) - Manual VFLUX2 MATLAB original

---

# 1. ¿Qué es VFLUX2?

**VFLUX2** es un toolbox desarrollado en MATLAB que estima el **flujo vertical de agua** en el lecho de un río (infiltración o exfiltración) a partir de:

- Temperatura medida en diferentes profundidades del sedimento  
- Análisis armónico (amplitud + fase)  
- Propagación del calor (conducción–advección)  
- Propiedades térmicas del sedimento y del agua  

Según el manual oficial, VFLUX2:

* Lee un archivo Excel con **fecha y temperatura por cada sensor**  
* Alinea automáticamente las series aun si tienen **desfase temporal de minutos**  
* Realiza análisis espectral y armónico apoyado en Captain Toolbox (`arspec`)  
* Calcula **amplitud (A)** y **fase (φ)** de la señal diaria  
* Obtiene **ΔA** (atenuación) y **Δφ** (desfase) entre sensores  
* Usa modelos físicos para estimar flujo vertical (`q`) mediante 5 métodos:

- **McCallum** (principal)
- **Hatch – Amplitud**
- **Hatch – Fase**
- **Keery**
- **Luce**

VFLUX2 permite ajustar varios parámetros claves del análisis:

- `rfactor`: reducción de muestreo  
- `windows`: pares de sensores a comparar  
- `Pf`: filtro espectral  
- `n`: número de armónicos  
- `beta`: dispersividad térmica  
- `Kcal`: conductividad térmica del sedimento  
- `Cscal`: calor específico del sedimento  
- `Cwcal`: calor específico del agua  

---

## 2. Flujo de trabajo de VFLUX2 (según el manual)

### **1. Preparación del archivo Excel**
El archivo debe incluir columnas:

fecha1 | temp1 | fecha2 | temp2 | fecha3 | temp3


Ordenados desde el **sensor más superficial** al más profundo.  
Si los sensores tienen desfase de 1–3 minutos, VFLUX2 lo corrige automáticamente.

---

### **2. Lectura y alineación temporal**

VFLUX2:
- convierte las fechas a formato MATLAB (`datenum`)
- interpola los tiempos
- alinea las series
- genera un objeto estructurado (`vdata`) que contiene:

  - temperatura por sensor  
  - profundidad  
  - tiempos alineados  
  - series corregidas  

---

### **3. Análisis armónico**

De cada sensor se obtiene amplitud \(A\) y fase \(\phi\).
Luego, entre sensores:

$$
\Delta A \;=\; \ln\!\left(\frac{A_{1}}{A_{2}}\right)
$$

$$
\Delta \phi \;=\; \phi_{2}\;-\;\phi_{1}
$$


Estos dos parámetros son fundamentales para estimar flujo vertical.

---

### **4. Solver de flujo térmico**

VFLUX2 aplica las ecuaciones de conducción–advección de calor y calcula **q (m/s)** mediante cinco métodos:

- McCallum (más estable y recomendado)
- Hatch (amplitud y fase)
- Keery
- Luce

Finalmente entrega un vector de tiempo con:

- flujo por método  
- indicadores espectrales  
- periodo de análisis  

---

# 3. ¿Cómo replicaremos VFLUX2 exactamente en Python?

Para que Python produzca **los mismos resultados que MATLAB**, debemos replicar **cada módulo interno** del toolbox:

---

## 3.1. Etapa 1 — Lectura de datos (equivalente a vfluxformat)

En Python:

- usar `pandas.read_excel`
- convertir fechas a `datetime`
- alinear sensores mediante `resample` + `interpolate`
- ordenar sensores según profundidad

Esto replica la preparación que hace:

vdata = vfluxformat(...)


---

## 3.2. Etapa 2 — Análisis armónico (FFT o curve_fit)

VFLUX2 usa `arspec` del Captain Toolbox.

En Python usaremos una combinación de:

- `scipy.signal.periodogram`
- `curve_fit` (ajuste sinusoidal)
- `numpy.fft` (si se requiere análisis espectral)

De cada sensor obtendremos:

- Amplitud A  
- Fase φ  
- Temperatura media  

Luego calculamos:

- **ΔA** (atenuación vertical de amplitud)  
- **Δφ** (desfase entre sensores)  

---

## 3.3. Etapa 3 — Implementación de métodos de flujo térmico

Se replicarán los **cinco métodos originales**:

### * Método Hatch – Amplitud
Basado en atenuación de amplitud y propiedades térmicas.

### * Método Hatch – Fase
Basado en retraso de fase entre sensores.

### * Método McCallum
Combina ΔA + Δφ → método más estable.

### * Método Keery
Incluye difusividad térmica corregida.

### * Método Luce
Método empírico útil para diagnóstico.

Cada método se implementará con las ecuaciones originales publicadas en la literatura científica e interpretadas tal como VFLUX2 las aplica.

---

## 3.4. Etapa 4 — Parámetros térmicos

Definiremos una estructura estándar para:

## 3.4. Etapa 4 — Parámetros térmicos

- conductividad térmica: $\lambda$
- calor específico del sedimento: $C_s$
- calor específico del agua: $C_w$
- difusividad térmica: $\alpha$
- dispersividad: $\beta$



Estos valores deben ser configurables para cada campaña.

---

## 3.5. Etapa 5 — Comparación MATLAB vs Python

Implementaremos:

- gráfico comparativo de flujos  
- RMSE por método  
- validación temporal  
- reporte de equivalencia entre ambos modelos  

Esto permitirá certificar que el solver Python reproduce exactamente lo que MATLAB entrega.

---

# 4. Arquitectura del repositorio en Python

```text
Hidrologia-Termocuplas-BH/
|
+-- data/
|   +-- raw/                     # Datos crudos (Excel original o sintético)
|   +-- processed/               # Datos alineados y limpios
|   \-- thermal_properties/      # Parámetros térmicos del sedimento/agua
|
+-- notebooks/
|   +-- 01_exploracion.ipynb     # Exploración de datos
|   +-- 02_armonicos.ipynb       # Cálculo amplitud/fase (ΔA, Δφ)
|   \-- 03_solver.ipynb          # Implementación de métodos VFLUX en Python
|
+-- src/
|   +-- io_utils.py              # Lectura y alineación de datos
|   +-- preprocess.py            # Resample, interpolación, normalización
|   +-- harmonic_analysis.py     # FFT, ajuste sinusoidal, cálculo ΔA y Δφ
|   +-- vflux_methods.py         # Métodos: McCallum, Hatch, Keery, Luce
|   \-- visualization.py         # Gráficas y validaciones
|
+-- tests/                       # Validaciones unitarias
|
+-- README.md
+-- requirements.txt
\-- .gitignore
```

# 5. Estado actual del proyecto

**Completado:**
- Manual de VFLUX2 analizado  
- Arquitectura Python definida  
- Módulos principales implementados (`vflux_methods.py`, `signal_processing.py`, `data_loader.py`)
- Generación de datos sintéticos validada
- **Corrección crítica en método Hatch-Fase** (Nov 2025)
- Auditoría completa de todos los métodos
- Suite de notebooks interactivos

**En Progreso:**
- Corrección de métodos Keery, McCallum y Luce
- Validación contra MATLAB VFLUX2 original
- Tests unitarios automatizados

**Pendiente:**
- Aplicación a datos reales del Campo de Bombeo Huachipa
- Análisis espacial y mapas de flujo
- Documentación de usuario final
- Paper técnico con hallazgos

---

## Próximos Pasos

### Prioridad Alta (2 semanas)

1. **Corregir métodos restantes**
   - Keery: Aplicar separación conductiva/advectiva
   - Luce: Revisar ecuación empírica
   - McCallum: Verificar comportamiento de fallback

2. **Validación completa**
   - Re-ejecutar con todas las correcciones
   - Comparar con MATLAB VFLUX2
   - Objetivo: CV < 20% entre métodos

### Prioridad Media (1-2 meses)

3. **Tests automatizados**
   - Suite completa de tests unitarios
   - Casos sintéticos para cada método
   - CI/CD para prevenir regresiones

4. **Datos reales**
   - Procesamiento de series 2023-2024 Huachipa
   - Análisis temporal y espacial
   - Generación de mapas de flujo

---

## Contribuciones

Este proyecto está abierto a colaboración. Puedes contribuir:

- Reportando issues o bugs
- Sugiriendo mejoras
- Mejorando documentación
- Validando contra papers originales
- Enviando pull requests

### Cómo Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

**Resumen: Generación de Datos Sintéticos***

**Objetivo**

Crear series temporales de temperatura sintéticas con flujo vertical conocido (5 mm/día) para validar los métodos VFLUX2.

**Parámetros:**

* TARGET_FLUX = 5.0 mm/día          # Flujo objetivo de infiltración
* Profundidades: 10, 20, 30 cm      # Tres sensores
* Frecuencia: 15 minutos            # 3 días de datos


**Física Implementada**
Desfase de fase calculado mediante ecuación de McCallum (aproximación lineal):

$$

Δφ = √((ω×Δz²)/(4α)) + (v×Cw×Δz)/(2λ)
     └──conductivo──┘   └──advectivo──┘

$$     

**Componentes:**

Δφ_conductivo: ~98.7% del desfase (difusión térmica pura)
Δφ_advectivo: ~1.3% del desfase (transporte con flujo)


**Series Generadas**

Tres señales sinusoidales con:

* Amplitud decreciente con profundidad (3.0 → 2.0 → 1.2 °C)
* Temperatura base decreciente (20 → 19 → 18 °C)
* Desfase temporal proporcional al flujo y profundidad

Desfases calculados:

* Sensor 1→2 (10 cm): ~9.3 min
* Sensor 2→3 (10 cm): ~9.3 min
* Sensor 1→3 (20 cm): ~18.6 min

**Resultado**
Archivo: termocuplas_sinteticas.xlsx

* 288 registros (3 días × 96 mediciones/día)
* Formato compatible con VFLUX2
* Flujo recuperable: 5.03 mm/día (0.6% error) OK

Uso: Datos de referencia para validar que cada método VFLUX2 recupere correctamente el flujo de 5 mm/día conocido.




## Referencias Científicas

- **Stallman, R.W. (1965)** - *Steady one-dimensional fluid flow in a semi-infinite porous medium with sinusoidal surface temperature*. Journal of Geophysical Research, 70(12), 2821-2827.

- **Hatch, C.E., et al. (2006)** - *Quantifying surface water–groundwater interactions using time series analysis of streambed thermal records*. Water Resources Research, 42(10).

- **Keery, J., et al. (2007)** - *Temporal and spatial variability of groundwater–surface water fluxes: Development and application of an analytical method using temperature time series*. Journal of Hydrology, 336(1-2), 1-16.

- **McCallum, A.M., et al. (2012)** - *Limitations of the use of environmental tracers to infer groundwater age*. Groundwater, 50(6), 949-951.

- **Luce, C.H., et al. (2013)** - *Solutions for the diurnally forced advection-diffusion equation to estimate bulk fluid velocity and diffusivity in streambeds from temperature time series*. Water Resources Research, 49(1), 488-506.

---

## Contacto

**FlowHydroTech**  
GitHub: [@FlowHydroTech](https://github.com/FlowHydroTech)

Para consultas sobre el proyecto o colaboraciones, por favor abre un issue en el repositorio.

---

## 📄 Licencia

Este proyecto es de código privado y está disponible bajo la licencia MIT.

---

# 6. Objetivo final

Construir un **solver térmico completo en Python**, totalmente reproducible, capaz de:

- Leer datos crudos  
- Procesarlos como VFLUX2  
- Calcular ΔA, Δφ  
- Aplicar los métodos de flujo con la misma lógica que MATLAB  
- Validar equivalencia Python/MATLAB  
- Integrarse a reportabilidad profesional (Power BI, gráficos, dashboards)

---

## © FlowHydroTech – Proyecto Termocuplas  
Repositorio oficial de investigación y desarrollo para el análisis térmico río–acuífero.