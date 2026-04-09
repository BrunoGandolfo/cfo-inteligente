"""
Tests unitarios para el router de Contratos (backend/app/api/contratos.py).

Testea control de acceso, listado, búsqueda, CRUD y soft delete.
Mockea BD y dependencias (Claude, DOCX).
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import HTTPException

from app.api.contratos import (
    _tiene_acceso_contratos,
    listar_categorias,
    listar_contratos,
    obtener_contrato,
    crear_contrato,
    eliminar_contrato,
    generar_contrato,
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


def _mock_contrato(titulo="Compraventa Inmueble", activo=True):
    contrato = MagicMock()
    contrato.id = uuid4()
    contrato.titulo = titulo
    contrato.categoria = "compraventa"
    contrato.subcategoria = None
    contrato.descripcion = None
    contrato.activo = activo
    contrato.deleted_at = None
    contrato.contenido_docx = b"fake-docx-content"
    contrato.contenido_texto = "Este es un contrato de compraventa..."
    contrato.campos_editables = {"total_campos": 2, "campos": []}
    contrato.nombre_archivo = "compraventa.docx"
    contrato.fuente_original = "machado"
    contrato.archivo_original = "compraventa.docx"
    contrato.created_at = datetime.now(timezone.utc)
    contrato.updated_at = datetime.now(timezone.utc)
    return contrato


# ============================================================================
# CONTROL DE ACCESO
# ============================================================================


class TestTieneAccesoContratos:
    def test_socio_tiene_acceso(self):
        user = _mock_usuario(es_socio=True)
        assert _tiene_acceso_contratos(user) is True

    def test_colaborador_autorizado(self):
        user = _mock_usuario(email="gferrari@grupoconexion.uy", es_socio=False)
        assert _tiene_acceso_contratos(user) is True

    def test_colaborador_no_autorizado(self):
        user = _mock_usuario(email="nadie@grupoconexion.uy", es_socio=False)
        assert _tiene_acceso_contratos(user) is False


# ============================================================================
# LISTAR CATEGORÍAS
# ============================================================================


class TestListarCategorias:
    def test_retorna_categorias_ordenadas(self):
        user = _mock_usuario()
        db = MagicMock()
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [
            ("hipoteca",), ("compraventa",), ("poder",)
        ]

        result = listar_categorias(db=db, current_user=user)
        assert result == ["compraventa", "hipoteca", "poder"]


# ============================================================================
# LISTAR CONTRATOS
# ============================================================================


class TestListarContratos:
    @patch("app.api.contratos.ContratoListResponse")
    @patch("app.api.contratos.ContratoResponse")
    def test_listar_sin_filtros(self, mock_response_cls, mock_list_cls):
        """Verifica que listar_contratos llama la BD y retorna resultados."""
        user = _mock_usuario()
        db = MagicMock()

        mock_contrato = _mock_contrato()
        mock_response_cls.model_validate.return_value = MagicMock()
        mock_list_response = MagicMock()
        mock_list_response.total = 1
        mock_list_cls.return_value = mock_list_response

        query = db.query.return_value.filter.return_value
        query.filter.return_value = query
        query.count.return_value = 1
        query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_contrato]
        query.distinct.return_value.all.return_value = [("compraventa",)]

        result = listar_contratos(q=None, categoria=None, activo=True, skip=0, limit=50, db=db, current_user=user)
        assert result.total == 1


# ============================================================================
# OBTENER CONTRATO
# ============================================================================


class TestObtenerContrato:
    @patch("app.api.contratos.ContratoResponse")
    def test_contrato_encontrado(self, mock_response_cls):
        user = _mock_usuario()
        contrato = _mock_contrato()
        mock_response_cls.model_validate.return_value = MagicMock(id=contrato.id)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = contrato

        result = obtener_contrato(contrato.id, db=db, current_user=user)
        assert result is not None

    def test_contrato_no_encontrado(self):
        user = _mock_usuario()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            obtener_contrato(uuid4(), db=db, current_user=user)
        assert exc_info.value.status_code == 404


# ============================================================================
# CREAR CONTRATO
# ============================================================================


class TestCrearContrato:
    @patch("app.api.contratos.ContratoResponse")
    @patch("app.api.contratos.ContratoFieldsExtractor")
    def test_crear_contrato_socio(self, mock_extractor, mock_response_cls):
        user = _mock_usuario(es_socio=True)
        db = MagicMock()
        db.refresh = MagicMock()
        mock_response_cls.model_validate.return_value = MagicMock()

        data = MagicMock()
        data.titulo = "Nuevo contrato"
        data.categoria = "poder"
        data.subcategoria = None
        data.descripcion = None
        data.contenido_docx = None
        data.contenido_texto = None
        data.archivo_original = None
        data.fuente_original = None
        data.activo = True

        result = crear_contrato(contrato=data, db=db, current_user=user)
        assert db.add.called
        assert db.commit.called

    def test_crear_contrato_sin_permiso(self):
        user = _mock_usuario(email="nadie@grupoconexion.uy", es_socio=False)
        db = MagicMock()

        data = MagicMock()
        data.titulo = "Intento"

        with pytest.raises(HTTPException) as exc_info:
            crear_contrato(contrato=data, db=db, current_user=user)
        assert exc_info.value.status_code == 403


# ============================================================================
# ELIMINAR (soft delete)
# ============================================================================


class TestEliminarContrato:
    def test_soft_delete_exitoso(self):
        user = _mock_usuario(es_socio=True)
        contrato = _mock_contrato()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = contrato

        result = eliminar_contrato(contrato.id, db=db, current_user=user)
        assert db.commit.called
        assert result["message"] == "Contrato eliminado"

    def test_soft_delete_sin_permiso(self):
        user = _mock_usuario(email="nadie@grupoconexion.uy", es_socio=False)
        db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            eliminar_contrato(uuid4(), db=db, current_user=user)
        assert exc_info.value.status_code == 403

    def test_soft_delete_contrato_no_encontrado(self):
        user = _mock_usuario(es_socio=True)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            eliminar_contrato(uuid4(), db=db, current_user=user)
        assert exc_info.value.status_code == 404


# ============================================================================
# GENERAR CONTRATO
# ============================================================================


class TestGenerarContrato:
    @patch("app.api.contratos.ContratoGenerator")
    def test_generar_exitoso(self, mock_generator_class):
        user = _mock_usuario(es_socio=True)
        contrato = _mock_contrato()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = contrato

        mock_generator = MagicMock()
        mock_generator.generar.return_value = b"generated-docx"
        mock_generator_class.return_value = mock_generator

        result = generar_contrato(
            contrato_id=contrato.id,
            datos={"valores": {"campo1": "valor1"}},
            db=db,
            current_user=user,
        )
        # Debe retornar un Response con contenido binario
        assert result.body == b"generated-docx"

    def test_generar_sin_valores(self):
        user = _mock_usuario(es_socio=True)
        contrato = _mock_contrato()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = contrato

        with pytest.raises(HTTPException) as exc_info:
            generar_contrato(
                contrato_id=contrato.id,
                datos={"valores": {}},
                db=db,
                current_user=user,
            )
        assert exc_info.value.status_code == 400

    def test_generar_sin_permiso(self):
        user = _mock_usuario(email="nadie@grupoconexion.uy", es_socio=False)
        db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            generar_contrato(
                contrato_id=uuid4(),
                datos={"valores": {"x": "y"}},
                db=db,
                current_user=user,
            )
        assert exc_info.value.status_code == 403
