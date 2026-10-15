from jose import jwt
from starlette.requests import Request

from app.core.config import settings
from app.core.rate_limiter import limiter, user_id_or_ip_key


def make_request(authorization: str | None = None, host: str = "203.0.113.10") -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode("utf-8")))

    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": headers,
            "query_string": b"",
            "client": (host, 12345),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


def test_user_id_or_ip_key_usa_sub_de_jwt_valido():
    token = jwt.encode(
        {"sub": "user-123"},
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    key = user_id_or_ip_key(make_request(f"Bearer {token}"))

    assert key == "user:user-123"


def test_user_id_or_ip_key_sin_authorization_usa_ip():
    key = user_id_or_ip_key(make_request(host="198.51.100.25"))

    assert key == "ip:198.51.100.25"


def test_user_id_or_ip_key_token_invalido_usa_ip_sin_lanzar():
    key = user_id_or_ip_key(make_request("Bearer token-malformado", host="192.0.2.44"))

    assert key == "ip:192.0.2.44"


def test_limiter_swallow_errors_true():
    # slowapi guarda el flag como privado (_swallow_errors); es la unica superficie observable.
    # Blinda contra que saquen el fail-open del constructor: sin el, un fallo del storage
    # volveria a tirar 500 en el login (el bug original).
    assert limiter._swallow_errors is True


# ── Fail-open real: un fallo del storage no puede convertirse en 500 ──────
# Incidente 15/10/2026: el proceso se quedó sin threads, el storage del
# limiter falló y slowapi devolvió 500 en /api/auth/login a todos.

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.rate_limiter import LimiterFailOpen


def _app_con(limiter_instancia):
    app = FastAPI()
    app.state.limiter = limiter_instancia
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.post("/login")
    @limiter_instancia.limit("10/minute")
    def login(request: Request):  # sync, como el login real
        return {"ok": True}

    return app


def _storage_roto(limiter_instancia):
    return patch.object(
        limiter_instancia._limiter, "hit", side_effect=RuntimeError("can't start new thread"),
    )


def test_limiter_original_reproduce_el_500():
    """Documenta el bug de slowapi que tumbó el login (si deja de fallar, se puede simplificar)."""
    original = Limiter(key_func=get_remote_address, storage_uri="memory://", swallow_errors=True)
    client = TestClient(_app_con(original), raise_server_exceptions=False)
    with _storage_roto(original):
        assert client.post("/login").status_code == 500


def test_limiter_fail_open_deja_pasar_si_el_storage_falla():
    fail_open = LimiterFailOpen(key_func=get_remote_address, storage_uri="memory://", swallow_errors=True)
    client = TestClient(_app_con(fail_open), raise_server_exceptions=False)
    with _storage_roto(fail_open):
        respuesta = client.post("/login")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"ok": True}


def test_limiter_fail_open_sigue_limitando_cuando_funciona():
    fail_open = LimiterFailOpen(key_func=get_remote_address, storage_uri="memory://", swallow_errors=True)
    client = TestClient(_app_con(fail_open), raise_server_exceptions=False)
    codigos = [client.post("/login").status_code for _ in range(11)]
    assert codigos[:10] == [200] * 10
    assert codigos[10] == 429


def test_limiter_de_la_app_es_fail_open():
    assert isinstance(limiter, LimiterFailOpen)
