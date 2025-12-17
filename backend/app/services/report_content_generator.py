"""
Report Content Generator - Sistema CFO Inteligente

Genera contenido estructurado para reportes usando Claude.
Recibe datos agregados y produce JSON con narrativas profesionales.

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

import json
from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from app.core.logger import get_logger
from app.services.report_data_aggregator import DatosReporte
from app.services.ai.ai_orchestrator import AIOrchestrator

logger = get_logger(__name__)


@dataclass
class SeccionReporte:
    """Una sección del reporte."""
    tipo: str  # "resumen_ejecutivo", "kpis", "grafico", "tabla", "analisis", "conclusiones"
    titulo: str
    contenido: Any  # str para narrativas, dict/list para datos
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tipo": self.tipo,
            "titulo": self.titulo,
            "contenido": self.contenido
        }


@dataclass
class ContenidoReporte:
    """Contenido completo estructurado para el PDF."""
    titulo: str
    subtitulo: str
    fecha_generacion: str
    periodo_label: str
    secciones: List[SeccionReporte] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            "titulo": self.titulo,
            "subtitulo": self.subtitulo,
            "fecha_generacion": self.fecha_generacion,
            "periodo_label": self.periodo_label,
            "secciones": [s.to_dict() for s in self.secciones]
        }


class ReportContentGenerator:
    """
    Genera contenido narrativo para reportes usando Claude.
    
    El contenido generado sigue una estructura JSON que el template
    HTML puede renderizar directamente.
    
    Ejemplo:
        >>> generator = ReportContentGenerator()
        >>> contenido = generator.generate(datos)
        >>> contenido.secciones[0].titulo
        "Resumen Ejecutivo"
    """
    
    PROMPT_TEMPLATE = '''Eres el CFO de Conexión Consultora, una firma legal-contable uruguaya.
Genera contenido profesional para un reporte financiero basándote en estos datos REALES:

══════════════════════════════════════════════════════════════
PERÍODO: {periodo_label}
TIPO DE REPORTE: {tipo_reporte}
══════════════════════════════════════════════════════════════

MÉTRICAS PRINCIPALES:
- Ingresos: ${ingresos:,.0f} UYU
- Gastos: ${gastos:,.0f} UYU
- Resultado Neto: ${resultado:,.0f} UYU
- Rentabilidad: {rentabilidad:.1f}%
- Total Operaciones: {total_operaciones}
- Retiros: ${retiros:,.0f} UYU
- Distribuciones: ${distribuciones:,.0f} UYU

{variaciones_texto}

{areas_texto}

{localidades_texto}

{top_clientes_texto}

{top_proveedores_texto}

══════════════════════════════════════════════════════════════

Genera un JSON con EXACTAMENTE esta estructura:

{{
    "resumen_ejecutivo": "Párrafo de 3-4 oraciones resumiendo el período. Incluir cifras exactas de ingresos, gastos, resultado y rentabilidad. Mencionar tendencia general.",
    
    "puntos_destacados": [
        "Punto positivo o logro importante con cifra específica",
        "Otro punto relevante del período",
        "Área de atención o mejora si corresponde"
    ],
    
    "analisis_ingresos": "Análisis de 2-3 oraciones sobre los ingresos. Mencionar las áreas que más aportaron si hay datos por área.",
    
    "analisis_gastos": "Análisis de 2-3 oraciones sobre los gastos. Mencionar categorías principales si hay datos.",
    
    "analisis_rentabilidad": "Análisis de la rentabilidad: qué la impulsa, si es saludable (>60% es bueno, >70% excelente), y qué factores influyen.",
    
    "comparativa": {comparativa_instruccion},
    
    "conclusiones": [
        "Conclusión o recomendación basada en los datos",
        "Segunda conclusión con enfoque en mejora continua",
        "Tercera conclusión mirando hacia adelante"
    ]
}}

REGLAS ESTRICTAS:
1. Usar ÚNICAMENTE las cifras proporcionadas arriba - NO inventar datos
2. Montos en formato: $X,XXX,XXX UYU
3. Porcentajes con 1 decimal: XX.X%
4. Tono profesional ejecutivo, conciso y orientado a resultados
5. Si rentabilidad >70%, destacarlo como fortaleza
6. Si rentabilidad <50%, mencionar necesidad de optimización
7. Si hay variación negativa respecto al período anterior, ser constructivo
8. Responder SOLO con JSON válido, sin markdown ni explicaciones'''

    def __init__(self):
        self._orchestrator = AIOrchestrator()
        logger.info("ReportContentGenerator inicializado")
    
    def generate(self, datos: DatosReporte) -> ContenidoReporte:
        """
        Genera contenido estructurado para el reporte.
        
        Args:
            datos: Datos agregados del reporte
            
        Returns:
            ContenidoReporte con todas las secciones
        """
        logger.info(f"Generando contenido para reporte: {datos.params.titulo}")
        
        try:
            # 1. Construir prompt con datos reales
            prompt = self._build_prompt(datos)
            
            # 2. Llamar a Claude
            response = self._orchestrator.complete(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.3  # Baja para consistencia
            )
            
            if not response:
                logger.warning("Respuesta vacía de IA, usando fallback")
                contenido_json = self._get_fallback_content(datos)
            else:
                # 3. Parsear respuesta JSON
                contenido_json = self._parse_response(response)
            
        except Exception as e:
            logger.error(f"Error generando contenido con IA: {e}")
            contenido_json = self._get_fallback_content(datos)
        
        # 4. Construir secciones
        secciones = self._build_secciones(contenido_json, datos)
        
        return ContenidoReporte(
            titulo=datos.params.titulo,
            subtitulo="Conexión Consultora - Servicios Profesionales",
            fecha_generacion=datos.metadata.get("generado_en", datetime.now().isoformat()),
            periodo_label=datos.params.periodo_actual.label,
            secciones=secciones
        )
    
    def _build_prompt(self, datos: DatosReporte) -> str:
        """Construye el prompt con los datos reales."""
        pa = datos.periodo_actual  # Período actual
        
        # Texto de variaciones
        variaciones_texto = ""
        if datos.variaciones:
            pc = datos.periodo_comparacion
            variaciones_texto = f"""COMPARACIÓN CON PERÍODO ANTERIOR ({pc.label if pc else 'anterior'}):
- Variación Ingresos: {datos.variaciones['ingresos']:+.1f}%
- Variación Gastos: {datos.variaciones['gastos']:+.1f}%
- Variación Resultado: {datos.variaciones['resultado']:+.1f}%
- Variación Rentabilidad: {datos.variaciones['rentabilidad_pp']:+.1f} puntos porcentuales"""
        
        # Texto de áreas
        areas_texto = ""
        if pa.por_area:
            lineas = ["RESULTADOS POR ÁREA:"]
            for area, m in pa.por_area.items():
                lineas.append(f"- {area}: Ing=${m['ingresos']:,.0f}, Gas=${m['gastos']:,.0f}, Rent={m['rentabilidad']:.1f}%")
            areas_texto = "\n".join(lineas)
        
        # Texto de localidades
        localidades_texto = ""
        if pa.por_localidad:
            lineas = ["RESULTADOS POR LOCALIDAD:"]
            for loc, m in pa.por_localidad.items():
                lineas.append(f"- {loc}: Ing=${m['ingresos']:,.0f}, Gas=${m['gastos']:,.0f}, Rent={m['rentabilidad']:.1f}%")
            localidades_texto = "\n".join(lineas)
        
        # Texto de top clientes
        top_clientes_texto = ""
        if datos.top_clientes:
            lineas = ["TOP CLIENTES:"]
            for i, c in enumerate(datos.top_clientes[:5], 1):
                lineas.append(f"- {i}. {c['cliente']}: ${c['total']:,.0f} ({c['operaciones']} ops)")
            top_clientes_texto = "\n".join(lineas)
        
        # Texto de top proveedores
        top_proveedores_texto = ""
        if datos.top_proveedores:
            lineas = ["TOP PROVEEDORES (GASTOS):"]
            for i, p in enumerate(datos.top_proveedores[:5], 1):
                lineas.append(f"- {i}. {p['proveedor']}: ${p['total']:,.0f} ({p['operaciones']} ops)")
            top_proveedores_texto = "\n".join(lineas)
        
        # Instrucción de comparativa
        if datos.variaciones:
            comparativa_instruccion = '"Análisis detallado de las variaciones respecto al período anterior. Explicar qué mejoró, qué empeoró y posibles causas."'
        else:
            comparativa_instruccion = 'null'
        
        return self.PROMPT_TEMPLATE.format(
            periodo_label=datos.params.periodo_actual.label,
            tipo_reporte=datos.params.tipo.value,
            ingresos=pa.ingresos,
            gastos=pa.gastos,
            resultado=pa.resultado,
            rentabilidad=pa.rentabilidad,
            total_operaciones=pa.total_operaciones,
            retiros=pa.retiros,
            distribuciones=pa.distribuciones,
            variaciones_texto=variaciones_texto,
            areas_texto=areas_texto,
            localidades_texto=localidades_texto,
            top_clientes_texto=top_clientes_texto,
            top_proveedores_texto=top_proveedores_texto,
            comparativa_instruccion=comparativa_instruccion
        )
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parsea el JSON de la respuesta de Claude."""
        # Limpiar respuesta
        cleaned = response.strip()
        
        # Remover markdown si viene envuelto
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON de Claude: {e}")
            logger.debug(f"Respuesta raw: {response[:500]}")
            return {}
    
    def _get_fallback_content(self, datos: DatosReporte) -> Dict[str, Any]:
        """Genera contenido genérico si Claude falla."""
        pa = datos.periodo_actual
        
        # Determinar estado de rentabilidad
        if pa.rentabilidad >= 70:
            estado_rent = "excelente"
        elif pa.rentabilidad >= 60:
            estado_rent = "saludable"
        elif pa.rentabilidad >= 50:
            estado_rent = "aceptable"
        else:
            estado_rent = "que requiere atención"
        
        return {
            "resumen_ejecutivo": f"Durante {datos.params.periodo_actual.label}, Conexión Consultora registró ingresos por ${pa.ingresos:,.0f} UYU y gastos por ${pa.gastos:,.0f} UYU, generando un resultado neto de ${pa.resultado:,.0f} UYU. La rentabilidad del período fue de {pa.rentabilidad:.1f}%, un nivel {estado_rent} para la operación.",
            
            "puntos_destacados": [
                f"Ingresos totales de ${pa.ingresos:,.0f} UYU en el período",
                f"Rentabilidad de {pa.rentabilidad:.1f}% sobre ingresos",
                f"Se procesaron {pa.total_operaciones} operaciones en total"
            ],
            
            "analisis_ingresos": f"Los ingresos del período totalizaron ${pa.ingresos:,.0f} UYU, provenientes de las distintas áreas de la firma. El flujo de facturación se mantuvo activo con múltiples operaciones registradas.",
            
            "analisis_gastos": f"Los gastos operativos sumaron ${pa.gastos:,.0f} UYU, representando el {100-pa.rentabilidad:.1f}% de los ingresos. Se mantiene un control adecuado de los costos operativos.",
            
            "analisis_rentabilidad": f"La rentabilidad de {pa.rentabilidad:.1f}% refleja un margen {estado_rent} entre ingresos y gastos. Este indicador es fundamental para evaluar la salud financiera de la firma.",
            
            "comparativa": None,
            
            "conclusiones": [
                "Mantener el seguimiento mensual de los indicadores financieros clave",
                "Continuar con el control de gastos para preservar la rentabilidad",
                "Evaluar oportunidades de crecimiento en las áreas más rentables"
            ]
        }
    
    def _build_secciones(
        self, 
        contenido: Dict[str, Any], 
        datos: DatosReporte
    ) -> List[SeccionReporte]:
        """
        Construye las secciones del reporte combinando:
        - Narrativas de Claude
        - Datos numéricos del agregador
        - Estructura para gráficos
        """
        secciones = []
        pa = datos.periodo_actual
        
        # 1. Resumen ejecutivo (narrativa)
        secciones.append(SeccionReporte(
            tipo="resumen_ejecutivo",
            titulo="Resumen Ejecutivo",
            contenido=contenido.get("resumen_ejecutivo", "")
        ))
        
        # 2. Puntos destacados
        if contenido.get("puntos_destacados"):
            secciones.append(SeccionReporte(
                tipo="puntos_destacados",
                titulo="Puntos Destacados",
                contenido=contenido.get("puntos_destacados", [])
            ))
        
        # 3. KPIs principales (datos numéricos)
        kpis_data = {
            "metricas": [
                {"nombre": "Ingresos", "valor": pa.ingresos, "formato": "moneda"},
                {"nombre": "Gastos", "valor": pa.gastos, "formato": "moneda"},
                {"nombre": "Resultado Neto", "valor": pa.resultado, "formato": "moneda"},
                {"nombre": "Rentabilidad", "valor": pa.rentabilidad, "formato": "porcentaje"},
                {"nombre": "Retiros", "valor": pa.retiros, "formato": "moneda"},
                {"nombre": "Distribuciones", "valor": pa.distribuciones, "formato": "moneda"},
            ],
            "total_operaciones": pa.total_operaciones
        }
        
        if datos.variaciones:
            kpis_data["variaciones"] = datos.variaciones
        
        secciones.append(SeccionReporte(
            tipo="kpis",
            titulo="Indicadores Clave",
            contenido=kpis_data
        ))
        
        # 4. Tabla por área (si hay datos)
        if pa.por_area:
            filas = []
            for area, m in sorted(pa.por_area.items(), key=lambda x: x[1]["ingresos"], reverse=True):
                filas.append({
                    "area": area,
                    "ingresos": m["ingresos"],
                    "gastos": m["gastos"],
                    "resultado": m["resultado"],
                    "rentabilidad": m["rentabilidad"]
                })
            
            secciones.append(SeccionReporte(
                tipo="tabla",
                titulo="Resultados por Área",
                contenido={
                    "columnas": ["Área", "Ingresos", "Gastos", "Resultado", "Rentabilidad"],
                    "filas": filas
                }
            ))
        
        # 5. Tabla por localidad (si hay datos)
        if pa.por_localidad:
            filas_loc = []
            for loc, m in pa.por_localidad.items():
                filas_loc.append({
                    "localidad": loc.title(),
                    "ingresos": m["ingresos"],
                    "gastos": m["gastos"],
                    "resultado": m["resultado"],
                    "rentabilidad": m["rentabilidad"]
                })
            
            secciones.append(SeccionReporte(
                tipo="tabla",
                titulo="Resultados por Localidad",
                contenido={
                    "columnas": ["Localidad", "Ingresos", "Gastos", "Resultado", "Rentabilidad"],
                    "filas": filas_loc
                }
            ))
        
        # 6. Gráfico evolución mensual (si hay datos)
        if pa.por_mes:
            secciones.append(SeccionReporte(
                tipo="grafico",
                titulo="Evolución Mensual",
                contenido={
                    "tipo_grafico": "barras",
                    "datos": pa.por_mes
                }
            ))
        
        # 7. Top clientes (si hay datos)
        if datos.top_clientes:
            secciones.append(SeccionReporte(
                tipo="ranking",
                titulo="Principales Clientes",
                contenido={
                    "tipo": "clientes",
                    "datos": datos.top_clientes
                }
            ))
        
        # 8. Top proveedores (si hay datos)
        if datos.top_proveedores:
            secciones.append(SeccionReporte(
                tipo="ranking",
                titulo="Principales Proveedores",
                contenido={
                    "tipo": "proveedores",
                    "datos": datos.top_proveedores
                }
            ))
        
        # 9. Análisis detallado (narrativas)
        analisis = {}
        if contenido.get("analisis_ingresos"):
            analisis["ingresos"] = contenido["analisis_ingresos"]
        if contenido.get("analisis_gastos"):
            analisis["gastos"] = contenido["analisis_gastos"]
        if contenido.get("analisis_rentabilidad"):
            analisis["rentabilidad"] = contenido["analisis_rentabilidad"]
        
        if analisis:
            secciones.append(SeccionReporte(
                tipo="analisis",
                titulo="Análisis Detallado",
                contenido=analisis
            ))
        
        # 10. Comparativa (si hay período de comparación)
        if contenido.get("comparativa") and datos.variaciones:
            secciones.append(SeccionReporte(
                tipo="comparativa",
                titulo=f"Comparativa vs {datos.params.periodo_comparacion.label if datos.params.periodo_comparacion else 'Período Anterior'}",
                contenido={
                    "narrativa": contenido["comparativa"],
                    "variaciones": datos.variaciones
                }
            ))
        
        # 11. Conclusiones (narrativa)
        if contenido.get("conclusiones"):
            secciones.append(SeccionReporte(
                tipo="conclusiones",
                titulo="Conclusiones y Recomendaciones",
                contenido=contenido["conclusiones"]
            ))
        
        return secciones


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIÓN HELPER
# ═══════════════════════════════════════════════════════════════════════════

def generate_report_content(datos: DatosReporte) -> Dict[str, Any]:
    """
    Genera contenido de reporte y retorna como diccionario.
    
    Args:
        datos: Datos agregados del reporte
        
    Returns:
        Dict con contenido estructurado para el PDF
    """
    generator = ReportContentGenerator()
    contenido = generator.generate(datos)
    return contenido.to_dict()


# ═══════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════

def _run_tests():
    """Tests del generador de contenido."""
    from datetime import date
    from app.core.database import SessionLocal
    from app.services.report_params_extractor import ReportParams, PeriodoReporte, ReportType
    from app.services.report_data_aggregator import ReportDataAggregator
    
    print("\n" + "="*70)
    print(" TEST DE GENERACIÓN DE CONTENIDO")
    print("="*70)
    
    db = SessionLocal()
    
    try:
        # 1. Crear parámetros de prueba
        params = ReportParams(
            tipo=ReportType.MENSUAL,
            titulo="Reporte Financiero - Noviembre 2024",
            periodo_actual=PeriodoReporte(
                fecha_inicio=date(2024, 11, 1),
                fecha_fin=date(2024, 11, 30),
                label="Noviembre 2024"
            ),
            periodo_comparacion=PeriodoReporte(
                fecha_inicio=date(2024, 10, 1),
                fecha_fin=date(2024, 10, 31),
                label="Octubre 2024"
            ),
            dimensiones=["area", "localidad"],
            moneda_preferida="UYU",
            incluir_graficos=True,
            incluir_narrativas_ia=True,
            filtros_adicionales={}
        )
        
        # 2. Agregar datos
        print("\n📊 Agregando datos...")
        aggregator = ReportDataAggregator(db)
        datos = aggregator.aggregate(params)
        
        print(f"   Ingresos: ${datos.periodo_actual.ingresos:,.0f}")
        print(f"   Rentabilidad: {datos.periodo_actual.rentabilidad:.1f}%")
        
        # 3. Generar contenido
        print("\n📝 Generando contenido con IA...")
        generator = ReportContentGenerator()
        contenido = generator.generate(datos)
        
        # 4. Mostrar resultados
        print(f"\n   Título: {contenido.titulo}")
        print(f"   Período: {contenido.periodo_label}")
        print(f"   Secciones generadas: {len(contenido.secciones)}")
        
        print("\n   Secciones:")
        for i, seccion in enumerate(contenido.secciones, 1):
            print(f"   {i}. [{seccion.tipo}] {seccion.titulo}")
        
        # 5. Mostrar resumen ejecutivo
        resumen = next((s for s in contenido.secciones if s.tipo == "resumen_ejecutivo"), None)
        if resumen:
            print(f"\n   📋 Resumen Ejecutivo:")
            print(f"   {resumen.contenido[:200]}...")
        
        print("\n✅ Test completado")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "="*70)


if __name__ == "__main__":
    _run_tests()

