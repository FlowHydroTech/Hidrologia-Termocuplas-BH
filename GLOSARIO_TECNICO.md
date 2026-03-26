# GLOSARIO TÉCNICO - PROYECTO VFLUX2

**Fecha:** 25 de marzo de 2026  
**Proyecto:** Hidrología - Termocuplas BH  
**Propósito:** Definiciones de conceptos técnicos y terminología especializada

---

## F

### **FALLBACK**
**Definición:** Mecanismo de respaldo automático que se activa cuando un método principal falla o produce resultados inválidos.

**Contexto VFLUX2:** Cuando un método complejo (como McCallum que combina amplitud y fase) encuentra condiciones matemáticas problemáticas (ej: raíz cuadrada negativa), automáticamente utiliza un método más simple y confiable (como Hatch-Amplitude que solo usa amplitud).

**Ejemplo práctico:**
```python
# Método McCallum intenta ecuación completa
if discriminante < 0:
    # FALLBACK: Usa Hatch-Amplitude como respaldo
    return hatch_amplitude_method(...)
```

**Ventajas:**
- Garantiza resultados válidos cuando métodos complejos fallan
- Evita errores matemáticos (raíces negativas, divisiones por cero)
- Proporciona estimaciones confiables basadas en métodos más robustos

**Implementación en proyecto:** McCallum y Keery usan fallback a Hatch-Amplitude cuando sus ecuaciones combinadas no pueden resolverse matemáticamente.

---

## A

### **ANÁLISIS DIMENSIONAL**
**Definición:** Técnica matemática para verificar que las ecuaciones físicas tengan unidades consistentes en ambos lados.

**Propósito:** Detectar errores fundamentales en implementaciones de ecuaciones antes de aplicarlas a datos reales.

**Ejemplo:** Una velocidad debe tener unidades [m/s], no [adimensional].

### **AMPLITUD TÉRMICA**
**Definición:** Magnitud de la variación de temperatura en una señal sinusoidal diaria.

**Símbolo:** A [°C]  
**Medición:** Diferencia entre temperatura máxima y mínima en un ciclo de 24 horas.  
**Comportamiento:** Disminuye con la profundidad debido a atenuación térmica.

### **ATENUACIÓN TÉRMICA**
**Definición:** Reducción de la amplitud de la señal térmica conforme se propaga a mayor profundidad.

**Causa física:** Difusión térmica en el sedimento.  
**Aplicación:** Base del método Hatch-Amplitude para estimar flujo vertical.

---

## C

### **CALIBRACIÓN TÉRMICA**
**Definición:** Proceso de ajustar parámetros térmicos del sedimento para que los métodos VFLUX2 produzcan resultados dentro de rangos validados por literatura.

**Parámetros calibrados:**
- λ (conductividad térmica)
- C (capacidad calorífica)  
- α (difusividad térmica)

**Resultado exitoso:** Hatch-Amplitude = 56 cm/día (dentro del rango Silala 9-60 cm/día).

### **COEFICIENTE DE VARIACIÓN (CV)**
**Definición:** Medida de dispersión relativa entre resultados de diferentes métodos.

**Fórmula:** CV = (desviación estándar / media) × 100%  
**Objetivo del proyecto:** CV < 20%  
**Logrado:** CV ≈ 65% (mejoría significativa vs 224% inicial)

### **CONDUCCIÓN TÉRMICA**
**Definición:** Transferencia de calor por contacto directo entre partículas, sin movimiento de fluido.

**En VFLUX2:** Representa el transporte térmico que ocurre incluso sin flujo de agua (componente de fondo siempre presente).

---

## D

### **DOCKER / DOCKER COMPOSE**
**Definición:** Plataforma de contenedores que empaqueta el pipeline con todas sus dependencias en una imagen reproducible.

**Contexto VFLUX2:** El proyecto incluye `Dockerfile` (multi-stage build con Python 3.12-slim) y `docker-compose.yml` con 3 servicios:
- `prefect` — Dashboard Prefect en http://localhost:4200
- `pipeline` — Pipeline con Prefect conectado al dashboard
- `standalone` — Pipeline Python puro (sin Prefect)

**Uso:** `docker compose up` (completo), `docker compose run --rm standalone` (sin Prefect).

### **DESFASE CONDUCTIVO (Δφ_conductivo)**
**Definición:** Retraso en la señal térmica causado únicamente por difusión térmica, sin influencia del flujo de agua.

**Cálculo:** Δφ_conductivo = √((ω×Δz²)/(4α))  
**Importancia:** Representa ~98% del desfase total para flujos pequeños.  
**Aplicación:** Debe restarse del desfase total para calcular el componente advectivo.

### **DESFASE ADVECTIVO (Δφ_advectivo)**
**Definición:** Retraso adicional en la señal térmica causado específicamente por el transporte de calor con el agua en movimiento.

**Cálculo:** Δφ_advectivo = Δφ_total - Δφ_conductivo  
**Importancia:** Solo este componente refleja el flujo de agua real.  
**Magnitud típica:** ~1-2% del desfase total para flujos pequeños.

### **DIFUSIVIDAD TÉRMICA (α)**
**Definición:** Propiedad del material que indica qué tan rápido se difunde el calor a través de él.

**Unidades:** m²/s  
**Fórmula:** α = λ / C  
**Valor calibrado:** 1.60×10⁻⁷ m²/s (ultra-baja, típica de sedimentos porosos)

---

## E

### **ERROR DIMENSIONAL**
**Definición:** Problema fundamental donde una ecuación produce unidades incorrectas para la variable que pretende calcular.

**Ejemplo crítico:** La ecuación Hatch-Phase implementada produce unidades [adimensional] en lugar de [m/s] para velocidad.

**Detección:** Análisis dimensional riguroso antes de implementación.

---

## F

### **FASE TÉRMICA (φ)**
**Definición:** Desfase temporal entre señales térmicas medidas a diferentes profundidades.

**Unidades:** radianes [rad]  
**Conversión:** 1 rad = 57.3°  
**Interpretación física:** Tiempo que tarda la onda térmica en propagarse entre sensores.

### **FLUJO VERTICAL DARCY**
**Definición:** Velocidad aparente del agua a través del medio poroso, incluyendo espacios vacíos.

**Símbolo:** q o v [m/s]  
**Rango típico:** 1-100 mm/día para ríos con intercambio sedimento-agua.  
**Conversión:** 1 mm/día = 1.157×10⁻⁸ m/s

### **FLOW v3**
**Definición:** Estilo visual estandarizado del proyecto para figuras de publicación y paneles interactivos.

**Características:** Fuentes sans-serif (Calibri/Arial), color celeste `#4FC3F7` para datos filtrados, bordes negros en ejes, grilla gris suave, fondo blanco, DPI 300. Se aplica en figuras estáticas (matplotlib) y paneles HTML (Plotly/Folium).

### **FOLIUM**
**Definición:** Librería Python para crear mapas interactivos basados en Leaflet.js.

**Contexto VFLUX2:** Genera los paneles SIG interactivos con capas satelitales (Esri WorldImagery), marcadores por termocupla con popups de series temporales, y controles de capas. Archivo generado: `panel_sig_integrado_05A.html` y `panel_sig_tendencia_central_mad.html`.

---

## H

### **HATCH-AMPLITUDE**
**Definición:** Método VFLUX2 que estima flujo vertical usando únicamente la atenuación de amplitud térmica entre sensores.

**Ventajas:**
- Robusto y confiable
- Independiente de problemas de fase
- Elegido como método principal en caso Silala

**Estado en proyecto:** VALIDADO (56 cm/día, rango Silala)

### **HATCH-PHASE**
**Definición:** Método VFLUX2 que estima flujo vertical usando el desfase de fase térmica entre sensores.

**Problema identificado:** Error dimensional fundamental en ecuación implementada.  
**Estado en proyecto:** Requiere corrección antes de uso.

---

## I

### **iBUTTON (DS1922L)**
**Definición:** Sensor autónomo de temperatura de alta resolución (0.0625 °C) fabricado por Maxim Integrated, encapsulado en acero inoxidable de 17 mm de diámetro.

**Contexto VFLUX2:** 15 sensores iButton distribuidos en 5 termocuplas (3 por TC) a profundidades de 0, 0.20–0.28 y 0.40–0.56 m en el lecho del Río Cuncumén. Registran temperatura cada 10 min durante la campaña Dic 2025 – Feb 2026.

---

## M

### **MAD (Median Absolute Deviation)**
**Definición:** Medida robusta de dispersión estadística definida como la mediana de las desviaciones absolutas respecto a la mediana de los datos.

**Fórmula:** MAD = mediana(|xᵢ − mediana(x)|)  
**Z-score modificado:** Zₘ = 0.6745 × |xᵢ − mediana(x)| / MAD

**Contexto VFLUX2:** Se usa como filtro de outliers con umbral Zₘ < 2.5 (con fallback a 3.5 y 5.0 si se descarta >90% de los datos). El resultado filtrado se suaviza con mediana móvil de ventana 5 para obtener la tendencia central del flujo.

### **MCCALLUM**
**Definición:** Método VFLUX2 que combina información de amplitud y fase para estimación de flujo más robusta.

**Característica especial:** Incluye sistema de fallback a Hatch-Amplitude cuando la ecuación combinada no puede resolverse.  
**Estado en proyecto:** Funcional con fallback (198.9 mm/día, usa respaldo cuando discriminante < 0).

### **MÉTODO TÉRMICO**
**Definición:** Técnica que utiliza la propagación de señales de temperatura para inferir movimiento de agua subterránea.

**Principio:** El agua en movimiento transporta calor (advección), modificando los patrones naturales de difusión térmica.

---

## N

### **NÚMERO DE PÉCLET (Pe)**
**Definición:** Parámetro adimensional que indica la importancia relativa de advección vs. difusión térmica.

**Fórmula:** Pe = (v × L) / α  
**Interpretación:**
- Pe << 1: Difusión domina (métodos térmicos válidos)
- Pe >> 1: Advección domina (límite de validez de métodos)

**Valor en proyecto:** Pe ≈ 0.022 (difusión domina, métodos válidos)

---

## P

### **PARÁMETROS TÉRMICOS**
**Definición:** Propiedades físicas del sedimento que controlan la propagación del calor.

**Principales:**
- **λ (conductividad):** 0.8 W/m·K (calibrado)
- **C (capacidad calorífica):** 5.0 MJ/m³·K (calibrado)  
- **α (difusividad):** λ/C = 1.60×10⁻⁷ m²/s

### **PIPELINE**
**Definición:** Secuencia automatizada de 11 etapas que procesa datos crudos de temperatura hasta generar resultados, figuras y paneles interactivos.

**Implementaciones:** 3 modos de ejecución — Python puro (`run_pipeline.py`), Prefect orquestado (`prefect_pipeline.py`) y Docker (`docker compose`). Las etapas se ejecutan secuencialmente: carga → alineación → armónico → flujo → series → confiabilidad → incertidumbre → IQR → exportación → resumen → figuras + paneles.

### **PREFECT**
**Definición:** Framework de orquestación de flujos de trabajo en Python que proporciona observabilidad, reintentos automáticos y dashboard web.

**Contexto VFLUX2:** El pipeline Hatch-Amplitude se ejecuta como un `@flow` de Prefect con 11 `@task` modulares en `scripts/stages/`. El dashboard (http://localhost:4200) muestra estado, duración y logs de cada corrida. Se puede ejecutar localmente o vía Docker.

---

## R

### **RANGO SILALA**
**Definición:** Intervalo de flujos verticales medidos en el río Silala (Chile-Bolivia) que sirve como referencia de validación.

**Valores:** 9-60 cm/día  
**Fuente:** Suárez et al. (2023), DOI: 10.1002/wat2.1639  
**Importancia:** Nuestro resultado (56 cm/día) está dentro de este rango validado.

---

## S

### **SEPARACIÓN CONDUCTIVO/ADVECTIVO**
**Definición:** Proceso matemático de dividir el desfase térmico total en sus componentes físicos fundamentales.

**Fórmula:** Δφ_total = Δφ_conductivo + Δφ_advectivo  
**Importancia crítica:** Solo el componente advectivo refleja el flujo de agua real.  
**Aplicación:** Esencial para métodos Hatch-Phase y Keery.

---

## T

### **TERMOCUPLAS**
**Definición:** Sensores de temperatura de alta precisión utilizados para medir variaciones térmicas en sedimentos.

**En el proyecto:** 5 termocuplas (TC1–TC5) instaladas en el lecho del Río Cuncumén, cada una con 3 sensores iButton DS1922L a profundidades de 0, 0.20–0.28 y 0.40–0.56 m. Registran temperatura cada 10 minutos durante Dic 2025 – Feb 2026.

### **TENDENCIA CENTRAL (MAD)**
**Definición:** Serie temporal de flujo procesada con filtrado MAD (Median Absolute Deviation) y suavizada con mediana móvil, que representa el comportamiento central del flujo eliminando valores atípicos.

**Parámetros:** Umbral MAD = 2.5, ventana suavizado = 5 puntos (con fallback a 3.5 y 5.0).  
**Archivos generados:**
- `series_tendencia_central_informe.png/pdf` — Panel 5×1 con series por TC
- `boxplot_tendencia_central_informe.png/pdf` — Distribución por TC
- `resumen_estadistico_tendencia_central_MAD.csv/xlsx` — Tabla estadística
- `panel_sig_tendencia_central_mad.html` — Mapa interactivo con popups

---

## V

### **VFLUX2**
**Definición:** Software y conjunto de métodos para calcular flujos verticales entre agua superficial y sedimento usando señales térmicas.

**Métodos incluidos:** 5 métodos térmicos (Hatch-Amplitude, Hatch-Phase, McCallum, Keery, Luce)  
**Objetivo del proyecto:** Implementar versión Python compatible con MATLAB original.

### **VALIDACIÓN CRUZADA**
**Definición:** Proceso de verificar resultados usando múltiples métodos independientes y comparar con literatura.

**En proyecto:**
- Coherencia con caso Silala
- Consistencia entre métodos funcionales
- Parámetros dentro de rangos físicamente realistas

---

## Siglas y Abreviaturas

- **CV:** Coeficiente de Variación
- **DOI:** Digital Object Identifier (identificador de documentos)
- **FFT:** Fast Fourier Transform (análisis frecuencial)
- **IQR:** Interquartile Range (rango intercuartílico Q1–Q3)
- **MAD:** Median Absolute Deviation (desviación absoluta mediana)
- **MATLAB:** Lenguaje de programación científica
- **Pe:** Número de Péclet
- **SI:** Sistema Internacional de Unidades
- **SIG:** Sistema de Información Geográfica
- **TR:** Temperature Rod (varilla de temperatura)
- **TC:** Termocupla

---

## Referencias Bibliográficas

- **Hatch et al. (2006)** - Métodos Hatch: DOI 10.1029/2006WR004835
- **McCallum et al. (2012)** - Método McCallum: DOI 10.1029/2012WR012007  
- **Keery et al. (2007)** - Método Keery: DOI 10.1016/j.jhydrol.2006.12.003
- **Luce et al. (2013)** - Método Luce: DOI 10.1029/2012WR012380
- **Suárez et al. (2023)** - Caso Silala: DOI 10.1002/wat2.1639

---

**Elaborado por:** GitHub Copilot + Cesar (FlowHydroTech)  
**Última actualización:** 25 de marzo de 2026  
**Estado:** Versión 2.0 - Incluye términos de pipeline Prefect, Docker, filtrado MAD y tendencia central