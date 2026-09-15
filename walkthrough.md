# Walkthrough: Mejoras Avanzadas en «🏆 Rankings & Tops Nacionales»

Se ha actualizado integralmente la ventana y pestaña analítica **`🏆 Rankings & Tops Nacionales`**, incorporando capacidades avanzadas de análisis anual, multianual (2018–2026), seguimiento mensual continuo, dos nuevos gráficos analíticos estratégicos y una barra de controles para el **Cuadrante Estratégico**.

---

## 🚀 Resumen de Nuevas Funcionalidades

| Capacidad | Descripción | Beneficio Clave |
| :--- | :--- | :--- |
| **Enfoque Temporal Multianual** | Selector entre `📅 Análisis Anual / Mensual` y `📈 Comparativa Multianual (2018-2026)`. | Permite analizar la evolución histórica de todos los ministerios sin cambiar de vista. |
| **Análisis Mensual Continuo** | Filtro de tipo de periodo (`Todos`, `📅 Solo Meses`, `📊 Solo Trimestres`) y selector cronológico (Enero a Diciembre). | Permite examinar el avance mes a mes y detectar estacionalidades del gasto. |
| **Gráfico Extra 1: Serie Multianual** | Evolución Histórica Multianual del Presupuesto y Devengo por Ministerio (2018–2026). | Permite comparar trayectorias presupuestarias con métricas intercambiables y eje categórico sin decimales. |
| **Gráfico Extra 2: Heatmap & Curvas** | Mapa de Calor de Avance Mensual con encabezados superiores (`side="top"`) y toggle a curvas acumuladas. | Visualiza en una sola matriz qué ministerios aceleran o frenan su ejecución a lo largo del año. |
| **Cuadrante Estratégico Optimizado** | Barra de herramientas dedicada con **Escala Logarítmica**, métricas dinámicas en X/Y/Burbuja y filtros por cuadrante. | Resuelve la aglomeración en el origen y permite aislar carteras críticas al instante. |
| **Filtros por Estrato y Avance** | Clasificación automática por tamaño de presupuesto (Grandes, Medianas, Focalizadas) y ritmo de gasto. | Segmentación precisa para análisis de políticas públicas y control de gestión. |

---

## 🎯 1. Controles Avanzados del Cuadrante Estratégico

El **Cuadrante Estratégico** (*Presupuesto Vigente vs. % Avance de Ejecución con Tamaño de Burbuja: Inversión Real Subt. 31*) ahora cuenta con una barra de herramientas de personalización inmediata:

### Mejoras de Visualización y Filtro:
1. **Escala Eje X (Logarítmica por Defecto):**
   - Permite separar con nitidez las carteras medianas y focalizadas (< $1.000 MM) de los macro-ministerios como Obras Públicas, Salud, Educación y Trabajo ($5.000 MM a $45.000 MM), eliminando la aglomeración en el origen.
   - Cuenta con un interruptor para volver a la escala lineal cuando se requiera evaluar magnitudes absolutas.
2. **Métricas Dinámicas e Intercambiables:**
   - **Eje X:** `Presupuesto Vigente`, `Presupuesto Inicial (Ley)`, `Saldo Disponible`, `Ejecución Devengada`.
   - **Eje Y:** `% Avance Presupuestario Total`, `% Inversión Real (Subt. 31 Obras)`, `% Gasto de Capital (29+31+33)`, `% Gasto en Personal (Subt. 21)`.
   - **Tamaño de Burbuja:** `Inversión Real (Subt. 31)`, `Presupuesto Vigente`, `Gasto en Personal (Subt. 21)`, `Saldo Pendiente de Gasto`, `Capital Total (29+31+33)`.
3. **Filtro Rápido por Cuadrante Estratégico:**
   - *Mostrar Todos los Cuadrantes*
   - *🟢 Cuadrante 1: Motores de Ejecución* (Alto presupuesto, alta ejecución)
   - *🟣 Cuadrante 2: Carteras Ágiles* (Presupuesto focalizado, alta eficiencia)
   - *🟡 Cuadrante 3: Alerta de Capacidad* (Alto presupuesto, ejecución rezagada)
   - *⚪ Cuadrante 4: Rezagados / En Riesgo* (Presupuesto focalizado, bajo avance)
4. **Control de Etiquetas de Texto:**
   - *Destacados*: Etiqueta automáticamente carteras clave y extremas sin solapamiento.
   - *Mostrar Todos*: Despliega el nombre en cada una de las 33 carteras.
   - *Solo en Hover*: Vista limpia con tooltip al pasar el cursor.

---

## 📈 2. Gráfico Extra 1: Evolución Histórica Multianual por Ministerio (2018–2026)

Se incorporó un gráfico de series temporales multianuales para evaluar la trayectoria de largo plazo de los ministerios seleccionados:
- **Eje Temporal Categórico:** Los años se presentan como enteros discretos (`2022`, `2023`, `2024`, `2025`, `2026`) sin ticks fraccionarios.
- **Selector de Métrica de Tendencia:** Permite cambiar al instante entre `Presupuesto Vigente`, `Ejecución Devengada`, `% Avance Presupuestario` e `Inversión Real Subt. 31`.
- **Líneas con Marcadores y Hover Rico:** Curvas diferenciadas por cartera ministerial con indicadores de monto y avance en pesos chilenos formateados.

---

## 🌡️ 3. Gráfico Extra 2: Mapa de Calor (Heatmap) y Curvas de Aceleración Mensual

Permite examinar la estacionalidad del gasto a través de los meses disponibles (Enero a Diciembre):
- **Encabezados Superiores Visibles (`side="top"`):** Las columnas de los meses (`Enero`, `Febrero`, `Marzo`, `Abril`, `Mayo`, etc.) se ubican en la parte superior del gráfico, asegurando legibilidad inmediata sin importar la cantidad de carteras.
- **Escala de Colores Viridis:** Gradiente térmico que resalta inmediatamente las carteras que lideran el devengo versus aquellas con bajo gasto.
- **Modo Alternativo: Curvas de Gasto Acumulado:** Con un solo clic se activa la vista de líneas que ilustra la aceleración del gasto mensual acumulado para cada ministerio.

---

## 🔍 4. Nuevos Filtros en el Panel Lateral y Optimización SQL

### A. Enfoque Temporal y Selección Multianual
El usuario puede alternar fácilmente entre:
1. **`📅 Análisis Anual / Mensual`**: Foco en un ejercicio específico con desglose por mes o trimestre.
2. **`📈 Comparativa Multianual (2018-2026)`**: Permite seleccionar libremente años de la serie con botones rápidos (`Todos (2018-26)`, `2022-26`, `2024-26`).

### B. Filtro de Tipo de Periodo y Selección Mensual
- Permite filtrar entre `Todos`, `📅 Solo Meses` y `📊 Solo Trimestres`.
- Al elegir `📅 Solo Meses`, el selector de periodos se restringe exclusivamente a cortes mensuales continuos (`Enero`, `Febrero`, `Marzo`, `Abril`, `Mayo`, `Junio`, `Julio`, etc.).

### C. Nuevos Filtros de Segmentación
- **Estrato Presupuestario:** `Todos los Tamaños`, `🏢 Grandes (> $5.000 MM)`, `🏬 Medianas ($1.000 - $5.000 MM)`, `🎯 Focalizadas (< $1.000 MM)`.
- **Rango de Avance:** `Cualquier Avance`, `🟢 Alto (> 50%)`, `🟡 Regular (35% - 50%)`, `🔴 Rezagados (< 35%)`.

### D. Optimización de Obtención de Datos (`DatabaseManager`)
- Métodos `get_national_multiyear_ranking()` y `get_national_monthly_progression()` implementados con agregaciones SQL nativas indexadas.
- Desglose directo de Subtítulos 21 (Personal), 22 (Bienes y Servicios), 29, 31 y 33 calculado en menos de **0.2 segundos** para más de 30 carteras a lo largo de 9 años.



