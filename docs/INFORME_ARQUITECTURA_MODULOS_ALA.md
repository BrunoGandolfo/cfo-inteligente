# Informe: Arquitectura de Módulos CFO Inteligente — Base para Módulo ALA (Anti-Lavado de Activos)

**Objetivo:** Documentar la estructura actual del proyecto para implementar el módulo ALA (escribanos) siguiendo los mismos patrones.  
**Alcance:** Backend (módulos Expedientes, Casos, Contratos, Leyes), modelos, servicios externos, frontend.  
**Sin código:** Solo investigación y documentación.

---

## 1. BACKEND — Estructura de módulos existentes

### 1.1 Módulo Expedientes

| Capa | Ubicación | Notas |
|------|-----------|--------|
| **API (router)** | `backend/app/api/expedientes.py` | `APIRouter(prefix="/api/expedientes", tags=["expedientes"])` |
| **Modelos** | `backend/app/models/expediente.py` | `Expediente`, `ExpedienteMovimiento` + helpers `parsear_iue`, `generar_hash_movimiento` |
| **Servicio** | `backend/app/services/expediente_service.py` | Lógica de negocio + integración SOAP Poder Judicial |
| **Schemas** | Inline en `api/expedientes.py` | `ExpedienteCreate`, `MovimientoResponse`, `ExpedienteResponse`, etc. (no hay `schemas/expediente.py`) |

- **Registro en main:** `app.include_router(expedientes_router)` (sin prefix extra; el router ya lleva `/api/expedientes`).
- **Dependencias:** `get_db`, `get_current_user`; acceso restringido a socios (lista `USUARIOS_FILTRO_EXPEDIENTES` en backend).
- **Patrón:** API → Service → Model/DB. No usa Repository.

---

### 1.2 Módulo Casos

| Capa | Ubicación | Notas |
|------|-----------|--------|
| **API** | `backend/app/api/casos.py` | `APIRouter(prefix="/api/casos", tags=["casos"])` |
| **Modelos** | `backend/app/models/caso.py` | `Caso`, enums `EstadoCaso`, `PrioridadCaso` |
| **Servicio** | Reutiliza `expediente_service` | Sincronización por IUE al crear caso |
| **Schemas** | `backend/app/schemas/caso.py` | `CasoBase`, `CasoCreate`, `CasoUpdate`, `CasoResponse`, `CasoList` |

- Filtrado por `responsable_id == current_user.id`.
- Crear caso puede recibir `iue` y llama a `expediente_service.sincronizar_expediente`.

---

### 1.3 Módulo Contratos (Notarial)

| Capa | Ubicación | Notas |
|------|-----------|--------|
| **API** | `backend/app/api/contratos.py` | `APIRouter(prefix="/api/contratos", tags=["contratos"])` |
| **Modelos** | `backend/app/models/contrato.py` | `Contrato` (DOCX, categorías, campos editables) |
| **Servicios** | `contrato_fields_extractor.py`, `contrato_generator.py` | Extracción de campos (Claude), generación DOCX |
| **Schemas** | `backend/app/schemas/contrato.py` | `ContratoBase`, `ContratoCreate`, `ContratoUpdate`, `ContratoResponse`, `ContratoListResponse`, `ContratoBusquedaParams` |

- GET públicos (categorías, buscar, listar, ver, descargar); POST/PATCH/DELETE y acciones requieren socio.
- CRUD en API: creación/actualización directas sobre el modelo; servicios solo para extracción y generación.

---

### 1.4 Módulo Leyes (referencia)

| Capa | Ubicación | Notas |
|------|-----------|--------|
| **API** | `backend/app/api/leyes.py` | `APIRouter(prefix="/api/leyes", tags=["leyes"])` |
| **Modelos** | `backend/app/models/ley.py` | `Ley` (numero, anio, titulo, texto_completo, resumen, etc.) |
| **Servicio** | `backend/app/services/ley_service.py` | Búsqueda, carga CSV Parlamento, IMPO |
| **Schemas** | `backend/app/schemas/ley.py` | `LeyResponse`, `LeyDetalleResponse`, `LeyBusquedaParams`, `LeyListResponse` |

- API delega en `ley_service` para búsqueda y cargas; patrón Service claro.

---

### 1.5 Patrón general backend

- **Repository:** Solo Operaciones usa `repositories/operations_repository.py` y `base_repository.py`. Expedientes, Casos, Contratos y Leyes **no** usan repositorios: la API inyecta `Session` y llama al **Service**; el Service recibe `db: Session` y trabaja con los modelos.
- **Flujo:** `Router (Depends get_db, get_current_user)` → **Service (db, …)** → Modelos / APIs externas.
- **Schemas:** Lo habitual es archivo en `app/schemas/<modulo>.py`. Expedientes es la excepción (schemas inline en el router).
- **Registro:** Cada router define su `prefix` y en `main.py` se hace `include_router(router)` sin volver a añadir prefix.

---

## 2. MODELOS — Resumen y convenciones

### 2.1 Listado de modelos y relaciones (relevantes para ALA)

| Modelo | Archivo | Tabla | Relaciones principales |
|--------|---------|--------|-------------------------|
| Usuario | `models/usuario.py` | usuarios | conversaciones |
| Area | `models/area.py` | areas | operaciones, expedientes |
| Cliente | `models/cliente.py` | clientes | expedientes |
| Expediente | `models/expediente.py` | expedientes | ExpedienteMovimiento, Cliente, Area, Usuario (responsable) |
| ExpedienteMovimiento | `models/expediente.py` | expedientes_movimientos | Expediente |
| Caso | `models/caso.py` | casos | Usuario (responsable), Expediente |
| Contrato | `models/contrato.py` | contratos | — |
| Ley | `models/ley.py` | leyes | — |
| Operacion | `models/operacion.py` | operaciones | Area |
| Conversacion, Mensaje | `models/conversacion.py` | — | Usuario |
| DistribucionDetalle | `models/distribucion.py` | — | — |
| Socio, Proveedor | `models/socio.py`, `models/proveedor.py` | — | — |

Exportación central: `app/models/__init__.py` reexporta los modelos usados en la app.

### 2.2 Soft delete

- **Con `deleted_at`:** Expediente, ExpedienteMovimiento (no), Caso, Contrato, Ley, Operacion.
- **Sin `deleted_at`:** Usuario, Cliente, Area (catálogos/activos).
- **Uso:** `Model.deleted_at.is_(None)` en listados y filtros; borrado lógico: `objeto.deleted_at = datetime.now(timezone.utc)`.

### 2.3 Auditoría (created_at, updated_at)

- **Convención:** `created_at = Column(DateTime, default=utc_now)` y `updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)`.
- **utc_now:** Definido en cada modelo (o compartido) como `datetime.now(timezone.utc)`.
- Modelos de dominio (Caso, Contrato, Expediente, Ley, Operacion) siguen esta pauta.

### 2.4 Clave primaria

- **UUID** en todos los modelos revisados: `id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`.
- Ningún módulo de dominio usa Integer como PK.

---

## 3. SERVICIOS EXTERNOS — Patrones de integración

### 3.1 Poder Judicial (SOAP – Expedientes)

- **Archivo:** `backend/app/services/expediente_service.py`.
- **Cliente:** `zeep.Client(WSDL_URL)` con `Settings(strict=False, xml_huge_tree=True)`.
- **Patrón:** Cliente SOAP cacheado en variable módulo `_soap_client`; función `_obtener_cliente_soap()` (lazy init) y `_resetear_cliente_soap()` en errores.
- **Config:** URL WSDL fija en el módulo; sin variables de entorno para el WS.
- **Uso:** `consultar_expediente_ws(iue)` devuelve dict; el servicio luego persiste en BD (Expediente, ExpedienteMovimiento).

### 3.2 Twilio (WhatsApp)

- **Archivo:** `backend/app/services/twilio_service.py`.
- **Cliente:** `twilio.rest.Client`; inicialización lazy en `_get_twilio_client()` con `os.getenv("TWILIO_ACCOUNT_SID")`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`, `TWILIO_NOTIFY_NUMBERS`.
- **Patrón:** Cliente global opcional; si faltan credenciales, las funciones devuelven resultado de error sin lanzar.

### 3.3 Tipo de cambio / APIs REST

- **Archivo:** `backend/app/services/tipo_cambio_service.py`.
- **Cliente:** `requests.get("https://uy.dolarapi.com/v1/cotizaciones/usd")`.
- **Patrón:** Cache en memoria (`_cache` con timestamp); fallback a valores fijos si falla la petición; sin clase, solo funciones.

### 3.4 Leyes (Parlamento / IMPO)

- **Archivo:** `backend/app/services/ley_service.py`.
- **Orígenes:** CSV Parlamento, posible integración IMPO para texto.
- **Patrón:** Servicio que recibe `db: Session` y realiza búsquedas/cargas en `Ley`.

### 3.5 Patrón común para APIs externas

1. **Cliente único por servicio:** variable de módulo (lazy init o cache) para no recrear conexiones.
2. **Configuración:** variables de entorno (`os.getenv`) o `settings` de Pydantic; no credenciales en código.
3. **Manejo de fallos:** try/except, log, retorno controlado o fallback; en Twilio, retorno con `exito: False` si no está configurado.
4. **Sin capa “Adapter” formal:** la lógica de llamada externa vive dentro del servicio de dominio (ej. `expediente_service`, `twilio_service`, `tipo_cambio_service`).

---

## 4. FRONTEND — Estructura

### 4.1 Páginas (Expedientes, Casos, Contratos)

- **Ubicación:** `frontend/src/pages/`  
  - `Expedientes.jsx`, `Casos.jsx`, `Contratos.jsx`.
- **Navegación:** No hay React Router. Estado en `App.jsx`: `currentPage` (string: 'dashboard', 'expedientes', 'casos', 'notarial', etc.). `renderContent()` hace `switch (currentPage)` y devuelve el componente de página.
- **Layout:** `Layout` recibe `onNavigate`, `currentPage`, `onCasosToggle`, `onNotarialToggle` y renderiza `Sidebar` + `children`. El Sidebar llama a `onExpedientesToggle`, `onCasosToggle`, `onNotarialToggle` para cambiar de página.

### 4.2 Hooks

- **Ubicación:** `frontend/src/hooks/`  
  - `useExpedientes.js`, `useCasos.js`, `useContratos.js`.
- **Patrón:** Hook que devuelve estado (lista, item actual, loading, error) y funciones (fetch, crear, actualizar, eliminar). Usan `axiosClient` de `services/api/axiosClient.js` (baseURL, interceptors JWT, manejo 401).
- **Rutas API:** Coinciden con el backend: `/api/casos/`, `/api/expedientes/...`, `/api/contratos/...`.

### 4.3 Formularios

- Estado local con `useState` para `formData` y para modal (ej. `showModal`, `editMode`).
- Al abrir edición: se rellena `formData` desde el item seleccionado; al crear, se resetea.
- `handleSubmit` arma el payload y llama a la función del hook (`crearCaso`, `actualizarCaso`, etc.); el hook muestra `toast` y refresca la lista.
- Componentes UI reutilizables: `Card`, `Button`, etc. en `components/ui/`; modales en `components/modals/` o inline.

### 4.4 Menú y permisos

- **Sidebar:** `frontend/src/components/layout/Sidebar.jsx`. Lista `allItems` (Dashboard, Expedientes, Notarial, Casos, Operaciones, CFO AI, Indicadores, Soporte, Configuración). Se filtra según `esSocio` (localStorage) y `USUARIOS_ACCESO_EXPEDIENTES_CASOS` (lista de emails) para mostrar u ocultar Expedientes y Casos.
- **Mobile:** `MobileNav.jsx` repite la misma lógica de ítems y callbacks.

---

## 5. ARQUITECTURA ACTUAL (RESUMEN)

```
BACKEND
  main.py
    └── include_router( auth | operaciones | tipo_cambio | cfo | catalogos | metricas | indicadores | expedientes | leyes | casos | contratos )
  app/
    api/          → Routers FastAPI (prefix + tags), Depends(get_db, get_current_user)
    models/       → SQLAlchemy, UUID PK, deleted_at donde aplique, created_at/updated_at
    schemas/      → Pydantic (Create, Update, Response, List) — excepto expedientes (inline)
    services/     → Lógica de negocio + integraciones externas (SOAP, REST, Twilio)
    repositories/ → Solo operaciones (BaseRepository + OperationsRepository)
    core/         → config, database, security, dependencies

FRONTEND
  App.jsx         → currentPage, validateToken, renderContent() switch
  pages/          → Una página por módulo (Expedientes, Casos, Contratos, …)
  hooks/          → useCasos, useExpedientes, useContratos (estado + API con axiosClient)
  services/api/   → axiosClient (JWT, 401 redirect)
  components/
    layout/        → Layout, Sidebar, MobileNav (navegación por callbacks)
    ui/            → Card, Button, Modal, …
```

---

## 6. PATRONES A SEGUIR PARA EL MÓDULO ALA

1. **Backend**
   - **Modelo:** `app/models/ala.py` (o `prevencion_ala.py`) con UUID, `deleted_at`, `created_at`, `updated_at` y relaciones (ej. Usuario, Cliente) si aplican.
   - **Schema:** `app/schemas/ala.py` con al menos Create, Update, Response y uno de listado (List/ListResponse).
   - **Servicio:** `app/services/ala_service.py` (o nombre de dominio) con funciones que reciban `db: Session` y opcionalmente parámetros de integración externa.
   - **API:** `app/api/ala.py` con `APIRouter(prefix="/api/ala", tags=["ala"])`, uso de `get_db` y `get_current_user`, y delegación de lógica al servicio.
   - **Registro:** En `main.py`, `from app.api.ala import router as ala_router` y `app.include_router(ala_router)`.
   - No es necesario usar Repository a menos que se decida estandarizar ese patrón más adelante.

2. **Modelos**
   - PK UUID; soft delete con `deleted_at` si la entidad se “da de baja”; auditoría con `utc_now` en `created_at` y `updated_at`.

3. **Servicios externos (si ALA consume APIs)**
   - Un módulo de servicio (ej. `ala_external_service.py` o dentro de `ala_service.py`) con cliente cacheado/lazy y configuración por env.

4. **Frontend**
   - **Página:** `frontend/src/pages/ALA.jsx` (o `PrevencionALA.jsx`).
   - **Hook:** `frontend/src/hooks/useALA.js` con estado y llamadas a `axiosClient.get/post/patch/delete` a `/api/ala/...`.
   - **Navegación:** Añadir ítem en `Sidebar.jsx` y `MobileNav.jsx` (ej. “ALA” o “Prevención ALA”) y un case en `renderContent()` de `App.jsx` (ej. `case 'ala': return <ALA />`).
   - **Permisos:** Si el acceso es restringido (ej. por rol o lista de usuarios), reutilizar el patrón de `USUARIOS_ACCESO_EXPEDIENTES_CASOS` o equivalente en backend y en el filtrado del menú.

---

## 7. UBICACIÓN RECOMENDADA DEL MÓDULO ALA

| Capa | Ruta recomendada |
|------|-------------------|
| **Modelo** | `backend/app/models/ala.py` (o `prevencion_ala.py` si se prefiere nombre más explícito) |
| **Schema** | `backend/app/schemas/ala.py` |
| **Servicio** | `backend/app/services/ala_service.py` |
| **API** | `backend/app/api/ala.py` |
| **Página** | `frontend/src/pages/ALA.jsx` |
| **Hook** | `frontend/src/hooks/useALA.js` |

**Registro backend:** En `backend/app/main.py`, después de los otros routers:

```text
from app.api.ala import router as ala_router
app.include_router(ala_router)
```

**Registro frontend:** En `App.jsx` importar la página y añadir case `'ala'`; en `Layout.jsx` pasar un callback `onALAToggle` si se desea simetría con Casos/Notarial; en `Sidebar.jsx` y `MobileNav.jsx` añadir el ítem “ALA” (o “Prevención ALA”) y el callback correspondiente.

**Exportación del modelo:** Añadir en `backend/app/models/__init__.py` el import y el nombre del modelo ALA en `__all__`.

Con esto, el módulo ALA queda alineado con la arquitectura actual de CFO Inteligente y listo para implementar sin generar código en esta fase, tal como se solicitó.
