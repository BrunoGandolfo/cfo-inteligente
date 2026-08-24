"""
Adaptador de consultas financieras de solo lectura para el servidor MCP local.

Este módulo NO reimplementa cálculos: envuelve la lógica ya existente en
app/api/metricas.py, app/api/operaciones.py, app/api/catalogos.py y
app/services/metrics/metrics_aggregator.py.

Los queries de operaciones/dashboard/catálogos viven hoy inline dentro de los
routers FastAPI (no existe una capa de repositorio reutilizable — ver
app/repositories/__init__.py, que está vacío). Por eso cada función de este
módulo es una réplica literal del query correspondiente, citada en su
docstring, en vez de una llamada a una función de servicio inexistente.

Decisión de diseño (metricas_dashboard): el endpoint /api/metricas/dashboard
(app/api/metricas.py:39-64) suma los montos con `float(...)` operación por
operación, en el orden que devuelve la query. MetricsAggregator.aggregate_all()
calcula los mismos totales pero en Decimal, sumando en el mismo orden sobre la
misma lista de operaciones — el resultado numérico coincide, pero para
garantizar equivalencia exacta al centavo con el endpoint (incluyendo
redondeo float) se replica aquí la misma aritmética que usa el endpoint para
el bloque "metricas" (ingresos/gastos/rentabilidad/area_lider), y por separado
se agrega la salida completa de aggregate_all() (29+ métricas) bajo la clave
"metricas_extendidas". No se usa el M27 (area_lider) del aggregator para el
bloque principal porque ese cálculo puede rankear áreas de forma distinta
según la moneda de vista en casos de borde (mezcla de monedas por área); el
área líder del bloque "metricas" replica exactamente el criterio del
endpoint para esa misma moneda_vista.

Reglas duras de este módulo:
- Solo SELECT. Ninguna función hace INSERT/UPDATE/DELETE ni db.commit().
- Prohibido importar app.services.operacion_service (solo-escritura).
- Cada función abre su propia sesión con SessionLocal() y la cierra en finally.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from app.core.database import SessionLocal
from app.models.area import Area
from app.models.operacion import Operacion, TipoOperacion
from app.models.socio import Socio
from app.services.metrics.metrics_aggregator import MetricsAggregator


def obtener_operaciones_periodo(
    fecha_desde: date,
    fecha_hasta: date,
    localidad: Optional[str] = None,
) -> List[Operacion]:
    """
    Réplica exacta del query base del dashboard (app/api/metricas.py:27-36).

    Filtra operaciones no eliminadas (deleted_at IS NULL) en el rango de
    fechas [fecha_desde, fecha_hasta], con área precargada (joinedload) y
    filtro opcional de localidad.
    """
    db = SessionLocal()
    try:
        query = db.query(Operacion).options(joinedload(Operacion.area)).filter(
            Operacion.deleted_at.is_(None),
            Operacion.fecha >= fecha_desde,
            Operacion.fecha <= fecha_hasta,
        )

        if localidad and localidad != "Todas":
            query = query.filter(Operacion.localidad == localidad.upper())

        return query.all()
    finally:
        db.close()


def metricas_dashboard(
    fecha_desde: date,
    fecha_hasta: date,
    localidad: Optional[str] = None,
    moneda_vista: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Métricas del dashboard: bloque equivalente al endpoint /api/metricas/dashboard
    (app/api/metricas.py:16-79) más el detalle extendido de MetricsAggregator
    (app/services/metrics/metrics_aggregator.py:88).

    Ver docstring del módulo para la justificación de por qué el bloque
    "metricas" replica la aritmética del endpoint en vez de leerla del
    aggregator.
    """
    moneda_vista = moneda_vista or "UYU"
    operaciones = obtener_operaciones_periodo(fecha_desde, fecha_hasta, localidad)

    # ── Bloque "metricas": réplica literal de metricas.py:39-64 ──
    campo_monto = "monto_usd" if moneda_vista == "USD" else "monto_uyu"

    ingresos = sum(
        float(getattr(op, campo_monto) or 0)
        for op in operaciones
        if op.tipo_operacion == TipoOperacion.INGRESO
    )

    gastos = sum(
        float(getattr(op, campo_monto) or 0)
        for op in operaciones
        if op.tipo_operacion == TipoOperacion.GASTO
    )

    rentabilidad = ((ingresos - gastos) / ingresos * 100) if ingresos > 0 else 0

    areas_ingresos: Dict[str, float] = {}
    for op in operaciones:
        if op.tipo_operacion == TipoOperacion.INGRESO and op.area:
            area_nombre = op.area.nombre
            areas_ingresos[area_nombre] = areas_ingresos.get(area_nombre, 0) + float(
                getattr(op, campo_monto) or 0
            )

    area_lider = max(areas_ingresos, key=areas_ingresos.get) if areas_ingresos else None

    # ── Bloque extendido: MetricsAggregator (29+ métricas) ──
    aggregador = MetricsAggregator(
        operaciones=operaciones,
        fecha_inicio=fecha_desde,
        fecha_fin=fecha_hasta,
    )
    metricas_extendidas = aggregador.aggregate_all()

    return {
        "metricas": {
            "ingresos": {"valor": round(ingresos, 2), "moneda": moneda_vista},
            "gastos": {"valor": round(gastos, 2), "moneda": moneda_vista},
            "rentabilidad": round(rentabilidad, 2),
            "area_lider": area_lider,
        },
        "filtros_aplicados": {
            "fecha_desde": str(fecha_desde),
            "fecha_hasta": str(fecha_hasta),
            "localidad": localidad,
            "moneda_vista": moneda_vista,
        },
        "metricas_extendidas": metricas_extendidas,
    }


def listar_operaciones(
    limit: int = 20,
    localidad: Optional[str] = None,
    area: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Listado de operaciones no eliminadas, más recientes primero.

    Réplica del query base de app/api/operaciones.py:43-54 (joinedload área,
    deleted_at IS NULL, order_by fecha/created_at desc, limit), extendida con
    filtros opcionales de localidad/área/rango de fechas (no presentes en el
    endpoint original, agregados aquí para uso exploratorio vía MCP). No
    replica el filtro de "usuario solo-contable" del endpoint (es una regla
    de autorización por email de usuario — no aplica a un servidor MCP local
    sin sesión de usuario).
    """
    db = SessionLocal()
    try:
        query = (
            db.query(Operacion)
            .options(joinedload(Operacion.area))
            .filter(Operacion.deleted_at.is_(None))
        )

        if localidad and localidad != "Todas":
            query = query.filter(Operacion.localidad == localidad.upper())

        if area:
            query = query.join(Area).filter(Area.nombre == area)

        if fecha_desde:
            query = query.filter(Operacion.fecha >= fecha_desde)

        if fecha_hasta:
            query = query.filter(Operacion.fecha <= fecha_hasta)

        operaciones = (
            query.order_by(desc(Operacion.fecha), desc(Operacion.created_at))
            .limit(limit)
            .all()
        )

        result = []
        for op in operaciones:
            result.append(
                {
                    "id": str(op.id),
                    "tipo_operacion": op.tipo_operacion.value if op.tipo_operacion else None,
                    "fecha": op.fecha.isoformat() if op.fecha else None,
                    "monto_original": float(op.monto_original) if op.monto_original else 0,
                    "moneda_original": op.moneda_original.value if op.moneda_original else None,
                    "tipo_cambio": float(op.tipo_cambio) if op.tipo_cambio else 0,
                    "monto_uyu": float(op.monto_uyu) if op.monto_uyu else 0,
                    "monto_usd": float(op.monto_usd) if op.monto_usd else 0,
                    "area": {"id": str(op.area.id), "nombre": op.area.nombre} if op.area else None,
                    "localidad": op.localidad.value if op.localidad else None,
                    "cliente": op.cliente,
                    "proveedor": op.proveedor,
                    "descripcion": op.descripcion,
                }
            )

        return result
    finally:
        db.close()


def listar_areas() -> List[Dict[str, Any]]:
    """Réplica exacta de app/api/catalogos.py:20-27 (áreas activas, orden alfabético)."""
    db = SessionLocal()
    try:
        areas = db.query(Area).filter(Area.activo == True).order_by(Area.nombre).all()  # noqa: E712
        return [{"id": str(a.id), "nombre": a.nombre} for a in areas]
    finally:
        db.close()


def listar_socios() -> List[Dict[str, Any]]:
    """Réplica exacta de app/api/catalogos.py:30-37 (socios activos, orden alfabético)."""
    db = SessionLocal()
    try:
        socios = db.query(Socio).filter(Socio.activo == True).order_by(Socio.nombre).all()  # noqa: E712
        return [{"id": str(s.id), "nombre": s.nombre} for s in socios]
    finally:
        db.close()
