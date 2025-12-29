from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.operaciones import router as operaciones_router
from app.api.tipo_cambio import router as tipo_cambio_router

app = FastAPI(
    title="CFO Inteligente API",
    description="Sistema Financiero Conexión Consultora",
    version="0.1.0"
)

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

