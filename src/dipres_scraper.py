"""
Motor de Scraping para Informes de Ejecución Presupuestaria de DIPRES.
Extrae la jerarquía de Ministerios, Capítulos, Programas e Informes de Ejecución (.xls).
"""
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
import config

class DipresScraper:
    def __init__(self, year=2026):
        self.year = int(year)
        self.year_id = config.YEAR_IDS.get(self.year, "37782")
        self.catalog = []
        self._html_content = None

    @staticmethod
    def clean_text(s):
        """Normaliza texto corrigiendo fallas comunes de codificación y acentuación."""
        if not s:
            return ""
        reemplazos = {
            "Pblicas": "Públicas",
            "P\ufffdblicas": "Públicas",
            "Repblica": "República",
            "Rep\ufffdblica": "República",
            "Secretara": "Secretaría",
            "Secretar\ufffda": "Secretaría",
            "Administracin": "Administración",
            "Administraci\ufffdn": "Administración",
            "Direccin": "Dirección",
            "Direcci\ufffdn": "Dirección",
            "Hidrulicas": "Hidráulicas",
            "Hidr\ufffdulicas": "Hidráulicas",
            "Hidrulica": "Hidráulica",
            "Hidr\ufffdulica": "Hidráulica",
            "Hdrica": "Hídrica",
            "H\ufffdrica": "Hídrica",
            "Cmara": "Cámara",
            "C\ufffdmara": "Cámara",
            "Auditora": "Auditoría",
            "Auditor\ufffda": "Auditoría",
            "Ejecucin": "Ejecución",
            "Ejecuci\ufffdn": "Ejecución",
            "Captulo": "Capítulo",
            "Cap\ufffdtulo": "Capítulo",
            "Gestin": "Gestión",
            "Gesti\ufffdn": "Gestión",
            "Contralora": "Contraloría",
            "Contralor\ufffda": "Contraloría",
            "Fiscala": "Fiscalía",
            "Fiscal\ufffda": "Fiscalía",
            "Subdireccin": "Subdirección",
            "Subdirecci\ufffdn": "Subdirección",
            "Construccin": "Construcción",
            "Construcci\ufffdn": "Construcción",
            "Reparacin": "Reparación",
            "Reparaci\ufffdn": "Reparación",
            "Mantencin": "Mantención",
            "Mantenci\ufffdn": "Mantención",
            "Tramitacin": "Tramitación",
            "Tramitaci\ufffdn": "Tramitación",
        }
        for k, v in reemplazos.items():
            s = s.replace(k, v)
        return re.sub(r'\s+', ' ', s).strip()

    def fetch_aux_html(self, force_refresh=False):
        """
        Descarga o lee de caché el HTML de Programas para cualquier año configurado (2000-2026).
        Implementa búsqueda dinámica con fallback a través de la portadilla oficial DIPRES.
        """
        cache_file = config.DATA_DIR / f"dipres_programa_{self.year}.html"
        if not force_refresh and cache_file.exists() and cache_file.stat().st_size > 50000:
            with open(cache_file, "r", encoding="utf-8") as f:
                self._html_content = f.read()
            # Si el archivo en caché contiene el carácter de reemplazo en palabras críticas, refrescar
            if "P\ufffdblicas" not in self._html_content and "Rep\ufffdblica" not in self._html_content:
                return self._html_content

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
        }

        # 1. Candidato directo estándar (usado en años recientes)
        candidates = [
            f"https://www.dipres.gob.cl/597/aux-multipropertyvalues-25930-{self.year_id}.html",
            f"https://www.dipres.gob.cl/597/aux-multipropertyvalues-{self.year_id}-25930.html"
        ]

        raw_data = None
        for cand_url in candidates:
            try:
                req = urllib.request.Request(cand_url, headers=headers)
                with urllib.request.urlopen(req, timeout=25) as resp:
                    data = resp.read()
                    if b"format-xls" in data or b"recuadros_articulo_5871" in data or b"carga_ejec_programa" in data:
                        raw_data = data
                        break
            except Exception:
                continue

        # 2. Descubrimiento dinámico mediante link rel="appendix"
        if not raw_data:
            portadillas = [
                f"https://www.dipres.gob.cl/597/w3-multipropertyvalues-15149-{self.year_id}.html",
                f"https://www.dipres.gob.cl/597/w3-multipropertyvalues-15199-{self.year_id}.html",
                f"https://www.dipres.gob.cl/597/w3-multipropertyvalues-25910-{self.year_id}.html",
                f"https://www.dipres.gob.cl/597/w3-multipropertyvalues-{self.year_id}-25910.html"
            ]
            for p_url in portadillas:
                try:
                    req_p = urllib.request.Request(p_url, headers=headers)
                    with urllib.request.urlopen(req_p, timeout=20) as resp_p:
                        p_html = resp_p.read().decode("utf-8", errors="replace")
                        p_soup = BeautifulSoup(p_html, "html.parser")
                        for link in p_soup.find_all("link"):
                            rel = link.get("rel", [])
                            if isinstance(rel, list):
                                rel = " ".join(rel)
                            title = link.get("title", "")
                            href = link.get("href", "")
                            if "appendix" in rel.lower() and "programa" in title.lower():
                                full_aux = urllib.parse.urljoin("https://www.dipres.gob.cl/597/", href)
                                req_aux = urllib.request.Request(full_aux, headers=headers)
                                with urllib.request.urlopen(req_aux, timeout=25) as aresp:
                                    aux_data = aresp.read()
                                    if b"format-xls" in aux_data:
                                        raw_data = aux_data
                                        break
                    if raw_data:
                        break
                except Exception:
                    continue

        if not raw_data:
            # Si no se pudo obtener nuevo, usar caché si existe
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    self._html_content = f.read()
                return self._html_content
            raise RuntimeError(f"No se pudo descargar la estructura presupuestaria para el año {self.year} (ID {self.year_id})")

        # Decodificar con UTF-8
        try:
            html_text = raw_data.decode("utf-8")
        except UnicodeDecodeError:
            html_text = raw_data.decode("latin1", errors="replace")

        # Sanear entidades y mojibake
        html_text = self.clean_text(html_text)

        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(html_text)

        self._html_content = html_text
        return self._html_content

    def build_catalog(self, force_refresh=False):
        """
        Parsea el árbol HTML completo y genera un catálogo estructurado de informes.
        Incluye tanto Ejecución Presupuestaria general como Identificación y Ejecución de Inversión.
        """
        html_text = self.fetch_aux_html(force_refresh=force_refresh)
        soup = BeautifulSoup(html_text, "html.parser")
        container = soup.find("div", id="recuadros_articulo_5871")
        if not container:
            container = soup.find("div", id="carga_ejec_programa") or soup

        catalog = []
        # Encontrar todas las Partidas (Ministerios)
        for min_h3 in container.find_all("h3"):
            classes = min_h3.get("class", [])
            if "pv-pid-0" not in classes:
                continue

            ministerio_nom = self.clean_text(min_h3.get_text(strip=True))
            min_div = min_h3.find_next_sibling("div")
            if not min_div:
                continue

            # Buscar servicios / capítulos / programas dentro de este ministerio
            sub_h3s = min_div.find_all("h3")
            for sub_h3 in sub_h3s:
                prog_name = self.clean_text(sub_h3.get_text(strip=True))
                prog_div = sub_h3.find_next_sibling("div")
                if not prog_div:
                    continue

                recuadros = prog_div.find_all("div", class_="recuadro")
                inner_h3 = prog_div.find("h3")
                if inner_h3 and len(prog_div.find_all("div", class_="recuadro", recursive=False)) == 0:
                    continue

                for rec in recuadros:
                    title_elem = rec.find("p", class_="titulo")
                    if not title_elem:
                        continue
                    raw_title = title_elem.get_text(strip=True)
                    title_text = self.clean_text(raw_title)

                    # Filtrar: Ejecución de Programas e Identificación de Inversión
                    is_ejec = "informe ejecuci" in title_text.lower()
                    is_inv = "identificaci" in title_text.lower()
                    if not (is_ejec or is_inv):
                        continue

                    tipo_informe = "Inversión Detallada (BIP)" if is_inv else "Ejecución Presupuestaria"

                    # Extraer periodo y moneda (mapeando trimestres a meses: 1er->Marzo, 2do->Junio, 3er->Septiembre, 4to/Desconocido->Diciembre)
                    title_lower = title_text.lower()
                    periodo = "Desconocido"
                    if "primer trimestre" in title_lower or "1er trimestre" in title_lower or "i trimestre" in title_lower:
                        periodo = "Marzo"
                    elif "segundo trimestre" in title_lower or "2do trimestre" in title_lower or "ii trimestre" in title_lower:
                        periodo = "Junio"
                    elif "tercer trimestre" in title_lower or "tercero trimestre" in title_lower or "3er trimestre" in title_lower or "iii trimestre" in title_lower:
                        periodo = "Septiembre"
                    elif "cuarto trimestre" in title_lower or "4to trimestre" in title_lower or "iv trimestre" in title_lower or "cierre" in title_lower:
                        periodo = "Diciembre"
                    else:
                        for m in config.MESES_ORDEN:
                            if m.lower() in title_lower:
                                periodo = m
                                break
                    if periodo == "Desconocido" and ("anual" in title_lower or "cierre" in title_lower or "cuarto" in title_lower):
                        periodo = "Diciembre"

                    moneda = "Pesos"
                    if "[dólares]" in title_text.lower() or "[dolares]" in title_text.lower():
                        moneda = "Dólares"

                    # Extraer enlaces
                    xls_link = None
                    csv_link = None
                    pdf_link = None
                    xml_link = None

                    div_xls = rec.find("div", class_="format-xls")
                    if div_xls and div_xls.find("a"):
                        xls_link = div_xls.find("a").get("href")

                    div_csv = rec.find("div", class_="format-csv")
                    if div_csv and div_csv.find("a"):
                        csv_link = div_csv.find("a").get("href")

                    div_pdf = rec.find("div", class_="format-pdf")
                    if div_pdf and div_pdf.find("a"):
                        pdf_link = div_pdf.find("a").get("href")

                    div_xml = rec.find("div", class_="format-xml")
                    if div_xml and div_xml.find("a"):
                        xml_link = div_xml.find("a").get("href")

                    aid = ""
                    for c in title_elem.get("class", []):
                        if c.startswith("aid-"):
                            aid = c.replace("aid-", "")

                    if xls_link:
                        xls_full_url = urllib.parse.urljoin(config.DIPRES_BASE_URL, xls_link) if not xls_link.startswith("http") else xls_link
                    else:
                        xls_full_url = None

                    catalog.append({
                        "year": self.year,
                        "ministerio": ministerio_nom,
                        "programa": prog_name,
                        "titulo_informe": title_text,
                        "tipo_informe": tipo_informe,
                        "periodo": periodo,
                        "moneda": moneda,
                        "aid": aid,
                        "url_xls": xls_full_url,
                        "url_csv": urllib.parse.urljoin(config.DIPRES_BASE_URL, csv_link) if csv_link else None,
                        "url_pdf": urllib.parse.urljoin(config.DIPRES_BASE_URL, pdf_link) if pdf_link else None,
                        "rel_xls": xls_link,
                    })

        # Eliminar posibles duplicados exactos conservando orden
        unique_catalog = []
        seen = set()
        for item in catalog:
            key = (item["year"], item["ministerio"], item["programa"], item["titulo_informe"])
            if key not in seen:
                seen.add(key)
                unique_catalog.append(item)

        self.catalog = unique_catalog
        return self.catalog

    def get_ministerios(self):
        """Retorna la lista ordenada de ministerios encontrados."""
        if not self.catalog:
            self.build_catalog()
        ministerios = sorted(list(set(item["ministerio"] for item in self.catalog)))
        return ministerios

    def get_programas(self, ministerio=None):
        """Retorna la lista ordenada de programas para un ministerio dado."""
        if not self.catalog:
            self.build_catalog()
        items = self.catalog
        if ministerio:
            items = [x for x in items if x["ministerio"] == ministerio]
        programas = sorted(list(set(item["programa"] for item in items)))
        return programas

    def get_periodos(self, ministerio=None, programa=None):
        """Retorna la lista de periodos disponibles ordenados cronológicamente."""
        if not self.catalog:
            self.build_catalog()
        items = self.catalog
        if ministerio:
            items = [x for x in items if x["ministerio"] == ministerio]
        if programa:
            items = [x for x in items if x["programa"] == programa]
        periodos_found = set(item["periodo"] for item in items)
        # Ordenar según config.MESES_ORDEN
        ordered = [m for m in config.MESES_ORDEN if m in periodos_found]
        for p in periodos_found:
            if p not in ordered:
                ordered.append(p)
        return ordered

    def filter_catalog(self, ministerio=None, programas=None, periodos=None, monedas=None):
        """
        Filtra el catálogo según los parámetros seleccionados.
        """
        if not self.catalog:
            self.build_catalog()

        filtered = self.catalog
        if ministerio:
            filtered = [x for x in filtered if x["ministerio"] == ministerio]

        if programas:
            if isinstance(programas, str):
                programas = [programas]
            filtered = [x for x in filtered if x["programa"] in programas]

        if periodos:
            if isinstance(periodos, str):
                periodos = [periodos]
            filtered = [x for x in filtered if x["periodo"] in periodos]

        if monedas:
            if isinstance(monedas, str):
                monedas = [monedas]
            filtered = [x for x in filtered if x["moneda"] in monedas]

        return filtered

    @staticmethod
    def clean_filename(name):
        """Limpia caracteres inválidos para nombres de carpeta/archivo en Windows."""
        cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
        cleaned = re.sub(r'\s+', "_", cleaned.strip())
        return cleaned[:80]

    def get_local_path_for_report(self, report_item):
        """Genera la ruta local donde se almacena el archivo Excel."""
        year_str = str(report_item["year"])
        min_dir = self.clean_filename(report_item["ministerio"])
        prog_dir = self.clean_filename(report_item["programa"])

        target_dir = config.DOWNLOADS_DIR / year_str / min_dir / prog_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        periodo_clean = self.clean_filename(report_item["periodo"])
        moneda_clean = self.clean_filename(report_item["moneda"])
        aid = report_item.get("aid", "doc")
        filename = f"ejecucion_{periodo_clean}_{moneda_clean}_{aid}.xls"
        return target_dir / filename

    def is_downloaded(self, report_item):
        """Verifica si el archivo ya existe localmente y es válido (> 1KB)."""
        custom_local = report_item.get("archivo_local")
        if custom_local and Path(custom_local).exists():
            try:
                if Path(custom_local).stat().st_size > 1024:
                    return True
            except OSError:
                pass
        local_path = self.get_local_path_for_report(report_item)
        return local_path.exists() and local_path.stat().st_size > 1024

    def download_report(self, report_item, force=False):
        """
        Descarga un informe Excel específico de DIPRES.
        Retorna la ruta local del archivo o None si falló.
        """
        url = report_item.get("url_xls")
        if not url:
            return None

        local_path = self.get_local_path_for_report(report_item)
        if not force and self.is_downloaded(report_item):
            return local_path

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": config.DIPRES_PORTADILLA_URL.format(year_id=self.year_id)
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=25) as resp:
                    data = resp.read()
                    if len(data) < 500:
                        raise ValueError("Archivo descargado demasiado pequeño o inválido")
                    with open(local_path, "wb") as f:
                        f.write(data)
                return local_path
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Error descargando {url}: {e}")
                    return None
                time.sleep(1)
        return None

    def download_batch(self, reports_list, force=False, progress_callback=None):
        """
        Descarga una lista de informes con reporte de progreso opcional.
        Retorna una tupla (descargados, omitidos, fallidos).
        """
        descargados = []
        omitidos = []
        fallidos = []

        total = len(reports_list)
        for i, item in enumerate(reports_list):
            if not force and self.is_downloaded(item):
                omitidos.append((item, self.get_local_path_for_report(item)))
            else:
                path = self.download_report(item, force=force)
                if path:
                    descargados.append((item, path))
                else:
                    fallidos.append(item)

            if progress_callback:
                progress_callback(i + 1, total, item)

        return descargados, omitidos, fallidos
