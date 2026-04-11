from app.models.area import Area
from app.models.socio import Socio
from app.models.operacion import Operacion, TipoOperacion, Moneda, Localidad
from app.models.distribucion import DistribucionDetalle
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.proveedor import Proveedor
from app.models.conversacion import Conversacion, Mensaje
from app.models.expediente import Expediente, ExpedienteMovimiento
from app.models.caso import Caso, EstadoCaso, PrioridadCaso
from app.models.contrato import Contrato
from app.models.doctrina import Doctrina
from app.models.sentencia import Sentencia
from app.models.scraping_progress import ScrapingProgress, ScrapingFailure, ScrapingLog
from app.models.tramite_dgr import TramiteDgr
from app.models.tramite_dgr_historial import TramiteDgrHistorial
from app.models.telegram_usuario import TelegramUsuario
from app.models.verificacion_ala import VerificacionALA, ListaALAMetadata
from app.models.consulta_contable import ConsultaContable

__all__ = [
    "Area",
    "Socio", 
    "Operacion",
    "TipoOperacion",
    "Moneda",
    "Localidad",
    "DistribucionDetalle",
    "Usuario",
    "Cliente",
    "Proveedor",
    "Conversacion",
    "Mensaje",
    "Expediente",
    "ExpedienteMovimiento",
    "Caso",
    "EstadoCaso",
    "PrioridadCaso",
    "Contrato",
    "Doctrina",
    "Sentencia",
    "ScrapingProgress",
    "ScrapingFailure",
    "ScrapingLog",
    "TramiteDgr",
    "TramiteDgrHistorial",
    "TelegramUsuario",
    "VerificacionALA",
    "ListaALAMetadata",
    "ConsultaContable",
]
