"""Servicio de persistencia y ejecución para consultas contables DGI."""

from datetime import date, datetime, time, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.models.consulta_contable import ConsultaContable

try:
    from app.services.dgi_service import consultar_certificado_unico
except ImportError:
    consultar_certificado_unico = None  # type: ignore[assignment]

try:
    from app.services.dgi_consultas_service import (
        consultar_certificado_residencia_fiscal,
        consultar_declaracion_irpf,
    )
except ImportError:
    consultar_certificado_residencia_fiscal = None  # type: ignore[assignment]
    consultar_declaracion_irpf = None  # type: ignore[assignment]

try:
    from app.services.dgi_afiliacion_service import consultar_afiliacion_bancaria
except ImportError:
    consultar_afiliacion_bancaria = None  # type: ignore[assignment]

try:
    from app.services.dgi_otras_consultas_service import (
        consultar_borradores_iass,
        consultar_constancia_primaria,
        consultar_devolucion_iva_gasoil,
        consultar_estado_tramite,
        consultar_expediente_administrativo,
        consultar_exoneracion_arrendamientos,
    )
except ImportError:
    consultar_borradores_iass = None  # type: ignore[assignment]
    consultar_constancia_primaria = None  # type: ignore[assignment]
    consultar_devolucion_iva_gasoil = None  # type: ignore[assignment]
    consultar_estado_tramite = None  # type: ignore[assignment]
    consultar_expediente_administrativo = None  # type: ignore[assignment]
    consultar_exoneracion_arrendamientos = None  # type: ignore[assignment]

logger = get_logger(__name__)


def _normalizar_servicio(servicio: str) -> str:
    return (servicio or "").strip().upper()


def _limpiar_texto(texto: Any) -> Optional[str]:
    if texto is None:
        return None
    texto_str = str(texto).strip()
    return texto_str or None


def _resultado_texto(resultado: Optional[Dict[str, Any]]) -> Optional[str]:
    if not resultado:
        return None
    texto = resultado.get("resultado_texto")
    if texto:
        return str(texto)
    error = resultado.get("error")
    if error:
        return str(error)
    return None


def _resultado_exitosa(resultado: Optional[Dict[str, Any]]) -> bool:
    if not resultado:
        return False
    if resultado.get("error"):
        return False
    return bool(resultado.get("consultado"))


def _fecha_inicio(filtro: Optional[datetime | date]) -> Optional[datetime]:
    if filtro is None:
        return None
    if isinstance(filtro, datetime):
        return filtro
    return datetime.combine(filtro, time.min, tzinfo=timezone.utc)


def _fecha_fin(filtro: Optional[datetime | date]) -> Optional[datetime]:
    if filtro is None:
        return None
    if isinstance(filtro, datetime):
        return filtro
    return datetime.combine(filtro, time.max, tzinfo=timezone.utc)


def registrar_consulta(
    db: Session,
    usuario_id: UUID,
    servicio: str,
    rut: Optional[str],
    ci: Optional[str],
    datos_entrada: Optional[Dict[str, Any]],
    resultado: Optional[Dict[str, Any]],
    cliente_nombre: Optional[str] = None,
    cliente_rut: Optional[str] = None,
) -> ConsultaContable:
    """Guarda una consulta contable en la base de datos."""
    servicio_norm = _normalizar_servicio(servicio)
    consulta = ConsultaContable(
        usuario_id=usuario_id,
        servicio=servicio_norm,
        rut=_limpiar_texto(rut),
        ci=_limpiar_texto(ci),
        datos_entrada=datos_entrada,
        exitosa=_resultado_exitosa(resultado),
        resultado_texto=_resultado_texto(resultado),
        resultado_datos=resultado,
        error=_limpiar_texto(resultado.get("error") if resultado else None),
        cliente_nombre=_limpiar_texto(cliente_nombre),
        cliente_rut=_limpiar_texto(cliente_rut),
    )
    db.add(consulta)
    db.commit()
    db.refresh(consulta)
    return consulta


def listar_consultas(
    db: Session,
    usuario_id: Optional[UUID] = None,
    servicio: Optional[str] = None,
    rut: Optional[str] = None,
    fecha_desde: Optional[datetime | date] = None,
    fecha_hasta: Optional[datetime | date] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Lista consultas con filtros opcionales y paginación."""
    query = db.query(ConsultaContable).filter(ConsultaContable.deleted_at.is_(None))

    if usuario_id is not None:
        query = query.filter(ConsultaContable.usuario_id == usuario_id)

    if servicio:
        query = query.filter(ConsultaContable.servicio == _normalizar_servicio(servicio))

    if rut:
        query = query.filter(ConsultaContable.rut == _limpiar_texto(rut))

    if fecha_desde is not None:
        query = query.filter(ConsultaContable.created_at >= _fecha_inicio(fecha_desde))

    if fecha_hasta is not None:
        query = query.filter(ConsultaContable.created_at <= _fecha_fin(fecha_hasta))

    total = query.count()
    consultas = (
        query.order_by(ConsultaContable.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {"total": total, "consultas": consultas}


def obtener_consulta(db: Session, consulta_id: UUID) -> Optional[ConsultaContable]:
    """Obtiene una consulta por ID excluyendo eliminadas."""
    return (
        db.query(ConsultaContable)
        .filter(
            ConsultaContable.id == consulta_id,
            ConsultaContable.deleted_at.is_(None),
        )
        .first()
    )


def eliminar_consulta(db: Session, consulta_id: UUID) -> None:
    """Soft delete de una consulta contable."""
    consulta = obtener_consulta(db, consulta_id)
    if consulta is None:
        return
    consulta.deleted_at = datetime.now(timezone.utc)
    db.commit()


def _resultado_servicio_no_implementado(servicio: str) -> Dict[str, Any]:
    return {
        "consultado": False,
        "error": f"Servicio no implementado: {servicio}",
        "resultado_texto": "",
    }


def _merge_datos_entrada(
    rut: Optional[str],
    ci: Optional[str],
    datos_extra: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    datos: Dict[str, Any] = dict(datos_extra or {})
    if rut is not None:
        datos.setdefault("rut", rut)
    if ci is not None:
        datos.setdefault("ci", ci)
    return datos


async def _ejecutar_servicio_dgi(
    servicio: str,
    rut: Optional[str],
    ci: Optional[str],
    datos_extra: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    servicio_norm = _normalizar_servicio(servicio)
    datos = dict(datos_extra or {})

    if servicio_norm == "CERTIFICADO_UNICO":
        if consultar_certificado_unico is None:
            return _resultado_servicio_no_implementado(servicio_norm)
        return await consultar_certificado_unico(rut or "", ci or "")

    if servicio_norm == "DECLARACION_IRPF":
        if consultar_declaracion_irpf is None:
            return _resultado_servicio_no_implementado(servicio_norm)
        return await consultar_declaracion_irpf(ci or "")

    if servicio_norm == "AFILIACION_BANCARIA":
        if consultar_afiliacion_bancaria is None:
            return _resultado_servicio_no_implementado(servicio_norm)
        return await consultar_afiliacion_bancaria(rut or "")

    if servicio_norm == "BORRADORES_IASS":
        if consultar_borradores_iass is None:
            return _resultado_servicio_no_implementado(servicio_norm)
        return await consultar_borradores_iass(rut or "")

    if servicio_norm == "EXONERACION_ARRENDAMIENTOS":
        if consultar_exoneracion_arrendamientos is None:
            return _resultado_servicio_no_implementado(servicio_norm)
        tipo_doc = datos.get("tipo_doc", "")
        numero_doc = datos.get("numero_doc", "")
        pais = datos.get("pais", "URUGUAY")
        return await consultar_exoneracion_arrendamientos(tipo_doc, numero_doc, pais)

    if servicio_norm == "ESTADO_TRAMITE":
        if consultar_estado_tramite is None:
            return _resultado_servicio_no_implementado(servicio_norm)
        nro_tramite = datos.get("nro_tramite", "")
        return await consultar_estado_tramite(nro_tramite)

    if servicio_norm == "EXPEDIENTE_ADMINISTRATIVO":
        if consultar_expediente_administrativo is None:
            return _resultado_servicio_no_implementado(servicio_norm)
        nro_expediente = datos.get("nro_expediente", "")
        return await consultar_expediente_administrativo(nro_expediente)

    if servicio_norm == "DEVOLUCION_IVA_GASOIL":
        if consultar_devolucion_iva_gasoil is None:
            return _resultado_servicio_no_implementado(servicio_norm)
        return await consultar_devolucion_iva_gasoil(rut or datos.get("ruc", "") or "")

    if servicio_norm == "CONSTANCIA_PRIMARIA":
        if consultar_constancia_primaria is None:
            return _resultado_servicio_no_implementado(servicio_norm)
        nro_constancia = datos.get("nro_constancia", "")
        return await consultar_constancia_primaria(nro_constancia)

    if servicio_norm == "RESIDENCIA_FISCAL":
        if consultar_certificado_residencia_fiscal is None:
            return _resultado_servicio_no_implementado(servicio_norm)
        nro_solicitud = datos.get("nro_solicitud", "")
        linea = datos.get("linea", "")
        tipo = datos.get("tipo", "")
        principio_crc = datos.get("principio_crc", "")
        return await consultar_certificado_residencia_fiscal(
            nro_solicitud, linea, tipo, principio_crc
        )

    return _resultado_servicio_no_implementado(servicio_norm)


async def ejecutar_y_registrar(
    db: Session,
    usuario_id: UUID,
    servicio: str,
    rut: Optional[str] = None,
    ci: Optional[str] = None,
    datos_extra: Optional[Dict[str, Any]] = None,
    cliente_nombre: Optional[str] = None,
    cliente_rut: Optional[str] = None,
) -> ConsultaContable:
    """Ejecuta la consulta DGI y registra el resultado en BD."""
    servicio_norm = _normalizar_servicio(servicio)
    datos_entrada = _merge_datos_entrada(rut, ci, datos_extra)

    try:
        resultado = await _ejecutar_servicio_dgi(servicio_norm, rut, ci, datos_extra)
    except Exception as exc:
        logger.exception("Error ejecutando servicio DGI %s", servicio_norm)
        resultado = {
            "consultado": False,
            "error": str(exc),
            "resultado_texto": "",
        }

    return registrar_consulta(
        db=db,
        usuario_id=usuario_id,
        servicio=servicio_norm,
        rut=rut,
        ci=ci,
        datos_entrada=datos_entrada,
        resultado=resultado,
        cliente_nombre=cliente_nombre,
        cliente_rut=cliente_rut,
    )
