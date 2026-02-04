"""
Servicio para generación de certificados PDF de debida diligencia ALA.

Decreto 379/018 - Arts. 17-18, 44.
Genera certificado profesional en formato A4 usando WeasyPrint.
"""

from datetime import datetime
from typing import TYPE_CHECKING
import logging

from weasyprint import HTML

if TYPE_CHECKING:
    from app.models.verificacion_ala import VerificacionALA

logger = logging.getLogger(__name__)

# Colores por nivel de riesgo
COLORES_RIESGO = {
    "CRITICO": "#DC2626",
    "ALTO": "#EA580C",
    "MEDIO": "#CA8A04",
    "BAJO": "#16A34A",
}


def _formato_fecha(dt: datetime | None) -> str:
    """Formatea datetime a dd/mm/yyyy HH:MM."""
    if dt is None:
        return "-"
    return dt.strftime("%d/%m/%Y %H:%M")


def _formato_fecha_corta(d) -> str:
    """Formatea date a dd/mm/yyyy."""
    if d is None:
        return "-"
    if hasattr(d, "strftime"):
        return d.strftime("%d/%m/%Y")
    return str(d)


def _resultado_lista_html(nombre: str, resultado: dict | None, total_registros: int | None = None) -> str:
    """Genera HTML para una fila de resultado de lista."""
    if resultado is None:
        return f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #E5E7EB;">{nombre}</td>
            <td style="padding: 8px; border: 1px solid #E5E7EB; color: #9CA3AF;">No disponible</td>
            <td style="padding: 8px; border: 1px solid #E5E7EB;">-</td>
            <td style="padding: 8px; border: 1px solid #E5E7EB;">-</td>
            <td style="padding: 8px; border: 1px solid #E5E7EB;">-</td>
        </tr>
        """
    
    checked = resultado.get("checked", False)
    hits = resultado.get("hits", 0)
    mejor_match = resultado.get("mejor_match", "-")
    similitud = resultado.get("similitud")
    similitud_str = f"{similitud:.0%}" if similitud else "-"
    
    if not checked:
        estado = '<span style="color: #9CA3AF;">No verificado</span>'
        resultado_txt = "-"
    elif hits > 0:
        estado = '<span style="color: #16A34A;">✓ Verificada</span>'
        resultado_txt = f'<span style="color: #DC2626; font-weight: bold;">Match encontrado ({hits})</span>'
    else:
        estado = '<span style="color: #16A34A;">✓ Verificada</span>'
        resultado_txt = '<span style="color: #16A34A;">No encontrado</span>'
    
    registros = f"{total_registros:,}" if total_registros else "-"
    
    return f"""
    <tr>
        <td style="padding: 8px; border: 1px solid #E5E7EB; font-weight: 500;">{nombre}</td>
        <td style="padding: 8px; border: 1px solid #E5E7EB;">{estado}</td>
        <td style="padding: 8px; border: 1px solid #E5E7EB;">{resultado_txt}</td>
        <td style="padding: 8px; border: 1px solid #E5E7EB;">{similitud_str}</td>
        <td style="padding: 8px; border: 1px solid #E5E7EB;">{registros}</td>
    </tr>
    """


def _busqueda_html(nombre: str, icono: str, realizada: bool, observaciones: str | None) -> str:
    """Genera HTML para una sección de búsqueda Art. 44."""
    estado = "Sí" if realizada else "No"
    estado_color = "#16A34A" if realizada else "#9CA3AF"
    obs = observaciones or "Sin observaciones"
    # Escapar HTML básico
    obs = obs.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Preservar saltos de línea
    obs = obs.replace("\n", "<br>")
    
    return f"""
    <div style="margin-bottom: 16px; padding: 12px; background: #F9FAFB; border-radius: 6px;">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 16px; margin-right: 8px;">{icono}</span>
            <span style="font-weight: 600;">{nombre}</span>
            <span style="margin-left: auto; color: {estado_color}; font-weight: 500;">
                Realizada: {estado}
            </span>
        </div>
        <div style="font-size: 11px; color: #4B5563; line-height: 1.5;">
            {obs}
        </div>
    </div>
    """


def generar_certificado_ala(verificacion: "VerificacionALA") -> bytes:
    """
    Genera certificado PDF de debida diligencia ALA.
    
    Args:
        verificacion: Instancia de VerificacionALA con todos los datos
        
    Returns:
        bytes: Contenido del PDF generado
    """
    logger.info(f"Generando certificado PDF para verificación {verificacion.id}")
    
    # Datos básicos
    fecha_verificacion = _formato_fecha(verificacion.created_at)
    hash_corto = verificacion.hash_verificacion[:12] if verificacion.hash_verificacion else "N/A"
    hash_completo = verificacion.hash_verificacion or "N/A"
    
    # Color del nivel de riesgo
    color_riesgo = COLORES_RIESGO.get(verificacion.nivel_riesgo, "#6B7280")
    
    # Puede operar
    puede_operar = "NO" if verificacion.nivel_riesgo == "CRITICO" else "SÍ"
    puede_operar_color = "#DC2626" if verificacion.nivel_riesgo == "CRITICO" else "#16A34A"
    
    # Es PEP
    es_pep = "Sí" if verificacion.es_pep else "No"
    es_pep_color = "#EA580C" if verificacion.es_pep else "#16A34A"
    
    # Persona jurídica
    es_pj = "Sí" if verificacion.es_persona_juridica else "No"
    razon_social = verificacion.razon_social or "-"
    
    # Resultados de listas
    listas_html = ""
    listas_html += _resultado_lista_html("PEP Uruguay", verificacion.resultado_pep, 5737)
    listas_html += _resultado_lista_html("ONU (Sanciones)", verificacion.resultado_onu, 726)
    listas_html += _resultado_lista_html("OFAC (SDN)", verificacion.resultado_ofac, 18598)
    listas_html += _resultado_lista_html("Unión Europea", verificacion.resultado_ue, 23471)
    listas_html += _resultado_lista_html("GAFI (País)", verificacion.resultado_gafi, None)
    
    # Búsquedas Art. 44
    busquedas_html = ""
    busquedas_html += _busqueda_html(
        "Google / Análisis IA",
        "🌐",
        verificacion.busqueda_google_realizada,
        verificacion.busqueda_google_observaciones
    )
    busquedas_html += _busqueda_html(
        "Noticias / Análisis IA",
        "📰",
        verificacion.busqueda_news_realizada,
        verificacion.busqueda_news_observaciones
    )
    busquedas_html += _busqueda_html(
        "Wikipedia",
        "📚",
        verificacion.busqueda_wikipedia_realizada,
        verificacion.busqueda_wikipedia_observaciones
    )
    
    # HTML del certificado
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 1.5cm;
            }}
            body {{
                font-family: Arial, Helvetica, sans-serif;
                font-size: 11px;
                color: #1F2937;
                line-height: 1.4;
                margin: 0;
                padding: 0;
            }}
            .header {{
                text-align: center;
                padding: 20px;
                background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
                color: white;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .header h1 {{
                margin: 0 0 8px 0;
                font-size: 22px;
                letter-spacing: 1px;
            }}
            .header h2 {{
                margin: 0 0 12px 0;
                font-size: 14px;
                font-weight: normal;
                opacity: 0.9;
            }}
            .header-meta {{
                font-size: 11px;
                opacity: 0.85;
            }}
            .section {{
                margin-bottom: 20px;
                page-break-inside: avoid;
            }}
            .section-title {{
                font-size: 13px;
                font-weight: bold;
                color: #1E3A8A;
                border-bottom: 2px solid #3B82F6;
                padding-bottom: 6px;
                margin-bottom: 12px;
            }}
            .data-grid {{
                display: table;
                width: 100%;
            }}
            .data-row {{
                display: table-row;
            }}
            .data-label {{
                display: table-cell;
                padding: 6px 12px 6px 0;
                font-weight: 500;
                color: #6B7280;
                width: 40%;
            }}
            .data-value {{
                display: table-cell;
                padding: 6px 0;
                color: #1F2937;
            }}
            .result-cards {{
                display: flex;
                gap: 12px;
                margin-bottom: 16px;
            }}
            .result-card {{
                flex: 1;
                padding: 12px;
                border-radius: 8px;
                text-align: center;
            }}
            .result-card-label {{
                font-size: 10px;
                color: #6B7280;
                text-transform: uppercase;
                margin-bottom: 4px;
            }}
            .result-card-value {{
                font-size: 16px;
                font-weight: bold;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 10px;
            }}
            th {{
                background: #F3F4F6;
                padding: 10px 8px;
                text-align: left;
                font-weight: 600;
                border: 1px solid #E5E7EB;
            }}
            .footer {{
                margin-top: 30px;
                padding: 16px;
                background: #F9FAFB;
                border-radius: 8px;
                font-size: 10px;
                color: #6B7280;
            }}
            .footer-hash {{
                font-family: monospace;
                font-size: 9px;
                word-break: break-all;
                background: #E5E7EB;
                padding: 8px;
                border-radius: 4px;
                margin: 8px 0;
            }}
        </style>
    </head>
    <body>
        <!-- ENCABEZADO -->
        <div class="header">
            <h1>CERTIFICADO DE DEBIDA DILIGENCIA</h1>
            <h2>Anti-Lavado de Activos (Decreto 379/018)</h2>
            <div class="header-meta">
                Fecha: {fecha_verificacion} &nbsp;|&nbsp; Certificado N°: {hash_corto}
            </div>
        </div>
        
        <!-- SECCIÓN 1: DATOS DE LA PERSONA -->
        <div class="section">
            <div class="section-title">1. DATOS DE LA PERSONA / ENTIDAD</div>
            <div class="data-grid">
                <div class="data-row">
                    <div class="data-label">Nombre completo:</div>
                    <div class="data-value"><strong>{verificacion.nombre_completo}</strong></div>
                </div>
                <div class="data-row">
                    <div class="data-label">Tipo de documento:</div>
                    <div class="data-value">{verificacion.tipo_documento or "-"}</div>
                </div>
                <div class="data-row">
                    <div class="data-label">Número de documento:</div>
                    <div class="data-value">{verificacion.numero_documento or "-"}</div>
                </div>
                <div class="data-row">
                    <div class="data-label">Nacionalidad:</div>
                    <div class="data-value">{verificacion.nacionalidad or "-"}</div>
                </div>
                <div class="data-row">
                    <div class="data-label">Fecha de nacimiento:</div>
                    <div class="data-value">{_formato_fecha_corta(verificacion.fecha_nacimiento)}</div>
                </div>
                <div class="data-row">
                    <div class="data-label">Persona jurídica:</div>
                    <div class="data-value">{es_pj}</div>
                </div>
                <div class="data-row">
                    <div class="data-label">Razón social:</div>
                    <div class="data-value">{razon_social}</div>
                </div>
            </div>
        </div>
        
        <!-- SECCIÓN 2: RESULTADO DE LA VERIFICACIÓN -->
        <div class="section">
            <div class="section-title">2. RESULTADO DE LA VERIFICACIÓN</div>
            <div style="display: flex; gap: 12px; margin-bottom: 12px;">
                <div style="flex: 1; padding: 12px; background: #F9FAFB; border-radius: 8px; border-left: 4px solid {color_riesgo};">
                    <div style="font-size: 10px; color: #6B7280; text-transform: uppercase;">Nivel de Riesgo</div>
                    <div style="font-size: 18px; font-weight: bold; color: {color_riesgo};">{verificacion.nivel_riesgo}</div>
                </div>
                <div style="flex: 1; padding: 12px; background: #F9FAFB; border-radius: 8px; border-left: 4px solid #3B82F6;">
                    <div style="font-size: 10px; color: #6B7280; text-transform: uppercase;">Nivel de Diligencia</div>
                    <div style="font-size: 18px; font-weight: bold; color: #1E3A8A;">{verificacion.nivel_diligencia}</div>
                </div>
                <div style="flex: 1; padding: 12px; background: #F9FAFB; border-radius: 8px; border-left: 4px solid {puede_operar_color};">
                    <div style="font-size: 10px; color: #6B7280; text-transform: uppercase;">Puede Operar</div>
                    <div style="font-size: 18px; font-weight: bold; color: {puede_operar_color};">{puede_operar}</div>
                </div>
                <div style="flex: 1; padding: 12px; background: #F9FAFB; border-radius: 8px; border-left: 4px solid {es_pep_color};">
                    <div style="font-size: 10px; color: #6B7280; text-transform: uppercase;">Es PEP</div>
                    <div style="font-size: 18px; font-weight: bold; color: {es_pep_color};">{es_pep}</div>
                </div>
            </div>
        </div>
        
        <!-- SECCIÓN 3: DETALLE POR LISTA -->
        <div class="section">
            <div class="section-title">3. DETALLE POR LISTA</div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 25%;">Lista</th>
                        <th style="width: 20%;">Estado</th>
                        <th style="width: 25%;">Resultado</th>
                        <th style="width: 15%;">Similitud</th>
                        <th style="width: 15%;">Registros</th>
                    </tr>
                </thead>
                <tbody>
                    {listas_html}
                </tbody>
            </table>
        </div>
        
        <!-- SECCIÓN 4: BÚSQUEDAS ART. 44 C.4 -->
        <div class="section">
            <div class="section-title">4. BÚSQUEDAS COMPLEMENTARIAS (Art. 44 C.4)</div>
            {busquedas_html}
        </div>
        
        <!-- PIE -->
        <div class="footer">
            <strong>Hash de integridad (SHA-256):</strong>
            <div class="footer-hash">{hash_completo}</div>
            <div style="margin-top: 12px; text-align: center;">
                Este certificado fue generado automáticamente por <strong>CFO Inteligente</strong>.<br>
                Verificación realizada el {fecha_verificacion}.
            </div>
        </div>
    </body>
    </html>
    """
    
    # Generar PDF con WeasyPrint
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    logger.info(f"Certificado PDF generado: {len(pdf_bytes)} bytes")
    
    return pdf_bytes
