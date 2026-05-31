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
