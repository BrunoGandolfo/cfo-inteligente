from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import logging
import os
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.operaciones import router as operaciones_router
from app.api.tipo_cambio import router as tipo_cambio_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="CFO Inteligente API",
    description="Sistema Financiero Conexión Consultora",
    version="0.1.0"
)

# Middleware para manejar headers de proxy (X-Forwarded-Proto, X-Forwarded-For)
# Necesario para que Railway preserve HTTPS en redirects
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

# CORS - lee orígenes de variable de entorno
cors_origins = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost:3000,http://localhost:5173,http://localhost:5174"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Incluir routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(operaciones_router, prefix="/api/operaciones", tags=["operaciones"])
app.include_router(tipo_cambio_router, prefix="/api/tipo-cambio", tags=["tipo_cambio"])

@app.get("/")
def read_root():
    return {"message": "CFO Inteligente API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "environment": settings.environment}
from app.api.cfo_ai import router as cfo_router
app.include_router(cfo_router, prefix="/api/cfo", tags=["cfo"])

from app.api.cfo_streaming import router as cfo_streaming_router
app.include_router(cfo_streaming_router, prefix="/api/cfo", tags=["cfo-streaming"])

from app.api.chat_export import router as chat_export_router
app.include_router(chat_export_router, prefix="/api/cfo", tags=["cfo-export"])

from app.api.frases_motivacionales import router as frases_router
app.include_router(frases_router)

from app.api.catalogos import router as catalogos_router
app.include_router(catalogos_router, prefix="/api/catalogos", tags=["catalogos"])

from app.api.metricas import router as metricas_router
app.include_router(metricas_router, prefix="/api/metricas", tags=["metricas"])

from app.api.soporte_ai import router as soporte_router
app.include_router(soporte_router)

from app.api.indicadores import router as indicadores_router
app.include_router(indicadores_router)

from app.api.expedientes import router as expedientes_router
app.include_router(expedientes_router)

from app.api.leyes import router as leyes_router
app.include_router(leyes_router)
from app.api.casos import router as casos_router
app.include_router(casos_router)
from app.api.contratos import router as contratos_router
app.include_router(contratos_router)

from app.api.ala import router as ala_router
app.include_router(ala_router, prefix="/api/ala", tags=["ALA - Anti Lavado"])


# ============================================================================
# EVENTOS STARTUP / SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Inicia servicios al arrancar la aplicación."""
    if settings.environment == "production":
        from app.services.scheduler_service import iniciar_scheduler
        iniciar_scheduler()
        logger.info("🚀 Scheduler activado (producción)")
    else:
        logger.info("⏸️ Scheduler desactivado (desarrollo)")


@app.on_event("shutdown")
async def shutdown_event():
    """Detiene servicios al cerrar la aplicación."""
    if settings.environment == "production":
        from app.services.scheduler_service import detener_scheduler
        detener_scheduler()
