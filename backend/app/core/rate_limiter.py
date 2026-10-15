"""Rate limiter instance for SlowAPI.

Provee dos key_funcs:
- get_remote_address (default): rate limit por IP. Usado por endpoints de auth
  donde el usuario todavía no está autenticado.
- user_id_or_ip_key: rate limit por user_id extraído del JWT. Usado por
  endpoints autenticados que generan gasto en APIs externas (Anthropic,
  CapSolver). La oficina comparte IP, así que limitar por IP castigaría
  a usuarios inocentes.
"""

from fastapi import Request
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def user_id_or_ip_key(request: Request) -> str:
    """Devuelve user:<id> si el request trae un JWT válido, sino ip:<addr>.

    Decodifica el Authorization header sin tocar la BD: misma firma de
    settings que core.security.get_current_user, sólo que no valida que el
    usuario exista. Ante cualquier fallo cae a IP para no romper el endpoint.
    """
    auth = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except (JWTError, ValueError):
            pass
    return f"ip:{get_remote_address(request)}"


class LimiterFailOpen(Limiter):
    """Limiter que deja pasar el request si el chequeo de límites falla.

    swallow_errors=True no alcanza: si el storage falla, slowapi no setea
    request.state.view_rate_limit y sus endpoints sync lo leen igual al
    inyectar headers → AttributeError → 500. Pasó en producción (15/10/2026):
    el proceso se quedó sin threads y nadie pudo hacer login. Inicializarlo
    en None antes del chequeo hace que un fallo interno deje pasar.
    """

    def _check_request_limit(self, request, endpoint_func, in_middleware=True):
        request.state.view_rate_limit = None
        super()._check_request_limit(request, endpoint_func, in_middleware)


limiter = LimiterFailOpen(
    key_func=get_remote_address,
    storage_uri=settings.redis_url or "memory://",
    swallow_errors=True,
)
