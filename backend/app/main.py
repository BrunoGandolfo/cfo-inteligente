from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.operaciones import router as operaciones_router
from app.api.tipo_cambio import router as tipo_cambio_router
from app.api.reportes import router as reportes_router
from app.api import reportes_dashboard

app = FastAPI(
    title="CFO Inteligente API",
    description="Sistema Financiero Conexión Consultora",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(operaciones_router, prefix="/api/operaciones", tags=["operaciones"])
app.include_router(tipo_cambio_router, prefix="/api/tipo-cambio", tags=["tipo_cambio"])
app.include_router(reportes_router, prefix="/api/reportes", tags=["reportes"])
app.include_router(reportes_dashboard.router, prefix="/api/reportes", tags=["reportes"])

@app.get("/")
def read_root():
    return {"message": "CFO Inteligente API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}
from app.api.cfo_ai import router as cfo_router
app.include_router(cfo_router, prefix="/api/cfo", tags=["cfo"])
