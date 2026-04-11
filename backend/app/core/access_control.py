"""
Listas centralizadas de control de acceso por módulo.
ÚNICA FUENTE DE VERDAD para permisos basados en email.
Cualquier cambio de permisos se hace SOLO en este archivo.
"""

# --- Socios autorizados (prefijos de email) ---
SOCIOS_AUTORIZADOS = ["aborio", "falgorta", "vcaresani", "gtaborda", "bgandolfo"]
DOMINIO_DEFAULT = "grupoconexion.uy"
DOMINIOS_EXCEPCION = {"bgandolfo": "cgmasociados.com"}
DOMINIOS_PERMITIDOS = ["cgmasociados.com", "grupoconexion.uy"]

# --- Operaciones (acceso restringido a área Contable) ---
EMAILS_OPERACIONES_CONTABLE = ["naraujo@grupoconexion.uy"]
AREA_CONTABLE_ID = "14700c01-3b3d-49c6-8e2e-f3ebded1b1bb"

# --- Expedientes ---
USUARIOS_ACCESO_EXPEDIENTES = [
    "bgandolfo@cgmasociados.com",
    "gtaborda@grupoconexion.uy",
    "falgorta@grupoconexion.uy",
    "gferrari@grupoconexion.uy",
]
# Usuarios que solo ven expedientes donde ellos son el responsable
# Bruno NO está en esta lista → ve todos
USUARIOS_FILTRO_EXPEDIENTES = [
    "gferrari@grupoconexion.uy",
    "falgorta@grupoconexion.uy",
    "gtaborda@grupoconexion.uy",
]

# --- Casos ---
USUARIOS_ACCESO_CASOS = [
    "bgandolfo@cgmasociados.com",
    "gtaborda@grupoconexion.uy",
    "falgorta@grupoconexion.uy",
    "gferrari@grupoconexion.uy",
]
# --- Jurisprudencia ---
USUARIOS_ACCESO_JURISPRUDENCIA = [
    "bgandolfo@cgmasociados.com",
    "gtaborda@grupoconexion.uy",
    "falgorta@grupoconexion.uy",
    "gferrari@grupoconexion.uy",
]
# Usuarios que solo ven casos donde ellos son el responsable
# Bruno NO está en esta lista → ve todos
USUARIOS_FILTRO_CASOS = [
    "gtaborda@grupoconexion.uy",
    "falgorta@grupoconexion.uy",
    "gferrari@grupoconexion.uy",
]

# --- Contratos ---
COLABORADORES_ACCESO_CONTRATOS = [
    "gferrari@grupoconexion.uy",
    "jmora@grupoconexion.uy",
]

# --- DGR ---
COLABORADORES_ACCESO_DGR = [
    "jmora@grupoconexion.uy",
    "gferrari@grupoconexion.uy",
]
USUARIOS_NOTIFICACION_DGR = [
    "vcaresani@grupoconexion.uy",
    "aborio@grupoconexion.uy",
    "jmora@grupoconexion.uy",
]

# --- ALA ---
COLABORADORES_ACCESO_COMPLETO_ALA = ["gferrari@grupoconexion.uy"]
USUARIOS_ACCESO_ALA = [
    "bgandolfo@cgmasociados.com",
    "gferrari@grupoconexion.uy",
]


# --- CONTABLE ---
USUARIOS_ACCESO_CONTABLE = [
    "naraujo@grupoconexion.uy",
    "bgandolfo@cgmasociados.com",
]


def tiene_acceso(email: str, lista: list[str]) -> bool:
    """Verifica si un email tiene acceso según una lista."""
    return email.lower() in [e.lower() for e in lista]
