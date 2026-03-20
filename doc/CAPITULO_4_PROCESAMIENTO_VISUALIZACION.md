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

## 4.5 Reproducibilidad

Todo el procesamiento queda registrado en un cuaderno computacional interactivo (notebook Jupyter) que documenta cada paso junto con su resultado, permitiendo verificar, auditar o repetir el análisis completo en cualquier momento.
