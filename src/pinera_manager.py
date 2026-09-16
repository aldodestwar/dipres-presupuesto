"""
Módulo de Gestión, Análisis Técnico y Estrategia de Defensa Presupuestaria
de los Programas del Presidente Sebastián Piñera (2010-2014 / 2018-2022).
"""
import sqlite3
from typing import Dict, List, Optional, Any
import pandas as pd
from config import DB_PATH

# ==============================================================================
# CATASTRO Y REGISTRO ESTRATÉGICO DE LOS PROGRAMAS DEL PDTE. SEBASTIÁN PIÑERA
# ==============================================================================
PINERA_PROGRAMS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "liceos_bicentenario": {
        "id": "liceos_bicentenario",
        "name": "Liceos Bicentenario de Excelencia",
        "short_name": "Liceos Bicentenario",
        "category": "Educación y Capital Humano",
        "ministerio": "Ministerio de Educación",
        "risk_level": "Crítico",
        "badge_color": "#e11d48",  # Rose/Red
        "legal_framework": "Creado en 2010 (Piñera I); ampliado a 420 recintos (Piñera II)",
        "target_population": "420 liceos técnico-profesionales, científico-humanistas y artísticos (~250.000 estudiantes vulnerables).",
        "budget_codes": {
            "partida": "09 (Ministerio de Educación)",
            "capitulo": "01 (Subsecretaría de Educación)",
            "programa": "01 y 02",
            "subtitulos": "Subtítulo 24 (Transferencias Corrientes) y Subtítulo 33 (Transferencias de Capital)",
            "glosas": "Glosas de Excelencia Pedagógica, Fortalecimiento de Talleres y Equipamiento Técnico"
        },
        "threat_diagnosis": (
            "Intentos sistemáticos de reducción presupuestaria en ejercicios anteriores (-24,7% en Subtítulo 24 y "
            "-13,9% en Subtítulo 33), asfixiando los convenios de perfeccionamiento pedagógico, evaluación continua "
            "y reposición de maquinaria en talleres técnicos."
        ),
        "impact_evidence": (
            "Evaluaciones de Impacto DIPRES y Agencia de Calidad confirman rendimientos sistemática y estadísticamente "
            "superiores en pruebas SIMCE y PAES frente a establecimientos municipales y SLEP con idéntico nivel socioeconómico. "
            "Mayor tasa de titulación oportuna e inserción en educación superior con alta tasa de retorno social."
        ),
        "defense_strategy": (
            "Condicionar la aprobación de los fondos de administración central del Mineduc (Partida 09, Cap. 01) "
            "al mantenimiento íntegro de las asignaciones de excelencia pedagógica (Subtítulo 24) y capital (Subtítulo 33), "
            "con glosa que mandate convocatorias concursables obligatorias para nuevas cohortes de liceos."
        ),
        "proposed_rider": (
            "Glosa XX: 'Los recursos asignados al Programa Liceos Bicentenario de Excelencia no podrán ser objeto de disminuciones "
            "administrativas ni reasignaciones a otros programas del Ministerio. La Subsecretaría deberá convocar durante el primer "
            "trimestre a un concurso nacional de incorporación a la red para al menos 50 nuevos establecimientos escolares.'"
        ),
        "sql_condition": """
            ministerio LIKE '%Educaci%' 
            AND (UPPER(item_nom) LIKE '%BICENTENARIO%' OR UPPER(clasificacion) LIKE '%BICENTENARIO%' OR UPPER(programa) LIKE '%BICENTENARIO%')
            AND nivel IN ('ITEM', 'ASIGNACION', 'SUBTITULO')
        """
    },

    "pgu": {
        "id": "pgu",
        "name": "Pensión Garantizada Universal (PGU)",
        "short_name": "Pensión Garantizada (PGU)",
        "category": "Seguridad Social y Empleo",
        "ministerio": "Ministerio del Trabajo y Previsión Social",
        "risk_level": "Moderada a Severa",
        "badge_color": "#ea580c",  # Orange
        "legal_framework": "Ley N° 21.419 de enero de 2022 (Piñera II)",
        "target_population": "Cobertura cuasi-universal para el 90% de la población de 65 años y más (más de 2,1 millones de pensionados).",
        "budget_codes": {
            "partida": "15 (Ministerio del Trabajo y Previsión Social)",
            "capitulo": "05 / 08 (Instituto de Previsión Social - IPS)",
            "programa": "01 y 02",
            "subtitulos": "Subtítulo 23 (Prestaciones Previsionales) y Subtítulo 24 (Transferencias Corrientes)",
            "glosas": "Representa más del 56% del presupuesto ministerial consolidado."
        },
        "threat_diagnosis": (
            "El compromiso legal y programático de converger hacia una asignación de $250.000 mensuales presiona los "
            "techos de gasto de Hacienda. Riesgo inminente de que el Ejecutivo intente modular, dilatar o subordinar el "
            "beneficio a la recaudación de reformas o integrarlo a fondos colectivos administrados discrecionalmente."
        ),
        "impact_evidence": (
            "Viraje estructural en el pilar solidario que superó la focalización del antiguo APS y PBS. La PGU ha sido "
            "el instrumento más eficaz en la reducción histórica de la pobreza en la tercera edad en Chile, mejorando "
            "las tasas de reemplazo del 80% más vulnerable en más de 30 puntos porcentuales."
        ),
        "defense_strategy": (
            "Defender la intangibilidad del derecho previsional adquirido. La PGU debe permanecer como beneficio no "
            "contributivo de financiamiento general del Estado. Exigir informe actuarial y prohibir la creación de "
            "requisitos adicionales de postulación o trabas al cobro retroactivo."
        ),
        "proposed_rider": (
            "Glosa XX: 'El Instituto de Previsión Social garantizará la entrega ininterrumpida de la Pensión Garantizada Universal "
            "a la totalidad del universo legalmente habilitado bajo la Ley N° 21.419. Se prohíbe cualquier transferencia o redirección "
            "de estos fondos hacia otros componentes de seguridad social o administración previsional.'"
        ),
        "sql_condition": """
            ministerio LIKE '%Trabajo%' 
            AND (UPPER(item_nom) LIKE '%GARANTIZADA%' OR UPPER(clasificacion) LIKE '%GARANTIZADA%')
            AND nivel IN ('ITEM', 'ASIGNACION')
        """
    },

    "ingreso_etico": {
        "id": "ingreso_etico",
        "name": "Ingreso Ético Familiar / Seguridades y Oportunidades",
        "short_name": "Ingreso Ético Familiar",
        "category": "Seguridad Social y Empleo",
        "ministerio": "Ministerio de Desarrollo Social y Familia",
        "risk_level": "Media",
        "badge_color": "#d97706",  # Amber
        "legal_framework": "Ley N° 20.595 de 2012 (Piñera I)",
        "target_population": "Familias y personas en extrema pobreza y vulnerabilidad bio-psicosocial a nivel nacional.",
        "budget_codes": {
            "partida": "21 (Ministerio de Desarrollo Social y Familia)",
            "capitulo": "01 (Subsecretaría de Servicios Sociales)",
            "programa": "05 (Ingreso Ético Familiar y Sistema Seguridades y Oportunidades)",
            "subtitulos": "Subtítulo 24 (Transferencias Corrientes a personas y convenios municipales)",
            "glosas": "Bono Logro Escolar, Subsidio al Empleo, Acompañamiento Psicosocial"
        },
        "threat_diagnosis": (
            "Tendencia burocrática a desfinanciar los convenios municipales de acompañamiento psicosocial y sociolaboral, "
            "diluyendo el programa hacia una transferencia puramente asistencial sin activación de capital humano."
        ),
        "impact_evidence": (
            "Diseño premiado internacionalmente que combina transferencias condicionadas (Dignidad, Deberes y Logros) "
            "con tutores comunitarios. El Bono por Logro Escolar incentiva el mérito directo en el 30% más vulnerable sin "
            "intermediación política."
        ),
        "defense_strategy": (
            "Blindar el presupuesto de los convenios comunales en el Subtítulo 24 e indexar el Bono por Logro Escolar a la "
            "inflación acumulada para resguardar su poder adquisitivo frente al incremento del costo de la canasta básica."
        ),
        "proposed_rider": (
            "Glosa XX: 'De los recursos asignados al Programa Ingreso Ético Familiar, al menos el 25% se destinará exclusivamente "
            "a la ejecución de convenios comunales para el acompañamiento sociolaboral y psicosocial continuo de las familias beneficiarias.'"
        ),
        "sql_condition": """
            ministerio LIKE '%Desarrollo Social%'
            AND (UPPER(programa) LIKE '%INGRESO ETICO%' OR UPPER(programa) LIKE '%SEGURIDADES%')
            AND nivel = 'TIPO' AND tipo = 'GASTOS'
        """
    },

    "btm": {
        "id": "btm",
        "name": "Bono al Trabajo de la Mujer (BTM)",
        "short_name": "Bono Trabajo Mujer",
        "category": "Seguridad Social y Empleo",
        "ministerio": "Ministerio del Trabajo y Previsión Social",
        "risk_level": "Baja a Media",
        "badge_color": "#059669",  # Emerald
        "legal_framework": "Ley N° 20.595 de 2012 (Componente IEF, Piñera I)",
        "target_population": "Mujeres trabajadoras (dependientes e independientes) de 25 a 59 años del 40% del RSH.",
        "budget_codes": {
            "partida": "15 (Ministerio del Trabajo y Previsión Social)",
            "capitulo": "05 (SENCE - Servicio Nacional de Capacitación y Empleo)",
            "programa": "04 (Servicio Nacional de Capacitación y Empleo - Empleo)",
            "subtitulos": "Subtítulo 24, Ítem 01 (Al Sector Privado - Subsidio Empleo a la Mujer)",
            "glosas": "Aporte directo a la trabajadora y complemento al empleador"
        },
        "threat_diagnosis": (
            "En 2026 sufrió un drástico recorte administrativo que redujo su presupuesto vigente de $107.7 MM a $45.3 MM (-57.97%). "
            "Tras la extinción del IMG, recortar el BTM destruye el incentivo más efectivo a la formalización laboral femenina."
        ),
        "impact_evidence": (
            "Evaluaciones de la DIPRES certifican aumentos permanentes en las tasas de empleo formal femenino, reducción "
            "de la brecha salarial de género en el decil más pobre y estímulo a la contratación formal por parte de pymes."
        ),
        "defense_strategy": (
            "Denunciar el recorte acumulado en 2026 y reponer el piso basal de al menos $105 mil millones en el Subtítulo 24 "
            "de SENCE, condicionando la aprobación del presupuesto ministerial a la restitución de estos fondos."
        ),
        "proposed_rider": (
            "Glosa XX: 'La partida asignada al Subsidio al Empleo de la Mujer (BTM) Ley N° 20.595 no podrá ser reducida durante el ejercicio "
            "presupuestario. El SENCE informará trimestralmente a la Comisión Mixta de Presupuestos la nómina de beneficiarias y montos liquidados.'"
        ),
        "sql_condition": """
            ministerio LIKE '%Trabajo%' 
            AND (clasificacion LIKE '%Subsidio Empleo a la Mujer%' OR clasificacion LIKE '%Bono%Mujer%')
            AND nivel IN ('ITEM', 'ASIGNACION')
        """
    },

    "hospital_digital": {
        "id": "hospital_digital",
        "name": "Hospital Digital (Telemedicina APS)",
        "short_name": "Hospital Digital",
        "category": "Salud y Telemedicina",
        "ministerio": "Ministerio de Salud",
        "risk_level": "Alta",
        "badge_color": "#ea580c",  # Orange
        "legal_framework": "Iniciativa Estratégica Sectorial 2019 (Piñera II)",
        "target_population": "Población beneficiaria de Fonasa en todo Chile; más de 1.090.000 atenciones remotas anuales.",
        "budget_codes": {
            "partida": "16 (Ministerio de Salud)",
            "capitulo": "10 (Subsecretaría de Redes Asistenciales)",
            "programa": "01 (Hospital Digital)",
            "subtitulos": "Subtítulo 22 (Servicios Informáticos y de Telecomunicaciones) y Subtítulo 29",
            "glosas": "Asignación 429, Glosas 09 y 23 de interoperabilidad médica"
        },
        "threat_diagnosis": (
            "Riesgo de absorción burocrática y desfinanciamiento de sus contratos de soporte informático en el Subtítulo 22, "
            "desviando recursos a financiar déficits operacionales de hospitales de la red central."
        ),
        "impact_evidence": (
            "Procesa anualmente más de 82.000 interconsultas sincrónicas y 1.090.000 diagnósticos en teledermatología, teleoftalmología "
            "y mamografía remota. Costo por resolución diagnóstica hasta 70% inferior al traslado físico de especialistas."
        ),
        "defense_strategy": (
            "Exigir autonomía técnica e indivisibilidad de la Asignación 429 de Redes Asistenciales. Prohibir el traspaso de sus fondos "
            "a gastos corrientes hospitalarios y fijar metas de reducción de listas de espera de especialidades."
        ),
        "proposed_rider": (
            "Glosa XX: 'Los recursos de la Asignación 429 destinados a Hospital Digital son de afectación exclusiva para la provisión "
            "de telemedicina sincrónica y asincrónica en la red pública de salud. Se prohíbe expresamente su reasignación a gasto hospitalario común.'"
        ),
        "sql_condition": """
            ministerio LIKE '%Salud%'
            AND (UPPER(programa) LIKE '%HOSPITAL DIGITAL%' OR UPPER(item_nom) LIKE '%HOSPITAL DIGITAL%' OR UPPER(clasificacion) LIKE '%HOSPITAL DIGITAL%')
        """
    },

    "fondo_cancer": {
        "id": "fondo_cancer",
        "name": "Ley y Fondo Nacional del Cáncer",
        "short_name": "Fondo Nacional del Cáncer",
        "category": "Salud y Telemedicina",
        "ministerio": "Ministerio de Salud",
        "risk_level": "Media a Alta",
        "badge_color": "#d97706",
        "legal_framework": "Ley N° 21.258 de agosto de 2020 (Piñera II)",
        "target_population": "Pacientes oncológicos de la red pública de salud en todo el territorio nacional.",
        "budget_codes": {
            "partida": "16 (Ministerio de Salud)",
            "capitulo": "01 / 02 (Subsecretaría de Salud Pública y Redes Asistenciales)",
            "programa": "01 y 02",
            "subtitulos": "Subtítulo 24 (Investigación), Subtítulo 29 (Equipos Médicos) y Subtítulo 33 (Capital)",
            "glosas": "Adquisición de Aceleradores Lineales y Terapias de Alto Costo"
        },
        "threat_diagnosis": (
            "Recortes administrativos y retrasos en las compras de equipamiento de radioterapia de alta gama (-$2.150 millones "
            "en ejercicios precedentes), diluyendo la ejecución diferida del fondo en la tesorería central del Minsal."
        ),
        "impact_evidence": (
            "Marco regulatorio que reconoció el cáncer como prioridad sanitaria de Estado. El Fondo financia ensayos clínicos, "
            "equipamiento de última generación y coberturas complementarias no contempladas en los decretos GES."
        ),
        "defense_strategy": (
            "Blindar la asignación de capital para maquinaria oncológica y exigir que la DIPRES rinda semestralmente el estado "
            "financiero de la cuenta especial del Fondo Nacional del Cáncer."
        ),
        "proposed_rider": (
            "Glosa XX: 'El Ministerio de Salud ejecutará con prioridad las licitaciones públicas de equipamiento oncológico y "
            "aceleradores lineales con cargo al Fondo Nacional del Cáncer Ley N° 21.258, no pudiendo reducirse sus fondos de capital.'"
        ),
        "sql_condition": """
            ministerio LIKE '%Salud%'
            AND (UPPER(item_nom) LIKE '%C%NCER%' OR UPPER(clasificacion) LIKE '%C%NCER%' OR UPPER(programa) LIKE '%C%NCER%')
        """
    },

    "mejor_ninez": {
        "id": "mejor_ninez",
        "name": "Servicio Mejor Niñez (Protección Especializada)",
        "short_name": "Mejor Niñez",
        "category": "Protección a la Niñez y Reinserción",
        "ministerio": "Ministerio de Desarrollo Social y Familia",
        "risk_level": "Alta",
        "badge_color": "#ea580c",
        "legal_framework": "Ley N° 21.302 de 2021 (Piñera II)",
        "target_population": "Más de 102.500 plazas en programas ambulatorios, residenciales y familias de acogida.",
        "budget_codes": {
            "partida": "21 (Ministerio de Desarrollo Social y Familia)",
            "capitulo": "Servicio Nacional de Protección Especializada a la Niñez y Adolescencia",
            "programa": "01 (Dirección Nacional y Direcciones Regionales)",
            "subtitulos": "Subtítulo 21 (Personal), Subtítulo 24 (Transferencias a Residencias y FAE)",
            "glosas": "Estándares residenciales familiares y fiscalización de convenios"
        },
        "threat_diagnosis": (
            "Recurrentes problemas de subejecución presupuestaria que exponen al servicio a recortes por parte de DIPRES, "
            "perjudicando la cobertura del programa FAE y la mantención digna de residencias familiares."
        ),
        "impact_evidence": (
            "Superó la nefasta estructura del antiguo Sename de protección infantil, estableciendo un estándar técnico "
            "centrado en la reintegración familiar, la desinstitucionalización y el resguardo de derechos fundamentales."
        ),
        "defense_strategy": (
            "Impedir la devolución o recorte de saldos no ejecutados, mandatando su redistribución interna mediante glosa "
            "hacia las residencias de administración directa y a la ampliación de cobertura del programa FAE."
        ),
        "proposed_rider": (
            "Glosa XX: 'Los saldos no devengados al tercer trimestre por el Servicio Mejor Niñez serán automáticamente asignados "
            "al fortalecimiento del Programa de Familias de Acogida Especializadas (FAE) y a mejoras de infraestructura residencial.'"
        ),
        "sql_condition": """
            ministerio LIKE '%Desarrollo Social%'
            AND (UPPER(programa) LIKE '%MEJOR NI%' OR UPPER(programa) LIKE '%PROTECCI%N ESPECIALIZADA%')
            AND nivel = 'TIPO' AND tipo = 'GASTOS'
        """
    },

    "reinsercion_juvenil": {
        "id": "reinsercion_juvenil",
        "name": "Servicio Nacional de Reinserción Social Juvenil",
        "short_name": "Reinserción Social Juvenil",
        "category": "Protección a la Niñez y Reinserción",
        "ministerio": "Ministerio de Justicia y Derechos Humanos",
        "risk_level": "Crítico",
        "badge_color": "#e11d48",
        "legal_framework": "Ley N° 21.527 (promulgada en 2022/2023, Piñera II)",
        "target_population": "Adolescentes y jóvenes infractores de la Ley de Responsabilidad Penal Adolescente (N° 20.084).",
        "budget_codes": {
            "partida": "10 (Ministerio de Justicia y Derechos Humanos)",
            "capitulo": "Servicio Nacional de Reinserción Social Juvenil",
            "programa": "01 y centros de administración directa",
            "subtitulos": "Subtítulo 21 (Personal técnico y mediadores) y Subtítulo 33 (Adecuación de Centros)",
            "glosas": "Entrada en régimen Macrozona Centro (RM, Valparaíso, Maule)"
        },
        "threat_diagnosis": (
            "La entrada en régimen de la Macrozona Centro (más del 60% de los casos penales juveniles de Chile) requiere "
            "expansiones operativas ineludibles. Cualquier retraso presupuestario en 2026/2027 provocará el colapso de la reforma."
        ),
        "impact_evidence": (
            "Separa definitivamente la justicia penal juvenil del sistema proteccional. Introduce mediación penal, estándares "
            "especializados de intervención psicosocial y modelos efectivos para quebrar carreras delictivas tempranas."
        ),
        "defense_strategy": (
            "Exigir en la Comisión Mixta el financiamiento total del cronograma de despliegue en Santiago y regiones centrales, "
            "impidiendo que los centros queden operando en precariedad administrativa."
        ),
        "proposed_rider": (
            "Glosa XX: 'El Ministerio de Hacienda asegurará la disponibilidad de recursos para la entrada en régimen del Servicio "
            "Nacional de Reinserción Social Juvenil en las regiones de Valparaíso, Metropolitana y Maule, sin restricciones de dotación.'"
        ),
        "sql_condition": """
            ministerio LIKE '%Justicia%'
            AND UPPER(programa) LIKE '%REINSERCI%N SOCIAL JUVENIL%'
            AND nivel = 'TIPO' AND tipo = 'GASTOS'
        """
    },

    "monitoreo_telematico": {
        "id": "monitoreo_telematico",
        "name": "Monitoreo Telemático en Violencia Intrafamiliar (Tobilleras)",
        "short_name": "Monitoreo Telemático VIF",
        "category": "Seguridad y Control Fronterizo",
        "ministerio": "Ministerio de Justicia y Derechos Humanos",
        "risk_level": "Media",
        "badge_color": "#d97706",
        "legal_framework": "Ley N° 21.378 de 2021 (Piñera II)",
        "target_population": "Víctimas de violencia intrafamiliar con medidas cautelares en tribunales de familia y garantía.",
        "budget_codes": {
            "partida": "10 (Ministerio de Justicia y Derechos Humanos)",
            "capitulo": "04 (Gendarmería de Chile)",
            "programa": "01 (Operaciones Penitenciarias)",
            "subtitulos": "Subtítulo 22 (Bienes y Servicios de Consumo - Servicios Satelitales e Informáticos)",
            "glosas": "Licitaciones y convenios de conectividad GPS / tobilleras telemáticas"
        },
        "threat_diagnosis": (
            "Presiones de ajuste en el Subtítulo 22 asociadas a licitaciones informáticas pueden provocar escasez de tobilleras "
            "activas, generando listas de espera críticas en la aplicación de medidas de protección a mujeres en riesgo vital."
        ),
        "impact_evidence": (
            "Revolucionó la protección judicial preventiva: permite monitorear electrónicamente el perímetro de exclusión "
            "en tiempo real, alertando de forma inmediata a Carabineros y a la víctima ante cualquier acercamiento del agresor."
        ),
        "defense_strategy": (
            "Declarar prioritario el financiamiento de los contratos de telecomunicaciones de Gendarmería en el Subtítulo 22 "
            "e impedir cualquier tope presupuestario que limite la entrega de dispositivos ordenados por jueces de familia."
        ),
        "proposed_rider": (
            "Glosa XX: 'Gendarmería de Chile asegurará la disponibilidad permanente de dispositivos de monitoreo telemático para dar "
            "cumplimiento inmediato a las órdenes cautelares bajo la Ley N° 21.378, sin límite presupuestario por tribunal.'"
        ),
        "sql_condition": """
            ministerio LIKE '%Justicia%' 
            AND programa LIKE '%Gendarmer%' 
            AND subtitulo_cod = '22'
        """
    },

    "sermig": {
        "id": "sermig",
        "name": "Servicio Nacional de Migraciones (SERMIG)",
        "short_name": "Servicio Migraciones",
        "category": "Seguridad y Control Fronterizo",
        "ministerio": "Ministerio del Interior y Seguridad Pública",
        "risk_level": "Alta",
        "badge_color": "#ea580c",
        "legal_framework": "Ley N° 21.325 de Migración y Extranjería de 2021 (Piñera II)",
        "target_population": "Control de regularidad migratoria, biometría fronteriza y ejecución de expulsiones judiciales y administrativas.",
        "budget_codes": {
            "partida": "05 (Ministerio del Interior y Seguridad Pública)",
            "capitulo": "Servicio Nacional de Migraciones",
            "programa": "01 (Gestión Migratoria)",
            "subtitulos": "Subtítulo 22 (Arriendo de Vuelos Chárter y Biometría) y Subtítulo 24",
            "glosas": "Glosas de Financiamiento para Operativos de Reconducción y Expulsión"
        },
        "threat_diagnosis": (
            "Frecuentes recortes y trabas administrativas a las glosas de arriendo de aviones chárter para la ejecución "
            "efectiva de decretos de expulsión, debilitando el principio de migración ordenada, segura y regular."
        ),
        "impact_evidence": (
            "Modernizó el arcaico Departamento de Extranjería de 1975, creando una institucionalidad descentralizada dotada "
            "de facultades para empadronar, sancionar la irregularidad y agilizar los procedimientos sancionatorios."
        ),
        "defense_strategy": (
            "Garantizar la suficiencia de recursos para vuelos chárter de expulsión y empadronamiento biométrico fronterizo, "
            "condicionando la aprobación del presupuesto del Ministerio del Interior a metas de expulsiones ejecutadas."
        ),
        "proposed_rider": (
            "Glosa XX: 'Se destinarán al menos $5.000 millones exclusivamente a la contratación de vuelos chárter y operativos "
            "logísticos para la materialización de órdenes de expulsión judicial y administrativa de ciudadanos extranjeros infractores.'"
        ),
        "sql_condition": """
            (UPPER(programa) LIKE '%SERVICIO NACIONAL DE MIGRACIONES%' OR UPPER(programa) LIKE '%DEPARTAMENTO DE EXTRANJER%')
            AND nivel = 'TIPO' AND tipo = 'GASTOS'
        """
    },

    "cediam_senama": {
        "id": "cediam_senama",
        "name": "Centros Diurnos del Adulto Mayor (CEDIAM / SENAMA)",
        "short_name": "Centros Diurnos (CEDIAM)",
        "category": "Seguridad Social y Empleo",
        "ministerio": "Ministerio de Desarrollo Social y Familia",
        "risk_level": "Media",
        "badge_color": "#d97706",
        "legal_framework": "Plan Adulto Mejor (2018–2022, Piñera II)",
        "target_population": "Adultos mayores con dependencia leve o moderada en convenios comunales en todo Chile.",
        "budget_codes": {
            "partida": "21 (Ministerio de Desarrollo Social y Familia)",
            "capitulo": "02 (Servicio Nacional del Adulto Mayor - SENAMA)",
            "programa": "01 (Servicio Nacional del Adulto Mayor)",
            "subtitulos": "Subtítulo 24, Ítem 03 (Convenios Municipales y Organizaciones de Adulto Mayor)",
            "glosas": "Atención diurna biopsicosocial comunal"
        },
        "threat_diagnosis": (
            "Dispersión territorial y riesgo de contracción en transferencias corrientes a municipios, recortando horas de talleres "
            "y personal kinesiológico y psicológico en centros diurnos locales."
        ),
        "impact_evidence": (
            "Estudios de costo-efectividad de SENAMA demuestran que la permanencia en un CEDIAM frena el deterioro cognitivo y físico, "
            "retrasando en hasta 4 años la internación en un ELEAM institucionalizado (con un costo fiscal 5 veces menor)."
        ),
        "defense_strategy": (
            "Resguardar los convenios municipales en el Subtítulo 24 e impedir la merma en el financiamiento por usuario atendido."
        ),
        "proposed_rider": (
            "Glosa XX: 'Los convenios comunales para Centros Diurnos del Adulto Mayor (CEDIAM) suscritos con municipios mantendrán "
            "su dotación presupuestaria indexada al IPC, asegurando la continuidad de las atenciones terapéuticas sin interrupción.'"
        ),
        "sql_condition": """
            ministerio LIKE '%Desarrollo Social%'
            AND (UPPER(item_nom) LIKE '%CENTROS DIURNOS%' OR UPPER(clasificacion) LIKE '%CENTROS DIURNOS%' OR (UPPER(programa) LIKE '%ADULTO MAYOR%' AND subtitulo_cod = '24'))
            AND nivel IN ('ITEM', 'ASIGNACION', 'SUBTITULO')
        """
    },

    "subsidios_ds1_ds52": {
        "id": "subsidios_ds1_ds52",
        "name": "Subsidios Habitacionales DS 1 y DS 52 (Sectores Medios y Arriendo)",
        "short_name": "Subsidios DS 1 y DS 52",
        "category": "Vivienda y Hábitat",
        "ministerio": "Ministerio de Vivienda y Urbanismo",
        "risk_level": "Alta",
        "badge_color": "#ea580c",
        "legal_framework": "DS N° 1 de 2011 (Sectores Medios) y DS N° 52 de 2013 (Arriendo) (Piñera I)",
        "target_population": "Clases medias y familias vulnerables con copago, ahorro y capacidad de endeudamiento formal.",
        "budget_codes": {
            "partida": "18 (Ministerio de Vivienda y Urbanismo)",
            "capitulo": "SERVIU Regionales (Regiones I a XVI)",
            "programa": "Programas Regionales de Vivienda",
            "subtitulos": "Subtítulo 33, Ítem 01 ('Sistema Integrado de Subsidio' y 'Subsidio al Arriendo')",
            "glosas": "Llamados regulares a postulación individual y colectiva"
        },
        "threat_diagnosis": (
            "Reorientación masiva de caudales del Minvu hacia la adquisición directa estatal bajo el Plan de Emergencia Habitacional, "
            "dejando sin subsidios a la clase media con capacidad de ahorro hipotecario."
        ),
        "impact_evidence": (
            "Pilar de la política habitacional chilena moderna: premia el esfuerzo y el ahorro familiar previo, movilizando inversión "
            "privada e impidiendo la segregación socioespacial mediante el acceso a viviendas de alto estándar constructivo."
        ),
        "defense_strategy": (
            "Defender los fondos del 'Sistema Integrado de Subsidio' y 'Subsidio al Arriendo' en el Subtítulo 33 de los SERVIU, "
            "exigiendo calendarios públicos de llamados anuales regulares."
        ),
        "proposed_rider": (
            "Glosa XX: 'El Ministerio de Vivienda y Urbanismo asegurará la realización de al menos dos llamados anuales de postulación "
            "al Subsidio de Sectores Medios (DS 1) y de Arriendo (DS 52), resguardando los fondos de transferencia de capital en SERVIU.'"
        ),
        "sql_condition": """
            ministerio LIKE '%Vivienda%' 
            AND subtitulo_cod = '33' 
            AND (UPPER(clasificacion) LIKE '%INTEGRADO DE SUBSIDIO%' OR UPPER(clasificacion) LIKE '%ARRIENDO%')
        """
    },

    "elige_vivir_sano": {
        "id": "elige_vivir_sano",
        "name": "Sistema Elige Vivir Sano",
        "short_name": "Elige Vivir Sano",
        "category": "Salud y Telemedicina",
        "ministerio": "Ministerio de Desarrollo Social y Familia",
        "risk_level": "Media",
        "badge_color": "#d97706",
        "legal_framework": "Leyes N° 20.606 y N° 20.670 (Piñera I)",
        "target_population": "Comunidades escolares, municipios y familias vulnerables en prevención de obesidad y sedentarismo.",
        "budget_codes": {
            "partida": "21 (Desarrollo Social) / Partida 16 (Salud)",
            "capitulo": "01 (Subsecretaría de Servicios Sociales)",
            "programa": "01 / Planes Locales MCCS",
            "subtitulos": "Subtítulo 24 (Transferencias a Municipios)",
            "glosas": "Planes de Promoción Comunal de Salud y Alimentación Saludable"
        },
        "threat_diagnosis": (
            "Riesgo de dispersión técnica y desvío de recursos hacia campañas comunicacionales centralizadas, sin impacto "
            "directo en las ferias libres, escuelas y polideportivos comunales."
        ),
        "impact_evidence": (
            "Marco pionero de salud preventiva intersectorial: articula deporte, nutrición y vida familiar para frenar la "
            "pandemia de enfermedades crónicas no transmisibles (hipertensión, diabetes tipo 2)."
        ),
        "defense_strategy": (
            "Focalizar los recursos en transferencias directas a los Planes de Promoción de la Salud en Municipios (MCCS), "
            "prohibiendo gastos publicitarios institucionales del gobierno central."
        ),
        "proposed_rider": (
            "Glosa XX: 'Los recursos del Sistema Elige Vivir Sano se destinarán en al menos un 80% a transferencias directas a municipios "
            "para la implementación de ferias vespertinas, canchas deportivas y huertos escolares, prohibiéndose gastos en publicidad central.'"
        ),
        "sql_condition": """
            (UPPER(item_nom) LIKE '%ELIGE VIVIR SANO%' OR UPPER(clasificacion) LIKE '%ELIGE VIVIR SANO%' OR UPPER(programa) LIKE '%ELIGE VIVIR SANO%')
        """
    }
}


# ==============================================================================
# CLASE GESTORA DE DATOS Y CONSULTAS
# ==============================================================================
class PineraManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_program_definition(self, program_id: str) -> Optional[Dict[str, Any]]:
        return PINERA_PROGRAMS_REGISTRY.get(program_id)

    def get_all_definitions(self) -> List[Dict[str, Any]]:
        return list(PINERA_PROGRAMS_REGISTRY.values())

    def get_categories(self) -> List[str]:
        return sorted(list(set(p["category"] for p in PINERA_PROGRAMS_REGISTRY.values())))

    def get_risk_levels(self) -> List[str]:
        return ["Crítico", "Alta", "Moderada a Severa", "Media", "Media a Alta", "Baja a Media"]

    def get_program_kpis(
        self,
        program_id: str,
        year: int = 2026,
        periodo: str = "Julio",
        moneda: str = "Pesos"
    ) -> Dict[str, Any]:
        """
        Calcula los KPIs presupuestarios para un programa específico de Sebastián Piñera.
        """
        spec = PINERA_PROGRAMS_REGISTRY.get(program_id)
        if not spec:
            return {}

        sql_cond = spec["sql_condition"]
        query = f"""
            SELECT 
                SUM(presupuesto_inicial) as p_ini,
                SUM(presupuesto_vigente) as p_vig,
                SUM(ejecucion_acumulada) as p_eje,
                SUM(saldo) as p_sal
            FROM ejecucion_consolidada
            WHERE year = ? AND periodo = ? AND moneda = ?
              AND ({sql_cond})
        """

        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(query, (year, periodo, moneda))
            row = c.fetchone()

            p_ini = float(row[0] or 0.0)
            p_vig = float(row[1] or 0.0)
            p_eje = float(row[2] or 0.0)
            p_sal = float(row[3] or (p_vig - p_eje))

            delta_ley = p_vig - p_ini
            pct_change_ley = (delta_ley / p_ini * 100.0) if p_ini > 0 else 0.0
            pct_ejecucion = (p_eje / p_vig * 100.0) if p_vig > 0 else 0.0

            # Estado Presupuestario
            if delta_ley < -1000:
                if pct_change_ley < -10.0:
                    status = "🔻 Recorte Severo"
                else:
                    status = "🔻 Recorte Moderado"
            elif delta_ley > 1000:
                status = "🔺 Expansión"
            else:
                status = "➖ Sin Modificación"

            # Diagnóstico de Alerta
            if pct_change_ley < -5.0:
                alert = f"⚠️ Recorte de {pct_change_ley:+.1f}% vs Ley Inicial"
            elif pct_ejecucion < 35.0 and periodo in ["Junio", "Julio", "Agosto", "Septiembre"]:
                alert = f"⏳ Alerta de Subejecución ({pct_ejecucion:.1f}% al {periodo})"
            elif pct_change_ley > 5.0:
                alert = f"✅ Suplementación de {pct_change_ley:+.1f}% vs Ley"
            else:
                alert = "Normalidad Presupuestaria"

            return {
                "id": program_id,
                "name": spec["name"],
                "short_name": spec["short_name"],
                "category": spec["category"],
                "ministerio": spec["ministerio"],
                "risk_level": spec["risk_level"],
                "badge_color": spec["badge_color"],
                "year": year,
                "periodo": periodo,
                "moneda": moneda,
                "presupuesto_inicial": p_ini,
                "presupuesto_vigente": p_vig,
                "delta_ley": delta_ley,
                "pct_change_ley": pct_change_ley,
                "ejecucion_acumulada": p_eje,
                "pct_ejecucion": pct_ejecucion,
                "saldo": p_sal,
                "status": status,
                "alert": alert
            }

    def get_all_programs_kpis(
        self,
        year: int = 2026,
        periodo: str = "Julio",
        moneda: str = "Pesos",
        category_filter: Optional[str] = None,
        risk_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retorna la matriz consolidada de KPIs para todos los programas de Piñera.
        """
        rows = []
        for pid in PINERA_PROGRAMS_REGISTRY:
            kpis = self.get_program_kpis(pid, year=year, periodo=periodo, moneda=moneda)
            if not kpis:
                continue

            if category_filter and category_filter != "Todos" and kpis["category"] != category_filter:
                continue

            if risk_filter and risk_filter != "Todos" and kpis["risk_level"] != risk_filter:
                continue

            rows.append(kpis)

        df = pd.DataFrame(rows)
        if not df.empty:
            # Convertir a Miles de Millones (MM) para visualización ejecutiva
            df["ini_mm"] = df["presupuesto_inicial"] * 1000 / 1e9
            df["vig_mm"] = df["presupuesto_vigente"] * 1000 / 1e9
            df["delta_mm"] = df["delta_ley"] * 1000 / 1e9
            df["eje_mm"] = df["ejecucion_acumulada"] * 1000 / 1e9
            df["saldo_mm"] = df["saldo"] * 1000 / 1e9

        return df

    def get_program_history(
        self,
        program_id: str,
        start_year: int = 2018,
        end_year: int = 2026,
        moneda: str = "Pesos"
    ) -> pd.DataFrame:
        """
        Calcula la serie histórica de presupuesto y ejecución de un programa entre start_year y end_year.
        Para años previos a 2026 toma el cierre ('Diciembre'), y para 2026 toma el corte más reciente.
        """
        spec = PINERA_PROGRAMS_REGISTRY.get(program_id)
        if not spec:
            return pd.DataFrame()

        sql_cond = spec["sql_condition"]
        query = f"""
            SELECT 
                year,
                periodo,
                SUM(presupuesto_inicial) as p_ini,
                SUM(presupuesto_vigente) as p_vig,
                SUM(ejecucion_acumulada) as p_eje
            FROM ejecucion_consolidada
            WHERE year BETWEEN ? AND ? AND moneda = ?
              AND ({sql_cond})
            GROUP BY year, periodo
            ORDER BY year ASC
        """

        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=(start_year, end_year, moneda))
            if df.empty:
                return pd.DataFrame()

            # Filtrar hito representativo por año (Diciembre para años cerrados, mes más avanzado para año en curso)
            rows = []
            order_m = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            for y, grp in df.groupby("year"):
                if "Diciembre" in grp["periodo"].values:
                    chosen = grp[grp["periodo"] == "Diciembre"].iloc[0]
                else:
                    # El mes más avanzado disponible
                    grp_sorted = grp.copy()
                    grp_sorted["m_idx"] = grp_sorted["periodo"].apply(lambda m: order_m.index(m) if m in order_m else -1)
                    chosen = grp_sorted.sort_values("m_idx", ascending=False).iloc[0]

                rows.append({
                    "year": int(y),
                    "periodo": chosen["periodo"],
                    "presupuesto_inicial": float(chosen["p_ini"]),
                    "presupuesto_vigente": float(chosen["p_vig"]),
                    "ejecucion_acumulada": float(chosen["p_eje"]),
                    "pct_ejecucion": (float(chosen["p_eje"]) / float(chosen["p_vig"]) * 100.0) if float(chosen["p_vig"]) > 0 else 0.0,
                    "gobierno": "Piñera II (2018-2022)" if y <= 2021 else "Boric (2022-2026)"
                })

            res = pd.DataFrame(rows)
            res["ini_mm"] = res["presupuesto_inicial"] * 1000 / 1e9
            res["vig_mm"] = res["presupuesto_vigente"] * 1000 / 1e9
            res["eje_mm"] = res["ejecucion_acumulada"] * 1000 / 1e9
            return res

    def get_program_detail_records(
        self,
        program_id: str,
        year: int = 2026,
        periodo: str = "Julio",
        moneda: str = "Pesos"
    ) -> pd.DataFrame:
        """
        Retorna las cuentas detalladas (subtítulos, ítems, asignaciones) asociadas al programa.
        """
        spec = PINERA_PROGRAMS_REGISTRY.get(program_id)
        if not spec:
            return pd.DataFrame()

        sql_cond = spec["sql_condition"]
        query = f"""
            SELECT 
                ministerio,
                programa,
                codigo_programa,
                subtitulo_cod,
                subtitulo_nom,
                COALESCE(NULLIF(item_cod, ''), '-') as item_cod,
                COALESCE(NULLIF(item_nom, ''), NULLIF(clasificacion, ''), subtitulo_nom) as item_nom,
                SUM(presupuesto_inicial) as p_ini,
                SUM(presupuesto_vigente) as p_vig,
                SUM(ejecucion_acumulada) as p_eje,
                SUM(saldo) as p_sal,
                AVG(pct_ejecucion) as pct_eje
            FROM ejecucion_consolidada
            WHERE year = ? AND periodo = ? AND moneda = ?
              AND ({sql_cond})
            GROUP BY ministerio, programa, codigo_programa, subtitulo_cod, subtitulo_nom, item_cod, item_nom
            HAVING p_vig > 0 OR p_ini > 0
            ORDER BY p_vig DESC
        """

        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=(year, periodo, moneda))
            if not df.empty:
                df["delta_ley"] = df["p_vig"] - df["p_ini"]
                df["pct_change"] = df.apply(lambda r: (r["delta_ley"] / r["p_ini"] * 100.0) if r["p_ini"] > 0 else 0.0, axis=1)
                df["p_ini_mm"] = df["p_ini"] * 1000 / 1e9
                df["p_vig_mm"] = df["p_vig"] * 1000 / 1e9
                df["p_eje_mm"] = df["p_eje"] * 1000 / 1e9
                df["p_sal_mm"] = df["p_sal"] * 1000 / 1e9
            return df
