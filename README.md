# Sistema de Extracción, Consolidación y Dashboard de Ejecución Presupuestaria (DIPRES) 🏛️🇨🇱

Solución integral y automatizada para scrapear, descargar, parsear y analizar la ejecución presupuestaria publicada por la **Dirección de Presupuestos de Chile (DIPRES)**, con especial énfasis en **Iniciativas de Inversión (Subtítulo 31)** y el **Ministerio de Obras Públicas (MOP)**.

---

## 🌟 Características Principales

1. **Scraping Dinámico del Catálogo DIPRES:**
   - Detecta automáticamente los 33 ministerios y organismos del Estado.
   - Analiza el árbol jerárquico oficial: **Partida (Ministerio) ➔ Capítulo (Dirección / Servicio) ➔ Programa Presupuestario**.
   - Identifica y clasifica todos los informes de ejecución por periodo (**Enero a Diciembre / Trimestres**) y moneda (**Pesos / Dólares**).
   - Descarga inteligente con control de caché: evita volver a descargar archivos ya existentes.

2. **Parser y Normalizador de Planillas Excel (.xls):**
   - Procesa directamente los archivos binarios Excel OLE2 (`xlrd`) publicados por DIPRES.
   - Reconstruye la jerarquía presupuestaria: **Tipo ➔ Subtítulo ➔ Ítem ➔ Asignación**.
   - Calcula métricas clave: `% de Ejecución`, `Saldo por Ejecutar`, y flags especiales para **Inversión Pública (Subtítulo 31)**.

3. **Base de Datos Local Consolidada (SQLite):**
   - Almacena de forma permanente y relacional todos los informes procesados en `data/database/presupuesto.db`.
   - Carga transaccional e idempotente: no duplica registros si se reprocesa un informe.
   - Consultas indexadas y optimizadas para agregaciones instantáneas.

4. **Dashboard Interactivo y Ejecutivo (Streamlit + Plotly):**
   - **Pestaña 1: 📊 Dashboard de Ejecución:** Tarjetas KPI, evolución mensual acumulada del gasto, distribución por subtítulo económico y comparativa entre servicios.
   - **Pestaña 2: 🏗️ Foco Inversión (Subt. 31):** Análisis dedicado a proyectos de infraestructura, obras públicas y estudios básicos.
   - **Pestaña 3: 🌐 Catálogo & Scraper DIPRES:** Interfaz visual para descargar nuevos informes con barra de progreso en vivo.
   - **Pestaña 4: 📑 Base de Datos Consolidada:** Buscador por texto, filtros cruzados y exportación a **Excel (.xlsx)** y **CSV**.

---

## 📁 Estructura del Proyecto

```
Ejecucion presupuestaria imversion/
│
├── app.py                     # Dashboard interactivo principal (Streamlit)
├── main.py                    # Interfaz por línea de comandos (CLI)
├── config.py                  # Parámetros, rutas y mapeos de códigos DIPRES
├── run_dashboard.bat          # Acceso directo para ejecutar en Windows (doble clic)
│
├── src/
│   ├── dipres_scraper.py      # Motor de scraping y descarga desde la web
│   ├── excel_parser.py        # Parser y normalizador de archivos Excel .xls
│   └── db_manager.py          # Gestor de base de datos SQLite y consultas analíticas
│
├── data/
│   ├── downloads/             # Planillas .xls descargadas ordenadas por año y servicio
│   ├── database/              # Base de datos SQLite local (presupuesto.db)
│   └── exports/               # Archivos Excel y CSV exportados
│
└── README.md                  # Documentación del sistema
```

---

## 🚀 Inicio Rápido

### 1. Iniciar el Dashboard Web
Puedes hacer doble clic en `run_dashboard.bat` o ejecutar en tu terminal:

```bash
streamlit run app.py
```

Se abrirá automáticamente tu navegador en `http://localhost:8501`.

---

## 💻 Uso desde la Línea de Comandos (CLI)

El sistema incluye `main.py` para ejecutar descargas y análisis automatizados por terminal:

### Ver estado actual de la base de datos:
```bash
python main.py --status
```

### Listar todos los ministerios disponibles en DIPRES:
```bash
python main.py --list-ministerios
```

### Listar los programas del Ministerio de Obras Públicas:
```bash
python main.py --ministerio "Obras Públicas" --list-programas
```

### Descargar y consolidar programas específicos (ej. Vialidad):
```bash
python main.py --ministerio "Obras Públicas" --programa "Vialidad" --download --consolidate
```

### Descargar y consolidar todo el Ministerio de Obras Públicas:
```bash
python main.py --ministerio "Obras Públicas" --download --consolidate
```

### Exportar la base de datos consolidada a Excel o CSV:
```bash
python main.py --export excel
python main.py --export csv
```

---

## 🔄 Preparado para Futuros Scrapeos

Cuando la DIPRES publique nuevos meses (por ejemplo, Agosto, Septiembre, etc.) o para analizar años futuros:
1. Abre el Dashboard y ve a la pestaña **"🌐 Catálogo & Scraper DIPRES"**.
2. Los nuevos informes aparecerán automáticamente marcados como `⏳ Pendiente`.
3. Presiona el botón **"📥 Descargar & Consolidar"**.
4. El sistema descargará únicamente los informes nuevos, los procesará e incorporará a la base de datos sin alterar los históricos ya consolidados.

---

## 📊 Glosario Presupuestario Clave (Chile)

- **Subtítulo 21:** Gastos en Personal.
- **Subtítulo 22:** Bienes y Servicios de Consumo.
- **Subtítulo 29:** Adquisición de Activos No Financieros (Equipos, software, vehículos).
- **Subtítulo 31 (Iniciativas de Inversión):** Recursos para estudios de preinversión y obras de infraestructura pública (carreteras, embalses, puertos, etc.).
- **Subtítulo 33:** Transferencias de Capital.
