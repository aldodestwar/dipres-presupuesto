"""
Parser y Normalizador de Planillas Excel (.xls) de Ejecución Presupuestaria DIPRES.
Estandariza la jerarquía presupuestaria (Subtítulo, Ítem, Asignación) y extrae metadatos.
"""
import re
import pandas as pd
import numpy as np
import config

class DipresExcelParser:
    @staticmethod
    def clean_numeric(val):
        """Convierte valores de Excel a float seguro."""
        if pd.isna(val):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip().replace(".", "").replace(",", ".")
        try:
            return float(val_str)
        except ValueError:
            return 0.0

    @staticmethod
    def clean_code(val):
        """Limpia códigos presupuestarios asegurando string sin decimales."""
        if pd.isna(val):
            return ""
        val_str = str(val).strip()
        # Si vino como float tipo 31.0 -> '31'
        if val_str.endswith(".0"):
            val_str = val_str[:-2]
        return val_str.zfill(2) if len(val_str) == 1 else val_str

    @classmethod
    def parse_file(cls, file_path):
        """
        Lee una planilla .xls de DIPRES y retorna (metadata_dict, dataframe_normalizado).
        """
        try:
            df_raw = pd.read_excel(file_path, engine="xlrd", header=None)
        except Exception as e:
            raise ValueError(f"Error al abrir archivo Excel con motor xlrd: {e}")

        # 1. Encontrar la fila de encabezados
        header_row_idx = None
        for idx in range(min(15, len(df_raw))):
            row_text = " ".join([str(x).lower() for x in df_raw.iloc[idx].values])
            if ("subt" in row_text or "clasificaci" in row_text) and ("presupuesto" in row_text or "inicial" in row_text):
                header_row_idx = idx
                break

        if header_row_idx is None:
            # Búsqueda alternativa por nombres de columnas clásicas
            for idx in range(min(15, len(df_raw))):
                vals = [str(x).strip() for x in df_raw.iloc[idx].values if pd.notna(x)]
                if len(vals) >= 4 and any("Presupuesto" in v for v in vals):
                    header_row_idx = idx
                    break

        if header_row_idx is None:
            raise ValueError(f"No se pudo detectar la fila de encabezados en {file_path}")

        # 2. Extraer metadatos de las filas superiores
        meta_lines = []
        codigo_programa = ""
        nombre_programa = ""
        partida_cod = ""
        capitulo_cod = ""
        programa_cod = ""
        unidad_moneda = ""

        for r in range(header_row_idx):
            non_null = [str(v).strip() for v in df_raw.iloc[r] if pd.notna(v) and str(v).strip()]
            line_str = " - ".join(non_null)
            if line_str:
                meta_lines.append(line_str)

            # Buscar patrón de código de programa: "120101 : SECRETARÍA Y ADMINISTRACIÓN GENERAL"
            for val in non_null:
                m = re.search(r"(\d{6})\s*:\s*(.+)", val)
                if m:
                    codigo_programa = m.group(1)
                    nombre_programa = m.group(2).strip()
                    partida_cod = codigo_programa[:2]
                    capitulo_cod = codigo_programa[2:4]
                    programa_cod = codigo_programa[4:6]
                if "moneda" in val.lower():
                    unidad_moneda = val

        # Nombre de la última columna de ejecución (ej. "Ejecución Acumulada a Enero")
        header_vals = df_raw.iloc[header_row_idx].tolist()
        periodo_ejecucion_header = ""
        for h in header_vals:
            if pd.notna(h) and "ejecuci" in str(h).lower():
                periodo_ejecucion_header = str(h).replace("\n", " ").strip()
                break

        # 3. Detectar índices de columnas
        # Generalmente:
        # Col 1: Subtítulo
        # Col 2: Ítem
        # Col 3: Asignación
        # Col 4: Clasificación Económica
        # Col 5: Presupuesto Inicial
        # Col 6: Presupuesto Vigente
        # Col 7: Ejecución Acumulada
        # Para robustez, buscamos por posición relativa a partir de los textos
        cols_map = {}
        for c_idx, val in enumerate(header_vals):
            if pd.isna(val):
                continue
            v_lower = str(val).lower()
            if "subt" in v_lower:
                cols_map["subt"] = c_idx
            elif "tem" in v_lower:
                cols_map["item"] = c_idx
            elif "asig" in v_lower:
                cols_map["asig"] = c_idx
            elif "clasificaci" in v_lower or "denominaci" in v_lower:
                cols_map["clasificacion"] = c_idx
            elif "inicial" in v_lower:
                cols_map["inicial"] = c_idx
            elif "vigente" in v_lower:
                cols_map["vigente"] = c_idx
            elif "ejecuci" in v_lower:
                cols_map["ejecucion"] = c_idx

        # Fallback si no detectó por nombres exactos
        if "subt" not in cols_map:
            cols_map["subt"] = 1
        if "item" not in cols_map:
            cols_map["item"] = 2
        if "asig" not in cols_map:
            cols_map["asig"] = 3
        if "clasificacion" not in cols_map:
            cols_map["clasificacion"] = 4
        if "inicial" not in cols_map:
            cols_map["inicial"] = 5
        if "vigente" not in cols_map:
            cols_map["vigente"] = 6
        if "ejecucion" not in cols_map:
            cols_map["ejecucion"] = 7

        # 4. Procesar filas de datos
        records = []
        tipo_actual = "GENERAL"
        subt_cod_actual = ""
        subt_nom_actual = ""
        item_cod_actual = ""
        item_nom_actual = ""

        data_rows = df_raw.iloc[header_row_idx + 1:].copy()

        for idx, row in data_rows.iterrows():
            clasificacion_val = row.iloc[cols_map["clasificacion"]] if cols_map["clasificacion"] < len(row) else np.nan
            if pd.isna(clasificacion_val):
                continue
            clasificacion_str = str(clasificacion_val).strip()
            if not clasificacion_str:
                continue

            subt_val = row.iloc[cols_map["subt"]] if cols_map["subt"] < len(row) else np.nan
            item_val = row.iloc[cols_map["item"]] if cols_map["item"] < len(row) else np.nan
            asig_val = row.iloc[cols_map["asig"]] if cols_map["asig"] < len(row) else np.nan

            subt_str = cls.clean_code(subt_val)
            item_str = cls.clean_code(item_val)
            asig_str = cls.clean_code(asig_val)

            ini_val = cls.clean_numeric(row.iloc[cols_map["inicial"]] if cols_map["inicial"] < len(row) else 0)
            vig_val = cls.clean_numeric(row.iloc[cols_map["vigente"]] if cols_map["vigente"] < len(row) else 0)
            ejec_val = cls.clean_numeric(row.iloc[cols_map["ejecucion"]] if cols_map["ejecucion"] < len(row) else 0)

            saldo_val = vig_val - ejec_val
            pct_val = round((ejec_val / vig_val * 100), 2) if vig_val > 0 else 0.0

            # Detectar niveles
            if clasificacion_str.upper() in ["INGRESOS", "GASTOS", "RESULTADO"]:
                tipo_actual = clasificacion_str.upper()
                subt_cod_actual = ""
                subt_nom_actual = ""
                item_cod_actual = ""
                item_nom_actual = ""
                nivel = "TIPO"
            elif subt_str and not item_str and not asig_str:
                # Nivel Subtítulo
                subt_cod_actual = subt_str
                subt_nom_actual = clasificacion_str
                item_cod_actual = ""
                item_nom_actual = ""
                nivel = "SUBTITULO"
            elif item_str and not asig_str:
                # Nivel Ítem
                item_cod_actual = item_str
                item_nom_actual = clasificacion_str
                nivel = "ITEM"
            elif asig_str:
                # Nivel Asignación
                nivel = "ASIGNACION"
            else:
                nivel = "DETALLE"

            # Determinar si es inversión pública
            # Subtítulo 31 = Iniciativas de Inversión
            # Subtítulo 29 = Adquisición de Activos No Financieros
            # Subtítulo 33 = Transferencias de Capital
            es_inversion = subt_cod_actual in ["31", "29", "33"]
            es_inversion_directa = subt_cod_actual == "31"

            # Información enriquecida del subtítulo
            subt_info = config.SUBTITULOS_INFO.get(subt_cod_actual, {})
            categoria_gasto = subt_info.get("categoria", "Otros")
            tipo_presupuesto = subt_info.get("tipo", "Corriente")

            records.append({
                "fila_excel": idx,
                "tipo": tipo_actual,
                "nivel": nivel,
                "subtitulo_cod": subt_cod_actual,
                "subtitulo_nom": subt_nom_actual,
                "item_cod": item_cod_actual,
                "item_nom": item_nom_actual,
                "asig_cod": asig_str,
                "clasificacion": clasificacion_str,
                "categoria_gasto": categoria_gasto,
                "tipo_presupuesto": tipo_presupuesto,
                "presupuesto_inicial": ini_val,
                "presupuesto_vigente": vig_val,
                "ejecucion_acumulada": ejec_val,
                "saldo": saldo_val,
                "pct_ejecucion": pct_val,
                "es_inversion": es_inversion,
                "es_inversion_directa": es_inversion_directa
            })

        df_result = pd.DataFrame(records)

        metadata = {
            "archivo": str(file_path),
            "codigo_programa": codigo_programa,
            "nombre_programa": nombre_programa,
            "partida_cod": partida_cod,
            "capitulo_cod": capitulo_cod,
            "programa_cod": programa_cod,
            "unidad_moneda": unidad_moneda,
            "header_ejecucion": periodo_ejecucion_header,
            "filas_totales": len(df_result)
        }

        return metadata, df_result
