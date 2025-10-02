"""
Sistema de Logging Profesional - CFO Inteligente

Configuración centralizada de logging con:
- Niveles apropiados (DEBUG, INFO, WARNING, ERROR)
- Formato con timestamps
- Rotación de archivos
- Logs separados por módulo

NO usar print() en producción - siempre usar logger

Uso:
    from app.core.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("Mensaje informativo")
    logger.error("Error crítico", exc_info=True)
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Configuración global
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_logger(name: str) -> logging.Logger:
    """
    Retorna logger configurado para un módulo
    
    Args:
        name: Nombre del módulo (usar __name__)
        
    Returns:
        Logger configurado con handlers apropiados
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(LOG_LEVEL)
    
    # Formatter común
    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    
    # Handler 1: Console (solo INFO y superior)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler 2: Archivo general (todos los niveles)
    file_handler = RotatingFileHandler(
        LOG_DIR / 'cfo_inteligente.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler 3: Archivo de errores (solo ERROR y CRITICAL)
    error_handler = RotatingFileHandler(
        LOG_DIR / 'errors.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger


# Logger por defecto para el core
core_logger = get_logger('cfo_inteligente.core')

