from app.schemas.doctrina import DoctrinaBase, DoctrinaCreate, DoctrinaResponse
from app.schemas.tramite_dgr import (
    TramiteDgrCreate,
    TramiteDgrResponse,
    TramiteDgrUpdate,
)
from app.schemas.scraping_progress import (
    OverallScrapingProgress,
    ScrapingFailureCreate,
    ScrapingFailureRead,
    ScrapingLogCreate,
    ScrapingLogRead,
    ScrapingProgressRead,
    ScrapingProgressUpdate,
)

__all__ = [
    "DoctrinaBase",
    "DoctrinaCreate",
    "DoctrinaResponse",
    "OverallScrapingProgress",
    "ScrapingFailureCreate",
    "ScrapingFailureRead",
    "ScrapingLogCreate",
    "ScrapingLogRead",
    "ScrapingProgressRead",
    "ScrapingProgressUpdate",
    "TramiteDgrCreate",
    "TramiteDgrResponse",
    "TramiteDgrUpdate",
]
