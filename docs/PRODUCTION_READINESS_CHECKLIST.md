# CFO Inteligente -- Checklist de Produccion

**Fecha:** 2026-02-07
**Version analizada:** Branch `main`
**Estado actual:** NO APTO para produccion sin correcciones
**Nota global:** 4.5/10

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Seguridad -- Vulnerabilidades Criticas](#2-seguridad--vulnerabilidades-criticas)
3. [Seguridad -- Autenticacion y Autorizacion](#3-seguridad--autenticacion-y-autorizacion)
4. [Seguridad -- Proteccion de Datos](#4-seguridad--proteccion-de-datos)
5. [Seguridad -- Headers y CORS](#5-seguridad--headers-y-cors)
6. [Backend -- Calidad de Codigo](#6-backend--calidad-de-codigo)
7. [Backend -- Base de Datos](#7-backend--base-de-datos)
8. [Backend -- AI/LLM Pipeline](#8-backend--aillm-pipeline)
9. [Frontend -- Arquitectura](#9-frontend--arquitectura)
10. [Frontend -- Calidad de Codigo](#10-frontend--calidad-de-codigo)
11. [Testing](#11-testing)
12. [DevOps e Infraestructura](#12-devops-e-infraestructura)
13. [Docker y Contenedores](#13-docker-y-contenedores)
14. [Monitoreo y Observabilidad](#14-monitoreo-y-observabilidad)
15. [Rendimiento](#15-rendimiento)
16. [Dependencias](#16-dependencias)
17. [Documentacion y Mantenibilidad](#17-documentacion-y-mantenibilidad)
18. [Plan de Accion Priorizado](#18-plan-de-accion-priorizado)

---

## 1. Resumen Ejecutivo

CFO Inteligente es una aplicacion financiera (FastAPI + React + PostgreSQL + Claude AI) para una consultora uruguaya. Maneja operaciones financieras, expedientes judiciales, verificaciones anti-lavado (ALA), insights AI y generacion de documentos.

### Estado por Area

| Area | Nota | Estado |
|------|------|--------|
| Seguridad | 3/10 | CRITICO - Bloquea produccion |
| Arquitectura Backend | 6/10 | Aceptable con mejoras |
| Arquitectura Frontend | 4/10 | Requiere refactorizacion |
| Testing | 3/10 | CRITICO - 79% tests frontend son stubs |
| DevOps/Infra | 3/10 | CRITICO - Sin CI/CD ni monitoreo |
| Rendimiento | 5/10 | Aceptable con mejoras |
| Documentacion | 7/10 | Buena |

### Criterios de Bloqueo para Produccion

Los items marcados con `[BLOQUEANTE]` deben resolverse ANTES de ir a produccion.
Los items marcados con `[ALTO]` deben resolverse en los primeros 30 dias post-launch.
Los items marcados con `[MEDIO]` deben resolverse en los primeros 90 dias.
Los items marcados con `[BAJO]` son mejoras recomendadas sin fecha limite.

---

## 2. Seguridad -- Vulnerabilidades Criticas

### 2.1 [BLOQUEANTE] SQL Injection via LLM

**Archivo:** `backend/app/services/cfo_ai_service.py:40`
```python
result = db.execute(text(sql_query))
```

**Problema:** Queries SQL generadas por IA se ejecutan directamente contra la base de datos de produccion. El filtro actual (lineas 10-13) es un blocklist con regex que puede ser evadido.

**Blocklist actual (linea 10-13):**
```python
COMANDOS_PROHIBIDOS = [
    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE',
    'ALTER', 'GRANT', 'REVOKE', 'CREATE', 'COPY'
]
```

**Vectores de bypass conocidos:**
- Subqueries: `SELECT * FROM (DELETE FROM operaciones RETURNING *) x`
- Comentarios SQL: `SEL/**/ECT` o `DR/**/OP`
- Encoding: `\x44\x52\x4F\x50` (DROP)
- `EXEC`, `CALL`, `SET`, `EXPLAIN` no estan bloqueados
- El chequeo de punto y coma (`sql_query.count(';') > 1`) no maneja semicolons en strings

**Solucion requerida:**
- [ ] Crear un usuario de base de datos de solo lectura (READ-ONLY) dedicado para queries AI
- [ ] Implementar whitelist de tablas permitidas en lugar de blocklist de comandos
- [ ] Ejecutar queries AI en una conexion separada con timeout de 5 segundos
- [ ] Agregar LIMIT forzado a todas las queries AI (max 1000 filas)
- [ ] Validar AST del SQL con `sqlparse` en lugar de regex
- [ ] Loggear toda query AI ejecutada para auditoria

---

### 2.2 [BLOQUEANTE] Password de Reset Hardcodeada

**Archivo:** `backend/app/api/auth.py:352`
```python
temp_password = "Temporal123"
usuario.password_hash = hash_password(temp_password)
```

**Problema:** Todos los resets de password generan la misma contraseña. Un atacante que conozca esto puede acceder a cualquier cuenta recien reseteada.

**Agravante (lineas 356-358):** La password temporal se devuelve en el body de la respuesta HTTP:
```python
return ResetPasswordResponse(
    message=f"Contraseña de {usuario.nombre} reseteada exitosamente",
    temp_password=temp_password
)
```

**Solucion requerida:**
- [ ] Reemplazar por `secrets.token_urlsafe(16)` para generar una password unica por reset
- [ ] Implementar flujo de reset por email con token de un solo uso y expiracion (15 min)
- [ ] Forzar cambio de password en el siguiente login
- [ ] Registrar evento de reset en log de auditoria

---

### 2.3 [BLOQUEANTE] Datos Sensibles en el Repositorio Git

**Archivos comprometidos:**
| Archivo | Contenido Sensible |
|---------|-------------------|
| `operaciones_auditoria.csv` | UUIDs, nombres de clientes, montos financieros |
| `operaciones_auditoria_v2.csv` | Mismos datos con nombres de areas |
| `backend/backup_antes_datos_masivos.sql` | Backup completo de la base de datos |
| `backend/cfo_test_backup.dump` | Dump PostgreSQL con esquema y datos |
| `backend/scripts/test_50_resultados.csv` | Queries SQL que revelan esquema completo |
| `scripts/setup_production_db.sh:42` | Password `cfo_pass` hardcodeada |

**Problema:** Aunque `.gitignore` ahora incluye `*.sql` y `*.dump`, estos archivos fueron committeados antes y persisten en el historial de git.

**Solucion requerida:**
- [ ] Ejecutar `git filter-repo` o BFG Repo Cleaner para eliminar archivos del historial
- [ ] Rotar todas las credenciales expuestas (password DB, API keys)
- [ ] Verificar que `.gitignore` cubra: `*.csv`, `*.sql`, `*.dump`, `.env*`, `*.log`
- [ ] Configurar pre-commit hook con `detect-secrets` para prevenir futuros leaks
- [ ] Notificar al equipo que las credenciales expuestas deben considerarse comprometidas

---

### 2.4 [BLOQUEANTE] Password de Base de Datos Hardcodeada

**Archivo:** `scripts/setup_production_db.sh:42`
```bash
export DATABASE_URL="postgresql://$DB_USER:cfo_pass@localhost:5432/$DB_NAME"
```

**Archivo:** `docker-compose.yml` (defaults inseguros)
```yaml
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-cfo_password}
```

**Solucion requerida:**
- [ ] Eliminar passwords hardcodeadas de todos los scripts
- [ ] Usar variables de entorno o secrets manager (Railway secrets, AWS Secrets Manager)
- [ ] Generar passwords fuertes (32+ caracteres aleatorios)
- [ ] No usar valores default para credentials en docker-compose

---

## 3. Seguridad -- Autenticacion y Autorizacion

### 3.1 [BLOQUEANTE] Token JWT de 30 Dias sin Revocacion

**Archivo:** `backend/app/core/config.py:12`
```python
access_token_expire_minutes: int = 43200  # 30 dias
```

**Archivo:** `backend/app/core/security.py:24-28`
```python
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
```

**Problemas:**
- 30 dias de validez es excesivo para una app financiera
- No existe mecanismo de refresh tokens
- No existe blacklist/revocacion de tokens
- El token solo incluye claim `exp`, falta `iss`, `aud`, `iat`, `jti`

**Solucion requerida:**
- [ ] Reducir access token a 15-60 minutos
- [ ] Implementar refresh tokens (7-14 dias) almacenados en httpOnly cookie
- [ ] Agregar tabla `revoked_tokens` para blacklist
- [ ] Agregar claims JWT: `iss` (issuer), `aud` (audience), `iat` (issued at), `jti` (unique ID)
- [ ] Implementar endpoint `/api/auth/refresh` y `/api/auth/logout`

---

### 3.2 [BLOQUEANTE] Autorizacion Client-Side Bypassable

**Archivo:** `frontend/src/pages/Login.jsx:33-36`
```javascript
localStorage.setItem('token', response.data.access_token);
localStorage.setItem('userName', response.data.nombre);
localStorage.setItem('esSocio', String(response.data.es_socio).toLowerCase());
localStorage.setItem('userEmail', email);
```

**Archivo:** `frontend/src/components/layout/Sidebar.jsx:10-23`
```javascript
const USUARIOS_ACCESO_EXPEDIENTES_CASOS = [
    "bgandolfo@cgmasociados.com",
    "gtaborda@grupoconexion.uy",
    "falgorta@grupoconexion.uy",
    "gferrari@grupoconexion.uy",
];
```

**Problemas:**
- `esSocio` leido de `localStorage` es modificable desde DevTools
- ACLs hardcodeadas con emails en el bundle JavaScript (visible para todos)
- Toda la logica de autorizacion de modulos (Expedientes, ALA, Notarial) es client-side

**Solucion requerida:**
- [ ] Mover toda la logica de autorizacion al backend con middleware de permisos
- [ ] Crear sistema de roles en la base de datos (tabla `roles`, `user_roles`, `permissions`)
- [ ] Endpoint `/api/auth/me` debe devolver roles y permisos
- [ ] Eliminar hardcoded emails del frontend
- [ ] Frontend solo debe ocultar UI basado en permisos del backend, nunca decidir acceso

---

### 3.3 [BLOQUEANTE] Sin Control de Acceso en Mutations Criticas

**Archivo:** `backend/app/api/operaciones.py:58-81`
```python
@router.patch("/{operacion_id}/anular")
def anular_operacion(
    operacion_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
```

**Problema:** `anular_operacion` y `actualizar_operacion` inyectan `current_user` pero nunca verifican si es socio o tiene permisos. Cualquier usuario autenticado puede anular o modificar cualquier operacion.

**Comparacion:** `crear_retiro` (linea 93) y `crear_distribucion` (linea 99) SI verifican `current_user.es_socio`.

**Solucion requerida:**
- [ ] Agregar verificacion `if not current_user.es_socio: raise HTTPException(403)` en `anular_operacion`
- [ ] Agregar verificacion en `actualizar_operacion`
- [ ] Crear decorator o dependency `require_socio` reutilizable
- [ ] Auditar TODOS los endpoints para consistencia de permisos
- [ ] Agregar tests que verifiquen que usuarios no-socio reciben 403

---

### 3.4 [ALTO] Password Policy Debil

**Archivo:** `backend/app/api/auth.py:137`
```python
if len(request.password) < 6:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="La contraseña debe tener al menos 6 caracteres"
    )
```

**Problema:** Solo se requieren 6 caracteres sin requisitos de complejidad. Inaceptable para app financiera.

**Solucion requerida:**
- [ ] Minimo 12 caracteres
- [ ] Requerir al menos: 1 mayuscula, 1 minuscula, 1 numero, 1 caracter especial
- [ ] Implementar check contra diccionario de passwords comunes (top 10K)
- [ ] No permitir password igual al email o nombre de usuario
- [ ] Crear funcion `validate_password_strength()` centralizada
- [ ] Aplicar la misma politica en: `/register`, `/change-password`, `/cambiar-password-publico`

---

### 3.5 [ALTO] Enumeracion de Usuarios

**Archivo:** `backend/app/api/auth.py:263-274`
```python
if not usuario:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Usuario no encontrado"
    )
# vs
if not verify_password(request.password_actual, usuario.password_hash):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Contraseña actual incorrecta"
    )
```

**Problema:** En el endpoint `cambiar-password-publico`, el mensaje y codigo HTTP difieren entre "usuario no encontrado" (404) y "password incorrecta" (400). Un atacante puede determinar que cuentas existen.

**Nota:** El endpoint `/login` (linea 88) NO tiene este problema -- usa un mensaje combinado.

**Solucion requerida:**
- [ ] Unificar respuesta: siempre devolver `400 "Credenciales invalidas"` para ambos casos
- [ ] Agregar delay constante (timing-safe) para prevenir timing attacks
- [ ] Auditar todos los endpoints de auth por mensajes de error informativos

---

### 3.6 [ALTO] Registro Abierto sin Verificacion

**Archivo:** `backend/app/api/auth.py:112-179`
```python
@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registro publico - cualquiera puede crear su cuenta.
```

**Problema:** Cualquiera puede crear una cuenta sin verificacion de email, sin CAPTCHA, y sin rate limiting.

**Solucion requerida:**
- [ ] Implementar verificacion de email (enviar link de confirmacion)
- [ ] Agregar CAPTCHA (reCAPTCHA v3 o hCaptcha) en el registro
- [ ] Implementar rate limiting (max 5 registros por IP por hora)
- [ ] Considerar: registro solo por invitacion para app financiera interna

---

### 3.7 [ALTO] Sin Rate Limiting

**Problema:** No existe rate limiting en ningun endpoint de la aplicacion.

**Endpoints criticos sin proteccion:**
- `POST /api/auth/login` -- Permite brute-force de passwords
- `POST /api/auth/register` -- Permite creacion masiva de cuentas
- `POST /api/auth/reset-password` -- Permite spam de resets
- `POST /api/cfo/preguntar` -- Permite abuso de la API de Claude (costos)
- `POST /api/cfo/streaming/preguntar` -- Mismo problema

**Solucion requerida:**
- [ ] Instalar `slowapi` (wrapper de `limits` para FastAPI)
- [ ] Configurar limites por endpoint:
  - Login: 5 intentos / minuto por IP
  - Register: 3 registros / hora por IP
  - Reset password: 3 resets / hora por email
  - CFO AI: 20 preguntas / hora por usuario
  - Endpoints generales: 100 requests / minuto por usuario
- [ ] Almacenar contadores en Redis (o en memoria si no hay Redis)
- [ ] Devolver headers `X-RateLimit-*` en las respuestas
- [ ] Implementar lockout temporal tras 10 intentos fallidos de login

---

### 3.8 [ALTO] JWT en localStorage (Vulnerable a XSS)

**Archivo:** `frontend/src/pages/Login.jsx:33`
```javascript
localStorage.setItem('token', response.data.access_token);
```

**Problema:** localStorage es accesible por cualquier JavaScript en la pagina. Un ataque XSS podria robar el token.

**Solucion requerida:**
- [ ] Migrar token a httpOnly cookie con flags: `Secure`, `SameSite=Strict`, `Path=/api`
- [ ] Backend debe setear la cookie en `/login` response y leerla automaticamente
- [ ] Eliminar token de localStorage
- [ ] Agregar proteccion CSRF (token en header custom + cookie double-submit)

---

## 4. Seguridad -- Proteccion de Datos

### 4.1 [ALTO] PII en Logs

**Multiples archivos logean emails de usuarios:**
```python
logger.info(f"Sincronizando expediente {data.iue} - Usuario: {current_user.email}")
```

**Solucion requerida:**
- [ ] Reemplazar `current_user.email` por `current_user.id` en todos los logs
- [ ] Crear funcion `mask_pii(email)` que devuelva `b***@domain.com`
- [ ] Auditar todos los `logger.info/error/warning` por datos sensibles
- [ ] Documentar politica de logs: no PII, no tokens, no passwords

---

### 4.2 [MEDIO] API Key Parcialmente Expuesta en Script de Debug

**Archivo:** `backend/scripts/test_claude_directo.py:39-41`
```python
print(f"   Primeros 10 chars: {api_key[:10]}...")
print(f"   Longitud: {len(api_key)}")
print(f"   Formato valido: {api_key.startswith('sk-ant-')}")
```

**Solucion requerida:**
- [ ] Eliminar script de debug del repositorio o moverlo a `.gitignore`
- [ ] Nunca logear prefijos de API keys
- [ ] Agregar `scripts/test_*` a `.gitignore`

---

### 4.3 [MEDIO] Excepciones Internas Expuestas al Cliente

**Archivo:** `backend/app/services/cfo_ai_service.py:54`
```python
except Exception as e:
    return {"success": False, "error": str(e)}
```

**Archivo:** `backend/app/api/cfo_ai.py:105-109`
```python
except Exception as e:
    return {"error": str(e), "status": "error"}
```

**Archivo:** `backend/app/api/cfo_streaming.py:275-277`
```python
yield sse_format("error", {"detail": str(e)[:100]})
```

**Problema:** `str(e)` puede contener nombres de tablas, columnas, estructura SQL, rutas de archivos.

**Solucion requerida:**
- [ ] Reemplazar `str(e)` en respuestas al cliente por mensajes genericos
- [ ] Logear el error completo solo en server-side: `logger.exception("Error en CFO AI")`
- [ ] Crear mapeo de excepciones conocidas a mensajes amigables
- [ ] Devolver un `error_id` para correlacion con logs internos

---

## 5. Seguridad -- Headers y CORS

### 5.1 [ALTO] Sin Security Headers en Nginx

**Archivo:** `frontend/nginx.conf`

**Headers faltantes:**

**Solucion requerida -- agregar al bloque `server`:**
```nginx
# Seguridad
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https://cfo-inteligente-production.up.railway.app;" always;
```

- [ ] Agregar todos los security headers listados
- [ ] Testear con https://securityheaders.com/ tras deployment
- [ ] Ajustar CSP segun recursos externos reales usados

---

### 5.2 [ALTO] CORS Wildcard en Streaming

**Archivo:** `backend/app/api/cfo_streaming.py:286`
```python
headers={
    "Access-Control-Allow-Origin": "*"
}
```

**Problema:** El endpoint SSE sobreescribe la politica CORS de la app con wildcard `*`, permitiendo que cualquier sitio web consuma el stream.

**Solucion requerida:**
- [ ] Eliminar el header manual `Access-Control-Allow-Origin: *`
- [ ] Dejar que el middleware CORS global de FastAPI maneje CORS consistentemente
- [ ] Si se necesita CORS especial para SSE, usar el origin del request validado

---

### 5.3 [MEDIO] ProxyHeadersMiddleware Trust All

**Archivo:** `backend/app/main.py:21`
```python
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])
```

**Problema:** Cualquier cliente puede falsificar `X-Forwarded-For` y `X-Forwarded-Proto`.

**Solucion requerida:**
- [ ] Restringir a IPs conocidas del proxy/load balancer: `trusted_hosts=["10.0.0.0/8", "172.16.0.0/12"]`
- [ ] Si se usa Railway, configurar con las IPs de su infraestructura

---

## 6. Backend -- Calidad de Codigo

### 6.1 [ALTO] `get_db()` Duplicado

**Archivo 1:** `backend/app/core/database.py:11-16`
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Archivo 2:** `backend/app/core/dependencies.py:29-47`
```python
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Problema:** Diferentes modulos importan `get_db` de diferentes ubicaciones, creando confusion y potenciales inconsistencias.

**Solucion requerida:**
- [ ] Mantener `get_db` SOLO en `dependencies.py` (lugar canonico para FastAPI dependencies)
- [ ] Eliminar de `database.py`
- [ ] Actualizar todos los imports: `from app.core.dependencies import get_db`
- [ ] Buscar con grep: `from app.core.database import get_db` y reemplazar todos

---

### 6.2 [ALTO] Endpoint PATCH sin Schema de Validacion

**Archivo:** `backend/app/api/operaciones.py:220-225`
```python
@router.patch("/{operacion_id}")
def actualizar_operacion(
    operacion_id: str,
    data: dict,  # <-- Sin schema Pydantic
    ...
):
```

**Problema:** Acepta cualquier JSON sin validacion. No aparece en la documentacion OpenAPI.

**Solucion requerida:**
- [ ] Crear `ActualizarOperacionRequest(BaseModel)` con campos opcionales tipados
- [ ] Reemplazar `data: dict` por `data: ActualizarOperacionRequest`
- [ ] Validar que solo campos permitidos sean actualizados
- [ ] Agregar test de que campos no permitidos son rechazados

---

### 6.3 [ALTO] Division por Cero sin Guardia

**Archivo:** `backend/app/services/operacion_service.py`

**Lineas afectadas:** 9, 101, 112, 167, 203

```python
# Linea 9
return monto_original, monto_original / tipo_cambio

# Linea 101
monto_usd = data.monto_uyu / data.tipo_cambio

# Lineas 112, 167
total_dolarizado = total_usd + (total_uyu / data.tipo_cambio)

# Linea 203
detalle_total_dolarizado = detalle_monto_usd + (detalle_monto_uyu / data.tipo_cambio)
```

**Solucion requerida:**
- [ ] Agregar validacion en Pydantic schema: `tipo_cambio: Decimal = Field(gt=0)`
- [ ] Agregar guardia en `calcular_montos`: `if tipo_cambio <= 0: raise ValueError("tipo_cambio debe ser mayor a 0")`
- [ ] Agregar test: `test_calcular_montos_tipo_cambio_cero`

---

### 6.4 [MEDIO] Singletons Globales a Nivel de Modulo

**Archivo:** `backend/app/api/cfo_ai.py:30-33`
```python
_orchestrator = AIOrchestrator()
claude_sql_gen = ClaudeSQLGenerator()
```

**Archivo:** `backend/app/api/cfo_streaming.py:41-46`
```python
client = Anthropic(api_key=api_key_limpia)
claude_sql_gen = ClaudeSQLGenerator()
```

**Problemas:**
- Instancias duplicadas de `ClaudeSQLGenerator` en dos modulos
- Imposible inyectar mocks para testing limpio
- Instancias creadas al importar el modulo (side effects en import)

**Solucion requerida:**
- [ ] Usar FastAPI dependency injection: `Depends(get_ai_orchestrator)`
- [ ] Crear factory functions en `dependencies.py`
- [ ] Usar `@lru_cache` para singleton con inyeccion:
  ```python
  @lru_cache
  def get_orchestrator():
      return AIOrchestrator()
  ```

---

### 6.5 [MEDIO] Retry Chains Multiplicativas

**Problema:** `claude_client.py` tiene 3 retries con backoff. `AIOrchestrator` tiene su propio retry de 3 intentos. En el peor caso: 3 x 3 = 9 llamadas API y ~32 segundos de espera.

**Solucion requerida:**
- [ ] Definir retry SOLO en un nivel (preferiblemente en el orchestrator)
- [ ] Eliminar retry del client individual
- [ ] Configurar timeout total maximo de 30 segundos

---

### 6.6 [MEDIO] Imports Desorganizados en main.py

**Archivo:** `backend/app/main.py`

3 routers importados al inicio (lineas 7-9) y 8+ routers importados inline despues del health check (lineas 49-82).

**Solucion requerida:**
- [ ] Mover todos los imports de routers al inicio del archivo
- [ ] Agrupar `include_router` en una seccion dedicada
- [ ] Considerar crear `app/api/router.py` que registre todos los sub-routers

---

### 6.7 [MEDIO] Deprecated FastAPI Event Handlers

**Archivo:** `backend/app/main.py:89-101`
```python
@app.on_event("startup")
async def startup_event():
...
@app.on_event("shutdown")
async def shutdown_event():
```

**Solucion requerida:**
- [ ] Migrar a `lifespan` context manager:
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      # startup
      yield
      # shutdown
  app = FastAPI(lifespan=lifespan)
  ```

---

### 6.8 [BAJO] Deprecated SQLAlchemy Import

**Archivo:** `backend/app/core/database.py`
```python
from sqlalchemy.ext.declarative import declarative_base
```

**Solucion requerida:**
- [ ] Migrar a `from sqlalchemy.orm import DeclarativeBase`

---

## 7. Backend -- Base de Datos

### 7.1 [ALTO] Sin Configuracion de Connection Pool

**Archivo:** `backend/app/core/database.py:6`
```python
engine = create_engine(settings.database_url)
```

**Solucion requerida:**
- [ ] Configurar el engine para produccion:
  ```python
  engine = create_engine(
      settings.database_url,
      pool_size=10,
      max_overflow=20,
      pool_pre_ping=True,
      pool_recycle=300,
      pool_timeout=30,
  )
  ```
- [ ] `pool_pre_ping=True` es critico para detectar conexiones muertas
- [ ] Ajustar `pool_size` segun carga esperada

---

### 7.2 [ALTO] Sin SSL/TLS para Conexion a Base de Datos

**Problema:** No hay parametros SSL en la URL de la base de datos ni en `create_engine`.

**Solucion requerida:**
- [ ] Agregar `?sslmode=require` a la DATABASE_URL en produccion
- [ ] O configurar via connect_args:
  ```python
  engine = create_engine(url, connect_args={"sslmode": "require"})
  ```

---

### 7.3 [MEDIO] Sin Backup Automatizado

**Problema:** Solo existen backups manuales committeados en git (que en si es un problema de seguridad).

**Solucion requerida:**
- [ ] Configurar backup automatico diario con `pg_dump`
- [ ] Almacenar backups en storage externo (S3, GCS, Backblaze B2)
- [ ] Implementar retencion: 7 dias diarios, 4 semanales, 12 mensuales
- [ ] Testear restauracion de backup mensualmente
- [ ] Configurar alertas si el backup falla

---

### 7.4 [BAJO] psycopg2-binary en Produccion

**Archivo:** `backend/requirements.txt`
```
psycopg2-binary==2.9.9
```

**Problema:** La propia documentacion de psycopg2 dice que `-binary` no es recomendado para produccion.

**Solucion requerida:**
- [ ] Reemplazar por `psycopg2==2.9.9`
- [ ] Asegurar que `libpq-dev` esta instalado en el Dockerfile

---

## 8. Backend -- AI/LLM Pipeline

### 8.1 [ALTO] Model Drift entre Endpoints

**Archivo:** `backend/app/api/cfo_streaming.py:205`
```python
model="claude-sonnet-4-5-20250929"
```

**Archivo:** `backend/app/services/ai_orchestrator.py:44`
```python
model="claude-sonnet-4-20250514"
```

**Problema:** El endpoint streaming usa un modelo diferente al no-streaming. Las respuestas seran inconsistentes.

**Solucion requerida:**
- [ ] Centralizar modelo en `config.py`: `ai_model: str = "claude-sonnet-4-5-20250929"`
- [ ] Todos los clientes AI deben leer de `settings.ai_model`
- [ ] Documentar procedimiento de actualizacion de modelo

---

### 8.2 [ALTO] Pipeline Streaming Duplicado

**Archivos:**
- `backend/app/api/cfo_ai.py` (296 lineas)
- `backend/app/api/cfo_streaming.py` (288 lineas)

**Problema:** Ambos implementan el mismo pipeline (SQL generation, validation, execution, narrative) por separado. Bug fixes deben aplicarse en ambos.

**Solucion requerida:**
- [ ] Extraer logica comun a `cfo_pipeline_service.py`
- [ ] `cfo_ai.py` y `cfo_streaming.py` solo deben manejar formato de respuesta (JSON vs SSE)
- [ ] Un solo punto de validacion y ejecucion SQL

---

### 8.3 [MEDIO] Sleep Bloqueante en Streaming

**Archivo:** `backend/app/api/cfo_streaming.py:220`
```python
time.sleep(0.15)
```

**Problema:** `time.sleep()` es sincronico y bloquea el thread del worker de Uvicorn. Con 1 solo worker, esto bloquea TODA la aplicacion.

**Solucion requerida:**
- [ ] Reemplazar por `await asyncio.sleep(0.15)` y hacer el generador `async`
- [ ] O eliminar el delay artificial (el streaming ya tiene latencia natural de red)

---

## 9. Frontend -- Arquitectura

### 9.1 [BLOQUEANTE] Sin Router (React Router No Implementado)

**Archivo:** `frontend/src/App.jsx:18`
```javascript
const [currentPage, setCurrentPage] = useState('home');
```

**Problema:** `react-router-dom` esta instalado (`package.json:27`) pero no se usa. La navegacion se hace con `useState`. Consecuencias:
- Sin URLs navegables (no se puede compartir link a una pagina especifica)
- Sin historial del browser (boton atras no funciona)
- Sin deep links
- Sin code splitting por ruta (todo se carga a la vez)
- Sin SEO (no aplica tanto para SPA financiera interna, pero si para crawlers)

**Solucion requerida:**
- [ ] Implementar `BrowserRouter` con `Routes` y `Route`
- [ ] Mapear cada `currentPage` a una ruta URL:
  - `'home'` -> `/`
  - `'dashboard'` -> `/dashboard`
  - `'operaciones'` -> `/operaciones`
  - `'expedientes'` -> `/expedientes`
  - `'ala'` -> `/ala`
  - `'chat'` -> `/chat`
  - etc.
- [ ] Reemplazar `setCurrentPage('X')` por `navigate('/X')`
- [ ] Implementar `ProtectedRoute` component para rutas autenticadas
- [ ] Agregar lazy loading: `React.lazy(() => import('./pages/Dashboard'))`

---

### 9.2 [ALTO] Sin ErrorBoundary

**Problema:** Si cualquier componente lanza una excepcion en render, toda la app muestra pantalla blanca sin informacion.

**Solucion requerida:**
- [ ] Crear `ErrorBoundary` component con `componentDidCatch`
- [ ] Mostrar fallback UI amigable: "Algo salio mal. Recargar pagina."
- [ ] Enviar error a servicio de monitoreo (Sentry)
- [ ] Envolver al menos `<App>` y cada pagina principal con ErrorBoundary

---

### 9.3 [ALTO] Prop Drilling Extremo

**Problema:** `Sidebar` recibe 10+ callbacks de navegacion desde `App.jsx` a traves de `Layout`. Cada nueva pagina agrega un nuevo prop.

**Solucion requerida:**
- [ ] Implementar React Router (resuelve la mayoria del prop drilling de navegacion)
- [ ] Para estado compartido restante, usar Context o Zustand
- [ ] Sidebar debe consumir de router context, no recibir 10 callbacks

---

### 9.4 [ALTO] Modales Duplicados

**Problema:** `ModalIngreso.jsx` (228 lineas) y `ModalGasto.jsx` (227 lineas) son practicamente identicos.

**Solucion requerida:**
- [ ] Crear `ModalOperacion.jsx` parametrizado con `type: 'ingreso' | 'gasto'`
- [ ] Diferencias (endpoint, labels, colores) pasan como props o config
- [ ] Reducir ~450 lineas a ~250 lineas

---

## 10. Frontend -- Calidad de Codigo

### 10.1 [ALTO] FilterContext sin Memoizar

**Archivo:** `frontend/src/context/FilterContext.jsx:18`
```javascript
<FilterContext.Provider value={{ from, to, setFrom, setTo, localidad, setLocalidad, monedaVista, setMonedaVista, version, apply }}>
```

**Problema:** Objeto `value` se recrea en cada render, causando re-renders innecesarios en TODOS los consumidores.

**Solucion requerida:**
- [ ] Envolver en `useMemo`:
  ```javascript
  const value = useMemo(() => ({
    from, to, setFrom, setTo, localidad, setLocalidad,
    monedaVista, setMonedaVista, version, apply
  }), [from, to, localidad, monedaVista, version]);
  ```

---

### 10.2 [ALTO] Hook useMetrics sin Manejo de Errores

**Archivo:** `frontend/src/hooks/useMetrics.js:14-29`
```javascript
try {
    setLoading(true);
    const { data } = await axiosClient.get('/api/metricas/dashboard', { params });
    setMetricas(data.metricas);
} finally {
    setLoading(false);
}
// Sin catch -> Dashboard muestra $0 silenciosamente
```

**Solucion requerida:**
- [ ] Agregar `catch` con estado de error:
  ```javascript
  catch (err) {
    setError(err.response?.data?.detail || "Error cargando metricas");
  }
  ```
- [ ] Retornar `error` del hook para que Dashboard pueda mostrar mensaje
- [ ] Auditar TODOS los hooks por mismo patron

---

### 10.3 [ALTO] Axios Inconsistente

**Archivo:** `frontend/src/App.jsx`

3 formas diferentes de hacer HTTP requests en el mismo archivo:
1. **Linea 35:** `axios.get(...)` -- Raw axios sin interceptors
2. **Lineas 62-76:** `fetch(...)` -- API nativa con fallback `http://localhost:8000`
3. **Otros archivos:** `axiosClient.get(...)` -- Cliente configurado

**Problemas:**
- Las llamadas raw no pasan por el interceptor 401 (logout automatico)
- El fallback de `fetch` es `http://localhost:8000` vs `axiosClient` que usa la URL de produccion
- 3 patrones = 3 puntos de mantenimiento

**Solucion requerida:**
- [ ] Reemplazar TODAS las llamadas HTTP por `axiosClient`
- [ ] Eliminar `import axios from 'axios'` de `App.jsx`
- [ ] Eliminar todas las llamadas `fetch()` nativas
- [ ] Buscar con grep: `axios.get\|axios.post\|fetch(` y reemplazar

---

### 10.4 [MEDIO] Limpieza 401 Incompleta

**Archivo:** `frontend/src/services/api/axiosClient.js:59-60`
```javascript
localStorage.removeItem('token');
localStorage.removeItem('user');  // 'user' nunca se setea!
```

**Login setea:** `'token'`, `'userName'`, `'esSocio'`, `'userEmail'`
**401 limpia:** `'token'`, `'user'` (inexistente)

**Solucion requerida:**
- [ ] Limpiar exactamente lo que se setea:
  ```javascript
  localStorage.removeItem('token');
  localStorage.removeItem('userName');
  localStorage.removeItem('esSocio');
  localStorage.removeItem('userEmail');
  ```
- [ ] Mejor aun: centralizar keys en constantes:
  ```javascript
  const AUTH_KEYS = ['token', 'userName', 'esSocio', 'userEmail'];
  AUTH_KEYS.forEach(k => localStorage.removeItem(k));
  ```

---

### 10.5 [MEDIO] console.log en Produccion

**Problema:** 50+ `console.log` dispersos en hooks y componentes, exponiendo payloads de datos en la consola del browser.

**Solucion requerida:**
- [ ] Instalar `eslint-plugin-no-console` o similar
- [ ] Eliminar todos los `console.log` de produccion
- [ ] Si se necesita logging, crear wrapper que solo logee en desarrollo:
  ```javascript
  const log = import.meta.env.DEV ? console.log : () => {};
  ```

---

### 10.6 [BAJO] Paquetes Instalados No Usados

**Paquete:** `react-router-dom` instalado pero no importado en ningun componente.

**Solucion requerida:**
- [ ] Implementar React Router (item 9.1) o remover el paquete

---

## 11. Testing

### 11.1 [BLOQUEANTE] 79% de Tests Frontend son Stubs Vacios

**Archivos afectados:**

| Archivo | Tests Totales | Tests REALES | Tests STUB |
|---------|:---:|:---:|:---:|
| `tests/e2e/auth.spec.js` | 8 | 8 | 0 |
| `tests/e2e/chat.spec.js` | 10 | 0 | **10** |
| `tests/e2e/dashboard.spec.js` | 6 | 2 | **4** |
| `tests/e2e/filtros.spec.js` | 8 | 0 | **8** |
| `tests/e2e/operaciones.spec.js` | 16 | 0 | **16** |
| **TOTAL** | **48** | **10** | **38** |

**Ejemplo de test stub:**
```javascript
test('1. Filtro moneda USD', async ({ page }) => {
    expect(true).toBe(true);  // SIEMPRE pasa
});
```

**Problema:** El reporte dice "48 tests passed" pero solo 10 verifican algo real. Esto es peor que no tener tests porque crea falsa confianza.

**Solucion requerida:**
- [ ] Implementar los 38 tests stub o eliminarlos
- [ ] Priorizar tests E2E de:
  - Flujo de login/logout
  - Creacion de operacion (ingreso/gasto)
  - Anulacion de operacion
  - Filtros del dashboard
  - Chat AI basico
- [ ] Agregar check en CI que rechace `expect(true).toBe(true)`

---

### 11.2 [ALTO] Tests Backend con Assertions Debiles

**Archivo:** `backend/tests/test_operaciones_cobertura.py:462-463`
```python
assert response.status_code in [200, 422]  # Acepta exito Y error
```

**Archivo:** `backend/tests/test_cfo_streaming_cobertura.py:446`
```python
assert response.status_code in [200, 400, 500]  # Acepta cualquier cosa
```

**Solucion requerida:**
- [ ] Cada test debe assertar UN status code esperado
- [ ] Agregar assertions sobre el body de la respuesta
- [ ] Agregar linter rule para detectar `in [200, 400, 500]` en tests

---

### 11.3 [ALTO] Tests Faltantes Criticos

**Tests que NO existen y DEBEN existir:**

- [ ] Test de SQL injection en queries AI (intentar `'; DROP TABLE --`)
- [ ] Test de division por cero con `tipo_cambio=0`
- [ ] Test de que usuario no-socio recibe 403 en `anular_operacion`
- [ ] Test de que usuario no-socio recibe 403 en `actualizar_operacion`
- [ ] Test de que password reset genera password unica
- [ ] Test de expracion de token JWT
- [ ] Test de CORS (origin no permitido)
- [ ] Test de campos no permitidos en PATCH operacion
- [ ] Test de concurrencia: dos usuarios anulan la misma operacion simultaneamente

---

### 11.4 [MEDIO] Coverage Report Ausente

**Problema:** No hay configuracion de pytest-cov ni reporte de cobertura.

**Solucion requerida:**
- [ ] Agregar `pytest-cov` a requirements-dev.txt
- [ ] Configurar en `pytest.ini` o `pyproject.toml`:
  ```ini
  [tool.pytest.ini_options]
  addopts = "--cov=app --cov-report=html --cov-fail-under=70"
  ```
- [ ] Objetivo minimo: 70% cobertura de lineas
- [ ] Integrar reporte en CI/CD

---

## 12. DevOps e Infraestructura

### 12.1 [BLOQUEANTE] Sin CI/CD Pipeline

**Problema:** No existe `.github/workflows/`, no hay Jenkins, no hay GitLab CI, no hay ningun pipeline de integracion continua.

**Solucion requerida:**
- [ ] Crear `.github/workflows/ci.yml` con:
  ```yaml
  on: [push, pull_request]
  jobs:
    backend-tests:
      - pip install -r requirements.txt
      - pytest --cov=app --cov-fail-under=70
    frontend-tests:
      - npm ci
      - npm run lint
      - npm run build
    security-scan:
      - pip-audit
      - npm audit
  ```
- [ ] Bloquear merge a `main` sin CI verde
- [ ] Agregar badge de CI en README

---

### 12.2 [ALTO] Sin Pre-commit Hooks

**Problema:** No hay `.pre-commit-config.yaml` ni hooks de git configurados.

**Solucion requerida:**
- [ ] Instalar `pre-commit` framework
- [ ] Configurar hooks:
  ```yaml
  repos:
    - repo: https://github.com/pre-commit/pre-commit-hooks
      hooks:
        - id: check-added-large-files
        - id: detect-private-key
        - id: check-merge-conflict
    - repo: https://github.com/Yelp/detect-secrets
      hooks:
        - id: detect-secrets
    - repo: https://github.com/astral-sh/ruff-pre-commit
      hooks:
        - id: ruff
        - id: ruff-format
  ```

---

### 12.3 [ALTO] Sin Linter/Formatter Backend

**Problema:** No hay `ruff.toml`, `pyproject.toml` con configuracion de linting, ni `flake8`, `black`, o `isort` configurados.

**Solucion requerida:**
- [ ] Configurar `ruff` (reemplaza flake8 + black + isort):
  ```toml
  # pyproject.toml
  [tool.ruff]
  line-length = 100
  select = ["E", "F", "I", "W", "B", "S"]  # Incluye bandit (S) para seguridad
  ```

---

### 12.4 [MEDIO] Sin Lint Frontend

**Problema:** No hay `.eslintrc`, `eslint.config.js`, ni configuracion de ESLint visible.

**Solucion requerida:**
- [ ] Configurar ESLint con reglas de React
- [ ] Integrar en CI y en pre-commit hooks

---

## 13. Docker y Contenedores

### 13.1 [ALTO] Container Backend Corre como Root

**Archivo:** `backend/Dockerfile`

**Problema:** Sin directiva `USER`. La aplicacion corre como root dentro del container.

**Solucion requerida:**
- [ ] Agregar al Dockerfile:
  ```dockerfile
  RUN useradd -m -r appuser && chown -R appuser:appuser /app
  USER appuser
  ```

---

### 13.2 [ALTO] Sin .dockerignore en Backend

**Archivo faltante:** `backend/.dockerignore`

**Problema:** `COPY . .` copia todo: `.env`, `.git`, `__pycache__`, `venv/`, backups SQL.

**Solucion requerida:**
- [ ] Crear `backend/.dockerignore`:
  ```
  .git
  .env
  .env.*
  __pycache__
  *.pyc
  venv/
  .venv/
  *.sql
  *.dump
  *.csv
  tests/
  .pytest_cache/
  ```

---

### 13.3 [MEDIO] Sin HEALTHCHECK en Backend

**Archivo:** `backend/Dockerfile`

**Solucion requerida:**
- [ ] Agregar al Dockerfile:
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
  ```
- [ ] El endpoint `/health` debe verificar conectividad a la BD:
  ```python
  @app.get("/health")
  def health():
      try:
          db.execute(text("SELECT 1"))
          return {"status": "healthy", "database": "connected"}
      except:
          return JSONResponse(status_code=503, content={"status": "unhealthy"})
  ```

---

### 13.4 [MEDIO] Compilador gcc en Imagen Final

**Archivo:** `backend/Dockerfile`

**Problema:** `gcc` se instala para compilar dependencias C pero nunca se remueve.

**Solucion requerida:**
- [ ] Usar multi-stage build:
  ```dockerfile
  FROM python:3.12-slim AS builder
  RUN apt-get update && apt-get install -y gcc
  COPY requirements.txt .
  RUN pip install --user -r requirements.txt

  FROM python:3.12-slim
  COPY --from=builder /root/.local /root/.local
  COPY . .
  ```

---

### 13.5 [MEDIO] Puerto de Base de Datos Expuesto

**Archivo:** `docker-compose.yml`
```yaml
ports:
  - "5433:5432"
```

**Solucion requerida:**
- [ ] Eliminar `ports` del servicio de base de datos en produccion
- [ ] Solo los servicios que necesitan acceso directo (backend) deben comunicarse via red interna Docker
- [ ] Si se necesita acceso externo para admin, usar SSH tunnel

---

### 13.6 [MEDIO] URL de Produccion Hardcodeada en Dockerfile

**Archivo:** `frontend/Dockerfile:17`
```dockerfile
ARG VITE_API_URL=https://cfo-inteligente-production.up.railway.app
```

**Solucion requerida:**
- [ ] No usar default para `VITE_API_URL` -- forzar que sea explicitamente seteado en cada ambiente
- [ ] O usar `ARG VITE_API_URL` sin default y fallar el build si no se provee

---

### 13.7 [BAJO] Single Uvicorn Worker

**Archivo:** `backend/entrypoint.sh:8`
```bash
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Solucion requerida:**
- [ ] Usar Gunicorn con workers Uvicorn:
  ```bash
  exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
  ```
- [ ] Agregar `gunicorn` a `requirements.txt`
- [ ] Numero de workers = `2 * num_cpu + 1`

---

## 14. Monitoreo y Observabilidad

### 14.1 [ALTO] Sin Servicio de Error Tracking

**Problema:** No hay Sentry, Datadog, New Relic, ni ningun servicio de error tracking.

**Solucion requerida:**
- [ ] Integrar Sentry (plan gratuito disponible):
  ```python
  import sentry_sdk
  sentry_sdk.init(dsn="...", traces_sample_rate=0.1)
  ```
- [ ] Configurar alertas por email/Slack para errores criticos
- [ ] Capturar excepciones no manejadas automaticamente

---

### 14.2 [ALTO] Health Check No Verifica Dependencias

**Archivo:** `backend/app/main.py` -- El endpoint `/health` devuelve respuesta estatica.

**Solucion requerida:**
- [ ] Verificar conectividad a PostgreSQL
- [ ] Verificar que Anthropic API key es valida (opcional, costoso)
- [ ] Devolver estado de cada dependencia:
  ```json
  {
    "status": "healthy",
    "dependencies": {
      "database": "connected",
      "ai_service": "available"
    },
    "version": "1.0.0",
    "uptime_seconds": 3600
  }
  ```

---

### 14.3 [MEDIO] Sin Metricas de Aplicacion

**Solucion requerida:**
- [ ] Instrumentar con Prometheus client:
  - Requests por endpoint por segundo
  - Latencia P50, P95, P99
  - Errores por tipo (4xx, 5xx)
  - Uso de AI (tokens consumidos, latencia)
  - Conexiones DB activas
- [ ] Crear dashboard en Grafana (o Railway Metrics)

---

### 14.4 [MEDIO] Sin Uptime Monitoring

**Solucion requerida:**
- [ ] Configurar UptimeRobot, Betterstack, o Checkly (planes gratuitos)
- [ ] Monitorear endpoint `/health` cada 1 minuto
- [ ] Alertar por email + Slack si esta down > 2 minutos

---

## 15. Rendimiento

### 15.1 [ALTO] Filtrado Client-Side Innecesario

**Problema:** El dashboard carga todas las operaciones y filtra en el frontend en lugar de enviar filtros al backend.

**Solucion requerida:**
- [ ] Pasar filtros (fecha, moneda, localidad) como query params al backend
- [ ] Backend filtra en SQL (WHERE clauses)
- [ ] Implementar paginacion server-side
- [ ] Agregar indices en columnas de filtro frecuente

---

### 15.2 [MEDIO] Sin Cache para Consultas AI

**Problema:** Preguntas identicas al CFO AI ejecutan una nueva consulta a Claude cada vez.

**Solucion requerida:**
- [ ] Implementar cache de queries:
  - Key: hash(pregunta_normalizada + filtros)
  - TTL: 5 minutos (datos pueden cambiar)
  - Storage: Redis o cache en memoria
- [ ] Estimar ahorro: si 30% de preguntas se repiten, ahorro de ~30% en costos AI

---

### 15.3 [MEDIO] Sin Lazy Loading en Frontend

**Problema:** Todos los componentes se cargan al inicio. No hay code splitting.

**Solucion requerida:**
- [ ] Implementar con React Router + React.lazy:
  ```javascript
  const Dashboard = React.lazy(() => import('./pages/Dashboard'));
  const Operaciones = React.lazy(() => import('./pages/Operaciones'));
  ```
- [ ] Agregar `<Suspense fallback={<Spinner />}>` como wrapper

---

### 15.4 [BAJO] Sin Compresion en Nginx

**Archivo:** `frontend/nginx.conf` -- Sin configuracion de gzip.

**Solucion requerida:**
- [ ] Agregar:
  ```nginx
  gzip on;
  gzip_types text/plain text/css application/json application/javascript text/xml;
  gzip_min_length 1000;
  ```

---

## 16. Dependencias

### 16.1 [ALTO] python-jose Abandonada

**Archivo:** `backend/requirements.txt`
```
python-jose[cryptography]==3.3.0
```

**Problema:** Ultima release 2021. No mantiene. Vulnerabilidades conocidas.

**Solucion requerida:**
- [ ] Migrar a `PyJWT>=2.8.0` o `joserfc`
- [ ] Actualizar `security.py` para usar la nueva libreria
- [ ] Testear generacion y validacion de tokens

---

### 16.2 [MEDIO] Dependencias sin Pin Superior

**Archivo:** `backend/requirements.txt`
```
anthropic>=0.39.0  # Sin limite superior
scipy>=1.16.2      # Sin limite superior
```

**Solucion requerida:**
- [ ] Pinear todas las dependencias con version exacta: `anthropic==0.39.0`
- [ ] O usar rangos: `anthropic>=0.39.0,<1.0.0`
- [ ] Generar `requirements.lock` con `pip freeze`
- [ ] Configurar Dependabot o Renovate para updates automaticos

---

### 16.3 [BAJO] Sin requirements-dev.txt

**Problema:** Dependencias de testing (`pytest`, `httpx`) mezcladas con produccion.

**Solucion requerida:**
- [ ] Crear `requirements-dev.txt` con:
  ```
  -r requirements.txt
  pytest
  pytest-cov
  httpx
  ruff
  pre-commit
  ```
- [ ] Dockerfile solo instala `requirements.txt`

---

## 17. Documentacion y Mantenibilidad

### 17.1 [MEDIO] Sin CHANGELOG

**Solucion requerida:**
- [ ] Crear `CHANGELOG.md` con formato Keep a Changelog
- [ ] Documentar cada release con: Added, Changed, Fixed, Security

---

### 17.2 [MEDIO] Sin CONTRIBUTING Guide

**Solucion requerida:**
- [ ] Crear `CONTRIBUTING.md` con:
  - Setup de ambiente local
  - Proceso de PR
  - Convenciones de commits
  - Politica de branching

---

### 17.3 [BAJO] Sin Versionamiento Semantico

**Problema:** No hay version tag, ni `__version__`, ni `package.json` version actualizada.

**Solucion requerida:**
- [ ] Definir version actual en `backend/app/__init__.py`: `__version__ = "1.0.0"`
- [ ] Usar git tags: `git tag v1.0.0`
- [ ] Sincronizar con `frontend/package.json` version

---

## 18. Plan de Accion Priorizado

### Fase 1: CRITICA (Semana 1-2) -- Bloquea produccion

| # | Tarea | Esfuerzo | Archivos |
|---|-------|----------|----------|
| 1 | Purgar datos sensibles del historial git | 4h | `.gitignore`, BFG |
| 2 | Reemplazar password hardcodeada de reset | 1h | `auth.py` |
| 3 | Crear DB user read-only para AI queries | 4h | `cfo_ai_service.py`, DB config |
| 4 | Reducir JWT a 1h + refresh tokens | 8h | `security.py`, `config.py`, `auth.py`, frontend |
| 5 | Agregar RBAC en anular/actualizar operacion | 2h | `operaciones.py` |
| 6 | Crear CI/CD pipeline basico | 4h | `.github/workflows/ci.yml` |
| 7 | Eliminar o implementar tests stub frontend | 8h | `tests/e2e/*.spec.js` |

**Total estimado Fase 1: ~31 horas**

### Fase 2: ALTA (Semana 3-4)

| # | Tarea | Esfuerzo | Archivos |
|---|-------|----------|----------|
| 8 | Implementar rate limiting con slowapi | 4h | `main.py`, endpoints auth |
| 9 | Agregar security headers en nginx | 2h | `nginx.conf` |
| 10 | Implementar React Router | 12h | `App.jsx`, todos los componentes |
| 11 | Unificar get_db, eliminar duplicado | 1h | `database.py`, `dependencies.py` |
| 12 | Fortalecer password policy | 2h | `auth.py` |
| 13 | Configurar pool de conexiones DB | 1h | `database.py` |
| 14 | Integrar Sentry | 2h | `main.py`, frontend |
| 15 | Crear .dockerignore backend + USER no-root | 1h | `Dockerfile`, `.dockerignore` |
| 16 | Eliminar CORS wildcard en streaming | 1h | `cfo_streaming.py` |

**Total estimado Fase 2: ~26 horas**

### Fase 3: MEDIA (Mes 2)

| # | Tarea | Esfuerzo |
|---|-------|----------|
| 17 | Unificar pipeline streaming / no-streaming | 8h |
| 18 | Migrar de python-jose a PyJWT | 4h |
| 19 | Agregar ErrorBoundary en frontend | 2h |
| 20 | Memoizar FilterContext | 1h |
| 21 | Unificar HTTP calls a axiosClient | 2h |
| 22 | Configurar backup automatico de DB | 4h |
| 23 | Agregar Pydantic schema a PATCH operacion | 2h |
| 24 | Guardia division por cero en operacion_service | 1h |
| 25 | Reemplazar str(e) por mensajes genericos | 2h |
| 26 | Limpiar console.log de produccion | 2h |
| 27 | Configurar pre-commit hooks | 2h |
| 28 | Monitoreo uptime externo | 1h |

**Total estimado Fase 3: ~31 horas**

### Fase 4: MEJORAS (Mes 3+)

| # | Tarea | Esfuerzo |
|---|-------|----------|
| 29 | Lazy loading / code splitting frontend | 4h |
| 30 | Multi-stage Docker build | 2h |
| 31 | Migrar a lifespan en FastAPI | 1h |
| 32 | Cache para consultas AI | 4h |
| 33 | Metricas Prometheus + dashboard | 8h |
| 34 | Gunicorn con multiple workers | 1h |
| 35 | Versionamiento semantico + CHANGELOG | 2h |
| 36 | Dependency pinning + Renovate | 2h |
| 37 | Filtrado server-side + paginacion | 8h |
| 38 | Unificar modales duplicados | 4h |

**Total estimado Fase 4: ~36 horas**

---

### Resumen de Esfuerzo Total

| Fase | Prioridad | Horas Estimadas |
|------|-----------|:---:|
| Fase 1 | CRITICA (bloquea produccion) | ~31h |
| Fase 2 | ALTA (primeros 30 dias) | ~26h |
| Fase 3 | MEDIA (primeros 90 dias) | ~31h |
| Fase 4 | MEJORAS (trimestre 2) | ~36h |
| **TOTAL** | | **~124h** |

---

*Documento generado por analisis automatizado de QA. Cada item incluye archivo y linea exacta para facilitar la correccion.*
