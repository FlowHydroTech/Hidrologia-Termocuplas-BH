# Hidrología – Proyecto Termocuplas (VFLUX2 → Python)

Este repositorio contiene el desarrollo metodológico y computacional para estimar **flujos verticales río–acuífero** mediante análisis térmico usando datos de **termocuplas**.

El objetivo central es **replicar en Python** el comportamiento del toolbox **VFLUX2 (MATLAB)** utilizando una arquitectura abierta, reproducible y escalable.

---

# ✅ 1. ¿Qué es VFLUX2?

**VFLUX2** es un toolbox desarrollado en MATLAB que estima el **flujo vertical de agua** en el lecho de un río (infiltración o exfiltración) a partir de:

- Temperatura medida en diferentes profundidades del sedimento  
- Análisis armónico (amplitud + fase)  
- Propagación del calor (conducción–advección)  
- Propiedades térmicas del sedimento y del agua  

Según el manual oficial, VFLUX2:

✅ Lee un archivo Excel con **fecha y temperatura por cada sensor**  
✅ Alinea automáticamente las series aun si tienen **desfase temporal de minutos**  
✅ Realiza análisis espectral y armónico apoyado en Captain Toolbox (`arspec`)  
✅ Calcula **amplitud (A)** y **fase (φ)** de la señal diaria  
✅ Obtiene **ΔA** (atenuación) y **Δφ** (desfase) entre sensores  
✅ Usa modelos físicos para estimar flujo vertical (`q`) mediante 5 métodos:

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

## ✅ 2. Flujo de trabajo de VFLUX2 (según el manual)

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

# ✅ 3. ¿Cómo replicaremos VFLUX2 exactamente en Python?

Para que Python produzca **los mismos resultados que MATLAB**, debemos replicar **cada módulo interno** del toolbox:

---

## ✅ 3.1. Etapa 1 — Lectura de datos (equivalente a vfluxformat)

En Python:

- usar `pandas.read_excel`
- convertir fechas a `datetime`
- alinear sensores mediante `resample` + `interpolate`
- ordenar sensores según profundidad

Esto replica la preparación que hace:

vdata = vfluxformat(...)


---

## ✅ 3.2. Etapa 2 — Análisis armónico (FFT o curve_fit)

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

## ✅ 3.3. Etapa 3 — Implementación de métodos de flujo térmico

Se replicarán los **cinco métodos originales**:

### ✅ Método Hatch – Amplitud
Basado en atenuación de amplitud y propiedades térmicas.

### ✅ Método Hatch – Fase
Basado en retraso de fase entre sensores.

### ✅ Método McCallum
Combina ΔA + Δφ → método más estable.

### ✅ Método Keery
Incluye difusividad térmica corregida.

### ✅ Método Luce
Método empírico útil para diagnóstico.

Cada método se implementará con las ecuaciones originales publicadas en la literatura científica e interpretadas tal como VFLUX2 las aplica.

---

## ✅ 3.4. Etapa 4 — Parámetros térmicos

Definiremos una estructura estándar para:

## ✅ 3.4. Etapa 4 — Parámetros térmicos

- conductividad térmica: $\lambda$
- calor específico del sedimento: $C_s$
- calor específico del agua: $C_w$
- difusividad térmica: $\alpha$
- dispersividad: $\beta$



Estos valores deben ser configurables para cada campaña.

---

## ✅ 3.5. Etapa 5 — Comparación MATLAB vs Python

Implementaremos:

- gráfico comparativo de flujos  
- RMSE por método  
- validación temporal  
- reporte de equivalencia entre ambos modelos  

Esto permitirá certificar que el solver Python reproduce exactamente lo que MATLAB entrega.

---

# ✅ 4. Arquitectura del repositorio en Python

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

# ✅ 5. Estado actual del proyecto

✅ Manual de VFLUX2 analizado  
✅ Definida la arquitectura Python  
✅ Modelo conceptual completo  
✅ Se generará dataset sintético compatible con MATLAB  
✅ Próximo paso → implementar los módulos:

- `harmonic_analysis.py`
- `vflux_methods.py`
- `01_exploracion.ipynb`

---

# ✅ 6. Objetivo final

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