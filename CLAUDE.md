# CFO Inteligente
Sistema financiero y de gestión para Conexión Consultora, estudio jurídico-contable en Uruguay. Producción en Railway. Operaciones reales bimoneda (UYU/USD) con cotizaciones históricas.

## Stack
- Backend: Python 3.11 + FastAPI 0.115 + SQLAlchemy 2.0 (SYNC, no async) + Pydantic + Alembic
- Frontend: React 19 + Vite 7 + TailwindCSS 3.4 + Recharts + Framer Motion (JavaScript puro, sin TypeScript)
- Base de datos: PostgreSQL 15 (UUIDs como PK, soft delete con deleted_at)
- IA: Anthropic API — claude-sonnet-4-5-20250929 para todo (SQL, narrativa, soporte, ALA, contratos)
- Deploy: Railway. Backend: dazzling-courage. Frontend: sunny-serenity. Deploy automático en push a main
- Tipo de cambio: DolarApi (https://uy.dolarapi.com/v1/cotizaciones/usd), no BCU directo

## Estructura
```
backend/app/
  api/          → 15 routers, 65 endpoints
  models/       → 15 modelos SQLAlchemy (15 tablas)
  services/     → 25+ servicios (ai/, metrics/, validators/, report_data/)
  schemas/      → Pydantic schemas
  core/         → config, database, security, constants, exceptions
  repositories/ → Base + Operations
frontend/src/
  pages/        → 10 páginas (Dashboard, Expedientes, Casos, ALA, Contratos, Indicadores, Soporte, Home, Login, ColaboradorView)
  components/   → 12 carpetas, 39 componentes
  hooks/        → 13 custom hooks
  context/      → FilterContext + ThemeContext
  services/api/ → axiosClient centralizado
```

## Módulos del sistema
- Financiero (operaciones, retiros, distribuciones) — módulo central
- Expedientes judiciales (sincronización SOAP con Poder Judicial Uruguay)
- Casos legales (CRUD con estados y prioridades)
- Antilavado ALA (verificación contra listas PEP/ONU/OFAC/UE, certificado PDF)
- Contratos notariales (plantillas DOCX, extracción de campos con Claude)
- Indicadores económicos (UI, UR, BPC, inflación, cotización USD)
- Soporte AI (chat con documentación contextual)
- Dashboard y métricas (4 métricas principales + 3 gráficos Recharts)

## Comandos
```bash
cd ~/cfo-inteligente/backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8002  # Backend
cd ~/cfo-inteligente/frontend && npm run dev          # Frontend (localhost:5174)
cd ~/cfo-inteligente/backend && python -m pytest tests/ -q -k "not TestStreaming and not test_tasa_respuesta_exitosa" --tb=short  # Tests (695 verdes)
cd ~/cfo-inteligente/frontend && npm run build         # Build frontend
```

## Restricciones CRÍTICAS
- SQL siempre parametrizado. Nunca f-strings en queries
- Soft delete: nunca DELETE FROM. Siempre UPDATE SET deleted_at = NOW(). Filtrar deleted_at IS NULL en toda query
- PostgreSQL agrega → Python calcula → Claude narra. Claude NUNCA hace aritmética
- total_pesificado y total_dolarizado son las únicas columnas válidas para sumar operaciones multi-moneda
- Retiros y Distribuciones son dos pasos del mismo movimiento. Nunca contar ambos en capital de trabajo
- Nunca git add -A. Solo archivos específicos
- Nunca modificar migraciones Alembic ya existentes
- Nunca leer ni loggear .env, API keys, tokens, passwords
- Todo cambio se prueba local primero. El arquitecto humano decide cuándo commitear y pushear
- 695 tests verdes antes de cualquier push a producción

## Convenciones
- Backend: snake_case funciones, UPPERCASE enums, imports absolutos (from app.core.database import get_db)
- Frontend: PascalCase componentes (.jsx), camelCase hooks (.js), TailwindCSS utility-first con tokens CSS en index.css
- Data fetching: via custom hooks usando axiosClient. Streaming SSE usa fetch nativo (justificado)
- Services reciben db: Session como primer argumento. Errores: HTTPException con status_code y detail
- Montos: NUMERIC(15,2). Tipo de cambio: NUMERIC(10,4). Type hints en services y repositories

## Skills
Los agentes deben leer .claude/skills/ antes de ejecutar tareas. Skills tienen prioridad si hay conflicto.

## Cómo trabajamos
- Un arquitecto humano orquesta, no programa. Los agentes ejecutan
- Una tarea a la vez. Aprobación explícita antes de avanzar
- 95% investigación, 5% ejecución. Verificar antes de cambiar
