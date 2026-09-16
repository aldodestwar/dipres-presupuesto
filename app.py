"""
Dashboard Minimalista de Ejecución Presupuestaria DIPRES · Sector Público de Chile.
Filtros dinámicos adaptados a la información scrapeada.
Paleta de colores de alto contraste: Fondo blanco, texto nítido y barras de colores vibrantes (cero barras negras).
"""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config
from src.dipres_scraper import DipresScraper
from src.excel_parser import DipresExcelParser
from src.db_manager import DatabaseManager

import streamlit.components.v1 as components

# Configuración inicial de la página
st.set_page_config(
    page_title="DIPRES | Ejecución Presupuestaria e Inversión",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Forzar tema claro en el navegador cliente y persistir la pestaña activa seleccionada
components.html("""
<script>
    (function() {
        try {
            const pLoc = window.parent.localStorage;
            const pSes = window.parent.sessionStorage;
            let needsReload = false;
            
            // Revisar si existe configuración oscura en localStorage de Streamlit
            const curV1 = pLoc.getItem("stActiveTheme-/-v1");
            if (curV1 && (curV1.includes("Dark") || curV1.includes("dark"))) {
                pLoc.setItem("stActiveTheme-/-v1", JSON.stringify({ name: "Light" }));
                needsReload = true;
            } else if (!curV1) {
                pLoc.setItem("stActiveTheme-/-v1", JSON.stringify({ name: "Light" }));
            }
            
            if (pLoc.getItem("stActiveTheme") !== "light") {
                pLoc.setItem("stActiveTheme", "light");
            }
            
            window.parent.document.documentElement.setAttribute('data-theme', 'light');
            window.parent.document.body.setAttribute('data-theme', 'light');
            
            if (needsReload) {
                window.parent.location.reload();
            }

            // Persistencia de pestaña activa (evita que Streamlit cambie de pestaña al filtrar o descargar)
            function syncActiveTab() {
                try {
                    const doc = window.parent.document;
                    const tabs = doc.querySelectorAll('button[data-baseweb="tab"]');
                    if (!tabs || tabs.length === 0) return;
                    
                    tabs.forEach((tab, idx) => {
                        if (!tab.dataset.dipresTracked) {
                            tab.dataset.dipresTracked = "true";
                            tab.addEventListener("click", () => {
                                pSes.setItem("dipres_active_tab_label", tab.innerText.trim());
                                pSes.setItem("dipres_active_tab_idx", idx.toString());
                            });
                        }
                    });

                    const savedLabel = pSes.getItem("dipres_active_tab_label");
                    let restored = false;
                    if (savedLabel) {
                        for (let tab of tabs) {
                            if (tab.innerText.trim() === savedLabel) {
                                if (tab.getAttribute("aria-selected") !== "true") {
                                    tab.click();
                                }
                                restored = true;
                                break;
                            }
                        }
                    }

                    if (!restored) {
                        const savedTab = pSes.getItem("dipres_active_tab_idx");
                        if (savedTab !== null && savedTab !== undefined) {
                            const targetIdx = parseInt(savedTab, 10);
                            if (targetIdx >= 0 && targetIdx < tabs.length) {
                                if (tabs[targetIdx].getAttribute("aria-selected") !== "true") {
                                    tabs[targetIdx].click();
                                }
                            }
                        }
                    }
                } catch(e) {}
            }

            syncActiveTab();
            setTimeout(syncActiveTab, 50);
            setTimeout(syncActiveTab, 150);
            setTimeout(syncActiveTab, 350);
            setTimeout(syncActiveTab, 700);
            setTimeout(syncActiveTab, 1200);

            // Manejo de pantalla completa y redibujado de gráficos Plotly
            function triggerPlotlyResize() {
                try {
                    window.parent.dispatchEvent(new Event('resize'));
                    const pWin = window.parent;
                    const doc = pWin.document;
                    if (pWin.Plotly && pWin.Plotly.Plots && pWin.Plotly.Plots.resize) {
                        const plots = doc.querySelectorAll('.js-plotly-plot');
                        plots.forEach(p => {
                            try { pWin.Plotly.Plots.resize(p); } catch(err) {}
                        });
                    }
                } catch(e) {}
            }

            window.parent.document.addEventListener('fullscreenchange', () => {
                setTimeout(triggerPlotlyResize, 40);
                setTimeout(triggerPlotlyResize, 180);
                setTimeout(triggerPlotlyResize, 400);
            });
            window.parent.document.addEventListener('webkitfullscreenchange', () => {
                setTimeout(triggerPlotlyResize, 40);
                setTimeout(triggerPlotlyResize, 180);
                setTimeout(triggerPlotlyResize, 400);
            });

            const obs = new MutationObserver(() => {
                syncActiveTab();
                if (window.parent.document.querySelector('[data-testid="stFullScreenFrame"]')) {
                    triggerPlotlyResize();
                }
            });
            obs.observe(window.parent.document.body, { childList: true, subtree: true });
        } catch(e) {
            console.error("Error setting theme or tab persistence:", e);
        }
    })();
</script>
""", height=0, width=0)

# Estilos CSS de Alta Legibilidad y Contraste:
# Fondo blanco puro (#ffffff), texto negro nítido (#0f172a), y OCULTAR la barra superior de Deploy que tapa contenido.
st.markdown("""
<style>
    /* 1. OCULTAR COMPLETAMENTE LA BARRA SUPERIOR DE DEPLOY Y TOOLBAR (Evita que tape información) */
    header[data-testid="stHeader"],
    [data-testid="stHeader"],
    .stDeployButton,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    #MainMenu,
    footer {
        display: none !important;
        height: 0px !important;
        min-height: 0px !important;
        max-height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }

    /* 2. ESTRUCTURA Y OCUPAR TODO EL ANCHO DISPONIBLE (CERO BARRAS INVISIBLES A LA DERECHA) */
    html, body, [data-testid="stAppViewContainer"], .main, .block-container {
        background-color: #ffffff !important;
        background: #ffffff !important;
        color: #0f172a !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }
    
    .block-container,
    .stMainBlockContainer {
        padding-top: 0.6rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        max-width: 100% !important;
        width: 100% !important;
    }

    [data-testid="stVerticalBlock"],
    .stVerticalBlock,
    [data-testid="stHorizontalBlock"],
    .stHorizontalBlock,
    [data-testid="stTabs"],
    .stTabs,
    .header-box {
        width: 100% !important;
        max-width: 100% !important;
    }

    /* 3. BARRA LATERAL (SIDEBAR): FONDO CLARO (#f8fafc) Y ANCHO EQUILIBRADO */
    [data-testid="stSidebar"], 
    section[data-testid="stSidebar"], 
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarNav"] {
        background-color: #f8fafc !important;
        background: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"] {
        min-width: 295px !important;
        max-width: 305px !important;
        width: 300px !important;
    }
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label {
        color: #0f172a !important;
    }
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] .stCaption p {
        color: #64748b !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #e2e8f0 !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }
    [data-testid="stSidebarCollapsedControl"] svg {
        fill: #0f172a !important;
    }

    /* 4. SELECTBOXES: FONDO BLANCO, BORDE SUAVE Y TEXTO NEGRO (Cero cajas o píldoras negras) */
    div[data-baseweb="select"],
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        background: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #0f172a !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    }
    div[data-baseweb="select"] * {
        color: #0f172a !important;
    }
    div[data-baseweb="select"] svg {
        fill: #475569 !important;
    }
    /* Menú emergente de selección (popover) */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    ul[data-baseweb="menu"],
    li[data-baseweb="menu-item"] {
        background-color: #ffffff !important;
        background: #ffffff !important;
        color: #0f172a !important;
    }
    li[data-baseweb="menu-item"]:hover {
        background-color: #f1f5f9 !important;
        color: #2563eb !important;
    }
    li[data-baseweb="menu-item"][aria-selected="true"] {
        background-color: #eff6ff !important;
        color: #1d4ed8 !important;
        font-weight: 600 !important;
    }

    /* 5. MULTISELECT: CHIPS CON FONDO CLARO Y TEXTO LEGIBLE */
    span[data-baseweb="tag"] {
        background-color: #f1f5f9 !important;
        background: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
        margin: 2px !important;
    }
    span[data-baseweb="tag"] span {
        color: #0f172a !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
    }
    span[data-baseweb="tag"] svg {
        fill: #64748b !important;
    }
    span[data-baseweb="tag"]:hover svg {
        fill: #dc2626 !important;
    }

    /* 6. BOTONES: FONDO BLANCO/GRIS SUAVE, TEXTO OSCURO (Cero botones negros) */
    .stButton > button,
    button[data-testid="baseButton-secondary"] {
        background-color: #ffffff !important;
        background: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.15s ease-in-out !important;
    }
    .stButton > button:hover,
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #f8fafc !important;
        border-color: #94a3b8 !important;
        color: #2563eb !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08) !important;
    }
    button[data-testid="baseButton-primary"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: 1px solid #1d4ed8 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    button[data-testid="baseButton-primary"]:hover {
        background-color: #1d4ed8 !important;
    }

    /* 7. RADIOS: TEXTO NEGRO NÍTIDO Y CÍRCULOS CLAROS (Cero texto invisible) */
    div[role="radiogroup"] label,
    div[role="radiogroup"] *,
    div[role="radiogroup"] span,
    div[role="radiogroup"] p {
        color: #0f172a !important;
    }
    div[role="radiogroup"] div[data-testid="stMarkdownContainer"] p {
        color: #0f172a !important;
        font-weight: 500 !important;
    }
    div[role="radiogroup"] div[data-baseweb="radio"] > div:first-child {
        background-color: #ffffff !important;
        border: 2px solid #94a3b8 !important;
    }

    /* 8. INPUTS DE BÚSQUEDA Y TEXTO */
    div[data-baseweb="input"],
    div[data-baseweb="input"] > div,
    input[data-testid="stTextInputRootElement"],
    div[data-testid="stTextInputRootElement"] input {
        background-color: #ffffff !important;
        background: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"] input {
        color: #0f172a !important;
    }
    div[data-baseweb="input"] input::placeholder {
        color: #94a3b8 !important;
    }

    /* 9. CHECKBOXES */
    label[data-baseweb="checkbox"] span {
        color: #0f172a !important;
    }
    div[data-baseweb="checkbox"] > div {
        border-color: #94a3b8 !important;
        background-color: #ffffff !important;
    }

    /* 10. ENCABEZADO PRINCIPAL DE LA PÁGINA */
    .header-box {
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.6rem;
        margin-bottom: 0.9rem;
        background-color: #ffffff;
        width: 100% !important;
        max-width: 100% !important;
    }
    .header-title-text {
        font-size: 1.35rem;
        font-weight: 800;
        color: #0f172a !important;
        margin: 0;
        line-height: 1.2;
    }
    .header-sub-text {
        font-size: 0.80rem;
        color: #475569 !important;
        margin-top: 3px;
    }

    /* 11. PÍLDORAS Y BADGES INFORMATIVOS */
    .year-pill-hero {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);
        color: #ffffff !important;
        padding: 3px 12px;
        border-radius: 9999px;
        font-size: 0.84rem;
        font-weight: 800;
        letter-spacing: 0.02em;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
        border: 1px solid #1e40af;
        white-space: nowrap;
        vertical-align: middle;
    }
    .year-pill-hero .year-icon {
        margin-right: 5px;
        font-size: 0.90rem;
    }
    .year-pill-sidebar {
        display: inline-flex;
        align-items: center;
        background: #eff6ff;
        color: #1d4ed8 !important;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1.5px solid #93c5fd;
        box-shadow: 0 1px 3px rgba(37, 99, 235, 0.10);
        margin-top: 3px;
        margin-bottom: 6px;
    }
    .pill-badge {
        display: inline-block;
        padding: 2.5px 9px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 600;
        background-color: #f8fafc;
        color: #334155 !important;
        border: 1px solid #cbd5e1;
        margin-left: 4px;
    }

    /* 12. TARJETAS DE MÉTRICAS EJECUTIVAS */
    .executive-kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 9px 12px 8px 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 98px;
        margin-bottom: 6px;
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    }
    .executive-kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.07);
        border-color: #cbd5e1;
    }
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }

    /* 13. PESTAÑAS (TABS) */
    div[data-baseweb="tab-list"] {
        border-bottom: 2px solid #e2e8f0 !important;
        background-color: transparent !important;
        width: 100% !important;
    }
    button[data-baseweb="tab"] {
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        padding: 5px 11px !important;
        background-color: transparent !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #2563eb !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #2563eb !important;
        border-bottom: 2px solid #2563eb !important;
    }

    /* 14. TABLAS Y DATAFRAMES */
    [data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        background-color: #ffffff !important;
        color-scheme: light !important;
    }
    [data-testid="stDataFrame"] > div {
        background-color: #ffffff !important;
        color-scheme: light !important;
    }

    /* 14.1 ALTURA DE CONTENEDORES PLOTLY (Evita que colapsen a 0px en vista estándar) */
    div[data-testid="stPlotlyChart"],
    .stPlotlyChart {
        min-height: 410px !important;
        width: 100% !important;
    }

    /* 15. OPTIMIZACIÓN DE PANTALLA COMPLETA EN GRÁFICOS (OCUPAR 100% DEL ESPACIO SIN BARRAS DESAPROVECHADAS) */
    :fullscreen,
    :-webkit-full-screen,
    :fullscreen [data-testid="stFullScreenFrame"],
    :-webkit-full-screen [data-testid="stFullScreenFrame"],
    [data-testid="stFullScreenFrame"]:fullscreen,
    [data-testid="stFullScreenFrame"]:-webkit-full-screen {
        background-color: #ffffff !important;
        background: #ffffff !important;
        width: 100vw !important;
        height: 100vh !important;
        max-width: 100vw !important;
        max-height: 100vh !important;
        padding: 1.5rem !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        z-index: 999999 !important;
    }

    :fullscreen div[data-testid="stPlotlyChart"],
    :fullscreen .stPlotlyChart,
    :fullscreen .plotly,
    :fullscreen .js-plotly-plot,
    :fullscreen .plot-container,
    :-webkit-full-screen div[data-testid="stPlotlyChart"],
    :-webkit-full-screen .stPlotlyChart,
    :-webkit-full-screen .plotly,
    :-webkit-full-screen .js-plotly-plot,
    :-webkit-full-screen .plot-container {
        width: 100% !important;
        height: 88vh !important;
        min-height: 82vh !important;
        max-height: 92vh !important;
    }

    :fullscreen .svg-container,
    :fullscreen svg.main-svg,
    :-webkit-full-screen .svg-container,
    :-webkit-full-screen svg.main-svg {
        width: 100% !important;
        height: 100% !important;
        max-height: 88vh !important;
    }
</style>
""", unsafe_allow_html=True)

def get_db():
    """Instancia del gestor de base de datos."""
    return DatabaseManager()

@st.cache_resource
def get_scraper(year):
    """Instancia en caché del Scraper para el año seleccionado."""
    scraper = DipresScraper(year=year)
    scraper.build_catalog()
    return scraper

def format_currency(val):
    """Formatea valores en miles de pesos a notación chilena clara ($ MM / $ B)."""
    if pd.isna(val) or val is None or val == 0:
        return "$0"
    pesos = float(val) * 1000
    if abs(pesos) >= 1e12:
        return f"${pesos / 1e12:.2f} B"
    elif abs(pesos) >= 1e9:
        return f"${pesos / 1e9:.1f} MM"
    elif abs(pesos) >= 1e6:
        return f"${pesos / 1e6:.1f} M"
    else:
        return f"${pesos:,.0f}"

def format_prog_label(name, max_len=24, **kwargs):
    """Acorta nombres de programas para que las etiquetas del eje X sean nítidas y no se superpongan."""
    if not name:
        return ""
    length = kwargs.get("max_line", max_len)
    s = str(name).strip()
    if len(s) <= length:
        return s
    return s[:length-3] + "..."

def get_kpis_safe(db_inst, year, ministerio, programas, periodo, moneda):
    """Obtiene los KPIs garantizando cero fallos y valores por defecto numéricos."""
    try:
        raw = db_inst.get_kpis(
            year=year,
            ministerio=ministerio,
            programas=programas,
            periodo=periodo,
            moneda=moneda
        )
    except Exception:
        raw = {}
        
    return {
        "presupuesto_inicial": raw.get("presupuesto_inicial", 0.0) or 0.0,
        "presupuesto_vigente": raw.get("presupuesto_vigente", 0.0) or 0.0,
        "ejecucion_acumulada": raw.get("ejecucion_acumulada", 0.0) or 0.0,
        "saldo": raw.get("saldo", 0.0) or 0.0,
        "pct_ejecucion": raw.get("pct_ejecucion", 0.0) or 0.0,
        "capital_vigente": raw.get("capital_vigente", raw.get("inversion_vigente", 0.0)) or 0.0,
        "capital_ejecucion": raw.get("capital_ejecucion", raw.get("inversion_ejecucion", 0.0)) or 0.0,
        "pct_capital": raw.get("pct_capital", raw.get("pct_inversion", 0.0)) or 0.0,
        "subt31_vigente": raw.get("subt31_vigente", 0.0) or 0.0,
        "subt31_ejecucion": raw.get("subt31_ejecucion", 0.0) or 0.0,
        "pct_subt31": raw.get("pct_subt31", 0.0) or 0.0,
        "subt29_vigente": raw.get("subt29_vigente", 0.0) or 0.0,
        "subt29_ejecucion": raw.get("subt29_ejecucion", 0.0) or 0.0,
        "pct_subt29": raw.get("pct_subt29", 0.0) or 0.0,
        "subt33_vigente": raw.get("subt33_vigente", 0.0) or 0.0,
        "subt33_ejecucion": raw.get("subt33_ejecucion", 0.0) or 0.0,
        "pct_subt33": raw.get("pct_subt33", 0.0) or 0.0
    }

def render_kpi_card_html(title, value, subtitle, icon="📊", theme="blue", progress=None, badge=None):
    """Genera una tarjeta KPI moderna, ejecutiva y elegante con HTML/CSS puro."""
    palette = {
        "blue": {
            "border_top": "#2563eb",
            "icon_bg": "#eff6ff",
            "icon_color": "#1d4ed8",
            "bar_fill": "linear-gradient(90deg, #3b82f6, #2563eb)",
            "pill_bg": "#eff6ff",
            "pill_text": "#1e40af",
            "pill_border": "#dbeafe"
        },
        "green": {
            "border_top": "#10b981",
            "icon_bg": "#ecfdf5",
            "icon_color": "#047857",
            "bar_fill": "linear-gradient(90deg, #34d399, #059669)",
            "pill_bg": "#ecfdf5",
            "pill_text": "#065f46",
            "pill_border": "#a7f3d0"
        },
        "indigo": {
            "border_top": "#6366f1",
            "icon_bg": "#eef2ff",
            "icon_color": "#4338ca",
            "bar_fill": "linear-gradient(90deg, #818cf8, #4f46e5)",
            "pill_bg": "#eef2ff",
            "pill_text": "#3730a3",
            "pill_border": "#c7d2fe"
        },
        "amber": {
            "border_top": "#f59e0b",
            "icon_bg": "#fffbeb",
            "icon_color": "#b45309",
            "bar_fill": "linear-gradient(90deg, #fbbf24, #d97706)",
            "pill_bg": "#fffbeb",
            "pill_text": "#92400e",
            "pill_border": "#fde68a"
        },
        "purple": {
            "border_top": "#8b5cf6",
            "icon_bg": "#f5f3ff",
            "icon_color": "#6d28d9",
            "bar_fill": "linear-gradient(90deg, #a78bfa, #7c3aed)",
            "pill_bg": "#f5f3ff",
            "pill_text": "#5b21b6",
            "pill_border": "#ddd6fe"
        }
    }
    c = palette.get(theme, palette["blue"])
    
    progress_html = ""
    if progress is not None:
        pct = max(0.0, min(100.0, float(progress)))
        progress_html = (
            f'<div style="margin: 6px 0 5px 0;">'
            f'<div style="background-color: #f1f5f9; border-radius: 9999px; height: 5px; width: 100%; overflow: hidden;">'
            f'<div style="background: {c["bar_fill"]}; width: {pct}%; height: 100%; border-radius: 9999px;"></div>'
            f'</div>'
            f'</div>'
        )

    badge_html = (
        f'<span style="background-color: {c["pill_bg"]}; color: {c["pill_text"]}; border: 1px solid {c["pill_border"]}; '
        f'font-size: 0.60rem; font-weight: 700; padding: 1.5px 6px; border-radius: 9999px; white-space: nowrap; flex-shrink: 0;">{badge}</span>'
    ) if badge else ""

    return (
        f'<div class="executive-kpi-card" style="border-top: 3.5px solid {c["border_top"]} !important;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; gap: 4px; margin-bottom: 2px;">'
        f'<div style="display: flex; align-items: center; gap: 5px; min-width: 0;">'
        f'<span style="background: {c["icon_bg"]}; color: {c["icon_color"]}; width: 18px; height: 18px; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center; font-size: 0.75rem; flex-shrink: 0;">{icon}</span>'
        f'<span style="font-size: 0.60rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.015em; color: #475569; white-space: nowrap;">{title}</span>'
        f'</div>'
        f'{badge_html}'
        f'</div>'
        f'<div>'
        f'<div style="font-size: 1.35rem; font-weight: 800; color: #0f172a; line-height: 1.15; letter-spacing: -0.02em; margin: 3px 0 2px 0;">{value}</div>'
        f'{progress_html}'
        f'</div>'
        f'<div style="font-size: 0.68rem; color: #475569; font-weight: 500; display: flex; align-items: center; gap: 5px; margin-top: 2px;">'
        f'<span style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 5px; padding: 1.5px 6px; color: #334155; font-weight: 600; font-size: 0.66rem;">{subtitle}</span>'
        f'</div>'
        f'</div>'
    )

db = get_db()

def render_national_tops_view(
    year,
    moneda,
    periodo,
    view_focus="📅 Análisis Anual / Mensual",
    multi_years=None,
    estrato="Todos los Tamaños",
    rango_avance="Cualquier Avance",
    scope="Presupuesto Total (Todos los Subtítulos)",
    sort_by="Presupuesto Vigente (Mayor a menor)",
    top_n=10,
    exclude_tesoro=True,
    filter_mins=None
):
    """Renderiza la ventana ejecutiva de Rankings & Tops Presupuestarios Nacionales con análisis macro, sectorial, multianual y mensual."""
    if not multi_years:
        multi_years = [2022, 2023, 2024, 2025, 2026]

    is_multianual = (view_focus == "📈 Comparativa Multianual (2018-2026)")

    # 1. Header Box
    title_sub = f"Comparativa Multianual ({min(multi_years)} - {max(multi_years)})" if is_multianual else f"Consolidado Nacional {year}"
    st.markdown(f"""
    <div class="header-box">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
            <div>
                <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap; margin-bottom: 5px;">
                    <span class="header-title-text">🏆 Rankings & Tops Presupuestarios del Estado</span>
                    <span class="year-pill-hero">
                        <span class="year-icon">🇨🇱</span> {title_sub}
                    </span>
                </div>
                <div class="header-sub-text">Corte: <b>{periodo}</b> · Moneda: <b>{moneda}</b> · Alcance: <b>{scope}</b> · Estrato: <b>{estrato}</b></div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                <span class="pill-badge" style="background-color: #eff6ff; border-color: #93c5fd; color: #1d4ed8 !important;">📊 Cobertura Nacional</span>
                <span class="pill-badge" style="background-color: #ecfdf5; border-color: #a7f3d0; color: #047857 !important;">{'🛡️ Sin Tesoro Público' if exclude_tesoro else '🏛️ Incluye Tesoro Público'}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Carga y Filtrado de Datos Base
    df_mins_raw = db.get_national_ministerios_ranking(
        year=year,
        periodo=periodo,
        moneda=moneda,
        exclude_tesoro=exclude_tesoro,
        ministerios=filter_mins if filter_mins else None
    )

    if df_mins_raw.empty:
        st.warning(f"⚠️ No se encontraron datos consolidados en la Base de Datos para el año **{year}** y corte **{periodo}**.")
        st.info("💡 Puedes descargar masivamente los informes de todos los ministerios desde la pestaña **'🌐 Catálogo & Scraper DIPRES'**.")
        return

    # Aplicar Filtro de Estrato Presupuestario
    df_mins_filtered = df_mins_raw.copy()
    if "Grandes" in estrato:
        df_mins_filtered = df_mins_filtered[df_mins_filtered["vigente"] * 1000 / 1e9 >= 5000]
    elif "Medianas" in estrato:
        df_mins_filtered = df_mins_filtered[(df_mins_filtered["vigente"] * 1000 / 1e9 >= 1000) & (df_mins_filtered["vigente"] * 1000 / 1e9 < 5000)]
    elif "Focalizadas" in estrato:
        df_mins_filtered = df_mins_filtered[df_mins_filtered["vigente"] * 1000 / 1e9 < 1000]

    # Aplicar Filtro de Rango de Avance
    if "Alto" in rango_avance:
        df_mins_filtered = df_mins_filtered[df_mins_filtered["pct_ejecucion"] > 50]
    elif "Regular" in rango_avance:
        df_mins_filtered = df_mins_filtered[(df_mins_filtered["pct_ejecucion"] >= 35) & (df_mins_filtered["pct_ejecucion"] <= 50)]
    elif "Rezagados" in rango_avance:
        df_mins_filtered = df_mins_filtered[df_mins_filtered["pct_ejecucion"] < 35]

    if df_mins_filtered.empty:
        st.warning("⚠️ No hay ministerios que coincidan con la combinación de filtros seleccionados (Estrato / Rango de Avance).")
        st.info("💡 Intenta relajar los filtros en la barra lateral para visualizar resultados.")
        return

    # Helper para nombres cortos de ministerios
    def clean_min_name(m):
        return (str(m).replace("Ministerio de las Culturas, las Artes y el Patrimonio", "Culturas")
                      .replace("Ministerio del Trabajo y Previsión Social", "Trabajo")
                      .replace("Ministerio de Transportes y Telecomunicaciones", "Transportes")
                      .replace("Ministerio de Vivienda y Urbanismo", "Vivienda (MINVU)")
                      .replace("Ministerio de Obras Públicas", "Obras Públicas (MOP)")
                      .replace("Ministerio del Medio Ambiente", "Medio Ambiente")
                      .replace("Ministerio de Desarrollo Social y Familia", "Desarrollo Social")
                      .replace("Ministerio de Secretaría General de la Presidencia", "SEGPRES")
                      .replace("Ministerio de Secretaría General de Gobierno", "SEGEGOB")
                      .replace("Ministerio de Economía, Fomento y Turismo", "Economía")
                      .replace("Ministerio de Ciencia, Tecnología, Conocimiento e Innovación", "Ciencia")
                      .replace("Ministerio de ", "").replace("Ministerio del ", "").replace("Ministerio ", ""))

    # 3. Macro KPIs
    total_inicial = df_mins_filtered["inicial"].sum()
    total_vigente = df_mins_filtered["vigente"].sum()
    total_ejec = df_mins_filtered["ejecucion"].sum()
    total_saldo = df_mins_filtered["saldo"].sum()
    pct_global = (total_ejec / total_vigente * 100) if total_vigente > 0 else 0.0

    total_subt31_vig = df_mins_filtered["subt31_vigente"].sum()
    total_subt31_ejec = df_mins_filtered["subt31_ejecucion"].sum()
    pct_subt31_global = (total_subt31_ejec / total_subt31_vig * 100) if total_subt31_vig > 0 else 0.0
    share_inv = (total_subt31_vig / total_vigente * 100) if total_vigente > 0 else 0.0

    threshold = total_vigente * 0.005
    df_sig = df_mins_filtered[df_mins_filtered["vigente"] >= threshold]
    top_performer = df_sig.sort_values(by="pct_ejecucion", ascending=False).iloc[0] if not df_sig.empty else df_mins_filtered.sort_values(by="pct_ejecucion", ascending=False).iloc[0]

    col1, col2, col3, col4 = st.columns(4, gap="small")
    with col1:
        st.markdown(render_kpi_card_html(
            title="Presupuesto Vigente Analizado",
            value=format_currency(total_vigente),
            subtitle=f"Ley Inicial: {format_currency(total_inicial)}",
            icon="🏛️",
            theme="blue",
            badge=f"{len(df_mins_filtered)} carteras"
        ), unsafe_allow_html=True)
    with col2:
        st.markdown(render_kpi_card_html(
            title="Ejecución Devengada Total",
            value=format_currency(total_ejec),
            subtitle=f"Saldo: {format_currency(total_saldo)}",
            icon="⚡",
            theme="green",
            progress=pct_global,
            badge=f"{pct_global:.1f}% devengado"
        ), unsafe_allow_html=True)
    with col3:
        st.markdown(render_kpi_card_html(
            title="Inversión Real (Subt. 31)",
            value=format_currency(total_subt31_vig),
            subtitle=f"Devengado: {format_currency(total_subt31_ejec)}",
            icon="🏗️",
            theme="amber",
            progress=pct_subt31_global,
            badge=f"{share_inv:.1f}% del presupuesto"
        ), unsafe_allow_html=True)
    with col4:
        st.markdown(render_kpi_card_html(
            title="Líder en Avance Presupuestario",
            value=f"{top_performer['pct_ejecucion']:.1f}%",
            subtitle=format_prog_label(clean_min_name(top_performer['ministerio']), 26),
            icon="🥇",
            theme="purple",
            progress=top_performer['pct_ejecucion'],
            badge="Top Desempeño"
        ), unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Conclusiones Rápidas
    top3_mins = df_mins_filtered.sort_values(by="vigente", ascending=False).head(3)
    top3_share = (top3_mins["vigente"].sum() / total_vigente * 100) if total_vigente > 0 else 0
    top3_names = ", ".join([clean_min_name(m) for m in top3_mins["ministerio"]])
    
    lead_inv = df_mins_filtered.sort_values(by="subt31_vigente", ascending=False).iloc[0]
    lead_inv_share = (lead_inv["subt31_vigente"] / total_subt31_vig * 100) if total_subt31_vig > 0 else 0
    lead_inv_name = clean_min_name(lead_inv["ministerio"])

    st.markdown(f"""
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #2563eb; border-radius: 8px; padding: 10px 14px; margin-bottom: 14px; font-size: 0.82rem; color: #334155;">
        <b>💡 Hallazgos y Conclusiones Clave del Análisis:</b>
        <ul style="margin: 4px 0 0 16px; padding: 0;">
            <li><b>Concentración Presupuestaria:</b> Los 3 mayores ministerios del corte (<b>{top3_names}</b>) concentran el <b>{top3_share:.1f}%</b> del total analizado.</li>
            <li><b>Liderazgo en Obras e Inversión:</b> El <b>{lead_inv_share:.1f}%</b> de la inversión real directa (Subt. 31) corresponde a <b>{lead_inv_name}</b> ({format_currency(lead_inv['subt31_vigente'])}).</li>
            <li><b>Promedio Ponderado de Ejecución:</b> La tasa media de avance devengado es de <b>{pct_global:.1f}%</b> en este corte temporal.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # ==============================================================================
    # 4. CUADRANTE ESTRATÉGICO CON FILTROS Y CONTROLES AVANZADOS
    # ==============================================================================
    st.markdown("##### 🎯 Cuadrante Estratégico: Presupuesto Vigente vs. % Avance de Ejecución")
    st.caption("Eje X: Presupuesto Vigente ($ Miles de Millones) · Eje Y: % Ejecución Devengada · Tamaño de burbuja: Inversión Real (Subt. 31).")

    # BARRA DE HERRAMIENTAS Y FILTROS DEDICADA DEL CUADRANTE
    with st.expander("🛠️ Filtros y Opciones del Cuadrante Estratégico (Escala, Métricas y Cuadrantes)", expanded=True):
        cq1, cq2, cq3, cq4 = st.columns([2.5, 2.5, 2.5, 2.5])
        with cq1:
            quad_scale_x = st.selectbox(
                "Escala Eje X",
                options=["Logarítmica (Descomprime Cúmulos)", "Lineal"],
                index=0,
                key="quad_scale_x",
                help="La escala logarítmica expande el origen permitiendo ver y diferenciar claramente todas las carteras medianas y pequeñas sin amontonamientos."
            )
        with cq2:
            quad_metric_x = st.selectbox(
                "Métrica Eje X",
                options=[
                    "Presupuesto Vigente ($ MM)",
                    "Presupuesto Inicial ($ MM)",
                    "Saldo Disponible ($ MM)",
                    "Ejecución Devengada ($ MM)"
                ],
                index=0,
                key="quad_metric_x"
            )
        with cq3:
            quad_metric_y = st.selectbox(
                "Métrica Eje Y",
                options=[
                    "% Avance Presupuestario Total",
                    "% Avance Inversión Real (Subt. 31)",
                    "% Avance Capital (29+31+33)",
                    "% Inversión en Presupuesto Total"
                ],
                index=0,
                key="quad_metric_y"
            )
        with cq4:
            quad_bubble_size = st.selectbox(
                "Tamaño de Burbuja",
                options=[
                    "Inversión Real Subt. 31 ($ MM)",
                    "Presupuesto Vigente ($ MM)",
                    "Gasto Personal Subt. 21 ($ MM)",
                    "Saldo Pendiente ($ MM)",
                    "Gasto Capital Total (29+31+33) ($ MM)"
                ],
                index=0,
                key="quad_bubble_size"
            )

        cq_f1, cq_f2 = st.columns([5.5, 4.5])
        with cq_f1:
            quad_filter = st.selectbox(
                "Filtrar por Cuadrante Específico",
                options=[
                    "Mostrar Todos los Cuadrantes",
                    "🟢 Motores (Alto Presupuesto / Alto Avance)",
                    "🟣 Ágiles (Presupuesto Focalizado / Alto Avance)",
                    "🟡 Alerta de Capacidad (Alto Presupuesto / Bajo Avance)",
                    "⚪ Rezagados (Presupuesto Focalizado / Bajo Avance)"
                ],
                index=0,
                key="quad_filter"
            )
        with cq_f2:
            quad_labels_mode = st.selectbox(
                "Etiquetas de Texto en el Gráfico",
                options=[
                    "Destacados (Automático sin solapes)",
                    "Mostrar Todos los Ministerios",
                    "Solo al Pasar el Mouse (Hover Limpio)"
                ],
                index=0,
                key="quad_labels_mode"
            )

    df_bubble = df_mins_filtered.copy()
    df_bubble["min_short"] = df_bubble["ministerio"].apply(clean_min_name)
    df_bubble["vigente_mm"] = df_bubble["vigente"] * 1000 / 1e9
    df_bubble["inicial_mm"] = df_bubble["inicial"] * 1000 / 1e9
    df_bubble["ejecucion_mm"] = df_bubble["ejecucion"] * 1000 / 1e9
    df_bubble["saldo_mm"] = df_bubble["saldo"] * 1000 / 1e9
    df_bubble["subt31_mm"] = df_bubble["subt31_vigente"] * 1000 / 1e9
    df_bubble["subt21_mm"] = df_bubble["subt21_vigente"] * 1000 / 1e9
    df_bubble["capital_mm"] = df_bubble["capital_vigente"] * 1000 / 1e9

    # Resolver columna X
    if quad_metric_x == "Presupuesto Inicial ($ MM)":
        col_x = "inicial_mm"
        label_x = "Presupuesto Inicial ($ Miles de Millones - MM)"
    elif quad_metric_x == "Saldo Disponible ($ MM)":
        col_x = "saldo_mm"
        label_x = "Saldo Disponible ($ Miles de Millones - MM)"
    elif quad_metric_x == "Ejecución Devengada ($ MM)":
        col_x = "ejecucion_mm"
        label_x = "Ejecución Devengada ($ Miles de Millones - MM)"
    else:
        col_x = "vigente_mm"
        label_x = "Presupuesto Vigente ($ Miles de Millones - MM)"

    # Resolver columna Y
    if quad_metric_y == "% Avance Inversión Real (Subt. 31)":
        col_y = "pct_subt31"
        label_y = "% Avance Inversión Real (Subt. 31)"
    elif quad_metric_y == "% Avance Capital (29+31+33)":
        col_y = "pct_capital"
        label_y = "% Avance Gastos de Capital (29+31+33)"
    elif quad_metric_y == "% Inversión en Presupuesto Total":
        col_y = "pct_share_inv"
        label_y = "% Inversión Subt. 31 / Vigente Total"
    else:
        col_y = "pct_ejecucion"
        label_y = "% Avance Presupuestario Total"

    # Resolver tamaño de burbuja
    if quad_bubble_size == "Presupuesto Vigente ($ MM)":
        col_size_raw = "vigente_mm"
        label_size = "Presupuesto Vigente ($ MM)"
    elif quad_bubble_size == "Gasto Personal Subt. 21 ($ MM)":
        col_size_raw = "subt21_mm"
        label_size = "Personal Subt. 21 ($ MM)"
    elif quad_bubble_size == "Saldo Pendiente ($ MM)":
        col_size_raw = "saldo_mm"
        label_size = "Saldo por Gastar ($ MM)"
    elif quad_bubble_size == "Gasto Capital Total (29+31+33) ($ MM)":
        col_size_raw = "capital_mm"
        label_size = "Capital (29+31+33) ($ MM)"
    else:
        col_size_raw = "subt31_mm"
        label_size = "Inversión Subt. 31 ($ MM)"

    df_bubble["size_scaled"] = df_bubble[col_size_raw].apply(lambda v: max(11, min(48, (max(float(v), 0) ** 0.5) * 1.8 + 11)))

    # Líneas divisorias de Cuadrantes
    mediana_x = float(df_bubble[col_x].median()) if not df_bubble.empty else 1.0
    media_y = float(df_bubble[col_y].mean()) if not df_bubble.empty else 50.0

    def assign_cuadrante(r):
        high_x = r[col_x] >= mediana_x
        high_y = r[col_y] >= media_y
        if high_x and high_y:
            return "🟢 Motores (Alto Presupuesto / Alto Avance)"
        elif not high_x and high_y:
            return "🟣 Ágiles (Presupuesto Focalizado / Alto Avance)"
        elif high_x and not high_y:
            return "🟡 Alerta de Capacidad (Alto Presupuesto / Bajo Avance)"
        else:
            return "⚪ Rezagados (Presupuesto Focalizado / Bajo Avance)"

    df_bubble["cuadrante_cat"] = df_bubble.apply(assign_cuadrante, axis=1)

    # Filtrar por cuadrante si se seleccionó uno
    if quad_filter != "Mostrar Todos los Cuadrantes":
        df_bubble = df_bubble[df_bubble["cuadrante_cat"] == quad_filter]

    if df_bubble.empty:
        st.info(f"No hay ministerios en el cuadrante seleccionado: **{quad_filter}**.")
    else:
        # Modo de etiquetas
        if quad_labels_mode == "Destacados (Automático sin solapes)":
            top_x_mins = df_bubble.nlargest(6, col_x)["ministerio"].tolist()
            top_y_mins = df_bubble.nlargest(4, col_y)["ministerio"].tolist()
            featured_mins = set(top_x_mins + top_y_mins)
            df_bubble["text_label"] = df_bubble.apply(lambda r: r["min_short"] if r["ministerio"] in featured_mins else "", axis=1)
        elif quad_labels_mode == "Mostrar Todos los Ministerios":
            df_bubble["text_label"] = df_bubble["min_short"]
        else:
            df_bubble["text_label"] = ""

        # Manejo de escala logarítmica
        is_log_x = quad_scale_x.startswith("Logarítmica")
        if is_log_x:
            df_bubble["plot_x"] = df_bubble[col_x].apply(lambda v: max(float(v), 0.1))
        else:
            df_bubble["plot_x"] = df_bubble[col_x]

        fig_quad = px.scatter(
            df_bubble,
            x="plot_x",
            y=col_y,
            size="size_scaled",
            color=col_y,
            text="text_label",
            color_continuous_scale="Tealgrn",
            hover_name="ministerio",
            hover_data={
                "text_label": False,
                "min_short": False,
                "size_scaled": False,
                "plot_x": False,
                col_x: ":,.1f",
                col_y: ":.1f",
                "subt31_mm": ":,.1f",
                "saldo_mm": ":,.1f",
                "cuadrante_cat": True
            },
            labels={
                "plot_x": label_x,
                col_y: label_y,
                "subt31_mm": "Inversión Subt. 31 ($ MM)",
                "saldo_mm": "Saldo ($ MM)",
                "cuadrante_cat": "Cuadrante"
            }
        )
        fig_quad.update_traces(
            textposition="top center",
            textfont=dict(size=10.5, color="#0f172a", family="sans-serif"),
            marker=dict(line=dict(width=1.5, color="#0f172a"), opacity=0.88)
        )
        fig_quad.add_hline(
            y=media_y,
            line_dash="dot",
            line_color="#ef4444",
            annotation_text=f"Promedio Eje Y: {media_y:.1f}%",
            annotation_position="bottom right",
            annotation_font_size=10,
            annotation_font_color="#b91c1c"
        )
        fig_quad.add_vline(
            x=max(mediana_x, 0.1) if is_log_x else mediana_x,
            line_dash="dot",
            line_color="#64748b",
            annotation_text=f"Mediana Eje X: ${mediana_x:,.1f} MM",
            annotation_position="top left",
            annotation_font_size=10,
            annotation_font_color="#475569"
        )

        quad_layout = dict(
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            height=450,
            autosize=True,
            hovermode="closest",
            hoverdistance=60,
            margin=dict(l=45, r=45, t=35, b=45),
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9", linecolor="#cbd5e1", title=label_x),
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9", linecolor="#cbd5e1", ticksuffix="%", title=label_y),
            coloraxis_colorbar=dict(title="% Avance", thickness=14, len=0.75, ticksuffix="%")
        )
        if is_log_x:
            quad_layout["xaxis"]["type"] = "log"
            quad_layout["xaxis"]["tickformat"] = ",.0f"
        else:
            quad_layout["xaxis"]["tickformat"] = ",.0f"

        fig_quad.update_layout(**quad_layout)
        st.plotly_chart(fig_quad, use_container_width=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # ==============================================================================
    # 5. DOS NUEVOS GRÁFICOS ESTRATÉGICOS (MULTIANUAL & MENSUAL)
    # ==============================================================================
    st.markdown("---")
    st.markdown("#### 🚀 Análisis Estratégico Avanzado: Dinámica Multianual y Velocidad Mensual")
    st.caption("Nuevas visualizaciones para comparar la trayectoria histórica de las carteras y monitorear el ritmo continuo de devengo mes a mes.")

    # GRÁFICO EXTRA 1: EVOLUCIÓN HISTÓRICA MULTIANUAL (2018-2026)
    st.markdown("##### 📈 Gráfico Extra 1: Evolución Histórica Multianual por Ministerio (2018–2026)")
    st.caption("Compara la trayectoria y el crecimiento interanual de los ministerios a lo largo de los distintos ejercicios presupuestarios.")

    c_g1_opt1, c_g1_opt2, c_g1_opt3 = st.columns([3.5, 3.5, 3])
    with c_g1_opt1:
        g1_metric = st.selectbox(
            "Métrica a Comparar por Año",
            options=[
                "Presupuesto Vigente ($ MM)",
                "Ejecución Devengada ($ MM)",
                "% Avance Presupuestario",
                "Inversión Subt. 31 ($ MM)"
            ],
            index=0,
            key="g1_metric"
        )
    with c_g1_opt2:
        g1_years = st.multiselect(
            "Años en el Gráfico",
            options=db.get_loaded_years(),
            default=multi_years if len(multi_years) >= 3 else [2022, 2023, 2024, 2025, 2026],
            key="g1_years"
        )
        if not g1_years:
            g1_years = [2022, 2023, 2024, 2025, 2026]
    with c_g1_opt3:
        g1_top_mins_str = st.selectbox(
            "Carteras a Visualizar",
            options=["Top 5 Mayor Presupuesto", "Top 10 Mayor Presupuesto", "Carteras Seleccionadas"],
            index=0,
            key="g1_top_mins_str"
        )

    # Cargar datos multianuales
    df_my_all = db.get_national_multiyear_ranking(
        years=g1_years,
        periodo="Junio" if ("Trimestre" in periodo or periodo == "Junio") else periodo,
        moneda=moneda,
        exclude_tesoro=exclude_tesoro,
        ministerios=filter_mins if filter_mins else None
    )

    if not df_my_all.empty:
        # Determinar ministerios a graficar
        if g1_top_mins_str == "Top 5 Mayor Presupuesto":
            top_mins_list = df_my_all.groupby("ministerio")["vigente"].mean().nlargest(5).index.tolist()
        elif g1_top_mins_str == "Top 10 Mayor Presupuesto":
            top_mins_list = df_my_all.groupby("ministerio")["vigente"].mean().nlargest(10).index.tolist()
        else:
            top_mins_list = df_my_all["ministerio"].unique().tolist()[:8]

        df_my_plot = df_my_all[df_my_all["ministerio"].isin(top_mins_list)].copy()
        df_my_plot["min_short"] = df_my_plot["ministerio"].apply(clean_min_name)
        df_my_plot["vigente_mm"] = df_my_plot["vigente"] * 1000 / 1e9
        df_my_plot["ejecucion_mm"] = df_my_plot["ejecucion"] * 1000 / 1e9
        df_my_plot["subt31_mm"] = df_my_plot["subt31_vigente"] * 1000 / 1e9
        df_my_plot["year_str"] = df_my_plot["year"].astype(str)

        if g1_metric == "Presupuesto Vigente ($ MM)":
            y_col_g1 = "vigente_mm"
            y_title_g1 = "Presupuesto Vigente ($ Miles de Millones - MM)"
            y_fmt_g1 = ":,.1f"
        elif g1_metric == "Ejecución Devengada ($ MM)":
            y_col_g1 = "ejecucion_mm"
            y_title_g1 = "Ejecución Devengada ($ Miles de Millones - MM)"
            y_fmt_g1 = ":,.1f"
        elif g1_metric == "% Avance Presupuestario":
            y_col_g1 = "pct_ejecucion"
            y_title_g1 = "% Avance Presupuestario"
            y_fmt_g1 = ":.1f"
        else:
            y_col_g1 = "subt31_mm"
            y_title_g1 = "Inversión Subt. 31 ($ Miles de Millones - MM)"
            y_fmt_g1 = ":,.1f"

        fig_g1 = px.line(
            df_my_plot,
            x="year_str",
            y=y_col_g1,
            color="min_short",
            markers=True,
            hover_name="ministerio",
            hover_data={"year_str": True, y_col_g1: y_fmt_g1, "min_short": False},
            labels={"year_str": "Año", y_col_g1: y_title_g1, "min_short": "Ministerio"}
        )
        fig_g1.update_traces(
            line=dict(width=2.8),
            marker=dict(size=8, line=dict(width=1, color="#ffffff"))
        )
        fig_g1.update_layout(
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            height=430,
            autosize=True,
            hovermode="closest",
            hoverdistance=60,
            margin=dict(l=20, r=20, t=30, b=35),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=9.5)),
            xaxis=dict(gridcolor="#f1f5f9", linecolor="#cbd5e1", title="Año", type="category"),
            yaxis=dict(gridcolor="#f1f5f9", linecolor="#cbd5e1", title=y_title_g1)
        )
        st.plotly_chart(fig_g1, use_container_width=True)
    else:
        st.info("No hay datos multianuales suficientes para construir la serie histórica con los filtros actuales.")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # GRÁFICO EXTRA 2: MAPA DE CALOR (HEATMAP) & CURVAS DE ACELERACIÓN MENSUAL (ENERO A DICIEMBRE)
    st.markdown("##### 🔥 Gráfico Extra 2: Mapa de Calor (Heatmap) / Velocidad de Ejecución Mensual")
    st.caption("Seguimiento mes a mes (Enero a Diciembre): detecta el ritmo de ejecución de cada cartera e identifica aceleraciones tempranas o cuellos de botella.")

    c_g2_opt1, c_g2_opt2, c_g2_opt3 = st.columns([4.2, 2.8, 3.0])
    with c_g2_opt1:
        g2_view_type = st.radio(
            "Tipo de Visualización Mensual:",
            options=["🔥 Mapa de Calor (Heatmap Interministerial)", "⚡ Curvas de Aceleración de Gasto Acumulado"],
            index=0,
            horizontal=True,
            key="g2_view_type"
        )
    with c_g2_opt2:
        loaded_g2_years = sorted(db.get_loaded_years(), reverse=True)
        g2_year = st.selectbox(
            "Año para Análisis Mensual",
            options=loaded_g2_years,
            index=loaded_g2_years.index(year) if year in loaded_g2_years else 0,
            key="g2_year"
        )
    with c_g2_opt3:
        st.markdown("<div style='height: 26px;'></div>", unsafe_allow_html=True)
        g2_full_12m = st.checkbox(
            "Matriz completa 12 meses (Ene - Dic)",
            value=True,
            key="g2_full_12m",
            help="Despliega los 12 meses del calendario oficial en la cuadrícula del Heatmap."
        )

    df_monthly = db.get_national_monthly_progression(
        year=g2_year,
        moneda=moneda,
        exclude_tesoro=exclude_tesoro,
        ministerios=filter_mins if filter_mins else None
    )

    if not df_monthly.empty:
        df_monthly["min_short"] = df_monthly["ministerio"].apply(clean_min_name)
        meses_orden = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

        if "Heatmap" in g2_view_type:
            # Pivot table para el Heatmap
            pivot_mo = df_monthly.pivot(index="min_short", columns="periodo", values="pct_ejecucion")
            if g2_full_12m:
                pivot_mo = pivot_mo.reindex(columns=meses_orden)
            else:
                cols_present = [m for m in meses_orden if m in pivot_mo.columns]
                pivot_mo = pivot_mo[cols_present] if cols_present else pivot_mo

            # Ordenar carteras según el último mes disponible con datos
            non_empty_cols = [c for c in pivot_mo.columns if pivot_mo[c].notna().any()]
            if non_empty_cols:
                last_col = non_empty_cols[-1]
                pivot_mo = pivot_mo.sort_values(by=last_col, ascending=True)

            fig_heat = px.imshow(
                pivot_mo,
                labels=dict(x="Mes", y="Ministerio", color="% Avance"),
                x=pivot_mo.columns,
                y=pivot_mo.index,
                color_continuous_scale="Viridis",
                aspect="auto",
                text_auto=".1f"
            )
            fig_heat.update_layout(
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                height=max(420, len(pivot_mo) * 22),
                autosize=True,
                margin=dict(l=20, r=20, t=60, b=30),
                xaxis=dict(
                    title="Mes del Ejercicio Presupuestario (12 Meses Calendario)",
                    side="top",
                    categoryorder="array",
                    categoryarray=meses_orden,
                    tickfont=dict(size=11, color="#0f172a", family="sans-serif")
                ),
                yaxis=dict(title="", tickfont=dict(size=9.5, color="#0f172a")),
                coloraxis_colorbar=dict(title="% Avance", thickness=14, len=0.8, ticksuffix="%")
            )
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            # Curvas de aceleración de gasto
            top_mo_mins = df_monthly.groupby("min_short")["vigente"].mean().nlargest(8).index.tolist()
            df_curve = df_monthly[df_monthly["min_short"].isin(top_mo_mins)].copy()
            df_curve = df_curve.sort_values(by=["min_short", "mes_num"])

            fig_curve = px.line(
                df_curve,
                x="periodo",
                y="pct_ejecucion",
                color="min_short",
                markers=True,
                labels={"periodo": "Mes", "pct_ejecucion": "% Avance Devengado", "min_short": "Ministerio"}
            )
            fig_curve.update_traces(line=dict(width=2.5), marker=dict(size=7))
            fig_curve.update_layout(
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                height=430,
                autosize=True,
                hovermode="closest",
                hoverdistance=60,
                margin=dict(l=20, r=20, t=30, b=35),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=9.5)),
                xaxis=dict(title="Mes", gridcolor="#f1f5f9", categoryorder="array", categoryarray=meses_orden),
                yaxis=dict(title="% Avance Devengado", gridcolor="#f1f5f9", ticksuffix="%")
            )
            st.plotly_chart(fig_curve, use_container_width=True)
    else:
        st.info(f"No hay datos de progresión mensual disponibles para el año {g2_year} con los filtros actuales.")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # ==============================================================================
    # 5.3 GRÁFICO EXTRA 3: AUMENTO Y VARIACIÓN DE PRESUPUESTO VIGENTE POR MINISTERIO (% Y TRAMOS)
    # ==============================================================================
    st.markdown("---")
    st.markdown("##### 📈 Crecimiento de Presupuesto Vigente por Ministerio (% y Tramos de Crecimiento)")
    st.caption("Analiza qué carteras han experimentado mayor expansión presupuestaria (% y $ Miles de Millones) entre dos años a elección, clasificadas en tramos cualitativos de crecimiento.")

    # Detección dinámica de todos los años cargados en el sistema
    db_loaded_years = db.get_loaded_years()
    if not db_loaded_years:
        db_loaded_years = list(range(2014, 2027))
    min_loaded_yr = min(db_loaded_years)
    max_loaded_yr = max(db_loaded_years)

    years_avail_start = [y for y in db_loaded_years if y < max_loaded_yr]
    years_avail_end = [y for y in db_loaded_years if y > min_loaded_yr]

    # Controles del Gráfico de Crecimiento (Accesos Rápidos)
    c_gr_pre1, c_gr_pre2 = st.columns([6.5, 3.5])
    with c_gr_pre1:
        st.markdown("**⚡ Accesos Rápidos de Tramos:**")
        preset_cols = st.columns(4)
        with preset_cols[0]:
            if st.button("🎯 2022 - 2026 (Por Defecto)", key="btn_gr_def", use_container_width=True):
                st.session_state["gr_sel_start"] = 2022 if 2022 in years_avail_start else min_loaded_yr
                st.session_state["gr_sel_end"] = 2026 if 2026 in years_avail_end else max_loaded_yr
        with preset_cols[1]:
            if st.button(f"🏛️ {min_loaded_yr} - {max_loaded_yr} (Histórico)", key="btn_gr_hist", use_container_width=True):
                st.session_state["gr_sel_start"] = min_loaded_yr
                st.session_state["gr_sel_end"] = max_loaded_yr
        with preset_cols[2]:
            if st.button("⚡ 2024 - 2026 (Bienio)", key="btn_gr_2426", use_container_width=True):
                st.session_state["gr_sel_start"] = 2024 if 2024 in years_avail_start else min_loaded_yr
                st.session_state["gr_sel_end"] = 2026 if 2026 in years_avail_end else max_loaded_yr
        with preset_cols[3]:
            if st.button("📊 2018 - 2022 (Periodo)", key="btn_gr_1822", use_container_width=True):
                st.session_state["gr_sel_start"] = 2018 if 2018 in years_avail_start else min_loaded_yr
                st.session_state["gr_sel_end"] = 2022 if 2022 in years_avail_end else max_loaded_yr

    # Session state defaults
    if "gr_sel_start" not in st.session_state or st.session_state["gr_sel_start"] not in years_avail_start:
        st.session_state["gr_sel_start"] = 2022 if 2022 in years_avail_start else min_loaded_yr
    if "gr_sel_end" not in st.session_state or st.session_state["gr_sel_end"] not in years_avail_end:
        st.session_state["gr_sel_end"] = 2026 if 2026 in years_avail_end else max_loaded_yr

    c_g3_1, c_g3_2, c_g3_3, c_g3_4, c_g3_5 = st.columns([2.0, 2.0, 2.2, 3.2, 2.6])
    with c_g3_1:
        gr_start = st.selectbox(
            "Año Inicial (Desde)",
            options=years_avail_start,
            key="gr_sel_start"
        )
    with c_g3_2:
        valid_end = [y for y in years_avail_end if y > gr_start]
        if not valid_end:
            valid_end = [y for y in years_avail_end if y >= gr_start]
        if st.session_state.get("gr_sel_end", max_loaded_yr) not in valid_end:
            st.session_state["gr_sel_end"] = max(valid_end)
        gr_end = st.selectbox(
            "Año Final (Hasta)",
            options=valid_end,
            key="gr_sel_end"
        )
    with c_g3_3:
        common_periods = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        if gr_end == 2026:
            common_periods = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio']
        gr_periodo = st.selectbox(
            "Mes de Corte",
            options=common_periods,
            index=common_periods.index("Junio") if "Junio" in common_periods else 0,
            key="gr_periodo_sel",
            help="Compara presupuestos vigentes homologados al mismo mes del año."
        )
    with c_g3_4:
        tramos_opciones = [
            "Todos los tramos",
            "🚀 Extraordinario (> 50%)",
            "📈 Alto (25% a 50%)",
            "📊 Moderado (10% a 25%)",
            "⚖️ Leve (0% a 10%)",
            "🔻 Contracción (< 0%)"
        ]
        gr_tramo_filtro = st.multiselect(
            "Filtrar por Tramos de Aumento",
            options=tramos_opciones[1:],
            default=[],
            placeholder="Todos los tramos visibles",
            key="gr_tramo_filtro"
        )
    with c_g3_5:
        gr_sort = st.selectbox(
            "Ordenar Cartera por",
            options=["Mayor % de Aumento", "Menor % de Aumento / Contracción", "Mayor Aumento en Monto ($ MM)", "Presupuesto Final ($ MM)"],
            index=0,
            key="gr_sort_sel"
        )

    # Opción interactiva para activar/desactivar el desglose de recursos por ítem dentro de la barra
    c_tog_row1, c_tog_row2 = st.columns([5.5, 4.5])
    with c_tog_row1:
        gr_desglosar_items = st.toggle(
            "🧩 Desglosar barras por ítem de gasto (en qué se gasta cada recurso)",
            value=False,
            key="gr_toggle_desglose",
            help="Fragmenta la barra de cada cartera (ej. Deportes, Salud, Obras) en sus conceptos específicos de gasto (Personal, Bienes, Obras, Transferencias, etc.)."
        )
    with c_tog_row2:
        if gr_desglosar_items:
            c_sub_m1, c_sub_m2 = st.columns(2)
            with c_sub_m1:
                gr_item_mode = st.selectbox(
                    "Métrica del Desglose",
                    options=["Monto Real ($ MM)", "Distribución (%) 100% Apilado"],
                    index=0,
                    key="gr_item_mode"
                )
            with c_sub_m2:
                gr_item_year = st.selectbox(
                    "Año a Desglosar",
                    options=[f"Año Final ({gr_end})", f"Año Inicial ({gr_start})"],
                    index=0,
                    key="gr_item_year"
                )
        else:
            gr_item_mode = "Monto Real ($ MM)"
            gr_item_year = f"Año Final ({gr_end})"

    if gr_start >= gr_end:
        st.warning(f"⚠️ El Año Inicial ({gr_start}) debe ser estrictamente menor al Año Final ({gr_end}) para calcular la tasa de crecimiento.")
    else:
        df_growth = db.get_national_budget_growth(
            start_year=gr_start,
            end_year=gr_end,
            periodo=gr_periodo,
            moneda=moneda,
            exclude_tesoro=exclude_tesoro,
            ministerios=filter_mins if filter_mins else None
        )

        if not df_growth.empty:
            df_growth["min_short"] = df_growth["ministerio"].apply(clean_min_name)

            if gr_tramo_filtro:
                df_growth_plot = df_growth[df_growth["tramo"].isin(gr_tramo_filtro)].copy()
            else:
                df_growth_plot = df_growth.copy()

            if gr_sort == "Menor % de Aumento / Contracción":
                df_growth_plot = df_growth_plot.sort_values(by="pct_aumento", ascending=True)
            elif gr_sort == "Mayor Aumento en Monto ($ MM)":
                df_growth_plot = df_growth_plot.sort_values(by="dif_mm", ascending=False)
            elif gr_sort == "Presupuesto Final ($ MM)":
                df_growth_plot = df_growth_plot.sort_values(by="fin_mm", ascending=False)
            else:
                df_growth_plot = df_growth_plot.sort_values(by="pct_aumento", ascending=False)

            total_ini_mm = df_growth["ini_mm"].sum()
            total_fin_mm = df_growth["fin_mm"].sum()
            total_dif_mm = total_fin_mm - total_ini_mm
            total_pct_grow = round((total_dif_mm / total_ini_mm * 100), 2) if total_ini_mm > 0 else 0.0

            top_pct_row = df_growth.loc[df_growth["pct_aumento"].idxmax()]
            top_din_row = df_growth.loc[df_growth["dif_mm"].idxmax()]
            tramos_cnt = df_growth["tramo"].value_counts()

            kpi_gr1, kpi_gr2, kpi_gr3, kpi_gr4 = st.columns(4)
            with kpi_gr1:
                st.metric(
                    label=f"🚀 Mayor % Aumento ({gr_start} - {gr_end})",
                    value=f"+{top_pct_row['pct_aumento']:.1f}%",
                    delta=f"{clean_min_name(top_pct_row['ministerio'])} (+${top_pct_row['dif_mm']:,.0f} MM)"
                )
            with kpi_gr2:
                st.metric(
                    label=f"💰 Mayor Aumento en Dinero",
                    value=f"+${top_din_row['dif_mm']:,.1f} MM",
                    delta=f"{clean_min_name(top_din_row['ministerio'])} (+{top_din_row['pct_aumento']:.1f}%)"
                )
            with kpi_gr3:
                st.metric(
                    label=f"🇨🇱 Expansión Total Consolidada",
                    value=f"{'+' if total_pct_grow >= 0 else ''}{total_pct_grow:.1f}%",
                    delta=f"{'+' if total_dif_mm >= 0 else ''}${total_dif_mm:,.1f} MM (Base: ${total_ini_mm:,.1f} MM)"
                )
            with kpi_gr4:
                n_extra = tramos_cnt.get("🚀 Extraordinario (> 50%)", 0)
                n_alto = tramos_cnt.get("📈 Alto (25% a 50%)", 0)
                n_mod = tramos_cnt.get("📊 Moderado (10% a 25%)", 0)
                n_leve = tramos_cnt.get("⚖️ Leve (0% a 10%)", 0)
                n_cont = tramos_cnt.get("🔻 Contracción (< 0%)", 0)
                st.metric(
                    label=f"📊 Carteras por Tramo ({len(df_growth)} Total)",
                    value=f"{n_extra} Extr · {n_alto} Alto · {n_mod} Mod",
                    delta=f"{n_leve} Leve · {n_cont} Contracción",
                    delta_color="off"
                )

            df_chart_data = df_growth_plot.iloc[::-1].copy()

            if gr_desglosar_items:
                # ==============================================================================
                # MODO ACTIVADO: BARRA DESGLOSADA POR ÍTEM / SUBTÍTULO DE GASTO (EN QUÉ SE GASTA CADA RECURSO)
                # ==============================================================================
                target_decomp_year = gr_end if "Final" in gr_item_year else gr_start
                df_items_decomp = db.get_national_subtitulos_by_ministerio(
                    year=target_decomp_year,
                    periodo=gr_periodo,
                    moneda=moneda,
                    exclude_tesoro=exclude_tesoro,
                    ministerios=filter_mins if filter_mins else None
                )

                if not df_items_decomp.empty:
                    df_items_decomp["min_short"] = df_items_decomp["ministerio"].apply(clean_min_name)
                    df_items_decomp["sub_key"] = df_items_decomp["subtitulo_cod"].apply(lambda c: str(c).zfill(2))

                    macro_item_palette = {
                        '21': ('👥 Personal y Sueldos (Subt. 21)', '#3b82f6'),
                        '22': ('📦 Bienes y Servicios (Subt. 22)', '#8b5cf6'),
                        '24': ('🤝 Transferencias y Subsidios (Subt. 24)', '#f59e0b'),
                        '31': ('🏗️ Inversión Real en Obras (Subt. 31)', '#10b981'),
                        '33': ('🚜 Transferencias de Capital (Subt. 33)', '#d97706'),
                        '29': ('💻 Activos No Financieros (Subt. 29)', '#06b6d4'),
                        '23': ('🛡️ Seguridad Social (Subt. 23)', '#ec4899'),
                        '34': ('💳 Deuda Pública (Subt. 34)', '#64748b'),
                        '25': ('📑 Íntegros al Fisco (Subt. 25)', '#475569'),
                        '30': ('📈 Activos Financieros (Subt. 30)', '#14b8a6'),
                        '32': ('🏦 Préstamos (Subt. 32)', '#6366f1'),
                        '35': ('💰 Saldo Final de Caja (Subt. 35)', '#94a3b8')
                    }

                    tot_by_min = df_items_decomp.groupby("min_short")["vigente_mm"].sum().to_dict()
                    mins_ordered = df_chart_data["min_short"].tolist()

                    fig_growth = go.Figure()
                    for cod, (cat_name, color) in macro_item_palette.items():
                        sub_cat = df_items_decomp[df_items_decomp["sub_key"] == cod]
                        if not sub_cat.empty and sub_cat["vigente_mm"].sum() > 0:
                            map_val = dict(zip(sub_cat["min_short"], sub_cat["vigente_mm"]))
                            map_pct = dict(zip(sub_cat["min_short"], sub_cat["pct_ejecucion"]))
                            
                            x_vals = []
                            custom_data = []
                            for m in mins_ordered:
                                val_mm = map_val.get(m, 0.0)
                                tot_m = tot_by_min.get(m, 1.0)
                                share_pct = (val_mm / tot_m * 100) if tot_m > 0 else 0.0
                                ejec_pct = map_pct.get(m, 0.0)
                                if "Distribución" in gr_item_mode:
                                    x_vals.append(share_pct)
                                    custom_data.append([val_mm, ejec_pct])
                                else:
                                    x_vals.append(val_mm)
                                    custom_data.append([share_pct, ejec_pct])
                            
                            if any(v > 0 for v in x_vals):
                                if "Distribución" in gr_item_mode:
                                    hovertemp = (
                                        "<b>%{y}</b><br>"
                                        f"Rubro: <b>{cat_name}</b><br>"
                                        "Proporción en la Cartera: <b>%{x:.1f}%</b><br>"
                                        "Presupuesto Vigente: <b>$%{customdata[0]:,.1f} MM</b><br>"
                                        "Avance Devengado del Rubro: <b>%{customdata[1]:.1f}%</b><extra></extra>"
                                    )
                                else:
                                    hovertemp = (
                                        "<b>%{y}</b><br>"
                                        f"Rubro: <b>{cat_name}</b><br>"
                                        "Presupuesto Vigente: <b>$%{x:,.1f} MM</b><br>"
                                        "Proporción en la Cartera: <b>%{customdata[0]:.1f}%</b><br>"
                                        "Avance Devengado del Rubro: <b>%{customdata[1]:.1f}%</b><extra></extra>"
                                    )
                                fig_growth.add_trace(go.Bar(
                                    name=cat_name,
                                    y=mins_ordered,
                                    x=x_vals,
                                    orientation='h',
                                    marker=dict(color=color),
                                    customdata=custom_data,
                                    hovertemplate=hovertemp
                                ))

                    is_pct_mode = "Distribución" in gr_item_mode
                    x_axis_title = (
                        f"Distribución Porcentual del Gasto por Ítem (%) · {target_decomp_year} (Corte {gr_periodo})"
                        if is_pct_mode
                        else f"Presupuesto Vigente Desglosado por Ítem ($ Miles de Millones - MM) · {target_decomp_year} (Corte {gr_periodo})"
                    )

                    fig_growth.update_layout(
                        barmode='stack',
                        paper_bgcolor="#ffffff",
                        plot_bgcolor="#ffffff",
                        height=max(500, len(mins_ordered) * 27),
                        autosize=True,
                        hovermode="closest",
                        hoverdistance=60,
                        margin=dict(l=20, r=40, t=35, b=40),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=9.5)
                        ),
                        xaxis=dict(
                            title=x_axis_title,
                            gridcolor="#f1f5f9",
                            linecolor="#cbd5e1",
                            ticksuffix="%" if is_pct_mode else " MM",
                            tickprefix="" if is_pct_mode else "$ ",
                            range=[0, 100] if is_pct_mode else None
                        ),
                        yaxis=dict(
                            title="",
                            tickfont=dict(size=9.8, color="#0f172a"),
                            linecolor="#cbd5e1",
                            categoryorder="array",
                            categoryarray=mins_ordered
                        )
                    )
                else:
                    st.info(f"No hay registros de ítems/subtítulos para el año {target_decomp_year} y corte {gr_periodo}.")
            else:
                # ==============================================================================
                # MODO DESACTIVADO (POR DEFECTO): GRÁFICO CONSOLIDADO POR TRAMOS DE CRECIMIENTO
                # ==============================================================================
                tramo_colors = {
                    "🚀 Extraordinario (> 50%)": "#10b981",
                    "📈 Alto (25% a 50%)": "#2563eb",
                    "📊 Moderado (10% a 25%)": "#8b5cf6",
                    "⚖️ Leve (0% a 10%)": "#f59e0b",
                    "🔻 Contracción (< 0%)": "#ef4444"
                }

                fig_growth = px.bar(
                    df_chart_data,
                    x="pct_aumento",
                    y="min_short",
                    orientation="h",
                    color="tramo",
                    color_discrete_map=tramo_colors,
                    labels={
                        "pct_aumento": f"% Aumento Presupuesto Vigente ({gr_start} vs {gr_end})",
                        "min_short": "Ministerio",
                        "tramo": "Tramo de Crecimiento"
                    },
                    hover_name="ministerio",
                    hover_data={
                        "min_short": False,
                        "tramo": True,
                        "pct_aumento": ":+.1f",
                        "ini_mm": ":,.1f",
                        "fin_mm": ":,.1f",
                        "dif_mm": ":+,.1f"
                    },
                    text=df_chart_data["pct_aumento"].apply(lambda v: f" {v:+.1f}%")
                )

                fig_growth.update_traces(
                    textposition="outside",
                    cliponaxis=False,
                    marker=dict(line=dict(width=0.5, color="#cbd5e1"))
                )

                fig_growth.add_vline(x=0, line_width=1.5, line_color="#94a3b8", line_dash="solid")

                fig_growth.update_layout(
                    paper_bgcolor="#ffffff",
                    plot_bgcolor="#ffffff",
                    height=max(480, len(df_chart_data) * 26),
                    autosize=True,
                    hovermode="closest",
                    hoverdistance=60,
                    margin=dict(l=20, r=45, t=35, b=40),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        font=dict(size=10)
                    ),
                    xaxis=dict(
                        title=f"% Variación de Presupuesto Vigente (Corte {gr_periodo}: {gr_start} → {gr_end})",
                        gridcolor="#f1f5f9",
                        linecolor="#cbd5e1",
                        ticksuffix="%"
                    ),
                    yaxis=dict(
                        title="",
                        tickfont=dict(size=9.8, color="#0f172a"),
                        linecolor="#cbd5e1"
                    )
                )

            # 💡 Mensaje de interactividad para el usuario
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: space-between; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 7px 12px; margin: 6px 0 10px 0;">
                <span style="font-size: 0.82rem; color: #166534; font-weight: 600;">
                    👆 <b>Profundización Interactiva:</b> Haz clic en la barra de cualquier ministerio para analizar en detalle sus <b>gastos específicos y programas</b>.
                </span>
                <span style="font-size: 0.74rem; color: #15803d; font-weight: 600; background: #dcfce7; padding: 2px 8px; border-radius: 9999px;">
                    Nivel 1: Subtítulos ➔ Nivel 2: Programas
                </span>
            </div>
            """, unsafe_allow_html=True)

            growth_chart_key = f"growth_chart_sel_{gr_start}_{gr_end}_{gr_periodo}_{'decomp' if gr_desglosar_items else 'bar'}"
            growth_sel_event = st.plotly_chart(
                fig_growth,
                use_container_width=True,
                on_select="rerun",
                selection_mode="points",
                key=growth_chart_key
            )

            # Capturar clic en la barra del gráfico principal
            if growth_sel_event and "selection" in growth_sel_event and growth_sel_event["selection"].get("points"):
                pt_main = growth_sel_event["selection"]["points"][0]
                clicked_y = pt_main.get("y")
                if clicked_y:
                    min_lookup = dict(zip(df_chart_data["min_short"], df_chart_data["ministerio"]))
                    for full_m in df_growth["ministerio"]:
                        min_lookup[full_m] = full_m
                    selected_m = min_lookup.get(clicked_y, clicked_y)
                    if st.session_state.get("growth_drill_min") != selected_m:
                        st.session_state["growth_drill_min"] = selected_m
                        st.session_state["growth_drill_subt"] = None
                        st.session_state["growth_drill_prog"] = None

            # Selector complementario por si el usuario prefiere elegir de una lista
            all_mins_sorted = sorted(df_growth["ministerio"].unique().tolist())
            current_drill = st.session_state.get("growth_drill_min")
            idx_sel = (all_mins_sorted.index(current_drill) + 1) if (current_drill and current_drill in all_mins_sorted) else 0

            c_sel_dd1, c_sel_dd2 = st.columns([7, 3])
            with c_sel_dd1:
                chosen_dd_min = st.selectbox(
                    "🔍 Cartera seleccionada para profundizar (haz clic en el gráfico o elígela aquí):",
                    options=["-- Ninguna (ver panorama general) --"] + all_mins_sorted,
                    index=idx_sel,
                    key="sb_growth_drill_min"
                )
                if chosen_dd_min != "-- Ninguna (ver panorama general) --":
                    if st.session_state.get("growth_drill_min") != chosen_dd_min:
                        st.session_state["growth_drill_min"] = chosen_dd_min
                        st.session_state["growth_drill_subt"] = None
                        st.session_state["growth_drill_prog"] = None
                else:
                    if current_drill is not None:
                        st.session_state["growth_drill_min"] = None
                        st.session_state["growth_drill_subt"] = None
                        st.session_state["growth_drill_prog"] = None

            with c_sel_dd2:
                if st.session_state.get("growth_drill_min"):
                    if st.button("❌ Cerrar Profundización", key="btn_close_drill", use_container_width=True):
                        st.session_state["growth_drill_min"] = None
                        st.session_state["growth_drill_subt"] = None
                        st.session_state["growth_drill_prog"] = None
                        st.rerun()

            # ==============================================================================
            # PANEL DE PROFUNDIZACIÓN DINÁMICA (NIVELES 1, 2 Y 3)
            # ==============================================================================
            active_dd_min = st.session_state.get("growth_drill_min")
            if active_dd_min and active_dd_min in df_growth["ministerio"].values:
                st.markdown(f"""
                <div style="background-color: #f8fafc; border: 2px solid #3b82f6; border-radius: 12px; padding: 14px 18px; margin: 12px 0 16px 0; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                            <span style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">🔎 Profundización de Gastos:</span>
                            <span style="background-color: #eff6ff; color: #1d4ed8; font-weight: 800; font-size: 1.05rem; padding: 3px 12px; border-radius: 8px; border: 1px solid #bfdbfe;">
                                {active_dd_min}
                            </span>
                            <span style="background-color: #f1f5f9; color: #475569; font-size: 0.82rem; padding: 2px 8px; border-radius: 6px; font-weight: 600;">
                                Corte {gr_periodo} ({gr_start} ➔ {gr_end})
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Tarjetas de resumen del ministerio seleccionado
                row_m = df_growth[df_growth["ministerio"] == active_dd_min].iloc[0]
                c_dd_k1, c_dd_k2, c_dd_k3, c_dd_k4 = st.columns(4)
                with c_dd_k1:
                    st.metric(f"Presupuesto {gr_start}", f"${row_m['ini_mm']:,.1f} MM")
                with c_dd_k2:
                    st.metric(f"Presupuesto {gr_end}", f"${row_m['fin_mm']:,.1f} MM")
                with c_dd_k3:
                    st.metric("Variación en Monto", f"{'+' if row_m['dif_mm']>=0 else ''}${row_m['dif_mm']:,.1f} MM")
                with c_dd_k4:
                    st.metric("Tasa de Crecimiento", f"{'+' if row_m['pct_aumento']>=0 else ''}{row_m['pct_aumento']:.1f}%", delta=row_m["tramo"], delta_color="off")

                # Obtener gastos específicos por subtítulo del ministerio
                df_sub_growth = db.get_ministry_subtitulos_growth(
                    ministerio=active_dd_min,
                    start_year=gr_start,
                    end_year=gr_end,
                    periodo=gr_periodo,
                    moneda=moneda
                )

                if df_sub_growth.empty:
                    st.info(f"No se encontraron registros de subtítulos de gasto para {active_dd_min} en los años {gr_start} y {gr_end}.")
                else:
                    active_subt = st.session_state.get("growth_drill_subt")

                    # Migas de pan de navegación
                    b_col1, b_col2 = st.columns([8, 2])
                    with b_col1:
                        if active_subt:
                            subt_name_match = df_sub_growth[df_sub_growth["subtitulo_cod"] == active_subt]
                            subt_label_txt = subt_name_match["label"].iloc[0] if not subt_name_match.empty else f"Subtítulo {active_subt}"
                            st.markdown(f"""
                            <div style="font-size: 0.88rem; color: #475569; margin: 4px 0 8px 0;">
                                <b>Navegación:</b> <span style="color: #2563eb; font-weight: 600;">🏛️ {clean_min_name(active_dd_min)}</span> &nbsp;➔&nbsp; <span style="background-color: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 5px; font-weight: 700;">📦 {subt_label_txt}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="font-size: 0.88rem; color: #475569; margin: 4px 0 8px 0;">
                                <b>Nivel 1:</b> <span style="color: #2563eb; font-weight: 700;">🏛️ Gastos Específicos por Subtítulo de {clean_min_name(active_dd_min)}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    with b_col2:
                        if active_subt:
                            if st.button("⬅️ Volver a Subtítulos", key="btn_back_subt", use_container_width=True):
                                st.session_state["growth_drill_subt"] = None
                                st.session_state["growth_drill_prog"] = None
                                st.rerun()

                    if not active_subt:
                        # ------------------------------------------------------------------
                        # NIVEL 1: GRÁFICO DE GASTOS ESPECÍFICOS POR SUBTÍTULO
                        # ------------------------------------------------------------------
                        st.markdown(f"###### 📊 Variación de Gastos Específicos por Subtítulo ({gr_start} vs {gr_end})")
                        st.caption("Haz clic en cualquier barra de subtítulo para ver qué programas o direcciones ejecutan ese gasto.")

                        df_sub_plot = df_sub_growth.sort_values(by="dif_mm", ascending=True).copy()

                        fig_subt = go.Figure()
                        fig_subt.add_trace(go.Bar(
                            name=f"Año {gr_start}",
                            y=df_sub_plot["label"],
                            x=df_sub_plot["ini_mm"],
                            orientation='h',
                            marker=dict(color="#94a3b8"),
                            customdata=df_sub_plot[["subtitulo_cod", "dif_mm", "pct_grow", "ini_ejec_mm"]].values,
                            hovertemplate=(
                                "<b>%{y}</b><br>"
                                f"Presupuesto {gr_start}: <b>$%{{x:,.1f}} MM</b><br>"
                                f"Presupuesto {gr_end}: <b>$%{{customdata[1]+%{{x}}:,.1f}} MM</b><br>"
                                "Variación Neta: <b>%{customdata[1]:+,.1f} MM</b> (%{customdata[2]:+.1f}%)<extra></extra>"
                            )
                        ))
                        fig_subt.add_trace(go.Bar(
                            name=f"Año {gr_end}",
                            y=df_sub_plot["label"],
                            x=df_sub_plot["fin_mm"],
                            orientation='h',
                            marker=dict(color="#2563eb"),
                            customdata=df_sub_plot[["subtitulo_cod", "dif_mm", "pct_grow", "fin_ejec_mm"]].values,
                            hovertemplate=(
                                "<b>%{y}</b><br>"
                                f"Presupuesto {gr_end}: <b>$%{{x:,.1f}} MM</b><br>"
                                f"Presupuesto {gr_start}: <b>$%{{%{{x}}-%{{customdata[1]}}:,.1f}} MM</b><br>"
                                "Variación Neta: <b>%{customdata[1]:+,.1f} MM</b> (%{customdata[2]:+.1f}%)<extra></extra>"
                            )
                        ))

                        fig_subt.update_layout(
                            barmode='group',
                            paper_bgcolor="#ffffff",
                            plot_bgcolor="#ffffff",
                            height=max(360, len(df_sub_plot) * 32),
                            margin=dict(l=20, r=30, t=30, b=40),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            xaxis=dict(title="Presupuesto Vigente ($ Miles de Millones - MM)", gridcolor="#f1f5f9", linecolor="#cbd5e1"),
                            yaxis=dict(title="", tickfont=dict(size=9.5, color="#0f172a"), linecolor="#cbd5e1")
                        )

                        subt_event = st.plotly_chart(
                            fig_subt,
                            use_container_width=True,
                            on_select="rerun",
                            selection_mode="points",
                            key=f"chart_subt_drill_{active_dd_min}_{gr_start}_{gr_end}"
                        )

                        # Detectar clic en un subtítulo
                        if subt_event and "selection" in subt_event and subt_event["selection"].get("points"):
                            pt_s = subt_event["selection"]["points"][0]
                            c_data = pt_s.get("customdata")
                            s_cod_found = None
                            if c_data is not None and len(c_data) > 0:
                                s_cod_found = str(c_data[0])
                            else:
                                clicked_subt_label = pt_s.get("y")
                                if clicked_subt_label:
                                    sub_match = df_sub_growth[df_sub_growth["label"] == clicked_subt_label]
                                    if not sub_match.empty:
                                        s_cod_found = sub_match["subtitulo_cod"].iloc[0]
                            if s_cod_found:
                                st.session_state["growth_drill_subt"] = s_cod_found
                                st.session_state["growth_drill_prog"] = None
                                st.rerun()

                        # Acceso rápido alternativo con selector
                        sub_opts = ["-- Seleccionar Subtítulo para Profundizar --"] + df_sub_growth["label"].tolist()
                        c_sub_pick, _ = st.columns([6, 4])
                        with c_sub_pick:
                            pick_sub_lbl = st.selectbox("📦 O profundiza eligiendo el subtítulo:", options=sub_opts, key=f"sb_pick_subt_{active_dd_min}")
                            if pick_sub_lbl != "-- Seleccionar Subtítulo para Profundizar --":
                                s_code = df_sub_growth[df_sub_growth["label"] == pick_sub_lbl]["subtitulo_cod"].iloc[0]
                                if st.session_state.get("growth_drill_subt") != s_code:
                                    st.session_state["growth_drill_subt"] = s_code
                                    st.session_state["growth_drill_prog"] = None
                                    st.rerun()

                    else:
                        # ------------------------------------------------------------------
                        # NIVEL 2: PROFUNDIZAR EN PROGRAMAS DEL SUBTÍTULO
                        # ------------------------------------------------------------------
                        subt_info = df_sub_growth[df_sub_growth["subtitulo_cod"] == active_subt]
                        subt_title = subt_info["label"].iloc[0] if not subt_info.empty else f"Subtítulo {active_subt}"
                        subt_dif = subt_info["dif_mm"].iloc[0] if not subt_info.empty else 0.0
                        subt_pct = subt_info["pct_grow"].iloc[0] if not subt_info.empty else 0.0

                        st.markdown(f"##### 🏢 Programas y Servicios que Explican: {subt_title}")
                        st.caption(f"Variación Total del Rubro en la Cartera: **{'+' if subt_dif>=0 else ''}${subt_dif:,.1f} MM ({subt_pct:+.1f}%)**. Haz clic en cualquier programa para ver sus ítems específicos.")

                        df_prog_growth = db.get_ministry_subtitulo_programas_growth(
                            ministerio=active_dd_min,
                            subtitulo_cod=active_subt,
                            start_year=gr_start,
                            end_year=gr_end,
                            periodo=gr_periodo,
                            moneda=moneda
                        )

                        if df_prog_growth.empty:
                            st.info("No hay registros detallados de programas para este subtítulo.")
                        else:
                            df_prog_plot = df_prog_growth.sort_values("dif_mm", ascending=True).copy()
                            # Limitar a top 25 si son demasiados para legibilidad
                            if len(df_prog_plot) > 25:
                                df_prog_plot = df_prog_plot.tail(25)

                            fig_prog = go.Figure()
                            fig_prog.add_trace(go.Bar(
                                name=f"Año {gr_start}",
                                y=df_prog_plot["programa"].apply(lambda p: format_prog_label(p, max_len=32)),
                                x=df_prog_plot["ini_mm"],
                                orientation='h',
                                marker=dict(color="#cbd5e1"),
                                customdata=df_prog_plot[["programa", "dif_mm", "pct_grow"]].values,
                                hovertemplate=(
                                    "<b>%{customdata[0]}</b><br>"
                                    f"Presupuesto {gr_start}: <b>$%{{x:,.1f}} MM</b><br>"
                                    f"Presupuesto {gr_end}: <b>$%{{customdata[1]+%{{x}}:,.1f}} MM</b><br>"
                                    "Variación: <b>%{customdata[1]:+,.1f} MM</b> (%{customdata[2]:+.1f}%)<extra></extra>"
                                )
                            ))
                            fig_prog.add_trace(go.Bar(
                                name=f"Año {gr_end}",
                                y=df_prog_plot["programa"].apply(lambda p: format_prog_label(p, max_len=32)),
                                x=df_prog_plot["fin_mm"],
                                orientation='h',
                                marker=dict(color="#059669"),
                                customdata=df_prog_plot[["programa", "dif_mm", "pct_grow"]].values,
                                hovertemplate=(
                                    "<b>%{customdata[0]}</b><br>"
                                    f"Presupuesto {gr_end}: <b>$%{{x:,.1f}} MM</b><br>"
                                    f"Presupuesto {gr_start}: <b>$%{{%{{x}}-%{{customdata[1]}}:,.1f}} MM</b><br>"
                                    "Variación: <b>%{customdata[1]:+,.1f} MM</b> (%{customdata[2]:+.1f}%)<extra></extra>"
                                )
                            ))

                            fig_prog.update_layout(
                                barmode='group',
                                paper_bgcolor="#ffffff",
                                plot_bgcolor="#ffffff",
                                height=max(380, len(df_prog_plot) * 28),
                                margin=dict(l=20, r=30, t=30, b=40),
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                xaxis=dict(title=f"Presupuesto Vigente en {subt_title} ($ MM)", gridcolor="#f1f5f9", linecolor="#cbd5e1"),
                                yaxis=dict(title="", tickfont=dict(size=9.2, color="#0f172a"), linecolor="#cbd5e1")
                            )

                            prog_event = st.plotly_chart(
                                fig_prog,
                                use_container_width=True,
                                on_select="rerun",
                                selection_mode="points",
                                key=f"chart_prog_drill_{active_dd_min}_{active_subt}"
                            )

                            # Capturar clic en un programa
                            if prog_event and "selection" in prog_event and prog_event["selection"].get("points"):
                                pt_p = prog_event["selection"]["points"][0]
                                c_data = pt_p.get("customdata")
                                if c_data is not None and len(c_data) > 0:
                                    full_prog_name = c_data[0]
                                    st.session_state["growth_drill_prog"] = full_prog_name
                                    st.rerun()

                            # Selector complementario para programas
                            prog_opts = ["-- Seleccionar Programa para Detalle de Ítems --"] + df_prog_growth["programa"].tolist()
                            c_prog_pick, _ = st.columns([7, 3])
                            with c_prog_pick:
                                pick_prog_val = st.selectbox(
                                    "🏢 O selecciona un programa específico de la lista:",
                                    options=prog_opts,
                                    key=f"sb_pick_prog_{active_dd_min}_{active_subt}"
                                )
                                if pick_prog_val != "-- Seleccionar Programa para Detalle de Ítems --":
                                    if st.session_state.get("growth_drill_prog") != pick_prog_val:
                                        st.session_state["growth_drill_prog"] = pick_prog_val
                                        st.rerun()

                            # ------------------------------------------------------------------
                            # NIVEL 3: DETALLE POR ÍTEM DE UN PROGRAMA ESPECÍFICO
                            # ------------------------------------------------------------------
                            active_prog = st.session_state.get("growth_drill_prog")
                            if active_prog:
                                st.markdown(f"###### 📑 Líneas Presupuestarias e Ítems de: **{active_prog}**")
                                df_items_growth = db.get_ministry_programa_items_growth(
                                    ministerio=active_dd_min,
                                    subtitulo_cod=active_subt,
                                    programa=active_prog,
                                    start_year=gr_start,
                                    end_year=gr_end,
                                    periodo=gr_periodo,
                                    moneda=moneda
                                )
                                if not df_items_growth.empty:
                                    st.dataframe(
                                        df_items_growth[[
                                            "item_cod", "item_nom", "clasificacion", "ini_mm", "fin_mm", "dif_mm", "pct_grow"
                                        ]].rename(columns={
                                            "item_cod": "Ítem",
                                            "item_nom": "Nombre del Ítem",
                                            "clasificacion": "Clasificación Económica",
                                            "ini_mm": f"Presupuesto {gr_start} ($ MM)",
                                            "fin_mm": f"Presupuesto {gr_end} ($ MM)",
                                            "dif_mm": "Variación ($ MM)",
                                            "pct_grow": "% Crecimiento"
                                        }).style.format({
                                            f"Presupuesto {gr_start} ($ MM)": "${:,.1f}",
                                            f"Presupuesto {gr_end} ($ MM)": "${:,.1f}",
                                            "Variación ($ MM)": "${:+,.1f}",
                                            "% Crecimiento": "{:+.1f}%"
                                        }),
                                        use_container_width=True,
                                        height=250
                                    )
                                else:
                                    st.info("No hay asignaciones secundarias adicionales para este programa.")

                            with st.expander(f"📋 Ver Tabla de Programas de {subt_title}"):
                                st.dataframe(
                                    df_prog_growth[[
                                        "programa", "ini_mm", "fin_mm", "dif_mm", "pct_grow"
                                    ]].rename(columns={
                                        "programa": "Programa / Servicio",
                                        "ini_mm": f"Presupuesto {gr_start} ($ MM)",
                                        "fin_mm": f"Presupuesto {gr_end} ($ MM)",
                                        "dif_mm": "Variación ($ MM)",
                                        "pct_grow": "% Crecimiento"
                                    }).style.format({
                                        f"Presupuesto {gr_start} ($ MM)": "${:,.1f}",
                                        f"Presupuesto {gr_end} ($ MM)": "${:,.1f}",
                                        "Variación ($ MM)": "${:+,.1f}",
                                        "% Crecimiento": "{:+.1f}%"
                                    }),
                                    use_container_width=True,
                                    height=280
                                )

                st.markdown("---")

            with st.expander(f"📋 Ver Tabla Detallada de Cifras y Variaciones del Tramo ({gr_start} - {gr_end})"):
                df_export = df_growth_plot[[
                    "ministerio", "ini_mm", "fin_mm", "dif_mm", "pct_aumento", "tramo"
                ]].copy()
                df_export.columns = [
                    "Ministerio",
                    f"Presupuesto {gr_start} ($ MM)",
                    f"Presupuesto {gr_end} ($ MM)",
                    "Variación Neta ($ MM)",
                    "% Crecimiento",
                    "Tramo de Aumento"
                ]

                st.dataframe(
                    df_export.style.format({
                        f"Presupuesto {gr_start} ($ MM)": "${:,.1f}",
                        f"Presupuesto {gr_end} ($ MM)": "${:,.1f}",
                        "Variación Neta ($ MM)": "${:+,.1f}",
                        "% Crecimiento": "{:+.2f}%"
                    }),
                    use_container_width=True,
                    height=360
                )

                csv_growth = df_export.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"📥 Descargar Datos del Tramo {gr_start}-{gr_end} en CSV",
                    data=csv_growth,
                    file_name=f"crecimiento_presupuesto_ministerios_{gr_start}_{gr_end}.csv",
                    mime="text/csv",
                    key="btn_download_growth"
                )
        else:
            st.info(f"No hay datos suficientes para comparar el crecimiento entre {gr_start} y {gr_end} con el corte '{gr_periodo}'.")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # ==============================================================================
    # 5.4 GRÁFICO EXTRA 4: RADIOGRAFÍA ESTRUCTURAL & CALIDAD DEL GASTO PÚBLICO
    # ==============================================================================
    st.markdown("---")
    st.markdown("##### 🧬 Gráfico Extra 4: Radiografía Estructural y Calidad del Gasto por Ministerio")
    st.caption("Descubre en qué gasta realmente cada ministerio (Personal vs. Inversión en Obras vs. Transferencias y Subsidios), explora la estructura jerárquica con drill-down interactivo y evalúa el riesgo de subejecución fiscal.")

    # 1. Controles y Filtros Avanzados
    c_e4_opt1, c_e4_opt2, c_e4_opt3, c_e4_opt4 = st.columns([4.2, 2.0, 2.2, 3.6], gap="small")
    with c_e4_opt1:
        e4_mode = st.radio(
            "Perspectiva de Análisis:",
            options=[
                "📊 Anatomía y Calidad (100% Apilado)",
                "🗺️ Treemap Jerárquico (Drill-Down)",
                "🚨 Matriz de Riesgo de Subejecución"
            ],
            index=0,
            horizontal=True,
            key="e4_mode_sel"
        )
    with c_e4_opt2:
        loaded_e4_years = sorted(db.get_loaded_years(), reverse=True)
        e4_year = st.selectbox(
            "Año Análisis",
            options=loaded_e4_years,
            index=loaded_e4_years.index(year) if year in loaded_e4_years else 0,
            key="e4_year_sel"
        )
    with c_e4_opt3:
        avail_e4_pers = db.get_available_periods_for_year(e4_year, moneda=moneda)
        if not avail_e4_pers:
            avail_e4_pers = ["Junio", "Marzo", "Septiembre", "Diciembre"]
        e4_period = st.selectbox(
            "Mes de Corte",
            options=avail_e4_pers,
            index=avail_e4_pers.index("Junio") if "Junio" in avail_e4_pers else 0,
            key="e4_period_sel"
        )
    with c_e4_opt4:
        if "Anatomía" in e4_mode:
            e4_sort = st.selectbox(
                "Ordenar Ministerios por",
                options=[
                    "🏗️ Mayor % Inversión Real (Subt. 31)",
                    "👥 Mayor % Personal y Sueldos (Subt. 21)",
                    "🤝 Mayor % Transferencias / Subsidios (Subt. 24)",
                    "💰 Mayor Presupuesto Vigente Total ($ MM)",
                    "⚡ Mayor % Avance Global"
                ],
                index=0,
                key="e4_sort_anatomy"
            )
        elif "Treemap" in e4_mode:
            e4_tree_metric = st.selectbox(
                "Métrica del Tamaño de Celda",
                options=["Presupuesto Vigente ($ MM)", "Ejecución Devengada ($ MM)", "Saldo Disponible ($ MM)"],
                index=0,
                key="e4_tree_metric"
            )
        else: # Riesgo de Subejecución
            e4_risk_filter = st.selectbox(
                "Filtrar por Nivel de Riesgo",
                options=["Todos los Niveles", "🚨 Riesgo Crítico", "⚠️ Alerta Amarilla", "✅ Ritmo Óptimo", "⚡ Acelerado"],
                index=0,
                key="e4_risk_filter"
            )

    # 2. Carga de datos de subtítulos interministeriales
    df_e4_subts = db.get_national_subtitulos_by_ministerio(
        year=e4_year,
        periodo=e4_period,
        moneda=moneda,
        exclude_tesoro=exclude_tesoro,
        ministerios=filter_mins if filter_mins else None
    )

    if not df_e4_subts.empty:
        # Clasificación macroeconómica de subtítulos
        def map_subt_macro_e4(cod, nom):
            cod = str(cod).strip()
            if cod == '21':
                return '👥 Personal y Sueldos (Subt. 21)'
            elif cod == '22':
                return '📦 Bienes y Servicios (Subt. 22)'
            elif cod == '23':
                return '🛡️ Seguridad Social (Subt. 23)'
            elif cod == '24':
                return '🤝 Transferencias y Subsidios (Subt. 24)'
            elif cod == '31':
                return '🏗️ Inversión Real y Obras (Subt. 31)'
            elif cod == '33':
                return '🚜 Transferencias de Capital (Subt. 33)'
            elif cod == '29':
                return '💻 Activos No Financieros (Subt. 29)'
            elif cod == '34':
                return '💳 Deuda Pública (Subt. 34)'
            else:
                return '📑 Otros Subtítulos'

        df_e4_subts['macro_categoria'] = df_e4_subts.apply(lambda r: map_subt_macro_e4(r['subtitulo_cod'], r['subtitulo_nom']), axis=1)
        df_e4_subts['min_short'] = df_e4_subts['ministerio'].apply(clean_min_name)

        # Paleta de colores macroeconómicos de alta gama
        cat_colors_e4 = {
            '🏗️ Inversión Real y Obras (Subt. 31)': '#10b981',
            '🚜 Transferencias de Capital (Subt. 33)': '#34d399',
            '💻 Activos No Financieros (Subt. 29)': '#06b6d4',
            '👥 Personal y Sueldos (Subt. 21)': '#3b82f6',
            '📦 Bienes y Servicios (Subt. 22)': '#8b5cf6',
            '🛡️ Seguridad Social (Subt. 23)': '#ec4899',
            '🤝 Transferencias y Subsidios (Subt. 24)': '#f59e0b',
            '💳 Deuda Pública (Subt. 34)': '#64748b',
            '📑 Otros Subtítulos': '#94a3b8'
        }

        # Totales por ministerio y pivot para la barra 100%
        pivot_vig_e4 = df_e4_subts.pivot_table(index='min_short', columns='macro_categoria', values='vigente_mm', aggfunc='sum', fill_value=0.0)
        tot_vig_by_min = pivot_vig_e4.sum(axis=1)
        pivot_pct_e4 = pivot_vig_e4.div(tot_vig_by_min, axis=0) * 100

        # Totales agregados a nivel país para KPIs
        macro_totals = df_e4_subts.groupby('macro_categoria')['vigente_mm'].sum()
        total_pais_vig = df_e4_subts['vigente_mm'].sum()
        pct_inv_pais = (macro_totals.get('🏗️ Inversión Real y Obras (Subt. 31)', 0.0) / total_pais_vig * 100) if total_pais_vig > 0 else 0.0
        pct_pers_pais = (macro_totals.get('👥 Personal y Sueldos (Subt. 21)', 0.0) / total_pais_vig * 100) if total_pais_vig > 0 else 0.0

        # Identificar líderes para las tarjetas KPI
        top_inv_name = pivot_pct_e4['🏗️ Inversión Real y Obras (Subt. 31)'].idxmax() if '🏗️ Inversión Real y Obras (Subt. 31)' in pivot_pct_e4.columns else "N/A"
        top_inv_val = pivot_pct_e4.loc[top_inv_name, '🏗️ Inversión Real y Obras (Subt. 31)'] if top_inv_name != "N/A" else 0.0
        top_inv_mm = pivot_vig_e4.loc[top_inv_name, '🏗️ Inversión Real y Obras (Subt. 31)'] if top_inv_name != "N/A" else 0.0

        top_pers_name = pivot_pct_e4['👥 Personal y Sueldos (Subt. 21)'].idxmax() if '👥 Personal y Sueldos (Subt. 21)' in pivot_pct_e4.columns else "N/A"
        top_pers_val = pivot_pct_e4.loc[top_pers_name, '👥 Personal y Sueldos (Subt. 21)'] if top_pers_name != "N/A" else 0.0
        top_pers_mm = pivot_vig_e4.loc[top_pers_name, '👥 Personal y Sueldos (Subt. 21)'] if top_pers_name != "N/A" else 0.0

        # Tarjetas KPI de Calidad del Gasto
        kpi_e4_1, kpi_e4_2, kpi_e4_3, kpi_e4_4 = st.columns(4, gap="small")
        with kpi_e4_1:
            st.metric(
                label="🏗️ Líder en Inversión en Obras (Subt. 31)",
                value=f"{top_inv_name} ({top_inv_val:.1f}%)",
                delta=f"${top_inv_mm:,.1f} MM presupuestados"
            )
        with kpi_e4_2:
            st.metric(
                label="👥 Mayor Proporción en Personal (Subt. 21)",
                value=f"{top_pers_name} ({top_pers_val:.1f}%)",
                delta=f"${top_pers_mm:,.1f} MM en sueldos/honorarios"
            )
        with kpi_e4_3:
            st.metric(
                label=f"🇨🇱 Estructura Presupuestaria ({e4_year})",
                value=f"{pct_inv_pais:.1f}% Obras · {pct_pers_pais:.1f}% Personal",
                delta=f"Total: ${total_pais_vig:,.0f} MM analizados"
            )
        with kpi_e4_4:
            meses_dict = {'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12}
            m_num = meses_dict.get(e4_period, 6)
            exp_pct = (m_num / 12.0) * 100
            df_mins_rank_e4 = db.get_national_ministerios_ranking(year=e4_year, periodo=e4_period, moneda=moneda, exclude_tesoro=exclude_tesoro)
            df_mins_rank_e4['brecha_meta'] = df_mins_rank_e4['pct_ejecucion'] - exp_pct
            df_mins_rank_e4['vigente_mm'] = df_mins_rank_e4['vigente'] * 1000 / 1e9
            df_mins_rank_e4['ejec_mm'] = df_mins_rank_e4['ejecucion'] * 1000 / 1e9
            df_mins_rank_e4['saldo_mm'] = df_mins_rank_e4['saldo'] * 1000 / 1e9
            crit_sub = df_mins_rank_e4[(df_mins_rank_e4['brecha_meta'] <= -12.0) & (df_mins_rank_e4['saldo_mm'] >= 300)]
            tot_crit_saldo = crit_sub['saldo_mm'].sum()
            n_crit = len(crit_sub)
            st.metric(
                label=f"🚨 Subejecución Crítica (Corte {e4_period})",
                value=f"{n_crit} Carteras en Riesgo",
                delta=f"${tot_crit_saldo:,.1f} MM en saldo retrasado",
                delta_color="inverse"
            )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # 3. RENDERIZACIÓN SEGÚN VISTA SELECCIONADA
        if "Anatomía" in e4_mode:
            # Ordenamiento interactivo de los ministerios
            if "Inversión Real" in e4_sort:
                order_col = '🏗️ Inversión Real y Obras (Subt. 31)'
                mins_ordered = pivot_pct_e4[order_col].sort_values(ascending=True).index.tolist() if order_col in pivot_pct_e4.columns else pivot_pct_e4.index.tolist()
            elif "Personal" in e4_sort:
                order_col = '👥 Personal y Sueldos (Subt. 21)'
                mins_ordered = pivot_pct_e4[order_col].sort_values(ascending=True).index.tolist() if order_col in pivot_pct_e4.columns else pivot_pct_e4.index.tolist()
            elif "Transferencias Capital" in e4_sort:
                order_col = '🚜 Transferencias de Capital (Subt. 33)'
                mins_ordered = pivot_pct_e4[order_col].sort_values(ascending=True).index.tolist() if order_col in pivot_pct_e4.columns else pivot_pct_e4.index.tolist()
            elif "Transferencias Corrientes" in e4_sort:
                order_col = '🤝 Transferencias y Subsidios (Subt. 24)'
                mins_ordered = pivot_pct_e4[order_col].sort_values(ascending=True).index.tolist() if order_col in pivot_pct_e4.columns else pivot_pct_e4.index.tolist()
            elif "Mayor Presupuesto" in e4_sort:
                mins_ordered = tot_vig_by_min.sort_values(ascending=True).index.tolist()
            elif "Mayor % Avance" in e4_sort:
                min_ejec_map = df_e4_subts.groupby('min_short').apply(lambda g: (g['ejec_mm'].sum() / g['vigente_mm'].sum() * 100) if g['vigente_mm'].sum() > 0 else 0)
                mins_ordered = min_ejec_map.sort_values(ascending=True).index.tolist()
            else:
                mins_ordered = sorted(pivot_pct_e4.index.tolist(), reverse=True)

            pivot_pct_e4 = pivot_pct_e4.loc[mins_ordered]

            fig_stack_e4 = go.Figure()
            for cat, color in cat_colors_e4.items():
                if cat in pivot_pct_e4.columns and pivot_pct_e4[cat].sum() > 0:
                    y_vals = pivot_pct_e4.index.tolist()
                    x_vals = pivot_pct_e4[cat].tolist()
                    custom_mm = [pivot_vig_e4.loc[m, cat] if (m in pivot_vig_e4.index and cat in pivot_vig_e4.columns) else 0.0 for m in y_vals]
                    
                    fig_stack_e4.add_trace(go.Bar(
                        y=y_vals,
                        x=x_vals,
                        name=cat,
                        orientation='h',
                        marker=dict(color=color),
                        customdata=custom_mm,
                        hovertemplate="<b>%{y}</b><br>" + cat + "<br>Proporción: %{x:.1f}%<br>Monto: $%{customdata:,.1f} MM<extra></extra>"
                    ))

            fig_stack_e4.update_layout(
                barmode='stack',
                paper_bgcolor='#ffffff',
                plot_bgcolor='#ffffff',
                height=max(540, len(mins_ordered) * 23),
                autosize=True,
                margin=dict(l=10, r=20, t=35, b=30),
                xaxis=dict(
                    title="Distribución Porcentual del Presupuesto Vigente (%)",
                    range=[0, 100],
                    ticksuffix="%",
                    gridcolor='#f1f5f9',
                    linecolor='#cbd5e1'
                ),
                yaxis=dict(
                    title="",
                    tickfont=dict(size=10.5, color='#0f172a'),
                    categoryorder='array',
                    categoryarray=mins_ordered
                ),
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='center',
                    x=0.5,
                    font=dict(size=10.5)
                )
            )
            st.plotly_chart(fig_stack_e4, use_container_width=True)

        elif "Treemap" in e4_mode:
            metric_col_map = {
                "Presupuesto Vigente ($ MM)": "vigente_mm",
                "Ejecución Devengada ($ MM)": "ejec_mm",
                "Saldo Disponible ($ MM)": "saldo_mm"
            }
            val_col_tree = metric_col_map.get(e4_tree_metric, "vigente_mm")
            df_tree_data = df_e4_subts[df_e4_subts[val_col_tree] > 0.5].copy()
            df_tree_data['pct_ejec_color'] = df_tree_data['pct_ejecucion'].clip(0, 100)

            fig_tree_e4 = px.treemap(
                df_tree_data,
                path=['min_short', 'macro_categoria'],
                values=val_col_tree,
                color='pct_ejec_color',
                color_continuous_scale='Tealgrn',
                range_color=[0, 100],
                labels={
                    val_col_tree: e4_tree_metric,
                    'pct_ejec_color': '% Avance (0-100%)',
                    'pct_ejecucion': '% Avance Real',
                    'min_short': 'Ministerio',
                    'macro_categoria': 'Naturaleza del Gasto'
                },
                hover_name='subtitulo_nom',
                hover_data={
                    'min_short': True,
                    'macro_categoria': True,
                    val_col_tree: ':,.1f',
                    'pct_ejecucion': ':.1f',
                    'pct_ejec_color': False
                }
            )
            fig_tree_e4.update_traces(
                textinfo="label+value+percent parent",
                marker=dict(cornerradius=3)
            )
            fig_tree_e4.update_layout(
                paper_bgcolor='#ffffff',
                plot_bgcolor='#ffffff',
                height=560,
                autosize=True,
                margin=dict(l=10, r=10, t=30, b=20),
                coloraxis_colorbar=dict(title="% Avance", thickness=14, len=0.8, ticksuffix="%")
            )
            st.plotly_chart(fig_tree_e4, use_container_width=True)

        else: # 🚨 Matriz de Riesgo de Subejecución
            df_risk_plot = df_mins_rank_e4.copy()
            df_risk_plot['min_short'] = df_risk_plot['ministerio'].apply(clean_min_name)
            df_risk_plot['meta_teorica'] = exp_pct
            df_risk_plot['burbuja_tamano'] = df_risk_plot['vigente_mm'].clip(lower=15.0)

            def clasif_nivel_e4(r):
                brecha = r['brecha_meta']
                saldo = r['saldo_mm']
                if brecha <= -12.0 and saldo >= 300:
                    return '🚨 Riesgo Crítico'
                elif brecha < -5.0:
                    return '⚠️ Alerta Amarilla'
                elif brecha <= 5.0:
                    return '✅ Ritmo Óptimo'
                else:
                    return '⚡ Acelerado'

            df_risk_plot['riesgo_nivel'] = df_risk_plot.apply(clasif_nivel_e4, axis=1)

            if e4_risk_filter != "Todos los Niveles":
                df_risk_plot = df_risk_plot[df_risk_plot['riesgo_nivel'] == e4_risk_filter]

            risk_palette = {
                '🚨 Riesgo Crítico': '#ef4444',
                '⚠️ Alerta Amarilla': '#f59e0b',
                '✅ Ritmo Óptimo': '#10b981',
                '⚡ Acelerado': '#2563eb'
            }

            fig_risk = px.scatter(
                df_risk_plot,
                x='saldo_mm',
                y='brecha_meta',
                size='burbuja_tamano',
                color='riesgo_nivel',
                color_discrete_map=risk_palette,
                text='min_short',
                labels={
                    'saldo_mm': f'Saldo Disponible por Gastar ($ MM - Corte {e4_period})',
                    'brecha_meta': f'Brecha respecto a Meta del Mes ({exp_pct:.1f}%) [Puntos %]',
                    'vigente_mm': 'Presupuesto Vigente ($ MM)',
                    'burbuja_tamano': 'Tamaño Presupuestario ($ MM)',
                    'riesgo_nivel': 'Nivel de Riesgo'
                },
                hover_name='ministerio',
                hover_data={
                    'min_short': False,
                    'burbuja_tamano': False,
                    'saldo_mm': ':,.1f',
                    'brecha_meta': ':+.1f',
                    'pct_ejecucion': ':.1f',
                    'vigente_mm': ':,.1f'
                }
            )

            fig_risk.update_traces(
                textposition='top right',
                textfont=dict(size=10.5, color='#0f172a', family='sans-serif'),
                marker=dict(line=dict(width=1, color='#ffffff'), opacity=0.88)
            )

            fig_risk.add_hline(y=0, line_dash='dash', line_color='#94a3b8', line_width=1.5, annotation_text=f"Meta Teórica {e4_period} ({exp_pct:.1f}%)", annotation_position="top left")

            fig_risk.update_layout(
                paper_bgcolor='#ffffff',
                plot_bgcolor='#ffffff',
                height=520,
                autosize=True,
                hovermode="closest",
                hoverdistance=60,
                margin=dict(l=20, r=20, t=35, b=40),
                xaxis=dict(gridcolor='#f1f5f9', linecolor='#cbd5e1', tickprefix='$ ', ticksuffix=' MM'),
                yaxis=dict(gridcolor='#f1f5f9', linecolor='#cbd5e1', ticksuffix='%'),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=10.5))
            )
            st.plotly_chart(fig_risk, use_container_width=True)

        # 4. Tabla Plegable y Descarga CSV
        with st.expander(f"📋 Ver Datos Detallados de Radiografía Presupuestaria ({e4_year} · Corte {e4_period})"):
            df_e4_export = df_e4_subts[[
                'ministerio', 'subtitulo_cod', 'subtitulo_nom', 'macro_categoria', 'vigente_mm', 'ejec_mm', 'saldo_mm', 'pct_ejecucion'
            ]].copy()
            df_e4_export.columns = [
                'Ministerio', 'Cód. Subt.', 'Nombre Subtítulo', 'Macro Categoría',
                'Presupuesto Vigente ($ MM)', 'Ejecución Devengada ($ MM)', 'Saldo Disponible ($ MM)', '% Avance'
            ]
            st.dataframe(
                df_e4_export.style.format({
                    'Presupuesto Vigente ($ MM)': '${:,.1f}',
                    'Ejecución Devengada ($ MM)': '${:,.1f}',
                    'Saldo Disponible ($ MM)': '${:,.1f}',
                    '% Avance': '{:.1f}%'
                }),
                use_container_width=True,
                height=350
            )

            csv_e4 = df_e4_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Descargar Radiografía Presupuestaria ({e4_year}) en CSV",
                data=csv_e4,
                file_name=f"radiografia_presupuestaria_{e4_year}_{e4_period}.csv",
                mime="text/csv",
                key="btn_download_e4_csv"
            )
    else:
        st.info(f"No hay datos de desglose por subtítulo disponibles para el año {e4_year} y corte '{e4_period}'.")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # ==============================================================================
    # 6. TOPS DE BARRAS (VIGENTE VS DEVENGADO & INVERSIÓN)
    # ==============================================================================
    st.markdown("---")
    if "Capital" in scope:
        sort_metric = "capital_vigente" if "Vigente" in sort_by else ("capital_ejecucion" if "Ejecución" in sort_by else "pct_capital")
    elif "31" in scope:
        sort_metric = "subt31_vigente" if "Vigente" in sort_by else ("subt31_ejecucion" if "Ejecución" in sort_by else "pct_subt31")
    else:
        if "Ejecución Acumulada" in sort_by:
            sort_metric = "ejecucion"
        elif "% Avance Presupuestario" in sort_by:
            sort_metric = "pct_ejecucion"
        elif "Inversión Subt. 31" in sort_by:
            sort_metric = "subt31_vigente"
        elif "Saldo Disponible" in sort_by:
            sort_metric = "saldo"
        else:
            sort_metric = "vigente"

    is_asc = "Menor a mayor" in sort_by
    df_sorted = df_mins_filtered.sort_values(by=sort_metric, ascending=is_asc).reset_index(drop=True)
    df_top = df_sorted.head(top_n).copy()
    df_top_rev = df_top.iloc[::-1].copy()

    c_top1, c_top2 = st.columns([5.2, 4.8], gap="medium")
    with c_top1:
        st.markdown(f"##### 📊 Top Ministerios por Presupuesto y Ejecución ({len(df_top)})")
        st.caption(f"Comparación de Presupuesto Vigente vs. Ejecución Devengada · Orden: {sort_by}")
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            y=df_top_rev["ministerio"].apply(lambda m: format_prog_label(clean_min_name(m), 32)),
            x=df_top_rev["vigente"] * 1000 / 1e9,
            name="Presupuesto Vigente",
            orientation="h",
            marker=dict(color="#2563eb", cornerradius=4),
            customdata=df_top_rev["pct_ejecucion"],
            hovertemplate="<b>%{y}</b><br>Vigente: $%{x:,.1f} MM<br>Avance: %{customdata:.1f}%<extra></extra>"
        ))
        fig_bar.add_trace(go.Bar(
            y=df_top_rev["ministerio"].apply(lambda m: format_prog_label(clean_min_name(m), 32)),
            x=df_top_rev["ejecucion"] * 1000 / 1e9,
            name="Ejecución Devengada",
            orientation="h",
            marker=dict(color="#10b981", cornerradius=4),
            customdata=df_top_rev["saldo"] * 1000 / 1e9,
            hovertemplate="<b>%{y}</b><br>Ejecutado: $%{x:,.1f} MM<br>Saldo: $%{customdata:,.1f} MM<extra></extra>"
        ))
        fig_bar.update_layout(
            barmode="group",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            height=440,
            autosize=True,
            margin=dict(l=15, r=20, t=30, b=35),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
            xaxis=dict(title="Monto ($ Miles de Millones - MM)", gridcolor="#f1f5f9", tickformat=",.0f"),
            yaxis=dict(gridcolor="#f1f5f9", tickfont=dict(size=10.5))
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c_top2:
        st.markdown(f"##### 🏗️ Ranking de Inversión y Capital (Subt. 29, 31, 33)")
        st.caption("Composición de Gasto en Infraestructura (Subt. 31) vs. Otros Activos y Transferencias Capital")
        df_inv_top = df_mins_filtered.sort_values(by="capital_vigente", ascending=False).head(top_n).iloc[::-1].copy()
        df_inv_top["otros_capital_vig"] = (df_inv_top["capital_vigente"] - df_inv_top["subt31_vigente"]).clip(lower=0)

        fig_inv = go.Figure()
        fig_inv.add_trace(go.Bar(
            y=df_inv_top["ministerio"].apply(lambda m: format_prog_label(clean_min_name(m), 32)),
            x=df_inv_top["subt31_vigente"] * 1000 / 1e9,
            name="Subt. 31 (Inversión Real)",
            orientation="h",
            marker=dict(color="#d97706", cornerradius=4),
            customdata=df_inv_top["pct_subt31"],
            hovertemplate="<b>%{y}</b><br>Subt. 31 Vigente: $%{x:,.1f} MM<br>Avance Obras: %{customdata:.1f}%<extra></extra>"
        ))
        fig_inv.add_trace(go.Bar(
            y=df_inv_top["ministerio"].apply(lambda m: format_prog_label(clean_min_name(m), 32)),
            x=df_inv_top["otros_capital_vig"] * 1000 / 1e9,
            name="Subt. 29 y 33 (Otros Capital)",
            orientation="h",
            marker=dict(color="#3b82f6", cornerradius=4),
            customdata=df_inv_top["pct_capital"],
            hovertemplate="<b>%{y}</b><br>Otros Capital: $%{x:,.1f} MM<br>Avance Capital Global: %{customdata:.1f}%<extra></extra>"
        ))
        fig_inv.update_layout(
            barmode="stack",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            height=440,
            autosize=True,
            margin=dict(l=15, r=20, t=30, b=35),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
            xaxis=dict(title="Monto ($ Miles de Millones - MM)", gridcolor="#f1f5f9", tickformat=",.0f"),
            yaxis=dict(gridcolor="#f1f5f9", tickfont=dict(size=10.5))
        )
        st.plotly_chart(fig_inv, use_container_width=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # ==============================================================================
    # 7. PROGRAMAS Y SUBTÍTULOS NACIONALES
    # ==============================================================================
    c_p1, c_p2 = st.columns([5.2, 4.8], gap="medium")
    with c_p1:
        st.markdown("##### 🏛️ Top 10 Servicios y Programas Más Grandes de Todo Chile")
        st.caption("Organismos del Estado con mayor presupuesto vigente asignado a nivel nacional")
        df_top_progs = db.get_national_top_programas(
            year=year,
            periodo=periodo,
            moneda=moneda,
            top_n=10,
            exclude_tesoro=exclude_tesoro,
            ministerios=filter_mins if filter_mins else None
        )
        if not df_top_progs.empty:
            df_progs_rev = df_top_progs.iloc[::-1].copy()
            fig_progs = go.Figure()
            fig_progs.add_trace(go.Bar(
                y=df_progs_rev["programa"].apply(lambda p: format_prog_label(p, 32)),
                x=df_progs_rev["vigente"] * 1000 / 1e9,
                orientation="h",
                marker=dict(
                    color=df_progs_rev["pct_ejecucion"],
                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(title="% Devengo", thickness=12, len=0.8, ticksuffix="%"),
                    cornerradius=4
                ),
                customdata=df_progs_rev[["ministerio", "ejecucion", "pct_ejecucion"]],
                hovertemplate="<b>%{y}</b><br>Ministerio: %{customdata[0]}<br>Vigente: $%{x:,.1f} MM<br>Avance: %{customdata[2]:.1f}%<extra></extra>"
            ))
            fig_progs.update_layout(
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                height=440,
                autosize=True,
                margin=dict(l=15, r=20, t=30, b=35),
                xaxis=dict(title="Presupuesto Vigente ($ Miles de Millones - MM)", gridcolor="#f1f5f9", tickformat=",.0f"),
                yaxis=dict(gridcolor="#f1f5f9", tickfont=dict(size=10.5))
            )
            st.plotly_chart(fig_progs, use_container_width=True)
        else:
            st.info("No se encontraron programas disponibles para este corte.")

    with c_p2:
        st.markdown("##### 🍩 Distribución del Gasto Público Nacional por Subtítulo")
        st.caption("Estructura económica del presupuesto consolidado del Estado (en %)")
        df_subts = db.get_national_subtitulos_breakdown(
            year=year,
            periodo=periodo,
            moneda=moneda,
            exclude_tesoro=exclude_tesoro,
            ministerios=filter_mins if filter_mins else None
        )
        if not df_subts.empty:
            fig_donut = px.pie(
                df_subts,
                names="subtitulo_nom",
                values="vigente",
                hole=0.52,
                color_discrete_sequence=['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899', '#f97316', '#64748b', '#6366f1']
            )
            fig_donut.update_traces(
                textposition="inside",
                textinfo="percent",
                hovertemplate="<b>%{label}</b><br>Monto Vigente: $%{value:,.0f} M$<br>Participación: %{percent}<extra></extra>"
            )
            fig_donut.update_layout(
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                height=440,
                autosize=True,
                margin=dict(l=15, r=15, t=25, b=25),
                legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5, font=dict(size=9.5))
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No se encontraron subtítulos para este corte.")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # ==============================================================================
    # 8. MATRIZ RANKING INTERMINISTERIAL COMPLETA CON EXPORTACIÓN
    # ==============================================================================
    st.markdown("---")
    st.markdown("##### 📑 Matriz Ranking Interministerial Completa")
    st.caption("Detalle exhaustivo de todas las carteras ministeriales con indicadores de volumen, avance y esfuerzo inversor.")

    df_matrix = df_sorted.copy()
    df_matrix.insert(0, "Ranking", [f"#{i+1}" for i in range(len(df_matrix))])
    
    df_display = pd.DataFrame({
        "Ranking": df_matrix["Ranking"],
        "Ministerio": df_matrix["ministerio"],
        "Presupuesto Inicial ($ MM)": df_matrix["inicial"] * 1000 / 1e9,
        "Presupuesto Vigente ($ MM)": df_matrix["vigente"] * 1000 / 1e9,
        "Ejecución Devengada ($ MM)": df_matrix["ejecucion"] * 1000 / 1e9,
        "Saldo Disponible ($ MM)": df_matrix["saldo"] * 1000 / 1e9,
        "% Avance": df_matrix["pct_ejecucion"],
        "Inversión Subt. 31 ($ MM)": df_matrix["subt31_vigente"] * 1000 / 1e9,
        "% Inversión en Total": df_matrix["pct_share_inv"]
    })

    col_exp1, col_exp2, col_exp_spacer = st.columns([2, 2, 6])
    with col_exp1:
        ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        excel_path = config.EXPORTS_DIR / f"ranking_nacional_ministerios_{year}_{ts}.xlsx"
        df_matrix.to_excel(excel_path, index=False)
        with open(excel_path, "rb") as f:
            st.download_button(
                "⬇️ Descargar Ranking (Excel)",
                data=f.read(),
                file_name=excel_path.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    with col_exp2:
        csv_data = df_matrix.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "⬇️ Descargar Ranking (CSV)",
            data=csv_data,
            file_name=f"ranking_nacional_ministerios_{year}_{ts}.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.dataframe(
        df_display.style.format({
            "Presupuesto Inicial ($ MM)": "${:,.1f} MM",
            "Presupuesto Vigente ($ MM)": "${:,.1f} MM",
            "Ejecución Devengada ($ MM)": "${:,.1f} MM",
            "Saldo Disponible ($ MM)": "${:,.1f} MM",
            "% Avance": "{:.1f}%",
            "Inversión Subt. 31 ($ MM)": "${:,.1f} MM",
            "% Inversión en Total": "{:.2f}%"
        }),
        use_container_width=True,
        height=480
    )

# ==============================================================================
# SIDEBAR DE FILTROS DINÁMICOS
# ==============================================================================
with st.sidebar:
    st.markdown("### 🏛️ DIPRES · Presupuesto")
    st.caption("Dirección de Presupuestos · Chile")
    
    # 🌐 Enlace Online Público (Cloudflare Tunnel) si está habilitado
    try:
        from src.tunnel_manager import get_active_url, start_tunnel
        active_tunnel_url = get_active_url()
        if active_tunnel_url:
            st.markdown(f"""
            <div style="background-color: #f0fdf4; border: 1.5px solid #86efac; border-radius: 8px; padding: 7px 10px; margin: 4px 0 10px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.70rem; font-weight: 700; color: #166534; display: flex; align-items: center; gap: 5px;">
                        <span style="display: inline-block; width: 7px; height: 7px; background-color: #22c55e; border-radius: 50%;"></span>
                        EN LÍNEA (INTERNET)
                    </span>
                    <span style="font-size: 0.60rem; background-color: #dcfce7; color: #15803d; padding: 1px 6px; border-radius: 9999px; font-weight: 700;">Activo</span>
                </div>
                <a href="{active_tunnel_url}" target="_blank" style="font-size: 0.73rem; color: #15803d; font-weight: 600; text-decoration: underline; word-break: break-all; display: block; margin-top: 3px;">
                    🔗 {active_tunnel_url}
                </a>
                <div style="font-size: 0.64rem; color: #64748b; margin-top: 2px;">
                    Enlace público seguro para compartir o ver en celular.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            with st.expander("🌐 Compartir en línea (Túnel)", expanded=False):
                st.caption("Genera un enlace público HTTPS para que cualquiera acceda desde internet.")
                if st.button("Activar Enlace Online", key="btn_activate_online", use_container_width=True):
                    with st.spinner("Conectando con Cloudflare Tunnel..."):
                        new_online_url = start_tunnel(8501)
                        if new_online_url:
                            st.success("¡Enlace online generado!")
                            st.rerun()
                        else:
                            st.error("No se pudo generar el túnel online.")
    except Exception:
        pass
    
    # 1. Selector de Año (2000 a 2026) y Moneda
    c_yr, c_mon = st.columns(2)
    with c_yr:
        sorted_years = sorted(list(config.YEAR_IDS.keys()), reverse=True)
        selected_year = st.selectbox("Año", options=sorted_years, index=0)
    with c_mon:
        selected_currency = st.selectbox("Moneda", ["Pesos", "Dólares"], index=0)

    st.markdown(f"""
    <div style="margin-top: 4px; margin-bottom: 8px;">
        <span class="year-pill-sidebar">
            <span style="font-weight: 500;">📅 Año Activo:</span>
            <b style="margin-left: 6px; font-size: 1.05rem;">{selected_year}</b>
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Selector de Modo / Ventana de Análisis
    nav_view_mode = st.radio(
        "🪟 Ventana de Análisis:",
        options=["🏛️ Detalle por Ministerio", "🏆 Rankings & Tops Nacionales"],
        index=0,
        key="sb_nav_view_mode"
    )
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    scraper = get_scraper(selected_year)
    all_mins = scraper.get_ministerios()

    if nav_view_mode == "🏛️ Detalle por Ministerio":
        # 2. Selector Dinámico de Ministerio con Persistencia
        if "saved_ministerio" not in st.session_state:
            st.session_state["saved_ministerio"] = next((m for m in all_mins if "Obras" in m), all_mins[0])
            
        target_min = st.session_state.get("saved_ministerio", "")
        if target_min in all_mins:
            min_idx = all_mins.index(target_min)
        else:
            matches = [i for i, m in enumerate(all_mins) if target_min[:15].lower() in m.lower()]
            min_idx = matches[0] if matches else next((i for i, m in enumerate(all_mins) if "Obras" in m), 0)

        def on_min_change():
            st.session_state["saved_ministerio"] = st.session_state["sb_min_widget"]

        selected_min = st.selectbox(
            "Ministerio / Partida",
            options=all_mins,
            index=min_idx,
            key="sb_min_widget",
            on_change=on_min_change
        )
        st.session_state["saved_ministerio"] = selected_min
        
        # 3. Periodo de Análisis Dinámico con Persistencia (Ubicado estratégicamente arriba de Servicios)
        avail_periods = scraper.get_periodos(selected_min)
        if "saved_period" not in st.session_state:
            st.session_state["saved_period"] = "Junio" if "Junio" in avail_periods else ("Segundo Trimestre" if "Segundo Trimestre" in avail_periods else (avail_periods[-1] if avail_periods else None))
            
        target_per = st.session_state.get("saved_period", "")
        if target_per in avail_periods:
            per_idx = avail_periods.index(target_per)
        elif "Junio" in avail_periods:
            per_idx = avail_periods.index("Junio")
        elif "Segundo Trimestre" in avail_periods:
            per_idx = avail_periods.index("Segundo Trimestre")
        else:
            per_idx = 0 if avail_periods else 0

        def on_per_change():
            st.session_state["saved_period"] = st.session_state["sb_per_widget"]

        selected_period = st.selectbox(
            "Periodo de Análisis",
            options=avail_periods,
            index=per_idx,
            key="sb_per_widget",
            on_change=on_per_change
        )
        st.session_state["saved_period"] = selected_period

        st.markdown("---")
        
        # 4. FILTROS DINÁMICOS ADAPTADOS A LA INFORMACIÓN SCRAPEADA
        all_progs = scraper.get_programas(selected_min)
        total_progs_count = len(all_progs)
        
        # Obtener programas que ya están descargados en BD para este ministerio
        df_prog_db = db.get_programas_comparison(
            year=selected_year,
            ministerio=selected_min,
            periodo=selected_period,
            moneda=selected_currency
        )
        
        progs_with_data = []
        top_progs = []
        if not df_prog_db.empty:
            progs_with_data = df_prog_db["programa"].tolist()
            top_progs = df_prog_db.sort_values(by="vigente", ascending=False)["programa"].head(5).tolist()
        else:
            top_progs = all_progs[:5]
            
        st.markdown(f"**Servicios ({total_progs_count} disponibles)**")
        
        # Opciones dinámicas según los datos disponibles
        opciones_modo = [
            f"📋 Todos los servicios ({total_progs_count})",
            f"🔝 Top 5 con mayor presupuesto",
            "✏️ Selección personalizada"
        ]
        if progs_with_data and len(progs_with_data) < total_progs_count:
            opciones_modo.insert(2, f"💾 Con datos en BD ({len(progs_with_data)})")

        modo_filtro = st.radio(
            "Modo de selección:",
            options=opciones_modo,
            index=0,
            label_visibility="collapsed"
        )
        
        # Determinar selección según modo dinámico
        if "Todos" in modo_filtro:
            pre_selected = all_progs
        elif "Top 5" in modo_filtro:
            pre_selected = [p for p in top_progs if p in all_progs]
        elif "Con datos" in modo_filtro:
            pre_selected = [p for p in all_progs if p in progs_with_data]
        else:
            # Selección personalizada inicial
            pre_selected = [p for p in top_progs if p in all_progs] if top_progs else all_progs[:3]

        # Botones rápidos de selección
        col_btn_all, col_btn_clear = st.columns(2)
        with col_btn_all:
            if st.button("Marcar Todos", use_container_width=True):
                st.session_state[f"progs_{selected_min}"] = all_progs
        with col_btn_clear:
            if st.button("Limpiar", use_container_width=True):
                st.session_state[f"progs_{selected_min}"] = []

        # Estado de sesión para multiselect
        current_selected = st.session_state.get(f"progs_{selected_min}", pre_selected)
        # Validar que los seleccionados pertenezcan al ministerio actual
        current_selected = [p for p in current_selected if p in all_progs]
        if not current_selected and "Todos" in modo_filtro:
            current_selected = all_progs

        selected_progs = st.multiselect(
            "Servicios activos:",
            options=all_progs,
            default=current_selected if current_selected else (pre_selected if pre_selected else all_progs),
            label_visibility="collapsed"
        )
        
        # Salvaguarda: si no hay ninguno seleccionado, activar todos
        if not selected_progs:
            selected_progs = all_progs

    else:
        # CONTROLES PARA LA VENTANA DE RANKINGS Y TOPS NACIONALES
        nat_view_focus = st.radio(
            "Enfoque Temporal:",
            options=["📅 Análisis Anual / Mensual", "📈 Comparativa Multianual (2018-2026)"],
            index=0,
            key="sb_nat_view_focus"
        )

        meses_nombres = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        trimestres_meses = ['Marzo', 'Junio', 'Septiembre', 'Diciembre']
        
        nat_multi_years = [2022, 2023, 2024, 2025, 2026]

        if nat_view_focus == "📈 Comparativa Multianual (2018-2026)":
            c_my1, c_my2, c_my3 = st.columns(3)
            with c_my1:
                if st.button("2018-26", use_container_width=True, key="btn_my_all"):
                    st.session_state["sb_nat_multi_years"] = list(range(2018, 2027))
            with c_my2:
                if st.button("2022-26", use_container_width=True, key="btn_my_recent"):
                    st.session_state["sb_nat_multi_years"] = [2022, 2023, 2024, 2025, 2026]
            with c_my3:
                if st.button("2024-26", use_container_width=True, key="btn_my_tri"):
                    st.session_state["sb_nat_multi_years"] = [2024, 2025, 2026]

            nat_multi_years = st.multiselect(
                "Años a Comparar",
                options=list(range(2018, 2027)),
                default=st.session_state.get("sb_nat_multi_years", [2022, 2023, 2024, 2025, 2026]),
                key="sb_nat_multi_years"
            )
            if not nat_multi_years:
                nat_multi_years = [2024, 2025, 2026]

            avail_nat_periods = ["Junio", "Marzo", "Septiembre", "Diciembre", "Mayo", "Julio"]
            selected_nat_period = st.selectbox(
                "Periodo de Corte Homogéneo",
                options=avail_nat_periods,
                index=0,
                key="sb_nat_multi_period"
            )
        else:
            # ANÁLISIS ANUAL / MENSUAL
            avail_nat_periods = db.get_available_periods_for_year(selected_year, selected_currency)
            if not avail_nat_periods:
                avail_nat_periods = ["Junio", "Marzo", "Mayo", "Abril"]

            nat_per_filter_type = st.radio(
                "Filtrar Tipo de Periodo:",
                options=["Todos los Meses (12 Meses)", "📊 Cortes Trimestrales (Mar, Jun, Sep, Dic)", "📅 Meses Regulares"],
                index=0,
                horizontal=True,
                key="sb_nat_per_filter_type"
            )

            filtered_periods = avail_nat_periods
            if nat_per_filter_type == "📊 Cortes Trimestrales (Mar, Jun, Sep, Dic)":
                filtered_periods = [p for p in avail_nat_periods if p in trimestres_meses]
                if not filtered_periods:
                    filtered_periods = avail_nat_periods
            elif nat_per_filter_type == "📅 Meses Regulares":
                filtered_periods = [p for p in avail_nat_periods if p not in trimestres_meses]
                if not filtered_periods:
                    filtered_periods = avail_nat_periods

            nat_per_idx = filtered_periods.index("Junio") if "Junio" in filtered_periods else (len(filtered_periods)-1 if filtered_periods else 0)
            
            selected_nat_period = st.selectbox(
                "Periodo de Análisis (Corte)",
                options=filtered_periods,
                index=nat_per_idx,
                key="sb_nat_period"
            )

        # Más Filtros: Estrato Presupuestario y Rango de Avance
        c_filt1, c_filt2 = st.columns(2)
        with c_filt1:
            nat_estrato = st.selectbox(
                "Estrato Presupuestario",
                options=[
                    "Todos los Tamaños",
                    "🏛️ Grandes (> $5.000 MM)",
                    "🏢 Medianas ($1.000 - $5.000 MM)",
                    "🎯 Focalizadas (< $1.000 MM)"
                ],
                index=0,
                key="sb_nat_estrato"
            )
        with c_filt2:
            nat_rango_avance = st.selectbox(
                "Rango de Avance",
                options=[
                    "Cualquier Avance",
                    "🟢 Alto (> 50%)",
                    "🟡 Regular (35% - 50%)",
                    "🔴 Rezagados (< 35%)"
                ],
                index=0,
                key="sb_nat_rango_avance"
            )

        nat_scope = st.selectbox(
            "Alcance Presupuestario",
            options=[
                "Presupuesto Total (Todos los Subtítulos)",
                "Inversión y Capital (Subt. 29, 31, 33)",
                "Solo Iniciativas de Inversión (Subt. 31)"
            ],
            index=0,
            key="sb_nat_scope"
        )
        
        nat_sort_by = st.selectbox(
            "Ordenar Rankings Por",
            options=[
                "Presupuesto Vigente (Mayor a menor)",
                "Ejecución Acumulada (Mayor a menor)",
                "% Avance Presupuestario (Mayor a menor)",
                "% Avance Presupuestario (Menor a mayor - Rezagados)",
                "Inversión Subt. 31 Obras (Mayor a menor)",
                "Saldo Disponible (Mayor a menor)"
            ],
            index=0,
            key="sb_nat_sort_by"
        )
        
        nat_top_n_str = st.selectbox(
            "Mostrar Top",
            options=["Top 5", "Top 10", "Top 15", "Top 20", "Todos los Ministerios (33)"],
            index=1,
            key="sb_nat_top_n"
        )
        nat_top_n_map = {"Top 5": 5, "Top 10": 10, "Top 15": 15, "Top 20": 20, "Todos los Ministerios (33)": 999}
        nat_top_n = nat_top_n_map.get(nat_top_n_str, 10)
        
        nat_exclude_tesoro = st.checkbox(
            "Excluir Tesoro Público",
            value=True,
            key="sb_nat_exclude_tesoro",
            help="Tesoro Público agrupa transferencias globales y servicio de la deuda. Excluirlo permite comparar equitativamente la gestión sectorial de los ministerios."
        )
        
        nat_filter_mins = st.multiselect(
            "Filtrar Ministerios Específicos",
            options=all_mins,
            default=[],
            key="sb_nat_filter_mins",
            placeholder="Todos los ministerios (sin filtro)"
        )
        
        # Fallbacks para variables requeridas en contexto global
        selected_min = all_mins[0] if all_mins else ""
        selected_period = selected_nat_period
        selected_progs = []
        total_progs_count = 0

    st.markdown("---")
    db_summary = db.get_processed_reports_summary()
    total_informes_db = int(db_summary["total_informes"].sum()) if not db_summary.empty else 0
    st.caption(f"📦 Base de Datos: **{total_informes_db}** informes en disco")

# ==============================================================================
# VISTA PRINCIPAL SEGÚN MODO SELECCIONADO
# ==============================================================================
if nav_view_mode == "🏆 Rankings & Tops Nacionales":
    render_national_tops_view(
        year=selected_year,
        moneda=selected_currency,
        periodo=selected_nat_period,
        view_focus=nat_view_focus,
        multi_years=nat_multi_years,
        estrato=nat_estrato,
        rango_avance=nat_rango_avance,
        scope=nat_scope,
        sort_by=nat_sort_by,
        top_n=nat_top_n,
        exclude_tesoro=nat_exclude_tesoro,
        filter_mins=nat_filter_mins
    )
    st.stop()

# ENCABEZADO PRINCIPAL DE LA PÁGINA (MINISTERIAL)
st.markdown(f"""
<div class="header-box">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
        <div>
            <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap; margin-bottom: 5px;">
                <span class="header-title-text">{selected_min}</span>
                <span class="year-pill-hero">
                    <span class="year-icon">📅</span> Presupuesto {selected_year}
                </span>
            </div>
            <div class="header-sub-text">Periodo de Análisis: <b>{selected_period}</b> · Moneda: <b>{selected_currency}</b></div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
            <span class="pill-badge">🏢 {len(selected_progs)} de {total_progs_count} servicios activos</span>
            <span class="pill-badge" style="background-color: #eff6ff; border-color: #93c5fd; color: #1d4ed8 !important;">🎯 Foco: Subt. 29, 31 y 33</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Pestañas principales
tab_dashboard, tab_inversion, tab_comparativa, tab_rankings, tab_catalogo, tab_database = st.tabs([
    "📊 Resumen Ejecutivo",
    "🏗️ Inversión y Capital (Subt. 29, 31, 33)",
    "📈 Comparativa Histórica",
    "🏆 Rankings & Tops Nacionales",
    "🌐 Catálogo & Scraper DIPRES",
    "📑 Base de Datos Consolidada"
])

# Obtener KPIs seguros
kpis = get_kpis_safe(
    db_inst=db,
    year=selected_year,
    ministerio=selected_min,
    programas=selected_progs,
    periodo=selected_period,
    moneda=selected_currency
)

# ==============================================================================
# TAB 1: RESUMEN EJECUTIVO
# ==============================================================================
with tab_dashboard:
    if kpis["presupuesto_vigente"] == 0:
        st.warning(f"⚠️ No hay datos consolidados en la Base de Datos para el año **{selected_year}**, periodo **{selected_period}** y ministerio **{selected_min}**.")
        st.info("💡 Puedes descargar y procesar los informes oficiales con 1 clic desde la pestaña **'Catálogo & Scraper DIPRES'**.")
    else:
        # 4 Tarjetas de Métricas Ejecutivas de Alto Nivel
        col1, col2, col3, col4 = st.columns(4, gap="small")
        with col1:
            st.markdown(render_kpi_card_html(
                title="Presupuesto Vigente",
                value=format_currency(kpis["presupuesto_vigente"]),
                subtitle=f"Inicial: {format_currency(kpis['presupuesto_inicial'])}",
                icon="🏛️",
                theme="blue",
                badge="Total Anual"
            ), unsafe_allow_html=True)
        with col2:
            st.markdown(render_kpi_card_html(
                title="Ejecución Acumulada",
                value=format_currency(kpis["ejecucion_acumulada"]),
                subtitle=f"Saldo: {format_currency(kpis['saldo'])}",
                icon="⚡",
                theme="green",
                badge=f"{kpis['pct_ejecucion']}% devengado"
            ), unsafe_allow_html=True)
        with col3:
            st.markdown(render_kpi_card_html(
                title="% Avance Presupuestario",
                value=f"{kpis['pct_ejecucion']}%",
                subtitle=f"Ejecutado al {selected_period}",
                icon="🎯",
                theme="indigo",
                progress=kpis['pct_ejecucion'],
                badge="Devengado"
            ), unsafe_allow_html=True)
        with col4:
            st.markdown(render_kpi_card_html(
                title="Gasto en Capital",
                value=format_currency(kpis["capital_ejecucion"]),
                subtitle=f"Vigente: {format_currency(kpis['capital_vigente'])}",
                icon="🏗️",
                theme="amber",
                progress=kpis['pct_capital'],
                badge="Subt. 29+31+33"
            ), unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        
        # Gráficos con fondo blanco puro y colores contrastados (CERO barras negras)
        g1, g2 = st.columns([5.2, 4.8], gap="medium")
        with g1:
            st.markdown("##### 📈 Evolución Acumulada por Periodo")
            df_evol = db.get_monthly_evolution(
                year=selected_year,
                ministerio=selected_min,
                programas=selected_progs,
                moneda=selected_currency
            )
            if not df_evol.empty:
                # Si hay más de 6 servicios, graficar los Top 6 con mayor ejecución para mantener la gráfica nítida
                unique_progs = df_evol["programa"].unique()
                if len(unique_progs) > 6:
                    top_progs_evol = df_evol.groupby("programa")["ejecucion"].max().nlargest(6).index.tolist()
                    df_evol_plot = df_evol[df_evol["programa"].isin(top_progs_evol)].copy()
                else:
                    df_evol_plot = df_evol

                fig_evol = px.line(
                    df_evol_plot,
                    x="periodo",
                    y="ejecucion",
                    color="programa",
                    markers=True,
                    labels={"ejecucion": "Ejecución Acumulada (M$)", "periodo": "Periodo", "programa": "Servicio"},
                    color_discrete_sequence=['#2563eb', '#059669', '#d97706', '#7c3aed', '#db2777', '#0891b2']
                )
                fig_evol.update_traces(line=dict(width=3), marker=dict(size=7))
                fig_evol.update_layout(
                    paper_bgcolor="#ffffff",
                    plot_bgcolor="#ffffff",
                    autosize=True,
                    font=dict(color="#1e293b", family="sans-serif", size=10.5),
                    margin=dict(l=55, r=25, t=30, b=55, autoexpand=True),
                    hovermode="x unified",
                    hoverlabel=dict(bgcolor="#ffffff", font_color="#0f172a", bordercolor="#cbd5e1"),
                    legend=dict(orientation="h", y=-0.22, title_text="", font=dict(color="#1e293b", size=9.5)),
                    xaxis=dict(
                        automargin=True,
                        tickfont=dict(color="#475569", size=10),
                        gridcolor="#f1f5f9",
                        showline=True,
                        linecolor="#cbd5e1"
                    ),
                    yaxis=dict(
                        automargin=True,
                        tickfont=dict(color="#475569", size=10),
                        gridcolor="#f1f5f9",
                        showline=True,
                        linecolor="#cbd5e1",
                        tickprefix="$ "
                    )
                )
                st.plotly_chart(fig_evol, use_container_width=True, theme=None, config={"responsive": True, "displayModeBar": True, "autosizable": True})
            else:
                st.caption("No hay datos históricos de evolución disponibles.")

        with g2:
            st.markdown(f"##### 🎨 Gasto por Subtítulo ({selected_period})")
            df_subt = db.get_subtitulos_breakdown(
                year=selected_year,
                ministerio=selected_min,
                programas=selected_progs,
                periodo=selected_period,
                moneda=selected_currency
            )
            if not df_subt.empty:
                fig_pie = px.pie(
                    df_subt[df_subt["vigente"] > 0],
                    names="subtitulo_nom",
                    values="vigente",
                    hole=0.58,
                    color_discrete_sequence=['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#64748b', '#06b6d4', '#ec4899', '#f97316']
                )
                fig_pie.update_layout(
                    paper_bgcolor="#ffffff",
                    plot_bgcolor="#ffffff",
                    autosize=True,
                    font=dict(color="#1e293b", family="sans-serif", size=10),
                    margin=dict(l=20, r=25, t=25, b=25, autoexpand=True),
                    legend=dict(orientation="v", x=1.0, y=0.5, font=dict(color="#1e293b", size=9)),
                    hoverlabel=dict(bgcolor="#ffffff", font_color="#0f172a", bordercolor="#cbd5e1")
                )
                fig_pie.update_traces(
                    textposition='inside',
                    textinfo='percent',
                    textfont=dict(size=10, color="#ffffff"),
                    hovertemplate='<b>%{label}</b><br>Presupuesto Vigente: %{value:$,.0f} M$<br>Participación: %{percent}<extra></extra>'
                )
                st.plotly_chart(fig_pie, use_container_width=True, theme=None, config={"responsive": True, "displayModeBar": True, "autosizable": True})
            else:
                st.caption("No hay datos de subtítulos disponibles.")

        # Tabla de comparación entre programas
        st.markdown("##### 🏢 Desempeño y Saldo por Servicio / Programa")
        df_comp = db.get_programas_comparison(
            year=selected_year,
            ministerio=selected_min,
            programas=selected_progs,
            periodo=selected_period,
            moneda=selected_currency
        )
        if not df_comp.empty:
            st.dataframe(
                df_comp.style.format({
                    "inicial": "{:,.0f}",
                    "vigente": "{:,.0f}",
                    "ejecucion": "{:,.0f}",
                    "saldo": "{:,.0f}",
                    "pct_ejecucion": "{:.2f}%"
                }),
                use_container_width=True
            )

# ==============================================================================
# TAB 2: FOCO INVERSIÓN Y CAPITAL (SUBTÍTULOS 29, 31, 33)
# ==============================================================================
with tab_inversion:
    st.markdown("#### 🏗️ Inversión Pública y Gastos de Capital")
    st.caption("Análisis estratégico de cuentas de capital: Subtítulo 31 (Iniciativas de Inversión), Subtítulo 29 (Activos No Financieros) y Subtítulo 33 (Transferencias de Capital).")
    
    # 4 Tarjetas de Métricas Ejecutivas de Capital
    m1, m2, m3, m4 = st.columns(4, gap="small")
    with m1:
        st.markdown(render_kpi_card_html(
            title="Total Capital (29+31+33)",
            value=format_currency(kpis["capital_ejecucion"]),
            subtitle=f"Vigente: {format_currency(kpis['capital_vigente'])}",
            icon="🏗️",
            theme="blue",
            progress=kpis['pct_capital'],
            badge=f"{kpis['pct_capital']}% avance"
        ), unsafe_allow_html=True)
    with m2:
        st.markdown(render_kpi_card_html(
            title="Subt. 31: Obras e Inversión",
            value=format_currency(kpis["subt31_ejecucion"]),
            subtitle=f"Vigente: {format_currency(kpis['subt31_vigente'])}",
            icon="🚜",
            theme="green",
            progress=kpis['pct_subt31'],
            badge=f"{kpis['pct_subt31']}% avance"
        ), unsafe_allow_html=True)
    with m3:
        st.markdown(render_kpi_card_html(
            title="Subt. 29: Activos No Financ.",
            value=format_currency(kpis["subt29_ejecucion"]),
            subtitle=f"Vigente: {format_currency(kpis['subt29_vigente'])}",
            icon="💻",
            theme="purple",
            progress=kpis['pct_subt29'],
            badge=f"{kpis['pct_subt29']}% avance"
        ), unsafe_allow_html=True)
    with m4:
        st.markdown(render_kpi_card_html(
            title="Subt. 33: Transf. Capital",
            value=format_currency(kpis["subt33_ejecucion"]),
            subtitle=f"Vigente: {format_currency(kpis['subt33_vigente'])}",
            icon="🤝",
            theme="amber",
            progress=kpis['pct_subt33'],
            badge=f"{kpis['pct_subt33']}% avance"
        ), unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    # Selector de subtítulo específico para la vista analítica
    filtro_subt_tab = st.radio(
        "Filtrar desglose por cuenta de capital:",
        options=["Todos (29, 31, 33)", "Subtítulo 31 - Iniciativas de Inversión", "Subtítulo 29 - Activos No Financieros", "Subtítulo 33 - Transferencias de Capital"],
        horizontal=True
    )
    
    subts_query = ["29", "31", "33"]
    if "31" in filtro_subt_tab and "Todos" not in filtro_subt_tab:
        subts_query = ["31"]
    elif "29" in filtro_subt_tab and "Todos" not in filtro_subt_tab:
        subts_query = ["29"]
    elif "33" in filtro_subt_tab and "Todos" not in filtro_subt_tab:
        subts_query = ["33"]

    df_inv = db.get_inversiones_summary(
        year=selected_year,
        ministerio=selected_min,
        programas=selected_progs,
        periodo=selected_period,
        subtitulos=subts_query,
        moneda=selected_currency
    )
    
    if df_inv.empty:
        st.info(f"No hay registros de los subtítulos seleccionados en la Base de Datos para el periodo **{selected_period}**.")
    else:
        df_subts_summary = df_inv[df_inv["nivel"] == "SUBTITULO"]
        
        ig1, ig2 = st.columns([5.2, 4.8], gap="medium")
        with ig1:
            st.markdown("##### 📊 Gasto de Capital por Dirección / Servicio")
            if not df_subts_summary.empty:
                display_labels = [format_prog_label(p, max_len=24) for p in df_subts_summary["programa"]]
                full_prog_names = df_subts_summary["programa"].tolist()
                fig_inv = go.Figure()
                fig_inv.add_trace(go.Bar(
                    name="Presupuesto Vigente",
                    x=display_labels,
                    y=df_subts_summary["vigente"],
                    customdata=full_prog_names,
                    marker_color="#3b82f6",  # Azul Real claro y visible (NO barra negra)
                    hovertemplate="<b>%{customdata}</b><br>Presupuesto Vigente: %{y:$,.0f} M$<extra></extra>"
                ))
                fig_inv.add_trace(go.Bar(
                    name="Ejecución Acumulada",
                    x=display_labels,
                    y=df_subts_summary["ejecucion"],
                    customdata=full_prog_names,
                    marker_color="#10b981",  # Verde Esmeralda vibrante (NO barra negra)
                    hovertemplate="<b>%{customdata}</b><br>Ejecución Acumulada: %{y:$,.0f} M$<extra></extra>"
                ))
                fig_inv.update_layout(
                    paper_bgcolor="#ffffff",
                    plot_bgcolor="#ffffff",
                    barmode="group",
                    autosize=True,
                    font=dict(color="#1e293b", family="sans-serif"),
                    margin=dict(l=75, r=25, t=35, b=110, autoexpand=True),
                    legend=dict(orientation="h", y=1.15, title_text="", font=dict(color="#1e293b", size=11)),
                    hoverlabel=dict(bgcolor="#ffffff", font_color="#0f172a", bordercolor="#cbd5e1"),
                    xaxis=dict(
                        automargin=True,
                        tickangle=-35,
                        tickfont=dict(color="#475569", size=10),
                        gridcolor="#f1f5f9",
                        linecolor="#cbd5e1"
                    ),
                    yaxis=dict(
                        automargin=True,
                        tickfont=dict(color="#475569", size=10),
                        gridcolor="#f1f5f9",
                        linecolor="#cbd5e1",
                        tickprefix="$ "
                    )
                )
                st.plotly_chart(fig_inv, use_container_width=True, theme=None, config={"responsive": True, "displayModeBar": True, "autosizable": True})
                
        with ig2:
            st.markdown("##### ⚖️ Comparativa: Vigente vs Ejecutado")
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(
                name="Presupuesto Vigente",
                y=["Subt. 33 Transf.", "Subt. 29 Activos", "Subt. 31 Inversión"],
                x=[kpis["subt33_vigente"], kpis["subt29_vigente"], kpis["subt31_vigente"]],
                orientation="h",
                marker_color="#3b82f6",  # Azul vibrante
                hovertemplate="<b>%{y}</b><br>Vigente: %{x:$,.0f} M$<extra></extra>"
            ))
            fig_comp.add_trace(go.Bar(
                name="Ejecución Acumulada",
                y=["Subt. 33 Transf.", "Subt. 29 Activos", "Subt. 31 Inversión"],
                x=[kpis["subt33_ejecucion"], kpis["subt29_ejecucion"], kpis["subt31_ejecucion"]],
                orientation="h",
                marker_color="#10b981",  # Verde vibrante
                hovertemplate="<b>%{y}</b><br>Ejecutado: %{x:$,.0f} M$<extra></extra>"
            ))
            fig_comp.update_layout(
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                barmode="group",
                autosize=True,
                font=dict(color="#1e293b", family="sans-serif"),
                margin=dict(l=150, r=35, t=35, b=35, autoexpand=True),
                legend=dict(orientation="h", y=1.2, font=dict(color="#1e293b", size=11)),
                hoverlabel=dict(bgcolor="#ffffff", font_color="#0f172a", bordercolor="#cbd5e1"),
                xaxis=dict(
                    automargin=True,
                    tickfont=dict(color="#475569", size=10),
                    gridcolor="#f1f5f9",
                    linecolor="#cbd5e1",
                    tickprefix="$ "
                ),
                yaxis=dict(
                    automargin=True,
                    tickfont=dict(color="#1e293b", size=11)
                )
            )
            st.plotly_chart(fig_comp, use_container_width=True, theme=None, config={"responsive": True, "displayModeBar": True, "autosizable": True})
            
        st.markdown("##### 📋 Detalle de Cuentas, Proyectos y Estudios de Inversión")
        st.dataframe(
            df_inv[["subtitulo_cod", "subtitulo_nom", "programa", "nivel", "clasificacion", "vigente", "ejecucion", "saldo", "pct_ejecucion"]].style.format({
                "vigente": "{:,.0f}",
                "ejecucion": "{:,.0f}",
                "saldo": "{:,.0f}",
                "pct_ejecucion": "{:.2f}%"
            }),
            use_container_width=True,
            height=400
        )

# ==============================================================================
# TAB 3: COMPARATIVA HISTÓRICA & MULTIANUAL
# ==============================================================================
with tab_comparativa:
    st.markdown("#### 📈 Comparativa Histórica & Tendencia Multianual")
    st.caption(f"Contrasta la evolución presupuestaria, el ritmo de ejecución y los proyectos de inversión para **{selected_min}** a través de una serie de años seleccionable.")

    # 1. Selectores de Años y Periodo de Corte Homogéneo
    col_sel_yr, col_sel_per = st.columns([3, 2])
    
    # Obtener años disponibles en BD para este ministerio
    db_min_years = db.get_available_years_for_ministry(selected_min)
    if not db_min_years:
        db_min_years = sorted([2022, 2023, 2024, 2025, 2026])
    
    # Periodos disponibles para este ministerio y años
    avail_comp_periods = db.get_available_periods_for_ministry_years(selected_min, db_min_years)
    if not avail_comp_periods:
        avail_comp_periods = ["Segundo Trimestre", "Primer Trimestre"]
    
    default_comp_per = selected_period if selected_period in avail_comp_periods else ("Segundo Trimestre" if "Segundo Trimestre" in avail_comp_periods else avail_comp_periods[0])

    with col_sel_yr:
        # Botones rápidos de selección de años
        c_b1, c_b2, c_b3 = st.columns(3)
        with c_b1:
            if st.button("Todos los Años", use_container_width=True, key="btn_all_years"):
                st.session_state["comp_selected_years"] = db_min_years
        with c_b2:
            if st.button("2024 - 2026", use_container_width=True, key="btn_recent_years"):
                st.session_state["comp_selected_years"] = [y for y in db_min_years if y >= 2024]
        with c_b3:
            if st.button("2022 - 2026", use_container_width=True, key="btn_full_mop"):
                st.session_state["comp_selected_years"] = [y for y in db_min_years if 2022 <= y <= 2026]

        current_comp_years = st.session_state.get("comp_selected_years", db_min_years)
        # Validar que pertenezcan a los años disponibles
        current_comp_years = [y for y in current_comp_years if y in db_min_years]
        if not current_comp_years:
            current_comp_years = db_min_years

        sel_years = st.multiselect(
            "Base de años a comparar:",
            options=db_min_years,
            default=current_comp_years,
            key="ms_comp_years"
        )
        if not sel_years:
            sel_years = db_min_years

    with col_sel_per:
        st.markdown("<div style='height: 38px;'></div>", unsafe_allow_html=True)
        sel_comp_period = st.selectbox(
            "Periodo de corte homogéneo:",
            options=avail_comp_periods,
            index=avail_comp_periods.index(default_comp_per) if default_comp_per in avail_comp_periods else 0,
            key="sb_comp_period",
            help="Para comparar cifras equitativas entre años, se analiza el mismo periodo de corte calendario."
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Nota si hay pocos años registrados en BD para este ministerio
    if len(db_min_years) < 2:
        st.info(f"💡 **Sugerencia:** Para comparar más años de **{selected_min}**, puedes descargar y actualizar años en masa desde la pestaña **'🌐 Catálogo & Scraper DIPRES'**.")


    # 2. Consulta de Datos Multianuales
    filter_progs = selected_progs if len(selected_progs) < total_progs_count else None
    df_multi = db.get_multianual_summary(
        ministerio=selected_min,
        years=sel_years,
        periodo=sel_comp_period,
        programas=filter_progs,
        moneda=selected_currency
    )

    if df_multi.empty:
        st.warning(f"⚠️ No se registraron datos consolidados para los años {sel_years} en el periodo **{sel_comp_period}**.")
        st.info("💡 Puedes sincronizar o verificar los informes descargados en la pestaña **'Catálogo & Scraper DIPRES'**.")
    else:
        # Calcular métricas ejecutivas de alto nivel
        latest_row = df_multi.iloc[-1]
        earliest_row = df_multi.iloc[0]
        
        # Variación punta a punta de presupuesto vigente
        pct_growth_vig = 0.0
        if earliest_row["vigente"] > 0:
            pct_growth_vig = round(((latest_row["vigente"] - earliest_row["vigente"]) / earliest_row["vigente"]) * 100, 1)
        sign_vig = "+" if pct_growth_vig >= 0 else ""
        
        # Promedio histórico de % de avance en este periodo
        avg_pct_exec = round(df_multi["pct_ejecucion"].mean(), 1)
        
        # Total acumulado ejecutado a través de los años analizados
        total_ejec_sum = df_multi["ejecucion"].sum()
        
        # Inversión Subt. 31 del último año analizado y variación
        subt31_latest = latest_row["subt31_ejecucion"]
        subt31_earliest = earliest_row["subt31_ejecucion"]
        pct_growth_inv = 0.0
        if subt31_earliest > 0:
            pct_growth_inv = round(((subt31_latest - subt31_earliest) / subt31_earliest) * 100, 1)
        sign_inv = "+" if pct_growth_inv >= 0 else ""

        # 4 Tarjetas de KPIs Ejecutivos Multianuales
        kc1, kc2, kc3, kc4 = st.columns(4, gap="small")
        with kc1:
            st.markdown(render_kpi_card_html(
                title=f"Vigente {int(latest_row['year'])}",
                value=format_currency(latest_row["vigente"]),
                subtitle=f"{sign_vig}{pct_growth_vig}% vs {int(earliest_row['year'])}",
                icon="🏛️",
                theme="blue",
                badge=f"{len(df_multi)} Años Base"
            ), unsafe_allow_html=True)
        with kc2:
            st.markdown(render_kpi_card_html(
                title=f"Ejecución {int(latest_row['year'])}",
                value=format_currency(latest_row["ejecucion"]),
                subtitle=f"Total serie: {format_currency(total_ejec_sum)}",
                icon="⚡",
                theme="green",
                badge=f"{latest_row['pct_ejecucion']}% avance"
            ), unsafe_allow_html=True)
        with kc3:
            st.markdown(render_kpi_card_html(
                title="Tasa Promedio Avance",
                value=f"{avg_pct_exec}%",
                subtitle=f"Promedio corte al {sel_comp_period}",
                icon="🎯",
                theme="indigo",
                progress=avg_pct_exec,
                badge="Media Histórica"
            ), unsafe_allow_html=True)
        with kc4:
            st.markdown(render_kpi_card_html(
                title="Inversión Obras (31)",
                value=format_currency(subt31_latest),
                subtitle=f"{sign_inv}{pct_growth_inv}% vs {int(earliest_row['year'])}",
                icon="🚜",
                theme="amber",
                progress=latest_row["pct_capital"],
                badge=f"Subt. 31 en {int(latest_row['year'])}"
            ), unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # 3. Gráficos Comparativos Multianuales
        cg1, cg2 = st.columns([5.2, 4.8], gap="medium")
        with cg1:
            st.markdown("##### 📊 Presupuesto Vigente vs Ejecución Acumulada por Año")
            fig_hist = go.Figure()
            # Barra Vigente (Azul)
            fig_hist.add_trace(go.Bar(
                name="Presupuesto Vigente",
                x=[str(int(y)) for y in df_multi["year"]],
                y=df_multi["vigente"],
                marker_color="#2563eb",
                hovertemplate="<b>Año %{x}</b><br>Vigente: %{y:$,.0f} M$<extra></extra>"
            ))
            # Barra Ejecución (Verde)
            fig_hist.add_trace(go.Bar(
                name="Ejecución Acumulada",
                x=[str(int(y)) for y in df_multi["year"]],
                y=df_multi["ejecucion"],
                marker_color="#10b981",
                hovertemplate="<b>Año %{x}</b><br>Ejecución: %{y:$,.0f} M$<extra></extra>"
            ))
            # Línea de % de Avance en eje Y secundario
            fig_hist.add_trace(go.Scatter(
                name="% Avance Presupuestario",
                x=[str(int(y)) for y in df_multi["year"]],
                y=df_multi["pct_ejecucion"],
                yaxis="y2",
                mode="lines+markers+text",
                text=[f"{p}%" for p in df_multi["pct_ejecucion"]],
                textposition="top center",
                textfont=dict(color="#b45309", size=11, family="sans-serif"),
                line=dict(color="#f59e0b", width=3),
                marker=dict(size=8, color="#d97706"),
                hovertemplate="<b>Año %{x}</b><br>% Avance: %{y:.1f}%<extra></extra>"
            ))
            fig_hist.update_layout(
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                barmode="group",
                height=420,
                autosize=True,
                hovermode="x",
                hoverdistance=60,
                font=dict(color="#1e293b", family="sans-serif"),
                margin=dict(l=55, r=50, t=35, b=45, autoexpand=True),
                legend=dict(orientation="h", y=1.15, font=dict(color="#1e293b", size=11)),
                hoverlabel=dict(bgcolor="#ffffff", font_color="#0f172a", bordercolor="#cbd5e1"),
                xaxis=dict(type="category", automargin=True, tickfont=dict(color="#334155", size=11), gridcolor="#f1f5f9", linecolor="#cbd5e1"),
                yaxis=dict(automargin=True, tickfont=dict(color="#475569", size=10), gridcolor="#f1f5f9", linecolor="#cbd5e1", tickprefix="$ "),
                yaxis2=dict(
                    title="",
                    overlaying="y",
                    side="right",
                    automargin=True,
                    range=[0, max(df_multi["pct_ejecucion"].max() * 1.35, 60)],
                    showgrid=False,
                    tickfont=dict(color="#b45309", size=10),
                    ticksuffix="%"
                )
            )
            st.plotly_chart(fig_hist, use_container_width=True, theme=None, config={"responsive": True, "displayModeBar": True, "autosizable": True})

        with cg2:
            st.markdown("##### 🏗️ Evolución de Gastos de Capital (Subt. 29, 31, 33)")
            df_subts_hist = db.get_multianual_subtitulos_breakdown(
                ministerio=selected_min,
                years=sel_years,
                periodo=sel_comp_period,
                programas=filter_progs,
                moneda=selected_currency
            )
            if not df_subts_hist.empty:
                subt_colors = {"31": "#2563eb", "29": "#8b5cf6", "33": "#f59e0b"}
                subt_labels = {
                    "31": "Subt. 31 Inversión",
                    "29": "Subt. 29 Activos No Fin.",
                    "33": "Subt. 33 Transf. Capital"
                }
                fig_cap = go.Figure()
                for scode in ["31", "29", "33"]:
                    sub_df = df_subts_hist[df_subts_hist["subtitulo_cod"] == scode]
                    if not sub_df.empty:
                        fig_cap.add_trace(go.Bar(
                            name=subt_labels.get(scode, f"Subt. {scode}"),
                            x=[str(int(y)) for y in sub_df["year"]],
                            y=sub_df["ejecucion"],
                            marker_color=subt_colors.get(scode, "#64748b"),
                            hovertemplate="<b>Año %{x} - " + subt_labels.get(scode, f"Subt. {scode}") + "</b><br>Ejecución: %{y:$,.0f} M$<extra></extra>"
                        ))
                fig_cap.update_layout(
                    paper_bgcolor="#ffffff",
                    plot_bgcolor="#ffffff",
                    barmode="stack",
                    height=420,
                    autosize=True,
                    hovermode="x",
                    hoverdistance=60,
                    font=dict(color="#1e293b", family="sans-serif"),
                    margin=dict(l=55, r=25, t=35, b=45, autoexpand=True),
                    legend=dict(orientation="h", y=1.15, font=dict(color="#1e293b", size=10)),
                    hoverlabel=dict(bgcolor="#ffffff", font_color="#0f172a", bordercolor="#cbd5e1"),
                    xaxis=dict(type="category", automargin=True, tickfont=dict(color="#334155", size=11), gridcolor="#f1f5f9", linecolor="#cbd5e1"),
                    yaxis=dict(automargin=True, tickfont=dict(color="#475569", size=10), gridcolor="#f1f5f9", linecolor="#cbd5e1", tickprefix="$ ")
                )
                st.plotly_chart(fig_cap, use_container_width=True, theme=None, config={"responsive": True, "displayModeBar": True, "autosizable": True})
            else:
                st.info("No se registraron cuentas de capital para el periodo.")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # 3.5. Crecimiento y Variación por Ley de Presupuesto (Tramo Personalizable)
        st.markdown("##### 📈 Crecimiento de Presupuesto Vigente respecto a Ley de Presupuestos")
        st.caption("Analiza la variación y expansión presupuestaria seleccionando cualquier tramo temporal (ej. 2018 al 2026), contrastando la Ley de Presupuestos aprobada inicialmente contra el Presupuesto Vigente.")

        if len(db_min_years) >= 2:
            # Botones de tramo rápido
            c_p1, c_p2, c_p3, c_p4, _ = st.columns([1.5, 1.5, 1.5, 1.6, 3.9], gap="small")
            with c_p1:
                if st.button("2018 - 2026", key="btn_tr_2018_2026", use_container_width=True):
                    if 2018 in db_min_years:
                        st.session_state["sb_tramo_start"] = 2018
                    if 2026 in db_min_years:
                        st.session_state["sb_tramo_end"] = 2026
            with c_p2:
                if st.button("2020 - 2026", key="btn_tr_2020_2026", use_container_width=True):
                    if 2020 in db_min_years:
                        st.session_state["sb_tramo_start"] = 2020
                    if 2026 in db_min_years:
                        st.session_state["sb_tramo_end"] = 2026
            with c_p3:
                if st.button("2022 - 2026", key="btn_tr_2022_2026", use_container_width=True):
                    if 2022 in db_min_years:
                        st.session_state["sb_tramo_start"] = 2022
                    if 2026 in db_min_years:
                        st.session_state["sb_tramo_end"] = 2026
            with c_p4:
                if st.button("Todo el Periodo", key="btn_tr_all", use_container_width=True):
                    st.session_state["sb_tramo_start"] = min(db_min_years)
                    st.session_state["sb_tramo_end"] = max(db_min_years)

            # Inicialización segura en session_state
            if "sb_tramo_start" not in st.session_state or st.session_state["sb_tramo_start"] not in db_min_years:
                st.session_state["sb_tramo_start"] = min(db_min_years)
            if "sb_tramo_end" not in st.session_state or st.session_state["sb_tramo_end"] not in db_min_years:
                st.session_state["sb_tramo_end"] = max(db_min_years)
            if st.session_state["sb_tramo_start"] > st.session_state["sb_tramo_end"]:
                st.session_state["sb_tramo_end"] = st.session_state["sb_tramo_start"]

            # Controles de Tramo y Parámetros
            col_t1, col_t2, col_t3, col_t4 = st.columns([1.8, 1.8, 3.2, 3.2], gap="small")
            with col_t1:
                tramo_start = st.selectbox(
                    "Año Base (Desde):",
                    options=db_min_years,
                    key="sb_tramo_start"
                )
            with col_t2:
                valid_end_years = [y for y in db_min_years if y >= tramo_start]
                if not valid_end_years:
                    valid_end_years = [tramo_start]
                if st.session_state.get("sb_tramo_end", max(valid_end_years)) not in valid_end_years:
                    st.session_state["sb_tramo_end"] = max(valid_end_years)
                tramo_end = st.selectbox(
                    "Año Comparación (Hasta):",
                    options=valid_end_years,
                    key="sb_tramo_end"
                )
            with col_t3:
                scope_mode = st.selectbox(
                    "Ámbito Presupuestario:",
                    options=[
                        "🏛️ Presupuesto Total",
                        "🚜 Gastos de Capital (Subt. 29, 31, 33)",
                        "🏗️ Subtítulo 31 (Inversión y Obras)"
                    ],
                    key="sb_tramo_scope",
                    help="Permite evaluar el crecimiento tanto a nivel del ministerio completo como exclusivamente en inversión y obras."
                )
            with col_t4:
                calc_mode = st.selectbox(
                    "Métrica de % de Aumento:",
                    options=[
                        "📈 % vs Ley de Presupuesto Base",
                        "⚖️ % Aumento Intranual (Vigente vs Ley)",
                        "🚀 % Crecimiento Acumulado de Vigente",
                        "📊 % Variación Interanual (YoY)"
                    ],
                    key="sb_tramo_calc_mode",
                    help="Define la referencia de la curva porcentual: respecto a la Ley Inicial del año base, la modificación dentro de cada año fiscal, el crecimiento del vigente o la variación interanual."
                )

            # Obtener datos del tramo
            tramo_years = [y for y in db_min_years if tramo_start <= y <= tramo_end]
            if set(tramo_years) == set(sel_years):
                df_tramo = df_multi.copy()
            else:
                df_tramo = db.get_multianual_summary(
                    ministerio=selected_min,
                    years=tramo_years,
                    periodo=sel_comp_period,
                    programas=filter_progs,
                    moneda=selected_currency
                )

            if df_tramo.empty:
                st.info(f"No se registraron datos para el tramo {tramo_start}-{tramo_end} en el corte '{sel_comp_period}'.")
            else:
                # Selección de columnas según ámbito
                if "Subtítulo 31" in scope_mode:
                    col_ley = "subt31_inicial"
                    col_vig = "subt31_vigente"
                    label_scope = "Inversión Subt. 31"
                elif "Capital" in scope_mode:
                    col_ley = "capital_inicial"
                    col_vig = "capital_vigente"
                    label_scope = "Gastos de Capital"
                else:
                    col_ley = "inicial"
                    col_vig = "vigente"
                    label_scope = "Presupuesto Total"

                base_row = df_tramo.iloc[0]
                final_row = df_tramo.iloc[-1]
                val_ley_base = base_row[col_ley]
                val_vig_base = base_row[col_vig]
                val_ley_final = final_row[col_ley]
                val_vig_final = final_row[col_vig]

                # Determinar base de referencia para el cálculo de crecimiento
                base_notice = None
                if val_ley_base > 0:
                    base_calc = val_ley_base
                    base_ref_name = f"Ley Base ({tramo_start})"
                elif val_vig_base > 0:
                    base_calc = val_vig_base
                    base_ref_name = f"Vigente Base ({tramo_start})"
                    base_notice = (
                        f"En el año base {tramo_start}, {selected_min} no registró Ley de Presupuestos Inicial propia ($0) "
                        f"debido a que su partida fue incorporada o transferida durante el ejercicio presupuestario. "
                        f"Se toma como referencia base su Presupuesto Vigente inicial ({format_currency(val_vig_base)}) "
                        f"para calcular el crecimiento real."
                    )
                else:
                    nz_rows = df_tramo[df_tramo[col_vig] > 0]
                    if not nz_rows.empty:
                        first_nz = nz_rows.iloc[0]
                        base_calc = first_nz[col_ley] if first_nz[col_ley] > 0 else first_nz[col_vig]
                        base_ref_name = f"Base ({int(first_nz['year'])})"
                        base_notice = (
                            f"En el año base {tramo_start} no se registró presupuesto. "
                            f"Se toma como referencia el primer año con asignación presupuestaria ({int(first_nz['year'])}: {format_currency(base_calc)})."
                        )
                    else:
                        base_calc = 0.0
                        base_ref_name = f"Base ({tramo_start})"

                if base_notice:
                    st.info(f"💡 **Nota de Año Base ({tramo_start}):** {base_notice}")

                # Serie porcentual según modo de cálculo
                pct_values = []
                pct_labels = []

                if "% vs Ley de Presupuesto Base" in calc_mode:
                    metric_legend = f"% vs {base_ref_name}"
                    for _, r in df_tramo.iterrows():
                        val_vig = r[col_vig]
                        pct = round(((val_vig - base_calc) / base_calc) * 100, 1) if base_calc > 0 else 0.0
                        pct_values.append(pct)
                        sign = "+" if pct > 0 else ""
                        pct_labels.append(f"{sign}{pct}%")
                elif "Intranual" in calc_mode:
                    metric_legend = "% Aumento Vigente vs Ley (Mismo Año)"
                    for _, r in df_tramo.iterrows():
                        val_ini = r[col_ley]
                        val_vig = r[col_vig]
                        pct = round(((val_vig - val_ini) / val_ini) * 100, 1) if val_ini > 0 else 0.0
                        pct_values.append(pct)
                        sign = "+" if pct > 0 else ""
                        pct_labels.append(f"{sign}{pct}%")
                elif "Crecimiento Acumulado" in calc_mode:
                    metric_legend = f"% Crecimiento Acum. vs Vigente {tramo_start}"
                    for _, r in df_tramo.iterrows():
                        val_vig = r[col_vig]
                        pct = round(((val_vig - val_vig_base) / val_vig_base) * 100, 1) if val_vig_base > 0 else 0.0
                        pct_values.append(pct)
                        sign = "+" if pct > 0 else ""
                        pct_labels.append(f"{sign}{pct}%")
                else:  # YoY
                    metric_legend = "% Variación Interanual (YoY)"
                    prev_vig = None
                    for _, r in df_tramo.iterrows():
                        val_vig = r[col_vig]
                        if prev_vig is not None and prev_vig > 0:
                            pct = round(((val_vig - prev_vig) / prev_vig) * 100, 1)
                        else:
                            pct = 0.0
                        prev_vig = val_vig
                        pct_values.append(pct)
                        sign = "+" if pct > 0 else ""
                        pct_labels.append(f"{sign}{pct}%")

                # Métricas KPI del tramo
                total_tramo_pct = round(((val_vig_final - base_calc) / base_calc) * 100, 1) if base_calc > 0 else 0.0
                sign_tot = "+" if total_tramo_pct >= 0 else ""
                net_growth_nom = val_vig_final - base_calc
                n_span = int(final_row["year"]) - int(base_row["year"])
                cagr_val = round(((val_vig_final / base_calc) ** (1.0 / n_span) - 1.0) * 100, 2) if (n_span > 0 and base_calc > 0 and val_vig_final > 0) else 0.0

                # 4 Tarjetas KPI del Tramo
                tk1, tk2, tk3, tk4 = st.columns(4, gap="small")
                with tk1:
                    st.markdown(render_kpi_card_html(
                        title="% Aumento Total Tramo",
                        value=f"{sign_tot}{total_tramo_pct}%",
                        subtitle=f"{base_ref_name} ➔ Vigente {int(final_row['year'])}",
                        icon="🚀" if total_tramo_pct >= 0 else "📉",
                        theme="green" if total_tramo_pct >= 0 else "amber",
                        badge=f"{int(base_row['year'])} - {int(final_row['year'])}"
                    ), unsafe_allow_html=True)
                with tk2:
                    st.markdown(render_kpi_card_html(
                        title="Incremento Nominal Neto",
                        value=format_currency(net_growth_nom),
                        subtitle=f"Expansión en {label_scope}",
                        icon="💵",
                        theme="blue",
                        badge="Neto Tramo"
                    ), unsafe_allow_html=True)
                with tk3:
                    st.markdown(render_kpi_card_html(
                        title=f"Vigente {int(final_row['year'])}",
                        value=format_currency(val_vig_final),
                        subtitle=f"{base_ref_name}: {format_currency(base_calc)}",
                        icon="🏛️",
                        theme="indigo",
                        badge=label_scope
                    ), unsafe_allow_html=True)
                with tk4:
                    st.markdown(render_kpi_card_html(
                        title="Tasa Compuesta (CAGR)",
                        value=f"{cagr_val}% anual" if n_span > 0 else "N/A (1 año)",
                        subtitle=f"Ritmo anualizado en {n_span} años" if n_span > 0 else "Mismo año base",
                        icon="📈",
                        theme="purple",
                        badge="Tasa Anualizada"
                    ), unsafe_allow_html=True)

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                # Gráfico Plotly Combinado Dual-Axis
                fig_tramo = go.Figure()

                custom_data_tramo = []
                for _, r in df_tramo.iterrows():
                    l_val = r[col_ley]
                    v_val = r[col_vig]
                    custom_data_tramo.append([l_val, v_val, v_val - l_val])

                # 1. Barra Ley de Presupuestos (Inicial)
                fig_tramo.add_trace(go.Bar(
                    name="Ley de Presupuestos (Inicial)",
                    x=[str(int(y)) for y in df_tramo["year"]],
                    y=df_tramo[col_ley],
                    marker_color="#94a3b8",
                    customdata=custom_data_tramo,
                    hovertemplate="<b>Año %{x}</b><br>🏛️ Ley Inicial: %{y:$,.0f} M$<extra></extra>"
                ))

                # 2. Barra Presupuesto Vigente
                fig_tramo.add_trace(go.Bar(
                    name="Presupuesto Vigente",
                    x=[str(int(y)) for y in df_tramo["year"]],
                    y=df_tramo[col_vig],
                    marker_color="#2563eb",
                    customdata=custom_data_tramo,
                    hovertemplate="<b>Año %{x}</b><br>🔷 Presupuesto Vigente: %{y:$,.0f} M$<br>Diferencia vs Ley: %{customdata[2]:+$,.0f} M$<extra></extra>"
                ))

                # 3. Línea de % de Aumento en Eje Secundario Y2
                fig_tramo.add_trace(go.Scatter(
                    name=metric_legend,
                    x=[str(int(y)) for y in df_tramo["year"]],
                    y=pct_values,
                    yaxis="y2",
                    mode="lines+markers+text",
                    text=pct_labels,
                    textposition="top center",
                    textfont=dict(color="#047857", size=11, family="sans-serif"),
                    line=dict(color="#10b981", width=3.2),
                    marker=dict(size=8.5, color="#059669", symbol="circle", line=dict(color="#ffffff", width=1.5)),
                    customdata=custom_data_tramo,
                    hovertemplate="<b>Año %{x}</b><br>📈 " + metric_legend + ": <b>%{y:+.1f}%</b><br>Ley: %{customdata[0]:$,.0f} M$<br>Vigente: %{customdata[1]:$,.0f} M$<extra></extra>"
                ))

                min_pct = min(pct_values) if pct_values else 0
                max_pct = max(pct_values) if pct_values else 100
                y2_lower = min(0.0, min_pct * 1.25)
                y2_upper = max(max_pct * 1.35, 12.0)

                fig_tramo.update_layout(
                    paper_bgcolor="#ffffff",
                    plot_bgcolor="#ffffff",
                    barmode="group",
                    height=450,
                    bargap=0.22,
                    bargroupgap=0.08,
                    autosize=True,
                    hovermode="x",
                    hoverdistance=60,
                    font=dict(color="#1e293b", family="sans-serif"),
                    margin=dict(l=60, r=55, t=35, b=45, autoexpand=True),
                    legend=dict(
                        orientation="h",
                        y=1.14,
                        x=0.0,
                        font=dict(color="#1e293b", size=11),
                        bgcolor="rgba(255, 255, 255, 0.9)"
                    ),
                    hoverlabel=dict(bgcolor="#ffffff", font_color="#0f172a", bordercolor="#cbd5e1"),
                    xaxis=dict(
                        type="category",
                        automargin=True,
                        tickfont=dict(color="#334155", size=11),
                        gridcolor="#f1f5f9",
                        linecolor="#cbd5e1"
                    ),
                    yaxis=dict(
                        automargin=True,
                        tickfont=dict(color="#475569", size=10),
                        gridcolor="#f1f5f9",
                        linecolor="#cbd5e1",
                        tickprefix="$ "
                    ),
                    yaxis2=dict(
                        title="",
                        overlaying="y",
                        side="right",
                        automargin=True,
                        range=[y2_lower, y2_upper],
                        showgrid=False,
                        tickfont=dict(color="#047857", size=10),
                        ticksuffix="%"
                    )
                )

                st.plotly_chart(
                    fig_tramo,
                    use_container_width=True,
                    theme=None,
                    config={"responsive": True, "displayModeBar": True, "autosizable": True}
                )

                # Tabla Resumen Plegable
                with st.expander("📋 Ver Tabla Detallada de Cifras y Variaciones del Tramo", expanded=False):
                    df_table_tramo = pd.DataFrame({
                        "Año": [int(y) for y in df_tramo["year"]],
                        f"Ley Presupuesto - {label_scope}": [format_currency(v) for v in df_tramo[col_ley]],
                        f"Presupuesto Vigente - {label_scope}": [format_currency(v) for v in df_tramo[col_vig]],
                        "Diferencia Nominal": [format_currency(v - l) for l, v in zip(df_tramo[col_ley], df_tramo[col_vig])],
                        f"% vs {base_ref_name}": [
                            f"{'+' if ((v - base_calc) / base_calc * 100) >= 0 else ''}{round(((v - base_calc) / base_calc * 100), 1)}%"
                            if base_calc > 0 else "0.0%" for v in df_tramo[col_vig]
                        ],
                        "% Intranual (Vigente vs Ley)": [
                            f"{'+' if ((v - l) / l * 100) >= 0 else ''}{round(((v - l) / l * 100), 1)}%"
                            if l > 0 else "0.0%" for l, v in zip(df_tramo[col_ley], df_tramo[col_vig])
                        ],
                        "% Variación Interanual (YoY)": [
                            f"{'+' if yoy >= 0 else ''}{round(yoy, 1)}%" for yoy in (df_tramo[col_vig].pct_change() * 100).fillna(0.0)
                        ]
                    })
                    st.dataframe(df_table_tramo, use_container_width=True, hide_index=True)
        else:
            st.info(f"💡 Se requiere contar con más de un año en base de datos para comparar tramos temporales de {selected_min}.")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # 4. Evolución de Servicios / Direcciones Clave
        st.markdown("##### 🏢 Tendencia de Ejecución por Dirección / Servicio Principal")
        df_progs_hist = db.get_multianual_programas_breakdown(
            ministerio=selected_min,
            years=sel_years,
            periodo=sel_comp_period,
            top_n=6,
            moneda=selected_currency
        )
        if not df_progs_hist.empty:
            df_progs_hist_plot = df_progs_hist.copy()
            df_progs_hist_plot["Año"] = df_progs_hist_plot["year"].astype(str)
            fig_prog_trend = px.line(
                df_progs_hist_plot,
                x="Año",
                y="ejecucion",
                color="programa",
                markers=True,
                labels={"ejecucion": "Ejecución Acumulada (M$)", "Año": "Año", "programa": "Servicio / Dirección"},
                color_discrete_sequence=['#2563eb', '#059669', '#d97706', '#7c3aed', '#db2777', '#0891b2']
            )
            fig_prog_trend.update_traces(line=dict(width=3), marker=dict(size=8))
            fig_prog_trend.update_layout(
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                autosize=True,
                font=dict(color="#1e293b", family="sans-serif"),
                margin=dict(l=55, r=25, t=25, b=65, autoexpand=True),
                hoverlabel=dict(bgcolor="#ffffff", font_color="#0f172a", bordercolor="#cbd5e1"),
                legend=dict(orientation="h", y=-0.22, title_text="", font=dict(color="#1e293b", size=10)),
                xaxis=dict(type="category", automargin=True, tickfont=dict(color="#334155", size=11), gridcolor="#f1f5f9", linecolor="#cbd5e1"),
                yaxis=dict(automargin=True, tickfont=dict(color="#475569", size=10), gridcolor="#f1f5f9", linecolor="#cbd5e1", tickprefix="$ ")
            )
            st.plotly_chart(fig_prog_trend, use_container_width=True, theme=None, config={"responsive": True, "displayModeBar": True, "autosizable": True})

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # 5. Matriz Comparativa y Variaciones Interanuales (% YoY)
        st.markdown("##### 📑 Matriz Comparativa Anual y Variación Interanual (% YoY)")
        df_table = df_multi.copy()
        df_table["Año"] = df_table["year"].astype(str)
        df_table["Periodo"] = sel_comp_period
        
        # Formatear columnas
        cols_show = [
            "Año", "Periodo", "vigente", "ejecucion", "pct_ejecucion",
            "capital_ejecucion", "subt31_ejecucion", "subt29_ejecucion", "subt33_ejecucion",
            "var_vigente_pct", "var_ejecucion_pct"
        ]
        df_display = df_table[cols_show].rename(columns={
            "vigente": "Presupuesto Vigente (M$)",
            "ejecucion": "Ejecución Acum. (M$)",
            "pct_ejecucion": "% Avance",
            "capital_ejecucion": "Gasto Capital (M$)",
            "subt31_ejecucion": "Subt. 31 Obras (M$)",
            "subt29_ejecucion": "Subt. 29 Activos (M$)",
            "subt33_ejecucion": "Subt. 33 Transf. (M$)",
            "var_vigente_pct": "Δ% Vigente (YoY)",
            "var_ejecucion_pct": "Δ% Ejecución (YoY)"
        })

        st.dataframe(
            df_display.style.format({
                "Presupuesto Vigente (M$)": "{:,.0f}",
                "Ejecución Acum. (M$)": "{:,.0f}",
                "% Avance": "{:.1f}%",
                "Gasto Capital (M$)": "{:,.0f}",
                "Subt. 31 Obras (M$)": "{:,.0f}",
                "Subt. 29 Activos (M$)": "{:,.0f}",
                "Subt. 33 Transf. (M$)": "{:,.0f}",
                "Δ% Vigente (YoY)": lambda x: f"{x:+.1f}%" if pd.notnull(x) else "-",
                "Δ% Ejecución (YoY)": lambda x: f"{x:+.1f}%" if pd.notnull(x) else "-"
            }),
            use_container_width=True,
            height=260
        )

        # Botón de Descarga CSV de la comparativa
        csv_comp_data = df_display.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            label="📥 Descargar Matriz Comparativa (CSV)",
            data=csv_comp_data,
            file_name=f"comparativa_multianual_{selected_min[:20].strip()}_{sel_years[0]}_{sel_years[-1]}.csv",
            mime="text/csv",
            key="btn_dl_comp_csv"
        )

# ==============================================================================
# TAB 4: RANKINGS & TOPS NACIONALES (Acceso desde pestañas)
# ==============================================================================
with tab_rankings:
    render_national_tops_view(
        year=selected_year,
        moneda=selected_currency,
        periodo=selected_period,
        scope="Presupuesto Total (Todos los Subtítulos)",
        sort_by="Presupuesto Vigente (Mayor a menor)",
        top_n=10,
        exclude_tesoro=True,
        filter_mins=None
    )

# ==============================================================================
# TAB 5: CATÁLOGO & SCRAPER OFICIAL DIPRES
# ==============================================================================
with tab_catalogo:
    st.markdown("#### 🌐 Catálogo Oficial DIPRES & Sincronización")
    st.caption("Descarga, sincronización masiva multianual y verificación de informes oficiales desde dipres.gob.cl.")
    
    # --------------------------------------------------------------------------
    # SECCIÓN 1: SINCRONIZACIÓN Y DESCARGA MASIVA MULTIANUAL
    # --------------------------------------------------------------------------
    all_target_years = sorted(list(config.YEAR_IDS.keys()), reverse=True)
    common_target_years = [2026, 2025, 2024, 2023, 2022]

    with st.expander("📥 Sincronización y Actualización Masiva Multianual (Descarga de Años en Masa)", expanded=True):
        st.markdown("""
        <div style="font-size: 0.83rem; color: #334155; margin-bottom: 8px;">
            Descarga, procesa y consolida en lote múltiples años e informes oficiales DIPRES para cualquier ministerio sin salir de esta pestaña.
        </div>
        """, unsafe_allow_html=True)
        
        # 1. Selector de Ámbito (Todos los Ministerios vs Un Ministerio) y Periodo
        col_bm1, col_bm2 = st.columns([3.2, 2.8])
        with col_bm1:
            bulk_scope = st.radio(
                "🏛️ Cobertura de la Sincronización:",
                options=["🌐 TODOS los Ministerios (Consolidación Completa del Estado)", "🏛️ Un Ministerio Específico"],
                index=0,
                horizontal=True,
                key="rb_bulk_sync_scope"
            )
            if "Un Ministerio" in bulk_scope:
                bulk_min_idx = all_mins.index(selected_min) if selected_min in all_mins else 0
                bulk_selected_min = st.selectbox(
                    "Selecciona el Ministerio:",
                    options=all_mins,
                    index=bulk_min_idx,
                    key="sb_bulk_sync_min",
                    help="Elige el ministerio para el cual deseas sincronizar datos."
                )
                db_min_bulk_years = db.get_available_years_for_ministry(bulk_selected_min)
                missing_bulk_years = sorted([y for y in common_target_years if y not in db_min_bulk_years], reverse=True)
            else:
                bulk_selected_min = "TODOS"
                st.caption("💡 **Modo Estado Completo:** Se descargará y consolidará la información de **todos los ministerios y servicios públicos** de Chile para los años seleccionados.")
                db_all_filters = db.get_available_filters()
                db_min_bulk_years = db_all_filters["anios"]
                missing_bulk_years = sorted([y for y in common_target_years if y not in db_min_bulk_years], reverse=True)
        
        with col_bm2:
            period_bulk_options = [
                "Todos los periodos del año (Descarga completa)",
                "Segundo Trimestre (Corte estándar)",
                "Primer Trimestre",
                "Tercer Trimestre",
                "Cuarto Trimestre"
            ]
            bulk_selected_period = st.selectbox(
                "📅 Periodo de los Informes:",
                options=period_bulk_options,
                index=0,
                key="sb_bulk_sync_period",
                help="Elige 'Todos los periodos del año' para descargar y consolidar el historial íntegro anual, o un trimestre específico."
            )

        # Resumen dinámico de años existentes y sugerencias
        if bulk_selected_min == "TODOS":
            total_mins_in_db = len(db.get_available_filters()["ministerios"])
            badge_reg = f"{len(db_min_bulk_years)} años registrados ({', '.join(str(y) for y in sorted(db_min_bulk_years, reverse=True)[:5])}...) en {total_mins_in_db} ministerios"
            badge_sug = ", ".join(str(y) for y in missing_bulk_years) if missing_bulk_years else "Serie 2022-2026 ya iniciada en BD"
        else:
            badge_reg = ", ".join(str(y) for y in db_min_bulk_years) if db_min_bulk_years else "Ninguno"
            badge_sug = ", ".join(str(y) for y in missing_bulk_years) if missing_bulk_years else "Serie 2022-2026 completa en BD"
        
        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 12px; margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 18px; align-items: center; font-size: 0.81rem;">
            <div>📦 Años en Base de Datos: <b style="color: #059669;">{badge_reg}</b></div>
            <div>🎯 Años sugeridos faltantes: <b style="color: #d97706;">{badge_sug}</b></div>
        </div>
        """, unsafe_allow_html=True)

        # Inicializar versión y estado de años
        if "bulk_years_ver" not in st.session_state:
            st.session_state["bulk_years_ver"] = 0
            st.session_state["bulk_years_default"] = missing_bulk_years if missing_bulk_years else [y for y in [2026, 2025, 2024, 2023, 2022] if y in all_target_years]

        # Actualizar automáticamente la selección de años si cambia el ministerio en el selector
        current_scope_key = f"{bulk_selected_min}_{bulk_scope}"
        if st.session_state.get("last_bulk_scope_key") != current_scope_key:
            st.session_state["last_bulk_scope_key"] = current_scope_key
            st.session_state["bulk_years_default"] = missing_bulk_years if missing_bulk_years else [y for y in [2026, 2025, 2024, 2023, 2022] if y in all_target_years]
            st.session_state["bulk_years_ver"] += 1

        # Botones de selección rápida de años
        col_btn_sug, col_btn_22_26, col_btn_18_26, col_btn_clr = st.columns(4)
        with col_btn_sug:
            if st.button("🎯 Seleccionar Sugeridos", use_container_width=True, key="btn_pick_sug_bulk"):
                st.session_state["bulk_years_default"] = missing_bulk_years if missing_bulk_years else [y for y in [2026, 2025, 2024, 2023, 2022] if y in all_target_years]
                st.session_state["bulk_years_ver"] += 1
                st.rerun()
        with col_btn_22_26:
            if st.button("📅 2022 - 2026", use_container_width=True, key="btn_pick_22_26_bulk"):
                st.session_state["bulk_years_default"] = [2026, 2025, 2024, 2023, 2022]
                st.session_state["bulk_years_ver"] += 1
                st.rerun()
        with col_btn_18_26:
            if st.button("⭐ 2018 - 2026", use_container_width=True, key="btn_pick_18_26_bulk"):
                st.session_state["bulk_years_default"] = list(range(2026, 2017, -1))
                st.session_state["bulk_years_ver"] += 1
                st.rerun()
        with col_btn_clr:
            if st.button("🧹 Limpiar Años", use_container_width=True, key="btn_pick_clr_bulk"):
                st.session_state["bulk_years_default"] = []
                st.session_state["bulk_years_ver"] += 1
                st.rerun()

        # Multiselect dinámico y libre de años
        current_def_years = [y for y in st.session_state.get("bulk_years_default", []) if y in all_target_years]
        curr_ver = st.session_state.get("bulk_years_ver", 0)

        years_chosen = st.multiselect(
            "Selecciona libremente los años que deseas descargar y actualizar en masa:",
            options=all_target_years,
            default=current_def_years,
            key=f"ms_bulk_years_ver_{curr_ver}",
            help="Puedes seleccionar cualquier combinación de años para descargar e insertar en lote a la base de datos."
        )

        # Fila de opciones de descarga y botón de acción
        c_mo, c_fo, c_bt = st.columns([2, 2, 2])
        with c_mo:
            bulk_moneda = st.selectbox(
                "Moneda:",
                options=["Pesos", "Dólares", "Ambas monedas"],
                index=0,
                key="sb_bulk_sync_moneda"
            )
        with c_fo:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            force_bulk_sync = st.checkbox(
                "Forzar re-descarga de archivos existentes",
                value=False,
                key="chk_bulk_sync_force",
                help="Si está desactivado, el sistema detecta si el archivo ya existe en disco o base de datos y lo omite para máxima velocidad."
            )
        with c_bt:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            btn_start_bulk = st.button("🚀 Iniciar Sincronización Masiva", use_container_width=True, key="btn_exec_bulk_sync_action")

        if btn_start_bulk:
            if not years_chosen:
                st.warning("⚠️ Por favor selecciona al menos un año para sincronizar.")
            else:
                # Asegurar persistencia estricta en la pestaña de Catálogo & Scraper (índice 3)
                components.html("""
                <script>
                    window.parent.sessionStorage.setItem("dipres_active_tab_idx", "3");
                </script>
                """, height=0, width=0)
                
                cur_list = ["Pesos", "Dólares"] if bulk_moneda == "Ambas monedas" else [bulk_moneda]
                clean_period_str = bulk_selected_period.split(" (")[0] if "Todos los periodos" not in bulk_selected_period else None
                
                # Pre-cargar conjunto de URLs y llaves ya registradas en BD para búsqueda O(1)
                ingested_urls = db.get_ingested_urls_set()
                ingested_keys = db.get_ingested_keys_set()
                
                progress_bar_bulk = st.progress(0)
                status_text_bulk = st.empty()
                sub_text_bulk = st.empty()
                
                total_saved_bulk = 0
                total_from_disk_bulk = 0
                total_omitted_in_db_bulk = 0
                total_downloaded_bulk = 0
                
                all_tasks = []
                status_text_bulk.info("🔍 Recopilando catálogo oficial de informes DIPRES para los años seleccionados...")
                
                for y_val in years_chosen:
                    y_sc = get_scraper(y_val)
                    if bulk_selected_min == "TODOS":
                        y_sc.build_catalog()
                        catalog_items = list(y_sc.catalog)
                        if cur_list:
                            catalog_items = [it for it in catalog_items if it.get("moneda") in cur_list]
                    else:
                        catalog_items = y_sc.filter_catalog(ministerio=bulk_selected_min, monedas=cur_list)
                    
                    if clean_period_str:
                        catalog_items = [it for it in catalog_items if it.get("periodo") == clean_period_str]
                        
                    for itm in catalog_items:
                        all_tasks.append((y_val, y_sc, itm))

                if not all_tasks:
                    status_text_bulk.warning("⚠️ No se encontraron informes en DIPRES con los filtros seleccionados.")
                else:
                    total_items_to_proc = len(all_tasks)
                    target_desc = "TODOS los Ministerios del Estado" if bulk_selected_min == "TODOS" else bulk_selected_min
                    status_text_bulk.info(f"⏳ Sincronizando **{total_items_to_proc}** informes para **{target_desc}** en los años {years_chosen}...")
                    
                    for task_idx, (y_val, y_sc, itm) in enumerate(all_tasks):
                        prog_label = itm.get("programa", "Programa")
                        min_label = itm.get("ministerio", "")
                        per_label = itm.get("periodo", "")
                        url_xls = itm.get("url_xls", "")
                        m_key = (y_val, min_label, prog_label, per_label, itm.get("moneda", "Pesos"))
                        
                        # 1. DETECCIÓN EN BD: Si ya está procesado en base de datos y no forzamos re-descarga, saltar
                        already_in_db = (url_xls in ingested_urls or m_key in ingested_keys)
                        if already_in_db and not force_bulk_sync:
                            total_omitted_in_db_bulk += 1
                            if (task_idx + 1) % 25 == 0 or task_idx == total_items_to_proc - 1:
                                progress_bar_bulk.progress((task_idx + 1) / total_items_to_proc)
                                sub_text_bulk.caption(f"[{task_idx+1}/{total_items_to_proc}] Año {y_val} · {min_label[:28]} · {prog_label[:22]} (Ya en BD: {total_omitted_in_db_bulk} | Nuevos: {total_saved_bulk})")
                            continue
                            
                        # 2. DETECCIÓN EN DISCO: Si el archivo ya existe localmente, parsear directo sin descargar
                        file_on_disk = y_sc.is_downloaded(itm)
                        if file_on_disk and not force_bulk_sync:
                            x_path = y_sc.get_local_path_for_report(itm)
                            total_from_disk_bulk += 1
                        else:
                            x_path = y_sc.download_report(itm, force=force_bulk_sync)
                            if x_path:
                                total_downloaded_bulk += 1
                                
                        if x_path:
                            itm["archivo_local"] = str(x_path)
                            try:
                                m_p, d_p = DipresExcelParser.parse_file(x_path)
                                db.save_report_data(itm, m_p, d_p)
                                ingested_urls.add(url_xls)
                                ingested_keys.add(m_key)
                                total_saved_bulk += 1
                            except Exception:
                                pass
                        
                        progress_bar_bulk.progress((task_idx + 1) / total_items_to_proc)
                        sub_text_bulk.caption(f"[{task_idx+1}/{total_items_to_proc}] Año {y_val} · {min_label[:28]} · {prog_label[:22]} (Nuevos: {total_saved_bulk} | Desde disco: {total_from_disk_bulk} | Ya en BD: {total_omitted_in_db_bulk})")
                        
                    status_text_bulk.empty()
                    sub_text_bulk.empty()
                    progress_bar_bulk.empty()
                    
                    st.success(f"""
                    ✅ **¡Sincronización masiva finalizada con éxito!**
                    - 🏛️ **Ámbito:** {target_desc}
                    - 📅 **Años procesados:** {', '.join(str(y) for y in years_chosen)}
                    - 📊 **Informes guardados/consolidados:** {total_saved_bulk}
                    - ⚡ **Omitidos por ya estar al día en BD (0 descargas):** {total_omitted_in_db_bulk}
                    - 📁 **Procesados desde archivos locales en disco:** {total_from_disk_bulk}
                    - 🌐 **Nuevos descargados desde la web DIPRES:** {total_downloaded_bulk}
                    """)
                    
                    components.html("""
                    <script>
                        window.parent.sessionStorage.setItem("dipres_active_tab_idx", "3");
                    </script>
                    """, height=0, width=0)
                    st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # SECCIÓN 2: EXPLORADOR Y CATÁLOGO DETALLADO (AÑO ACTIVO)
    # --------------------------------------------------------------------------
    st.markdown(f"##### 🔍 Explorador y Filtro por Informe (Año Activo: {selected_year})")
    
    col_f_tipo, col_f_search = st.columns([1, 2])
    with col_f_tipo:
        filtro_tipo_rep = st.selectbox(
            "Tipo de Informe:",
            ["Todos", "Ejecución Presupuestaria", "Inversión Detallada (BIP)"],
            index=0
        )
    with col_f_search:
        filtro_text_rep = st.text_input("Buscar informe:", placeholder="Ej: Vialidad, Enero, Segundo Trimestre...")
        
    reports_matching = scraper.filter_catalog(
        ministerio=selected_min,
        programas=selected_progs,
        monedas=[selected_currency]
    )
    
    ingested_urls_active = db.get_ingested_urls_set()
    ingested_keys_active = db.get_ingested_keys_set()

    table_data = []
    for r in reports_matching:
        t_inf = r.get("tipo_informe", "Ejecución Presupuestaria")
        if filtro_tipo_rep != "Todos" and t_inf != filtro_tipo_rep:
            continue
        if filtro_text_rep and filtro_text_rep.lower() not in (r["programa"] + " " + r["titulo_informe"]).lower():
            continue
            
        r_url = r.get("url_xls", "")
        r_key = (r.get("year", selected_year), r.get("ministerio"), r.get("programa"), r.get("periodo"), r.get("moneda", "Pesos"))
        is_in_db = (r_url in ingested_urls_active or r_key in ingested_keys_active)
        descargado = scraper.is_downloaded(r)

        if is_in_db:
            estado_label = "✅ En Base de Datos"
        elif descargado:
            estado_label = "📁 En Disco (Listo para BD)"
        else:
            estado_label = "⏳ Pendiente en Web"

        table_data.append({
            "Programa": r["programa"],
            "Tipo": t_inf,
            "Periodo": r["periodo"],
            "Título Informe": r["titulo_informe"],
            "Estado": estado_label,
            "URL Excel": r["url_xls"],
            "item_ref": r,
            "is_in_db": is_in_db,
            "is_on_disk": descargado
        })
    df_cat = pd.DataFrame(table_data)
    
    c_btn1, c_btn2, c_chk = st.columns([3, 3, 4])
    with c_btn1:
        btn_descargar_seleccionados = st.button("📥 Sincronizar Selección Actual", use_container_width=True)
    with c_btn2:
        btn_descargar_todo = st.button("⚡ Sincronizar Todo el Ministerio", use_container_width=True)
    with c_chk:
        force_redownload = st.checkbox("Forzar re-descarga de archivos existentes", value=False, key="chk_single_force")
        
    if btn_descargar_seleccionados or btn_descargar_todo:
        # Asegurar persistencia de pestaña 3 al sincronizar individualmente
        components.html("""
        <script>
            window.parent.sessionStorage.setItem("dipres_active_tab_idx", "3");
        </script>
        """, height=0, width=0)
        
        items_to_download = [row["item_ref"] for row in table_data] if btn_descargar_seleccionados else scraper.filter_catalog(ministerio=selected_min, monedas=[selected_currency])
        st.write(f"Procesando **{len(items_to_download)}** informes...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        descargados_cnt = 0
        from_disk_cnt = 0
        omitted_cnt = 0
        
        for idx, item in enumerate(items_to_download):
            status_text.caption(f"[{idx+1}/{len(items_to_download)}] {item['programa']} · {item['periodo']}")
            it_url = item.get("url_xls", "")
            it_key = (item.get("year", selected_year), item.get("ministerio"), item.get("programa"), item.get("periodo"), item.get("moneda", "Pesos"))
            
            # Si ya está en BD y no forzamos, omitir
            if not force_redownload and (it_url in ingested_urls_active or it_key in ingested_keys_active):
                omitted_cnt += 1
                progress_bar.progress((idx + 1) / len(items_to_download))
                continue
                
            # Si ya está en disco, procesar directo sin descargar
            if not force_redownload and scraper.is_downloaded(item):
                xls_path = scraper.get_local_path_for_report(item)
                from_disk_cnt += 1
            else:
                xls_path = scraper.download_report(item, force=force_redownload)
                
            if xls_path:
                item["archivo_local"] = str(xls_path)
                try:
                    meta, df_parsed = DipresExcelParser.parse_file(xls_path)
                    db.save_report_data(item, meta, df_parsed)
                    ingested_urls_active.add(it_url)
                    ingested_keys_active.add(it_key)
                    descargados_cnt += 1
                except Exception:
                    pass
            progress_bar.progress((idx + 1) / len(items_to_download))
            
        status_text.empty()
        st.success(f"✅ Sincronización completada: {descargados_cnt} consolidados en BD ({from_disk_cnt} desde disco local, {omitted_cnt} ya existentes omitidos).")
        
        components.html("""
        <script>
            window.parent.sessionStorage.setItem("dipres_active_tab_idx", "3");
        </script>
        """, height=0, width=0)
        st.rerun()

    if not df_cat.empty:
        st.dataframe(
            df_cat[["Programa", "Tipo", "Periodo", "Título Informe", "Estado", "URL Excel"]],
            use_container_width=True,
            height=420
        )
    else:
        st.info("No hay informes para los filtros seleccionados.")

# ==============================================================================
# TAB 4: BASE DE DATOS CONSOLIDADA & EXPORTACIÓN
# ==============================================================================
with tab_database:
    st.markdown("#### 📑 Explorador de Base de Datos")
    st.caption("Búsqueda instantánea y exportación de datos consolidados a Excel y CSV.")
    
    f1, f2, f3, f4 = st.columns([4, 3, 2, 3])
    with f1:
        search_query = st.text_input("🔍 Buscar cuenta o proyecto:", placeholder="Ej: Puentes, Caminos, Pavimentación, Estudios...")
    with f2:
        filtro_subt_db = st.selectbox("Subtítulo:", ["Todos", "29, 31, 33 (Capital)", "31 (Inversión)", "29 (Activos)", "33 (Transferencias)"])
    with f3:
        records_limit = st.selectbox("Límite filas:", [200, 500, 1000, 5000], index=1)
    with f4:
        st.write("")
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            btn_exp_excel = st.button("📗 Excel", use_container_width=True)
        with col_ex2:
            btn_exp_csv = st.button("📄 CSV", use_container_width=True)

    # Determinar filtro de subtítulo
    target_subt_filter = None
    solo_capital_filter = False
    if "29, 31, 33" in filtro_subt_db:
        solo_capital_filter = True
    elif "31" in filtro_subt_db:
        target_subt_filter = "31"
    elif "29" in filtro_subt_db:
        target_subt_filter = "29"
    elif "33" in filtro_subt_db:
        target_subt_filter = "33"

    # Exportaciones
    if btn_exp_excel:
        ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        out_excel = config.EXPORTS_DIR / f"ejecucion_consolidada_{ts}.xlsx"
        db.export_consolidated_to_excel(
            out_excel,
            year=selected_year,
            ministerio=selected_min,
            programas=selected_progs,
            subtitulo=target_subt_filter,
            solo_inversion=solo_capital_filter,
            search_text=search_query if search_query else None
        )
        st.success("Archivo Excel generado con éxito.")
        with open(out_excel, "rb") as f:
            st.download_button("⬇️ Descargar Excel", f.read(), file_name=out_excel.name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if btn_exp_csv:
        ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        out_csv = config.EXPORTS_DIR / f"ejecucion_consolidada_{ts}.csv"
        db.export_consolidated_to_csv(
            out_csv,
            year=selected_year,
            ministerio=selected_min,
            programas=selected_progs,
            subtitulo=target_subt_filter,
            solo_inversion=solo_capital_filter,
            search_text=search_query if search_query else None
        )
        st.success("Archivo CSV generado con éxito.")
        with open(out_csv, "rb") as f:
            st.download_button("⬇️ Descargar CSV", f.read(), file_name=out_csv.name, mime="text/csv")

    df_records = db.get_detailed_records(
        year=selected_year,
        ministerio=selected_min,
        programas=selected_progs,
        periodos=[selected_period] if selected_period else None,
        subtitulo=target_subt_filter,
        solo_inversion=solo_capital_filter,
        search_text=search_query if search_query else None,
        moneda=selected_currency,
        limit=records_limit
    )

    st.caption(f"Mostrando **{len(df_records)}** registros consolidados")
    if not df_records.empty:
        st.dataframe(
            df_records.style.format({
                "Presupuesto Inicial (M$)": "{:,.0f}",
                "Presupuesto Vigente (M$)": "{:,.0f}",
                "Ejecución Acumulada (M$)": "{:,.0f}",
                "Saldo (M$)": "{:,.0f}",
                "% Ejecución": "{:.2f}%"
            }),
            use_container_width=True,
            height=480
        )
    else:
        st.info("No se encontraron registros con los filtros seleccionados.")
