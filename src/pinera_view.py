"""
Módulo de Visualización Ejecutiva: Monitor de Programas del Presidente Sebastián Piñera.
Auditoría técnica, seguimiento presupuestario y dossier de defensa legislativa para el Ejercicio Fiscal 2027.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import textwrap
from typing import Optional, List, Dict, Any

import config
from src.pinera_manager import PineraManager, PINERA_PROGRAMS_REGISTRY

# ==============================================================================
# HELPERS DE FORMATO Y ESTILO
# ==============================================================================
def format_currency_pinera(val: Any) -> str:
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

def get_risk_badge_html(risk_level: str) -> str:
    """Genera un badge HTML con estilo visual según el nivel de riesgo de ajuste fiscal."""
    risk_colors = {
        "Crítico": {"bg": "#fee2e2", "text": "#991b1b", "border": "#fca5a5", "icon": "🔴"},
        "Alto": {"bg": "#ffedd5", "text": "#9a3412", "border": "#fdba74", "icon": "🟠"},
        "Moderada a Severa": {"bg": "#ffedd5", "text": "#c2410c", "border": "#fed7aa", "icon": "🟠"},
        "Media a Alta": {"bg": "#fef3c7", "text": "#b45309", "border": "#fde68a", "icon": "🟡"},
        "Media": {"bg": "#fef9c3", "text": "#854d0e", "border": "#fef08a", "icon": "🟡"},
        "Baja a Media": {"bg": "#f0fdf4", "text": "#166534", "border": "#bbf7d0", "icon": "🟢"},
        "Baja": {"bg": "#f0fdf4", "text": "#15803d", "border": "#86efac", "icon": "🟢"}
    }
    cfg = risk_colors.get(risk_level, {"bg": "#f1f5f9", "text": "#334155", "border": "#cbd5e1", "icon": "⚪"})
    return (
        f'<span style="background-color: {cfg["bg"]}; color: {cfg["text"]}; border: 1px solid {cfg["border"]}; '
        f'padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.76rem; display: inline-flex; align-items: center; gap: 4px;">'
        f'{cfg["icon"]} {risk_level}</span>'
    )

def render_metric_card(title: str, value: str, subtitle: str, icon: str = "📊", theme: str = "blue", badge: Optional[str] = None) -> str:
    """Genera tarjetas ejecutivas estilizadas consistentes con el diseño de la suite."""
    palettes = {
        "blue": {"top": "#2563eb", "bg": "#f8fafc", "border": "#e2e8f0", "pill_bg": "#eff6ff", "pill_color": "#1d4ed8"},
        "rose": {"top": "#e11d48", "bg": "#fff1f2", "border": "#fecdd3", "pill_bg": "#ffe4e6", "pill_color": "#9f1239"},
        "orange": {"top": "#ea580c", "bg": "#fff7ed", "border": "#ffedd5", "pill_bg": "#ffedd5", "pill_color": "#c2410c"},
        "green": {"top": "#10b981", "bg": "#f0fdf4", "border": "#bbf7d0", "pill_bg": "#dcfce7", "pill_color": "#15803d"},
        "purple": {"top": "#8b5cf6", "bg": "#faf5ff", "border": "#e9d5ff", "pill_bg": "#f3e8ff", "pill_color": "#6b21a8"},
    }
    p = palettes.get(theme, palettes["blue"])
    badge_html = f'<span style="background-color: {p["pill_bg"]}; color: {p["pill_color"]}; font-size: 0.72rem; font-weight: 700; padding: 2px 7px; border-radius: 9999px;">{badge}</span>' if badge else ''
    
    return (
        f'<div style="background-color: #ffffff; border: 1.5px solid {p["border"]}; border-top: 4px solid {p["top"]}; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">'
        f'<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">'
        f'<span style="font-size: 0.80rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">{title}</span>'
        f'<span style="font-size: 1.25rem;">{icon}</span>'
        f'</div>'
        f'<div style="font-size: 1.45rem; font-weight: 800; color: #0f172a; line-height: 1.2; margin-bottom: 4px;">{value}</div>'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">'
        f'<span style="font-size: 0.75rem; color: #64748b;">{subtitle}</span>'
        f'{badge_html}'
        f'</div>'
        f'</div>'
    )

# ==============================================================================
# FUNCIÓN PRINCIPAL DE RENDERIZADO
# ==============================================================================
def render_pinera_programs_view(
    year: int = 2026,
    periodo: str = "Julio",
    moneda: str = "Pesos",
    selected_category: str = "Todos",
    selected_risk: str = "Todos",
    search_query: str = ""
):
    """
    Renderiza la ventana interactiva integral para el monitoreo, auditoría técnica
    y estrategia de defensa presupuestaria de los programas del Presidente Sebastián Piñera.
    """
    pm = PineraManager()

    # 1. ENCABEZADO INSTITUCIONAL HERO
    st.markdown(textwrap.dedent(f"""
    <div class="header-box" style="margin-bottom: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
            <div>
                <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 4px;">
                    <span class="header-title-text" style="color: #0f172a; font-size: 1.55rem; font-weight: 800;">
                        🇨🇱 Monitor de Programas del Presidente Sebastián Piñera
                    </span>
                    <span class="year-pill-hero">
                        <span class="year-icon">📅</span> Presupuesto {year} · {periodo}
                    </span>
                </div>
                <div class="header-sub-text" style="color: #475569; font-size: 0.88rem;">
                    Identificación, Auditoría Presupuestaria y Estrategia de Defensa Legislativa · <b>Ejercicio Fiscal 2027</b>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                <span class="pill-badge" style="background-color: #eff6ff; border-color: #93c5fd; color: #1d4ed8 !important; font-weight: 700;">
                    🏛️ Comisión Mixta de Presupuestos
                </span>
                <span class="pill-badge" style="background-color: #fef2f2; border-color: #fecaca; color: #b91c1c !important; font-weight: 700;">
                    🛡️ Blindaje de Glosas 2027
                </span>
                <span class="pill-badge" style="background-color: #f0fdf4; border-color: #bbf7d0; color: #15803d !important; font-weight: 700;">
                    📊 13 Líneas Prioritarias
                </span>
            </div>
        </div>
    </div>
    """), unsafe_allow_html=True)

    # 2. ALERTA MACROFISCAL Y ENTORNO DE RIGIDEZ 2027 (COLLAPSIBLE / DESTACADO)
    with st.expander("📌 Contexto Macroeconómico, Rigidez Presupuestaria y Amenazas de Ajuste Fiscal para 2027", expanded=False):
        st.markdown("""
        **Diagnóstico Fiscal Clave para la Negociación 2027:**
        * **Estrechez Fiscal Extrema:** La tramitación presupuestaria 2027 se proyecta con holguras financieras virtualmente nulas. Los desbalances en el balance estructural y los compromisos de consolidación del gasto público (>0,4% del PIB) obligan a DIPRES y Hacienda a buscar áreas de contención.
        * **Vulnerabilidad de Políticas Focalizadas:** Ante la rigidez de sueldos (Subtítulo 21) y subsidios ineludibles, los ajustes suelen recaer desproporcionadamente en **transferencias corrientes discrecionales (Subtítulo 24)**, **inversión de capital no comprometida (Subtítulo 33)** y **programas evaluados con observaciones técnicas por DIPRES**.
        * **Divergencias Doctrinales:** Los programas impulsados en los gobiernos de Sebastián Piñera (2010–2014 y 2018–2022) enfrentan cuestionamientos por basarse en principios de mérito escolar, subsidio a la demanda, copago y focalización social. La preservación de estos programas requiere blindaje técnico sustentado en evaluaciones de impacto ex-post y glosas intransferibles en las Subcomisiones Mixtas.
        """)

    # 3. EXTRACCIÓN DE DATOS CONSOLIDADOS
    with st.spinner("Cargando matriz presupuestaria de programas..."):
        df_all = pm.get_all_programs_kpis(
            year=year,
            periodo=periodo,
            moneda=moneda,
            category_filter=selected_category,
            risk_filter=selected_risk
        )

    if df_all.empty:
        st.warning(f"No se encontraron registros de programas para el año {year} y periodo {periodo} con los filtros seleccionados.")
        return

    # Filtro opcional por búsqueda de texto
    if search_query:
        q = search_query.strip().upper()
        df_all = df_all[
            df_all["name"].str.upper().str.contains(q) |
            df_all["ministerio"].str.upper().str.contains(q) |
            df_all["category"].str.upper().str.contains(q) |
            df_all["risk_level"].str.upper().str.contains(q)
        ]

    # Cálculos globales
    tot_vigente = df_all["presupuesto_vigente"].sum()
    tot_inicial = df_all["presupuesto_inicial"].sum()
    tot_ejecucion = df_all["ejecucion_acumulada"].sum()
    tot_saldo = df_all["saldo"].sum()
    delta_global = tot_vigente - tot_inicial
    pct_change_global = (delta_global / tot_inicial * 100.0) if tot_inicial > 0 else 0.0
    pct_avance_global = (tot_ejecucion / tot_vigente * 100.0) if tot_vigente > 0 else 0.0

    # Detección de alertas críticas
    criticos_count = len(df_all[df_all["risk_level"] == "Crítico"])
    recortes_count = len(df_all[df_all["pct_change_ley"] < -2.0])
    subejecutados_count = len(df_all[(df_all["pct_ejecucion"] < 35.0) & (df_all["presupuesto_vigente"] > 0)])

    # 4. TARJETAS DE MÉTRICAS MACRO (4 KPIs EJECUTIVOS)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(render_metric_card(
            title="Presupuesto Vigente Consolidado",
            value=format_currency_pinera(tot_vigente),
            subtitle=f"Ley Inicial: {format_currency_pinera(tot_inicial)}",
            icon="💰",
            theme="blue",
            badge=f"{len(df_all)} programas"
        ), unsafe_allow_html=True)
    with k2:
        theme_delta = "green" if delta_global >= 0 else "rose"
        st.markdown(render_metric_card(
            title="Modificación Neta vs Ley",
            value=f"{format_currency_pinera(delta_global)}",
            subtitle=f"Variación: {pct_change_global:+.2f}% vs Ley Inicial",
            icon="⚖️",
            theme=theme_delta,
            badge=f"{recortes_count} con recorte" if recortes_count > 0 else "Sin recortes"
        ), unsafe_allow_html=True)
    with k3:
        theme_pct = "green" if pct_avance_global >= 50.0 else "orange"
        st.markdown(render_metric_card(
            title="Ejecución Devengada Acumulada",
            value=format_currency_pinera(tot_ejecucion),
            subtitle=f"Saldo disponible: {format_currency_pinera(tot_saldo)}",
            icon="📈",
            theme=theme_pct,
            badge=f"{pct_avance_global:.1f}% avance"
        ), unsafe_allow_html=True)
    with k4:
        st.markdown(render_metric_card(
            title="Alertas Presupuestarias Activas",
            value=f"{recortes_count + subejecutados_count} Alertas",
            subtitle=f"{criticos_count} con Riesgo Fiscal Crítico",
            icon="🚨",
            theme="rose" if (recortes_count + subejecutados_count) > 0 else "green",
            badge=f"{subejecutados_count} subejecutados"
        ), unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # ==============================================================================
    # 5. MATRIZ INTEGRAL DE RIESGO Y ESTADO DE LOS PROGRAMAS
    # ==============================================================================
    st.markdown("### 📊 Matriz Integral de Programas y Riesgo de Ajuste Fiscal 2027")
    st.caption("Visión panorámica de las 13 líneas programáticas con clasificación de riesgo, presupuesto inicial vs vigente y alertas detectadas.")

    # Generar tabla para visualización
    display_rows = []
    for _, row in df_all.iterrows():
        display_rows.append({
            "ID": row["id"],
            "Programa": row["name"],
            "Eje Temático": row["category"],
            "Ministerio": row["ministerio"],
            "Riesgo 2027": row["risk_level"],
            "Presupuesto Inicial ($ MM)": row["ini_mm"],
            "Presupuesto Vigente ($ MM)": row["vig_mm"],
            "Var. vs Ley ($ MM)": row["delta_mm"],
            "% Var.": row["pct_change_ley"],
            "Ejecución ($ MM)": row["eje_mm"],
            "% Avance": row["pct_ejecucion"],
            "Estado / Alerta": row["alert"]
        })
    df_matrix_display = pd.DataFrame(display_rows)

    # Botones de exportación de la matriz completa
    col_exp_a, col_exp_b, col_exp_spacer = st.columns([2.5, 2.5, 5])
    with col_exp_a:
        ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"programas_pinera_matriz_{year}_{periodo}_{ts}.xlsx"
        excel_path = config.EXPORTS_DIR / excel_filename
        df_all.to_excel(excel_path, index=False)
        with open(excel_path, "rb") as f:
            st.download_button(
                "📥 Descargar Matriz (Excel)",
                data=f.read(),
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="btn_dl_matriz_excel"
            )
    with col_exp_b:
        csv_data = df_all.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📥 Descargar Matriz (CSV)",
            data=csv_data,
            file_name=f"programas_pinera_matriz_{year}_{periodo}_{ts}.csv",
            mime="text/csv",
            use_container_width=True,
            key="btn_dl_matriz_csv"
        )

    # Mostrar la tabla formateada
    st.dataframe(
        df_matrix_display[[
            "Programa", "Eje Temático", "Riesgo 2027", "Presupuesto Inicial ($ MM)",
            "Presupuesto Vigente ($ MM)", "Var. vs Ley ($ MM)", "% Var.", "Ejecución ($ MM)", "% Avance", "Estado / Alerta"
        ]].style.format({
            "Presupuesto Inicial ($ MM)": "${:,.1f} MM",
            "Presupuesto Vigente ($ MM)": "${:,.1f} MM",
            "Var. vs Ley ($ MM)": "${:+,.1f} MM",
            "% Var.": "{:+.1f}%",
            "Ejecución ($ MM)": "${:,.1f} MM",
            "% Avance": "{:.1f}%"
        }),
        use_container_width=True,
        height=380
    )

    st.markdown("---")

    # ==============================================================================
    # 6. DOSSIER DE DEFENSA PRESUPUESTARIA Y FICHA TÉCNICA INDIVIDUAL
    # ==============================================================================
    st.markdown("### 🛡️ Dossier Técnico y Estrategia de Defensa Parlamentaria")
    st.caption("Selecciona un programa para inspeccionar su trazabilidad histórica, evidencia empírica de impacto, justificación presupuestaria y glosa parlamentaria para la Ley de Presupuestos 2027.")

    # Selector de programa para Ficha Técnica
    prog_options = {row["id"]: f"{row['name']} ({row['ministerio']})" for _, row in df_all.iterrows()}
    if not prog_options:
        st.info("No hay programas disponibles para mostrar ficha técnica con los filtros activos.")
        return

    # Mantener selección en session_state si existe
    default_prog_id = list(prog_options.keys())[0]
    if "selected_pinera_prog" not in st.session_state or st.session_state["selected_pinera_prog"] not in prog_options:
        st.session_state["selected_pinera_prog"] = default_prog_id

    sel_prog_id = st.selectbox(
        "🎯 Selecciona el Programa a Auditar y Defender:",
        options=list(prog_options.keys()),
        format_func=lambda x: prog_options[x],
        index=list(prog_options.keys()).index(st.session_state["selected_pinera_prog"]),
        key="sb_select_pinera_prog"
    )

    spec = PINERA_PROGRAMS_REGISTRY.get(sel_prog_id)
    prog_row = df_all[df_all["id"] == sel_prog_id].iloc[0] if not df_all[df_all["id"] == sel_prog_id].empty else None

    if not spec or prog_row is None:
        st.error("No se pudo cargar la información del programa seleccionado.")
        return

    # Ficha del Programa (Encabezado visual con marco legal y riesgo)
    st.markdown(textwrap.dedent(f"""
    <div style="background-color: #f8fafc; border: 1.5px solid #cbd5e1; border-left: 6px solid {spec['badge_color']}; border-radius: 10px; padding: 16px 20px; margin: 12px 0 16px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 8px;">
            <div style="font-size: 1.35rem; font-weight: 800; color: #0f172a;">{spec['name']}</div>
            <div style="display: flex; gap: 8px; align-items: center;">
                {get_risk_badge_html(spec['risk_level'])}
                <span style="background-color: #e2e8f0; color: #334155; font-size: 0.76rem; font-weight: 700; padding: 3px 8px; border-radius: 6px;">
                    📂 {spec['category']}
                </span>
            </div>
        </div>
        <div style="font-size: 0.85rem; color: #334155; line-height: 1.5; margin-bottom: 6px;">
            <b>Marco Legal y Origen:</b> {spec['legal_framework']}
        </div>
        <div style="font-size: 0.85rem; color: #334155; line-height: 1.5; margin-bottom: 6px;">
            <b>Población Objetivo / Cobertura:</b> {spec['target_population']}
        </div>
        <div style="font-size: 0.80rem; color: #64748b;">
            <b>Asignación Institucional:</b> {spec['budget_codes']['partida']} · {spec['budget_codes']['capitulo']} · {spec['budget_codes']['subtitulos']}
        </div>
    </div>
    """), unsafe_allow_html=True)

    # Pestañas del Dossier del Programa
    tab_diag, tab_hist, tab_defensa, tab_cuentas = st.tabs([
        "📊 Diagnóstico y Estado en Ejecución",
        "📈 Serie Histórica 2018–2026 (Piñera II vs Boric)",
        "🛡️ Argumentario Técnico & Glosa 2027",
        "📑 Cuentas Granulares y Glosas"
    ])

    # --------------------------------------------------------------------------
    # SUB-TAB 1: DIAGNÓSTICO Y ESTADO ACTUAL
    # --------------------------------------------------------------------------
    with tab_diag:
        st.markdown("##### 📌 Balance Presupuestario y Alerta Operativa")
        
        c_d1, c_d2, c_d3, c_d4 = st.columns(4)
        with c_d1:
            st.markdown(render_metric_card(
                title="Presupuesto Inicial (Ley)",
                value=f"${prog_row['ini_mm']:,.1f} MM",
                subtitle="Aprobado en Ley",
                icon="🏛️",
                theme="blue"
            ), unsafe_allow_html=True)
        with c_d2:
            st.markdown(render_metric_card(
                title="Presupuesto Vigente",
                value=f"${prog_row['vig_mm']:,.1f} MM",
                subtitle=f"Variación: {prog_row['pct_change_ley']:+.2f}%",
                icon="💵",
                theme="green" if prog_row['pct_change_ley'] >= 0 else "rose"
            ), unsafe_allow_html=True)
        with c_d3:
            st.markdown(render_metric_card(
                title="Ejecución Devengada",
                value=f"${prog_row['eje_mm']:,.1f} MM",
                subtitle=f"% Avance: {prog_row['pct_ejecucion']:.1f}%",
                icon="⚡",
                theme="green" if prog_row['pct_ejecucion'] >= 45.0 else "orange"
            ), unsafe_allow_html=True)
        with c_d4:
            st.markdown(render_metric_card(
                title="Saldo Disponible",
                value=f"${prog_row['saldo_mm']:,.1f} MM",
                subtitle=f"{100.0 - prog_row['pct_ejecucion']:.1f}% por ejecutar",
                icon="💼",
                theme="purple"
            ), unsafe_allow_html=True)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        col_alert_diag, col_alert_chart = st.columns([5.5, 4.5])
        with col_alert_diag:
            st.markdown("###### ⚠️ Diagnóstico de Amenaza y Vulnerabilidad de Ajuste:")
            st.info(f"**Alerta Presupuestaria Actual:** {prog_row['alert']}")
            st.markdown(textwrap.dedent(f"""
            <div style="background-color: #fef2f2; border: 1.5px solid #fecaca; border-radius: 8px; padding: 12px 16px; font-size: 0.88rem; color: #7f1d1d; line-height: 1.6;">
                <b>Patrón de Ajuste Detectado para 2027:</b><br>
                {spec['threat_diagnosis']}
            </div>
            """), unsafe_allow_html=True)

        with col_alert_chart:
            st.markdown("###### 🎯 Termómetro de Avance Presupuestario:")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=prog_row['pct_ejecucion'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Avance a {periodo} (%)", 'font': {'size': 14, 'color': '#0f172a'}},
                delta={'reference': 58.3, 'increasing': {'color': "#16a34a"}, 'decreasing': {'color': "#dc2626"}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#64748b"},
                    'bar': {'color': "#2563eb"},
                    'bgcolor': "white",
                    'borderwidth': 1.5,
                    'bordercolor': "#cbd5e1",
                    'steps': [
                        {'range': [0, 35], 'color': '#fee2e2'},
                        {'range': [35, 60], 'color': '#fef3c7'},
                        {'range': [60, 100], 'color': '#dcfce7'}
                    ],
                    'threshold': {
                        'line': {'color': "#dc2626", 'width': 3},
                        'thickness': 0.75,
                        'value': 50.0
                    }
                }
            ))
            fig_gauge.update_layout(
                paper_bgcolor="#ffffff",
                font={'color': "#0f172a", 'family': "sans-serif"},
                height=220,
                margin=dict(l=20, r=20, t=30, b=10)
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

    # --------------------------------------------------------------------------
    # SUB-TAB 2: SERIE HISTÓRICA 2018-2026 (PIÑERA II VS BORIC)
    # --------------------------------------------------------------------------
    with tab_hist:
        st.markdown("##### 📈 Trazabilidad Multianual del Programa (2018–2026)")
        st.caption("Comparativa de presupuesto vigente y ejecución devengada entre la administración Piñera II (2018–2021) y el actual gobierno (2022–2026).")

        with st.spinner("Construyendo serie histórica multianual..."):
            df_hist = pm.get_program_history(sel_prog_id, start_year=2018, end_year=year, moneda=moneda)

        if df_hist.empty:
            st.info("No se dispone de registros históricos continuos para esta línea programática en los años solicitados.")
        else:
            col_chart_hist, col_table_hist = st.columns([6, 4])
            with col_chart_hist:
                fig_hist = go.Figure()
                
                # Barras de Presupuesto Vigente diferenciadas por gobierno
                colores_gob = df_hist["gobierno"].map(lambda g: "#2563eb" if "Piñera" in g else "#ef4444")
                fig_hist.add_trace(go.Bar(
                    x=df_hist["year"].astype(str),
                    y=df_hist["vig_mm"],
                    name="Presupuesto Vigente ($ MM)",
                    marker_color=colores_gob,
                    text=df_hist["vig_mm"].apply(lambda v: f"${v:,.1f} MM"),
                    textposition="auto",
                    hovertemplate="<b>Año %{x}</b><br>Vigente: $%{y:,.1f} MM<extra></extra>"
                ))
                
                # Línea de Ejecución Acumulada
                fig_hist.add_trace(go.Scatter(
                    x=df_hist["year"].astype(str),
                    y=df_hist["eje_mm"],
                    name="Ejecución Devengada ($ MM)",
                    mode="lines+markers",
                    line=dict(color="#10b981", width=3),
                    marker=dict(size=8, color="#047857"),
                    hovertemplate="<b>Ejecutado:</b> $%{y:,.1f} MM<extra></extra>"
                ))

                fig_hist.update_layout(
                    title=f"Evolución Presupuestaria: {spec['short_name']} (2018–{year})",
                    paper_bgcolor="#ffffff",
                    plot_bgcolor="#ffffff",
                    height=360,
                    margin=dict(l=20, r=20, t=40, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
                    xaxis=dict(gridcolor="#f1f5f9", title="Año Fiscal"),
                    yaxis=dict(gridcolor="#f1f5f9", title="Miles de Millones ($ MM)")
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            with col_table_hist:
                st.markdown("###### 📋 Datos Anuales Auditados:")
                df_hist_display = df_hist[["year", "gobierno", "vig_mm", "eje_mm", "pct_ejecucion"]].copy()
                st.dataframe(
                    df_hist_display.style.format({
                        "vig_mm": "${:,.1f} MM",
                        "eje_mm": "${:,.1f} MM",
                        "pct_ejecucion": "{:.1f}%"
                    }),
                    use_container_width=True,
                    height=330
                )

    # --------------------------------------------------------------------------
    # SUB-TAB 3: ARGUMENTARIO TÉCNICO Y GLOSA PROPUESTA 2027
    # --------------------------------------------------------------------------
    with tab_defensa:
        st.markdown("##### 🛡️ Dossier Técnico y Argumentario para Subcomisiones Mixtas")
        st.caption("Respaldo empírico, justificación de rentabilidad social y propuesta formal de glosa presupuestaria intransferible.")

        c_arg1, c_arg2 = st.columns(2)
        with c_arg1:
            st.markdown(textwrap.dedent(f"""
            <div style="background-color: #f0fdf4; border: 1.5px solid #86efac; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;">
                <div style="font-weight: 700; color: #166534; font-size: 0.95rem; margin-bottom: 6px;">
                    📊 Evidencia Empírica de Impacto y Evaluaciones Ex-Post:
                </div>
                <div style="font-size: 0.85rem; color: #14532d; line-height: 1.6;">
                    {spec['impact_evidence']}
                </div>
            </div>
            """), unsafe_allow_html=True)

        with c_arg2:
            st.markdown(textwrap.dedent(f"""
            <div style="background-color: #eff6ff; border: 1.5px solid #93c5fd; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;">
                <div style="font-weight: 700; color: #1e40af; font-size: 0.95rem; margin-bottom: 6px;">
                    🏛️ Estrategia de Defensa en Subcomisión Mixta:
                </div>
                <div style="font-size: 0.85rem; color: #1e3a8a; line-height: 1.6;">
                    {spec['defense_strategy']}
                </div>
            </div>
            """), unsafe_allow_html=True)

        st.markdown("###### 📝 Glosa Presupuestaria Propuesta (Borrador de Indicación Parlamentaria):")
        st.caption("Texto listo para ser patrocinado o propuesto como indicación parlamentaria en la tramitación del Proyecto de Ley de Presupuestos 2027:")

        st.code(spec['proposed_rider'], language="text")

        st.download_button(
            label="📄 Descargar Ficha Técnica de Defensa (Texto)",
            data=(
                f"FICHA TÉCNICA DE DEFENSA PRESUPUESTARIA - EJERCICIO FISCAL 2027\n"
                f"PROGRAMA: {spec['name']}\n"
                f"MARCO LEGAL: {spec['legal_framework']}\n"
                f"NIVEL DE RIESGO: {spec['risk_level']}\n"
                f"ASIGNACIÓN: {spec['budget_codes']['partida']} - {spec['budget_codes']['capitulo']} - {spec['budget_codes']['subtitulos']}\n\n"
                f"DIAGNÓSTICO DE AMENAZA:\n{spec['threat_diagnosis']}\n\n"
                f"EVIDENCIA EMPÍRICA:\n{spec['impact_evidence']}\n\n"
                f"ESTRATEGIA PARLAMENTARIA:\n{spec['defense_strategy']}\n\n"
                f"GLOSA CONDICIONANTE PROPUESTA:\n{spec['proposed_rider']}\n"
            ),
            file_name=f"ficha_defensa_{sel_prog_id}_2027.txt",
            mime="text/plain",
            key=f"btn_dl_ficha_{sel_prog_id}"
        )

    # --------------------------------------------------------------------------
    # SUB-TAB 4: CUENTAS GRANULARES Y GLOSAS
    # --------------------------------------------------------------------------
    with tab_cuentas:
        st.markdown("##### 📑 Cuentas y Asignaciones Granulares en Base de Datos")
        st.caption(f"Desglose de subtítulos, ítems y asignaciones presupuestarias para **{spec['short_name']}** ({periodo} {year}).")

        with st.spinner("Extrayendo partidas presupuestarias asociadas..."):
            df_det = pm.get_program_detail_records(sel_prog_id, year=year, periodo=periodo, moneda=moneda)

        if df_det.empty:
            st.info("No se encontraron desagregaciones a nivel de ítem para este programa.")
        else:
            col_det_exp1, col_det_exp2, _ = st.columns([2.5, 2.5, 5])
            with col_det_exp1:
                excel_det_name = f"cuentas_{sel_prog_id}_{year}_{periodo}.xlsx"
                excel_det_path = config.EXPORTS_DIR / excel_det_name
                df_det.to_excel(excel_det_path, index=False)
                with open(excel_det_path, "rb") as f:
                    st.download_button(
                        "📥 Descargar Cuentas (Excel)",
                        data=f.read(),
                        file_name=excel_det_name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key=f"btn_dl_det_excel_{sel_prog_id}"
                    )
            with col_det_exp2:
                st.download_button(
                    "📥 Descargar Cuentas (CSV)",
                    data=df_det.to_csv(index=False).encode('utf-8-sig'),
                    file_name=f"cuentas_{sel_prog_id}_{year}_{periodo}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key=f"btn_dl_det_csv_{sel_prog_id}"
                )

            st.dataframe(
                df_det[[
                    "programa", "subtitulo_cod", "subtitulo_nom", "item_cod", "item_nom",
                    "p_ini_mm", "p_vig_mm", "pct_change", "p_eje_mm", "pct_eje"
                ]].style.format({
                    "p_ini_mm": "${:,.2f} MM",
                    "p_vig_mm": "${:,.2f} MM",
                    "pct_change": "{:+.1f}%",
                    "p_eje_mm": "${:,.2f} MM",
                    "pct_eje": "{:.1f}%"
                }),
                use_container_width=True,
                height=350
            )

    # ==============================================================================
    # 7. HOJA DE RUTA LEGISLATIVA PARA LA COMISIÓN MIXTA 2027
    # ==============================================================================
    st.markdown("---")
    st.markdown("### 🏛️ Estrategia y Mecanismos de Blindaje en el Congreso Nacional")
    
    col_st1, col_st2, col_st3 = st.columns(3)
    with col_st1:
        st.markdown(textwrap.dedent("""
        <div style="background-color: #ffffff; border: 1.5px solid #cbd5e1; border-top: 4px solid #2563eb; border-radius: 8px; padding: 14px; min-height: 180px;">
            <div style="font-weight: 700; color: #1e3a8a; font-size: 0.95rem; margin-bottom: 6px;">
                1️⃣ Activación en Subcomisiones
            </div>
            <div style="font-size: 0.82rem; color: #475569; line-height: 1.5;">
                Focalizar el debate en la <b>Segunda Subcomisión</b> (Salud, Trabajo y Desarrollo Social) y la <b>Cuarta Subcomisión</b> (Educación). Usar la evidencia causal de DIPRES, SIMCE y Casen para bloquear justificaciones de indisponibilidad fiscal.
            </div>
        </div>
        """), unsafe_allow_html=True)
    with col_st2:
        st.markdown(textwrap.dedent("""
        <div style="background-color: #ffffff; border: 1.5px solid #cbd5e1; border-top: 4px solid #ea580c; border-radius: 8px; padding: 14px; min-height: 180px;">
            <div style="font-weight: 700; color: #9a3412; font-size: 0.95rem; margin-bottom: 6px;">
                2️⃣ Glosas Condicionantes
            </div>
            <div style="font-size: 0.82rem; color: #475569; line-height: 1.5;">
                Redactar glosas vinculantes que fijen pisos mínimos intransferibles de ejecución. Exigir la apertura de concursos de ampliación de red (Liceos Bicentenario, CEDIAM) e impedir traspasos hacia gasto corriente de subsecretarías.
            </div>
        </div>
        """), unsafe_allow_html=True)
    with col_st3:
        st.markdown(textwrap.dedent("""
        <div style="background-color: #ffffff; border: 1.5px solid #cbd5e1; border-top: 4px solid #dc2626; border-radius: 8px; padding: 14px; min-height: 180px;">
            <div style="font-weight: 700; color: #991b1b; font-size: 0.95rem; margin-bottom: 6px;">
                3️⃣ Palanca de Negociación Mixta
            </div>
            <div style="font-size: 0.82rem; color: #475569; line-height: 1.5;">
                Reservar y rechazar transitoriamente en bloque las partidas de <b>administración central</b> de Mineduc, Salud y MDSF. Esto históricamente obliga a Hacienda a patrocinar indicaciones de reposición y blindaje de programas emblemáticos.
            </div>
        </div>
        """), unsafe_allow_html=True)
