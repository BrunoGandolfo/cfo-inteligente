"""
Servidor MCP local, solo lectura, para el módulo financiero de CFO Inteligente.

Transporte: stdio (pensado para Claude Desktop, que lanza este script como
subproceso y le habla por stdin/stdout).

Este servidor NO reimplementa lógica financiera: cada tool llama directo a
app/services/consultas_financieras_service.py (adaptador de solo lectura),
app/services/indicadores_service.py o app/services/tipo_cambio_service.py.
Ninguna tool escribe en la base de datos.

Uso (desde backend/, con el venv activado):
    python -m mcp_server.cfo_financiero_mcp

Configuración típica en Claude Desktop (claude_desktop_config.json):
    {
      "mcpServers": {
        "cfo-financiero": {
          "command": "/ruta/absoluta/a/backend/.venv/bin/python",
          "args": ["-m", "mcp_server.cfo_financiero_mcp"],
          "cwd": "/ruta/absoluta/a/backend"
        }
      }
    }
"""

import sys
from datetime import date
from pathlib import Path
from typing import Optional

# Permite ejecutar este archivo directamente (python cfo_financiero_mcp.py)
# aunque el cwd del proceso que lo lanza no sea backend/.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from mcp.server.mcpserver import MCPServer  # noqa: E402

from app.services import consultas_financieras_service as consultas  # noqa: E402
from app.services import indicadores_service  # noqa: E402
from app.services import tipo_cambio_service  # noqa: E402

server = MCPServer(
    name="cfo-financiero",
    title="CFO Inteligente — Consultas Financieras",
    instructions=(
        "Servidor de solo lectura sobre el módulo financiero de Conexión "
        "Consultora. Todas las tools consultan datos existentes; ninguna "
        "modifica la base. Los montos financieros vienen ya calculados por "
        "el sistema (nunca los recalcules ni los redondees vos mismo al "
        "narrarlos)."
    ),
)


def _error_legible(operacion: str, exc: Exception) -> dict:
    """Traduce cualquier excepción a un mensaje legible, sin traceback crudo."""
    return {
        "error": True,
        "mensaje": f"No se pudo completar '{operacion}': {exc.__class__.__name__}: {exc}",
    }


# ══════════════════════════════════════════════════════════════
# MÉTRICAS Y OPERACIONES
# ══════════════════════════════════════════════════════════════


@server.tool(
    description=(
        "Métricas financieras del dashboard (ingresos, gastos, rentabilidad, "
        "área líder y 29+ métricas extendidas: tendencias, distribución por "
        "área/localidad, análisis de clientes) para un rango de fechas, con "
        "filtro opcional de localidad y moneda de vista."
    )
)
def get_dashboard_metrics(
    fecha_desde: str,
    fecha_hasta: str,
    localidad: Optional[str] = None,
    moneda_vista: Optional[str] = None,
) -> dict:
    """
    Args:
        fecha_desde: Fecha de inicio del período, formato YYYY-MM-DD.
        fecha_hasta: Fecha de fin del período, formato YYYY-MM-DD.
        localidad: Filtro opcional (ej. "MONTEVIDEO", "MERCEDES"). Omitir para todas.
        moneda_vista: "UYU" (default) o "USD".
    """
    try:
        return consultas.metricas_dashboard(
            fecha_desde=date.fromisoformat(fecha_desde),
            fecha_hasta=date.fromisoformat(fecha_hasta),
            localidad=localidad,
            moneda_vista=moneda_vista,
        )
    except Exception as exc:
        return _error_legible("get_dashboard_metrics", exc)


@server.tool(
    description=(
        "Lista operaciones financieras (ingresos, gastos, retiros, "
        "distribuciones) no anuladas, más recientes primero, con filtros "
        "opcionales de localidad, área y rango de fechas."
    )
)
def list_operaciones(
    limit: int = 20,
    localidad: Optional[str] = None,
    area: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
) -> dict:
    """
    Args:
        limit: Cantidad máxima de operaciones a devolver (default 20).
        localidad: Filtro opcional por localidad.
        area: Filtro opcional por nombre de área (ej. "Notarial").
        fecha_desde: Fecha de inicio opcional, formato YYYY-MM-DD.
        fecha_hasta: Fecha de fin opcional, formato YYYY-MM-DD.
    """
    try:
        operaciones = consultas.listar_operaciones(
            limit=limit,
            localidad=localidad,
            area=area,
            fecha_desde=date.fromisoformat(fecha_desde) if fecha_desde else None,
            fecha_hasta=date.fromisoformat(fecha_hasta) if fecha_hasta else None,
        )
        return {"operaciones": operaciones, "cantidad": len(operaciones)}
    except Exception as exc:
        return _error_legible("list_operaciones", exc)


@server.tool(
    description="Catálogos del sistema: áreas de negocio y socios activos."
)
def get_areas_y_socios() -> dict:
    try:
        return {
            "areas": consultas.listar_areas(),
            "socios": consultas.listar_socios(),
        }
    except Exception as exc:
        return _error_legible("get_areas_y_socios", exc)


# ══════════════════════════════════════════════════════════════
# INDICADORES ECONÓMICOS
# ══════════════════════════════════════════════════════════════


@server.tool(
    description=(
        "Todos los indicadores económicos de Uruguay en una sola llamada: "
        "UI, UR, BPC, inflación anual y cotización de USD."
    )
)
def get_indicadores_todos() -> dict:
    try:
        return indicadores_service.obtener_todos_indicadores()
    except Exception as exc:
        return _error_legible("get_indicadores_todos", exc)


@server.tool(description="Valor actual de la Unidad Indexada (UI) de Uruguay.")
def get_ui() -> dict:
    try:
        return indicadores_service.obtener_ui()
    except Exception as exc:
        return _error_legible("get_ui", exc)


@server.tool(description="Valor actual de la Unidad Reajustable (UR) de Uruguay.")
def get_ur() -> dict:
    try:
        return indicadores_service.obtener_ur()
    except Exception as exc:
        return _error_legible("get_ur", exc)


@server.tool(description="Valor actual de la Base de Prestaciones y Contribuciones (BPC) de Uruguay.")
def get_bpc() -> dict:
    try:
        return indicadores_service.obtener_bpc()
    except Exception as exc:
        return _error_legible("get_bpc", exc)


@server.tool(description="Inflación anual acumulada de Uruguay (últimos 12 meses).")
def get_inflacion() -> dict:
    try:
        return indicadores_service.obtener_inflacion()
    except Exception as exc:
        return _error_legible("get_inflacion", exc)


@server.tool(
    description=(
        "Cotización actual del dólar (USD/UYU): compra, venta y fuente "
        "(DolarApi en tiempo real, o valores de emergencia si la API externa falla)."
    )
)
def get_cotizacion_usd() -> dict:
    try:
        return tipo_cambio_service.obtener_tipo_cambio_actual()
    except Exception as exc:
        return _error_legible("get_cotizacion_usd", exc)


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
