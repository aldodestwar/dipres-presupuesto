"""
Punto de Entrada CLI para el Extractor y Consolidado de Ejecución Presupuestaria DIPRES.
Permite ejecutar descargas, consolidación y exportaciones directamente desde consola.
"""
import argparse
import sys
from pathlib import Path
import pandas as pd

import config
from src.dipres_scraper import DipresScraper
from src.excel_parser import DipresExcelParser
from src.db_manager import DatabaseManager

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extractor y Analizador de Ejecución Presupuestaria DIPRES"
    )
    parser.add_argument(
        "--year", "-y", type=int, default=2026,
        help="Año de ejecución presupuestaria (default: 2026)"
    )
    parser.add_argument(
        "--ministerio", "-m", type=str, default="Ministerio de Obras Públicas",
        help="Nombre o fragmento del ministerio a filtrar (default: 'Ministerio de Obras Públicas')"
    )
    parser.add_argument(
        "--programa", "-p", type=str, default=None,
        help="Nombre o fragmento del programa/servicio a filtrar"
    )
    parser.add_argument(
        "--periodo", type=str, default=None,
        help="Mes o periodo específico (ej. 'Enero', 'Primer Trimestre')"
    )
    parser.add_argument(
        "--moneda", type=str, default="Pesos", choices=["Pesos", "Dólares", "Todos"],
        help="Moneda de los informes (default: 'Pesos')"
    )
    parser.add_argument(
        "--download", "-d", action="store_true",
        help="Descargar los archivos Excel encontrados"
    )
    parser.add_argument(
        "--consolidate", "-c", action="store_true",
        help="Parsear los Excel descargados y guardarlos en la base de datos SQLite"
    )
    parser.add_argument(
        "--export", "-e", choices=["excel", "csv"], default=None,
        help="Exportar los datos consolidados de la BD a un archivo"
    )
    parser.add_argument(
        "--status", "-s", action="store_true",
        help="Mostrar estado actual de la base de datos y reportes procesados"
    )
    parser.add_argument(
        "--list-ministerios", action="store_true",
        help="Listar todos los ministerios disponibles en el catálogo"
    )
    parser.add_argument(
        "--list-programas", action="store_true",
        help="Listar los programas del ministerio seleccionado"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    db = DatabaseManager()

    if args.status:
        print("\n================ ESTADO DE BASE DE DATOS ================")
        summary = db.get_processed_reports_summary()
        if summary.empty:
            print("La base de datos está vacía. Ejecuta un comando de descarga y consolidación.")
        else:
            print(summary.to_string(index=False))
        return

    scraper = DipresScraper(year=args.year)
    print(f"Cargando catálogo DIPRES para el año {args.year}...")
    catalog = scraper.build_catalog()
    print(f"Total de informes encontrados en DIPRES: {len(catalog)}")

    if args.list_ministerios:
        print(f"\nMinisterios disponibles ({len(scraper.get_ministerios())}):")
        for m in scraper.get_ministerios():
            print(f" - {m}")
        return

    # Buscar ministerio más cercano
    selected_min = None
    if args.ministerio:
        for m in scraper.get_ministerios():
            if args.ministerio.lower() in m.lower():
                selected_min = m
                break
        if not selected_min:
            print(f"No se encontró ministerio que coincida con '{args.ministerio}'.")
            return

    if args.list_programas:
        print(f"\nProgramas para {selected_min}:")
        for p in scraper.get_programas(selected_min):
            print(f" - {p}")
        return

    # Filtrar catálogo
    monedas = ["Pesos"] if args.moneda == "Pesos" else (["Dólares"] if args.moneda == "Dólares" else ["Pesos", "Dólares"])
    
    # Filtrar por programa si se especificó
    programas_filter = None
    if args.programa:
        all_progs = scraper.get_programas(selected_min)
        programas_filter = [p for p in all_progs if args.programa.lower() in p.lower()]
        if not programas_filter:
            print(f"No se encontraron programas que coincidan con '{args.programa}' en {selected_min}.")
            return

    filtered_reports = scraper.filter_catalog(
        ministerio=selected_min,
        programas=programas_filter,
        periodos=[args.periodo] if args.periodo else None,
        monedas=monedas
    )

    print(f"\nFiltros aplicados:")
    print(f" - Ministerio: {selected_min}")
    print(f" - Programas: {len(programas_filter) if programas_filter else 'Todos'} programas")
    print(f" - Periodo: {args.periodo or 'Todos'}")
    print(f" - Moneda: {args.moneda}")
    print(f"-> Total informes seleccionados: {len(filtered_reports)}")

    if args.download or args.consolidate:
        print("\n--- INICIANDO PROCESO DE DESCARGA Y CONSOLIDACIÓN ---")
        exitos = 0
        errores = 0

        for idx, item in enumerate(filtered_reports, 1):
            prog_short = item["programa"][:35]
            print(f"[{idx}/{len(filtered_reports)}] {prog_short} | {item['periodo']}...", end="", flush=True)

            xls_path = scraper.download_report(item)
            if not xls_path:
                print(" [ERROR DESCARGA]")
                errores += 1
                continue

            item["archivo_local"] = str(xls_path)

            if args.consolidate:
                try:
                    meta, df = DipresExcelParser.parse_file(xls_path)
                    db.save_report_data(item, meta, df)
                    print(f" [OK] ({len(df)} filas)")
                    exitos += 1
                except Exception as e:
                    print(f" [ERROR PARSER: {e}]")
                    errores += 1
            else:
                print(" [DESCARGADO]")
                exitos += 1

        print(f"\nFinalizado: {exitos} exitosos, {errores} errores.")

    if args.export:
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        if args.export == "excel":
            out_file = config.EXPORTS_DIR / f"ejecucion_consolidada_{timestamp}.xlsx"
            db.export_consolidated_to_excel(out_file, ministerio=selected_min)
            print(f"\nExportado a Excel: {out_file}")
        elif args.export == "csv":
            out_file = config.EXPORTS_DIR / f"ejecucion_consolidada_{timestamp}.csv"
            db.export_consolidated_to_csv(out_file, ministerio=selected_min)
            print(f"\nExportado a CSV: {out_file}")

if __name__ == "__main__":
    main()
