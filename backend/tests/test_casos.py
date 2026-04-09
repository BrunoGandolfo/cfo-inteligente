"""
Tests unitarios para el router de Casos (backend/app/api/casos.py).

Testea control de acceso, CRUD y soft delete.
Mockea BD y dependencias.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import HTTPException

from app.api.casos import (
    _verificar_acceso_casos,
    listar_casos,
    obtener_caso,
    crear_caso,
    actualizar_caso,
    eliminar_caso,
)


# ============================================================================
# HELPERS
# ============================================================================


def _mock_usuario(email="bgandolfo@cgmasociados.com", es_socio=True):
    user = MagicMock()
    user.id = uuid4()
    user.email = email
    user.es_socio = es_socio
    return user


def _mock_caso(responsable_id=None, titulo="Caso Test"):
    caso = MagicMock()
    caso.id = uuid4()
    caso.titulo = titulo
    caso.estado = "pendiente"
    caso.prioridad = "media"
    caso.responsable_id = responsable_id or uuid4()
    caso.deleted_at = None
    caso.created_at = datetime.now(timezone.utc)
    return caso


# ============================================================================
# CONTROL DE ACCESO
# ============================================================================


class TestVerificarAccesoCasos:
    def test_usuario_autorizado(self):
        user = _mock_usuario(email="bgandolfo@cgmasociados.com")
        _verificar_acceso_casos(user)  # No debe lanzar

    def test_colaborador_autorizado(self):
        user = _mock_usuario(email="gferrari@grupoconexion.uy")
        _verificar_acceso_casos(user)  # No debe lanzar

    def test_usuario_no_autorizado(self):
        user = _mock_usuario(email="nadie@grupoconexion.uy")
        with pytest.raises(HTTPException) as exc_info:
            _verificar_acceso_casos(user)
        assert exc_info.value.status_code == 403


# ============================================================================
# LISTAR
# ============================================================================


class TestListarCasos:
    def test_listar_sin_filtros(self):
        user = _mock_usuario()
        db = MagicMock()

        mock_query = db.query.return_value.filter.return_value
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            _mock_caso(), _mock_caso()
        ]

        result = listar_casos(estado=None, prioridad=None, limit=20, offset=0, db=db, current_user=user)
        assert result["total"] == 2
        assert len(result["casos"]) == 2

    def test_usuario_filtrado_ve_solo_sus_casos(self):
        """Los usuarios en USUARIOS_FILTRO_CASOS solo ven sus propios casos."""
        user = _mock_usuario(email="gferrari@grupoconexion.uy")
        db = MagicMock()

        # El query debe agregar un filtro adicional por responsable_id
        mock_query = db.query.return_value.filter.return_value
        mock_filtered = mock_query.filter.return_value
        mock_filtered.count.return_value = 1
        mock_filtered.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [_mock_caso()]

        result = listar_casos(estado=None, prioridad=None, limit=20, offset=0, db=db, current_user=user)
        assert result["total"] == 1


# ============================================================================
# OBTENER
# ============================================================================


class TestObtenerCaso:
    def test_caso_encontrado(self):
        user = _mock_usuario()
        caso = _mock_caso()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = caso

        result = obtener_caso(str(caso.id), db=db, current_user=user)
        assert result.titulo == "Caso Test"

    def test_caso_no_encontrado(self):
        user = _mock_usuario()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            obtener_caso(str(uuid4()), db=db, current_user=user)
        assert exc_info.value.status_code == 404

    def test_id_invalido(self):
        user = _mock_usuario()
        db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            obtener_caso("no-es-uuid", db=db, current_user=user)
        assert exc_info.value.status_code == 400


# ============================================================================
# CREAR
# ============================================================================


class TestCrearCaso:
    @patch("app.api.casos.expediente_service")
    def test_crear_caso_exitoso(self, mock_exp_service):
        user = _mock_usuario()
        db = MagicMock()

        data = MagicMock()
        data.titulo = "Nuevo Caso"
        data.estado = "pendiente"
        data.prioridad = "alta"
        data.fecha_vencimiento = None
        data.expediente_id = None
        data.iue = None

        result = crear_caso(data=data, db=db, current_user=user)
        assert db.add.called
        assert db.commit.called

    @patch("app.api.casos.expediente_service")
    def test_crear_caso_con_iue(self, mock_exp_service):
        """Si se envía IUE, busca o crea el expediente."""
        user = _mock_usuario()
        db = MagicMock()

        mock_expediente = MagicMock()
        mock_expediente.id = uuid4()
        mock_expediente.responsable_id = user.id
        db.query.return_value.filter.return_value.first.return_value = mock_expediente

        data = MagicMock()
        data.titulo = "Caso con expediente"
        data.estado = "pendiente"
        data.prioridad = "media"
        data.fecha_vencimiento = None
        data.expediente_id = None
        data.iue = "2-12345/2023"

        result = crear_caso(data=data, db=db, current_user=user)
        assert db.add.called


# ============================================================================
# ELIMINAR (soft delete)
# ============================================================================


class TestEliminarCaso:
    def test_soft_delete_exitoso(self):
        user = _mock_usuario()
        caso = _mock_caso(responsable_id=user.id)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = caso

        result = eliminar_caso(str(caso.id), db=db, current_user=user)
        assert caso.deleted_at is not None
        assert db.commit.called
        assert "eliminado" in result["mensaje"].lower() or "Caso" in result["mensaje"]

    def test_soft_delete_caso_no_encontrado(self):
        user = _mock_usuario()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            eliminar_caso(str(uuid4()), db=db, current_user=user)
        assert exc_info.value.status_code == 404

    def test_colaborador_filtrado_no_puede_eliminar_caso_ajeno(self):
        """gferrari no puede eliminar un caso de otro responsable."""
        user = _mock_usuario(email="gferrari@grupoconexion.uy")
        caso = _mock_caso(responsable_id=uuid4())  # otro responsable
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = caso

        with pytest.raises(HTTPException) as exc_info:
            eliminar_caso(str(caso.id), db=db, current_user=user)
        assert exc_info.value.status_code == 403
