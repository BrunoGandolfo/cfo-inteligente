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


limiter = Limiter(key_func=get_remote_address)
