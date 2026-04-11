"""
API para consultas contables DGI.

Cada consulta queda registrada para trazabilidad, auditoria y exportacion.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.access_control import USUARIOS_ACCESO_CONTABLE, tiene_acceso
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario

router = APIRouter()


class ConsultaContableRequest(BaseModel):
    servicio: str
    rut: Optional[str] = None
    ci: Optional[str] = None
    datos_extra: Dict[str, Any] = Field(default_factory=dict)
    cliente_nombre: Optional[str] = None
    cliente_rut: Optional[str] = None


def _es_usuario_autorizado(usuario: Usuario) -> bool:
    if getattr(usuario, "es_socio", False):
        return True
    email = (getattr(usuario, "email", "") or "").strip().lower()
    return bool(email) and tiene_acceso(email, USUARIOS_ACCESO_CONTABLE)


def _verificar_acceso_modulo(usuario: Usuario) -> None:
    if _es_usuario_autorizado(usuario):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permiso para acceder a consultas contables",
    )


def _verificar_acceso_registro(consulta: Any, usuario: Usuario) -> None:
    if _es_usuario_autorizado(usuario) and getattr(usuario, "es_socio", False):
        return
    if getattr(consulta, "usuario_id", None) == usuario.id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permiso para acceder a esta consulta",
    )


def _serializar_consulta(consulta: Any) -> Dict[str, Any]:
    return {
        "id": str(getattr(consulta, "id", "")),
        "usuario_id": str(getattr(consulta, "usuario_id", "")),
        "servicio": getattr(consulta, "servicio", None),
        "rut": getattr(consulta, "rut", None),
        "ci": getattr(consulta, "ci", None),
        "datos_entrada": getattr(consulta, "datos_entrada", None),
        "exitosa": getattr(consulta, "exitosa", False),
        "resultado_texto": getattr(consulta, "resultado_texto", None),
        "resultado_datos": getattr(consulta, "resultado_datos", None),
        "error": getattr(consulta, "error", None),
        "cliente_nombre": getattr(consulta, "cliente_nombre", None),
        "cliente_rut": getattr(consulta, "cliente_rut", None),
        "created_at": getattr(consulta, "created_at", None),
        "deleted_at": getattr(consulta, "deleted_at", None),
    }


def _cargar_servicio_contable():
    try:
        from app.services import contable_service
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Servicio contable no disponible",
        ) from exc
    return contable_service


def _servicios_disponibles() -> List[Dict[str, Any]]:
    return [
        {
            "id": "CERTIFICADO_UNICO",
            "nombre": "Certificado Unico DGI",
            "descripcion": "Vigencia tributaria del contribuyente",
            "campos": ["rut", "ci"],
        },
        {
            "id": "DECLARACION_IRPF",
            "nombre": "Declaracion IRPF",
            "descripcion": "Verificar si presento declaracion IRPF",
            "campos": ["ci"],
        },
        {
            "id": "AFILIACION_BANCARIA",
            "nombre": "Afiliacion Bancaria",
            "descripcion": "Consulta de afiliacion bancaria disponible en DGI",
            "campos": ["rut", "ci"],
        },
        {
            "id": "BORRADORES_IASS",
            "nombre": "Borradores IASS",
            "descripcion": "Consulta de borradores IASS",
            "campos": ["rut"],
        },
        {
            "id": "EXONERACION_ARRENDAMIENTOS",
            "nombre": "Exoneracion Arrendamientos",
            "descripcion": "Constancia de exoneracion IRPF por arrendamientos",
            "campos": ["tipo_doc", "numero_doc", "pais"],
        },
        {
            "id": "ESTADO_TRAMITE",
            "nombre": "Estado de Tramite",
            "descripcion": "Seguimiento de tramites DGI",
            "campos": ["nro_tramite"],
        },
        {
            "id": "EXPEDIENTE_ADMINISTRATIVO",
            "nombre": "Expediente Administrativo",
            "descripcion": "Consulta de expedientes administrativos DGI",
            "campos": ["nro_expediente"],
        },
        {
            "id": "DEVOLUCION_IVA_GASOIL",
            "nombre": "Devolucion IVA Gasoil",
            "descripcion": "Consulta de devolucion de IVA gasoil",
            "campos": ["rut", "ci"],
        },
        {
            "id": "CONSTANCIA_PRIMARIA",
            "nombre": "Constancia de Primaria",
            "descripcion": "Consulta de constancia de primaria",
            "campos": ["nro_constancia"],
        },
        {
            "id": "RESIDENCIA_FISCAL",
            "nombre": "Residencia Fiscal",
            "descripcion": "Consulta de residencia fiscal",
            "campos": ["rut", "ci"],
        },
    ]


@router.post("/consultar")
async def consultar_contable(
    payload: ConsultaContableRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    _verificar_acceso_modulo(current_user)
    contable_service = _cargar_servicio_contable()

    consulta = await contable_service.ejecutar_y_registrar(
        db=db,
        usuario_id=current_user.id,
        servicio=payload.servicio,
        rut=payload.rut,
        ci=payload.ci,
        datos_extra=payload.datos_extra,
        cliente_nombre=payload.cliente_nombre,
        cliente_rut=payload.cliente_rut,
    )

    return {"consulta": _serializar_consulta(consulta)}


@router.get("/consultas")
def listar_consultas(
    servicio: Optional[str] = Query(None),
    rut: Optional[str] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    _verificar_acceso_modulo(current_user)
    contable_service = _cargar_servicio_contable()

    usuario_id = None if getattr(current_user, "es_socio", False) else current_user.id

    try:
        resultado = contable_service.listar_consultas(
            db=db,
            usuario_id=usuario_id,
            servicio=servicio,
            rut=rut,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limit=limit,
            offset=offset,
        )
    except TypeError:
        resultado = contable_service.listar_consultas(
            db=db,
            usuario_id=usuario_id,
            servicio=servicio,
            rut=rut,
            limit=limit,
            offset=offset,
        )

    consultas = resultado.get("consultas", []) if isinstance(resultado, dict) else []
    serializadas = [_serializar_consulta(consulta) for consulta in consultas]
    return {
        "total": resultado.get("total", len(serializadas)) if isinstance(resultado, dict) else len(serializadas),
        "consultas": serializadas,
        "limit": resultado.get("limit", limit) if isinstance(resultado, dict) else limit,
        "offset": resultado.get("offset", offset) if isinstance(resultado, dict) else offset,
    }


@router.get("/consultas/{consulta_id}")
def obtener_consulta(
    consulta_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    _verificar_acceso_modulo(current_user)
    contable_service = _cargar_servicio_contable()

    consulta = contable_service.obtener_consulta(db=db, consulta_id=consulta_id)
    if consulta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consulta no encontrada")

    _verificar_acceso_registro(consulta, current_user)
    return {"consulta": _serializar_consulta(consulta)}


@router.delete("/consultas/{consulta_id}")
def eliminar_consulta(
    consulta_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    _verificar_acceso_modulo(current_user)
    contable_service = _cargar_servicio_contable()

    consulta = contable_service.obtener_consulta(db=db, consulta_id=consulta_id)
    if consulta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consulta no encontrada")

    _verificar_acceso_registro(consulta, current_user)
    contable_service.eliminar_consulta(db=db, consulta_id=consulta_id)
    return {"ok": True}


@router.get("/servicios-disponibles")
def servicios_disponibles(
    current_user: Usuario = Depends(get_current_user),
):
    _verificar_acceso_modulo(current_user)
    return _servicios_disponibles()


@router.post("/consultas/exportar-excel")
def exportar_consultas_excel(
    current_user: Usuario = Depends(get_current_user),
):
    _verificar_acceso_modulo(current_user)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Exportacion Excel no implementada",
    )


@router.post("/consultas/{consulta_id}/exportar-pdf")
def exportar_consulta_pdf(
    consulta_id: UUID,
    current_user: Usuario = Depends(get_current_user),
):
    _verificar_acceso_modulo(current_user)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Exportacion PDF no implementada",
    )
