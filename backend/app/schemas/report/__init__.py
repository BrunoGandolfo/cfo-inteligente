"""
Schemas para Sistema de Reportes PDF

Expone todos los schemas en un solo import.
"""

from .request import ReportRequest, PeriodConfig, ComparisonConfig, ReportOptions
from .response import ReportResponse, ReportMetadata, ProgressUpdate
from .metrics import (
    TotalsMetrics,
    ResultsMetrics,
    RatiosMetrics,
    DistributionMetrics,
    EfficiencyMetrics,
    TrendsMetrics,
    MetricsAggregate
)

__all__ = [
    'ReportRequest',
    'PeriodConfig',
    'ComparisonConfig',
    'ReportOptions',
    'ReportResponse',
    'ReportMetadata',
    'ProgressUpdate',
    'TotalsMetrics',
    'ResultsMetrics',
    'RatiosMetrics',
    'DistributionMetrics',
    'EfficiencyMetrics',
    'TrendsMetrics',
    'MetricsAggregate'
]

