"""
Stats Calculator - Cálculos estadísticos con Scipy

Wrappers de scipy para regresión lineal, intervalos de confianza, etc.
Funciones puras enfocadas en estadística.

Requiere: scipy>=1.11.0

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import numpy as np
from scipy import stats
from typing import Tuple, List


def linear_regression_with_confidence(
    x_values: List[float],
    y_values: List[float],
    x_future: List[float],
    confidence_level: float = 0.95
) -> Tuple[List[float], List[float], List[float], float, float]:
    """
    Regresión lineal con intervalos de confianza.
    
    Args:
        x_values: Valores X históricos (ej: [1, 2, 3, ..., 12] para meses)
        y_values: Valores Y históricos (ej: ingresos mensuales)
        x_future: Valores X para proyectar (ej: [13, 14, 15] para próximos 3 meses)
        confidence_level: Nivel de confianza (default: 0.95 = 95%)
        
    Returns:
        Tupla de:
        - y_predicted: Valores proyectados
        - y_upper: Banda superior IC
        - y_lower: Banda inferior IC
        - r_squared: Coeficiente de determinación (0-1)
        - slope: Pendiente de la recta
        
    Ejemplos:
        >>> x = [1, 2, 3, 4, 5, 6]
        >>> y = [100, 120, 115, 130, 125, 140]
        >>> x_fut = [7, 8, 9]
        >>> y_pred, y_up, y_low, r2, slope = linear_regression_with_confidence(x, y, x_fut)
        >>> len(y_pred) == 3
        True
        >>> 0 <= r2 <= 1
        True
    """
    # Convertir a numpy arrays
    x = np.array(x_values, dtype=float)
    y = np.array(y_values, dtype=float)
    x_fut = np.array(x_future, dtype=float)
    
    # Regresión lineal
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # R²
    r_squared = r_value ** 2
    
    # Proyección
    y_predicted = slope * x_fut + intercept
    
    # Intervalo de confianza
    n = len(x)
    t_val = stats.t.ppf((1 + confidence_level) / 2, n - 2)
    
    # Error de predicción para cada punto futuro
    x_mean = np.mean(x)
    sxx = np.sum((x - x_mean) ** 2)
    
    predict_errors = std_err * np.sqrt(1 + 1/n + (x_fut - x_mean)**2 / sxx)
    margins = t_val * predict_errors
    
    y_upper = y_predicted + margins
    y_lower = y_predicted - margins
    
    return (
        y_predicted.tolist(),
        y_upper.tolist(),
        y_lower.tolist(),
        float(r_squared),
        float(slope)
    )


def calculate_moving_average(
    values: List[float],
    window: int = 3
) -> List[float]:
    """
    Calcula promedio móvil.
    
    Args:
        values: Serie de valores
        window: Tamaño de ventana (default: 3)
        
    Returns:
        Lista con promedios móviles (len = len(values))
        Los primeros window-1 valores son None
        
    Ejemplos:
        >>> calculate_moving_average([10, 20, 30, 40, 50], window=3)
        [None, None, 20.0, 30.0, 40.0]
    """
    arr = np.array(values, dtype=float)
    result = []
    
    for i in range(len(arr)):
        if i < window - 1:
            result.append(None)
        else:
            window_values = arr[i - window + 1 : i + 1]
            result.append(float(np.mean(window_values)))
    
    return result


def detect_outliers_iqr(
    values: List[float],
    threshold: float = 1.5
) -> List[int]:
    """
    Detecta outliers usando método IQR (Interquartile Range).
    
    Args:
        values: Serie de valores
        threshold: Multiplicador de IQR (default: 1.5 estándar)
        
    Returns:
        Índices de los outliers
        
    Ejemplos:
        >>> detect_outliers_iqr([10, 12, 11, 13, 100, 12, 11])
        [4]  # El valor 100 es outlier
    """
    arr = np.array(values, dtype=float)
    
    q1 = np.percentile(arr, 25)
    q3 = np.percentile(arr, 75)
    iqr = q3 - q1
    
    lower_bound = q1 - threshold * iqr
    upper_bound = q3 + threshold * iqr
    
    outlier_indices = []
    for i, val in enumerate(arr):
        if val < lower_bound or val > upper_bound:
            outlier_indices.append(i)
    
    return outlier_indices


def calculate_volatility(
    values: List[float]
) -> Tuple[float, float]:
    """
    Calcula volatilidad (desviación estándar y coeficiente de variación).
    
    Args:
        values: Serie de valores
        
    Returns:
        Tupla (std_dev, coefficient_of_variation)
        
    Ejemplos:
        >>> calculate_volatility([100, 120, 110, 130, 115])
        (11.789826, 10.164197)  # std ~11.8, cv ~10.2%
    """
    arr = np.array(values, dtype=float)
    
    std_dev = float(np.std(arr, ddof=1))  # ddof=1 para muestra
    mean = float(np.mean(arr))
    
    if mean == 0:
        coefficient_of_variation = 0.0
    else:
        coefficient_of_variation = (std_dev / mean) * 100
    
    return std_dev, coefficient_of_variation


def calculate_growth_rate(
    initial_value: float,
    final_value: float,
    periods: int
) -> float:
    """
    Calcula tasa de crecimiento compuesta (CAGR).
    
    Args:
        initial_value: Valor inicial
        final_value: Valor final
        periods: Número de períodos
        
    Returns:
        CAGR en porcentaje
        
    Formula:
        CAGR = ((final/initial)^(1/periods) - 1) × 100
        
    Ejemplos:
        >>> calculate_growth_rate(100, 121, 2)
        10.0  # 10% CAGR anual
    """
    if initial_value <= 0 or final_value <= 0 or periods <= 0:
        return 0.0
    
    cagr = (((final_value / initial_value) ** (1 / periods)) - 1) * 100
    return float(cagr)

