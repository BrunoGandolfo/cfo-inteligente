"""
Analytics Services Package

Servicios de análisis y detección de anomalías.

Autor: Sistema CFO Inteligente
Fecha: Noviembre 2025
"""

from app.services.analytics.anomaly_detector import AnomalyDetector
from app.services.analytics.variance_detector import VarianceDetector

__all__ = ['AnomalyDetector', 'VarianceDetector']

