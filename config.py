"""
Módulo de Configuración para el Extractor de Ejecución Presupuestaria DIPRES.
"""
from pathlib import Path

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent

# Rutas de datos
DATA_DIR = BASE_DIR / "data"
DOWNLOADS_DIR = DATA_DIR / "downloads"
DATABASE_DIR = DATA_DIR / "database"
EXPORTS_DIR = DATA_DIR / "exports"

# Asegurar directorios
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Ruta a la base de datos SQLite
DB_PATH = DATABASE_DIR / "presupuesto.db"

# URLs Base DIPRES
DIPRES_BASE_URL = "https://www.dipres.gob.cl/597/"
DIPRES_PORTADILLA_URL = "https://www.dipres.gob.cl/597/w3-multipropertyvalues-25910-{year_id}.html#ejec_programa"
DIPRES_AUX_PROGRAMA_URL = "https://www.dipres.gob.cl/597/aux-multipropertyvalues-25930-{year_id}.html"

# Mapeo completo de Años a IDs internos de Newtenberg DIPRES (2000 a 2026)
# Fuente: https://www.dipres.gob.cl/598/w3-propertyvalue-2129.html
YEAR_IDS = {
    2026: "37782",
    2025: "36882",
    2024: "35869",
    2023: "35324",
    2022: "34905",
    2021: "25771",
    2020: "25190",
    2019: "24532",
    2018: "24043",
    2017: "23712",
    2016: "22940",
    2015: "22369",
    2014: "22027",
    2013: "21672",
    2012: "21327",
    2011: "20971",
    2010: "2430",
    2009: "15967",
    2008: "15192",
    2007: "14885",
    2006: "13406",
    2005: "11154",
    2004: "11166",
    2003: "11207",
    2002: "11239",
    2001: "14882",
    2000: "14883"
}

# Subtítulos presupuestarios chilenos clave
SUBTITULOS_INFO = {
    "21": {"nombre": "Gastos en Personal", "tipo": "Corriente", "categoria": "Operación"},
    "22": {"nombre": "Bienes y Servicios de Consumo", "tipo": "Corriente", "categoria": "Operación"},
    "23": {"nombre": "Prestaciones de Seguridad Social", "tipo": "Corriente", "categoria": "Transferencias"},
    "24": {"nombre": "Transferencias Corrientes", "tipo": "Corriente", "categoria": "Transferencias"},
    "25": {"nombre": "Íntegros al Fisco", "tipo": "Corriente", "categoria": "Otros"},
    "26": {"nombre": "Otros Gastos Corrientes", "tipo": "Corriente", "categoria": "Otros"},
    "29": {"nombre": "Adquisición de Activos No Financieros", "tipo": "Capital", "categoria": "Inversión"},
    "30": {"nombre": "Adquisición de Activos Financieros", "tipo": "Capital", "categoria": "Financiero"},
    "31": {"nombre": "Iniciativas de Inversión", "tipo": "Capital", "categoria": "Inversión"},
    "32": {"nombre": "Préstamos", "tipo": "Capital", "categoria": "Financiero"},
    "33": {"nombre": "Transferencias de Capital", "tipo": "Capital", "categoria": "Inversión"},
    "34": {"nombre": "Servicio de la Deuda", "tipo": "Capital", "categoria": "Deuda"},
    "35": {"nombre": "Saldo Final de Caja", "tipo": "Capital", "categoria": "Caja"}
}

# Meses y orden cronológico oficial (12 meses calendario)
MESES_ORDEN = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# Mapeo de trimestres e informes de cierre a meses calendario
TRIMESTRES_A_MESES = {
    "primer trimestre": "Marzo",
    "1er trimestre": "Marzo",
    "i trimestre": "Marzo",
    "segundo trimestre": "Junio",
    "2do trimestre": "Junio",
    "ii trimestre": "Junio",
    "tercer trimestre": "Septiembre",
    "tercero trimestre": "Septiembre",
    "3er trimestre": "Septiembre",
    "iii trimestre": "Septiembre",
    "cuarto trimestre": "Diciembre",
    "4to trimestre": "Diciembre",
    "iv trimestre": "Diciembre",
    "cierre": "Diciembre",
    "desconocido": "Diciembre",
}

MESES_A_TRIMESTRES = {
    "Marzo": "Primer Trimestre",
    "Junio": "Segundo Trimestre",
    "Septiembre": "Tercer Trimestre",
    "Diciembre": "Cuarto Trimestre",
}

