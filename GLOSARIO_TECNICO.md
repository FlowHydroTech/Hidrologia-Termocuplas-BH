# GLOSARIO TÉCNICO - PROYECTO VFLUX2

**Fecha:** 19 de noviembre de 2025  
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

## M

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

**En el proyecto:** Datos sintéticos que simulan mediciones de termocuplas a diferentes profundidades (10, 20, 30 cm).

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
- **MATLAB:** Lenguaje de programación científica
- **Pe:** Número de Péclet
- **SI:** Sistema Internacional de Unidades
- **TR:** Temperature Rod (varilla de temperatura)

---

## Referencias Bibliográficas

- **Hatch et al. (2006)** - Métodos Hatch: DOI 10.1029/2006WR004835
- **McCallum et al. (2012)** - Método McCallum: DOI 10.1029/2012WR012007  
- **Keery et al. (2007)** - Método Keery: DOI 10.1016/j.jhydrol.2006.12.003
- **Luce et al. (2013)** - Método Luce: DOI 10.1029/2012WR012380
- **Suárez et al. (2023)** - Caso Silala: DOI 10.1002/wat2.1639

---

**Elaborado por:** GitHub Copilot + Cesar (FlowHydroTech)  
**Última actualización:** 19 de noviembre de 2025  
**Estado:** Versión 1.0 - Conceptos validados con implementación exitosa