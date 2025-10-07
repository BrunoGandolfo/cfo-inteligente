"""
AssetManager - Gestión de recursos para PDFs

Convierte imágenes a base64 para embeber en HTML/PDF.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import base64
from pathlib import Path
from typing import Dict


class AssetManager:
    """Gestiona conversión de imágenes a base64 para PDFs"""
    
    @staticmethod
    def image_to_base64(image_path: str) -> str:
        """
        Convierte imagen a string base64 para embeber en HTML.
        
        Args:
            image_path: Ruta de la imagen
            
        Returns:
            String base64 con data URI
        """
        with open(image_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode()
        
        # Determinar MIME type
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.svg': 'image/svg+xml'
        }
        mime = mime_types.get(ext, 'image/png')
        
        return f"data:{mime};base64,{encoded}"
    
    @staticmethod
    def batch_convert(image_paths: Dict[str, str]) -> Dict[str, str]:
        """
        Convierte múltiples imágenes a base64.
        
        Args:
            image_paths: Dict con {key: path}
            
        Returns:
            Dict con {key: base64_string}
        """
        return {
            key: AssetManager.image_to_base64(path)
            for key, path in image_paths.items()
        }

