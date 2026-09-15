"""
Gestor de Base de Datos SQLite Consolidada para Ejecución Presupuestaria DIPRES.
Almacena informes procesados, filas normalizadas y provee funciones analíticas.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd
import config

class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or config.DB_PATH
        self.init_db()

    def get_connection(self):
        """Retorna una conexión a SQLite con timeout adecuado."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Crea las tablas e índices si no existen."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Tabla de metadatos de informes descargados y procesados
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS informes_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                ministerio TEXT NOT NULL,
                programa TEXT NOT NULL,
                codigo_programa TEXT,
                titulo_informe TEXT,
                periodo TEXT NOT NULL,
                moneda TEXT NOT NULL,
                url_xls TEXT UNIQUE,
                archivo_local TEXT,
                fecha_descarga TEXT,
                fecha_proceso TEXT,
                filas_procesadas INTEGER DEFAULT 0
            );
            """)

            # Tabla de ejecución presupuestaria normalizada y consolidada
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ejecucion_consolidada (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                informe_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                ministerio TEXT NOT NULL,
                programa TEXT NOT NULL,
                codigo_programa TEXT,
                periodo TEXT NOT NULL,
                moneda TEXT NOT NULL,
                fila_excel INTEGER,
                tipo TEXT,
                nivel TEXT,
                subtitulo_cod TEXT,
                subtitulo_nom TEXT,
                item_cod TEXT,
                item_nom TEXT,
                asig_cod TEXT,
                clasificacion TEXT,
                categoria_gasto TEXT,
                tipo_presupuesto TEXT,
                presupuesto_inicial REAL,
                presupuesto_vigente REAL,
                ejecucion_acumulada REAL,
                saldo REAL,
                pct_ejecucion REAL,
                es_inversion INTEGER,
                es_inversion_directa INTEGER,
                FOREIGN KEY (informe_id) REFERENCES informes_metadata(id) ON DELETE CASCADE
            );
            """)

            # Índices de optimización para consultas rápidas en el dashboard
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_meta_prog ON informes_metadata(year, ministerio, programa);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ejec_filtro ON ejecucion_consolidada(year, ministerio, programa, periodo);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ejec_subt ON ejecucion_consolidada(subtitulo_cod);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ejec_inv ON ejecucion_consolidada(es_inversion_directa);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ejec_nivel ON ejecucion_consolidada(tipo, nivel);")

            conn.commit()

    def save_report_data(self, report_item, metadata, df_records):
        """
        Inserta o actualiza un informe y sus filas asociadas de manera transaccional.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        url_xls = report_item.get("url_xls", "")
        raw_periodo = report_item.get("periodo", "")
        periodo_clean = config.TRIMESTRES_A_MESES.get(str(raw_periodo).strip().lower(), str(raw_periodo).strip())

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Verificar si ya existe el informe
            cursor.execute("SELECT id FROM informes_metadata WHERE url_xls = ?", (url_xls,))
            row = cursor.fetchone()

            if row:
                informe_id = row["id"]
                # Borrar registros anteriores para evitar duplicados al reprocesar
                cursor.execute("DELETE FROM ejecucion_consolidada WHERE informe_id = ?", (informe_id,))
                cursor.execute("""
                UPDATE informes_metadata SET
                    periodo = ?,
                    codigo_programa = ?,
                    fecha_proceso = ?,
                    filas_procesadas = ?,
                    archivo_local = ?
                WHERE id = ?
                """, (
                    periodo_clean,
                    metadata.get("codigo_programa", ""),
                    now_str,
                    len(df_records),
                    str(report_item.get("archivo_local", "")),
                    informe_id
                ))
            else:
                cursor.execute("""
                INSERT INTO informes_metadata (
                    year, ministerio, programa, codigo_programa, titulo_informe,
                    periodo, moneda, url_xls, archivo_local, fecha_descarga,
                    fecha_proceso, filas_procesadas
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report_item.get("year", 2026),
                    report_item.get("ministerio", ""),
                    report_item.get("programa", ""),
                    metadata.get("codigo_programa", ""),
                    report_item.get("titulo_informe", ""),
                    periodo_clean,
                    report_item.get("moneda", "Pesos"),
                    url_xls,
                    str(report_item.get("archivo_local", "")),
                    now_str,
                    now_str,
                    len(df_records)
                ))
                informe_id = cursor.lastrowid

            # Insertar filas normalizadas
            rows_to_insert = []
            for _, r in df_records.iterrows():
                rows_to_insert.append((
                    informe_id,
                    report_item.get("year", 2026),
                    report_item.get("ministerio", ""),
                    report_item.get("programa", ""),
                    metadata.get("codigo_programa", ""),
                    periodo_clean,
                    report_item.get("moneda", "Pesos"),
                    int(r.get("fila_excel", 0)),
                    str(r.get("tipo", "")),
                    str(r.get("nivel", "")),
                    str(r.get("subtitulo_cod", "")),
                    str(r.get("subtitulo_nom", "")),
                    str(r.get("item_cod", "")),
                    str(r.get("item_nom", "")),
                    str(r.get("asig_cod", "")),
                    str(r.get("clasificacion", "")),
                    str(r.get("categoria_gasto", "")),
                    str(r.get("tipo_presupuesto", "")),
                    float(r.get("presupuesto_inicial", 0.0)),
                    float(r.get("presupuesto_vigente", 0.0)),
                    float(r.get("ejecucion_acumulada", 0.0)),
                    float(r.get("saldo", 0.0)),
                    float(r.get("pct_ejecucion", 0.0)),
                    1 if r.get("es_inversion") else 0,
                    1 if r.get("es_inversion_directa") else 0
                ))

            cursor.executemany("""
            INSERT INTO ejecucion_consolidada (
                informe_id, year, ministerio, programa, codigo_programa, periodo, moneda,
                fila_excel, tipo, nivel, subtitulo_cod, subtitulo_nom, item_cod, item_nom,
                asig_cod, clasificacion, categoria_gasto, tipo_presupuesto,
                presupuesto_inicial, presupuesto_vigente, ejecucion_acumulada,
                saldo, pct_ejecucion, es_inversion, es_inversion_directa
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows_to_insert)

            conn.commit()
            return informe_id

    def is_report_ingested(self, report_item):
        """
        Verifica si el informe ya fue descargado, parseado y guardado en la BD
        con filas procesadas (> 0).
        """
        url_xls = report_item.get("url_xls", "")
        if url_xls:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT filas_procesadas FROM informes_metadata WHERE url_xls = ?", (url_xls,))
                row = cursor.fetchone()
                if row and row["filas_procesadas"] and row["filas_procesadas"] > 0:
                    return True
        # Chequeo alternativo por atributos clave
        y = report_item.get("year")
        m = report_item.get("ministerio")
        p = report_item.get("programa")
        per = report_item.get("periodo")
        mon = report_item.get("moneda", "Pesos")
        if y and m and p and per:
            norm_per = config.TRIMESTRES_A_MESES.get(str(per).strip().lower(), str(per).strip())
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT filas_procesadas FROM informes_metadata 
                    WHERE year = ? AND ministerio = ? AND programa = ? AND (periodo = ? OR periodo = ?) AND moneda = ?
                """, (y, m, p, norm_per, str(per), mon))
                row = cursor.fetchone()
                if row and row["filas_procesadas"] and row["filas_procesadas"] > 0:
                    return True
        return False

    def get_ingested_urls_set(self):
        """
        Retorna un conjunto (set) de todas las URLs de informes ya procesados en la BD.
        Permite validaciones masivas ultra rápidas en memoria O(1).
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT url_xls FROM informes_metadata WHERE filas_procesadas > 0 AND url_xls IS NOT NULL AND url_xls != ''")
            return set(r[0] for r in cursor.fetchall())

    def get_ingested_keys_set(self):
        """
        Retorna un conjunto de tuplas (year, ministerio, programa, periodo, moneda) de informes ya consolidados.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT year, ministerio, programa, periodo, moneda FROM informes_metadata WHERE filas_procesadas > 0")
            return set((r[0], r[1], r[2], r[3], r[4]) for r in cursor.fetchall())

    def get_processed_reports_summary(self):
        """Retorna un resumen de informes guardados en BD."""
        query = """
        SELECT
            year,
            ministerio,
            COUNT(DISTINCT programa) as total_programas,
            COUNT(DISTINCT periodo) as total_periodos,
            COUNT(*) as total_informes,
            SUM(filas_procesadas) as total_filas
        FROM informes_metadata
        GROUP BY year, ministerio
        ORDER BY ministerio;
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn)

    def get_available_filters(self):
        """Retorna los valores únicos presentes en la BD para poblar filtros."""
        with self.get_connection() as conn:
            ministerios = [r[0] for r in conn.execute("SELECT DISTINCT ministerio FROM informes_metadata ORDER BY ministerio").fetchall()]
            programas = [r[0] for r in conn.execute("SELECT DISTINCT programa FROM informes_metadata ORDER BY programa").fetchall()]
            periodos = [r[0] for r in conn.execute("SELECT DISTINCT periodo FROM informes_metadata ORDER BY periodo").fetchall()]
            anios = [r[0] for r in conn.execute("SELECT DISTINCT year FROM informes_metadata ORDER BY year DESC").fetchall()]
        return {
            "anios": anios,
            "ministerios": ministerios,
            "programas": programas,
            "periodos": periodos
        }

    def _build_where_clause(self, year=None, ministerio=None, programas=None, periodos=None, moneda=None, subtitulo=None):
        clauses = []
        params = []
        if year:
            clauses.append("year = ?")
            params.append(year)
        if ministerio:
            clauses.append("(ministerio = ? OR ministerio LIKE ?)")
            params.extend([ministerio.strip(), f"%{ministerio.strip()}%"])
        if programas:
            if isinstance(programas, str):
                programas = [programas]
            cleaned_progs = [p.strip() for p in programas]
            placeholders = ",".join(["?"] * len(cleaned_progs))
            clauses.append(f"programa IN ({placeholders})")
            params.extend(cleaned_progs)
        if periodos:
            if isinstance(periodos, str):
                periodos = [periodos]
            norm_periodos = set()
            for p in periodos:
                norm = config.TRIMESTRES_A_MESES.get(str(p).strip().lower(), str(p).strip())
                norm_periodos.add(norm)
                norm_periodos.add(str(p).strip())
            norm_list = list(norm_periodos)
            placeholders = ",".join(["?"] * len(norm_list))
            clauses.append(f"periodo IN ({placeholders})")
            params.extend(norm_list)
        if moneda:
            clauses.append("moneda = ?")
            params.append(moneda)
        if subtitulo:
            if isinstance(subtitulo, str):
                subtitulo = [subtitulo]
            placeholders = ",".join(["?"] * len(subtitulo))
            clauses.append(f"subtitulo_cod IN ({placeholders})")
            params.extend(subtitulo)

        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        return where_sql, params

    def get_kpis(self, year=None, ministerio=None, programas=None, periodo=None, moneda="Pesos"):
        """
        Calcula los KPIs globales para el último periodo seleccionado.
        Usa el nivel TIPO == 'GASTOS' para evitar doble contabilidad.
        """
        where_sql, params = self._build_where_clause(
            year=year, ministerio=ministerio, programas=programas,
            periodos=[periodo] if periodo else None, moneda=moneda
        )
        extra_condition = "AND tipo = 'GASTOS' AND nivel = 'TIPO'" if where_sql else "WHERE tipo = 'GASTOS' AND nivel = 'TIPO'"

        query = f"""
        SELECT
            SUM(presupuesto_inicial) as total_inicial,
            SUM(presupuesto_vigente) as total_vigente,
            SUM(ejecucion_acumulada) as total_ejecucion,
            SUM(saldo) as total_saldo
        FROM ejecucion_consolidada
        {where_sql} {extra_condition}
        """

        # Inversión y Gastos de Capital: Subtítulos 29, 31 y 33
        extra_inv_total = "AND subtitulo_cod IN ('29', '31', '33') AND nivel = 'SUBTITULO'" if where_sql else "WHERE subtitulo_cod IN ('29', '31', '33') AND nivel = 'SUBTITULO'"
        query_inv_total = f"""
        SELECT
            SUM(presupuesto_vigente) as vig_total,
            SUM(ejecucion_acumulada) as ejec_total
        FROM ejecucion_consolidada
        {where_sql} {extra_inv_total}
        """

        # Desglose específico por cada uno de los 3 subtítulos (29, 31, 33)
        extra_subts = "AND subtitulo_cod IN ('29', '31', '33') AND nivel = 'SUBTITULO'" if where_sql else "WHERE subtitulo_cod IN ('29', '31', '33') AND nivel = 'SUBTITULO'"
        query_subts = f"""
        SELECT
            subtitulo_cod,
            SUM(presupuesto_vigente) as vigente,
            SUM(ejecucion_acumulada) as ejecucion
        FROM ejecucion_consolidada
        {where_sql} {extra_subts}
        GROUP BY subtitulo_cod
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()

            cursor.execute(query_inv_total, params)
            row_inv_tot = cursor.fetchone()

            cursor.execute(query_subts, params)
            rows_subts = {r["subtitulo_cod"]: {"vig": r["vigente"] or 0.0, "ejec": r["ejecucion"] or 0.0} for r in cursor.fetchall()}

        tot_ini = row["total_inicial"] or 0.0
        tot_vig = row["total_vigente"] or 0.0
        tot_ejec = row["total_ejecucion"] or 0.0
        tot_saldo = row["total_saldo"] or 0.0
        pct_global = round((tot_ejec / tot_vig * 100), 2) if tot_vig > 0 else 0.0

        inv_tot_vig = row_inv_tot["vig_total"] or 0.0
        inv_tot_ejec = row_inv_tot["ejec_total"] or 0.0
        pct_inv_tot = round((inv_tot_ejec / inv_tot_vig * 100), 2) if inv_tot_vig > 0 else 0.0

        # Subtítulo 29
        s29 = rows_subts.get("29", {"vig": 0.0, "ejec": 0.0})
        pct_s29 = round((s29["ejec"] / s29["vig"] * 100), 2) if s29["vig"] > 0 else 0.0

        # Subtítulo 31
        s31 = rows_subts.get("31", {"vig": 0.0, "ejec": 0.0})
        pct_s31 = round((s31["ejec"] / s31["vig"] * 100), 2) if s31["vig"] > 0 else 0.0

        # Subtítulo 33
        s33 = rows_subts.get("33", {"vig": 0.0, "ejec": 0.0})
        pct_s33 = round((s33["ejec"] / s33["vig"] * 100), 2) if s33["vig"] > 0 else 0.0

        return {
            "presupuesto_inicial": tot_ini,
            "presupuesto_vigente": tot_vig,
            "ejecucion_acumulada": tot_ejec,
            "saldo": tot_saldo,
            "pct_ejecucion": pct_global,
            # Total Capital / Inversión (29 + 31 + 33)
            "capital_vigente": inv_tot_vig,
            "capital_ejecucion": inv_tot_ejec,
            "pct_capital": pct_inv_tot,
            # Subtítulo 29 (Activos No Financieros)
            "subt29_vigente": s29["vig"],
            "subt29_ejecucion": s29["ejec"],
            "pct_subt29": pct_s29,
            # Subtítulo 31 (Iniciativas de Inversión)
            "subt31_vigente": s31["vig"],
            "subt31_ejecucion": s31["ejec"],
            "pct_subt31": pct_s31,
            # Subtítulo 33 (Transferencias de Capital)
            "subt33_vigente": s33["vig"],
            "subt33_ejecucion": s33["ejec"],
            "pct_subt33": pct_s33
        }

    def get_subtitulos_breakdown(self, year=None, ministerio=None, programas=None, periodo=None, moneda="Pesos"):
        """Desglose de gastos por subtítulo presupuestario."""
        where_sql, params = self._build_where_clause(
            year=year, ministerio=ministerio, programas=programas,
            periodos=[periodo] if periodo else None, moneda=moneda
        )
        extra = "AND nivel = 'SUBTITULO' AND tipo = 'GASTOS'" if where_sql else "WHERE nivel = 'SUBTITULO' AND tipo = 'GASTOS'"

        query = f"""
        SELECT
            subtitulo_cod,
            subtitulo_nom,
            categoria_gasto,
            SUM(presupuesto_inicial) as inicial,
            SUM(presupuesto_vigente) as vigente,
            SUM(ejecucion_acumulada) as ejecucion,
            SUM(saldo) as saldo,
            CASE WHEN SUM(presupuesto_vigente) > 0
                 THEN ROUND(SUM(ejecucion_acumulada) * 100.0 / SUM(presupuesto_vigente), 2)
                 ELSE 0.0 END as pct_ejecucion
        FROM ejecucion_consolidada
        {where_sql} {extra}
        GROUP BY subtitulo_cod, subtitulo_nom, categoria_gasto
        ORDER BY vigente DESC
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_programas_comparison(self, year=None, ministerio=None, programas=None, periodo=None, moneda="Pesos"):
        """Comparación del gasto y avance entre programas/servicios."""
        where_sql, params = self._build_where_clause(
            year=year, ministerio=ministerio, programas=programas,
            periodos=[periodo] if periodo else None, moneda=moneda
        )
        extra = "AND nivel = 'TIPO' AND tipo = 'GASTOS'" if where_sql else "WHERE nivel = 'TIPO' AND tipo = 'GASTOS'"

        query = f"""
        SELECT
            programa,
            codigo_programa,
            SUM(presupuesto_inicial) as inicial,
            SUM(presupuesto_vigente) as vigente,
            SUM(ejecucion_acumulada) as ejecucion,
            SUM(saldo) as saldo,
            CASE WHEN SUM(presupuesto_vigente) > 0
                 THEN ROUND(SUM(ejecucion_acumulada) * 100.0 / SUM(presupuesto_vigente), 2)
                 ELSE 0.0 END as pct_ejecucion
        FROM ejecucion_consolidada
        {where_sql} {extra}
        GROUP BY programa, codigo_programa
        ORDER BY vigente DESC
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_inversiones_summary(self, year=None, ministerio=None, programas=None, periodo=None, subtitulos=None, moneda="Pesos"):
        """Desglose específico de gastos de capital e inversión (Subtítulos 29, 31, 33) por programa, subtítulo e ítem."""
        where_sql, params = self._build_where_clause(
            year=year, ministerio=ministerio, programas=programas,
            periodos=[periodo] if periodo else None, moneda=moneda
        )
        target_subts = subtitulos if subtitulos else ["29", "31", "33"]
        if isinstance(target_subts, str):
            target_subts = [target_subts]
        placeholders = ",".join(["?"] * len(target_subts))
        params.extend(target_subts)

        extra = f"AND subtitulo_cod IN ({placeholders}) AND nivel IN ('SUBTITULO', 'ITEM')" if where_sql else f"WHERE subtitulo_cod IN ({placeholders}) AND nivel IN ('SUBTITULO', 'ITEM')"

        query = f"""
        SELECT
            subtitulo_cod,
            subtitulo_nom,
            programa,
            nivel,
            item_cod,
            item_nom,
            clasificacion,
            SUM(presupuesto_vigente) as vigente,
            SUM(ejecucion_acumulada) as ejecucion,
            SUM(saldo) as saldo,
            CASE WHEN SUM(presupuesto_vigente) > 0
                 THEN ROUND(SUM(ejecucion_acumulada) * 100.0 / SUM(presupuesto_vigente), 2)
                 ELSE 0.0 END as pct_ejecucion
        FROM ejecucion_consolidada
        {where_sql} {extra}
        GROUP BY subtitulo_cod, subtitulo_nom, programa, nivel, item_cod, item_nom, clasificacion
        ORDER BY subtitulo_cod, programa, nivel DESC, vigente DESC
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_monthly_evolution(self, year=None, ministerio=None, programas=None, subtitulo=None, moneda="Pesos"):
        """Serie de tiempo de ejecución acumulada por periodo/mes."""
        where_sql, params = self._build_where_clause(
            year=year, ministerio=ministerio, programas=programas,
            subtitulo=subtitulo, moneda=moneda
        )
        if subtitulo:
            extra = "AND nivel = 'SUBTITULO'" if where_sql else "WHERE nivel = 'SUBTITULO'"
        else:
            extra = "AND nivel = 'TIPO' AND tipo = 'GASTOS'" if where_sql else "WHERE nivel = 'TIPO' AND tipo = 'GASTOS'"

        query = f"""
        SELECT
            periodo,
            programa,
            SUM(presupuesto_vigente) as vigente,
            SUM(ejecucion_acumulada) as ejecucion,
            CASE WHEN SUM(presupuesto_vigente) > 0
                 THEN ROUND(SUM(ejecucion_acumulada) * 100.0 / SUM(presupuesto_vigente), 2)
                 ELSE 0.0 END as pct_ejecucion
        FROM ejecucion_consolidada
        {where_sql} {extra}
        GROUP BY periodo, programa
        """
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)

        if not df.empty:
            # Ordenar periodos según el orden del calendario oficial
            orden_map = {mes: i for i, mes in enumerate(config.MESES_ORDEN)}
            df["orden"] = df["periodo"].map(lambda x: orden_map.get(x, 99))
            df = df.sort_values(by=["orden", "programa"]).drop(columns=["orden"])
        return df

    def get_detailed_records(self, year=None, ministerio=None, programas=None, periodos=None, subtitulo=None, solo_inversion=False, search_text=None, moneda="Pesos", limit=1000):
        """Retorna filas detalladas con búsqueda y filtros para la tabla del explorador."""
        where_sql, params = self._build_where_clause(
            year=year, ministerio=ministerio, programas=programas,
            periodos=periodos, subtitulo=subtitulo, moneda=moneda
        )
        conditions = []
        if solo_inversion:
            conditions.append("subtitulo_cod IN ('29', '31', '33')")
        if search_text:
            conditions.append("(clasificacion LIKE ? OR subtitulo_nom LIKE ? OR item_nom LIKE ?)")
            pat = f"%{search_text}%"
            params.extend([pat, pat, pat])

        if conditions:
            connector = "AND" if where_sql else "WHERE"
            where_sql += f" {connector} " + " AND ".join(conditions)

        query = f"""
        SELECT
            year as "Año",
            periodo as "Periodo",
            programa as "Programa",
            subtitulo_cod as "Subt",
            item_cod as "Ítem",
            asig_cod as "Asig",
            clasificacion as "Clasificación Económica",
            nivel as "Nivel",
            presupuesto_inicial as "Presupuesto Inicial (M$)",
            presupuesto_vigente as "Presupuesto Vigente (M$)",
            ejecucion_acumulada as "Ejecución Acumulada (M$)",
            saldo as "Saldo (M$)",
            pct_ejecucion as "% Ejecución"
        FROM ejecucion_consolidada
        {where_sql}
        ORDER BY year DESC, programa, fila_excel
        LIMIT {limit}
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def export_consolidated_to_excel(self, output_path, **kwargs):
        """Exporta los datos consolidados a un archivo Excel con formato profesional."""
        df = self.get_detailed_records(limit=100000, **kwargs)
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Ejecución Consolidada", index=False)
        return output_path

    def export_consolidated_to_csv(self, output_path, **kwargs):
        """Exporta los datos consolidados a CSV."""
        df = self.get_detailed_records(limit=100000, **kwargs)
        df.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")
        return output_path

    def get_available_years_for_ministry(self, ministerio):
        """Retorna la lista de años disponibles en BD para un ministerio específico."""
        if not ministerio:
            return []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT year 
                FROM ejecucion_consolidada 
                WHERE ministerio = ? OR ministerio LIKE ?
                ORDER BY year ASC
            """, (ministerio.strip(), f"%{ministerio.strip()}%"))
            return [r[0] for r in cursor.fetchall()]

    def get_available_periods_for_ministry_years(self, ministerio, years):
        """Retorna los periodos disponibles para los años seleccionados, priorizando los que coinciden en más años."""
        if not ministerio or not years:
            return []
        placeholders = ",".join(["?"] * len(years))
        params = [ministerio.strip(), f"%{ministerio.strip()}%"] + list(years)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT periodo, COUNT(DISTINCT year) as year_count
                FROM ejecucion_consolidada
                WHERE (ministerio = ? OR ministerio LIKE ?) AND year IN ({placeholders})
                GROUP BY periodo
                ORDER BY year_count DESC
            """, params)
            return [r[0] for r in cursor.fetchall()]

    def get_multianual_summary(self, ministerio=None, years=None, periodo=None, programas=None, moneda="Pesos"):
        """
        Retorna resumen multianual agrupado por año con métricas globales y de capital.
        Calcula variaciones porcentuales interanuales (YoY).
        """
        if not years:
            return pd.DataFrame()

        clauses = []
        params = []
        if ministerio:
            clauses.append("(ministerio = ? OR ministerio LIKE ?)")
            params.extend([ministerio.strip(), f"%{ministerio.strip()}%"])
        if years:
            ph_years = ",".join(["?"] * len(years))
            clauses.append(f"year IN ({ph_years})")
            params.extend(list(years))
        if periodo:
            norm_p = config.TRIMESTRES_A_MESES.get(str(periodo).strip().lower(), str(periodo).strip())
            clauses.append("(periodo = ? OR periodo = ?)")
            params.extend([norm_p, str(periodo).strip()])
        if programas:
            if isinstance(programas, str):
                programas = [programas]
            cleaned_progs = [p.strip() for p in programas]
            ph_progs = ",".join(["?"] * len(cleaned_progs))
            clauses.append(f"programa IN ({ph_progs})")
            params.extend(cleaned_progs)
        if moneda:
            clauses.append("moneda = ?")
            params.append(moneda)

        where_base = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        # 1. Totales de Gasto a nivel TIPO
        query_global = f"""
        SELECT
            year,
            SUM(presupuesto_inicial) as inicial,
            SUM(presupuesto_vigente) as vigente,
            SUM(ejecucion_acumulada) as ejecucion,
            SUM(saldo) as saldo,
            CASE WHEN SUM(presupuesto_vigente) > 0 
                 THEN ROUND(SUM(ejecucion_acumulada) * 100.0 / SUM(presupuesto_vigente), 2)
                 ELSE 0.0 END as pct_ejecucion
        FROM ejecucion_consolidada
        {where_base} {"AND" if where_base else "WHERE"} tipo = 'GASTOS' AND nivel = 'TIPO'
        GROUP BY year
        ORDER BY year ASC
        """

        # 2. Desglose de Gastos de Capital (Subt. 29, 31, 33)
        query_subts = f"""
        SELECT
            year,
            subtitulo_cod,
            SUM(presupuesto_inicial) as ini_subt,
            SUM(presupuesto_vigente) as vig_subt,
            SUM(ejecucion_acumulada) as ejec_subt
        FROM ejecucion_consolidada
        {where_base} {"AND" if where_base else "WHERE"} subtitulo_cod IN ('29', '31', '33') AND nivel = 'SUBTITULO'
        GROUP BY year, subtitulo_cod
        ORDER BY year ASC
        """

        with self.get_connection() as conn:
            df_global = pd.read_sql_query(query_global, conn, params=params)
            df_subts = pd.read_sql_query(query_subts, conn, params=params)

        if df_global.empty:
            return pd.DataFrame()

        # Inicializar columnas de capital
        df_global["capital_inicial"] = 0.0
        df_global["capital_vigente"] = 0.0
        df_global["capital_ejecucion"] = 0.0
        df_global["pct_capital"] = 0.0
        df_global["subt31_inicial"] = 0.0
        df_global["subt31_vigente"] = 0.0
        df_global["subt31_ejecucion"] = 0.0
        df_global["subt29_inicial"] = 0.0
        df_global["subt29_vigente"] = 0.0
        df_global["subt29_ejecucion"] = 0.0
        df_global["subt33_inicial"] = 0.0
        df_global["subt33_vigente"] = 0.0
        df_global["subt33_ejecucion"] = 0.0

        if not df_subts.empty:
            for y in df_global["year"].unique():
                sub_y = df_subts[df_subts["year"] == y]
                cap_ini = sub_y["ini_subt"].sum()
                cap_vig = sub_y["vig_subt"].sum()
                cap_ejec = sub_y["ejec_subt"].sum()
                pct_cap = round(cap_ejec * 100.0 / cap_vig, 2) if cap_vig > 0 else 0.0

                s31 = sub_y[sub_y["subtitulo_cod"] == "31"]
                s29 = sub_y[sub_y["subtitulo_cod"] == "29"]
                s33 = sub_y[sub_y["subtitulo_cod"] == "33"]

                idx = df_global[df_global["year"] == y].index
                df_global.loc[idx, "capital_inicial"] = cap_ini
                df_global.loc[idx, "capital_vigente"] = cap_vig
                df_global.loc[idx, "capital_ejecucion"] = cap_ejec
                df_global.loc[idx, "pct_capital"] = pct_cap
                df_global.loc[idx, "subt31_inicial"] = s31["ini_subt"].sum() if not s31.empty else 0.0
                df_global.loc[idx, "subt31_vigente"] = s31["vig_subt"].sum() if not s31.empty else 0.0
                df_global.loc[idx, "subt31_ejecucion"] = s31["ejec_subt"].sum() if not s31.empty else 0.0
                df_global.loc[idx, "subt29_inicial"] = s29["ini_subt"].sum() if not s29.empty else 0.0
                df_global.loc[idx, "subt29_vigente"] = s29["vig_subt"].sum() if not s29.empty else 0.0
                df_global.loc[idx, "subt29_ejecucion"] = s29["ejec_subt"].sum() if not s29.empty else 0.0
                df_global.loc[idx, "subt33_inicial"] = s33["ini_subt"].sum() if not s33.empty else 0.0
                df_global.loc[idx, "subt33_vigente"] = s33["vig_subt"].sum() if not s33.empty else 0.0
                df_global.loc[idx, "subt33_ejecucion"] = s33["ejec_subt"].sum() if not s33.empty else 0.0

        # Calcular variaciones interanuales (YoY)
        df_global["var_inicial_pct"] = df_global["inicial"].pct_change() * 100
        df_global["var_vigente_pct"] = df_global["vigente"].pct_change() * 100
        df_global["var_ejecucion_pct"] = df_global["ejecucion"].pct_change() * 100
        df_global["var_capital_pct"] = df_global["capital_ejecucion"].pct_change() * 100

        return df_global

    def get_multianual_subtitulos_breakdown(self, ministerio=None, years=None, periodo=None, programas=None, moneda="Pesos"):
        """Retorna la serie multianual de subtítulos 29, 31 y 33 para gráficos apilados/agrupados."""
        if not years:
            return pd.DataFrame()

        clauses = []
        params = []
        if ministerio:
            clauses.append("(ministerio = ? OR ministerio LIKE ?)")
            params.extend([ministerio.strip(), f"%{ministerio.strip()}%"])
        if years:
            ph_years = ",".join(["?"] * len(years))
            clauses.append(f"year IN ({ph_years})")
            params.extend(list(years))
        if periodo:
            norm_p = config.TRIMESTRES_A_MESES.get(str(periodo).strip().lower(), str(periodo).strip())
            clauses.append("(periodo = ? OR periodo = ?)")
            params.extend([norm_p, str(periodo).strip()])
        if programas:
            if isinstance(programas, str):
                programas = [programas]
            cleaned_progs = [p.strip() for p in programas]
            ph_progs = ",".join(["?"] * len(cleaned_progs))
            clauses.append(f"programa IN ({ph_progs})")
            params.extend(cleaned_progs)
        if moneda:
            clauses.append("moneda = ?")
            params.append(moneda)

        where_base = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        query = f"""
        SELECT
            year,
            subtitulo_cod,
            subtitulo_nom,
            SUM(presupuesto_vigente) as vigente,
            SUM(ejecucion_acumulada) as ejecucion,
            CASE WHEN SUM(presupuesto_vigente) > 0 
                 THEN ROUND(SUM(ejecucion_acumulada) * 100.0 / SUM(presupuesto_vigente), 2)
                 ELSE 0.0 END as pct_ejecucion
        FROM ejecucion_consolidada
        {where_base} {"AND" if where_base else "WHERE"} subtitulo_cod IN ('29', '31', '33') AND nivel = 'SUBTITULO'
        GROUP BY year, subtitulo_cod, subtitulo_nom
        ORDER BY year ASC, subtitulo_cod ASC
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_multianual_programas_breakdown(self, ministerio=None, years=None, periodo=None, top_n=6, moneda="Pesos"):
        """Retorna la serie histórica de ejecución de los principales programas/servicios."""
        if not years:
            return pd.DataFrame()

        clauses = []
        params = []
        if ministerio:
            clauses.append("(ministerio = ? OR ministerio LIKE ?)")
            params.extend([ministerio.strip(), f"%{ministerio.strip()}%"])
        if years:
            ph_years = ",".join(["?"] * len(years))
            clauses.append(f"year IN ({ph_years})")
            params.extend(list(years))
        if periodo:
            norm_p = config.TRIMESTRES_A_MESES.get(str(periodo).strip().lower(), str(periodo).strip())
            clauses.append("(periodo = ? OR periodo = ?)")
            params.extend([norm_p, str(periodo).strip()])
        if moneda:
            clauses.append("moneda = ?")
            params.append(moneda)

        where_base = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        # Encontrar los top programas con mayor ejecución total en los años
        query_top = f"""
        SELECT programa, SUM(ejecucion_acumulada) as total_ejec
        FROM ejecucion_consolidada
        {where_base} {"AND" if where_base else "WHERE"} nivel = 'TIPO' AND tipo = 'GASTOS'
        GROUP BY programa
        ORDER BY total_ejec DESC
        LIMIT {top_n}
        """
        with self.get_connection() as conn:
            df_top = pd.read_sql_query(query_top, conn, params=params)
            if df_top.empty:
                return pd.DataFrame()
            top_progs = df_top["programa"].tolist()

            ph_top = ",".join(["?"] * len(top_progs))
            query_detail = f"""
            SELECT
                year,
                programa,
                SUM(presupuesto_vigente) as vigente,
                SUM(ejecucion_acumulada) as ejecucion,
                CASE WHEN SUM(presupuesto_vigente) > 0 
                     THEN ROUND(SUM(ejecucion_acumulada) * 100.0 / SUM(presupuesto_vigente), 2)
                     ELSE 0.0 END as pct_ejecucion
            FROM ejecucion_consolidada
            {where_base} {"AND" if where_base else "WHERE"} nivel = 'TIPO' AND tipo = 'GASTOS' AND programa IN ({ph_top})
            GROUP BY year, programa
            ORDER BY year ASC, ejecucion DESC
            """
            return pd.read_sql_query(query_detail, conn, params=params + top_progs)

    def get_national_ministerios_ranking(self, year=None, periodo=None, moneda="Pesos", exclude_tesoro=False, ministerios=None):
        """
        Retorna el ranking consolidado de todos los ministerios para un año y periodo determinado.
        Incluye métricas globales de gasto, así como inversión (Subt. 31) y capital (Subt. 29, 31, 33).
        """
        clauses_base = []
        params_base = []
        if year:
            clauses_base.append("year = ?")
            params_base.append(year)
        if periodo:
            norm_p = config.TRIMESTRES_A_MESES.get(str(periodo).strip().lower(), str(periodo).strip())
            clauses_base.append("(periodo = ? OR periodo = ?)")
            params_base.extend([norm_p, str(periodo).strip()])
        if moneda:
            clauses_base.append("moneda = ?")
            params_base.append(moneda)
        if exclude_tesoro:
            clauses_base.append("(ministerio NOT LIKE '%Tesoro Público%' AND ministerio NOT LIKE '%Tesoro Publico%')")
        if ministerios:
            if isinstance(ministerios, str):
                ministerios = [ministerios]
            ph = ",".join(["?"] * len(ministerios))
            clauses_base.append(f"ministerio IN ({ph})")
            params_base.extend(ministerios)

        where_base = ("WHERE " + " AND ".join(clauses_base)) if clauses_base else ""

        # 1. Totales globales a nivel TIPO
        query_global = f"""
        SELECT
            ministerio,
            SUM(presupuesto_inicial) as inicial,
            SUM(presupuesto_vigente) as vigente,
            SUM(ejecucion_acumulada) as ejecucion,
            SUM(saldo) as saldo,
            CASE WHEN SUM(presupuesto_vigente) > 0
                 THEN ROUND(SUM(ejecucion_acumulada) * 100.0 / SUM(presupuesto_vigente), 2)
                 ELSE 0.0 END as pct_ejecucion
        FROM ejecucion_consolidada
        {where_base} {"AND" if where_base else "WHERE"} tipo = 'GASTOS' AND nivel = 'TIPO'
        GROUP BY ministerio
        ORDER BY vigente DESC
        """

        # 2. Desglose de Gastos de Capital (29, 31, 33), Inversión (31), Personal (21) y Bienes y Servicios (22)
        query_inv = f"""
        SELECT
            ministerio,
            SUM(CASE WHEN subtitulo_cod IN ('29', '31', '33') THEN presupuesto_inicial ELSE 0 END) as capital_inicial,
            SUM(CASE WHEN subtitulo_cod IN ('29', '31', '33') THEN presupuesto_vigente ELSE 0 END) as capital_vigente,
            SUM(CASE WHEN subtitulo_cod IN ('29', '31', '33') THEN ejecucion_acumulada ELSE 0 END) as capital_ejecucion,
            SUM(CASE WHEN subtitulo_cod = '31' THEN presupuesto_inicial ELSE 0 END) as subt31_inicial,
            SUM(CASE WHEN subtitulo_cod = '31' THEN presupuesto_vigente ELSE 0 END) as subt31_vigente,
            SUM(CASE WHEN subtitulo_cod = '31' THEN ejecucion_acumulada ELSE 0 END) as subt31_ejecucion,
            SUM(CASE WHEN subtitulo_cod = '21' THEN presupuesto_vigente ELSE 0 END) as subt21_vigente,
            SUM(CASE WHEN subtitulo_cod = '21' THEN ejecucion_acumulada ELSE 0 END) as subt21_ejecucion,
            SUM(CASE WHEN subtitulo_cod = '22' THEN presupuesto_vigente ELSE 0 END) as subt22_vigente,
            SUM(CASE WHEN subtitulo_cod = '22' THEN ejecucion_acumulada ELSE 0 END) as subt22_ejecucion,
            SUM(CASE WHEN subtitulo_cod = '29' THEN presupuesto_vigente ELSE 0 END) as subt29_vigente,
            SUM(CASE WHEN subtitulo_cod = '29' THEN ejecucion_acumulada ELSE 0 END) as subt29_ejecucion,
            SUM(CASE WHEN subtitulo_cod = '33' THEN presupuesto_vigente ELSE 0 END) as subt33_vigente,
            SUM(CASE WHEN subtitulo_cod = '33' THEN ejecucion_acumulada ELSE 0 END) as subt33_ejecucion
        FROM ejecucion_consolidada
        {where_base} {"AND" if where_base else "WHERE"} nivel = 'SUBTITULO' AND subtitulo_cod IN ('21', '22', '29', '31', '33')
        GROUP BY ministerio
        """

        with self.get_connection() as conn:
            df_global = pd.read_sql_query(query_global, conn, params=params_base)
            df_inv = pd.read_sql_query(query_inv, conn, params=params_base)

        if df_global.empty:
            return pd.DataFrame()

        if not df_inv.empty:
            df_merged = pd.merge(df_global, df_inv, on="ministerio", how="left").fillna(0.0)
        else:
            df_merged = df_global.copy()
            df_merged["capital_inicial"] = 0.0
            df_merged["capital_vigente"] = 0.0
            df_merged["capital_ejecucion"] = 0.0
            df_merged["subt31_inicial"] = 0.0
            df_merged["subt31_vigente"] = 0.0
            df_merged["subt31_ejecucion"] = 0.0
            df_merged["subt21_vigente"] = 0.0
            df_merged["subt21_ejecucion"] = 0.0
            df_merged["subt22_vigente"] = 0.0
            df_merged["subt22_ejecucion"] = 0.0
            df_merged["subt29_vigente"] = 0.0
            df_merged["subt29_ejecucion"] = 0.0
            df_merged["subt33_vigente"] = 0.0
            df_merged["subt33_ejecucion"] = 0.0

        # Porcentajes de avance y ratios clave
        df_merged["pct_capital"] = df_merged.apply(
            lambda r: round(r["capital_ejecucion"] * 100.0 / r["capital_vigente"], 2) if r["capital_vigente"] > 0 else 0.0, axis=1
        )
        df_merged["pct_subt31"] = df_merged.apply(
            lambda r: round(r["subt31_ejecucion"] * 100.0 / r["subt31_vigente"], 2) if r["subt31_vigente"] > 0 else 0.0, axis=1
        )
        df_merged["pct_subt21"] = df_merged.apply(
            lambda r: round(r["subt21_ejecucion"] * 100.0 / r["subt21_vigente"], 2) if r["subt21_vigente"] > 0 else 0.0, axis=1
        )
        df_merged["pct_share_inv"] = df_merged.apply(
            lambda r: round(r["subt31_vigente"] * 100.0 / r["vigente"], 2) if r["vigente"] > 0 else 0.0, axis=1
        )
        df_merged["pct_share_cap"] = df_merged.apply(
            lambda r: round(r["capital_vigente"] * 100.0 / r["vigente"], 2) if r["vigente"] > 0 else 0.0, axis=1
        )

        return df_merged

    def get_national_multiyear_ranking(self, years=None, periodo=None, moneda="Pesos", exclude_tesoro=True, ministerios=None):
        """
        Retorna matriz multianual interministerial para comparar años seleccionados (ej. 2018 a 2026).
        Calcula vigente, devengado, saldo, % ejecución, subt31 e inversión agrupado por (year, ministerio).
        """
        if not years:
            years = [2022, 2023, 2024, 2025, 2026]

        clauses_base = []
        params_base = []
        if years:
            ph_years = ",".join(["?"] * len(years))
            clauses_base.append(f"year IN ({ph_years})")
            params_base.extend(list(years))
        if periodo:
            norm_p = config.TRIMESTRES_A_MESES.get(str(periodo).strip().lower(), str(periodo).strip())
            clauses_base.append("(periodo = ? OR periodo = ?)")
            params_base.extend([norm_p, str(periodo).strip()])
        if moneda:
            clauses_base.append("moneda = ?")
            params_base.append(moneda)
        if exclude_tesoro:
            clauses_base.append("(ministerio NOT LIKE '%Tesoro Público%' AND ministerio NOT LIKE '%Tesoro Publico%')")
        if ministerios:
            if isinstance(ministerios, str):
                ministerios = [ministerios]
            ph = ",".join(["?"] * len(ministerios))
            clauses_base.append(f"ministerio IN ({ph})")
            params_base.extend(ministerios)

        where_base = ("WHERE " + " AND ".join(clauses_base)) if clauses_base else ""

        query_global = f"""
        SELECT
            year,
            ministerio,
            SUM(presupuesto_inicial) as inicial,
            SUM(presupuesto_vigente) as vigente,
            SUM(ejecucion_acumulada) as ejecucion,
            SUM(saldo) as saldo,
            CASE WHEN SUM(presupuesto_vigente) > 0
                 THEN ROUND(SUM(ejecucion_acumulada) * 100.0 / SUM(presupuesto_vigente), 2)
                 ELSE 0.0 END as pct_ejecucion
        FROM ejecucion_consolidada
        {where_base} {"AND" if where_base else "WHERE"} tipo = 'GASTOS' AND nivel = 'TIPO'
        GROUP BY year, ministerio
        ORDER BY year ASC, vigente DESC
        """

        query_inv = f"""
        SELECT
            year,
            ministerio,
            SUM(CASE WHEN subtitulo_cod IN ('29', '31', '33') THEN presupuesto_vigente ELSE 0 END) as capital_vigente,
            SUM(CASE WHEN subtitulo_cod IN ('29', '31', '33') THEN ejecucion_acumulada ELSE 0 END) as capital_ejecucion,
            SUM(CASE WHEN subtitulo_cod = '31' THEN presupuesto_vigente ELSE 0 END) as subt31_vigente,
            SUM(CASE WHEN subtitulo_cod = '31' THEN ejecucion_acumulada ELSE 0 END) as subt31_ejecucion
        FROM ejecucion_consolidada
        {where_base} {"AND" if where_base else "WHERE"} nivel = 'SUBTITULO' AND subtitulo_cod IN ('29', '31', '33')
        GROUP BY year, ministerio
        """

        with self.get_connection() as conn:
            df_global = pd.read_sql_query(query_global, conn, params=params_base)
            df_inv = pd.read_sql_query(query_inv, conn, params=params_base)

        if df_global.empty:
            return pd.DataFrame()

        if not df_inv.empty:
            df_merged = pd.merge(df_global, df_inv, on=["year", "ministerio"], how="left").fillna(0.0)
        else:
            df_merged = df_global.copy()
            df_merged["capital_vigente"] = 0.0
            df_merged["capital_ejecucion"] = 0.0
            df_merged["subt31_vigente"] = 0.0
            df_merged["subt31_ejecucion"] = 0.0

        df_merged["pct_subt31"] = df_merged.apply(
            lambda r: round(r["subt31_ejecucion"] * 100.0 / r["subt31_vigente"], 2) if r["subt31_vigente"] > 0 else 0.0, axis=1
        )
        df_merged["pct_capital"] = df_merged.apply(
            lambda r: round(r["capital_ejecucion"] * 100.0 / r["capital_vigente"], 2) if r["capital_vigente"] > 0 else 0.0, axis=1
        )
        df_merged["pct_share_inv"] = df_merged.apply(
            lambda r: round(r["subt31_vigente"] * 100.0 / r["vigente"], 2) if r["vigente"] > 0 else 0.0, axis=1
        )
        return df_merged

    def get_national_monthly_progression(self, year, moneda="Pesos", exclude_tesoro=True, ministerios=None):
        """
        Retorna la progresión mensual continua de ejecución y % de avance para todos los ministerios durante un año (Enero a Diciembre).
        Utilizado para mapas de calor (Heatmap) y curvas de aceleración del gasto.
        """
        meses_orden = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        ph_meses = ",".join(["?"] * len(meses_orden))

        clauses = ["year = ?", "moneda = ?", f"periodo IN ({ph_meses})", "tipo = 'GASTOS'", "nivel = 'TIPO'"]
        params = [year, moneda] + meses_orden

        if exclude_tesoro:
            clauses.append("(ministerio NOT LIKE '%Tesoro Público%' AND ministerio NOT LIKE '%Tesoro Publico%')")
        if ministerios:
            if isinstance(ministerios, str):
                ministerios = [ministerios]
            ph = ",".join(["?"] * len(ministerios))
            clauses.append(f"ministerio IN ({ph})")
            params.extend(ministerios)

        where_str = "WHERE " + " AND ".join(clauses)

        query = f"""
        SELECT
            periodo,
            ministerio,
            SUM(presupuesto_vigente) as vigente,
            SUM(ejecucion_acumulada) as ejecucion,
            CASE WHEN SUM(presupuesto_vigente) > 0
                 THEN ROUND(SUM(ejecucion_acumulada) * 100.0 / SUM(presupuesto_vigente), 2)
                 ELSE 0.0 END as pct_ejecucion
        FROM ejecucion_consolidada
        {where_str}
        GROUP BY periodo, ministerio
        ORDER BY ministerio ASC
        """
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)

        if df.empty:
            return pd.DataFrame()

        df["mes_num"] = df["periodo"].apply(lambda p: meses_orden.index(p) + 1 if p in meses_orden else 99)
        df = df.sort_values(by=["ministerio", "mes_num"]).reset_index(drop=True)
        return df

    def get_national_budget_growth(self, start_year=2022, end_year=2026, periodo="Junio", moneda="Pesos", exclude_tesoro=True, ministerios=None):
        """
        Calcula la variación y el aumento de Presupuesto Vigente por ministerio entre dos años (tramo configurable, ej. 2022 a 2026).
        Calcula variación porcentual (% de aumento), incremento absoluto ($ MM), y clasifica por tramos de crecimiento.
        """
        df_ini = self.get_national_ministerios_ranking(
            year=start_year,
            periodo=periodo,
            moneda=moneda,
            exclude_tesoro=exclude_tesoro,
            ministerios=ministerios
        )
        df_fin = self.get_national_ministerios_ranking(
            year=end_year,
            periodo=periodo,
            moneda=moneda,
            exclude_tesoro=exclude_tesoro,
            ministerios=ministerios
        )

        if df_ini.empty or df_fin.empty:
            return pd.DataFrame()

        cols_keep = ["ministerio", "vigente", "ejecucion", "pct_ejecucion", "subt31_vigente", "subt31_ejecucion"]
        m = pd.merge(
            df_ini[cols_keep],
            df_fin[cols_keep],
            on="ministerio",
            suffixes=("_ini", "_fin")
        )

        if m.empty:
            return pd.DataFrame()

        m["ini_mm"] = m["vigente_ini"] * 1000 / 1e9
        m["fin_mm"] = m["vigente_fin"] * 1000 / 1e9
        m["dif_mm"] = m["fin_mm"] - m["ini_mm"]
        m["pct_aumento"] = m.apply(
            lambda r: round((r["vigente_fin"] - r["vigente_ini"]) * 100.0 / r["vigente_ini"], 2) if r["vigente_ini"] > 0 else 0.0,
            axis=1
        )

        # Inversión Subt. 31
        m["subt31_ini_mm"] = m["subt31_vigente_ini"] * 1000 / 1e9
        m["subt31_fin_mm"] = m["subt31_vigente_fin"] * 1000 / 1e9
        m["subt31_dif_mm"] = m["subt31_fin_mm"] - m["subt31_ini_mm"]
        m["subt31_pct_aumento"] = m.apply(
            lambda r: round((r["subt31_vigente_fin"] - r["subt31_vigente_ini"]) * 100.0 / r["subt31_vigente_ini"], 2) if r["subt31_vigente_ini"] > 0 else 0.0,
            axis=1
        )

        def clasificar_tramo(pct):
            if pct >= 50.0:
                return "🚀 Extraordinario (> 50%)"
            elif pct >= 25.0:
                return "📈 Alto (25% a 50%)"
            elif pct >= 10.0:
                return "📊 Moderado (10% a 25%)"
            elif pct >= 0.0:
                return "⚖️ Leve (0% a 10%)"
            else:
                return "🔻 Contracción (< 0%)"

        def color_tramo(pct):
            if pct >= 50.0:
                return "#10b981"  # Verde esmeralda
            elif pct >= 25.0:
                return "#2563eb"  # Azul real
            elif pct >= 10.0:
                return "#8b5cf6"  # Púrpura
            elif pct >= 0.0:
                return "#f59e0b"  # Ámbar
            else:
                return "#ef4444"  # Rojo coral

        m["tramo"] = m["pct_aumento"].apply(clasificar_tramo)
        m["tramo_color"] = m["pct_aumento"].apply(color_tramo)
        m["start_year"] = start_year
        m["end_year"] = end_year
        m = m.sort_values(by="pct_aumento", ascending=False).reset_index(drop=True)
        return m

    def get_national_top_programas(self, year=None, periodo=None, moneda="Pesos", top_n=15, exclude_tesoro=False, ministerios=None):
        """
        Retorna los principales programas/servicios del país según presupuesto vigente y ejecución.
        """
        clauses = []
        params = []
        if year:
            clauses.append("year = ?")
            params.append(year)
        if periodo:
            norm_p = config.TRIMESTRES_A_MESES.get(str(periodo).strip().lower(), str(periodo).strip())
            clauses.append("(periodo = ? OR periodo = ?)")
            params.extend([norm_p, str(periodo).strip()])
        if moneda:
            clauses.append("moneda = ?")
            params.append(moneda)
        if exclude_tesoro:
            clauses.append("(ministerio NOT LIKE '%Tesoro Público%' AND ministerio NOT LIKE '%Tesoro Publico%')")
        if ministerios:
            if isinstance(ministerios, str):
                ministerios = [ministerios]
            ph = ",".join(["?"] * len(ministerios))
            clauses.append(f"ministerio IN ({ph})")
            params.extend(ministerios)

        where_base = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        query = f"""
        SELECT
            ministerio,
            programa,
            SUM(presupuesto_inicial) as inicial,
            SUM(presupuesto_vigente) as vigente,
            SUM(ejecucion_acumulada) as ejecucion,
            SUM(saldo) as saldo,
            CASE WHEN SUM(presupuesto_vigente) > 0
                 THEN ROUND(SUM(ejecucion_acumulada) * 100.0 / SUM(presupuesto_vigente), 2)
                 ELSE 0.0 END as pct_ejecucion
        FROM ejecucion_consolidada
        {where_base} {"AND" if where_base else "WHERE"} nivel = 'TIPO' AND tipo = 'GASTOS'
        GROUP BY ministerio, programa
        ORDER BY vigente DESC
        LIMIT {top_n}
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_national_subtitulos_breakdown(self, year=None, periodo=None, moneda="Pesos", exclude_tesoro=False, ministerios=None):
        """
        Retorna la composición del gasto público nacional por subtítulo.
        """
        clauses = []
        params = []
        if year:
            clauses.append("year = ?")
            params.append(year)
        if periodo:
            norm_p = config.TRIMESTRES_A_MESES.get(str(periodo).strip().lower(), str(periodo).strip())
            clauses.append("(periodo = ? OR periodo = ?)")
            params.extend([norm_p, str(periodo).strip()])
        if moneda:
            clauses.append("moneda = ?")
            params.append(moneda)
        if exclude_tesoro:
            clauses.append("(ministerio NOT LIKE '%Tesoro Público%' AND ministerio NOT LIKE '%Tesoro Publico%')")
        if ministerios:
            if isinstance(ministerios, str):
                ministerios = [ministerios]
            ph = ",".join(["?"] * len(ministerios))
            clauses.append(f"ministerio IN ({ph})")
            params.extend(ministerios)

        where_base = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        query = f"""
        SELECT
            subtitulo_cod,
            subtitulo_nom,
            categoria_gasto,
            SUM(presupuesto_inicial) as inicial,
            SUM(presupuesto_vigente) as vigente,
            SUM(ejecucion_acumulada) as ejecucion,
            SUM(saldo) as saldo,
            CASE WHEN SUM(presupuesto_vigente) > 0
                 THEN ROUND(SUM(ejecucion_acumulada) * 100.0 / SUM(presupuesto_vigente), 2)
                 ELSE 0.0 END as pct_ejecucion
        FROM ejecucion_consolidada
        {where_base} {"AND" if where_base else "WHERE"} nivel = 'SUBTITULO' AND tipo = 'GASTOS'
        GROUP BY subtitulo_cod, subtitulo_nom, categoria_gasto
        ORDER BY vigente DESC
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_national_subtitulos_by_ministerio(self, year=None, periodo=None, moneda="Pesos", exclude_tesoro=True, ministerios=None):
        """
        Retorna la composición del gasto público nacional por ministerio y por subtítulo.
        Utilizado para análisis de calidad del gasto, treemaps jerárquicos y barras apiladas al 100%.
        """
        clauses = []
        params = []
        if year:
            clauses.append("year = ?")
            params.append(year)
        if periodo:
            norm_p = config.TRIMESTRES_A_MESES.get(str(periodo).strip().lower(), str(periodo).strip())
            clauses.append("(periodo = ? OR periodo = ?)")
            params.extend([norm_p, str(periodo).strip()])
        if moneda:
            clauses.append("moneda = ?")
            params.append(moneda)
        if exclude_tesoro:
            clauses.append("(ministerio NOT LIKE '%Tesoro Público%' AND ministerio NOT LIKE '%Tesoro Publico%')")
        if ministerios:
            if isinstance(ministerios, str):
                ministerios = [ministerios]
            ph = ",".join(["?"] * len(ministerios))
            clauses.append(f"ministerio IN ({ph})")
            params.extend(ministerios)

        where_base = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        query = f"""
        SELECT
            ministerio,
            subtitulo_cod,
            subtitulo_nom,
            categoria_gasto,
            SUM(presupuesto_inicial) as inicial,
            SUM(presupuesto_vigente) as vigente,
            SUM(ejecucion_acumulada) as ejecucion,
            SUM(saldo) as saldo,
            CASE WHEN SUM(presupuesto_vigente) > 0
                 THEN ROUND(SUM(ejecucion_acumulada) * 100.0 / SUM(presupuesto_vigente), 2)
                 ELSE 0.0 END as pct_ejecucion
        FROM ejecucion_consolidada
        {where_base} {"AND" if where_base else "WHERE"} nivel = 'SUBTITULO' AND tipo = 'GASTOS'
        GROUP BY ministerio, subtitulo_cod, subtitulo_nom, categoria_gasto
        ORDER BY ministerio ASC, vigente DESC
        """
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)

        if not df.empty:
            df["ini_mm"] = df["inicial"] * 1000 / 1e9
            df["vigente_mm"] = df["vigente"] * 1000 / 1e9
            df["ejec_mm"] = df["ejecucion"] * 1000 / 1e9
            df["saldo_mm"] = df["saldo"] * 1000 / 1e9
        return df

    def get_available_periods_for_year(self, year=None, moneda="Pesos"):
        """
        Retorna la lista de periodos disponibles para un año determinado,
        ordenados por la cantidad de ministerios presentes.
        """
        if not year:
            return []
        query = """
        SELECT periodo, COUNT(DISTINCT ministerio) as min_count
        FROM ejecucion_consolidada
        WHERE year = ? AND moneda = ?
        GROUP BY periodo
        ORDER BY min_count DESC
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (year, moneda))
            rows = cursor.fetchall()
            found = [r[0] for r in rows]
            ordered = [m for m in config.MESES_ORDEN if m in found]
            for p in found:
                if p not in ordered:
                    ordered.append(p)
            return ordered

    def get_national_budget_growth(self, start_year=2022, end_year=2026, periodo="Junio", moneda="Pesos", exclude_tesoro=True, ministerios=None):
        """
        Calcula el crecimiento del presupuesto vigente por ministerio entre start_year y end_year.
        Retorna un DataFrame ordenado con:
        - ministerio
        - vigente_ini, vigente_fin (Pesos)
        - ini_mm, fin_mm, dif_mm (Miles de Millones)
        - pct_aumento (% variación interanual en el tramo)
        - tramo (clasificación cualitativa por tramos de crecimiento)
        """
        df_ini = self.get_national_ministerios_ranking(year=start_year, periodo=periodo, moneda=moneda, exclude_tesoro=exclude_tesoro, ministerios=ministerios)
        df_fin = self.get_national_ministerios_ranking(year=end_year, periodo=periodo, moneda=moneda, exclude_tesoro=exclude_tesoro, ministerios=ministerios)
        
        if df_ini.empty or df_fin.empty:
            return pd.DataFrame()
            
        m = pd.merge(
            df_ini[['ministerio', 'vigente']], 
            df_fin[['ministerio', 'vigente']], 
            on='ministerio', 
            suffixes=('_ini', '_fin')
        )
        if m.empty:
            return pd.DataFrame()

        m['ini_mm'] = m['vigente_ini'] * 1000 / 1e9
        m['fin_mm'] = m['vigente_fin'] * 1000 / 1e9
        m['dif_mm'] = m['fin_mm'] - m['ini_mm']
        m['pct_aumento'] = m.apply(
            lambda r: round(((r['vigente_fin'] - r['vigente_ini']) / r['vigente_ini'] * 100), 2) if r['vigente_ini'] > 0 else 0.0, 
            axis=1
        )

        def clasificar_tramo(pct):
            if pct >= 50.0:
                return "🚀 Extraordinario (> 50%)"
            elif pct >= 25.0:
                return "📈 Alto (25% a 50%)"
            elif pct >= 10.0:
                return "📊 Moderado (10% a 25%)"
            elif pct >= 0.0:
                return "⚖️ Leve (0% a 10%)"
            else:
                return "🔻 Contracción (< 0%)"

        m['tramo'] = m['pct_aumento'].apply(clasificar_tramo)
        m = m.sort_values(by='pct_aumento', ascending=False).reset_index(drop=True)
        return m

    def get_loaded_years(self):
        """
        Retorna la lista ordenada de todos los años disponibles con datos cargados en ejecucion_consolidada.
        """
        query = "SELECT DISTINCT year FROM ejecucion_consolidada WHERE year IS NOT NULL ORDER BY year ASC"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            years = [int(r[0]) for r in cursor.fetchall() if r[0] is not None]
        return sorted(years) if years else list(range(2018, 2027))


